"""
Project Trinetra - Analysis & Backtest Schemas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Analysis Request / Response ───────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    """Body for POST /analysis/run."""

    market_code: str = Field(..., description="Market code, e.g. KALYAN")
    target_date: Optional[date] = Field(None, description="Date to analyse; defaults to today")
    analysis_type: str = Field("frequency", description="frequency / pattern / composite")


class CommandRequest(BaseModel):
    """Body for POST /analysis/command."""

    command: str = Field(..., min_length=3, description="Natural-language command string")


class CandidateResponse(BaseModel):
    """Single candidate score."""

    id: int
    candidate_type: str  # ank / jodi / patti
    candidate_value: str
    research_score: float
    model_probability: Optional[float] = None
    baseline_probability: Optional[float] = None
    confidence_level: Optional[str] = None
    supporting_signals: Optional[List[Dict[str, Any]]] = None
    conflicting_signals: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[Dict[str, Any]] = None
    sample_size: Optional[int] = None
    stability_level: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    """Full analysis run result."""

    success: bool = True
    message: str = "Analysis complete"
    run_id: int
    market_code: str
    market_name: str
    target_date: date
    analysis_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    candidates: List[CandidateResponse] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisStatusResponse(BaseModel):
    """Lightweight status check."""

    run_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    candidate_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WatchlistResponse(BaseModel):
    """Top candidates grouped by type."""

    market_code: str
    target_date: date
    top_anks: List[CandidateResponse] = Field(default_factory=list)
    top_jodis: List[CandidateResponse] = Field(default_factory=list)
    top_pattis: List[CandidateResponse] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExplanationResponse(BaseModel):
    """Detailed explanation for a single candidate."""

    candidate_type: str
    candidate_value: str
    research_score: float
    supporting_signals: List[Dict[str, Any]] = Field(default_factory=list)
    conflicting_signals: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: Dict[str, Any] = Field(default_factory=dict)


# ── Backtest ──────────────────────────────────────────────────────────────────

class BacktestRequest(BaseModel):
    """Body for POST /backtest/run."""

    market_code: str
    start_date: date
    end_date: date
    analysis_type: str = "frequency"


class BacktestResultItem(BaseModel):
    """Single day in a backtest."""

    test_date: date
    predicted_values: Optional[List[str]] = None
    actual_value: Optional[str] = None
    matched_rank: Optional[int] = None


class BacktestResponse(BaseModel):
    """Full backtest result."""

    success: bool = True
    message: str = "Backtest complete"
    run_id: int
    market_code: str
    start_date: date
    end_date: date
    status: str
    total_samples: int = 0
    top1_rate: Optional[float] = None
    top3_rate: Optional[float] = None
    top5_rate: Optional[float] = None
    top10_rate: Optional[float] = None
    random_baseline: Optional[float] = None
    freq_baseline: Optional[float] = None
    improvement_over_baseline: Optional[float] = None
    results: List[BacktestResultItem] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
