# Spec: Family Alignment & Mediator — Tasks

### TASK-ALIGN-01: Preference & alignment models + migrations
- `PreferenceSubmission`, `AlignmentSnapshot`, `MediationSession` models
- Migration: `20240901_006_create_alignment_tables`

### TASK-ALIGN-02: Alignment score service
- `compute_alignment_score()` and `compute_dimension_scores()` pure functions
- Unit tests: known vectors → expected scores

### TASK-ALIGN-03: Alignment API endpoints
- Submit/update preferences, dashboard endpoint, recompute snapshot on change
- Tests: both submitted, one submitted, score updates on preference change

### TASK-ALIGN-04: Conflict Mediator AI service
- RAG-grounded mediator in `backend/app/services/mediator_service.py`
- Retrieve relevant platform data (placements, cutoffs) for the conflict dimension
- Build prompt (no PII in LLM call), call LLM, parse response, validate citations
- Mocked in unit tests; integration test with mock LLM transport

### TASK-ALIGN-05: Mediation API endpoint
- `POST /api/v1/alignment/mediate`
- Citation validation (reject response if citations empty)
- Neutral language check (log if "blame" words detected)
- Tests: happy path (mocked LLM), citation missing → error, LLM timeout → 503

### TASK-FE-ALIGN-01: Family Alignment Dashboard UI
- Side-by-side radar chart (Recharts) for student vs parent preferences
- Dimension cards with agreement/conflict colour indicator
- Family Alignment Score gauge
- "Request AI Mediation" button per conflict dimension
- Mediator response modal with citations
- i18n all strings
