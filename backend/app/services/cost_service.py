"""
Cost, ROI, and scholarship service.
All financial calculations are pure functions for easy testing.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

DISCLAIMER = "Estimate only. Fees may change. Verify directly with the institution."


@dataclass
class FeeBreakdown:
    tuition: float
    hostel: float
    transport: float
    other: float
    total_annual: float
    total_4yr: float
    data_year: int
    data_source: str
    disclaimer: str = DISCLAIMER
    fee_data_note: str | None = None


@dataclass
class LoanScenario:
    loan_amount: float
    interest_rate_pct: float
    tenure_months: int
    monthly_emi: float
    payback_months_at_30pct: float | None


def calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """
    Standard EMI formula: P × r × (1+r)^n / ((1+r)^n - 1)
    where r = monthly rate = annual_rate_pct / 12 / 100
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    r = annual_rate_pct / 12 / 100
    if r == 0:
        return principal / tenure_months
    return round(principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1), 2)


def calculate_payback_months(
    loan_amount: float,
    monthly_salary: float,
    repayment_ratio: float = 0.30,
) -> float | None:
    """
    Estimate months to repay loan if repayment_ratio of monthly salary is used.
    Returns None if salary is 0.
    """
    if monthly_salary <= 0:
        return None
    monthly_payment = monthly_salary * repayment_ratio
    return round(loan_amount / monthly_payment, 1)


def build_loan_scenarios(
    total_4yr_cost: float,
    median_salary_lpa: float | None,
    loan_fractions: list[float] | None = None,
) -> list[LoanScenario]:
    """
    Generate loan scenarios for 50%, 75%, 100% of total cost
    at a standard 8.5% education loan rate over 60 months.
    """
    fractions = loan_fractions or [0.5, 0.75, 1.0]
    monthly_salary = (median_salary_lpa or 0) * 100000 / 12

    scenarios = []
    for frac in fractions:
        loan = round(total_4yr_cost * frac, 2)
        emi = calculate_emi(loan, 8.5, 60)
        payback = calculate_payback_months(loan, monthly_salary) if median_salary_lpa else None
        scenarios.append(
            LoanScenario(
                loan_amount=loan,
                interest_rate_pct=8.5,
                tenure_months=60,
                monthly_emi=emi,
                payback_months_at_30pct=payback,
            )
        )
    return scenarios


def check_scholarship_eligibility(
    category: str | None,
    income_range: str | None,
    scholarships: list[dict],
) -> list[dict]:
    """
    Filter scholarships by category and income, providing verified suitability explanations.
    income_range: 'low' (<2L), 'medium' (2–8L), 'high' (>8L).
    """
    INCOME_CEILINGS = {"low": 200000, "medium": 800000, "high": float("inf")}
    user_income = INCOME_CEILINGS.get(income_range or "", float("inf"))

    eligible = []
    for s in scholarships:
        reasons: list[str] = []
        cats = s.get("eligible_categories") or []
        if cats and category:
            if category in cats:
                reasons.append(f"Matches your category criteria ({category})")
            else:
                continue

        ceiling = s.get("income_ceiling")
        if ceiling is not None:
            if user_income > ceiling and income_range:
                continue
            reasons.append(f"Family income within eligibility ceiling (₹{ceiling:,.0f}/yr)")
        else:
            reasons.append("Open category / income ceiling not restricted")

        if s.get("covers_hostel"):
            reasons.append("Covers boarding / hostel maintenance allowances")

        amt = float(s.get("amount_per_year") or 0)
        if amt > 0:
            reasons.append(f"Provides up to ₹{amt:,.0f}/year in direct education support")

        s_copy = dict(s)
        s_copy["suitability_reasons"] = reasons
        eligible.append(s_copy)

    return eligible


def calculate_budget_plan(
    planned_budget_4yr: float,
    annual_tuition: float,
    annual_hostel: float = 0.0,
    annual_transport: float = 0.0,
    annual_other: float = 0.0,
    annual_food_living: float = 25000.0,
    confirmed_scholarship_annual: float = 0.0,
) -> dict:
    """Calculate 4-year total cost, out-of-pocket, funding gap, and affordability."""
    annual_gross = annual_tuition + annual_hostel + annual_transport + annual_other + annual_food_living
    total_4yr_cost = annual_gross * 4
    total_scholarship_4yr = confirmed_scholarship_annual * 4
    net_family_out_of_pocket = max(0.0, total_4yr_cost - total_scholarship_4yr)

    funding_gap = max(0.0, net_family_out_of_pocket - planned_budget_4yr)
    surplus = max(0.0, planned_budget_4yr - net_family_out_of_pocket)

    if funding_gap == 0:
        tier = "Fully Affordable Within Budget"
        tier_color = "green"
    elif funding_gap <= 150000:
        tier = "Moderate Gap (Manageable via education loan or savings)"
        tier_color = "amber"
    else:
        tier = "Significant Funding Gap (Requires financial aid or low-cost options)"
        tier_color = "red"

    assumptions = [
        "4-year calculation assumes standard 8 semesters without tuition escalation.",
        "Food & personal living expenses estimated at standard regional benchmark (₹25,000/yr).",
        "Confirmed scholarship assumes annual renewal meeting minimum CGPA/attendance standards.",
        "Calculations are strictly estimates for family planning and do not guarantee loan sanction or fee freezes.",
    ]

    return {
        "total_4yr_cost": round(total_4yr_cost, 2),
        "total_scholarship_4yr": round(total_scholarship_4yr, 2),
        "net_family_out_of_pocket": round(net_family_out_of_pocket, 2),
        "planned_budget_4yr": round(planned_budget_4yr, 2),
        "funding_gap": round(funding_gap, 2),
        "surplus": round(surplus, 2),
        "affordability_tier": tier,
        "affordability_color": tier_color,
        "breakdown_annual": {
            "tuition": round(annual_tuition, 2),
            "hostel": round(annual_hostel, 2),
            "transport": round(annual_transport, 2),
            "other_college_fees": round(annual_other, 2),
            "estimated_food_living": round(annual_food_living, 2),
        },
        "assumptions": assumptions,
    }
