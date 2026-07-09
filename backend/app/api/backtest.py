"""
Project Trinetra - Backtest API Routes (Phase 1 Placeholder)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter()

@router.post("/run")
async def start_backtest(db: AsyncSession = Depends(get_db)):
    """
    Start walk-forward backtest (Coming in Phase 2)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backtesting engine will be available in Phase 2"
    )

@router.get("/{run_id}")
async def get_backtest_results(run_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get backtest results (Coming in Phase 2)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Backtesting engine will be available in Phase 2"
    )
