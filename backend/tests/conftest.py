"""
Pytest configuration and shared fixtures.
Uses an in-memory SQLite database for unit tests (via aiosqlite)
and a test PostgreSQL database for integration tests.
"""
from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Use SQLite for unit tests if no TEST_DB_URL is set
TEST_DB_URL = os.getenv("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")

# Override settings before importing app
os.environ.setdefault("FAMPATH_DB_URL", "postgresql+asyncpg://test:test@localhost:5432/fampath_test")
os.environ.setdefault("FAMPATH_SECRET_KEY", "test-secret-key-for-unit-tests-only-not-production")
os.environ.setdefault("FAMPATH_ENCRYPTION_KEY", "a" * 64)  # 32 bytes hex
os.environ.setdefault("FAMPATH_REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("FAMPATH_APP_ENV", "testing")
os.environ.setdefault("FAMPATH_LLM_PROVIDER", "mock")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite session for unit tests."""
    from app.core.database import Base

    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with DB session override."""
    from app.core.database import get_db
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "TestPass1",
        "full_name": "Test User",
        "role": "student",
        "preferred_locale": "en",
    }


@pytest.fixture
def admin_user_data() -> dict:
    return {
        "email": f"admin_{uuid.uuid4().hex[:8]}@example.com",
        "password": "AdminPass1",
        "full_name": "Admin User",
        "role": "admin",
    }
