"""
Matka Quantum AI - Parser Package
=================================

Universal parsers for Satta Matka historical result data.
Supports HTML chart scraping, CSV import, JSON import, and raw text parsing.

All parsers return a unified list[dict] format:
    {
        "date": str,             # Date string (raw, normalized later)
        "open_patti": str,       # 3-digit open patti e.g. "123"
        "open_ank": int | None,  # Single digit 0-9
        "jodi": str,             # 2-digit jodi e.g. "65"
        "close_ank": int | None, # Single digit 0-9
        "close_patti": str,      # 3-digit close patti e.g. "357"
        "market_name": str | None
    }
"""

from backend.app.parser.html_parser import parse_html_chart
from backend.app.parser.csv_parser import parse_csv_data
from backend.app.parser.json_parser import parse_json_data
from backend.app.parser.text_parser import parse_text_data
from backend.app.parser.detector import detect_market, detect_date_format
from backend.app.parser.normalizer import normalize_records
from backend.app.parser.validator import validate_records, ValidationResult

__all__ = [
    "parse_html_chart",
    "parse_csv_data",
    "parse_json_data",
    "parse_text_data",
    "detect_market",
    "detect_date_format",
    "normalize_records",
    "validate_records",
    "ValidationResult",
]
