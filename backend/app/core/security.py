"""
Security utilities: password hashing, JWT creation/verification,
field-level encryption, and RBAC dependency factories.
"""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import struct
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

# ── Password hashing (argon2id) ───────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain-text password with argon2id."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against an argon2id hash."""
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(
    subject: str | UUID,
    role: str,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str | UUID,
    family_id: str,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a long-lived JWT refresh token with a family ID for rotation tracking."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "fid": family_id,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_token(raw_token: str) -> str:
    """SHA-256 hash of a raw token for safe storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ── Field-level encryption (AES-256-GCM) ─────────────────────────────────────

def _get_key(settings: Settings) -> bytes:
    return bytes.fromhex(settings.ENCRYPTION_KEY)


def encrypt_field(plaintext: str, settings: Settings) -> str:
    """
    Encrypt a string field with AES-256-GCM.
    Returns: base64(nonce[12] + ciphertext + tag[16])
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore[import-untyped]

    key = _get_key(settings)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_field(ciphertext_b64: str, settings: Settings) -> str:
    """Decrypt a field encrypted with encrypt_field."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore[import-untyped]

    key = _get_key(settings)
    data = base64.b64decode(ciphertext_b64)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()


# ── FastAPI security dependencies ─────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload:
    """Parsed JWT payload."""

    def __init__(self, user_id: UUID, role: str) -> None:
        self.user_id = user_id
        self.role = role


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> TokenPayload:
    """Extract and validate Bearer token; return parsed payload."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error_code": "INVALID_OR_MISSING_TOKEN"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise exc
    try:
        payload = decode_token(credentials.credentials, settings)
        if payload.get("type") != "access":
            raise exc
        return TokenPayload(user_id=UUID(payload["sub"]), role=payload["role"])
    except (JWTError, KeyError, ValueError):
        raise exc


def require_role(*allowed_roles: str):  # type: ignore[return]
    """Dependency factory: raises 403 if the token role is not in allowed_roles."""

    def _check(token: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
        if token.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error_code": "INSUFFICIENT_PERMISSIONS"},
            )
        return token

    return Depends(_check)


def generate_secure_token(length: int = 32) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(length)
