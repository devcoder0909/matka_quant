"""
Project Trinetra - Audit Logging Utility.

Provides a lightweight helper to write audit trail entries
for any state-changing operation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Write an audit log entry.

    Args:
        db: Async database session.
        user_id: ID of the acting user (None for system actions).
        action: Short verb phrase, e.g. "import_chart", "run_analysis".
        target_type: Entity type acted upon (e.g. "market", "import").
        target_id: Entity identifier.
        details: Arbitrary JSON-serialisable context dict.
        ip_address: Client IP if available.

    Returns:
        The created AuditLog ORM instance (already flushed to session).
    """
    details_json: Optional[str] = None
    if details is not None:
        details_json = json.dumps(details, default=str)

    entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details_json=details_json,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry
