# Spec: Shortlist, Reports & Timeline — Tasks

### TASK-SHORT-01: Shortlist & vote models + migrations
- All 6 models above
- Migration: `20240901_008_create_shortlist_timeline_tables`

### TASK-SHORT-02: Shortlist API endpoints
- CRUD + vote + mark final + decision log
- Limit enforcement (20 items)
- Snapshot frozen on add
- Tests: full CRUD, vote, limit, final decision

### TASK-SHORT-03: PDF report generation
- WeasyPrint HTML templates (en/te/hi)
- Celery task for generation
- PDF stream endpoint
- Tests: PDF generated, non-empty, disclaimer present

### TASK-SHORT-04: Timeline & checklist endpoints
- Seed counselling events (AP EAPCET 2024 synthetic)
- Seed document checklist (OC/BC/SC/ST variants)
- Timeline API, checklist API, mark-complete endpoint
- Tests: events returned for exam type, category filter, completion persisted

### TASK-SHORT-05: Notification infrastructure
- `notifications` table + in-app poll endpoint
- Celery Beat task for email reminders
- Tests: notification created on deadline approach

### TASK-FE-SHORT-01: Shortlist & decision log UI
- Shortlist panel with vote buttons, comments, remove
- Decision log timeline view
- Final decision badge
- i18n all strings

### TASK-FE-SHORT-02: PDF download button + report preview
- Download button → trigger Celery job → poll → download
- Loading state with progress indicator

### TASK-FE-SHORT-03: Counselling timeline & checklist UI
- Timeline with days-remaining countdown
- Checklist with checkbox per document, category-filtered
- Completed items strike-through
- i18n all strings
