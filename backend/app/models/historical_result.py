"""
Project Trinetra - Historical Result Model.

Stores validated daily results for each market. Each row is one draw
with open_patti, open_ank, jodi, close_ank, close_patti.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HistoricalResult(Base):
    __tablename__ = "historical_results"

    __table_args__ = (
        UniqueConstraint("market_id", "result_date", name="uq_market_date"),
        Index("ix_hist_market_date", "market_id", "result_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    result_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    open_patti: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    open_ank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jodi: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    close_ank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    close_patti: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="historical_results")

    def __repr__(self) -> str:
        return (
            f"<HistoricalResult(market_id={self.market_id}, date={self.result_date}, "
            f"jodi={self.jodi!r})>"
        )
