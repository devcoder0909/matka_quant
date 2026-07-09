"""
Project Trinetra - Charts & Import API.

Endpoints for importing chart data from various formats (HTML, CSV, JSON, text),
validating without importing, and reviewing import history.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chart_import import ChartImport, ImportErrorRecord
from app.models.historical_result import HistoricalResult
from app.models.market import Market
from app.schemas.chart import (
    ChartImportRequest,
    ChartImportResponse,
    ChartValidateRequest,
    FileUploadResponse,
    ImportDetailResponse,
    ImportErrorDetail,
    ImportHistoryItem,
    ImportHistoryResponse,
    ValidationReport,
)
from app.schemas.common import APIResponse
from app.utils.audit import log_action
from app.utils.sanitizer import sanitize_html

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Parser imports (graceful fallback) ────────────────────────────────────────

_PARSER_AVAILABLE = False
_PARSER_ERROR_MSG = ""

try:
    from app.parser.html_parser import parse_html_chart  # type: ignore[import-untyped]
    from app.parser.csv_parser import parse_csv_data  # type: ignore[import-untyped]
    from app.parser.json_parser import parse_json_data  # type: ignore[import-untyped]
    from app.parser.text_parser import parse_text_data  # type: ignore[import-untyped]
    from app.parser.detector import detect_market  # type: ignore[import-untyped]
    from app.parser.validator import validate_records  # type: ignore[import-untyped]
    from app.parser.normalizer import normalize_records  # type: ignore[import-untyped]

    _PARSER_AVAILABLE = True
except ImportError as exc:
    _PARSER_ERROR_MSG = (
        f"Parser modules not yet available ({exc}). "
        "Chart import functionality will be enabled once the parser package is installed."
    )
    logger.warning(_PARSER_ERROR_MSG)


def _require_parser() -> None:
    """Raise 503 if the parser package is not installed yet."""
    if not _PARSER_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_PARSER_ERROR_MSG,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_data(data: str) -> str:
    """SHA-256 hash for deduplication."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


async def _resolve_market(db: AsyncSession, code: Optional[str]) -> Optional[Market]:
    """Look up a Market by code. Returns None if code is None or not found."""
    if not code:
        return None
    result = await db.execute(select(Market).where(Market.code == code.upper()))
    return result.scalar_one_or_none()


