"""
Matka Quantum AI - Analysis Package
=====================================

Statistical frequency analysis and ensemble scoring for Satta Matka data.
"""

from backend.app.analysis.frequency import analyze_frequencies
from backend.app.analysis.ensemble import calculate_ensemble_scores
from backend.app.analysis.engine import run_analysis

__all__ = [
    "analyze_frequencies",
    "calculate_ensemble_scores",
    "run_analysis",
]
