"""Family workspace service: create, invite, accept, consent, member management."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_field, generate_secure_token, hash_token
from app.models.auth import User
from app.models.workspace import FamilyWorkspace, WorkspaceInvitation, WorkspaceMember, UserProfile
from app.schemas.workspace_schema import (
    CreateWorkspaceRequest,
    StudentProfileRequest,
    ParentProfileRequest,
)

logger = structlog.get_logger(__name__)

INVITATION_EXPIRE_DAYS = 7
MAX_WORKSPACE_MEMBERS = 10


async def create_workspace(
    name: str,
    owner: User,
    db: AsyncSession,
) -> FamilyWorkspace:
    """Create a new family workspace for a student."""
    workspace = FamilyWorkspace(
        name=name,
        owner_id=owner.id,
        status="active",
    )
    db.add(workspace)
    await db.flush()

    # Add owner as student member
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner.id,
        role="student",
        consent_given=False,
        created_at=datetime.now(UTC),
    )
    db.add(member)
    logger.info("workspace_created", workspace_id=str(workspace.id), owner_id=str(owner.id))
    return workspace


async def get_user_workspaces(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> list[FamilyWorkspace]:
    """Fetch all active workspaces where user is an active member."""
    result = await db.execute(
        select(FamilyWorkspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == FamilyWorkspace.id)
        .where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.removed_at.is_(None),
            FamilyWorkspace.deleted_at.is_(None),
        )
        .order_by(FamilyWorkspace.created_at.desc())
    )
    return list(result.scalars().all())


async def get_workspace_for_user(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> FamilyWorkspace:
    """Fetch workspace, ensuring user is a member."""
    result = await db.execute(
        select(FamilyWorkspace).where(
            FamilyWorkspace.id == workspace_id,
            FamilyWorkspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail={"error_code": "WORKSPACE_NOT_FOUND"})

    # Check membership
    member_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.removed_at.is_(None),
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail={"error_code": "INSUFFICIENT_PERMISSIONS"})

    return workspace


async def invite_member(
    workspace_id: uuid.UUID,
    invited_email: str,
    invited_role: str,
    inviting_user: User,
    db: AsyncSession,
) -> tuple[WorkspaceInvitation, str]:
    """Create an invitation. Returns (invitation, raw_token)."""
    workspace = await get_workspace_for_user(workspace_id, inviting_user.id, db)

    # Only owner can invite
    if workspace.owner_id != inviting_user.id:
        raise HTTPException(status_code=403, detail={"error_code": "ONLY_OWNER_CAN_INVITE"})

    raw_token = generate_secure_token()
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        invited_by=inviting_user.id,
        invited_email=invited_email,
        invited_role=invited_role,
        token_hash=hash_token(raw_token),
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=INVITATION_EXPIRE_DAYS),
        created_at=datetime.now(UTC),
    )
    db.add(invitation)
    logger.info("invitation_created", workspace_id=str(workspace_id), email=invited_email)
    return invitation, raw_token


async def accept_invitation(
    raw_token: str,
    accepting_user: User,
    db: AsyncSession,
) -> FamilyWorkspace:
    """Accept a workspace invitation."""
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(WorkspaceInvitation).where(
            WorkspaceInvitation.token_hash == token_hash,
            WorkspaceInvitation.status == "pending",
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_INVITATION"})

    if invitation.expires_at < datetime.now(UTC):
        invitation.status = "expired"
        raise HTTPException(status_code=400, detail={"error_code": "INVITATION_EXPIRED"})

    # Check not already a member
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == invitation.workspace_id,
            WorkspaceMember.user_id == accepting_user.id,
            WorkspaceMember.removed_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"error_code": "ALREADY_A_MEMBER"})

    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(UTC)

    member = WorkspaceMember(
        workspace_id=invitation.workspace_id,
        user_id=accepting_user.id,
        role=invitation.invited_role,
        consent_given=False,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    db.add(member)

    ws_result = await db.execute(
        select(FamilyWorkspace).where(FamilyWorkspace.id == invitation.workspace_id)
    )
    workspace = ws_result.scalar_one()
    logger.info("invitation_accepted", workspace_id=str(workspace.id), user_id=str(accepting_user.id))
    return workspace


async def give_consent(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> datetime:
    """Record consent for a workspace member."""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.removed_at.is_(None),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail={"error_code": "MEMBER_NOT_FOUND"})

    now = datetime.now(UTC)
    member.consent_given = True
    member.consent_given_at = now
    return now


async def remove_member(
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    requesting_user: User,
    db: AsyncSession,
) -> None:
    """Remove a member from the workspace. Only the owner can remove members."""
    workspace = await get_workspace_for_user(workspace_id, requesting_user.id, db)
    if workspace.owner_id != requesting_user.id:
        raise HTTPException(status_code=403, detail={"error_code": "ONLY_OWNER_CAN_REMOVE"})

    if target_user_id == requesting_user.id:
        raise HTTPException(status_code=400, detail={"error_code": "CANNOT_REMOVE_OWNER"})

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target_user_id,
            WorkspaceMember.removed_at.is_(None),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail={"error_code": "MEMBER_NOT_FOUND"})

    member.removed_at = datetime.now(UTC)
    logger.info("member_removed", workspace_id=str(workspace_id), user_id=str(target_user_id))


async def update_profile(
    user_id: uuid.UUID,
    workspace_id: uuid.UUID | None,
    data: StudentProfileRequest | ParentProfileRequest,
    settings: Any,
    db: AsyncSession,
) -> UserProfile:
    """Create or update a user profile."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    from datetime import datetime as dt
    now = dt.now(UTC)

    if not profile:
        profile = UserProfile(
            user_id=user_id,
            workspace_id=workspace_id,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)

    if isinstance(data, StudentProfileRequest):
        profile.profile_type = "student"
        profile.exam_type = data.exam_type
        profile.category = data.category
        profile.gender = data.gender
        profile.home_district = data.home_district
        profile.home_state = data.home_state
        if data.rank is not None:
            profile.rank_encrypted = encrypt_field(str(data.rank), settings)
    else:
        profile.profile_type = "parent"
        profile.budget_min = data.budget_min
        profile.budget_max = data.budget_max
        profile.location_pref = data.location_pref
        profile.career_priorities = data.career_priorities

    profile.updated_at = now
    await db.flush()  # ensure id and timestamps are populated before returning
    return profile


