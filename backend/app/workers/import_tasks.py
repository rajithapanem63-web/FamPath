"""CSV import Celery tasks."""
from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.workers.import_tasks.process_import")
def process_import(
    self: Any,
    job_id: str,
    dataset_type: str,
    csv_content: str,
) -> None:
    """
    Parse a CSV string and import records into the database.
    Updates the ImportJob record with progress and errors.
    """
    import asyncio
    from sqlalchemy import select

    async def _run() -> None:
        from app.core.database import AsyncSessionLocal
        from app.models.college import ImportJob

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ImportJob).where(ImportJob.id == uuid.UUID(job_id)))
            job = result.scalar_one_or_none()
            if not job:
                return

            job.status = "processing"
            job.started_at = datetime.now(UTC)
            await db.commit()

            try:
                imported, skipped, errors = await _import_dataset(dataset_type, csv_content, db)
                job.status = "completed"
                job.total_rows = imported + skipped + len(errors)
                job.imported_rows = imported
                job.skipped_rows = skipped
                job.error_rows = len(errors)
                job.error_report = errors
                job.completed_at = datetime.now(UTC)
            except Exception as exc:
                job.status = "failed"
                job.error_report = [{"error": str(exc)}]
                job.completed_at = datetime.now(UTC)
                logger.error("import_failed", job_id=job_id, error=str(exc))

            await db.commit()

    asyncio.run(_run())


async def _import_dataset(
    dataset_type: str,
    csv_content: str,
    db: Any,
) -> tuple[int, int, list]:
    """Route to appropriate importer. Returns (imported, skipped, errors)."""
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    if dataset_type == "colleges":
        return await _import_colleges(rows, db)
    return 0, len(rows), [{"error": f"Importer for {dataset_type} not yet implemented"}]


async def _import_colleges(rows: list[dict], db: Any) -> tuple[int, int, list]:
    from app.models.college import College
    from sqlalchemy import select

    imported = 0
    skipped = 0
    errors: list[dict] = []

    for i, row in enumerate(rows, 1):
        try:
            code = (row.get("college_code") or "").strip()
            name = (row.get("name") or "").strip()
            if not code or not name:
                errors.append({"row": i, "error": "college_code and name are required"})
                skipped += 1
                continue

            existing = await db.execute(select(College).where(College.college_code == code))
            college = existing.scalar_one_or_none()
            now = datetime.now(UTC)

            if college:
                college.name = name
                college.state = row.get("state") or college.state
                college.district = row.get("district") or college.district
                college.updated_at = now
            else:
                college = College(
                    college_code=code,
                    name=name,
                    state=row.get("state"),
                    district=row.get("district"),
                    city=row.get("city"),
                    college_type=row.get("college_type"),
                    source=row.get("source", "CSV_IMPORT"),
                    source_year=int(row["source_year"]) if row.get("source_year") else None,
                    import_date=now,
                    verification_status="unverified",
                )
                db.add(college)

            imported += 1
        except Exception as exc:
            errors.append({"row": i, "error": str(exc)})
            skipped += 1

    return imported, skipped, errors
