"""
Matka Quantum AI - CSV Data Parser
====================================

Parses Satta Matka result data from CSV/TSV files with automatic delimiter,
encoding, and header detection.
"""

from __future__ import annotations

import csv
import io
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Regex patterns reused from html_parser
RE_5PART = re.compile(
    r"(\d{3})\s*[-–—]\s*(\d)\s*[-–—]?\s*(\d{2})\s*[-–—]?\s*(\d)\s*[-–—]\s*(\d{3})"
)
RE_3PART = re.compile(r"(\d{3})\s*[-–—]\s*(\d{2})\s*[-–—]\s*(\d{3})")

# ---------------------------------------------------------------------------
# Header keyword mapping (fuzzy)
# ---------------------------------------------------------------------------
_HEADER_KEYWORDS: dict[str, list[str]] = {
    "date": ["date", "dt", "day", "तारीख", "दिनांक"],
    "open_patti": ["open patti", "open panel", "open_patti", "opatti", "op"],
    "open_ank": ["open ank", "open digit", "open_ank", "oank", "oa"],
    "jodi": ["jodi", "jd", "pair"],
    "close_ank": ["close ank", "close digit", "close_ank", "cank", "ca"],
    "close_patti": ["close patti", "close panel", "close_patti", "cpatti", "cp"],
}


def _digit_sum_mod10(patti: str) -> int:
    return sum(int(d) for d in patti) % 10


def _detect_encoding(raw: bytes) -> str:
    """Detect the most likely text encoding for *raw* bytes."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, ValueError):
            continue
    return "latin-1"  # safe fallback


def _detect_delimiter(sample_text: str) -> str:
    """Detect the most common delimiter in the first few lines."""
    candidates = {",": 0, "\t": 0, ";": 0, "|": 0}
    for line in sample_text.splitlines()[:10]:
        for delim in candidates:
            candidates[delim] += line.count(delim)
    best = max(candidates, key=candidates.get)  # type: ignore[arg-type]
    if candidates[best] == 0:
        return ","
    return best


def _fuzzy_match_header(header: str) -> Optional[str]:
    """Match a header string to a standard field name."""
    h = header.strip().lower().replace("_", " ").replace("-", " ")
    for field, keywords in _HEADER_KEYWORDS.items():
        for kw in keywords:
            if kw == h or kw in h:
                return field
    return None


def _map_headers(headers: list[str]) -> Dict[str, int]:
    """Map header labels to column indices."""
    mapping: Dict[str, int] = {}
    for idx, h in enumerate(headers):
        field = _fuzzy_match_header(h)
        if field and field not in mapping:
            mapping[field] = idx
    return mapping


def _positional_mapping(num_cols: int) -> Dict[str, int]:
    """
    Fallback column mapping when no headers are present.

    Assumes common orderings:
        5 cols: date, open_patti, jodi, close_patti, (extra)
        6 cols: date, open_patti, open_ank, jodi, close_ank, close_patti
    """
    if num_cols >= 6:
        return {
            "date": 0,
            "open_patti": 1,
            "open_ank": 2,
            "jodi": 3,
            "close_ank": 4,
            "close_patti": 5,
        }
    if num_cols >= 4:
        return {
            "date": 0,
            "open_patti": 1,
            "jodi": 2,
            "close_patti": 3,
        }
    if num_cols >= 2:
        return {"date": 0, "jodi": 1}
    return {}


def _is_header_row(row: list[str]) -> bool:
    """Heuristic: if any cell fuzzy-matches a known header keyword it's a header row."""
    matches = sum(1 for c in row if _fuzzy_match_header(c) is not None)
    return matches >= 2


def _row_to_record(row: list[str], col_map: Dict[str, int], market_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Convert a CSV row to a record dict using the provided column mapping."""
    record: Dict[str, Any] = {
        "date": None,
        "open_patti": None,
        "open_ank": None,
        "jodi": None,
        "close_ank": None,
        "close_patti": None,
        "market_name": market_name,
    }

    for field, idx in col_map.items():
        if idx >= len(row):
            continue
        val = row[idx].strip()
        if not val or val in ("*", "**", "***", "XX", "---", "NA", "N/A"):
            continue
        if field in ("open_ank", "close_ank"):
            try:
                record[field] = int(val)
            except ValueError:
                pass
        else:
            record[field] = val

    # Try to extract result from any cell with regex
    if record["open_patti"] is None and record["jodi"] is None:
        full_row_text = " ".join(row)
        m5 = RE_5PART.search(full_row_text)
        m3 = RE_3PART.search(full_row_text)
        if m5:
            record["open_patti"] = m5.group(1)
            record["open_ank"] = int(m5.group(2))
            record["jodi"] = m5.group(3)
            record["close_ank"] = int(m5.group(4))
            record["close_patti"] = m5.group(5)
        elif m3:
            record["open_patti"] = m3.group(1)
            record["jodi"] = m3.group(2)
            record["close_patti"] = m3.group(3)
            record["open_ank"] = _digit_sum_mod10(m3.group(1))
            record["close_ank"] = _digit_sum_mod10(m3.group(3))

    if record["open_patti"] or record["jodi"] or record["close_patti"]:
        return record
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_csv_data(file_content: bytes, filename: str = "") -> List[Dict[str, Any]]:
    """
    Parse Satta Matka result data from CSV bytes.

    Parameters
    ----------
    file_content : bytes
        Raw file content.
    filename : str, optional
        Original filename (used for market-name heuristics).

    Returns
    -------
    list[dict]
        Parsed records in the standard format.
    """
    if not file_content:
        logger.warning("Empty CSV content received")
        return []

    encoding = _detect_encoding(file_content)
    text = file_content.decode(encoding, errors="replace")
    # Remove BOM if present
    text = text.lstrip("\ufeff")

    delimiter = _detect_delimiter(text)
    logger.debug("Detected encoding=%s, delimiter=%r", encoding, delimiter)

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return []

    # Detect header row
    has_header = _is_header_row(rows[0])
    if has_header:
        col_map = _map_headers(rows[0])
        data_rows = rows[1:]
    else:
        num_cols = max(len(r) for r in rows[:5]) if rows else 0
        col_map = _positional_mapping(num_cols)
        data_rows = rows

    # Market name from filename
    market_name: Optional[str] = None
    if filename:
        from backend.app.parser.detector import detect_market
        market_name_code = detect_market([], filename)
        if market_name_code != "UNKNOWN":
            market_name = market_name_code

    records: list[dict] = []
    for row in data_rows:
        if not any(c.strip() for c in row):
            continue
        rec = _row_to_record(row, col_map, market_name)
        if rec:
            records.append(rec)

    logger.info("Parsed %d records from CSV (encoding=%s, delimiter=%r)", len(records), encoding, delimiter)
    return records
