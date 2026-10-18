"""Unit tests for security utilities: hashing, JWT, encryption."""
from __future__ import annotations

import os
import time

import pytest
from jose import jwt

os.environ.setdefault("FAMPATH_DB_URL", "postgresql+asyncpg://test:test@localhost:5432/fampath_test")
os.environ.setdefault("FAMPATH_SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("FAMPATH_ENCRYPTION_KEY", "a" * 64)
os.environ.setdefault("FAMPATH_REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("FAMPATH_APP_ENV", "testing")
os.environ.setdefault("FAMPATH_LLM_PROVIDER", "mock")


from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_field,
    encrypt_field,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.config import get_settings


def test_hash_password_and_verify() -> None:
    plain = "MySecretPass1"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("WrongPass1", hashed)


def test_hash_password_different_each_time() -> None:
    plain = "MySecretPass1"
    h1 = hash_password(plain)
    h2 = hash_password(plain)
    assert h1 != h2  # argon2 includes random salt


def test_hash_token_deterministic() -> None:
    raw = "my-raw-token-value"
    assert hash_token(raw) == hash_token(raw)
    assert len(hash_token(raw)) == 64  # SHA-256 hex


def test_create_and_decode_access_token() -> None:
    settings = get_settings()
    user_id = "00000000-0000-0000-0000-000000000001"
    token = create_access_token(user_id, "student", settings)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["role"] == "student"
    assert payload["type"] == "access"


def test_create_refresh_token_has_family_id() -> None:
    settings = get_settings()
    family_id = "test-family-id"
    token = create_refresh_token("user-123", family_id, settings)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["fid"] == family_id
    assert payload["type"] == "refresh"


def test_encrypt_and_decrypt_field() -> None:
    settings = get_settings()
    plaintext = "12345"
    encrypted = encrypt_field(plaintext, settings)
    assert encrypted != plaintext
    decrypted = decrypt_field(encrypted, settings)
    assert decrypted == plaintext


def test_encrypt_different_ciphertext_each_time() -> None:
    settings = get_settings()
    plaintext = "12345"
    e1 = encrypt_field(plaintext, settings)
    e2 = encrypt_field(plaintext, settings)
    assert e1 != e2  # different nonce each time
    assert decrypt_field(e1, settings) == plaintext
    assert decrypt_field(e2, settings) == plaintext
