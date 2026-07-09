"""
Matka Quantum AI - Ensemble Scoring (Phase 1: Frequency-Only)
==============================================================

Combines frequency-analysis signals into a single normalised score for each
candidate (ank, jodi).  Architecture is extensible — additional modules
(pattern, cyclical, etc.) plug in as extra score contributors.

**Responsible-language policy**: no candidate is ever labelled "High Confidence",
"Guaranteed", "Sure Shot", or any similar term.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Confidence labels (strictly capped)
# ---------------------------------------------------------------------------
_CONFIDENCE_TIERS: list[tuple[float, str]] = [
    (0,  "Insufficient Data"),
    (15, "Very Low"),
    (30, "Low"),
    (50, "Experimental"),
    (70, "Moderate Statistical Signal"),
    # Intentionally nothing above — we NEVER claim high confidence
]


def _confidence_label(score: float, data_points: int) -> str:
    """Map a normalised score to a responsible confidence label."""
    if data_points < 10:
        return "Insufficient Data"
    label = "Insufficient Data"
    for threshold, lbl in _CONFIDENCE_TIERS:
        if score >= threshold:
            label = lbl
    return label


# ---------------------------------------------------------------------------
# Score calculators per module
# ---------------------------------------------------------------------------

def _frequency_score_for_value(
    freq_data: Dict[str, Any],
    value: str,
    data_field: str,
) -> Dict[str, Any]:
    """
    Calculate a frequency-based score for a single candidate value.

    Signals used:
    - Recent window (7d, 14d) z-scores → hot/overdue signals
    - Overdue bonus (if overdue, small bump for "due" effect)
    - Acceleration trend
    - Full-history deviation

    Returns dict with ``raw_score``, ``explanation``.
    """
    by_value = freq_data.get("by_value", {})
    windows = freq_data.get("windows", {})

    val_info = by_value.get(value, {})
    overdue_info = val_info.get("overdue", {})
    accel_info = val_info.get("acceleration", {})

    raw_score = 50.0  # neutral baseline
    explanation: dict[str, Any] = {}

    # --- Window z-score contributions ---
    window_keys = ["7d", "14d", "30d", "full"]
    window_weights = [0.35, 0.25, 0.20, 0.20]

    z_component = 0.0
    for wk, wt in zip(window_keys, window_weights):
        w_data = windows.get(wk, {}).get("values", {}).get(value, {})
        z = w_data.get("z_score", 0.0)
        # Clamp z-score contribution
        clamped = max(-3.0, min(3.0, z))
        z_component += clamped * wt

    # Map z-component (roughly -3 to +3) onto a 0-40 range centred at 20
    z_mapped = 20 + (z_component / 3.0) * 20
    z_mapped = max(0, min(40, z_mapped))
    raw_score = z_mapped
    explanation["frequency_z_contribution"] = round(z_mapped, 2)

    # --- Overdue bonus ---
    overdue_bonus = 0.0
    if overdue_info.get("is_overdue") and overdue_info.get("days_since_last") is not None:
        avg_gap = overdue_info.get("average_gap", 1)
        if avg_gap > 0:
            overdue_ratio = overdue_info["days_since_last"] / avg_gap
            overdue_bonus = min(15.0, (overdue_ratio - 1.0) * 5.0)
            overdue_bonus = max(0.0, overdue_bonus)
    raw_score += overdue_bonus
    explanation["overdue_bonus"] = round(overdue_bonus, 2)

    # --- Acceleration bonus ---
    accel_bonus = 0.0
    trend = accel_info.get("trend", "STABLE")
    accel_val = accel_info.get("acceleration", 0.0)
    if trend == "ACCELERATING":
        accel_bonus = min(10.0, abs(accel_val) * 100)
    elif trend == "DECAYING":
        accel_bonus = -min(5.0, abs(accel_val) * 50)
    raw_score += accel_bonus
    explanation["acceleration_bonus"] = round(accel_bonus, 2)
    explanation["trend"] = trend

    # --- Full-history deviation ---
    full_vals = windows.get("full", {}).get("values", {}).get(value, {})
    full_deviation = full_vals.get("deviation", 0.0)
    hist_bonus = full_deviation * 100  # scale small deviations
    hist_bonus = max(-10, min(10, hist_bonus))
    raw_score += hist_bonus
    explanation["history_deviation_bonus"] = round(hist_bonus, 2)

    # Clamp final raw score
    raw_score = max(0.0, min(100.0, raw_score))

    # Appearance data
    total_appearances = overdue_info.get("total_appearances", 0)
    full_hist = by_value.get(value, {}).get("full_history", {})
    explanation["full_count"] = full_hist.get("count", 0)
    explanation["full_frequency"] = full_hist.get("frequency", 0.0)

    return {
        "raw_score": round(raw_score, 2),
        "total_appearances": total_appearances,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_ensemble_scores(
    frequency_results: Dict[str, Any],
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Calculate ensemble scores for all candidate values using frequency signals.

    Phase 1 uses frequency analysis only.  The architecture supports adding
    more modules (pattern, cyclical, ML) by extending the score calculation.

    Parameters
    ----------
    frequency_results : dict
        Output of ``analyze_frequencies()``.
    records : list[dict]
        The historical records used for analysis.

    Returns
    -------
    list[dict]
        Sorted list of candidate dicts (highest score first), each containing:
        - ``type``: ``'ank'`` or ``'jodi'``
        - ``field``: ``'open_ank'``, ``'close_ank'``, ``'jodi'``
        - ``value``: the candidate value
        - ``score``: normalised 0-100
        - ``probability``: observed frequency
        - ``baseline``: uniform expected probability
        - ``confidence``: responsible label
        - ``explanation``: dict of score breakdown
    """
    candidates: list[dict] = []
    total_records = len(records)

    # --- Ank candidates (open_ank, close_ank) ---
    for field_name in ("open_ank", "close_ank"):
        freq_data = frequency_results.get(field_name, {})
        if not freq_data:
            continue

        for val in [str(i) for i in range(10)]:
            score_info = _frequency_score_for_value(freq_data, val, field_name)
            full_hist = freq_data.get("by_value", {}).get(val, {}).get("full_history", {})

            candidates.append({
                "type": "ank",
                "field": field_name,
                "value": val,
                "score": score_info["raw_score"],
                "probability": full_hist.get("frequency", 0.0),
                "baseline": round(1 / 10, 6),
                "confidence": _confidence_label(score_info["raw_score"], total_records),
                "explanation": {
                    "frequency": score_info["explanation"],
                    "modules_used": ["frequency"],
                },
            })

    # --- Jodi candidates (00-99) ---
    jodi_data = frequency_results.get("jodi", {})
    if jodi_data:
        for val in [f"{i:02d}" for i in range(100)]:
            score_info = _frequency_score_for_value(jodi_data, val, "jodi")
            full_hist = jodi_data.get("by_value", {}).get(val, {}).get("full_history", {})

            candidates.append({
                "type": "jodi",
                "field": "jodi",
                "value": val,
                "score": score_info["raw_score"],
                "probability": full_hist.get("frequency", 0.0),
                "baseline": round(1 / 100, 6),
                "confidence": _confidence_label(score_info["raw_score"], total_records),
                "explanation": {
                    "frequency": score_info["explanation"],
                    "modules_used": ["frequency"],
                },
            })

    # Sort by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Sanity: ensure no forbidden labels
    forbidden = {"high confidence", "guaranteed", "sure shot", "certain", "definite"}
    for c in candidates:
        if c["confidence"].lower() in forbidden:
            c["confidence"] = "Moderate Statistical Signal"

    logger.info(
        "Ensemble scoring complete: %d candidates generated (top score=%.1f)",
        len(candidates),
        candidates[0]["score"] if candidates else 0,
    )
    return candidates
