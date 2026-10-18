"""
Authentication API router.
Endpoints: register, verify-email, login, refresh, logout, forgot-password, reset-password, me.
"""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_token_payload
from app.schemas.auth_schema import (
    ErrorResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services import auth_service
from app.services.audit_service import log_audit_event
from app.workers.email_tasks import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

_REFRESH_COOKIE = "refresh_token"


def _get_cookie_opts(settings: Settings) -> dict:
    """Cookie options — disable secure flag in dev so localhost HTTP works."""
    return {
        "httponly": True,
        "secure": settings.APP_ENV not in ("development", "testing"),
        "samesite": "lax" if settings.APP_ENV in ("development", "testing") else "strict",
        "path": "/api/v1/auth",
    }


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Register a new user account",
    responses={409: {"model": ErrorResponse}},
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Create an account and send email verification."""
    user = await auth_service.register_user(data, db, settings)
    raw_token: str = user._verification_token  # type: ignore[attr-defined]
    
    # Commit the user to database
    await db.commit()
    
    # AUTO-VERIFY in development mode (bypass email for demo)
    if settings.APP_ENV in ("development", "testing"):
        await auth_service.verify_email(raw_token, db)
        await db.commit()
        return MessageResponse(message="Account created and verified! You can now sign in.")
    
    # Production: send email via Celery
    try:
        send_verification_email.delay(
            to_email=user.email,
            full_name=user.full_name or user.email,
            token=raw_token,
            locale=user.preferred_locale,
        )
    except Exception:
        pass  # Email sending is best-effort
    return MessageResponse(message="Verification email sent")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    responses={400: {"model": ErrorResponse}},
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Activate account using the verification token."""
    await auth_service.verify_email(data.token, db)
    return MessageResponse(message="Email verified")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and receive tokens",
    responses={401: {"model": ErrorResponse}, 423: {"model": ErrorResponse}},
)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Return access token in body; set refresh token as httpOnly cookie."""
    access_token, raw_refresh, user = await auth_service.login(
        data.email, data.password, db, settings, request
    )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw_refresh,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **_get_cookie_opts(settings),
    )
    await log_audit_event(db, user.id, "login", ip_address=str(request.client.host if request.client else ""))
    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token",
    responses={401: {"model": ErrorResponse}},
)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Rotate refresh token and issue a new access token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_REFRESH_TOKEN"},
        )
    new_access, new_refresh = await auth_service.refresh_access_token(
        refresh_token, db, settings
    )
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=new_refresh,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **_get_cookie_opts(settings),
    )
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse, summary="Revoke session")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    if refresh_token:
        await auth_service.logout(refresh_token, db)
    response.delete_cookie(_REFRESH_COOKIE, path="/api/v1/auth")
    return MessageResponse(message="Logged out")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset email",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Always returns 200 to prevent email enumeration."""
    raw_token = await auth_service.request_password_reset(data.email, db)
    if raw_token:
        send_password_reset_email.delay(to_email=data.email, token=raw_token)
    return MessageResponse(message="Reset email sent if account exists")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using token",
    responses={400: {"model": ErrorResponse}},
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await auth_service.reset_password(data.token, data.new_password, db)
    return MessageResponse(message="Password reset")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> UserResponse:
    from sqlalchemy import select
    from app.models.auth import User

    result = await db.execute(select(User).where(User.id == token.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail={"error_code": "USER_NOT_FOUND"})
    return UserResponse.model_validate(user)
