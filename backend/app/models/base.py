"""
Shared base mixin for all ORM models: UUID primary key, created_at, updated_at.
Works with both PostgreSQL and SQLite.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

from app.core.database import Base


class GUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL UUID natively; CHAR(36) string for SQLite.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value) if isinstance(value, uuid.UUID) else str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class TimestampMixin:
    """Adds created_at and updated_at columns with auto-management."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPKMixin:
    """UUID primary key — works on PostgreSQL and SQLite."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
