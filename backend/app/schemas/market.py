"""
Project Trinetra - Market Schemas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MarketResponse(BaseModel):
    """Single market detail."""

    id: int
    name: str
    code: str
    display_name: str
    schedule: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Enriched fields (filled by the endpoint)
    record_count: int = 0
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None

    model_config = {"from_attributes": True}


class MarketListResponse(BaseModel):
    """List of markets."""

    success: bool = True
    message: str = "OK"
    data: List[MarketResponse] = Field(default_factory=list)
    total: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
