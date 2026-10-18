"""Career roadmap and student skill progression models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from app.models.base import GUID  # SQLite-compat
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class StudentCareerGoal(UUIDPKMixin, TimestampMixin, Base):
    """Tracks a student's preferred engineering branch, target career role, and roadmap milestones."""

    __tablename__ = "student_career_goals"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_student_career_goal"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    branch_code: Mapped[str] = mapped_column(String(20), nullable=False)
    career_role: Mapped[str] = mapped_column(String(100), nullable=False)
    current_semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    completed_milestones: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
