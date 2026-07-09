"""
Project Trinetra - Analysis API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import re

from app.database import get_db
from app.models.market import Market
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.analysis.engine import run_analysis

router = APIRouter()

class CommandRequest(BaseModel):
    command: str
from typing import Any

@router.post("/run", response_model=Any)
async def start_analysis(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """
    Run Trinetra analysis on a specific market up to a target date.
    """
    market = await db.scalar(select(Market).where(Market.code == request.market_code))
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market not found: {request.market_code}"
        )
    
    try:
        result = await run_analysis(db, market.id, request.target_date, request.market_code)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.get("/{run_id}", response_model=AnalysisResponse)
async def get_analysis_result(run_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a past analysis result by ID. (Stub for Phase 1 - returns 404)
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Fetching past runs will be implemented in Phase 2"
    )

@router.get("/{run_id}/status")
async def check_analysis_status(run_id: int, db: AsyncSession = Depends(get_db)):
    """
    Check the status of an ongoing analysis.
    """
    return {"run_id": run_id, "status": "COMPLETED"}

@router.post("/command")
async def process_command(request: CommandRequest, db: AsyncSession = Depends(get_db)):
    """
    Process text commands from the dashboard.
    """
    cmd = request.command.strip().upper()
    
    if cmd == "RUN TRINETRA ANALYSIS":
        return {"action": "OPEN_ANALYSIS_MODAL", "message": "Select market and date to run analysis"}
    
    if cmd.startswith("ANALYZE "):
        market_name = cmd.replace("ANALYZE ", "").strip()
        market_code = market_name.replace(" ", "_")
        
        market = await db.scalar(select(Market).where(Market.code == market_code))
        if market:
            return {
                "action": "RUN_ANALYSIS", 
                "market_code": market.code,
                "message": f"Initializing analysis for {market.display_name}..."
            }
        else:
            return {"action": "ERROR", "message": f"Unknown market: {market_name}"}
            
    if cmd == "IMPORT CHART":
        return {"action": "NAVIGATE", "target": "import", "message": "Opening import panel..."}
        
    if cmd == "VALIDATE DATA":
        return {"action": "NAVIGATE", "target": "quality", "message": "Opening data quality dashboard..."}
        
    return {"action": "ERROR", "message": f"Command not recognized: {cmd}"}
