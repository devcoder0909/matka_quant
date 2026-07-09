"""
Project Trinetra - Common Response Schemas.

Generic wrappers used across all API endpoints for consistent
response structure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = True
    message: str = "OK"
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    success: bool = True
    message: str = "OK"
    data: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Error response body."""

    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Simple success acknowledgement."""

    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
