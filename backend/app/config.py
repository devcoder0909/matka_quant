"""
Project Trinetra - Application Configuration.

Environment-based configuration using pydantic-settings.
Reads from .env file or environment variables.
"""

from __future__ import annotations

import secrets
from typing import List
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/trinetra",
        description="Database connection string",
    )

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ADMIN_PASSWORD: str = "trinetra2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── General ───────────────────────────────────────────────────────────
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Matka Quantum AI - Project Trinetra"
    VERSION: str = "1.0.0"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
