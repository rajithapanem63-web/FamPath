"""
Authentication service: registration, email verification, login, token refresh,
password reset, and account lockout logic.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.redis_client import check_rate_limit, get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.auth import EmailToken, RefreshToken, User
from app.schemas.auth_schema import RegisterRequest

logger = structlog.get_logger(__name__)

MAX_FAILED_LOGINS = 10
LOCKOUT_DURATION_MINUTES = 60


async def register_user(
    data: RegisterRequest,
    db: AsyncSession,
    settings: Settings,
) -> User:
    """Create a new user and return them. Does NOT send the verification email (Celery handles that)."""
    # Check for existing email
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "EMAIL_ALREADY_REGISTERED", "message": "Email already registered"},
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        full_name=data.full_name,
        preferred_locale=data.preferred_locale,
        status="pending_verification",
    )
    db.add(user)
    await db.flush()  # get user.id before commit

    # Create email verification token
    raw_token = generate_secure_token()
    token = EmailToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        purpose="email_verification",
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_at=datetime.now(UTC),
    )
    db.add(token)
    await db.flush()

    # Attach raw token to user object for the caller to send in email
    user._verification_token = raw_token  # type: ignore[attr-defined]
    logger.info("user_registered", user_id=str(user.id), role=user.role)
    return user


async def verify_email(token_str: str, db: AsyncSession) -> User:
    """Mark user as active after verifying the email token."""
    token_hash = hash_token(token_str)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.purpose == "email_verification",
        )
    )
    token = result.scalar_one_or_none()

    if not token or not token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "VERIFICATION_LINK_EXPIRED", "message": "Token invalid or expired"},
        )

    # Mark token used
    token.used_at = datetime.now(UTC)

    # Activate user
    user_result = await db.execute(select(User).where(User.id == token.user_id))
    user = user_result.scalar_one()
    user.status = "active"
    logger.info("email_verified", user_id=str(user.id))
    return user


async def login(
    email: str,
    password: str,
    db: AsyncSession,
    settings: Settings,
    request: Request,
) -> tuple[str, str, User]:
    """
    Authenticate user. Returns (access_token, refresh_token, user).
    Enforces rate limiting and account lockout.
    """
    redis = get_redis()
    rate_key = f"auth:rate:{request.client.host if request.client else 'unknown'}"
    allowed, _ = await check_rate_limit(
        redis, rate_key,
        settings.AUTH_RATE_LIMIT_ATTEMPTS,
        settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error_code": "RATE_LIMIT_EXCEEDED", "message": "Too many attempts"},
        )

    # Fetch user
    result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        # Increment failed count if user exists
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_LOGINS:
                user.status = "locked"
                user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                logger.warning("account_locked", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    if user.status == "locked":
        if user.locked_until and user.locked_until > datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error_code": "ACCOUNT_LOCKED",
                    "message": "Account locked",
                    "unlock_at": user.locked_until.isoformat(),
                },
            )
        else:
            # Lockout expired — unlock
            user.status = "active"
            user.failed_login_count = 0

    if user.status == "pending_verification":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "EMAIL_NOT_VERIFIED", "message": "Please verify your email"},
        )

    # Reset failed count on successful login
    user.failed_login_count = 0
    user.last_login_at = datetime.now(UTC)

    # Issue tokens
    family_id = str(uuid.uuid4())
    raw_refresh = generate_secure_token()
    access_token = create_access_token(user.id, user.role, settings)
    refresh_token_str = create_refresh_token(user.id, family_id, settings)

    rt = RefreshToken(
        user_id=user.id,
        family_id=uuid.UUID(family_id),
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        created_at=datetime.now(UTC),
    )
    db.add(rt)
    logger.info("user_logged_in", user_id=str(user.id))
    return access_token, raw_refresh, user


async def refresh_access_token(
    raw_refresh_token: str,
    db: AsyncSession,
    settings: Settings,
) -> tuple[str, str]:
    """
    Rotate refresh token. Returns (new_access_token, new_raw_refresh_token).
    Invalidates entire family on reuse detection.
    """
    token_hash = hash_token(raw_refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalar_one_or_none()

    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_REFRESH_TOKEN"},
        )

    if not rt.is_valid:
        # Token reuse detected — revoke entire family
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == rt.family_id)
            .values(revoked_at=datetime.now(UTC))
        )
        logger.warning("refresh_token_reuse_detected", family_id=str(rt.family_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_REFRESH_TOKEN"},
        )

    # Revoke old token
    rt.revoked_at = datetime.now(UTC)

    # Get user
    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one()

    # Issue new tokens
    new_raw_refresh = generate_secure_token()
    new_access = create_access_token(user.id, user.role, settings)

    new_rt = RefreshToken(
        user_id=user.id,
        family_id=rt.family_id,
        token_hash=hash_token(new_raw_refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        created_at=datetime.now(UTC),
    )
    db.add(new_rt)
    return new_access, new_raw_refresh


async def logout(raw_refresh_token: str, db: AsyncSession) -> None:
    """Revoke the refresh token."""
    token_hash = hash_token(raw_refresh_token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked_at=datetime.now(UTC))
    )


async def request_password_reset(email: str, db: AsyncSession) -> str | None:
    """Generate a password reset token. Returns raw token or None if user not found."""
    result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user:
        return None  # Don't reveal whether email exists

    raw_token = generate_secure_token()
    token = EmailToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        purpose="password_reset",
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_at=datetime.now(UTC),
    )
    db.add(token)
    return raw_token


async def reset_password(token_str: str, new_password: str, db: AsyncSession) -> None:
    """Reset user password using the reset token."""
    token_hash = hash_token(token_str)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.purpose == "password_reset",
        )
    )
    token = result.scalar_one_or_none()
    if not token or not token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_RESET_TOKEN", "message": "Token invalid or expired"},
        )

    token.used_at = datetime.now(UTC)

    user_result = await db.execute(select(User).where(User.id == token.user_id))
    user = user_result.scalar_one()
    user.password_hash = hash_password(new_password)
    logger.info("password_reset", user_id=str(user.id))


async def reset_password(token_str: str, new_password: str, db: AsyncSession) -> None:
    """Validate reset token and update password."""
    token_hash = hash_token(token_str)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.purpose == "password_reset",
        )
    )
    token = result.scalar_one_or_none()
    if not token or not token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "RESET_TOKEN_INVALID", "message": "Token invalid or expired"},
        )
    token.used_at = datetime.now(UTC)
    user_result = await db.execute(select(User).where(User.id == token.user_id))
    user = user_result.scalar_one()
    user.password_hash = hash_password(new_password)
    user.failed_login_count = 0
    if user.status == "locked":
        user.status = "active"
    logger.info("password_reset", user_id=str(user.id))
