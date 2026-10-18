"""Aptitude quiz and branch-fit API router."""
from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.aptitude import AptitudeResult, QuizQuestion, QuizResponse, QuizSession
from app.services.aptitude_service import (
    compute_branch_fit,
    compute_riasec_scores,
    format_top_branches,
)
from app.services.aptitude_service import (
    compute_branch_fit as _compute_branch_fit,
    compute_riasec_scores as _compute_riasec_scores,
    format_top_branches as _format_top_branches,
)

router = APIRouter(prefix="/aptitude", tags=["Aptitude & Branch Fit"])
public_router = APIRouter(prefix="/aptitude/public", tags=["Aptitude Public"])


class PublicAnswersRequest(BaseModel):
    responses: list[dict] = Field(min_length=1,
        description="List of {question_id, value} dicts")


@public_router.get("/questions", response_model=StartSessionResponse, summary="Get aptitude questions (no login required)")
async def public_start_quiz(
    db: AsyncSession = Depends(get_db),
) -> StartSessionResponse:
    """Public endpoint — returns questions without requiring authentication."""
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.is_active == True)
    )
    questions = result.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail={"error_code": "NO_QUESTIONS_AVAILABLE"})

    # Deterministic shuffle based on count so it's reproducible
    shuffled = list(questions)[:20]
    # Give a fake session_id so frontend can track locally
    fake_session_id = uuid.uuid5(uuid.NAMESPACE_DNS, "public-quiz")

    return StartSessionResponse(
        session_id=fake_session_id,
        questions=[
            QuestionResponse(id=q.id, text=q.question_text, options=q.options, riasec_dimension=q.riasec_dimension)
            for q in shuffled
        ],
        total=len(shuffled),
    )


@public_router.post("/submit", response_model=SubmitResponse, summary="Submit aptitude answers (no login required)")
async def public_submit_quiz(
    data: PublicAnswersRequest,
    db: AsyncSession = Depends(get_db),
) -> SubmitResponse:
    """Public endpoint — computes RIASEC scores without saving to DB or requiring auth."""
    # Fetch question metadata for the given question IDs
    question_ids = [uuid.UUID(r["question_id"]) for r in data.responses if "question_id" in r]
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.id.in_(question_ids))
    )
    questions_map = {str(q.id): q for q in result.scalars().all()}

    response_dicts = []
    for r in data.responses:
        qid = r.get("question_id", "")
        q = questions_map.get(qid)
        if q:
            response_dicts.append({
                "question_id": qid,
                "riasec_dimension": q.riasec_dimension,
                "response_value": r.get("value", 3),
                "weight": float(q.weight),
            })

    riasec = compute_riasec_scores(response_dicts)
    branch_fits = compute_branch_fit(riasec)
    top_branches = format_top_branches(branch_fits)
    branch_fit_dict = {r.branch_code: r.score for r in branch_fits}

    return SubmitResponse(
        riasec_scores=riasec,
        branch_fit_scores=branch_fit_dict,
        top_branches=top_branches,
    )



class QuestionResponse(BaseModel):
    id: uuid.UUID
    text: str
    options: list | None
    riasec_dimension: str


class StartSessionResponse(BaseModel):
    session_id: uuid.UUID
    questions: list[QuestionResponse]
    total: int


class SaveResponsesRequest(BaseModel):
    responses: list[dict] = Field(min_length=1)


class SubmitResponse(BaseModel):
    riasec_scores: dict
    branch_fit_scores: dict
    top_branches: list


