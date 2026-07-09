"""
Matka Quantum AI - Record Normalizer
======================================

Normalises parsed Satta Matka records:
- Dates → YYYY-MM-DD
- Zero-pads patti (3 digits) and jodi (2 digits)
- Derives missing fields (ank from patti, jodi from anks)
- Strips whitespace, removes empty records
- Sorts by date ascending
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.app.parser.detector import detect_date_format

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_PARSERS: list[str] = [
    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
    "%d-%m-%y", "%d/%m/%y", "%d.%m.%y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%m-%d-%Y", "%m/%d/%Y",
]


def _parse_date_to_iso(raw: str, detected_fmt: Optional[str] = None) -> Optional[str]:
    """Try to parse *raw* into YYYY-MM-DD.  Return None on failure."""
    if not raw:
        return None
    raw = raw.strip()

    # Already ISO?
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # Normalise separators
    norm = raw.replace("/", "-").replace(".", "-")

    # Try detected format first
    ordered = list(_DATE_PARSERS)
    if detected_fmt:
        norm_fmt = detected_fmt.replace("/", "-").replace(".", "-")
        ordered.insert(0, norm_fmt)

    for fmt in ordered:
        fmt_norm = fmt.replace("/", "-").replace(".", "-")
        try:
            dt = datetime.strptime(norm, fmt_norm)
            # Basic sanity
            if dt.year < 1950 or dt.year > 2100:
                continue
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.warning("Could not parse date: %r", raw)
    return raw  # return unchanged – validator will flag it


def _digit_sum_mod10(patti: str) -> int:
    return sum(int(d) for d in patti) % 10


def _zero_pad(val: Optional[str], width: int) -> Optional[str]:
    """Zero-pad a numeric string to *width* digits."""
    if val is None:
        return None
    val = val.strip()
    if not val:
        return None
    # Strip non-digit characters
    digits = re.sub(r"\D", "", val)
    if not digits:
        return None
    return digits.zfill(width)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalise a list of parsed Matka result records.

    Operations performed (in order):
    1. Strip whitespace from all string values.
    2. Zero-pad ``open_patti`` / ``close_patti`` to 3 digits, ``jodi`` to 2.
    3. Calculate missing derived fields:
       - ``open_ank`` from ``open_patti`` (digit sum mod 10)
       - ``close_ank`` from ``close_patti``
       - ``jodi`` from ``open_ank`` + ``close_ank``
    4. Normalise all dates to ``YYYY-MM-DD``.
    5. Remove completely empty records.
    6. Sort by date ascending (nulls last).

    Parameters
    ----------
    records : list[dict]
        Raw parsed records.

    Returns
    -------
    list[dict]
        Normalised records.
    """
    if not records:
        return []

    # Detect prevalent date format from samples
    date_samples = [str(r.get("date", "")) for r in records if r.get("date")]
    detected_fmt = detect_date_format(date_samples) if date_samples else None

    normalised: list[dict] = []

    for rec in records:
        # Deep copy so we don't mutate the originals
        out: Dict[str, Any] = {
            "date": None,
            "open_patti": None,
            "open_ank": None,
            "jodi": None,
            "close_ank": None,
            "close_patti": None,
            "market_name": rec.get("market_name"),
        }

        # --- Strip & pad ---
        raw_date = rec.get("date")
        if raw_date and isinstance(raw_date, str):
            out["date"] = _parse_date_to_iso(raw_date.strip(), detected_fmt)

        out["open_patti"] = _zero_pad(str(rec["open_patti"]) if rec.get("open_patti") is not None else None, 3)
        out["close_patti"] = _zero_pad(str(rec["close_patti"]) if rec.get("close_patti") is not None else None, 3)
        out["jodi"] = _zero_pad(str(rec["jodi"]) if rec.get("jodi") is not None else None, 2)

        # Open ank
        raw_oa = rec.get("open_ank")
        if raw_oa is not None:
            try:
                out["open_ank"] = int(raw_oa)
            except (ValueError, TypeError):
                out["open_ank"] = None
        # Close ank
        raw_ca = rec.get("close_ank")
        if raw_ca is not None:
            try:
                out["close_ank"] = int(raw_ca)
            except (ValueError, TypeError):
                out["close_ank"] = None

        # --- Derive missing fields ---
        # open_ank from open_patti
        if out["open_ank"] is None and out["open_patti"] and re.match(r"^\d{3}$", out["open_patti"]):
            out["open_ank"] = _digit_sum_mod10(out["open_patti"])

        # close_ank from close_patti
        if out["close_ank"] is None and out["close_patti"] and re.match(r"^\d{3}$", out["close_patti"]):
            out["close_ank"] = _digit_sum_mod10(out["close_patti"])

        # jodi from open_ank + close_ank
        if out["jodi"] is None and out["open_ank"] is not None and out["close_ank"] is not None:
            out["jodi"] = f"{out['open_ank']}{out['close_ank']}"

        # --- Discard empty records ---
        has_data = any(
            out[f] is not None
            for f in ("open_patti", "open_ank", "jodi", "close_ank", "close_patti")
        )
        if has_data:
            normalised.append(out)

    # --- Sort by date ascending (None last) ---
    def _sort_key(r: dict) -> str:
        d = r.get("date")
        return d if d else "9999-99-99"

    normalised.sort(key=_sort_key)

    logger.info("Normalised %d records (from %d raw)", len(normalised), len(records))
    return normalised
