"""
Matka Quantum AI - Frequency Intelligence Module
==================================================

Analyses digit, jodi, and patti frequencies over multiple rolling windows.
Computes z-scores, hot/cold classification, overdue analysis, and frequency
acceleration/decay trends.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Rolling window sizes (in days)
WINDOWS: list[int] = [7, 14, 21, 30, 50, 90, 180]
# Z-score thresholds for classification
Z_HOT = 1.5
Z_COLD = -1.5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filter_by_window(
    records: List[Dict[str, Any]],
    target_date: datetime,
    window_days: int,
) -> List[Dict[str, Any]]:
    """Return records within [target_date - window_days, target_date)."""
    cutoff = target_date - timedelta(days=window_days)
    filtered: list[dict] = []
    for rec in records:
        d = rec.get("date")
        if not d:
            continue
        try:
            dt = datetime.strptime(str(d), "%Y-%m-%d")
        except ValueError:
            continue
        if cutoff <= dt < target_date:
            filtered.append(rec)
    return filtered


def _count_values(records: List[Dict[str, Any]], field: str) -> Counter:
    """Count occurrences of each value in *field*."""
    counter: Counter = Counter()
    for rec in records:
        v = rec.get(field)
        if v is not None:
            counter[str(v)] += 1
    return counter


def _z_score(observed: int, expected: float, n: int) -> float:
    """
    Compute z-score for a binomial proportion test.

    z = (observed - expected) / sqrt(expected * (1 - p))  where p = 1/k
    Simplified: z = (observed - expected) / sqrt(n * p * (1 - p))
    """
    if n == 0:
        return 0.0
    p = expected / n if n > 0 else 0
    variance = n * p * (1 - p)
    if variance <= 0:
        return 0.0
    return (observed - expected) / math.sqrt(variance)


def _classify(z: float) -> str:
    """Classify a z-score into HOT, COLD, or NORMAL."""
    if z >= Z_HOT:
        return "HOT"
    elif z <= Z_COLD:
        return "COLD"
    return "NORMAL"


def _overdue_analysis(
    records: List[Dict[str, Any]],
    field: str,
    value: str,
    target_date: datetime,
) -> Dict[str, Any]:
    """
    Compute overdue statistics for a specific value.

    Returns dict with ``days_since_last``, ``average_gap``, ``max_gap``,
    ``is_overdue`` (current gap > average_gap * 1.5).
    """
    # Find all dates where value appeared
    appearance_dates: list[datetime] = []
    for rec in records:
        if str(rec.get(field, "")) == value:
            d = rec.get("date")
            if d:
                try:
                    appearance_dates.append(datetime.strptime(str(d), "%Y-%m-%d"))
                except ValueError:
                    continue

    appearance_dates.sort()

    if not appearance_dates:
        return {
            "days_since_last": None,
            "average_gap": None,
            "max_gap": None,
            "is_overdue": False,
            "total_appearances": 0,
        }

    days_since = (target_date - appearance_dates[-1]).days

    # Calculate gaps
    gaps: list[int] = []
    for i in range(1, len(appearance_dates)):
        gaps.append((appearance_dates[i] - appearance_dates[i - 1]).days)

    avg_gap = sum(gaps) / len(gaps) if gaps else float(days_since)
    max_gap = max(gaps) if gaps else days_since

    return {
        "days_since_last": days_since,
        "average_gap": round(avg_gap, 2),
        "max_gap": max_gap,
        "is_overdue": days_since > avg_gap * 1.5 if avg_gap > 0 else False,
        "total_appearances": len(appearance_dates),
    }


def _frequency_acceleration(
    records: List[Dict[str, Any]],
    field: str,
    value: str,
    target_date: datetime,
) -> Dict[str, float]:
    """
    Compare recent-window frequency to longer-window frequency.

    Returns ``acceleration`` > 0 for trending-up, < 0 for trending-down.
    """
    short_recs = _filter_by_window(records, target_date, 14)
    long_recs = _filter_by_window(records, target_date, 90)

    short_count = sum(1 for r in short_recs if str(r.get(field, "")) == value)
    long_count = sum(1 for r in long_recs if str(r.get(field, "")) == value)

    short_n = max(len(short_recs), 1)
    long_n = max(len(long_recs), 1)

    short_freq = short_count / short_n
    long_freq = long_count / long_n

    acceleration = short_freq - long_freq

    return {
        "short_window_freq": round(short_freq, 6),
        "long_window_freq": round(long_freq, 6),
        "acceleration": round(acceleration, 6),
        "trend": "ACCELERATING" if acceleration > 0.01 else ("DECAYING" if acceleration < -0.01 else "STABLE"),
    }


# ---------------------------------------------------------------------------
# Per-field analysis
# ---------------------------------------------------------------------------

def _analyze_field(
    all_records: List[Dict[str, Any]],
    field: str,
    possible_values: List[str],
    target_date: datetime,
) -> Dict[str, Any]:
    """
    Full frequency analysis for a single field across all rolling windows.
    """
    num_possible = len(possible_values)
    result: Dict[str, Any] = {
        "by_value": {},
        "windows": {},
    }

    # Full history
    full_counts = _count_values(all_records, field)
    full_n = sum(full_counts.values())

    for val in possible_values:
        val_str = str(val)
        overdue = _overdue_analysis(all_records, field, val_str, target_date)
        accel = _frequency_acceleration(all_records, field, val_str, target_date)

        result["by_value"][val_str] = {
            "full_history": {
                "count": full_counts.get(val_str, 0),
                "total": full_n,
                "frequency": round(full_counts.get(val_str, 0) / max(full_n, 1), 6),
                "expected_frequency": round(1 / num_possible, 6),
            },
            "overdue": overdue,
            "acceleration": accel,
        }

    # Per-window analysis
    for window in WINDOWS:
        w_recs = _filter_by_window(all_records, target_date, window)
        w_counts = _count_values(w_recs, field)
        w_n = sum(w_counts.values())
        expected_per_value = w_n / num_possible if num_possible > 0 else 0

        window_data: dict[str, dict] = {}
        for val in possible_values:
            val_str = str(val)
            count = w_counts.get(val_str, 0)
            freq = count / max(w_n, 1)
            expected_freq = 1 / num_possible
            deviation = freq - expected_freq
            z = _z_score(count, expected_per_value, w_n)
            classification = _classify(z)

            window_data[val_str] = {
                "count": count,
                "total": w_n,
                "frequency": round(freq, 6),
                "expected_frequency": round(expected_freq, 6),
                "deviation": round(deviation, 6),
                "z_score": round(z, 4),
                "classification": classification,
            }

        result["windows"][f"{window}d"] = {
            "window_days": window,
            "record_count": len(w_recs),
            "total_observations": w_n,
            "values": window_data,
        }

    # Also add full history as a window
    expected_per_value_full = full_n / num_possible if num_possible > 0 else 0
    full_window_data: dict[str, dict] = {}
    for val in possible_values:
        val_str = str(val)
        count = full_counts.get(val_str, 0)
        freq = count / max(full_n, 1)
        expected_freq = 1 / num_possible
        z = _z_score(count, expected_per_value_full, full_n)
        full_window_data[val_str] = {
            "count": count,
            "total": full_n,
            "frequency": round(freq, 6),
            "expected_frequency": round(expected_freq, 6),
            "deviation": round(freq - expected_freq, 6),
            "z_score": round(z, 4),
            "classification": _classify(z),
        }
    result["windows"]["full"] = {
        "window_days": None,
        "record_count": len(all_records),
        "total_observations": full_n,
        "values": full_window_data,
    }

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_frequencies(
    records: List[Dict[str, Any]],
    target_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform comprehensive frequency analysis on Matka result records.

    Analyses digit frequencies for ``open_ank`` (0-9), ``close_ank`` (0-9),
    ``jodi`` (00-99), and ``open_patti`` / ``close_patti`` (top-N).

    For each value in each rolling window, computes raw count, frequency
    percentage, expected frequency (uniform baseline), deviation, z-score,
    and HOT / COLD / NORMAL classification.

    Also computes overdue analysis and frequency acceleration/decay.

    Parameters
    ----------
    records : list[dict]
        Normalised, validated historical records.
    target_date : str, optional
        Analysis target date in YYYY-MM-DD.  Defaults to today.

    Returns
    -------
    dict
        Nested structure with keys ``open_ank``, ``close_ank``, ``jodi``,
        ``open_patti``, ``close_patti``, ``meta``.
    """
    if target_date:
        try:
            t_dt = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            t_dt = datetime.now()
    else:
        t_dt = datetime.now()

    # Ensure records are sorted and before target date
    valid_records: list[dict] = []
    for rec in records:
        d = rec.get("date")
        if d:
            try:
                dt = datetime.strptime(str(d), "%Y-%m-%d")
                if dt < t_dt:
                    valid_records.append(rec)
            except ValueError:
                valid_records.append(rec)
        else:
            valid_records.append(rec)

    # Possible values
    ank_values = [str(i) for i in range(10)]
    jodi_values = [f"{i:02d}" for i in range(100)]

    # Patti: use only the values that have appeared (up to 1000)
    patti_counter_open = _count_values(valid_records, "open_patti")
    patti_counter_close = _count_values(valid_records, "close_patti")
    # Top patti values (those that actually appeared)
    open_patti_values = sorted(patti_counter_open.keys())
    close_patti_values = sorted(patti_counter_close.keys())

    logger.info("Running frequency analysis on %d records (target=%s)", len(valid_records), t_dt.strftime("%Y-%m-%d"))

    result: Dict[str, Any] = {
        "open_ank": _analyze_field(valid_records, "open_ank", ank_values, t_dt),
        "close_ank": _analyze_field(valid_records, "close_ank", ank_values, t_dt),
        "jodi": _analyze_field(valid_records, "jodi", jodi_values, t_dt),
        "meta": {
            "target_date": t_dt.strftime("%Y-%m-%d"),
            "total_records": len(valid_records),
            "windows": WINDOWS + ["full"],
            "z_hot_threshold": Z_HOT,
            "z_cold_threshold": Z_COLD,
        },
    }

    # Patti analysis (only top-N to keep result size manageable)
    if open_patti_values:
        result["open_patti"] = _analyze_field(
            valid_records, "open_patti",
            open_patti_values[:220] if len(open_patti_values) > 220 else open_patti_values,
            t_dt,
        )
    if close_patti_values:
        result["close_patti"] = _analyze_field(
            valid_records, "close_patti",
            close_patti_values[:220] if len(close_patti_values) > 220 else close_patti_values,
            t_dt,
        )

    return result
