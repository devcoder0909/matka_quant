"""
Project Trinetra - Market Model.

Represents a Satta Matka market (e.g. Kalyan, Main Bazar).
Includes a seeding helper that inserts the canonical market list on first run.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    schedule: Mapped[str] = mapped_column(String(20), nullable=False, default="day")  # day / night
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True,
    )

    # Relationships
    historical_results: Mapped[List["HistoricalResult"]] = relationship(
        "HistoricalResult", back_populates="market", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Market(code={self.code!r}, name={self.name!r})>"


# ── Seed Data ─────────────────────────────────────────────────────────────────

SEED_MARKETS = [
    {"name": "Kalyan", "code": "KALYAN", "display_name": "Kalyan Matka", "schedule": "day"},
]


async def seed_markets(db: AsyncSession) -> int:
    """Insert seed markets if they do not already exist. Returns count of inserted rows."""
    result = await db.execute(select(func.count()).select_from(Market))
    existing_count = result.scalar_one()
    if existing_count > 0:
        return 0

    inserted = 0
    for market_data in SEED_MARKETS:
        market = Market(**market_data)
        db.add(market)
        inserted += 1

    await db.commit()
    return inserted
