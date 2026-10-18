"""
FamPath FastAPI application entry point.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth_router import router as auth_router
from app.api.workspace_router import profile_router, router as workspace_router
from app.api.prediction_router import router as prediction_router
from app.api.aptitude_router import router as aptitude_router
from app.api.alignment_router import router as alignment_router
from app.api.cost_router import router as cost_router
from app.api.chat_router import router as chat_router
from app.api.shortlist_router import (
    checklist_router,
    router as shortlist_router,
    timeline_router,
)
from app.api.report_router import router as report_router
from app.api.admin_router import router as admin_router
from app.api.career_router import router as career_router
from app.api.preference_router import router as preference_router
from app.api.college_router import router as college_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.core.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.services.prediction_service import predictor

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(
        log_level=settings.LOG_LEVEL,
        json_output=settings.APP_ENV not in ("development", "testing"),
    )
    logger.info("fampath_starting", env=settings.APP_ENV, version=settings.APP_VERSION)

    # Auto-create tables on startup (works for both SQLite and PostgreSQL)
    from app.core.database import create_all_tables
    import app.models  # noqa: F401 - register all models
    try:
        await create_all_tables()
        logger.info("database_tables_ready")
    except Exception as e:
        logger.warning("table_creation_warning", error=str(e))

    # Sentry (optional)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
        except ImportError:
            pass

    # Load ML model (best-effort)
    predictor.load_model()
    logger.info("fampath_ready")
    yield
    logger.info("fampath_shutting_down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FamPath API",
        description="AI-Enabled Family Decision-Support Platform for Engineering Education",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # Try Prometheus metrics (optional)
    try:
        from prometheus_fastapi_instrumentator import Instrumentator  # type: ignore[import-untyped]
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    except ImportError:
        pass

    # Routers
    api_v1 = "/api/v1"
    app.include_router(auth_router, prefix=api_v1)
    app.include_router(workspace_router, prefix=api_v1)
    app.include_router(profile_router, prefix=api_v1)
    app.include_router(prediction_router, prefix=api_v1)
    app.include_router(aptitude_router, prefix=api_v1)
    app.include_router(alignment_router, prefix=api_v1)
    app.include_router(cost_router, prefix=api_v1)
    app.include_router(chat_router, prefix=api_v1)
    app.include_router(shortlist_router, prefix=api_v1)
    app.include_router(timeline_router, prefix=api_v1)
    app.include_router(checklist_router, prefix=api_v1)
    app.include_router(report_router, prefix=api_v1)
    app.include_router(admin_router, prefix=api_v1)
    app.include_router(career_router, prefix=api_v1)
    app.include_router(preference_router, prefix=api_v1)
    app.include_router(college_router, prefix=api_v1)

    # Health endpoints
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION, "env": settings.APP_ENV}

    @app.get("/ready", tags=["Health"], include_in_schema=False)
    async def ready() -> JSONResponse:
        checks: dict[str, str] = {}
        try:
            from sqlalchemy import text
            from app.core.database import engine
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["db"] = "ok"
        except Exception:
            checks["db"] = "error"

        try:
            from app.core.redis_client import get_redis
            r = get_redis()
            await r.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "fallback"

        checks["ml_model"] = "ok" if predictor._loaded else "fallback"
        all_ok = all(v in ("ok", "fallback") for v in checks.values())
        return JSONResponse(
            {"status": "ok" if all_ok else "degraded", **checks},
            status_code=200 if all_ok else 503,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if not isinstance(detail, dict):
            detail = {"error_code": "HTTP_ERROR", "message": str(detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback
        logger.error("unhandled_exception", error=str(exc), path=request.url.path, traceback=traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"},
        )

    return app


app = create_app()
