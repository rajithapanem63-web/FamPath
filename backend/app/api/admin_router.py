"""Admin API router: college management, CSV import, freshness, question bank."""
from __future__ import annotations

import hashlib
import io
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.college import College, CollegeProgram, CutoffRecord, FeeStructure, ImportJob, PlacementStat, Scholarship
from app.models.aptitude import QuizQuestion

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

_admin_only = require_role("admin")

MAX_IMPORT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ── College CRUD ──────────────────────────────────────────────────────────────

class CollegeCreate(BaseModel):
    college_code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=255)
    state: str | None = None
    district: str | None = None
    city: str | None = None
    college_type: str | None = None
    source: str | None = None
    source_year: int | None = None


@router.get("/colleges", response_model=list[dict], dependencies=[_admin_only])
async def list_colleges(
    search: str | None = Query(None),
    state: str | None = Query(None),
    college_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    query = select(College).where(College.is_active == True)
    if search:
        query = query.where(College.name.ilike(f"%{search}%"))
    if state:
        query = query.where(College.state == state)
    if college_type:
        query = query.where(College.college_type == college_type)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return [
        {
            "id": str(c.id),
            "college_code": c.college_code,
            "name": c.name,
            "state": c.state,
            "district": c.district,
            "college_type": c.college_type,
            "verification_status": c.verification_status,
        }
        for c in result.scalars().all()
    ]


@router.post("/colleges", response_model=dict, status_code=201, dependencies=[_admin_only])
async def create_college(
    data: CollegeCreate,
    db: AsyncSession = Depends(get_db),
    token=_admin_only,
) -> dict:
    now = datetime.now(UTC)
    college = College(
        college_code=data.college_code,
        name=data.name,
        state=data.state,
        district=data.district,
        city=data.city,
        college_type=data.college_type,
        source=data.source,
        source_year=data.source_year,
        import_date=now,
    )
    db.add(college)
    await db.flush()
    return {"id": str(college.id), "message": "College created"}


# ── CSV Import ────────────────────────────────────────────────────────────────

DATASET_TYPES = {"colleges", "cutoffs", "fees", "placements", "scholarships"}


@router.post("/import/{dataset_type}", response_model=dict, status_code=202, dependencies=[_admin_only])
async def import_csv(
    dataset_type: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    token=_admin_only,
) -> dict:
    if dataset_type not in DATASET_TYPES:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_DATASET_TYPE"})

    content = await file.read()
    if len(content) > MAX_IMPORT_SIZE_BYTES:
        raise HTTPException(status_code=413, detail={"error_code": "FILE_TOO_LARGE"})

    file_hash = hashlib.sha256(content).hexdigest()
    now = datetime.now(UTC)

    job = ImportJob(
        admin_id=token.user_id,
        dataset_type=dataset_type,
        filename=file.filename or "upload.csv",
        file_hash=file_hash,
        status="pending",
        created_at=now,
    )
    db.add(job)
    await db.flush()

    # Trigger Celery task
    from app.workers.import_tasks import process_import
    process_import.delay(str(job.id), dataset_type, content.decode("utf-8", errors="replace"))

    return {"job_id": str(job.id), "status": "pending"}


@router.get("/import/{job_id}", response_model=dict, dependencies=[_admin_only])
async def get_import_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND"})
    return {
        "job_id": str(job.id),
        "status": job.status,
        "total_rows": job.total_rows,
        "imported_rows": job.imported_rows,
        "skipped_rows": job.skipped_rows,
        "error_rows": job.error_rows,
        "error_report": job.error_report,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/freshness", response_model=list[dict], dependencies=[_admin_only])
async def get_freshness(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Return data freshness summary per dataset type."""
    from sqlalchemy import cast, Integer
    from datetime import date

    datasets = []
    for dtype in DATASET_TYPES:
        result = await db.execute(
            select(
                func.max(ImportJob.completed_at),
                func.count(ImportJob.id),
            ).where(ImportJob.dataset_type == dtype, ImportJob.status == "completed")
        )
        row = result.one()
        last_import = row[0]
        import_count = row[1]

        is_stale = False
        if last_import:
            age_days = (datetime.now(UTC) - last_import).days
            is_stale = age_days > 365

        datasets.append({
            "dataset_type": dtype,
            "last_import": last_import.isoformat() if last_import else None,
            "import_count": import_count,
            "is_stale": is_stale,
        })

    return datasets


# ── Question Bank ─────────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    question_text: str
    question_te: str
    question_hi: str
    riasec_dimension: str = Field(pattern="^[RIASEC]$")
    weight: float = Field(default=1.0, ge=0.1, le=5.0)
    options: list | None = None


@router.get("/questions", response_model=list[dict], dependencies=[_admin_only])
async def list_questions(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.is_active == True))
    return [
        {
            "id": str(q.id),
            "question_text": q.question_text,
            "riasec_dimension": q.riasec_dimension,
            "is_active": q.is_active,
        }
        for q in result.scalars().all()
    ]


@router.post("/questions", response_model=dict, status_code=201, dependencies=[_admin_only])
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    token=_admin_only,
) -> dict:
    now = datetime.now(UTC)
    q = QuizQuestion(
        question_text=data.question_text,
        question_te=data.question_te,
        question_hi=data.question_hi,
        riasec_dimension=data.riasec_dimension,
        weight=data.weight,
        options=data.options,
        is_active=True,
        created_by=token.user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(q)
    await db.flush()
    return {"id": str(q.id), "message": "Question created"}


@router.delete("/questions/{question_id}", response_model=dict, dependencies=[_admin_only])
async def deactivate_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail={"error_code": "QUESTION_NOT_FOUND"})
    q.is_active = False
    return {"message": "Question deactivated"}
