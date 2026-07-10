"""
Matka Quantum AI - Universal HTML Chart Parser
===============================================

Parses Satta Matka result charts from raw HTML.  Handles daily tables, weekly
jodi/panel grids, and compact result formats.  Uses BeautifulSoup with the
html5lib parser for maximum tolerance of broken markup.

Security: all ``<script>``, ``<style>`` elements and ``on*`` event-handler
attributes are stripped before any data extraction.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# Full 5-part: "123-6-65-5-357"
RE_5PART = re.compile(
    r"(\d{3})\s*[-–—]\s*(\d)\s*[-–—]?\s*(\d{2})\s*[-–—]?\s*(\d)\s*[-–—]\s*(\d{3})"
)
# Compact 3-part: "123-65-357"
RE_3PART = re.compile(r"(\d{3})\s*[-–—]\s*(\d{2})\s*[-–—]\s*(\d{3})")
# Jodi only: 2-digit number
RE_JODI_ONLY = re.compile(r"^\s*(\d{2})\s*$")
# Placeholder / pending markers
RE_PLACEHOLDER = re.compile(r"^[\s*Xx\-–—]+$|^\*{1,3}$|^XX$|^---$|^NA$|^N/A$", re.IGNORECASE)

# Day names for weekly grid detection
DAY_NAMES_EN = {"mon", "tue", "wed", "thu", "fri", "sat", "sun",
                "monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"}

# Header keywords for daily table detection
DAILY_HEADER_KW = {"date", "open", "close", "patti", "ank", "jodi", "result"}

# Date patterns
DATE_PATTERNS = [
    (re.compile(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})"), "%d-%m-%Y"),
    (re.compile(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2})"), "%d-%m-%y"),
    (re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})"), "%Y-%m-%d"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _digit_sum_mod10(patti: str) -> int:
    """Return sum of digits mod 10 for a 3-digit patti string."""
    return sum(int(d) for d in patti) % 10


def _sanitize_html(soup: BeautifulSoup) -> None:
    """Remove dangerous elements and attributes in-place."""
    for tag in soup.find_all(["script", "style", "link", "meta", "iframe", "object", "embed"]):
        tag.decompose()
    for tag in soup.find_all(True):
        attrs_to_remove = [a for a in tag.attrs if a.lower().startswith("on")]
        for attr in attrs_to_remove:
            del tag[attr]


def _clean_cell_text(cell: Tag) -> str:
    """Extract visible text from a cell, stripping nested tags."""
    return " ".join(cell.get_text(separator=" ", strip=True).split())


def _is_placeholder(text: str) -> bool:
    """Return True if the cell value is a placeholder / pending marker."""
    if not text:
        return True
    return bool(RE_PLACEHOLDER.match(text.strip()))


def _extract_market_name(soup: BeautifulSoup) -> Optional[str]:
    """Try to extract market name from page title or headings."""
    from app.parser.detector import detect_market as _detect

    candidates: list[str] = []
    if soup.title and soup.title.string:
        candidates.append(soup.title.string)
    for tag_name in ("h1", "h2", "h3", "caption"):
        for tag in soup.find_all(tag_name):
            candidates.append(tag.get_text(strip=True))
    raw = " ".join(candidates)
    code = _detect([], raw)
    return code if code != "UNKNOWN" else None


def _parse_date_string(text: str) -> Optional[str]:
    """Try to parse a date-like string and return as-is (normalization later)."""
    text = text.strip()
    for pat, _ in DATE_PATTERNS:
        if pat.search(text):
            return text
    return None


def _dates_for_week_row(first_col_text: str, day_count: int) -> List[Optional[str]]:
    """
    Given the first-column text of a weekly grid row (e.g. "07-07-2026 to 12-07-2026"),
    generate a list of date strings for each day column.
    """
    dates: List[Optional[str]] = [None] * day_count
    # Try to find two dates in the text
    found: list[str] = []
    for pat, fmt in DATE_PATTERNS:
        for m in pat.finditer(first_col_text):
            found.append(m.group(0))
    if len(found) >= 2:
        # parse start date
        start_dt = None
        for _, fmt in DATE_PATTERNS:
            try:
                start_dt = datetime.strptime(found[0], fmt.replace("-", found[0][2] if len(found[0]) > 2 else "-"))
            except (ValueError, IndexError):
                pass
        if start_dt is None:
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y"):
                try:
                    start_dt = datetime.strptime(found[0], fmt)
                    break
                except ValueError:
                    continue
        if start_dt:
            for i in range(day_count):
                dt = start_dt + timedelta(days=i)
                dates[i] = dt.strftime("%d-%m-%Y")
    elif len(found) == 1:
        start_dt = None
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y"):
            try:
                start_dt = datetime.strptime(found[0], fmt)
                break
            except ValueError:
                continue
        if start_dt:
            for i in range(day_count):
                dt = start_dt + timedelta(days=i)
                dates[i] = dt.strftime("%d-%m-%Y")
    return dates


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------

def _classify_table(table: Tag) -> str:
    """
    Classify a <table> as 'daily', 'weekly_jodi', 'weekly_panel', or 'unknown'.
    """
    header_cells = table.find_all(["th", "td"], limit=20)
    header_text_lower = " ".join(_clean_cell_text(c).lower() for c in header_cells[:15])

    # Check for day-name headers -> weekly grid
    tokens = set(re.findall(r"[a-z]+", header_text_lower))
    day_matches = tokens & DAY_NAMES_EN
    if len(day_matches) >= 3:
        # Determine if cells contain full results or just jodi
        sample_cells = table.find_all("td")
        panel_count = 0
        jodi_count = 0
        for c in sample_cells[:30]:
            txt = _clean_cell_text(c)
            if RE_3PART.search(txt) or RE_5PART.search(txt):
                panel_count += 1
            elif RE_JODI_ONLY.match(txt):
                jodi_count += 1
        if panel_count > jodi_count:
            return "weekly_panel"
        return "weekly_jodi"

    # Check for daily header keywords
    kw_matches = DAILY_HEADER_KW & set(re.findall(r"[a-z]+", header_text_lower))
    if len(kw_matches) >= 2:
        return "daily"

    # Fallback: check if cells contain result patterns
    all_cells = table.find_all("td")
    result_count = 0
    for c in all_cells[:40]:
        txt = _clean_cell_text(c)
        if RE_3PART.search(txt) or RE_5PART.search(txt):
            result_count += 1
    if result_count >= 3:
        return "weekly_panel"

    return "unknown"


# ---------------------------------------------------------------------------
# Per-layout extractors
# ---------------------------------------------------------------------------

def _map_header_columns(header_cells: list[str]) -> Dict[str, int]:
    """Map standard field names to column indices based on header text."""
    mapping: Dict[str, int] = {}
    keywords = {
        "date": ["date", "dt", "तारीख", "दिनांक"],
        "open_patti": ["open patti", "open panel", "op", "open_patti", "opatti"],
        "open_ank": ["open ank", "open digit", "open_ank", "oank", "oa"],
        "jodi": ["jodi", "jd", "jp", "jodi patti", "joди"],
        "close_ank": ["close ank", "close digit", "close_ank", "cank", "ca"],
        "close_patti": ["close patti", "close panel", "cp", "close_patti", "cpatti"],
    }
    for idx, cell_text in enumerate(header_cells):
        lower = cell_text.lower().strip()
        for field, kws in keywords.items():
            for kw in kws:
                if kw in lower:
                    mapping[field] = idx
                    break
    return mapping


def _extract_daily_table(table: Tag, market_name: Optional[str]) -> List[Dict[str, Any]]:
    """Extract records from a daily-format table."""
    rows = table.find_all("tr")
    if not rows:
        return []

    # Find header row (first row with <th> or matching keywords)
    header_idx = 0
    header_texts: list[str] = []
    for i, row in enumerate(rows):
        cells = row.find_all(["th", "td"])
        texts = [_clean_cell_text(c) for c in cells]
        joined = " ".join(t.lower() for t in texts)
        if any(kw in joined for kw in ("date", "open", "close", "jodi", "patti")):
            header_idx = i
            header_texts = texts
            break

    col_map = _map_header_columns(header_texts)
    records: list[dict] = []

    for row in rows[header_idx + 1:]:
        cells = row.find_all(["td", "th"])
        texts = [_clean_cell_text(c) for c in cells]
        if not any(t.strip() for t in texts):
            continue

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
            if idx < len(texts):
                val = texts[idx].strip()
                if _is_placeholder(val):
                    continue
                if field in ("open_ank", "close_ank"):
                    try:
                        record[field] = int(val)
                    except (ValueError, TypeError):
                        pass
                else:
                    record[field] = val

        # If no column mapping worked, try to parse the entire row text
        if record["open_patti"] is None and record["jodi"] is None:
            row_text = " ".join(texts)
            m5 = RE_5PART.search(row_text)
            m3 = RE_3PART.search(row_text)
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

        # Try to extract date from row if not mapped
        if record["date"] is None:
            for t in texts:
                d = _parse_date_string(t)
                if d:
                    record["date"] = d
                    break

        # Only keep records with at least some data
        if record["open_patti"] or record["jodi"] or record["close_patti"]:
            records.append(record)

    return records


def _extract_weekly_grid(table: Tag, market_name: Optional[str], grid_type: str) -> List[Dict[str, Any]]:
    """Extract records from a weekly grid table (jodi or panel)."""
    rows = table.find_all("tr")
    if not rows:
        return []

    # Determine the number of day columns from header
    header_row = rows[0]
    header_cells = header_row.find_all(["th", "td"])
    
    # Calculate true number of logical columns including colspans
    day_col_count = sum(1 for c in header_cells if any(dn in _clean_cell_text(c).lower() for dn in ["mon", "tue", "wed", "thu", "fri", "sat", "sun", "monday", "tuesday"]))
    num_days = max(day_col_count, 6)
    
    # Check if header has colspan="3", which guarantees it's the 3-column format
    is_3col_layout = any(c.get("colspan") in ("3", 3) for c in header_cells)

    records: list[dict] = []

    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        texts = [_clean_cell_text(c) for c in cells]
        if not texts:
            continue

        first_col = texts[0]
        week_dates = _dates_for_week_row(first_col, num_days)

        if is_3col_layout:
            for day_idx in range(num_days):
                base_idx = 1 + (day_idx * 3)
                if base_idx + 1 >= len(texts):
                    continue
                
                open_text = "".join(texts[base_idx].split()) if base_idx < len(texts) else ""
                jodi_text = "".join(texts[base_idx + 1].split()) if base_idx + 1 < len(texts) else ""
                close_text = "".join(texts[base_idx + 2].split()) if base_idx + 2 < len(texts) else ""

                if _is_placeholder(jodi_text) and not open_text and not close_text:
                    continue

                m_jodi = RE_JODI_ONLY.match(jodi_text)
                jodi = m_jodi.group(1) if m_jodi else None

                open_patti = open_text if len(open_text) == 3 and open_text.isdigit() else None
                close_patti = close_text if len(close_text) == 3 and close_text.isdigit() else None

                record = {
                    "date": week_dates[day_idx] if day_idx < len(week_dates) else None,
                    "open_patti": open_patti,
                    "open_ank": _digit_sum_mod10(open_patti) if open_patti else (int(jodi[0]) if jodi else None),
                    "jodi": jodi,
                    "close_ank": _digit_sum_mod10(close_patti) if close_patti else (int(jodi[1]) if jodi else None),
                    "close_patti": close_patti,
                    "market_name": market_name,
                }
                
                if record["jodi"] or record["open_patti"]:
                    records.append(record)
                    
        else:
            # 1-column per day layout (Jodi or single-cell panel)
            for day_idx in range(num_days):
                col_idx = day_idx + 1
                if col_idx >= len(texts):
                    continue
                
                cell_text = texts[col_idx].strip()
                if _is_placeholder(cell_text):
                    continue

                record = {
                    "date": week_dates[day_idx] if day_idx < len(week_dates) else None,
                    "open_patti": None,
                    "open_ank": None,
                    "jodi": None,
                    "close_ank": None,
                    "close_patti": None,
                    "market_name": market_name,
                }

                if grid_type == "weekly_panel" or "-" in cell_text or len(cell_text.replace(" ", "")) >= 8:
                    # Could be "123-55-123" or "1 2 3 55 1 2 3"
                    cleaned = "".join(cell_text.split())
                    if len(cleaned) >= 8:
                        if len(cleaned) == 8: # 123 55 123
                            record["open_patti"] = cleaned[0:3]
                            record["jodi"] = cleaned[3:5]
                            record["close_patti"] = cleaned[5:8]
                            record["open_ank"] = _digit_sum_mod10(record["open_patti"])
                            record["close_ank"] = _digit_sum_mod10(record["close_patti"])
                    else:
                        m5 = RE_5PART.search(cell_text)
                        m3 = RE_3PART.search(cell_text)
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
                else:
                    m_jodi = RE_JODI_ONLY.match(cell_text)
                    if m_jodi:
                        record["jodi"] = m_jodi.group(1)
                        record["open_ank"] = int(m_jodi.group(1)[0])
                        record["close_ank"] = int(m_jodi.group(1)[1])

                if record["jodi"] or record["open_patti"]:
                    records.append(record)

    return records


# ---------------------------------------------------------------------------
# Whole-document regex fallback
# ---------------------------------------------------------------------------

def _extract_from_raw_text(html: str, market_name: Optional[str]) -> List[Dict[str, Any]]:
    """Regex-based extraction as fallback when tables don't parse well."""
    records: list[dict] = []
    seen: set[str] = set()

    for m in RE_5PART.finditer(html):
        key = f"{m.group(1)}-{m.group(3)}-{m.group(5)}"
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "date": None,
            "open_patti": m.group(1),
            "open_ank": int(m.group(2)),
            "jodi": m.group(3),
            "close_ank": int(m.group(4)),
            "close_patti": m.group(5),
            "market_name": market_name,
        })

    for m in RE_3PART.finditer(html):
        key = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if key in seen:
            continue
        seen.add(key)
        op = m.group(1)
        cp = m.group(3)
        records.append({
            "date": None,
            "open_patti": op,
            "open_ank": _digit_sum_mod10(op),
            "jodi": m.group(2),
            "close_ank": _digit_sum_mod10(cp),
            "close_patti": cp,
            "market_name": market_name,
        })

    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_html_chart(raw_html: str) -> List[Dict[str, Any]]:
    """
    Parse Satta Matka result data from raw HTML.

    Handles three layouts:
        1. **Daily table** — Date | Open Patti | Open Ank | Jodi | Close Ank | Close Patti
        2. **Weekly Jodi grid** — rows=weeks, cols=Mon-Sat, cells=Jodi
        3. **Weekly Panel grid** — rows=weeks, cols=Mon-Sat, cells="123-65-357"

    Security: ``<script>``, ``<style>`` elements and ``on*`` event-handler
    attributes are stripped before processing.

    Parameters
    ----------
    raw_html : str
        The raw HTML content to parse.

    Returns
    -------
    list[dict]
        List of record dicts with keys:
        ``date``, ``open_patti``, ``open_ank``, ``jodi``,
        ``close_ank``, ``close_patti``, ``market_name``.
    """
    if not raw_html or not raw_html.strip():
        logger.warning("Empty HTML input received")
        return []

    try:
        soup = BeautifulSoup(raw_html, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
        except Exception as exc:
            logger.error("Failed to parse HTML: %s", exc)
            return []

    _sanitize_html(soup)
    market_name = _extract_market_name(soup)

    all_records: list[dict] = []
    tables = soup.find_all("table")

    if tables:
        for table in tables:
            layout = _classify_table(table)
            logger.debug("Table classified as: %s", layout)

            if layout == "daily":
                all_records.extend(_extract_daily_table(table, market_name))
            elif layout in ("weekly_jodi", "weekly_panel"):
                all_records.extend(_extract_weekly_grid(table, market_name, layout))
            else:
                # Try daily first, then regex
                daily_recs = _extract_daily_table(table, market_name)
                if daily_recs:
                    all_records.extend(daily_recs)
                else:
                    all_records.extend(_extract_weekly_grid(table, market_name, "weekly_panel"))
    else:
        logger.info("No <table> elements found; falling back to regex extraction")

    # Fallback: regex over entire document if nothing extracted from tables
    if not all_records:
        text = soup.get_text(separator=" ")
        all_records = _extract_from_raw_text(text, market_name)

    # Also try regex for any records missed by table parsing
    if len(all_records) < 3:
        text = soup.get_text(separator=" ")
        regex_recs = _extract_from_raw_text(text, market_name)
        existing_keys = {
            f"{r.get('open_patti')}-{r.get('jodi')}-{r.get('close_patti')}"
            for r in all_records
        }
        for rec in regex_recs:
            key = f"{rec.get('open_patti')}-{rec.get('jodi')}-{rec.get('close_patti')}"
            if key not in existing_keys:
                all_records.append(rec)
                existing_keys.add(key)

    logger.info("Parsed %d records from HTML", len(all_records))
    return all_records
