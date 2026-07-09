"""
Project Trinetra - Backtest Engine

Walk-forward simulation to calculate win-rates and evaluate model accuracy 
by predicting historical dates using only data prior to those dates.
"""

from typing import List, Dict, Any
import logging
from datetime import datetime

from app.analysis.predictive import analyze_predictive_signals

logger = logging.getLogger(__name__)

class MockRecord:
    def __init__(self, data):
        self.jodi = data.get("jodi")
        self.open_ank = data.get("open_ank")
        self.date = data.get("date")

def run_walk_forward_backtest(
    historical_records: List[Dict[str, Any]],
    test_window_days: int = 30
) -> Dict[str, Any]:
    """
    Simulates testing the model on the last N days.
    For each test day, it hides all future data, runs the prediction engine,
    and checks if the top prediction matched the actual outcome.
    """
    if len(historical_records) <= test_window_days:
        return {"error": "Not enough historical data to backtest"}
        
    # Sort chronological (oldest first) so we can slice properly
    sorted_records = sorted(historical_records, key=lambda x: x["date"])
    
    total_jodi_hits = 0
    total_ank_hits = 0
    results = []
    
    # Iterate over the test window (the last N days)
    for i in range(len(sorted_records) - test_window_days, len(sorted_records)):
        target_record = sorted_records[i]
        actual_jodi = str(target_record.get("jodi", "")).zfill(2)
        actual_ank = str(target_record.get("open_ank", ""))
        
        # Training data: everything BEFORE this day
        # We sort it reverse chronological because predictive.py expects newest first
        training_data = sorted_records[:i]
        training_data_reverse = sorted(training_data, key=lambda x: x["date"], reverse=True)
        
        obj_records = [MockRecord(r) for r in training_data_reverse]
        
        try:
            predictions = analyze_predictive_signals(obj_records, target_record["date"])
            top_jodis = [p["jodi"] for p in predictions["predictions"]["top_jodis"]]
            top_anks = [p["ank"] for p in predictions["predictions"]["top_anks"]]
            
            # Check for hits in top 3
            jodi_hit = actual_jodi in top_jodis[:3]
            ank_hit = actual_ank in top_anks[:3]
            
            if jodi_hit:
                total_jodi_hits += 1
            if ank_hit:
                total_ank_hits += 1
                
            results.append({
                "date": target_record["date"],
                "actual_jodi": actual_jodi,
                "predicted_jodis": top_jodis[:3],
                "jodi_hit": jodi_hit,
                "actual_ank": actual_ank,
                "predicted_anks": top_anks[:3],
                "ank_hit": ank_hit
            })
        except Exception as e:
            logger.error(f"Backtest error on {target_record['date']}: {str(e)}")
            continue
            
    win_rate_jodi = (total_jodi_hits / test_window_days) * 100
    win_rate_ank = (total_ank_hits / test_window_days) * 100
    
    return {
        "test_window_days": test_window_days,
        "jodi_win_rate_top3": f"{win_rate_jodi:.2f}%",
        "ank_win_rate_top3": f"{win_rate_ank:.2f}%",
        "random_baseline_jodi": "3.00%",
        "random_baseline_ank": "30.00%",
        "details": results
    }
