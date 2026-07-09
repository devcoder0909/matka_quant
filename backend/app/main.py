"""
Project Trinetra - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.config import settings
from app.database import init_db, async_session
from app.models.market import seed_markets
from app.api.router import api_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Project Trinetra API...")
    await init_db()
    
    # Seed markets
    async with async_session() as session:
        inserted = await seed_markets(session)
        if inserted > 0:
            logger.info(f"Seeded {inserted} markets.")
    
    yield
    # Shutdown
    logger.info("Shutting down Project Trinetra API...")

app = FastAPI(
    title="Matka Quantum AI - Project Trinetra API",
    description="Advanced Historical Chart Analysis & Probability Research Engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {"status": "online", "system": "Project Trinetra"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
