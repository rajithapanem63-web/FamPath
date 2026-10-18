# Spec: Cost, ROI & Scholarships — Requirements

## Overview
4-year total cost estimation, scholarship matching, EMI calculation, and payback period vs placement data to help families make financially informed decisions.

## User Stories
- US-COST-01: As a family, I can see the 4-year total cost (tuition + hostel + transport + books) for any college/branch.
- US-COST-02: As a family, I can see which scholarships I am eligible for based on category and income.
- US-COST-03: As a family, I can see the net cost after applying eligible scholarships.
- US-COST-04: As a family, I can model an education loan with EMI calculation and payback period.
- US-COST-05: As a family, I can see a ROI comparison: loan payback period vs median placement salary.
- US-COST-06: As a family, I can filter my college shortlist to only show colleges within budget.
- US-COST-07: Every cost figure shows its data source, data year, and the disclaimer "Estimate only."

## Acceptance Criteria

### Cost Calculation
- WHEN a college/branch is selected, THEN total 4-year cost = sum of annual fees × 4, with hostel and transport as optional add-ons.
- WHEN fee data is missing for any year, THEN the most recent available year's fee is used and a note "fee data from {year}, may have changed" is shown.
- WHEN a family sets a budget, THEN the budget-safe filter hides colleges with total 4-year cost > budget.

### Scholarship Matching
- WHEN a student's profile has category and income_range set, THEN eligible scholarships are shown filtered by those criteria.
- WHEN scholarship data is missing income ceiling, THEN the scholarship is shown with a note "income eligibility unknown."

### EMI & Payback
- WHEN a loan amount, interest rate, and tenure are entered, THEN monthly EMI = [P × r × (1+r)^n] / [(1+r)^n - 1] is computed client-side.
- WHEN median placement salary is available, THEN payback period (months) = loan_amount / (monthly_salary × repayment_ratio) is shown.
- Default repayment_ratio = 0.30 (30 % of salary towards loan), configurable by user.
