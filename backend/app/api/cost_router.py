"""Cost, ROI, and scholarship API router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.college import FeeStructure, PlacementStat, Scholarship
from app.services.cost_service import (
    DISCLAIMER,
    FeeBreakdown,
    build_loan_scenarios,
    calculate_budget_plan,
    calculate_emi,
    check_scholarship_eligibility,
)

router = APIRouter(prefix="/cost", tags=["Cost & ROI"])


@router.get("/{college_id}/{program_id}", response_model=dict)
async def get_cost(
    college_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Get 4-year cost breakdown for a college/program."""
    result = await db.execute(
        select(FeeStructure)
        .where(
            FeeStructure.college_id == college_id,
            FeeStructure.program_id == program_id,
        )
        .order_by(FeeStructure.academic_year.desc())
        .limit(1)
    )
    fee = result.scalar_one_or_none()

    if not fee:
        return {
            "college_id": str(college_id),
            "program_id": str(program_id),
            "error": "No fee data available",
            "disclaimer": DISCLAIMER,
        }

    tuition = float(fee.tuition_fee or 0)
    hostel = float(fee.hostel_fee or 0)
    transport = float(fee.transport_fee or 0)
    other = float(fee.other_fees or 0)
    annual = tuition + hostel + transport + other
    total_4yr = annual * 4

    return {
        "college_id": str(college_id),
        "program_id": str(program_id),
        "annual_fee_breakdown": {
            "tuition": tuition,
            "hostel": hostel,
            "transport": transport,
            "other": other,
        },
        "total_annual_fee": annual,
        "total_4yr_cost": total_4yr,
        "data_year": fee.academic_year,
        "data_source": fee.source or "college records",
        "disclaimer": DISCLAIMER,
    }


@router.get("/scholarships", response_model=list[dict])
async def get_scholarships(
    category: str | None = Query(None),
    income_range: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> list[dict]:
    """Get eligible scholarships filtered by category and income range."""
    result = await db.execute(
        select(Scholarship).where(Scholarship.is_active == True)
    )
    all_scholarships = [
        {
            "id": str(s.id),
            "name": s.name,
            "name_te": s.name_te,
            "name_hi": s.name_hi,
            "provider": s.provider,
            "amount_per_year": float(s.amount_per_year or 0),
            "covers_hostel": s.covers_hostel,
            "eligible_categories": s.eligible_categories,
            "income_ceiling": float(s.income_ceiling) if s.income_ceiling else None,
            "application_url": s.application_url,
            "deadline_notes": s.deadline_notes,
            "data_source": s.source,
            "data_year": s.source_year,
            "verification_status": s.verification_status,
        }
        for s in result.scalars().all()
    ]

    return check_scholarship_eligibility(category, income_range, all_scholarships)


class BudgetPlanRequest(BaseModel):
    planned_budget_4yr: float
    annual_tuition: float
    annual_hostel: float = 0.0
    annual_transport: float = 0.0
    annual_other: float = 0.0
    annual_food_living: float = 25000.0
    confirmed_scholarship_annual: float = 0.0


@router.post("/budget-plan", response_model=dict, summary="Calculate family budget and affordability gap")
async def calculate_family_budget(
    data: BudgetPlanRequest,
    token=Depends(get_token_payload),
) -> dict:
    """Calculate 4-year education budget, out-of-pocket funding gap, and affordability."""
    plan = calculate_budget_plan(
        planned_budget_4yr=data.planned_budget_4yr,
        annual_tuition=data.annual_tuition,
        annual_hostel=data.annual_hostel,
        annual_transport=data.annual_transport,
        annual_other=data.annual_other,
        annual_food_living=data.annual_food_living,
        confirmed_scholarship_annual=data.confirmed_scholarship_annual,
    )
    return plan


@router.get("/roi/{college_id}/{program_id}", response_model=dict)
async def get_roi(
    college_id: uuid.UUID,
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> dict:
    """Get ROI analysis: placement data + loan scenarios."""
    # Get latest placement stats
    p_result = await db.execute(
        select(PlacementStat)
        .where(
            PlacementStat.college_id == college_id,
            PlacementStat.program_id == program_id,
        )
        .order_by(PlacementStat.placement_year.desc())
        .limit(1)
    )
    placement = p_result.scalar_one_or_none()

    # Get fee for loan scenarios
    f_result = await db.execute(
        select(FeeStructure)
        .where(
            FeeStructure.college_id == college_id,
            FeeStructure.program_id == program_id,
        )
        .order_by(FeeStructure.academic_year.desc())
        .limit(1)
    )
    fee = f_result.scalar_one_or_none()
    total_4yr = 0.0
    if fee:
        total_4yr = float((fee.tuition_fee or 0) + (fee.hostel_fee or 0) +
                          (fee.transport_fee or 0) + (fee.other_fees or 0)) * 4

    median_lpa = float(placement.median_package_lpa) if placement and placement.median_package_lpa else None
    scenarios = build_loan_scenarios(total_4yr, median_lpa)

    return {
        "college_id": str(college_id),
        "program_id": str(program_id),
        "median_placement_lpa": median_lpa,
        "placement_year": placement.placement_year if placement else None,
        "placement_source": placement.source if placement else None,
        "loan_scenarios": [
            {
                "loan_amount": s.loan_amount,
                "interest_rate_pct": s.interest_rate_pct,
                "tenure_months": s.tenure_months,
                "monthly_emi": s.monthly_emi,
                "payback_months_at_30pct_salary": s.payback_months_at_30pct,
            }
            for s in scenarios
        ],
        "disclaimer": DISCLAIMER,
    }
