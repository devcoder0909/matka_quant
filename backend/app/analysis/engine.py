"""
Matka Quantum AI - Analysis Engine (Orchestrator)
==================================================

Main entry-point for running a full analysis cycle.  Fetches historical
records, runs frequency analysis, and produces ranked candidates with
explanations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.analysis.frequency import analyze_frequencies
from app.analysis.ensemble import calculate_ensemble_scores

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _records_from_db_rows(rows: list) -> List[Dict[str, Any]]:
    """
    Convert database row objects (or dicts) to the standard record format.

    Supports SQLAlchemy Row objects (with ``_mapping``), plain dicts, and
    objects with attribute access.
    """
    records: list[dict] = []
    for row in rows:
        if isinstance(row, dict):
            rec = row
        elif hasattr(row, "_mapping"):
            rec = dict(row._mapping)
        elif hasattr(row, "__dict__"):
            rec = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
        else:
            continue

        records.append({
            "date": str(rec.get("date", "") or ""),
            "open_patti": str(rec.get("open_patti", "") or "") or None,
            "open_ank": rec.get("open_ank"),
            "jodi": str(rec.get("jodi", "") or "") or None,
            "close_ank": rec.get("close_ank"),
            "close_patti": str(rec.get("close_patti", "") or "") or None,
            "market_name": rec.get("market_name") or rec.get("market_code"),
        })
    return records


def _build_summary(
    candidates: List[Dict[str, Any]],
    frequency_results: Dict[str, Any],
    records: List[Dict[str, Any]],
    target_date: str,
    market_code: str,
) -> Dict[str, Any]:
    """Build a human-readable summary of the analysis."""
    # Top ank candidates per field
    top_open = [c for c in candidates if c["field"] == "open_ank"][:3]
    top_close = [c for c in candidates if c["field"] == "close_ank"][:3]
    top_jodi = [c for c in candidates if c["field"] == "jodi"][:5]

    # Hot/cold summary from 30d window
    def _hot_cold(field: str, window: str = "30d") -> Dict[str, list]:
        w = frequency_results.get(field, {}).get("windows", {}).get(window, {}).get("values", {})
        hot = sorted(
            [v for v, d in w.items() if d.get("classification") == "HOT"],
            key=lambda v: w[v].get("z_score", 0), reverse=True,
        )
        cold = sorted(
            [v for v, d in w.items() if d.get("classification") == "COLD"],
            key=lambda v: w[v].get("z_score", 0),
        )
        return {"hot": hot[:5], "cold": cold[:5]}

    return {
        "target_date": target_date,
        "market_code": market_code,
        "total_historical_records": len(records),
        "top_open_ank": [{"value": c["value"], "score": c["score"], "confidence": c["confidence"]} for c in top_open],
        "top_close_ank": [{"value": c["value"], "score": c["score"], "confidence": c["confidence"]} for c in top_close],
        "top_jodi": [{"value": c["value"], "score": c["score"], "confidence": c["confidence"]} for c in top_jodi],
        "hot_cold_30d": {
            "open_ank": _hot_cold("open_ank"),
            "close_ank": _hot_cold("close_ank"),
            "jodi": _hot_cold("jodi"),
        },
        "disclaimer": (
            "These scores represent statistical patterns in historical data only. "
            "They do NOT predict future outcomes. Past frequency does NOT guarantee "
            "future results. Use responsibly."
        ),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_analysis(
    db: Any,
    market_id: int,
    target_date: str,
    market_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a complete analysis cycle for a market and target date.

    1. Fetch all historical records for *market_id* from the database.
    2. Run frequency analysis.
    3. Generate ranked candidates (ank, jodi) with ensemble scores.
    4. Build summary with explanations.

    Parameters
    ----------
    db : Any
        An async database session (SQLAlchemy AsyncSession or similar).
        Must support ``execute()`` returning rows with standard fields.
    market_id : int
        Primary key of the market in the database.
    target_date : str
        Target date for analysis in ``YYYY-MM-DD`` format.
    market_code : str, optional
        Standardised market code (e.g. ``'KALYAN'``).

    Returns
    -------
    dict
        Complete analysis result with keys: ``summary``, ``candidates``,
        ``frequency_raw``, ``meta``.
    """
    logger.info("Starting analysis for market_id=%d, target_date=%s", market_id, target_date)

    # ----- Fetch data -----
    records: List[Dict[str, Any]] = []
    try:
        # Try common ORM patterns
        if hasattr(db, "execute"):
            # SQLAlchemy-style: assume a results table
            from sqlalchemy import text
            query = text(
                "SELECT date, open_patti, open_ank, jodi, close_ank, close_patti, market_code "
                "FROM results WHERE market_id = :mid AND date < :td ORDER BY date"
            )
            result = await db.execute(query, {"mid": market_id, "td": target_date})
            rows = result.fetchall()
            records = _records_from_db_rows(rows)
        elif isinstance(db, list):
            # Direct record list (for testing or in-memory use)
            records = _records_from_db_rows(db)
        else:
            logger.warning("Unknown db type %s; treating as empty", type(db))
    except Exception as exc:
        logger.error("Failed to fetch records from database: %s", exc)
        # If db is a list of dicts, use directly
        if isinstance(db, (list, tuple)):
            records = _records_from_db_rows(list(db))

    if not records:
        logger.warning("No historical records found for market_id=%d", market_id)
        return {
            "summary": {
                "target_date": target_date,
                "market_code": market_code or "UNKNOWN",
                "total_historical_records": 0,
                "top_open_ank": [],
                "top_close_ank": [],
                "top_jodi": [],
                "hot_cold_30d": {},
                "disclaimer": "Insufficient data for analysis.",
            },
            "candidates": [],
            "frequency_raw": {},
            "meta": {
                "market_id": market_id,
                "target_date": target_date,
                "records_used": 0,
                "analysis_timestamp": datetime.now().isoformat(),
            },
        }

    # ----- Run analysis -----
    frequency_results = analyze_frequencies(records, target_date)
    candidates = calculate_ensemble_scores(frequency_results, records)
    
    # Run Phase 2 Quantum Predictive Analysis
    from app.analysis.predictive import analyze_predictive_signals
    # We must mock a historical record list structure to pass to it since it expects objects
    class MockRecord:
        def __init__(self, data):
            self.jodi = data.get("jodi")
            self.open_ank = data.get("open_ank")
            self.date = data.get("date")
            
    # Sort backwards for the Markov matrix (newest first)
    sorted_records = sorted(records, key=lambda x: x["date"], reverse=True)
    obj_records = [MockRecord(r) for r in sorted_records]
    
    quantum_predictions = analyze_predictive_signals(obj_records, target_date)
    
    summary = _build_summary(candidates, frequency_results, records, target_date, market_code or "UNKNOWN")
    summary["quantum_predictions"] = quantum_predictions

    analysis_result = {
        "summary": summary,
        "candidates": candidates,
        "frequency_raw": frequency_results,
        "meta": {
            "market_id": market_id,
            "target_date": target_date,
            "records_used": len(records),
            "analysis_timestamp": datetime.now().isoformat(),
        },
    }

    logger.info(
        "Analysis complete: %d candidates, top score=%.1f",
        len(candidates),
        candidates[0]["score"] if candidates else 0,
    )
    return analysis_result
