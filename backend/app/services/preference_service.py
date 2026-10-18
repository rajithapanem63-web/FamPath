"""
Preference service - business logic for preference questionnaires.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import PreferenceResponse, PreferenceWeight
from app.models.workspace import FamilyWorkspace, WorkspaceMember
from app.models.auth import User
from app.schemas.preference_schema import (
    MemberPreferenceStatus,
    PreferenceResponseInput,
    PreferenceResponseOutput,
    PreferenceSubmissionResult,
    UserPreferencesResponse,
    FamilyPreferencesSummary,
)

logger = structlog.get_logger(__name__)

TOTAL_DIMENSIONS = 8


class PreferenceService:
    """Service layer for preference operations."""
    
    async def submit_preferences(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        responses: list[PreferenceResponseInput],
    ) -> PreferenceSubmissionResult:
        """
        Submit or update preferences for a user in a workspace.
        
        For each dimension:
        - If already exists: mark old as inactive, create new version
        - If new: create with version=1
        """
        # Validate workspace membership
        await self._validate_membership(db, workspace_id, user_id)
        
        submission_time = datetime.now(timezone.utc)
        submission_id = None
        
        for resp in responses:
            # Check if dimension already exists
            stmt = select(PreferenceResponse).where(
                and_(
                    PreferenceResponse.workspace_id == workspace_id,
                    PreferenceResponse.user_id == user_id,
                    PreferenceResponse.dimension == resp.dimension,
                    PreferenceResponse.is_active == True,
                )
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Mark old as inactive
                existing.is_active = False
                version = existing.version + 1
            else:
                version = 1
            
            # Create new record
            weight_map = {"LOW": 3, "MEDIUM": 6, "HIGH": 9}
            new_response = PreferenceResponse(
                workspace_id=workspace_id,
                user_id=user_id,
                dimension=resp.dimension,
                weight=weight_map[resp.weight],
                selected_options={"options": resp.selected_options},
                additional_data=resp.additional_data,
                submitted_at=submission_time,
                updated_at=submission_time,
                version=version,
                is_active=True,
            )
            db.add(new_response)
            
            if submission_id is None:
                submission_id = new_response.id
        
        await db.commit()
        
        # Calculate completion
        completion_pct = (len(responses) / TOTAL_DIMENSIONS) * 100
        
        return PreferenceSubmissionResult(
            submission_id=submission_id or user_id,  # Fallback if no responses
            workspace_id=workspace_id,
            user_id=user_id,
            submitted_at=submission_time,
            dimensions_submitted=len(responses),
            completion_percentage=round(completion_pct, 1),
        )
    
    async def get_user_preferences(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
    ) -> UserPreferencesResponse:
        """Get active preferences for a user."""
        await self._validate_membership(db, workspace_id, user_id)
        
        # Get user info
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one()
        
        # Get workspace member to find role
        member_stmt = select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        member_result = await db.execute(member_stmt)
        member = member_result.scalar_one()
        
        # Get active preferences
        stmt = select(PreferenceResponse).where(
            and_(
                PreferenceResponse.workspace_id == workspace_id,
                PreferenceResponse.user_id == user_id,
                PreferenceResponse.is_active == True,
            )
        )
        result = await db.execute(stmt)
        preferences = result.scalars().all()
        
        # Convert to output
        responses = []
        last_updated = None
        for pref in preferences:
            weight_label = (
                "LOW" if pref.weight == 3 else
                "MEDIUM" if pref.weight == 6 else
                "HIGH"
            )
            responses.append(PreferenceResponseOutput(
                dimension=pref.dimension,
                dimension_label=pref.dimension.replace("_", " ").title(),
                weight=weight_label,
                weight_numeric=pref.weight,
                selected_options=pref.selected_options.get("options", []),
                submitted_at=pref.submitted_at,
                updated_at=pref.updated_at,
            ))
            if last_updated is None or pref.updated_at > last_updated:
                last_updated = pref.updated_at
        
        return UserPreferencesResponse(
            user_id=user_id,
            workspace_id=workspace_id,
            full_name=user.full_name or user.email,
            role=member.role,
            responses=responses,
            completion_percentage=round((len(responses) / TOTAL_DIMENSIONS) * 100, 1),
            completed_dimensions=len(responses),
            total_dimensions=TOTAL_DIMENSIONS,
            last_updated=last_updated,
        )
    
    async def get_family_preferences_summary(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        requesting_user_id: UUID,
    ) -> FamilyPreferencesSummary:
        """Get completion status for all family members (no details)."""
        await self._validate_membership(db, workspace_id, requesting_user_id)
        
        # Get workspace name
        ws_stmt = select(FamilyWorkspace).where(FamilyWorkspace.id == workspace_id)
        ws_result = await db.execute(ws_stmt)
        workspace = ws_result.scalar_one()
        
        # Get all members
        members_stmt = select(WorkspaceMember, User).join(
            User, WorkspaceMember.user_id == User.id
        ).where(WorkspaceMember.workspace_id == workspace_id)
        members_result = await db.execute(members_stmt)
        members_data = members_result.all()
        
        member_statuses = []
        total_completion = 0
        
        for member, user in members_data:
            # Count active preferences for this user
            count_stmt = select(PreferenceResponse).where(
                and_(
                    PreferenceResponse.workspace_id == workspace_id,
                    PreferenceResponse.user_id == user.id,
                    PreferenceResponse.is_active == True,
                )
            )
            count_result = await db.execute(count_stmt)
            prefs = count_result.scalars().all()
            
            completed = len(prefs)
            completion_pct = (completed / TOTAL_DIMENSIONS) * 100
            total_completion += completion_pct
            
            last_updated = max((p.updated_at for p in prefs), default=None)
            
            member_statuses.append(MemberPreferenceStatus(
                user_id=user.id,
                full_name=user.full_name or user.email,
                role=member.role,
                completion_percentage=round(completion_pct, 1),
                completed_dimensions=completed,
                last_updated=last_updated,
                has_completed=(completed == TOTAL_DIMENSIONS),
            ))
        
        family_rate = total_completion / len(member_statuses) if member_statuses else 0
        
        return FamilyPreferencesSummary(
            workspace_id=workspace_id,
            workspace_name=workspace.name,
            members=member_statuses,
            family_completion_rate=round(family_rate, 1),
        )
    
    async def update_dimension(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        dimension: str,
        weight: str,
        selected_options: list[str],
        additional_data: dict[str, Any] | None = None,
    ) -> PreferenceResponseOutput:
        """Update a single dimension."""
        await self._validate_membership(db, workspace_id, user_id)
        
        # Mark current active as inactive
        stmt = select(PreferenceResponse).where(
            and_(
                PreferenceResponse.workspace_id == workspace_id,
                PreferenceResponse.user_id == user_id,
                PreferenceResponse.dimension == dimension,
                PreferenceResponse.is_active == True,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            raise ValueError(f"No active preference found for dimension: {dimension}")
        
        existing.is_active = False
        version = existing.version + 1
        
        # Create new version
        weight_map = {"LOW": 3, "MEDIUM": 6, "HIGH": 9}
        now = datetime.now(timezone.utc)
        
        new_pref = PreferenceResponse(
            workspace_id=workspace_id,
            user_id=user_id,
            dimension=dimension,
            weight=weight_map[weight],
            selected_options={"options": selected_options},
            additional_data=additional_data,
            submitted_at=now,
            updated_at=now,
            version=version,
            is_active=True,
        )
        db.add(new_pref)
        await db.commit()
        await db.refresh(new_pref)
        
        weight_label = (
            "LOW" if new_pref.weight == 3 else
            "MEDIUM" if new_pref.weight == 6 else
            "HIGH"
        )
        
        return PreferenceResponseOutput(
            dimension=new_pref.dimension,
            dimension_label=new_pref.dimension.replace("_", " ").title(),
            weight=weight_label,
            weight_numeric=new_pref.weight,
            selected_options=new_pref.selected_options.get("options", []),
            submitted_at=new_pref.submitted_at,
            updated_at=new_pref.updated_at,
        )
    
    async def _validate_membership(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
    ) -> None:
        """Validate that user is a member of the workspace."""
        stmt = select(WorkspaceMember).where(
            and_(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise ValueError(f"User {user_id} is not a member of workspace {workspace_id}")


