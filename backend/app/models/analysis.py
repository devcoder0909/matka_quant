"""
Project Trinetra - Analysis & Backtesting Models.

Covers analysis runs, candidate scores, model versioning,
backtesting infrastructure, and feature snapshots.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Analysis Run ──────────────────────────────────────────────────────────────

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    analysis_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="frequency",
    )  # frequency / pattern / composite
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
    )  # pending / running / completed / failed
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    market: Mapped["Market"] = relationship("Market", lazy="selectin")
    candidates: Mapped[list["CandidateScore"]] = relationship(
        "CandidateScore", back_populates="run", cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AnalysisRun(id={self.id}, market_id={self.market_id}, "
            f"date={self.target_date}, status={self.status!r})>"
        )


# ── Candidate Score ───────────────────────────────────────────────────────────

class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    candidate_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
    )  # ank / jodi / patti
    candidate_value: Mapped[str] = mapped_column(String(10), nullable=False)
    research_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
    )  # low / medium / high / very_high
    supporting_signals_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conflicting_signals_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stability_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
    )  # stable / moderate / volatile
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="candidates")

    def __repr__(self) -> str:
        return (
            f"<CandidateScore(run_id={self.run_id}, type={self.candidate_type!r}, "
            f"value={self.candidate_value!r}, score={self.research_score})>"
        )


# ── Model Versioning ─────────────────────────────────────────────────────────

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    metrics: Mapped[list["ModelMetric"]] = relationship(
        "ModelMetric", back_populates="model_version", cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(name={self.name!r}, v={self.version!r})>"


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<ModelMetric(model={self.model_version_id}, {self.metric_name}={self.metric_value})>"


# ── Backtesting ───────────────────────────────────────────────────────────────

class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
    )  # pending / running / completed / failed
    total_samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top1_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top3_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top5_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top10_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    random_baseline: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    freq_baseline: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    improvement_over_baseline: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    market: Mapped["Market"] = relationship("Market", lazy="selectin")
    results: Mapped[list["BacktestResult"]] = relationship(
        "BacktestResult", back_populates="run", cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestRun(id={self.id}, market_id={self.market_id}, "
            f"status={self.status!r})>"
        )


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_values_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_value: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    matched_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    run: Mapped["BacktestRun"] = relationship("BacktestRun", back_populates="results")

    def __repr__(self) -> str:
        return f"<BacktestResult(run_id={self.run_id}, date={self.test_date}, rank={self.matched_rank})>"


# ── Feature Snapshot ──────────────────────────────────────────────────────────

class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

    __table_args__ = (
        UniqueConstraint("market_id", "snapshot_date", "feature_set_name", name="uq_feature_snap"),
        Index("ix_feature_snap_market_date", "market_id", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    feature_set_name: Mapped[str] = mapped_column(String(100), nullable=False)
    features_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    market: Mapped["Market"] = relationship("Market", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<FeatureSnapshot(market_id={self.market_id}, date={self.snapshot_date}, "
            f"set={self.feature_set_name!r})>"
        )
