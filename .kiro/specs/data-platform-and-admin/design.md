# Spec: Data Platform & Admin — Design

## Core Data Models

### `colleges` table
```sql
id              UUID PK
college_code    VARCHAR(20) UNIQUE NOT NULL  -- official EAPCET/JEE code
name            VARCHAR(255) NOT NULL
name_te         VARCHAR(255)  -- Telugu name
name_hi         VARCHAR(255)
state           VARCHAR(50)
district        VARCHAR(100)
city            VARCHAR(100)
college_type    VARCHAR(20)  -- government | private_aided | private_unaided | deemed | central
affiliation     VARCHAR(255)
naac_grade      VARCHAR(5)
nba_programs    JSONB  -- ["CSE","ECE"]
website         TEXT
established_year INT
is_active       BOOLEAN DEFAULT true
source          VARCHAR(255)
source_year     INT
import_date     TIMESTAMPTZ
imported_by     UUID REFERENCES users(id)
verification_status VARCHAR(20) DEFAULT 'unverified'
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

### `college_programs` table
```sql
id              UUID PK
college_id      UUID REFERENCES colleges(id)
branch_code     VARCHAR(20)  -- standardised code e.g. CSE, ECE, MECH
branch_name     VARCHAR(255)
branch_name_te  VARCHAR(255)
branch_name_hi  VARCHAR(255)
intake_seats    INT
duration_years  INT DEFAULT 4
is_active       BOOLEAN DEFAULT true
```

### `cutoff_records` table
```sql
id              UUID PK
college_id      UUID REFERENCES colleges(id)
program_id      UUID REFERENCES college_programs(id)
exam_type       VARCHAR(20)  -- AP_EAPCET | TS_EAPCET | JEE_MAINS
counselling_year INT NOT NULL
round           INT  -- 1 | 2 | 3 | spot
category        VARCHAR(20)
gender          VARCHAR(10)  -- any | male | female
opening_rank    INT
closing_rank    INT
source          VARCHAR(255)
source_year     INT
import_date     TIMESTAMPTZ
imported_by     UUID REFERENCES users(id)
verification_status VARCHAR(20) DEFAULT 'unverified'
INDEX (college_id, counselling_year, category, exam_type)
```

### `fee_structures` table
```sql
id              UUID PK
college_id      UUID REFERENCES colleges(id)
program_id      UUID REFERENCES college_programs(id)
academic_year   INT NOT NULL
tuition_fee     NUMERIC(12,2)
hostel_fee      NUMERIC(12,2)
transport_fee   NUMERIC(12,2)
other_fees      NUMERIC(12,2)
total_annual_fee NUMERIC(12,2) GENERATED ALWAYS AS (tuition_fee+hostel_fee+transport_fee+other_fees) STORED
source          VARCHAR(255)
source_year     INT
import_date     TIMESTAMPTZ
imported_by     UUID REFERENCES users(id)
verification_status VARCHAR(20) DEFAULT 'unverified'
```

### `placement_stats` table
```sql
id              UUID PK
college_id      UUID REFERENCES colleges(id)
program_id      UUID REFERENCES college_programs(id)
placement_year  INT NOT NULL
placed_percent  NUMERIC(5,2)
avg_package_lpa NUMERIC(8,2)
median_package_lpa NUMERIC(8,2)
highest_package_lpa NUMERIC(8,2)
top_recruiters  JSONB
source          VARCHAR(255)
source_year     INT
import_date     TIMESTAMPTZ
imported_by     UUID REFERENCES users(id)
verification_status VARCHAR(20) DEFAULT 'unverified'
```

### `scholarships` table
```sql
id              UUID PK
name            VARCHAR(255)
name_te         VARCHAR(255)
name_hi         VARCHAR(255)
provider        VARCHAR(255)
eligible_categories JSONB  -- ["SC","ST","EWS"]
income_ceiling  NUMERIC(12,2)
amount_per_year NUMERIC(12,2)
covers_hostel   BOOLEAN
application_url TEXT
deadline_notes  TEXT
source          VARCHAR(255)
source_year     INT
import_date     TIMESTAMPTZ
imported_by     UUID REFERENCES users(id)
verification_status VARCHAR(20) DEFAULT 'unverified'
is_active       BOOLEAN DEFAULT true
```

### `quiz_questions` table
```sql
id              UUID PK
question_text   TEXT NOT NULL  -- English
question_te     TEXT
question_hi     TEXT
riasec_dimension VARCHAR(10)  -- R | I | A | S | E | C
weight          NUMERIC(4,2) DEFAULT 1.0
options         JSONB  -- [{"value":1,"label_en":"Strongly Disagree","label_te":"...","label_hi":"..."}]
is_active       BOOLEAN DEFAULT true
created_by      UUID REFERENCES users(id)
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

