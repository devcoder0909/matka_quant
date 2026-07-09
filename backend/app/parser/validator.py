"""
Matka Quantum AI - Record Validator
=====================================

Validates normalised Satta Matka records for mathematical consistency,
duplicates, range validity, date coverage, and calculates quality /
completeness scores.

**Golden rule:** the validator NEVER silently modifies values.  Every issue
is logged as an error entry.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result data class
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Encapsulates the outcome of a validation run."""

    valid_records: List[Dict[str, Any]] = field(default_factory=list)
    invalid_records: List[Dict[str, Any]] = field(default_factory=list)
    duplicate_records: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    quality_score: float = 0.0
    completeness_score: float = 0.0
    total_imported: int = 0
    date_coverage: Dict[str, Any] = field(default_factory=dict)
    last_result_date: str = ""


# ---------------------------------------------------------------------------
# Internal checks
# ---------------------------------------------------------------------------

def _digit_sum_mod10(patti: str) -> int:
    return sum(int(d) for d in patti) % 10


def _add_error(
    errors: list,
    row: int,
    field_name: str,
    error_type: str,
    detail: str,
    raw_value: Any = None,
) -> None:
    errors.append({
        "row": row,
        "field": field_name,
        "error_type": error_type,
        "detail": detail,
        "raw_value": raw_value,
    })


def _validate_single_record(
    rec: Dict[str, Any],
    row_idx: int,
    errors: list,
) -> bool:
    """
    Validate a single record.  Appends any issues to *errors*.
    Returns ``True`` if the record is usable (may have warnings).
    """
    is_valid = True

    # --- Range checks ---
    op = rec.get("open_patti")
    cp = rec.get("close_patti")
    jodi = rec.get("jodi")
    oa = rec.get("open_ank")
    ca = rec.get("close_ank")

    if op is not None:
        if not re.match(r"^\d{3}$", str(op)):
            _add_error(errors, row_idx, "open_patti", "INVALID_FORMAT",
                       f"Expected 3-digit string, got '{op}'", op)
            is_valid = False
        else:
            val = int(op)
            if val < 0 or val > 999:
                _add_error(errors, row_idx, "open_patti", "OUT_OF_RANGE",
                           f"Patti must be 000-999, got {val}", op)
                is_valid = False

    if cp is not None:
        if not re.match(r"^\d{3}$", str(cp)):
            _add_error(errors, row_idx, "close_patti", "INVALID_FORMAT",
                       f"Expected 3-digit string, got '{cp}'", cp)
            is_valid = False
        else:
            val = int(cp)
            if val < 0 or val > 999:
                _add_error(errors, row_idx, "close_patti", "OUT_OF_RANGE",
                           f"Patti must be 000-999, got {val}", cp)
                is_valid = False

    if jodi is not None:
        if not re.match(r"^\d{2}$", str(jodi)):
            _add_error(errors, row_idx, "jodi", "INVALID_FORMAT",
                       f"Expected 2-digit string, got '{jodi}'", jodi)
            is_valid = False
        else:
            val = int(jodi)
            if val < 0 or val > 99:
                _add_error(errors, row_idx, "jodi", "OUT_OF_RANGE",
                           f"Jodi must be 00-99, got {val}", jodi)
                is_valid = False

    if oa is not None:
        if not isinstance(oa, int) or oa < 0 or oa > 9:
            _add_error(errors, row_idx, "open_ank", "OUT_OF_RANGE",
                       f"Ank must be 0-9, got {oa}", oa)
            is_valid = False

    if ca is not None:
        if not isinstance(ca, int) or ca < 0 or ca > 9:
            _add_error(errors, row_idx, "close_ank", "OUT_OF_RANGE",
                       f"Ank must be 0-9, got {ca}", ca)
            is_valid = False

    # --- Mathematical consistency ---
    if op and re.match(r"^\d{3}$", str(op)) and oa is not None:
        expected_oa = _digit_sum_mod10(str(op))
        if oa != expected_oa:
            _add_error(errors, row_idx, "open_ank", "MATH_INCONSISTENCY",
                       f"sum(digits of {op}) % 10 = {expected_oa}, but open_ank = {oa}",
                       oa)
            is_valid = False

    if cp and re.match(r"^\d{3}$", str(cp)) and ca is not None:
        expected_ca = _digit_sum_mod10(str(cp))
        if ca != expected_ca:
            _add_error(errors, row_idx, "close_ank", "MATH_INCONSISTENCY",
                       f"sum(digits of {cp}) % 10 = {expected_ca}, but close_ank = {ca}",
                       ca)
            is_valid = False

    if oa is not None and ca is not None and jodi is not None and re.match(r"^\d{2}$", str(jodi)):
        expected_jodi = f"{oa}{ca}"
        if str(jodi) != expected_jodi:
            _add_error(errors, row_idx, "jodi", "MATH_INCONSISTENCY",
                       f"Expected jodi = '{expected_jodi}' (open_ank={oa}, close_ank={ca}), "
                       f"but got '{jodi}'",
                       jodi)
            is_valid = False

    # --- Date check ---
    date_str = rec.get("date")
    if date_str:
        try:
            datetime.strptime(str(date_str), "%Y-%m-%d")
        except ValueError:
            _add_error(errors, row_idx, "date", "INVALID_DATE",
                       f"Date '{date_str}' is not in YYYY-MM-DD format", date_str)
            # Don't mark invalid just for date format
    else:
        _add_error(errors, row_idx, "date", "MISSING_DATE",
                   "Record has no date", None)

    return is_valid


