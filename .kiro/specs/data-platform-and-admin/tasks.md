# Spec: Data Platform & Admin — Tasks

### TASK-DATA-01: Core data models & migrations
- SQLAlchemy models: College, CollegeProgram, CutoffRecord, FeeStructure, PlacementStat, Scholarship, ImportJob, QuizQuestion
- Alembic migration: `20240901_003_create_data_tables`
- Tests: model instantiation, relationships

### TASK-DATA-02: CSV import service (generic)
- `backend/app/services/import_service.py`: generic CSV parser, row validator, upsert logic
- Pydantic row schemas for each dataset type
- Duplicate detection logic
- Unit tests: valid CSV, invalid rows, duplicate handling, oversized file

### TASK-DATA-03: Import Celery tasks
- `backend/app/workers/import_tasks.py`: async import tasks per dataset type
- Progress tracking in `import_jobs` table
- Error report generation (JSONB)
- Tests: task completion, partial failure, error report structure

### TASK-DATA-04: Admin college CRUD endpoints
- Full CRUD `/api/v1/admin/colleges/*`
- Admin RBAC enforcement
- Pagination, search (name, code, district), filter (state, type)
- Tests: CRUD happy path, non-admin blocked, filters work

### TASK-DATA-05: Admin import endpoints
- Upload endpoints for all 5 dataset types
- File validation (MIME type, size limit)
- `GET /api/v1/admin/import/{job_id}` polling endpoint
- Tests: upload, poll pending → completed, poll failed

### TASK-DATA-06: Freshness dashboard endpoint
- `GET /api/v1/admin/freshness` — aggregate last import date and unverified count per dataset
- Stale data flag (> 365 days)
- Tests: freshness calculation, stale detection

### TASK-DATA-07: Question bank endpoints
- CRUD `/api/v1/admin/questions/*`
- Translation completeness validation (all 3 locales required)
- Tests: create with all translations, missing translation blocked

### TASK-DATA-08: Synthetic seed data files
- Create all 6 seed CSV/JSON files
- `scripts/seed_db.py` — loads all seed files via import service
- Verification: seed script runs without errors, records show `verification_status = 'synthetic'`

### TASK-DATA-09: Frontend admin panel
- Admin dashboard with freshness cards
- College list table with search/filter/pagination
- CSV import wizard with job polling (SSE or polling interval)
- Question bank CRUD UI
- All strings i18n'd
