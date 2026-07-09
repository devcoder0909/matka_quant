"""
Project Trinetra - Quantum Predictive Engine (Phase 2)

Houses advanced algorithms: Transition Matrices (Markov), Time-Decay Weighting,
and Anomaly (Gap/Overdue) detection.
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
import math

from app.models.historical_result import HistoricalResult

def calculate_time_decay_weights(total_days: int, half_life_days: int = 90) -> List[float]:
    """
    Generate an array of weights using exponential decay.
    More recent results (index close to 0) get higher weight.
    """
    weights = []
    # decay constant lambda = ln(2) / half_life
    decay_constant = math.log(2) / half_life_days
    
    for day in range(total_days):
        weight = math.exp(-decay_constant * day)
        weights.append(weight)
        
    return weights


def build_1st_order_matrix(
    results: List[HistoricalResult], 
    target_field: str = "jodi"
) -> Dict[str, Dict[str, float]]:
    transitions: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for i in range(1, len(results)):
        current = getattr(results[i], target_field)
        next_val = getattr(results[i-1], target_field)
        if current is None or next_val is None:
            continue
        c_str = str(current).zfill(2 if target_field == "jodi" else 1)
        n_str = str(next_val).zfill(2 if target_field == "jodi" else 1)
        transitions[c_str][n_str] += 1.0

    prob_matrix: Dict[str, Dict[str, float]] = {}
    for state, next_states in transitions.items():
        total = sum(next_states.values())
        prob_matrix[state] = {k: v / total for k, v in next_states.items()}
    return prob_matrix

def build_2nd_order_matrix(
    results: List[HistoricalResult], 
    target_field: str = "jodi"
) -> Dict[Tuple[str, str], Dict[str, float]]:
    transitions: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for i in range(2, len(results)):
        prev2 = getattr(results[i], target_field)
        prev1 = getattr(results[i-1], target_field)
        current = getattr(results[i-2], target_field)
        
        if prev2 is None or prev1 is None or current is None:
            continue
            
        p2_str = str(prev2).zfill(2 if target_field == "jodi" else 1)
        p1_str = str(prev1).zfill(2 if target_field == "jodi" else 1)
        c_str = str(current).zfill(2 if target_field == "jodi" else 1)
        
        transitions[(p2_str, p1_str)][c_str] += 1.0

    prob_matrix: Dict[Tuple[str, str], Dict[str, float]] = {}
    for state_tuple, next_states in transitions.items():
        total = sum(next_states.values())
        prob_matrix[state_tuple] = {k: v / total for k, v in next_states.items()}
    return prob_matrix

def analyze_predictive_signals(
    historical_records: List[HistoricalResult],
    target_date: Any
) -> Dict[str, Any]:
    if not historical_records or len(historical_records) < 3:
        return {"error": "Insufficient historical data"}
        
    decay_weights = calculate_time_decay_weights(len(historical_records))
    
    jodi_scores = defaultdict(float)
    
    for i, record in enumerate(historical_records):
        weight = decay_weights[i]
        if record.jodi:
            jodi_scores[record.jodi] += weight
            
    total_jodi = sum(jodi_scores.values()) or 1.0
    normalized_jodi_decay = {k: (v / total_jodi) for k, v in jodi_scores.items()}
    
    latest = historical_records[0]
    yesterday = historical_records[1]
    
    # Build Matrices
    jodi_1st = build_1st_order_matrix(historical_records, "jodi")
    jodi_2nd = build_2nd_order_matrix(historical_records, "jodi")
    
    c1 = latest.jodi
    c2 = yesterday.jodi
    
    trans_1st = jodi_1st.get(c1, {}) if c1 else {}
    trans_2nd = jodi_2nd.get((c2, c1), {}) if (c1 and c2) else {}
    
    final_jodi_scores = {}
    for jodi_num in [str(i).zfill(2) for i in range(100)]:
        decay_prob = normalized_jodi_decay.get(jodi_num, 0.0)
        prob_1st = trans_1st.get(jodi_num, 0.0)
        prob_2nd = trans_2nd.get(jodi_num, 0.0)
        
        # Ensemble Weights: 50% Decay, 20% 1st-Order, 30% 2nd-Order
        final_score = (decay_prob * 0.5) + (prob_1st * 0.2) + (prob_2nd * 0.3)
        if final_score > 0:
            final_jodi_scores[jodi_num] = final_score
            
    top_jodis = sorted(final_jodi_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "metadata": {
            "sample_size": len(historical_records),
            "latest_sequence": f"{c2} -> {c1}"
        },
        "predictions": {
            "top_jodis": [{"jodi": k, "probability": v} for k, v in top_jodis]
        }
    }
