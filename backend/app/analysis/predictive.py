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


def build_transition_matrix(
    results: List[HistoricalResult], 
    target_field: str = "jodi"
) -> Dict[str, Dict[str, float]]:
    """
    Builds a Markov Chain Transition Matrix.
    Given state A (e.g., Jodi 65), calculates the probability of state B following it.
    `results` must be sorted descending (newest first).
    """
    transitions: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    
    # We iterate backwards through time to see what followed what
    # results[0] is newest. results[1] is yesterday.
    # So results[1] transitioned to results[0].
    
    for i in range(1, len(results)):
        current_state = getattr(results[i], target_field)
        next_state = getattr(results[i-1], target_field)
        
        if current_state is None or next_state is None:
            continue
            
        current_str = str(current_state).zfill(2 if target_field == "jodi" else 1)
        next_str = str(next_state).zfill(2 if target_field == "jodi" else 1)
        
        transitions[current_str][next_str] += 1.0

    # Normalize counts to probabilities
    prob_matrix: Dict[str, Dict[str, float]] = {}
    for state, next_states in transitions.items():
        total_transitions = sum(next_states.values())
        prob_matrix[state] = {
            next_state: count / total_transitions 
            for next_state, count in next_states.items()
        }
        
    return prob_matrix


def analyze_predictive_signals(
    historical_records: List[HistoricalResult],
    target_date: Any
) -> Dict[str, Any]:
    """
    Analyzes historical data to predict the most probable outcomes for the target_date.
    Returns deeply calculated probabilities for Ank and Jodi.
    """
    if not historical_records:
        return {"error": "Insufficient historical data"}
        
    # 1. Base Time-Decay Frequency
    decay_weights = calculate_time_decay_weights(len(historical_records))
    
    jodi_scores = defaultdict(float)
    ank_scores = defaultdict(float)
    
    for i, record in enumerate(historical_records):
        weight = decay_weights[i]
        if record.jodi:
            jodi_scores[record.jodi] += weight
        if record.open_ank is not None:
            ank_scores[str(record.open_ank)] += weight
            
    # Normalize Decay Scores
    total_jodi_weight = sum(jodi_scores.values()) or 1.0
    total_ank_weight = sum(ank_scores.values()) or 1.0
    
    normalized_jodi_decay = {k: (v / total_jodi_weight) for k, v in jodi_scores.items()}
    normalized_ank_decay = {k: (v / total_ank_weight) for k, v in ank_scores.items()}
    
    # 2. Transition Probabilities (Markov Chain)
    latest_record = historical_records[0]
    jodi_matrix = build_transition_matrix(historical_records, "jodi")
    ank_matrix = build_transition_matrix(historical_records, "open_ank")
    
    current_jodi = latest_record.jodi
    current_ank = str(latest_record.open_ank) if latest_record.open_ank is not None else None
    
    jodi_transitions = jodi_matrix.get(current_jodi, {}) if current_jodi else {}
    ank_transitions = ank_matrix.get(current_ank, {}) if current_ank else {}
    
    # 3. Ensemble Predictive Synthesis
    # Combine Decay Frequency (60%) with Transition Probability (40%)
    final_jodi_scores = {}
    for jodi_num in [str(i).zfill(2) for i in range(100)]:
        decay_prob = normalized_jodi_decay.get(jodi_num, 0.0)
        trans_prob = jodi_transitions.get(jodi_num, 0.0)
        
        # If a transition never happened, base probability is just the decay baseline
        final_score = (decay_prob * 0.6) + (trans_prob * 0.4)
        if final_score > 0:
            final_jodi_scores[jodi_num] = final_score
            
    final_ank_scores = {}
    for ank_num in [str(i) for i in range(10)]:
        decay_prob = normalized_ank_decay.get(ank_num, 0.0)
        trans_prob = ank_transitions.get(ank_num, 0.0)
        
        final_score = (decay_prob * 0.6) + (trans_prob * 0.4)
        if final_score > 0:
            final_ank_scores[ank_num] = final_score
            
    # Sort and get Top Candidates
    top_jodis = sorted(final_jodi_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    top_anks = sorted(final_ank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "metadata": {
            "sample_size": len(historical_records),
            "latest_state_jodi": current_jodi,
            "latest_state_ank": current_ank
        },
        "predictions": {
            "top_anks": [{"ank": k, "probability": v} for k, v in top_anks],
            "top_jodis": [{"jodi": k, "probability": v} for k, v in top_jodis]
        }
    }
