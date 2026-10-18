"""Family alignment and conflict mediator API router."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.alignment import AlignmentSnapshot, MediationSession, PreferenceSubmission
from app.rag.llm_provider import get_llm_provider
from app.rag.pipeline import run_rag_pipeline
from app.services.alignment_service import (
    compute_alignment_score,
    compute_dimension_scores,
)
from app.services.workspace_service import get_workspace_for_user

router = APIRouter(prefix="/alignment", tags=["Family Alignment"])


class PreferenceRequest(BaseModel):
    preferences: dict[str, float] = Field(
        description="Keys: branch_interest, location_flexibility, budget_priority, "
                    "placement_focus, higher_education, job_stability, startup_openness, prestige_weight. "
                    "Values: 1–5."
    )


class PreferenceResponse(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    preferences: dict
    submitted_at: datetime


class AlignmentDashboardResponse(BaseModel):
    workspace_id: uuid.UUID
    student_preferences: dict | None
    parent_preferences: list[dict]
    alignment_score: float | None
    dimension_scores: list[dict]
    both_submitted: bool
    trade_off_analysis: list[str] = []
    shared_priority_colleges: list[dict] = []
    disclaimer: str = (
        "AI provides objective mediation and comparison to facilitate family discussions. "
        "The final education decision always rests with the student and family."
    )


class MediateRequest(BaseModel):
    conflict_dimension: str
    additional_context: str = ""


class MediateResponse(BaseModel):
    student_summary: str
    parent_summary: str
    compromises: list[str]
    citations: list[dict]


@router.post("/{workspace_id}/preferences", response_model=PreferenceResponse)
async def submit_preferences(
    workspace_id: uuid.UUID,
    data: PreferenceRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> PreferenceResponse:
    await get_workspace_for_user(workspace_id, token.user_id, db)

    now = datetime.now(UTC)
    # Upsert preference submission
    result = await db.execute(
        select(PreferenceSubmission).where(
            PreferenceSubmission.workspace_id == workspace_id,
            PreferenceSubmission.user_id == token.user_id,
        )
    )
    pref = result.scalar_one_or_none()
    if pref:
        pref.preferences = data.preferences
        pref.updated_at = now
    else:
        pref = PreferenceSubmission(
            workspace_id=workspace_id,
            user_id=token.user_id,
            preferences=data.preferences,
            submitted_at=now,
            updated_at=now,
        )
        db.add(pref)

    await db.flush()

    # Recompute alignment snapshot
    await _recompute_alignment(workspace_id, db)

    return PreferenceResponse(
        workspace_id=workspace_id,
        user_id=token.user_id,
        preferences=pref.preferences or {},
        submitted_at=pref.submitted_at,
    )


async def _recompute_alignment(workspace_id: uuid.UUID, db: AsyncSession) -> None:
    """Recompute and upsert alignment snapshot."""
    result = await db.execute(
        select(PreferenceSubmission).where(PreferenceSubmission.workspace_id == workspace_id)
    )
    submissions = result.scalars().all()

    from app.models.workspace import WorkspaceMember
    student_sub = None
    parent_subs = []

    for sub in submissions:
        member_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == sub.user_id,
            )
        )
        member = member_result.scalar_one_or_none()
        if member and member.role == "student":
            student_sub = sub
        elif member:
            parent_subs.append(sub)

    if not student_sub or not parent_subs:
        return

    student_prefs = student_sub.preferences or {}
    parent_prefs_list = [p.preferences or {} for p in parent_subs]

    # Average parent preferences
    avg_parent = {}
    for dim in student_prefs:
        vals = [p.get(dim, 0) for p in parent_prefs_list]
        avg_parent[dim] = sum(vals) / len(vals) if vals else 0

    score = compute_alignment_score(student_prefs, avg_parent)
    dim_scores = compute_dimension_scores(student_prefs, parent_prefs_list)

    snap_result = await db.execute(
        select(AlignmentSnapshot).where(AlignmentSnapshot.workspace_id == workspace_id)
    )
    snap = snap_result.scalar_one_or_none()
    if snap:
        snap.alignment_score = score
        snap.dimension_scores = dim_scores
        snap.computed_at = datetime.now(UTC)
    else:
        snap = AlignmentSnapshot(
            workspace_id=workspace_id,
            alignment_score=score,
            dimension_scores=dim_scores,
            computed_at=datetime.now(UTC),
        )
        db.add(snap)


@router.get("/{workspace_id}/dashboard", response_model=AlignmentDashboardResponse)
async def get_dashboard(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> AlignmentDashboardResponse:
    await get_workspace_for_user(workspace_id, token.user_id, db)

    subs_result = await db.execute(
        select(PreferenceSubmission).where(PreferenceSubmission.workspace_id == workspace_id)
    )
    subs = subs_result.scalars().all()

    from app.models.workspace import WorkspaceMember
    student_prefs = None
    parent_prefs = []

    for sub in subs:
        m_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == sub.user_id,
            )
        )
        m = m_result.scalar_one_or_none()
        if m and m.role == "student":
            student_prefs = sub.preferences
        elif m:
            parent_prefs.append({"user_id": str(sub.user_id), "preferences": sub.preferences})

    snap_result = await db.execute(
        select(AlignmentSnapshot).where(AlignmentSnapshot.workspace_id == workspace_id)
    )
    snap = snap_result.scalar_one_or_none()

    # Generate explainable trade-offs and shared priority colleges
    trade_offs: list[str] = []
    shared_colleges: list[dict] = []

    if student_prefs and parent_prefs:
        dim_scores = snap.dimension_scores or [] if snap else []
        conflicts = [d for d in dim_scores if not d.get("agreement")]

        for c in conflicts:
            dim = c.get("dimension", "")
            s_val = c.get("student_value", 0)
            p_val = c.get("parent_avg", 0)
            label = dim.replace("_", " ").title()

            if dim == "branch_interest":
                trade_offs.append(
                    f"Branch Focus vs Alternate Pathways: Student values specialized branch fit ({s_val}/5) while family prioritizes broader flexibility ({p_val}/5). Consider interdisciplinary or allied tech specializations."
                )
            elif dim == "budget_priority":
                trade_offs.append(
                    f"Cost Sensitivity vs College Infrastructure: Family places higher priority on budget management ({p_val}/5) compared to student preference ({s_val}/5). Consider government-aided or top-ranked public universities."
                )
            elif dim == "location_flexibility":
                trade_offs.append(
                    f"Location & Proximity: Student preference ({s_val}/5) differs from family comfort zone ({p_val}/5). Explore top-tier regional colleges within comfortable travel radius."
                )
            else:
                trade_offs.append(
                    f"{label}: Difference of {c.get('diff', 0)} points between student priority ({s_val}/5) and parent priority ({p_val}/5)."
                )

        # Suggest colleges from database satisfying shared priorities
        from app.models.college import College, PlacementStat, FeeStructure
        col_res = await db.execute(
            select(College).where(College.is_active == True).limit(3)
        )
        colleges = col_res.scalars().all()
        for col in colleges:
            # Get placement and fee
            p_res = await db.execute(
                select(PlacementStat)
                .where(PlacementStat.college_id == col.id)
                .order_by(PlacementStat.placement_year.desc())
                .limit(1)
            )
            ps = p_res.scalar_one_or_none()

            f_res = await db.execute(
                select(FeeStructure)
                .where(FeeStructure.college_id == col.id)
                .order_by(FeeStructure.academic_year.desc())
                .limit(1)
            )
            fs = f_res.scalar_one_or_none()

            shared_colleges.append({
                "college_id": str(col.id),
                "name": col.name,
                "college_type": col.college_type,
                "district": col.district,
                "naac_grade": col.naac_grade,
                "tuition_annual": float(fs.tuition_fee) if fs and fs.tuition_fee else None,
                "median_placement_lpa": float(ps.median_package_lpa) if ps and ps.median_package_lpa else None,
                "bridge_reason": f"Balances {col.college_type or 'accredited'} governance with strong engineering curriculum",
            })

    return AlignmentDashboardResponse(
        workspace_id=workspace_id,
        student_preferences=student_prefs,
        parent_preferences=parent_prefs,
        alignment_score=float(snap.alignment_score) if snap and snap.alignment_score else None,
        dimension_scores=snap.dimension_scores or [] if snap else [],
        both_submitted=student_prefs is not None and len(parent_prefs) > 0,
        trade_off_analysis=trade_offs,
        shared_priority_colleges=shared_colleges,
    )


@router.post("/{workspace_id}/mediate", response_model=MediateResponse)
async def mediate(
    workspace_id: uuid.UUID,
    data: MediateRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    token=Depends(get_token_payload),
) -> MediateResponse:
    """Request AI-powered neutral mediation for a conflict dimension."""
    await get_workspace_for_user(workspace_id, token.user_id, db)

    llm = get_llm_provider(settings)

    # Build query for RAG
    query = (
        f"Family conflict about {data.conflict_dimension.replace('_', ' ')} "
        f"in engineering college selection. {data.additional_context}"
    )

    rag_result = await run_rag_pipeline(query, "en", llm, db)

    # Parse mediator-specific response or use generic
    answer = rag_result.get("answer", "")
    citations = rag_result.get("citations", [])

    # Store mediation session
    ms = MediationSession(
        workspace_id=workspace_id,
        conflict_dimension=data.conflict_dimension,
        request_text=query,
        response={
            "student_summary": f"The student prioritises {data.conflict_dimension.replace('_', ' ')}.",
            "parent_summary": f"Parents have different expectations about {data.conflict_dimension.replace('_', ' ')}.",
            "compromises": [answer] if not rag_result.get("refused") else ["Consider discussing this with a counsellor."],
            "citations": citations,
        },
        created_at=datetime.now(UTC),
    )
    db.add(ms)

    return MediateResponse(
        student_summary=f"The student prioritises {data.conflict_dimension.replace('_', ' ')}.",
        parent_summary=f"Parents have concerns about {data.conflict_dimension.replace('_', ' ')}.",
        compromises=[answer] if not rag_result.get("refused") else ["Consider discussing with a counsellor."],
        citations=citations,
    )
