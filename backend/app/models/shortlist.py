"""Shortlist, decision log, timeline and checklist models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from app.models.base import GUID  # SQLite-compat
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class ShortlistItem(UUIDPKMixin, Base):
    __tablename__ = "shortlist_items"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "college_id", "program_id", name="uq_shortlist_item"
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    college_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("colleges.id"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("college_programs.id"), nullable=False
    )
    added_by: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False
    )
    is_final_choice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cost_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    prediction_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ShortlistVote(UUIDPKMixin, Base):
    __tablename__ = "shortlist_votes"
    __table_args__ = (
        UniqueConstraint("shortlist_item_id", "user_id", name="uq_shortlist_vote"),
    )

    shortlist_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("shortlist_items.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False
    )
    vote: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DecisionLogEntry(UUIDPKMixin, Base):
    __tablename__ = "decision_log_entries"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CounsellingEvent(UUIDPKMixin, Base):
    __tablename__ = "counselling_events"

    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_name_te: Mapped[str | None] = mapped_column(String(255))
    event_name_hi: Mapped[str | None] = mapped_column(String(255))
    event_year: Mapped[int] = mapped_column(Integer, nullable=False)
    event_date: Mapped[datetime | None] = mapped_column(Date)
    round_number: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))


class DocumentChecklistItem(UUIDPKMixin, Base):
    __tablename__ = "document_checklist_items"

    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category_filter: Mapped[str | None] = mapped_column(String(20))
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_name_te: Mapped[str | None] = mapped_column(String(255))
    document_name_hi: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkspaceChecklistStatus(UUIDPKMixin, Base):
    __tablename__ = "workspace_checklist_status"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    checklist_item_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("document_checklist_items.id"), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(UUIDPKMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("family_workspaces.id")
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AdmissionTask(UUIDPKMixin, TimestampMixin, Base):
    """Personalized and official admission tasks and reminders."""
    __tablename__ = "admission_tasks"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))
    source_type: Mapped[str] = mapped_column(String(20), default="user_entered", nullable=False)  # 'official' | 'user_entered'
    source_citation: Mapped[str | None] = mapped_column(String(255))
