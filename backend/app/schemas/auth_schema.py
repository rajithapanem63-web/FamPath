"""Pydantic v2 schemas for authentication endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="student", pattern="^(student|parent|counsellor)$")
    preferred_locale: str = Field(default="en", pattern="^(en|te|hi)$")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Body is unused — refresh token comes from httpOnly cookie."""


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: str
    status: str
    preferred_locale: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict = {}
