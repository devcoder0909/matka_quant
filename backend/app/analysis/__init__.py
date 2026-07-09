"""
Matka Quantum AI - Analysis Package
=====================================

Statistical frequency analysis and ensemble scoring for Satta Matka data.
"""

from app.analysis.frequency import analyze_frequencies
from app.analysis.ensemble import calculate_ensemble_scores
from app.analysis.engine import run_analysis

__all__ = [
    "analyze_frequencies",
    "calculate_ensemble_scores",
    "run_analysis",
]
