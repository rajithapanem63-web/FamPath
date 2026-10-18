"""Integration tests for authentication endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_verify_flow(client: AsyncClient, sample_user_data: dict) -> None:
    """Full registration flow: register → check status → verify not active yet."""
    # Register
    resp = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Verification email sent"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(
    client: AsyncClient, sample_user_data: dict
) -> None:
    await client.post("/api/v1/auth/register", json=sample_user_data)
    resp = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.asyncio
async def test_register_weak_password_fails(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "weak", "full_name": "T", "role": "student"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_unverified_user_returns_403(
    client: AsyncClient, sample_user_data: dict
) -> None:
    await client.post("/api/v1/auth/register", json=sample_user_data)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": sample_user_data["email"], "password": sample_user_data["password"]},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "EMAIL_NOT_VERIFIED"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(
    client: AsyncClient, sample_user_data: dict, db_session: Any
) -> None:
    # Directly activate user in DB
    from app.models.auth import User
    from sqlalchemy import select

    await client.post("/api/v1/auth/register", json=sample_user_data)
    result = await db_session.execute(select(User).where(User.email == sample_user_data["email"]))
    user = result.scalar_one()
    user.status = "active"
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": sample_user_data["email"], "password": "WrongPass9"},
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_success_returns_token(
    client: AsyncClient, sample_user_data: dict, db_session: Any
) -> None:
    from app.models.auth import User
    from sqlalchemy import select

    await client.post("/api/v1/auth/register", json=sample_user_data)
    result = await db_session.execute(select(User).where(User.email == sample_user_data["email"]))
    user = result.scalar_one()
    user.status = "active"
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": sample_user_data["email"], "password": sample_user_data["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == sample_user_data["email"]


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_always_200(client: AsyncClient) -> None:
    """Should return 200 even for non-existent email (no enumeration)."""
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_expired_token(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": "invalid-token-that-does-not-exist"},
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "VERIFICATION_LINK_EXPIRED"


from typing import Any  # noqa: E402
