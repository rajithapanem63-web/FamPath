# Spec: Shortlist, Reports & Timeline — Design

## Data Models

### `shortlist_items` table
```sql
id              UUID PK
workspace_id    UUID REFERENCES family_workspaces(id)
college_id      UUID REFERENCES colleges(id)
program_id      UUID REFERENCES college_programs(id)
added_by        UUID REFERENCES users(id)
is_final_choice BOOLEAN DEFAULT false
cost_snapshot   JSONB  -- frozen at add time
prediction_snapshot JSONB  -- frozen at add time
created_at      TIMESTAMPTZ DEFAULT now()
removed_at      TIMESTAMPTZ
UNIQUE(workspace_id, college_id, program_id) WHERE removed_at IS NULL
```

### `shortlist_votes` table
```sql
id              UUID PK
shortlist_item_id UUID REFERENCES shortlist_items(id)
user_id         UUID REFERENCES users(id)
vote            SMALLINT  -- 1 (thumbs up) | -1 (thumbs down) | 0 (neutral)
comment         TEXT
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
UNIQUE(shortlist_item_id, user_id)
```

### `decision_log_entries` table
```sql
id              UUID PK
workspace_id    UUID REFERENCES family_workspaces(id)
user_id         UUID REFERENCES users(id)
action          VARCHAR(50)  -- added | removed | voted | commented | marked_final
resource_id     UUID
metadata        JSONB
created_at      TIMESTAMPTZ DEFAULT now()
```

### `counselling_events` table (seed data)
```sql
id              UUID PK
exam_type       VARCHAR(20)
event_name      VARCHAR(255)
event_name_te   VARCHAR(255)
event_name_hi   VARCHAR(255)
event_year      INT
event_date      DATE
round_number    INT
notes           TEXT
source          VARCHAR(255)
```

### `document_checklist_items` table (template)
```sql
id              UUID PK
exam_type       VARCHAR(20)
category_filter VARCHAR(20)  -- null = all, OC, BC, SC, ST
document_name   VARCHAR(255)
document_name_te VARCHAR(255)
document_name_hi VARCHAR(255)
description     TEXT
is_mandatory    BOOLEAN DEFAULT true
```

### `workspace_checklist_status` table
```sql
id              UUID PK
workspace_id    UUID REFERENCES family_workspaces(id)
checklist_item_id UUID REFERENCES document_checklist_items(id)
is_completed    BOOLEAN DEFAULT false
completed_by    UUID REFERENCES users(id)
completed_at    TIMESTAMPTZ
```

## API Contract

```
GET    /api/v1/shortlist/{workspace_id}
POST   /api/v1/shortlist/{workspace_id}         # add college
DELETE /api/v1/shortlist/{workspace_id}/{item_id}
POST   /api/v1/shortlist/{workspace_id}/{item_id}/vote
PUT    /api/v1/shortlist/{workspace_id}/{item_id}/final   # mark final decision

GET    /api/v1/shortlist/{workspace_id}/log     # decision history

GET    /api/v1/reports/{workspace_id}/pdf       # stream PDF download

GET    /api/v1/timeline/{workspace_id}          # counselling events for exam_type
GET    /api/v1/checklist/{workspace_id}         # doc checklist (filtered by category)
PUT    /api/v1/checklist/{workspace_id}/{item_id}  # mark complete
```

## PDF Report Generation

Technology: WeasyPrint (HTML → PDF)

Template: `backend/app/services/report_templates/decision_report_{locale}.html`

Sections:
1. Cover: family name, generated date, exam type
2. Student Profile: exam, rank (masked as "Rank: ****" in shared copy), category, gender
3. Aptitude Results: RIASEC bar chart (SVG embedded), top-3 branches
4. Top-5 Shortlisted Colleges: table with band, total cost, alignment score, votes
5. Family Alignment: alignment score, top-3 agreement/conflict dimensions
6. Final Decision: college/branch + family note
7. Disclaimers + Data Sources page

Generation flow: Celery task → render HTML → WeasyPrint → store temp file → stream to client → delete temp file.

## Notification System

- In-app: stored in `notifications` table, polled via `GET /api/v1/notifications`
- Email: Celery task `send_reminder_email` triggered by `counselling_events` scheduler (Celery Beat)

## Test Strategy
- `test_shortlist_service.py`: add, vote, mark final, limit enforcement
- `test_report_service.py`: PDF generated, non-empty, sections present
- `test_timeline_service.py`: correct events for exam type
- E2E Playwright: `report-download.spec.ts`
