"""
Project Trinetra - Chart / Import Schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class ChartImportRequest(BaseModel):
    """Body for POST /charts/import."""

    raw_html: str = Field(..., min_length=10, description="Raw HTML or text containing chart data")
    market_code: Optional[str] = Field(None, description="Market code if known (e.g. KALYAN)")
    source_type: str = Field("html", description="Source format: html, text")


class ChartValidateRequest(BaseModel):
    """Body for POST /charts/validate (dry-run)."""

    raw_html: str = Field(..., min_length=10)
    market_code: Optional[str] = None


# ── Validation detail ────────────────────────────────────────────────────────

class ImportErrorDetail(BaseModel):
    """Single import error."""

    row_number: Optional[int] = None
    column_name: Optional[str] = None
    error_type: str
    error_detail: Optional[str] = None
    raw_value: Optional[str] = None


class ValidationReport(BaseModel):
    """Validation summary returned from validate endpoint."""

    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    missing_records: int = 0
    data_quality_score: Optional[float] = None
    data_completeness_score: Optional[float] = None
    errors: List[ImportErrorDetail] = Field(default_factory=list)
    sample_valid: List[Dict[str, Any]] = Field(
        default_factory=list, description="First 5 valid records for preview",
    )


# ── Response ──────────────────────────────────────────────────────────────────

class ChartImportResponse(BaseModel):
    """Response from POST /charts/import."""

    success: bool = True
    message: str = "Import completed"
    import_id: int
    market_code: Optional[str] = None
    market_name: Optional[str] = None
    source_type: str = "html"
    total_records: int = 0
    valid_records: int = 0
    duplicate_records: int = 0
    invalid_records: int = 0
    missing_records: int = 0
    data_quality_score: Optional[float] = None
    data_completeness_score: Optional[float] = None
    errors: List[ImportErrorDetail] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileUploadResponse(BaseModel):
    """Response from POST /charts/upload."""

    success: bool = True
    message: str = "Upload processed"
    import_id: int
    file_name: str
    source_type: str
    total_records: int = 0
    valid_records: int = 0
    duplicate_records: int = 0
    invalid_records: int = 0
    missing_records: int = 0
    data_quality_score: Optional[float] = None
    data_completeness_score: Optional[float] = None
    errors: List[ImportErrorDetail] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImportHistoryItem(BaseModel):
    """Single import history entry."""

    id: int
    market_code: Optional[str] = None
    market_name: Optional[str] = None
    source_type: str
    file_name: Optional[str] = None
    total_records: int
    valid_records: int
    duplicate_records: int
    invalid_records: int
    missing_records: int
    data_quality_score: Optional[float] = None
    data_completeness_score: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportHistoryResponse(BaseModel):
    """List of past imports."""

    success: bool = True
    message: str = "OK"
    data: List[ImportHistoryItem] = Field(default_factory=list)
    total: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImportDetailResponse(BaseModel):
    """Full import detail with errors."""

    success: bool = True
    message: str = "OK"
    import_info: ImportHistoryItem
    errors: List[ImportErrorDetail] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
