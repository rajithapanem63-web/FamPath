"""Colleges and College Comparison API Router."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.college import College, CollegeProgram, FeeStructure, PlacementStat

router = APIRouter(prefix="/colleges", tags=["Colleges & Comparison"])


class CompareItemRequest(BaseModel):
    college_id: uuid.UUID
    program_id: uuid.UUID | None = None


class CompareRequest(BaseModel):
    items: list[CompareItemRequest] = Field(min_length=2, max_length=4)


class CollegeComparisonItem(BaseModel):
    college_id: str
    college_code: str
    name: str
    college_type: str | None
    state: str | None
    district: str | None
    city: str | None
    affiliation: str | None
    naac_grade: str | None
    established_year: int | None
    website: str | None
    # Program
    program_id: str | None
    branch_code: str | None
    branch_name: str | None
    intake_seats: int | None
    # Fee & Cost
    annual_tuition: float | None
    annual_hostel: float | None
    annual_transport: float | None
    annual_total: float | None
    estimated_4yr_cost: float | None
    fee_data_year: int | None
    fee_source: str | None
    # Placement
    placed_percent: float | None
    median_package_lpa: float | None
    avg_package_lpa: float | None
    highest_package_lpa: float | None
    top_recruiters: list[str]
    placement_year: int | None
    placement_source: str | None
    # Data Quality
    missing_fields: list[str]


class CompareResponse(BaseModel):
    colleges: list[CollegeComparisonItem]
    insights: list[str]
    disclaimer: str


@router.post("/compare", response_model=CompareResponse, summary="Compare 2 to 4 colleges")
async def compare_colleges(
    data: CompareRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> CompareResponse:
    """Compare 2–4 engineering colleges side-by-side with fees, facilities, and placements."""
    results: list[CollegeComparisonItem] = []

    for item in data.items:
        # 1. Fetch College
        col_res = await db.execute(select(College).where(College.id == item.college_id))
        college = col_res.scalar_one_or_none()
        if not college:
            continue

        missing: list[str] = []

        # 2. Fetch Program
        program: CollegeProgram | None = None
        if item.program_id:
            prog_res = await db.execute(
                select(CollegeProgram).where(CollegeProgram.id == item.program_id)
            )
            program = prog_res.scalar_one_or_none()
        else:
            # Default to first program
            prog_res = await db.execute(
                select(CollegeProgram)
                .where(CollegeProgram.college_id == college.id)
                .order_by(CollegeProgram.branch_code)
                .limit(1)
            )
            program = prog_res.scalar_one_or_none()

        # 3. Fetch Fee Structure
        fee_query = select(FeeStructure).where(FeeStructure.college_id == college.id)
        if program:
            fee_query = fee_query.where(FeeStructure.program_id == program.id)
        fee_query = fee_query.order_by(FeeStructure.academic_year.desc()).limit(1)
        fee_res = await db.execute(fee_query)
        fee = fee_res.scalar_one_or_none()

        tuition = float(fee.tuition_fee) if fee and fee.tuition_fee is not None else None
        hostel = float(fee.hostel_fee) if fee and fee.hostel_fee is not None else None
        transport = float(fee.transport_fee) if fee and fee.transport_fee is not None else None
        other = float(fee.other_fees) if fee and fee.other_fees is not None else None

        if tuition is None:
            missing.append("Tuition Fee data")
        if hostel is None:
            missing.append("Hostel Fee data")

        annual_total = None
        est_4yr = None
        if tuition is not None:
            annual_total = tuition + (hostel or 0) + (transport or 0) + (other or 0)
            est_4yr = annual_total * 4

        # 4. Fetch Placement Stat
        place_query = select(PlacementStat).where(PlacementStat.college_id == college.id)
        if program:
            place_query = place_query.where(PlacementStat.program_id == program.id)
        place_query = place_query.order_by(PlacementStat.placement_year.desc()).limit(1)
        place_res = await db.execute(place_query)
        placement = place_res.scalar_one_or_none()

        placed_pct = float(placement.placed_percent) if placement and placement.placed_percent is not None else None
        median_lpa = float(placement.median_package_lpa) if placement and placement.median_package_lpa is not None else None
        avg_lpa = float(placement.avg_package_lpa) if placement and placement.avg_package_lpa is not None else None
        highest_lpa = float(placement.highest_package_lpa) if placement and placement.highest_package_lpa is not None else None
        recruiters = (placement.top_recruiters or []) if placement else []

        if placed_pct is None:
            missing.append("Placement percentage")
        if median_lpa is None:
            missing.append("Median salary data")
        if not college.naac_grade:
            missing.append("NAAC grade")

        results.append(
            CollegeComparisonItem(
                college_id=str(college.id),
                college_code=college.college_code,
                name=college.name,
                college_type=college.college_type,
                state=college.state,
                district=college.district,
                city=college.city,
                affiliation=college.affiliation,
                naac_grade=college.naac_grade,
                established_year=college.established_year,
                website=college.website,
                program_id=str(program.id) if program else None,
                branch_code=program.branch_code if program else None,
                branch_name=program.branch_name if program else None,
                intake_seats=program.intake_seats if program else None,
                annual_tuition=tuition,
                annual_hostel=hostel,
                annual_transport=transport,
                annual_total=annual_total,
                estimated_4yr_cost=est_4yr,
                fee_data_year=fee.academic_year if fee else None,
                fee_source=fee.source if fee else None,
                placed_percent=placed_pct,
                median_package_lpa=median_lpa,
                avg_package_lpa=avg_lpa,
                highest_package_lpa=highest_lpa,
                top_recruiters=[str(r) for r in recruiters],
                placement_year=placement.placement_year if placement else None,
                placement_source=placement.source if placement else None,
                missing_fields=missing,
            )
        )

    # 5. Build explainable comparison insights
    insights: list[str] = []
    if len(results) >= 2:
        # Cost comparison
        valid_costs = [(r.name, r.estimated_4yr_cost) for r in results if r.estimated_4yr_cost is not None]
        if len(valid_costs) >= 2:
            sorted_costs = sorted(valid_costs, key=lambda x: x[1])
            cheapest = sorted_costs[0]
            costliest = sorted_costs[-1]
            diff = costliest[1] - cheapest[1]
            if diff > 0:
                insights.append(
                    f"{cheapest[0]} has the most economical 4-year estimated cost (₹{cheapest[1]:,.0f}), "
                    f"saving ₹{diff:,.0f} compared to {costliest[0]} (₹{costliest[1]:,.0f})."
                )

        # Placement comparison
        valid_medians = [(r.name, r.median_package_lpa) for r in results if r.median_package_lpa is not None]
        if len(valid_medians) >= 2:
            sorted_pkg = sorted(valid_medians, key=lambda x: x[1], reverse=True)
            top_pkg = sorted_pkg[0]
            insights.append(
                f"{top_pkg[0]} reports the highest median package at ₹{top_pkg[1]:.1f} LPA."
            )

        # Location / type
        types = {r.name: r.college_type for r in results if r.college_type}
        if len(set(types.values())) > 1:
            desc = ", ".join(f"{name} is {ctype}" for name, ctype in types.items())
            insights.append(f"Institutional governance: {desc}.")

    disclaimer = (
        "Comparison data is sourced from verified official records and institutional submissions. "
        "Missing fields are explicitly highlighted. Placement statistics reflect historical reporting "
        "and do not guarantee future placement outcomes."
    )

    return CompareResponse(colleges=results, insights=insights, disclaimer=disclaimer)
