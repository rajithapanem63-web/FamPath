"""Audit logging service — append-only writes to audit_logs."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = structlog.get_logger(__name__)


async def log_audit_event(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write an immutable audit record. Never raises — failures are logged."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_=metadata,
            created_at=datetime.now(UTC),
        )
        db.add(entry)
        # Flush without committing (caller's transaction commits it)
        await db.flush()
    except Exception as exc:
        logger.error("audit_log_failed", action=action, error=str(exc))
