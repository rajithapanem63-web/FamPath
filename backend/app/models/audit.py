"""Audit log model — append-only, no UPDATE or DELETE."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import GUID  # SQLite-compat UUID
from app.core.database import Base
from app.models.base import UUIDPKMixin


class AuditLog(UUIDPKMixin, Base):
    """Immutable audit record for sensitive platform actions."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    ip_address: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
