"""
Project Trinetra - Backtest API Routes (Phase 1 Placeholder)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.market import Market
from app.analysis.engine import _records_from_db_rows
from app.analysis.backtest_engine import run_walk_forward_backtest

router = APIRouter()

@router.post("/run/{market_code}")
async def start_backtest(market_code: str, days: int = 30, db: AsyncSession = Depends(get_db)):
    """
    Start walk-forward backtest on the specified market
    """
    market = await db.scalar(select(Market).where(Market.code == market_code.upper()))
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
        
    from sqlalchemy import text
    query = text(
        "SELECT date, open_patti, open_ank, jodi, close_ank, close_patti, market_code "
        "FROM results WHERE market_id = :mid ORDER BY date"
    )
    result = await db.execute(query, {"mid": market.id})
    rows = result.fetchall()
    records = _records_from_db_rows(rows)
    
    if len(records) < days + 10:
        raise HTTPException(status_code=400, detail="Not enough historical data")
        
    backtest_results = run_walk_forward_backtest(records, test_window_days=days)
    return backtest_results
