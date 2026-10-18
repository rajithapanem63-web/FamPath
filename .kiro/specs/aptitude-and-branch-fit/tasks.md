# Spec: Aptitude & Branch Fit — Tasks

### TASK-APT-01: Quiz session & result models + migrations
- `QuizSession`, `QuizResponse`, `AptitudeResult` SQLAlchemy models
- Migration: `20240901_005_create_aptitude_tables`

### TASK-APT-02: RIASEC scoring service
- `compute_riasec_scores()` and `compute_branch_fit()` pure functions
- Branch weight config (JSONB or constants file)
- Unit tests: full coverage with synthetic responses

### TASK-APT-03: Quiz API endpoints
- Start session (randomised question order, fixed seed)
- Save responses (partial)
- Submit and get results
- History and latest endpoints
- Auth + parent read-only access
- Tests: full flow, resume partial, parent access, retake stores both results

### TASK-FE-APT-01: Quiz UI
- Step-by-step question cards with Likert scale (1–5)
- Progress bar
- Resume banner if session in_progress
- Results page: RIASEC radar chart (Recharts) + branch fit bar chart + explanation chips
- Parent view: read-only results in workspace
- i18n all strings