### `import_jobs` table
```sql
id              UUID PK
admin_id        UUID REFERENCES users(id)
dataset_type    VARCHAR(30)  -- colleges | cutoffs | fees | placements | scholarships
filename        VARCHAR(255)
file_hash       VARCHAR(64)
status          VARCHAR(20)  -- pending | processing | completed | failed
total_rows      INT
imported_rows   INT
skipped_rows    INT
error_rows      INT
error_report    JSONB  -- [{row: 5, error: "missing college_code"}]
started_at      TIMESTAMPTZ
completed_at    TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT now()
```

## CSV Import Architecture

```
Admin Upload → /api/v1/admin/import/{dataset_type}
    │
    ▼
File validation (MIME, size < 10MB)
    │
    ▼
Celery task: parse CSV → validate rows → upsert records → update import_job
    │
    ▼ async result
Admin polls GET /api/v1/admin/import/{job_id} for status
```

### CSV Schema Definitions (pydantic models used for row validation)
Each dataset type has a Pydantic model in `backend/app/schemas/import_schemas.py`.

## Admin API Endpoints

```
GET    /api/v1/admin/colleges                    # list with filters
POST   /api/v1/admin/colleges                    # create
GET    /api/v1/admin/colleges/{id}               # detail
PUT    /api/v1/admin/colleges/{id}               # update
DELETE /api/v1/admin/colleges/{id}               # soft-delete

POST   /api/v1/admin/import/colleges             # CSV upload
POST   /api/v1/admin/import/cutoffs              # CSV upload
POST   /api/v1/admin/import/fees                 # CSV upload
POST   /api/v1/admin/import/placements           # CSV upload
POST   /api/v1/admin/import/scholarships         # CSV upload
GET    /api/v1/admin/import/{job_id}             # poll status

GET    /api/v1/admin/freshness                   # data freshness dashboard

GET    /api/v1/admin/questions                   # list questions
POST   /api/v1/admin/questions                   # create
PUT    /api/v1/admin/questions/{id}              # update
DELETE /api/v1/admin/questions/{id}              # deactivate
```

## Frontend Admin Panel

- Route: `/(admin)/dashboard` — freshness summary cards
- Route: `/(admin)/colleges` — searchable/filterable table, inline edit, CSV import button
- Route: `/(admin)/import` — upload wizard with real-time job status polling
- Route: `/(admin)/questions` — question bank CRUD with preview

## Seed Data Strategy

Synthetic seed files in `backend/seed_data/`:
- `colleges_seed.csv` — 50 fictional colleges with `source = "SEED_SYNTHETIC"`
- `cutoffs_seed.csv` — 3 years of fictional cutoffs (2022–2024)
- `fees_seed.csv` — fee structures for all seed colleges
- `placements_seed.csv` — placement stats for seed colleges
- `scholarships_seed.csv` — 10 fictional scholarships
- `questions_seed.json` — 20 RIASEC questions

All seed records have `verification_status = 'synthetic'` to distinguish from real data.
