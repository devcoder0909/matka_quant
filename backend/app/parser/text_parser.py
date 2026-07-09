"""
Matka Quantum AI - Plain-Text Data Parser
==========================================

Parses Satta Matka result data from raw text (e.g. tab-separated pastes,
compact "123-65-357" per line, "Date: 09-07-2026 Result: 123-65-357", etc.).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Regex patterns
RE_5PART = re.compile(
    r"(\d{3})\s*[-–—]\s*(\d)\s*[-–—]?\s*(\d{2})\s*[-–—]?\s*(\d)\s*[-–—]\s*(\d{3})"
)
RE_3PART = re.compile(r"(\d{3})\s*[-–—]\s*(\d{2})\s*[-–—]\s*(\d{3})")
RE_DATE = re.compile(
    r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})"
)
RE_LABELED = re.compile(
    r"(?:date|dt)\s*[:=]\s*(\S+)\s+(?:result|res)\s*[:=]\s*(.+)",
    re.IGNORECASE,
)


def _digit_sum_mod10(patti: str) -> int:
    return sum(int(d) for d in patti) % 10


def _empty_record(market_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "date": None,
        "open_patti": None,
        "open_ank": None,
        "jodi": None,
        "close_ank": None,
        "close_patti": None,
        "market_name": market_name,
    }


def _try_tab_separated(line: str, market_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Try to parse a tab-or-multi-space-separated line."""
    parts = re.split(r"\t+|\s{2,}", line.strip())
    if len(parts) < 2:
        return None

    record = _empty_record(market_name)

    # 6-column: date, open_patti, open_ank, jodi, close_ank, close_patti
    if len(parts) >= 6:
        record["date"] = parts[0].strip()
        record["open_patti"] = parts[1].strip()
        try:
            record["open_ank"] = int(parts[2].strip())
        except ValueError:
            pass
        record["jodi"] = parts[3].strip()
        try:
            record["close_ank"] = int(parts[4].strip())
        except ValueError:
            pass
        record["close_patti"] = parts[5].strip()
        return record

    # 4-column: date, open_patti, jodi, close_patti
    if len(parts) >= 4:
        record["date"] = parts[0].strip()
        record["open_patti"] = parts[1].strip()
        record["jodi"] = parts[2].strip()
        record["close_patti"] = parts[3].strip()
        if record["open_patti"] and re.match(r"^\d{3}$", record["open_patti"]):
            record["open_ank"] = _digit_sum_mod10(record["open_patti"])
        if record["close_patti"] and re.match(r"^\d{3}$", record["close_patti"]):
            record["close_ank"] = _digit_sum_mod10(record["close_patti"])
        return record

    # 2-column: date, result
    if len(parts) == 2:
        date_candidate = parts[0].strip()
        result_candidate = parts[1].strip()
        if RE_DATE.match(date_candidate):
            record["date"] = date_candidate
            m5 = RE_5PART.search(result_candidate)
            m3 = RE_3PART.search(result_candidate)
            if m5:
                record["open_patti"] = m5.group(1)
                record["open_ank"] = int(m5.group(2))
                record["jodi"] = m5.group(3)
                record["close_ank"] = int(m5.group(4))
                record["close_patti"] = m5.group(5)
                return record
            elif m3:
                record["open_patti"] = m3.group(1)
                record["jodi"] = m3.group(2)
                record["close_patti"] = m3.group(3)
                record["open_ank"] = _digit_sum_mod10(m3.group(1))
                record["close_ank"] = _digit_sum_mod10(m3.group(3))
                return record

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_text_data(text: str) -> List[Dict[str, Any]]:
    """
    Parse Satta Matka result data from raw text.

    Supported formats:
    - Compact ``123-65-357`` per line (with or without date prefix)
    - Five-part ``123-6-65-5-357`` per line
    - ``Date: DD-MM-YYYY  Result: 123-65-357``
    - Tab-separated or multi-space-separated columns
    - Regex-based fallback for any line with digit patterns

    Parameters
    ----------
    text : str
        Raw text to parse.

    Returns
    -------
    list[dict]
        Parsed records in the standard format.
    """
    if not text or not text.strip():
        logger.warning("Empty text input received")
        return []

    # Try to detect market from the whole text
    market_name: Optional[str] = None
    try:
        from backend.app.parser.detector import detect_market
        code = detect_market([], text)
        if code != "UNKNOWN":
            market_name = code
    except ImportError:
        pass

    records: list[dict] = []
    lines = text.strip().splitlines()

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # --- 1. Labeled format: "Date: ... Result: ..." ---
        m_lab = RE_LABELED.match(line_stripped)
        if m_lab:
            date_str = m_lab.group(1)
            result_str = m_lab.group(2)
            record = _empty_record(market_name)
            record["date"] = date_str

            m5 = RE_5PART.search(result_str)
            m3 = RE_3PART.search(result_str)
            if m5:
                record["open_patti"] = m5.group(1)
                record["open_ank"] = int(m5.group(2))
                record["jodi"] = m5.group(3)
                record["close_ank"] = int(m5.group(4))
                record["close_patti"] = m5.group(5)
                records.append(record)
                continue
            elif m3:
                record["open_patti"] = m3.group(1)
                record["jodi"] = m3.group(2)
                record["close_patti"] = m3.group(3)
                record["open_ank"] = _digit_sum_mod10(m3.group(1))
                record["close_ank"] = _digit_sum_mod10(m3.group(3))
                records.append(record)
                continue

        # --- 2. Five-part on this line ---
        m5 = RE_5PART.search(line_stripped)
        if m5:
            record = _empty_record(market_name)
            record["open_patti"] = m5.group(1)
            record["open_ank"] = int(m5.group(2))
            record["jodi"] = m5.group(3)
            record["close_ank"] = int(m5.group(4))
            record["close_patti"] = m5.group(5)
            # Try to find a date before the match
            prefix = line_stripped[:m5.start()]
            dm = RE_DATE.search(prefix)
            if dm:
                record["date"] = dm.group(1)
            records.append(record)
            continue

        # --- 3. Three-part on this line ---
        m3 = RE_3PART.search(line_stripped)
        if m3:
            record = _empty_record(market_name)
            record["open_patti"] = m3.group(1)
            record["jodi"] = m3.group(2)
            record["close_patti"] = m3.group(3)
            record["open_ank"] = _digit_sum_mod10(m3.group(1))
            record["close_ank"] = _digit_sum_mod10(m3.group(3))
            prefix = line_stripped[:m3.start()]
            dm = RE_DATE.search(prefix)
            if dm:
                record["date"] = dm.group(1)
            records.append(record)
            continue

        # --- 4. Tab/space separated ---
        rec = _try_tab_separated(line_stripped, market_name)
        if rec and (rec.get("open_patti") or rec.get("jodi") or rec.get("close_patti")):
            records.append(rec)
            continue

        # --- 5. Skip non-data lines (headers, labels, etc.) ---
        logger.debug("Skipped unrecognised line: %s", line_stripped[:80])

    logger.info("Parsed %d records from text", len(records))
    return records
