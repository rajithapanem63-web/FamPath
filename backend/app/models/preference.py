"""Enhanced preference response model for structured questionnaire data."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import JSON as JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import GUID, UUIDPKMixin


class PreferenceDimension(str, enum.Enum):
    """Valid preference dimensions."""
    BRANCH = "branch_preference"
    LOCATION = "location_preference"
    COLLEGE_TYPE = "college_type_preference"
    BUDGET = "budget_constraint"
    PLACEMENT = "placement_importance"
    FACILITIES = "campus_facilities"
    REPUTATION = "reputation_ranking"
    CAREER_GOAL = "career_goal"


class PreferenceWeight(int, enum.Enum):
    """Preference weight levels."""
    LOW = 3
    MEDIUM = 6
    HIGH = 9


class PreferenceResponse(UUIDPKMixin, Base):
    """
    Structured preference responses for family members.
    
    Each row represents one dimension's response for a user in a workspace.
    Supports versioning: when updated, old version is marked inactive.
    """
    __tablename__ = "preference_responses"
    
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("family_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dimension: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    weight: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    selected_options: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )
    additional_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )
    
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            "dimension",
            "version",
            name="unique_preference_version"
        ),
        CheckConstraint(
            "weight IN (3, 6, 9)",
            name="valid_weight"
        ),
        CheckConstraint(
            "dimension IN ('branch_preference', 'location_preference', 'college_type_preference', 'budget_constraint', 'placement_importance', 'campus_facilities', 'reputation_ranking', 'career_goal')",
            name="valid_dimension"
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<PreferenceResponse("
            f"user={self.user_id}, "
            f"dimension={self.dimension}, "
            f"weight={self.weight}, "
            f"version={self.version}, "
            f"active={self.is_active})>"
        )
