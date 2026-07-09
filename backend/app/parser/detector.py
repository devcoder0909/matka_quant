"""
Matka Quantum AI - Market & Date-Format Detector
==================================================

Detects the Satta Matka market name from text and auto-detects date formats.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Market detection
# ---------------------------------------------------------------------------

# Maps regex pattern -> standardised market code.
# Patterns are checked in order; first match wins.
_MARKET_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bkalyan\b", re.IGNORECASE), "KALYAN"),
    (re.compile(r"\bmain\s*baz[a]*[r]+\b", re.IGNORECASE), "MAIN_BAZAR"),
    (re.compile(r"\bmilan\s*day\b", re.IGNORECASE), "MILAN_DAY"),
    (re.compile(r"\bmilan\s*night\b", re.IGNORECASE), "MILAN_NIGHT"),
    (re.compile(r"\brajdhani\s*day\b", re.IGNORECASE), "RAJDHANI_DAY"),
    (re.compile(r"\brajdhani\s*night\b", re.IGNORECASE), "RAJDHANI_NIGHT"),
    (re.compile(r"\btime\s*baz[a]*[r]+\b", re.IGNORECASE), "TIME_BAZAR"),
    (re.compile(r"\bmadhur\s*day\b", re.IGNORECASE), "MADHUR_DAY"),
    (re.compile(r"\bmadhur\s*night\b", re.IGNORECASE), "MADHUR_NIGHT"),
    (re.compile(r"\bsridevi\b", re.IGNORECASE), "SRIDEVI"),
    (re.compile(r"\bsupreme\b", re.IGNORECASE), "SUPREME"),
    # Generic fallbacks (after specific variants)
    (re.compile(r"\bmilan\b", re.IGNORECASE), "MILAN_DAY"),
    (re.compile(r"\brajdhani\b", re.IGNORECASE), "RAJDHANI_DAY"),
    (re.compile(r"\bmadhur\b", re.IGNORECASE), "MADHUR_DAY"),
]


def detect_market(records: List[Dict[str, Any]], raw_input: str = "") -> str:
    """
    Detect the Satta Matka market name.

    First searches ``raw_input`` for known market-name keywords.  If that
    fails, searches the ``market_name`` field already present on *records*.

    Parameters
    ----------
    records : list[dict]
        Parsed records (may contain ``market_name`` keys).
    raw_input : str
        Any raw text that might contain the market name (HTML, filename, etc.).

    Returns
    -------
    str
        Standardised market code (e.g. ``'KALYAN'``, ``'MAIN_BAZAR'``).
        Returns ``'UNKNOWN'`` if detection fails.
    """
    # 1. Check raw input text
    if raw_input:
        for pattern, code in _MARKET_PATTERNS:
            if pattern.search(raw_input):
                logger.debug("Market detected from raw input: %s", code)
                return code

    # 2. Check market_name fields on records
    for rec in records:
        mn = rec.get("market_name")
        if mn:
            mn_str = str(mn)
            for pattern, code in _MARKET_PATTERNS:
                if pattern.search(mn_str):
                    logger.debug("Market detected from record field: %s", code)
                    return code

    logger.debug("Market not detected, returning UNKNOWN")
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Date format detection
# ---------------------------------------------------------------------------

_DATE_FORMATS: list[str] = [
    "%d-%m-%Y",   # 09-07-2026
    "%d/%m/%Y",   # 09/07/2026
    "%d.%m.%Y",   # 09.07.2026
    "%d-%m-%y",   # 09-07-26
    "%d/%m/%y",   # 09/07/26
    "%Y-%m-%d",   # 2026-07-09
    "%Y/%m/%d",   # 2026/07/09
    "%m-%d-%Y",   # 07-09-2026  (US format)
    "%m/%d/%Y",   # 07/09/2026
]


def detect_date_format(date_strings: List[str]) -> str:
    """
    Detect the most likely date format from a list of date strings.

    Tries every known format against every input string; the format that
    successfully parses the most strings wins.  In case of a tie, the
    format that appears first in the priority list is preferred.

    Parameters
    ----------
    date_strings : list[str]
        Sample date strings to analyse.

    Returns
    -------
    str
        The best-matching ``strftime``/``strptime`` format string.
        Defaults to ``'%d-%m-%Y'`` if nothing matches.
    """
    if not date_strings:
        return "%d-%m-%Y"

    # Filter out empty / None values
    samples = [s.strip() for s in date_strings if s and s.strip()]
    if not samples:
        return "%d-%m-%Y"

    # Normalise separators for matching
    def _norm(s: str) -> str:
        return s.replace("/", "-").replace(".", "-")

    scores: Counter[str] = Counter()
    for fmt in _DATE_FORMATS:
        fmt_norm = fmt.replace("/", "-").replace(".", "-")
        for s in samples:
            s_norm = _norm(s)
            try:
                dt = datetime.strptime(s_norm, fmt_norm)
                # Sanity checks: day 1-31, month 1-12
                if 1 <= dt.month <= 12 and 1 <= dt.day <= 31:
                    scores[fmt] += 1
            except ValueError:
                continue

    if not scores:
        logger.warning("Could not detect date format; defaulting to %%d-%%m-%%Y")
        return "%d-%m-%Y"

    # Return the format with the highest score (ties broken by priority order)
    best_score = max(scores.values())
    for fmt in _DATE_FORMATS:
        if scores.get(fmt, 0) == best_score:
            logger.debug("Detected date format: %s (score=%d/%d)", fmt, best_score, len(samples))
            return fmt

    return "%d-%m-%Y"
