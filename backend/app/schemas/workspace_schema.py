"""Pydantic v2 schemas for workspace and profile endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceMemberResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str | None
    email: str
    role: str
    consent_given: bool
    joined_at: datetime | None

    model_config = {"from_attributes": True}


class WorkspaceDetailResponse(WorkspaceResponse):
    members: list[WorkspaceMemberResponse] = []


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="parent", pattern="^(parent|counsellor)$")


class InvitationResponse(BaseModel):
    invitation_id: uuid.UUID
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=10)


class ConsentRequest(BaseModel):
    consented: bool


class ConsentResponse(BaseModel):
    consent_given_at: datetime


# ── Profile schemas ───────────────────────────────────────────────────────────

class StudentProfileRequest(BaseModel):
    exam_type: str | None = Field(None, pattern="^(AP_EAPCET|TS_EAPCET|JEE_MAINS|JEE_ADV)$")
    rank: int | None = Field(None, ge=1, le=500000)
    category: str | None = Field(None, pattern="^(OC|BC_A|BC_B|BC_C|BC_D|BC_E|SC|ST|EWS)$")
    gender: str | None = Field(None, pattern="^(male|female|other)$")
    home_district: str | None = Field(None, max_length=100)
    home_state: str | None = Field(None, max_length=100)


class ParentProfileRequest(BaseModel):
    budget_min: int | None = Field(None, ge=0)
    budget_max: int | None = Field(None, ge=0)
    location_pref: dict | None = None
    career_priorities: dict | None = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    profile_type: str | None
    exam_type: str | None
    category: str | None
    gender: str | None
    home_district: str | None
    home_state: str | None
    budget_min: int | None
    budget_max: int | None
    location_pref: dict | None
    career_priorities: dict | None
    updated_at: datetime

    model_config = {"from_attributes": True}