async def _store_results(
    db: AsyncSession,
    market: Market,
    records: list[dict],
) -> tuple[int, int]:
    """
    Persist validated records into historical_results using bulk operations.
    Returns: (inserted_count, duplicate_count)
    """
    inserted = 0
    duplicates = 0

    # Bulk query all existing dates for this market to avoid N+1 queries
    existing_result = await db.execute(
        select(HistoricalResult.result_date).where(HistoricalResult.market_id == market.id)
    )
    existing_dates = {row[0] for row in existing_result.all()}

    new_records_to_insert = []

    for rec in records:
        # Parse the date
        result_date = rec.get("date")
        if isinstance(result_date, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    result_date = datetime.strptime(result_date, fmt).date()
                    break
                except ValueError:
                    continue
        if not isinstance(result_date, date):
            continue

        if result_date in existing_dates:
            duplicates += 1
            continue
            
        # Also ensure we don't insert duplicates within the SAME batch
        existing_dates.add(result_date)

        # Parse ank values
        open_ank = rec.get("open_ank")
        close_ank = rec.get("close_ank")
        if open_ank is not None:
            try:
                open_ank = int(open_ank)
            except (ValueError, TypeError):
                open_ank = None
        if close_ank is not None:
            try:
                close_ank = int(close_ank)
            except (ValueError, TypeError):
                close_ank = None

        hist = HistoricalResult(
            market_id=market.id,
            result_date=result_date,
            open_patti=rec.get("open_patti"),
            open_ank=open_ank,
            jodi=rec.get("jodi"),
            close_ank=close_ank,
            close_patti=rec.get("close_patti"),
            is_validated=True,
        )
        new_records_to_insert.append(hist)
        inserted += 1

    if new_records_to_insert:
        db.add_all(new_records_to_insert)
        await db.flush()

    return inserted, duplicates


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/import",
    response_model=ChartImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import chart data from HTML/text",
)
async def import_chart(
    body: ChartImportRequest,
    db: AsyncSession = Depends(get_db),
) -> ChartImportResponse:
    """Parse and import chart data from raw HTML or text input."""
    _require_parser()

    # Sanitize
    safe_html = sanitize_html(body.raw_html)
    data_hash = _hash_data(safe_html)

    # Check for duplicate import
    dup_check = await db.execute(
        select(ChartImport).where(ChartImport.raw_data_hash == data_hash)
    )
    if dup_check.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This exact data has already been imported.",
        )

    # Create import record
    import_rec = ChartImport(
        source_type=body.source_type,
        raw_data_hash=data_hash,
        status="processing",
    )
    db.add(import_rec)
    await db.flush()

    try:
        # Parse
        if body.source_type == "text":
            records = parse_text_data(safe_html)
        else:
            records = parse_html_chart(safe_html)

        # Detect / resolve market
        market_code = body.market_code
        if not market_code and records:
            market_code = detect_market(records, body.raw_html)

        market = await _resolve_market(db, market_code)
        if market:
            import_rec.market_id = market.id

        # Validate
        validation = validate_records(records)
        valid_records = normalize_records(validation.valid_records)

        import_rec.total_records = len(records)
        import_rec.valid_records = len(valid_records)
        import_rec.invalid_records = len(validation.invalid_records)
        import_rec.data_quality_score = validation.quality_score
        import_rec.data_completeness_score = validation.completeness_score

        # Store validated records
        if market and valid_records:
            inserted, dups = await _store_results(db, market, valid_records)
            import_rec.valid_records = inserted
            import_rec.duplicate_records = dups

        # Record errors
        error_details: list[ImportErrorDetail] = []
        for err in validation.errors:
            err_rec = ImportErrorRecord(
                import_id=import_rec.id,
                row_number=getattr(err, "row_number", None),
                column_name=getattr(err, "column_name", None),
                error_type=getattr(err, "error_type", "validation"),
                error_detail=getattr(err, "error_detail", str(err)),
                raw_value=getattr(err, "raw_value", None),
            )
            db.add(err_rec)
            error_details.append(
                ImportErrorDetail(
                    row_number=err_rec.row_number,
                    column_name=err_rec.column_name,
                    error_type=err_rec.error_type,
                    error_detail=err_rec.error_detail,
                    raw_value=err_rec.raw_value,
                )
            )

        import_rec.status = "completed"
        await db.flush()

        # Audit
        await log_action(
            db,
            user_id=None,
            action="import_chart",
            target_type="chart_import",
            target_id=str(import_rec.id),
            details={
                "source_type": body.source_type,
                "market_code": market_code,
                "total": import_rec.total_records,
                "valid": import_rec.valid_records,
            },
        )

        return ChartImportResponse(
            import_id=import_rec.id,
            market_code=market.code if market else None,
            market_name=market.display_name if market else None,
            source_type=import_rec.source_type,
            total_records=import_rec.total_records,
            valid_records=import_rec.valid_records,
            duplicate_records=import_rec.duplicate_records,
            invalid_records=import_rec.invalid_records,
            missing_records=import_rec.missing_records,
            data_quality_score=import_rec.data_quality_score,
            data_completeness_score=import_rec.data_completeness_score,
            errors=error_details,
        )

    except HTTPException:
        raise
    except Exception as exc:
        import_rec.status = "failed"
        import_rec.error_message = str(exc)[:2000]
        await db.flush()
        logger.exception("Chart import failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {exc}",
        )


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV or JSON file",
)
async def upload_file(
    file: UploadFile = File(...),
    market_code: Optional[str] = Query(None, description="Market code if known"),
    db: AsyncSession = Depends(get_db),
) -> FileUploadResponse:
    """Accept a file upload (CSV/JSON), parse, validate, and store results."""
    _require_parser()

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    # Determine source type
    filename_lower = (file.filename or "").lower()
    if filename_lower.endswith(".csv"):
        source_type = "csv"
    elif filename_lower.endswith(".json"):
        source_type = "json"
    else:
        source_type = "text"

    data_hash = hashlib.sha256(content).hexdigest()

    # Create import record
    import_rec = ChartImport(
        source_type=source_type,
        raw_data_hash=data_hash,
        file_name=file.filename,
        status="processing",
    )
    db.add(import_rec)
    await db.flush()

    try:
        # Parse by type
        if source_type == "csv":
            records = parse_csv_data(content, file.filename)
        elif source_type == "json":
            records = parse_json_data(content.decode("utf-8"))
        else:
            records = parse_text_data(content.decode("utf-8"))

        # Market resolution
        resolved_code = market_code
        if not resolved_code and records:
            resolved_code = detect_market(records, content.decode("utf-8", errors="replace"))

        market = await _resolve_market(db, resolved_code)
        if market:
            import_rec.market_id = market.id

        # Validate
        validation = validate_records(records)
        valid_records = normalize_records(validation.valid_records)

        import_rec.total_records = len(records)
        import_rec.valid_records = len(valid_records)
        import_rec.invalid_records = len(validation.invalid_records)
        import_rec.data_quality_score = validation.quality_score
        import_rec.data_completeness_score = validation.completeness_score

        # Store
        if market and valid_records:
            inserted, dups = await _store_results(db, market, valid_records)
            import_rec.valid_records = inserted
            import_rec.duplicate_records = dups

        # Errors
        error_details: list[ImportErrorDetail] = []
        for err in validation.errors:
            err_rec = ImportErrorRecord(
                import_id=import_rec.id,
                row_number=getattr(err, "row_number", None),
                column_name=getattr(err, "column_name", None),
                error_type=getattr(err, "error_type", "validation"),
                error_detail=getattr(err, "error_detail", str(err)),
                raw_value=getattr(err, "raw_value", None),
            )
            db.add(err_rec)
            error_details.append(
                ImportErrorDetail(
                    row_number=err_rec.row_number,
                    column_name=err_rec.column_name,
                    error_type=err_rec.error_type,
                    error_detail=err_rec.error_detail,
                    raw_value=err_rec.raw_value,
                )
            )

        import_rec.status = "completed"
        await db.flush()

        await log_action(
            db,
            user_id=None,
            action="upload_file",
            target_type="chart_import",
            target_id=str(import_rec.id),
            details={"file": file.filename, "source_type": source_type, "market": resolved_code},
        )

        return FileUploadResponse(
            import_id=import_rec.id,
            file_name=file.filename or "",
            source_type=source_type,
            total_records=import_rec.total_records,
            valid_records=import_rec.valid_records,
            duplicate_records=import_rec.duplicate_records,
            invalid_records=import_rec.invalid_records,
            missing_records=import_rec.missing_records,
            data_quality_score=import_rec.data_quality_score,
            data_completeness_score=import_rec.data_completeness_score,
            errors=error_details,
        )

    except HTTPException:
        raise
    except Exception as exc:
        import_rec.status = "failed"
        import_rec.error_message = str(exc)[:2000]
        await db.flush()
        logger.exception("File upload processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {exc}",
        )


