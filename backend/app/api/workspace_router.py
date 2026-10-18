"""Workspace and profile API router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_token_payload, require_role
from app.models.auth import User
from app.schemas.workspace_schema import (
    AcceptInvitationRequest,
    ConsentRequest,
    ConsentResponse,
    CreateWorkspaceRequest,
    InviteMemberRequest,
    InvitationResponse,
    ParentProfileRequest,
    ProfileResponse,
    StudentProfileRequest,
    WorkspaceDetailResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)
from app.services import workspace_service
from app.services.audit_service import log_audit_event
from app.workers.email_tasks import send_workspace_invitation_email

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


async def _get_user(token=Depends(get_token_payload), db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail={"error_code": "USER_NOT_FOUND"})
    return user


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a family workspace",
)
async def create_workspace(
    data: CreateWorkspaceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> WorkspaceResponse:
    # Only students can create workspaces
    if current_user.role not in ("student", "admin"):
        raise HTTPException(status_code=403, detail={"error_code": "INSUFFICIENT_PERMISSIONS"})
    workspace = await workspace_service.create_workspace(data.name, current_user, db)
    await log_audit_event(db, current_user.id, "workspace_created", "workspace", workspace.id)
    return WorkspaceResponse.model_validate(workspace)


@router.get("", response_model=list[WorkspaceResponse], summary="List user's workspaces")
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> list[WorkspaceResponse]:
    workspaces = await workspace_service.get_user_workspaces(current_user.id, db)
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> WorkspaceDetailResponse:
    workspace = await workspace_service.get_workspace_for_user(workspace_id, current_user.id, db)
    # Build member response list
    members = []
    for m in workspace.members:
        if m.removed_at is None:
            u_result = await db.execute(select(User).where(User.id == m.user_id))
            u = u_result.scalar_one_or_none()
            if u:
                members.append(WorkspaceMemberResponse(
                    user_id=m.user_id,
                    full_name=u.full_name,
                    email=u.email,
                    role=m.role,
                    consent_given=m.consent_given,
                    joined_at=m.joined_at,
                ))

    return WorkspaceDetailResponse(
        id=workspace.id,
        name=workspace.name,
        owner_id=workspace.owner_id,
        status=workspace.status,
        created_at=workspace.created_at,
        members=members,
    )


@router.post("/{workspace_id}/invitations", response_model=InvitationResponse, status_code=201)
async def invite_member(
    workspace_id: uuid.UUID,
    data: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> InvitationResponse:
    invitation, raw_token = await workspace_service.invite_member(
        workspace_id, data.email, data.role, current_user, db
    )
    send_workspace_invitation_email.delay(
        to_email=data.email,
        invited_by_name=current_user.full_name or current_user.email,
        workspace_name="your family workspace",
        token=raw_token,
    )
    return InvitationResponse(invitation_id=invitation.id, expires_at=invitation.expires_at)


@router.post("/accept-invitation", response_model=WorkspaceResponse)
async def accept_invitation(
    data: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> WorkspaceResponse:
    workspace = await workspace_service.accept_invitation(data.token, current_user, db)
    return WorkspaceResponse.model_validate(workspace)


@router.post("/{workspace_id}/consent", response_model=ConsentResponse)
async def give_consent(
    workspace_id: uuid.UUID,
    data: ConsentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> ConsentResponse:
    if not data.consented:
        raise HTTPException(status_code=400, detail={"error_code": "CONSENT_REQUIRED"})
    ts = await workspace_service.give_consent(workspace_id, current_user.id, db)
    return ConsentResponse(consent_given_at=ts)


@router.delete("/{workspace_id}/members/{user_id}", response_model=dict)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> dict:
    await workspace_service.remove_member(workspace_id, user_id, current_user, db)
    return {"message": "Member removed"}


# ── Profile endpoints ──────────────────────────────────────────────────────────

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


@profile_router.put("", response_model=ProfileResponse)
async def update_profile(
    data: StudentProfileRequest | ParentProfileRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(_get_user),
) -> ProfileResponse:
    profile = await workspace_service.update_profile(
        current_user.id, None, data, settings, db
    )
    return ProfileResponse.model_validate(profile)


@profile_router.get("", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_user),
) -> ProfileResponse:
    from app.models.workspace import UserProfile
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail={"error_code": "PROFILE_NOT_FOUND"})
    return ProfileResponse.model_validate(profile)
