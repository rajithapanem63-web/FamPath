"""Aptitude quiz models: QuizQuestion, QuizSession, QuizResponse, AptitudeResult."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from app.models.base import GUID  # SQLite-compat
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class QuizQuestion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "quiz_questions"

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_te: Mapped[str | None] = mapped_column(Text)
    question_hi: Mapped[str | None] = mapped_column(Text)
    riasec_dimension: Mapped[str] = mapped_column(String(10), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, nullable=False)
    options: Mapped[list | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("users.id"))


class QuizSession(UUIDPKMixin, Base):
    __tablename__ = "quiz_sessions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)
    question_order: Mapped[list | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuizResponse(UUIDPKMixin, Base):
    __tablename__ = "quiz_responses"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("quiz_sessions.id"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("quiz_questions.id"), nullable=False
    )
    response_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AptitudeResult(UUIDPKMixin, Base):
    __tablename__ = "aptitude_results"

    student_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("quiz_sessions.id"), nullable=False
    )
    riasec_scores: Mapped[dict | None] = mapped_column(JSONB)
    branch_fit_scores: Mapped[dict | None] = mapped_column(JSONB)
    top_branches: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
