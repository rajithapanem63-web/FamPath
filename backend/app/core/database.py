"""
Async SQLAlchemy engine, session factory, and FastAPI dependency.
Supports both SQLite (local dev) and PostgreSQL (production).
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False and no pool config
if settings.is_sqlite:
    engine = create_async_engine(
        settings.DB_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.DB_URL,
        pool_size=5,
        max_overflow=15,
        pool_timeout=30,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — provides a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """Create all tables — used on startup in dev/SQLite mode."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
