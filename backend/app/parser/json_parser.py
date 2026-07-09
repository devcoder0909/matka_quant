"""
Matka Quantum AI - JSON Data Parser
=====================================

Parses Satta Matka result data from JSON strings.  Accepts flat arrays of
objects or nested structures.  Field keys are matched case-insensitively with
underscore/space/camelCase variants.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

RE_3PART = re.compile(r"(\d{3})\s*[-–—]\s*(\d{2})\s*[-–—]\s*(\d{3})")
RE_5PART = re.compile(
    r"(\d{3})\s*[-–—]\s*(\d)\s*[-–—]?\s*(\d{2})\s*[-–—]?\s*(\d)\s*[-–—]\s*(\d{3})"
)


def _digit_sum_mod10(patti: str) -> int:
    return sum(int(d) for d in patti) % 10


# ---------------------------------------------------------------------------
# Key normalisation
# ---------------------------------------------------------------------------

_KEY_MAP: dict[str, str] = {}

def _build_key_map() -> dict[str, str]:
    """Build a lookup from normalised key variants to canonical field names."""
    if _KEY_MAP:
        return _KEY_MAP
    fields: dict[str, list[str]] = {
        "date": ["date", "dt", "day", "result_date", "resultdate"],
        "open_patti": ["open_patti", "openpatti", "open patti", "open_panel", "openpanel", "op"],
        "open_ank": ["open_ank", "openank", "open ank", "open_digit", "opendigit", "oa"],
        "jodi": ["jodi", "jd", "pair", "jodipatti"],
        "close_ank": ["close_ank", "closeank", "close ank", "close_digit", "closedigit", "ca"],
        "close_patti": ["close_patti", "closepatti", "close patti", "close_panel", "closepanel", "cp"],
        "market_name": ["market_name", "marketname", "market", "game", "game_name", "gamename"],
        "result": ["result", "full_result", "fullresult"],
    }
    for canonical, variants in fields.items():
        for v in variants:
            _KEY_MAP[v] = canonical
    return _KEY_MAP


def _normalise_key(key: str) -> Optional[str]:
    """Map an arbitrary JSON key to a canonical field name."""
    km = _build_key_map()
    # Try exact lower, then stripped of underscores/spaces
    k = key.strip().lower()
    if k in km:
        return km[k]
    k_stripped = re.sub(r"[\s_\-]", "", k)
    for variant, canonical in km.items():
        if re.sub(r"[\s_\-]", "", variant) == k_stripped:
            return canonical
    return None


# ---------------------------------------------------------------------------
# Object normalisation
# ---------------------------------------------------------------------------

def _flatten_obj(obj: dict) -> Dict[str, Any]:
    """Flatten a single JSON object to the canonical record dict."""
    record: Dict[str, Any] = {
        "date": None,
        "open_patti": None,
        "open_ank": None,
        "jodi": None,
        "close_ank": None,
        "close_patti": None,
        "market_name": None,
    }

    for raw_key, raw_val in obj.items():
        canonical = _normalise_key(raw_key)
        if canonical is None:
            continue
        if canonical == "result":
            # Try to parse full result string
            s = str(raw_val)
            m5 = RE_5PART.search(s)
            m3 = RE_3PART.search(s)
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
            continue

        val = raw_val
        if val is None:
            continue
        val_str = str(val).strip()
        if not val_str:
            continue

        if canonical in ("open_ank", "close_ank"):
            try:
                record[canonical] = int(val_str)
            except (ValueError, TypeError):
                pass
        else:
            record[canonical] = val_str

    return record


def _extract_records_from_structure(data: Any) -> List[Dict[str, Any]]:
    """
    Recursively extract record dicts from an arbitrary JSON structure.

    Supports:
    - list of flat objects
    - dict with a key whose value is a list of objects
    - nested structures (walks until it finds lists of dicts)
    """
    records: list[dict] = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                rec = _flatten_obj(item)
                if rec.get("open_patti") or rec.get("jodi") or rec.get("close_patti"):
                    records.append(rec)
            elif isinstance(item, list):
                records.extend(_extract_records_from_structure(item))
    elif isinstance(data, dict):
        # Check if the dict itself is a record
        rec = _flatten_obj(data)
        if rec.get("open_patti") or rec.get("jodi") or rec.get("close_patti"):
            records.append(rec)
        else:
            # Recurse into values
            for val in data.values():
                if isinstance(val, (list, dict)):
                    records.extend(_extract_records_from_structure(val))

    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_json_data(json_str: str) -> List[Dict[str, Any]]:
    """
    Parse Satta Matka result data from a JSON string.

    Accepts a JSON array of objects or a nested structure with flexible key
    matching (case-insensitive, underscore/space/camelCase variants).

    Parameters
    ----------
    json_str : str
        Raw JSON string.

    Returns
    -------
    list[dict]
        Parsed records in the standard format.
    """
    if not json_str or not json_str.strip():
        logger.warning("Empty JSON input received")
        return []

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON: %s", exc)
        return []

    records = _extract_records_from_structure(data)
    logger.info("Parsed %d records from JSON", len(records))
    return records
