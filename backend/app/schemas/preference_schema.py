"""Pydantic schemas for preference questionnaires."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.preference import PreferenceDimension, PreferenceWeight


class PreferenceResponseInput(BaseModel):
    """Input for a single preference dimension."""
    dimension: str = Field(..., description="Preference dimension")
    weight: str = Field(..., description="Weight: LOW, MEDIUM, or HIGH")
    selected_options: list[str] = Field(..., min_length=1, description="At least one option required")
    additional_data: dict[str, Any] | None = None
    
    @field_validator("dimension")
    @classmethod
    def validate_dimension(cls, v: str) -> str:
        valid = [d.value for d in PreferenceDimension]
        if v not in valid:
            raise ValueError(f"Invalid dimension. Must be one of: {valid}")
        return v
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: str) -> str:
        if v.upper() not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError("Weight must be LOW, MEDIUM, or HIGH")
        return v.upper()


class PreferenceSubmissionRequest(BaseModel):
    """Request to submit/update preferences."""
    workspace_id: UUID
    responses: list[PreferenceResponseInput] = Field(..., max_length=8)


class PreferenceResponseOutput(BaseModel):
    """Output for a single preference response."""
    dimension: str
    dimension_label: str
    weight: str
    weight_numeric: int
    selected_options: list[str]
    submitted_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PreferenceSubmissionResult(BaseModel):
    """Result of preference submission."""
    submission_id: UUID
    workspace_id: UUID
    user_id: UUID
    submitted_at: datetime
    dimensions_submitted: int
    completion_percentage: float


class UserPreferencesResponse(BaseModel):
    """User's all preferences."""
    user_id: UUID
    workspace_id: UUID
    full_name: str
    role: str
    responses: list[PreferenceResponseOutput]
    completion_percentage: float
    completed_dimensions: int
    total_dimensions: int = 8
    last_updated: datetime | None


class MemberPreferenceStatus(BaseModel):
    """Preference completion status for a member."""
    user_id: UUID
    full_name: str
    role: str
    completion_percentage: float
    completed_dimensions: int
    last_updated: datetime | None
    has_completed: bool


class FamilyPreferencesSummary(BaseModel):
    """Family-wide preference completion summary."""
    workspace_id: UUID
    workspace_name: str
    members: list[MemberPreferenceStatus]
    family_completion_rate: float
