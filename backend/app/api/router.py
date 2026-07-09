"""
Project Trinetra - Main API Router.

Aggregates all sub-routers into a single router that is mounted
on the application under settings.API_PREFIX.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.markets import router as markets_router
from app.api.charts import router as charts_router
from app.api.analysis import router as analysis_router
from app.api.backtest import router as backtest_router

api_router = APIRouter()

api_router.include_router(markets_router, prefix="/markets", tags=["Markets"])
api_router.include_router(charts_router, prefix="/charts", tags=["Charts & Import"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(backtest_router, prefix="/backtest", tags=["Backtesting"])
