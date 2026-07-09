"""
Project Trinetra - Chart Import Models.

Tracks bulk data import operations and per-row errors for diagnostics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChartImport(Base):
    __tablename__ = "chart_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("markets.id", ondelete="SET NULL"), nullable=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="html",
    )  # html / csv / json / text
    raw_data_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_completeness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
    )  # pending / processing / completed / failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    market: Mapped[Optional["Market"]] = relationship("Market", lazy="selectin")
    errors: Mapped[list["ImportErrorRecord"]] = relationship(
        "ImportErrorRecord", back_populates="chart_import", cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<ChartImport(id={self.id}, source={self.source_type!r}, "
            f"status={self.status!r}, valid={self.valid_records})>"
        )


class ImportErrorRecord(Base):
    """Individual row-level error encountered during an import."""

    __tablename__ = "import_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chart_imports.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    chart_import: Mapped["ChartImport"] = relationship("ChartImport", back_populates="errors")

    def __repr__(self) -> str:
        return (
            f"<ImportErrorRecord(import_id={self.import_id}, row={self.row_number}, "
            f"type={self.error_type!r})>"
        )
