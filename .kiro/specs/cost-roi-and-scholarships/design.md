# Spec: Cost, ROI & Scholarships — Design

## API Contract

```
GET /api/v1/cost/{college_id}/{program_id}
Auth: Bearer
Response: {
  college_id, program_id,
  annual_fee_breakdown: { tuition, hostel, transport, other },
  total_4yr_cost: 600000,
  data_year: 2024,
  data_source: "college fee circular 2024",
  disclaimer: "Estimate only. Fees may change.",
  fee_data_note: null | "fee data from 2023, may have changed"
}

GET /api/v1/cost/scholarships
Auth: Bearer
Query: category, income_range (optional — falls back to profile)
Response: [{
  id, name, provider, amount_per_year, covers_hostel,
  eligibility_note, application_url, income_ceiling,
  data_source, data_year
}]

GET /api/v1/cost/roi/{college_id}/{program_id}
Auth: Bearer
Response: {
  median_placement_lpa,
  placement_year,
  placement_source,
  loan_scenarios: [{
    loan_amount, interest_rate_pct, tenure_months,
    monthly_emi, payback_months_at_30pct_salary
  }]
}
```

## EMI Formula (computed server-side for consistency)
```python
def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    r = annual_rate / 12 / 100
    return principal * r * (1+r)**tenure_months / ((1+r)**tenure_months - 1)

def payback_months(loan: float, monthly_salary: float, repayment_ratio: float = 0.30) -> float:
    return loan / (monthly_salary * repayment_ratio)
```

## Models (no new tables — uses existing fee_structures, placement_stats, scholarships)

A `CostSnapshot` is computed on-demand (not persisted) unless saved to shortlist.

## Shortlist Integration
When a college is added to shortlist, its cost snapshot is stored as JSONB in the shortlist item (so historical cost data is preserved even if fee data changes).

## Test Strategy
- `test_cost_service.py`: EMI formula, payback formula, scholarship eligibility filter
- `test_cost_endpoints.py`: missing fee data fallback, scholarship filter by category
- Frontend: calculator inputs produce correct EMI (Vitest)