@router.post(
    "/validate",
    response_model=APIResponse[ValidationReport],
    summary="Validate data without importing",
)
async def validate_data(
    body: ChartValidateRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ValidationReport]:
    """Parse and validate chart data without persisting. Useful for dry-run checks."""
    _require_parser()

    safe_html = sanitize_html(body.raw_html)

    try:
        records = parse_html_chart(safe_html)
        validation = validate_records(records)
        valid_list = normalize_records(validation.valid_records)

        report = ValidationReport(
            total_records=len(records),
            valid_records=len(valid_list),
            invalid_records=len(validation.invalid_records),
            duplicate_records=validation.duplicate_records if hasattr(validation, "duplicate_records") else 0,
            data_quality_score=validation.quality_score,
            data_completeness_score=validation.completeness_score,
            errors=[
                ImportErrorDetail(
                    row_number=getattr(e, "row_number", None),
                    column_name=getattr(e, "column_name", None),
                    error_type=getattr(e, "error_type", "validation"),
                    error_detail=getattr(e, "error_detail", str(e)),
                    raw_value=getattr(e, "raw_value", None),
                )
                for e in validation.errors
            ],
            sample_valid=valid_list[:5],
        )

        return APIResponse(data=report, message="Validation complete")

    except Exception as exc:
        logger.exception("Validation failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation failed: {exc}",
        )


@router.get(
    "/imports",
    response_model=ImportHistoryResponse,
    summary="List import history",
)
async def list_imports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ImportHistoryResponse:
    """Return paginated import history, most recent first."""
    # Count
    count_result = await db.execute(select(func.count()).select_from(ChartImport))
    total = count_result.scalar_one()

    # Fetch page
    offset = (page - 1) * page_size
    result = await db.execute(
        select(ChartImport)
        .order_by(ChartImport.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    imports = result.scalars().all()

    items: list[ImportHistoryItem] = []
    for imp in imports:
        market = imp.market
        items.append(
            ImportHistoryItem(
                id=imp.id,
                market_code=market.code if market else None,
                market_name=market.display_name if market else None,
                source_type=imp.source_type,
                file_name=imp.file_name,
                total_records=imp.total_records,
                valid_records=imp.valid_records,
                duplicate_records=imp.duplicate_records,
                invalid_records=imp.invalid_records,
                missing_records=imp.missing_records,
                data_quality_score=imp.data_quality_score,
                data_completeness_score=imp.data_completeness_score,
                status=imp.status,
                error_message=imp.error_message,
                created_at=imp.created_at,
            )
        )

    return ImportHistoryResponse(data=items, total=total)


@router.get(
    "/imports/{import_id}",
    response_model=APIResponse[ImportDetailResponse],
    summary="Get import details with errors",
)
async def get_import_detail(
    import_id: int,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ImportDetailResponse]:
    """Return full import detail including row-level errors."""
    result = await db.execute(
        select(ChartImport).where(ChartImport.id == import_id)
    )
    imp = result.scalar_one_or_none()

    if imp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import with id {import_id} not found",
        )

    market = imp.market
    info = ImportHistoryItem(
        id=imp.id,
        market_code=market.code if market else None,
        market_name=market.display_name if market else None,
        source_type=imp.source_type,
        file_name=imp.file_name,
        total_records=imp.total_records,
        valid_records=imp.valid_records,
        duplicate_records=imp.duplicate_records,
        invalid_records=imp.invalid_records,
        missing_records=imp.missing_records,
        data_quality_score=imp.data_quality_score,
        data_completeness_score=imp.data_completeness_score,
        status=imp.status,
        error_message=imp.error_message,
        created_at=imp.created_at,
    )

    errors = [
        ImportErrorDetail(
            row_number=e.row_number,
            column_name=e.column_name,
            error_type=e.error_type,
            error_detail=e.error_detail,
            raw_value=e.raw_value,
        )
        for e in imp.errors
    ]

    detail = ImportDetailResponse(import_info=info, errors=errors)
    return APIResponse(data=detail, message="Import details retrieved")