def _compute_date_coverage(
    valid_records: List[Dict[str, Any]],
    exclude_sundays: bool = True,
) -> Dict[str, Any]:
    """Compute date coverage statistics over valid records."""
    dates: list[datetime] = []
    for rec in valid_records:
        d = rec.get("date")
        if d:
            try:
                dates.append(datetime.strptime(str(d), "%Y-%m-%d"))
            except ValueError:
                continue

    if not dates:
        return {
            "start_date": None,
            "end_date": None,
            "total_days": 0,
            "records_found": 0,
            "missing_days": [],
        }

    dates.sort()
    start = dates[0]
    end = dates[-1]
    date_set = {dt.strftime("%Y-%m-%d") for dt in dates}

    # Generate expected dates
    total_expected = 0
    missing: list[str] = []
    current = start
    while current <= end:
        if exclude_sundays and current.weekday() == 6:
            current += timedelta(days=1)
            continue
        total_expected += 1
        iso = current.strftime("%Y-%m-%d")
        if iso not in date_set:
            missing.append(iso)
        current += timedelta(days=1)

    return {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "total_days": total_expected,
        "records_found": len(date_set),
        "missing_days": missing,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_records(
    records: List[Dict[str, Any]],
    existing_dates: Optional[Set[str]] = None,
) -> ValidationResult:
    """
    Validate a list of normalised Matka result records.

    Checks performed:
    - Range validity (patti 000-999, ank 0-9, jodi 00-99)
    - Mathematical consistency (patti→ank, ank+ank→jodi)
    - Duplicate detection (same date)
    - Date coverage analysis (missing days, excluding Sundays)
    - Quality & completeness scoring

    The validator **never** modifies record values.  Every issue is logged in
    ``errors``.

    Parameters
    ----------
    records : list[dict]
        Normalised records.
    existing_dates : set[str], optional
        Dates already in the database; used to detect duplicates with
        previously imported data.

    Returns
    -------
    ValidationResult
    """
    result = ValidationResult()

    if not records:
        logger.warning("No records to validate")
        return result

    existing = existing_dates or set()
    seen_dates: dict[str, int] = {}  # date -> first row index
    errors: list[dict] = []

    for idx, rec in enumerate(records):
        is_valid = _validate_single_record(rec, idx, errors)
        date_str = rec.get("date")

        # Duplicate check
        is_dup = False
        if date_str:
            ds = str(date_str)
            if ds in existing:
                _add_error(errors, idx, "date", "DUPLICATE_EXISTING",
                           f"Date {ds} already exists in database", ds)
                is_dup = True
            elif ds in seen_dates:
                _add_error(errors, idx, "date", "DUPLICATE_BATCH",
                           f"Date {ds} duplicated within batch (first at row {seen_dates[ds]})",
                           ds)
                is_dup = True
            else:
                seen_dates[ds] = idx

        if is_dup:
            result.duplicate_records.append(rec)
        elif is_valid:
            result.valid_records.append(rec)
        else:
            result.invalid_records.append(rec)

    result.errors = errors
    result.total_imported = len(result.valid_records)

    # --- Quality score ---
    total = len(records)
    valid_count = len(result.valid_records)
    consistency_errors = sum(1 for e in errors if e["error_type"] == "MATH_INCONSISTENCY")
    consistency_penalty = (consistency_errors / max(total, 1)) * 30

    if total > 0:
        base_quality = (valid_count / total) * 100
        result.quality_score = round(max(0.0, base_quality - consistency_penalty), 2)
    else:
        result.quality_score = 0.0

    # --- Date coverage ---
    result.date_coverage = _compute_date_coverage(result.valid_records)

    # --- Completeness score ---
    total_days = result.date_coverage.get("total_days", 0)
    records_found = result.date_coverage.get("records_found", 0)
    if total_days > 0:
        result.completeness_score = round((records_found / total_days) * 100, 2)
    else:
        result.completeness_score = 0.0 if not result.valid_records else 100.0

    # --- Last result date ---
    all_dates = sorted(
        (str(r["date"]) for r in result.valid_records if r.get("date")),
        reverse=True,
    )
    result.last_result_date = all_dates[0] if all_dates else ""

    logger.info(
        "Validation complete: %d valid, %d invalid, %d duplicates, quality=%.1f%%",
        len(result.valid_records), len(result.invalid_records),
        len(result.duplicate_records), result.quality_score,
    )
    return result
