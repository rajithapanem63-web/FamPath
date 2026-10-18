"""
Family workspace ORM models: FamilyWorkspace, WorkspaceMember, WorkspaceInvitation, UserProfile.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from app.models.base import GUID  # SQLite-compat
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class FamilyWorkspace(UUIDPKMixin, TimestampMixin, Base):
    """A shared decision-making space for a student and their family."""

    __tablename__ = "family_workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", lazy="selectin"
    )
    invitations: Mapped[list["WorkspaceInvitation"]] = relationship(back_populates="workspace")

    def __repr__(self) -> str:
        return f"<FamilyWorkspace {self.name}>"


class WorkspaceMember(UUIDPKMixin, Base):
    """Links a user to a workspace with a role and consent status."""

    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    workspace: Mapped["FamilyWorkspace"] = relationship(back_populates="members")


class WorkspaceInvitation(UUIDPKMixin, Base):
    """Email invitation to join a family workspace."""

    __tablename__ = "workspace_invitations"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), nullable=False, index=True
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False
    )
    invited_email: Mapped[str] = mapped_column(String(255), nullable=False)
    invited_role: Mapped[str] = mapped_column(String(20), default="parent", nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    workspace: Mapped["FamilyWorkspace"] = relationship(back_populates="invitations")


class UserProfile(UUIDPKMixin, TimestampMixin, Base):
    """
    Extended profile for a user within a workspace.
    Sensitive fields (rank, income) are stored encrypted.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("family_workspaces.id"), index=True
    )
    profile_type: Mapped[str | None] = mapped_column(String(20))

    # Student fields
    exam_type: Mapped[str | None] = mapped_column(String(20))
    rank_encrypted: Mapped[str | None] = mapped_column(Text)  # AES-256-GCM encrypted
    category: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(10))
    home_district: Mapped[str | None] = mapped_column(String(100))
    home_state: Mapped[str | None] = mapped_column(String(100))

    # Parent fields
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    location_pref: Mapped[dict | None] = mapped_column(JSONB)
    career_priorities: Mapped[dict | None] = mapped_column(JSONB)
    income_range_encrypted: Mapped[str | None] = mapped_column(Text)  # encrypted
