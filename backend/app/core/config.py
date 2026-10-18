"""
Application configuration via Pydantic Settings.
All values come from environment variables or a .env file at the repo root.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FAMPATH_",
        # Look for .env in backend/ first, then repo root
        env_file=["../.env", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "testing", "staging", "production"] = "development"
    APP_NAME: str = "FamPath"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b"

    # ── Database ─────────────────────────────────────────────────────────────
    # Supports both SQLite (local) and PostgreSQL (production)
    # Also accepts DATABASE_URL (Render's default env var name)
    DB_URL: str = "sqlite+aiosqlite:///./fampath_dev.db"
    DATABASE_URL: str = ""  # Render sets this automatically

    @model_validator(mode="after")
    def resolve_db_url(self) -> "Settings":
        """Use DATABASE_URL if DB_URL not explicitly set to postgres."""
        if "sqlite" in self.DB_URL and self.DATABASE_URL:
            # Convert postgres:// to postgresql+asyncpg://
            db_url = self.DATABASE_URL
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.DB_URL = db_url
        return self

    # ── Redis (optional — gracefully degraded in dev) ─────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@fampath.dev"
    SMTP_FROM_NAME: str = "FamPath"

    # ── LLM ───────────────────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["anthropic", "openai", "mock"] = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_MAX_TOKENS: int = 1500
    LLM_TIMEOUT_SECONDS: int = 30
    EMBEDDING_PROVIDER: Literal["openai", "mock"] = "mock"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: str = ""

    # ── MLflow ────────────────────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "http://localhost:5001"
    MLFLOW_EXPERIMENT_NAME: str = "fampath-predictor"
    ML_MODEL_VERSION: str = "latest"

    # ── Observability ─────────────────────────────────────────────────────────
    SENTRY_DSN: str = ""
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Rate limits ───────────────────────────────────────────────────────────
    AUTH_RATE_LIMIT_ATTEMPTS: int = 10
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 900
    CHAT_RATE_LIMIT_MESSAGES_PER_MINUTE: int = 20

    # ── Prediction bands ──────────────────────────────────────────────────────
    SAFE_MARGIN_PERCENT: float = 20.0
    TARGET_MARGIN_PERCENT: float = 10.0

    # ── Feature flags ─────────────────────────────────────────────────────────
    FEATURE_OTP_LOGIN: bool = False
    FEATURE_ROUND_SIMULATOR: bool = False
    FEATURE_PLAN_B_GENERATOR: bool = False
    FEATURE_MENTOR_MATCHING: bool = False
    FEATURE_COUNSELLOR_BOOKING: bool = False
    FEATURE_WHATSAPP_MODE: bool = False
    FEATURE_CLAIM_VERIFIER: bool = False

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        if v and len(v) != 64:
            raise ValueError("ENCRYPTION_KEY must be a 64-character hex string (32 bytes)")
        return v

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DB_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()
