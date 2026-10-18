"""ML model version registry."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy import JSON as JSONB  # SQLite-compat
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPKMixin


class MlModelVersion(UUIDPKMixin, Base):
    __tablename__ = "ml_model_versions"

    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(100))
    accuracy: Mapped[float | None] = mapped_column(Numeric(5, 4))
    ece: Mapped[float | None] = mapped_column(Numeric(5, 4))
    metrics_json: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    artifact_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
