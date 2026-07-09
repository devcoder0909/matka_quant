"""
Project Trinetra - Markets API.

Endpoints for listing and retrieving market information enriched
with historical data statistics.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.market import Market
from app.models.historical_result import HistoricalResult
from app.schemas.common import APIResponse
from app.schemas.market import MarketListResponse, MarketResponse

router = APIRouter()


@router.get(
    "",
    response_model=MarketListResponse,
    summary="List all markets",
    description="Returns every configured market with record counts and date ranges.",
)
async def list_markets(db: AsyncSession = Depends(get_db)) -> MarketListResponse:
    """Return all markets with enriched statistics."""
    result = await db.execute(select(Market).order_by(Market.name))
    markets = result.scalars().all()

    market_responses: list[MarketResponse] = []
    for m in markets:
        # Fetch record count and date range for this market
        stats_query = select(
            func.count(HistoricalResult.id).label("cnt"),
            func.min(HistoricalResult.result_date).label("min_date"),
            func.max(HistoricalResult.result_date).label("max_date"),
        ).where(HistoricalResult.market_id == m.id)

        stats_result = await db.execute(stats_query)
        stats_row = stats_result.one()

        market_responses.append(
            MarketResponse(
                id=m.id,
                name=m.name,
                code=m.code,
                display_name=m.display_name,
                schedule=m.schedule,
                is_active=m.is_active,
                created_at=m.created_at,
                updated_at=m.updated_at,
                record_count=stats_row.cnt or 0,
                date_range_start=stats_row.min_date,
                date_range_end=stats_row.max_date,
            )
        )

    return MarketListResponse(
        data=market_responses,
        total=len(market_responses),
    )


@router.get(
    "/{market_code}",
    response_model=APIResponse[MarketResponse],
    summary="Get market details",
    description="Returns a single market by code with record count and date range.",
)
async def get_market(
    market_code: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MarketResponse]:
    """Return a single market by its code."""
    result = await db.execute(
        select(Market).where(Market.code == market_code.upper())
    )
    market = result.scalar_one_or_none()

    if market is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with code '{market_code.upper()}' not found",
        )

    # Stats
    stats_query = select(
        func.count(HistoricalResult.id).label("cnt"),
        func.min(HistoricalResult.result_date).label("min_date"),
        func.max(HistoricalResult.result_date).label("max_date"),
    ).where(HistoricalResult.market_id == market.id)

    stats_result = await db.execute(stats_query)
    stats_row = stats_result.one()

    market_resp = MarketResponse(
        id=market.id,
        name=market.name,
        code=market.code,
        display_name=market.display_name,
        schedule=market.schedule,
        is_active=market.is_active,
        created_at=market.created_at,
        updated_at=market.updated_at,
        record_count=stats_row.cnt or 0,
        date_range_start=stats_row.min_date,
        date_range_end=stats_row.max_date,
    )

    return APIResponse(data=market_resp, message="Market retrieved successfully")

@router.get(
    "/{market_code}/latest",
    response_model=APIResponse[list],
    summary="Get latest market results",
    description="Returns the most recent 7 results for the market to show what was last imported.",
)
async def get_latest_results(
    market_code: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list]:
    """Return the 7 most recent results for a market."""
    market_result = await db.execute(
        select(Market).where(Market.code == market_code.upper())
    )
    market = market_result.scalar_one_or_none()

    if market is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with code '{market_code.upper()}' not found",
        )

    results_query = (
        select(HistoricalResult)
        .where(HistoricalResult.market_id == market.id)
        .order_by(HistoricalResult.result_date.desc())
        .limit(7)
    )
    
    records = await db.execute(results_query)
    
    data = []
    for r in records.scalars().all():
        data.append({
            "date": r.result_date.isoformat(),
            "open_patti": r.open_patti,
            "open_ank": r.open_ank,
            "jodi": r.jodi,
            "close_ank": r.close_ank,
            "close_patti": r.close_patti
        })
        
    data.reverse()
        
    return APIResponse(data=data, message="Latest results retrieved successfully")
