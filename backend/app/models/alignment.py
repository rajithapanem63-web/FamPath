"""Family alignment and mediator models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from app.models.base import GUID  # SQLite-compat
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPKMixin


class PreferenceSubmission(UUIDPKMixin, Base):
    __tablename__ = "preference_submissions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    preferences: Mapped[dict | None] = mapped_column(JSONB)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AlignmentSnapshot(UUIDPKMixin, Base):
    __tablename__ = "alignment_snapshots"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, unique=True, index=True
    )
    alignment_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    dimension_scores: Mapped[dict | None] = mapped_column(JSONB)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MediationSession(UUIDPKMixin, Base):
    __tablename__ = "mediation_sessions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    conflict_dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    request_text: Mapped[str | None] = mapped_column(Text)
    response: Mapped[dict | None] = mapped_column(JSONB)
    model_version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
