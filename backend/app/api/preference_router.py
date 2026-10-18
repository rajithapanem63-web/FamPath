"""
Preference API router.
Endpoints for submitting, retrieving, and updating preference questionnaire responses.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.schemas.preference_schema import (
    PreferenceResponseOutput,
    PreferenceSubmissionRequest,
    PreferenceSubmissionResult,
    UserPreferencesResponse,
    FamilyPreferencesSummary,
)
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.post(
    "",
    response_model=PreferenceSubmissionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit or update preference responses",
)
async def submit_preferences(
    data: PreferenceSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> PreferenceSubmissionResult:
    """
    Submit or update preference questionnaire responses.
    
    - If dimension already exists, creates a new version and marks old as inactive
    - Calculates completion percentage
    - Requires workspace membership
    """
    service = PreferenceService()
    try:
        result = await service.submit_preferences(
            db=db,
            workspace_id=data.workspace_id,
            user_id=token.user_id,
            responses=data.responses,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit preferences: {str(e)}"
        )


@router.get(
    "/me",
    response_model=UserPreferencesResponse,
    summary="Get own preferences",
)
async def get_my_preferences(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> UserPreferencesResponse:
    """
    Get authenticated user's preference responses.
    
    Returns only active (latest version) responses.
    """
    service = PreferenceService()
    try:
        result = await service.get_user_preferences(
            db=db,
            workspace_id=workspace_id,
            user_id=token.user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.get(
    "/family",
    response_model=FamilyPreferencesSummary,
    summary="Get family preference completion summary",
)
async def get_family_preferences_summary(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> FamilyPreferencesSummary:
    """
    Get completion status for all family members.
    
    Returns only completion percentages, not actual preference details.
    """
    service = PreferenceService()
    try:
        result = await service.get_family_preferences_summary(
            db=db,
            workspace_id=workspace_id,
            requesting_user_id=token.user_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get family summary: {str(e)}"
        )


@router.put(
    "/{dimension}",
    response_model=PreferenceResponseOutput,
    summary="Update a single preference dimension",
)
async def update_preference_dimension(
    dimension: str,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    weight: str = Query(..., description="Weight: LOW, MEDIUM, or HIGH"),
    selected_options: list[str] = Query(..., description="Selected options"),
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> PreferenceResponseOutput:
    """
    Update a single preference dimension.
    
    Creates a new version and marks the old one as inactive.
    """
    service = PreferenceService()
    try:
        result = await service.update_dimension(
            db=db,
            workspace_id=workspace_id,
            user_id=token.user_id,
            dimension=dimension,
            weight=weight.upper(),
            selected_options=selected_options,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "No active preference" in str(e) else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update dimension: {str(e)}"
        )