@router.get("/questions", response_model=StartSessionResponse, summary="Start aptitude quiz")
async def start_quiz(
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> StartSessionResponse:
    """Create a quiz session with randomised question order."""
    # Get active questions
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.is_active == True)
    )
    questions = result.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail={"error_code": "NO_QUESTIONS_AVAILABLE"})

    # Randomise order with user-id seed for reproducibility
    rng = random.Random(str(token.user_id))
    shuffled = list(questions)
    rng.shuffle(shuffled)
    shuffled = shuffled[:20]  # cap at 20

    # Create session
    now = datetime.now(UTC)
    session = QuizSession(
        student_id=token.user_id,
        status="in_progress",
        question_order=[str(q.id) for q in shuffled],
        started_at=now,
        created_at=now,
    )
    db.add(session)
    await db.flush()

    question_responses = []
    for q in shuffled:
        question_responses.append(QuestionResponse(
            id=q.id,
            text=q.question_text,
            options=q.options,
            riasec_dimension=q.riasec_dimension,
        ))

    return StartSessionResponse(
        session_id=session.id,
        questions=question_responses,
        total=len(shuffled),
    )


@router.post("/sessions/{session_id}/responses", response_model=dict)
async def save_responses(
    session_id: uuid.UUID,
    data: SaveResponsesRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Save partial or full responses to a quiz session."""
    session_result = await db.execute(
        select(QuizSession).where(
            QuizSession.id == session_id,
            QuizSession.student_id == token.user_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail={"error_code": "SESSION_NOT_FOUND"})

    now = datetime.now(UTC)
    for r in data.responses:
        resp = QuizResponse(
            session_id=session_id,
            question_id=uuid.UUID(r["question_id"]),
            response_value=r["value"],
            answered_at=now,
        )
        db.add(resp)

    # Get total answered
    existing = await db.execute(
        select(QuizResponse).where(QuizResponse.session_id == session_id)
    )
    answered = len(existing.scalars().all()) + len(data.responses)
    total = len(session.question_order or [])

    return {"saved": True, "progress": {"answered": answered, "total": total}}


@router.post("/sessions/{session_id}/submit", response_model=SubmitResponse)
async def submit_quiz(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> SubmitResponse:
    """Compute RIASEC scores and branch fit after quiz completion."""
    session_result = await db.execute(
        select(QuizSession).where(
            QuizSession.id == session_id,
            QuizSession.student_id == token.user_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail={"error_code": "SESSION_NOT_FOUND"})

    # Fetch responses with question metadata
    responses_result = await db.execute(
        select(QuizResponse, QuizQuestion)
        .join(QuizQuestion, QuizResponse.question_id == QuizQuestion.id)
        .where(QuizResponse.session_id == session_id)
    )
    rows = responses_result.all()

    response_dicts = [
        {
            "question_id": str(r.question_id),
            "riasec_dimension": q.riasec_dimension,
            "response_value": r.response_value,
            "weight": float(q.weight),
        }
        for r, q in rows
    ]

    riasec = compute_riasec_scores(response_dicts)
    branch_fits = compute_branch_fit(riasec)
    top_branches = format_top_branches(branch_fits)

    branch_fit_dict = {r.branch_code: r.score for r in branch_fits}

    # Mark session complete
    session.status = "completed"
    session.completed_at = datetime.now(UTC)

    # Store result
    result = AptitudeResult(
        student_id=token.user_id,
        session_id=session_id,
        riasec_scores=riasec,
        branch_fit_scores=branch_fit_dict,
        top_branches=top_branches,
        created_at=datetime.now(UTC),
    )
    db.add(result)

    return SubmitResponse(
        riasec_scores=riasec,
        branch_fit_scores=branch_fit_dict,
        top_branches=top_branches,
    )


@router.get("/results/latest", response_model=SubmitResponse | None)
async def get_latest_result(
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> SubmitResponse | None:
    """Get the most recent aptitude result for the current user."""
    result = await db.execute(
        select(AptitudeResult)
        .where(AptitudeResult.student_id == token.user_id)
        .order_by(AptitudeResult.created_at.desc())
        .limit(1)
    )
    ar = result.scalar_one_or_none()
    if not ar:
        return None
    return SubmitResponse(
        riasec_scores=ar.riasec_scores or {},
        branch_fit_scores=ar.branch_fit_scores or {},
        top_branches=ar.top_branches or [],
    )
