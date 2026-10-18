"""
Authentication ORM models: User, EmailToken, RefreshToken.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import GUID, TimestampMixin, UUIDPKMixin


class User(UUIDPKMixin, TimestampMixin, Base):
    """Platform user. Roles: student | parent | counsellor | admin."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_verification"
    )
    full_name: Mapped[str | None] = mapped_column(String(255))
    preferred_locale: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    otp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    email_tokens: Mapped[list["EmailToken"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")

    @property
    def is_active(self) -> bool:
        return self.status == "active" and self.deleted_at is None

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


class EmailToken(UUIDPKMixin, Base):
    """Single-use token for email verification, password reset, or workspace invite."""

    __tablename__ = "email_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="email_tokens")

    @property
    def is_valid(self) -> bool:
        from datetime import UTC, timezone
        # Make both datetimes timezone-aware for comparison
        now = datetime.now(UTC)
        expires = self.expires_at
        # If expires_at is naive (from SQLite), make it UTC
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return self.used_at is None and expires > now


class RefreshToken(UUIDPKMixin, Base):
    """Rotatable refresh token with theft-detection via family_id."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        from datetime import UTC
        return self.revoked_at is None and self.expires_at > datetime.now(UTC)
