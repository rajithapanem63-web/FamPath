# Spec: Cost, ROI & Scholarships — Tasks

### TASK-COST-01: Cost calculation service
- `backend/app/services/cost_service.py`: fee aggregation, missing data fallback, note generation
- EMI and payback period functions
- Unit tests: full coverage including edge cases

### TASK-COST-02: Cost and ROI API endpoints
- `GET /api/v1/cost/{college_id}/{program_id}`
- `GET /api/v1/cost/scholarships`
- `GET /api/v1/cost/roi/{college_id}/{program_id}`
- Auth, disclaimer enforcement
- Tests: happy path, missing fee data, scholarship filter

### TASK-FE-COST-01: Cost calculator UI
- College cost card with annual/4-year breakdown
- Scholarship panel (filtered list with eligibility notes)
- EMI calculator inputs (loan amount, rate, tenure slider)
- ROI comparison chart: payback months vs placement trend
- Budget filter toggle (hides over-budget colleges in predictor results)
- Data source badge + disclaimer on every figure
- i18n all strings
