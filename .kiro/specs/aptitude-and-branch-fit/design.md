# Spec: Aptitude & Branch Fit — Design

## RIASEC → Branch Mapping

Each engineering branch maps to primary and secondary RIASEC dimensions:

| Branch | Primary | Secondary | Tertiary |
|--------|---------|-----------|---------|
| CSE / IT | I | C | — |
| ECE / EEE | I | R | — |
| Mechanical | R | I | — |
| Civil | R | C | — |
| Chemical | I | R | — |
| Biotechnology | I | A | S |
| MBA/Management track | E | S | C |
| Architecture | A | R | I |

Branch Fit Score formula:
```
score = (primary_weight * riasec[primary] + secondary_weight * riasec[secondary]) / (primary_weight + secondary_weight)
primary_weight = 0.6, secondary_weight = 0.4 (configurable)
Normalized to 0–100.
```

## Data Models

### `quiz_sessions` table
```sql
id              UUID PK
student_id      UUID REFERENCES users(id)
workspace_id    UUID REFERENCES family_workspaces(id)
status          VARCHAR(20)  -- in_progress | completed
question_order  JSONB  -- [uuid, uuid, ...] randomised order
started_at      TIMESTAMPTZ
completed_at    TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT now()
```

### `quiz_responses` table
```sql
id              UUID PK
session_id      UUID REFERENCES quiz_sessions(id)
question_id     UUID REFERENCES quiz_questions(id)
response_value  SMALLINT  -- 1–5 Likert scale
answered_at     TIMESTAMPTZ
```

### `aptitude_results` table
```sql
id              UUID PK
student_id      UUID REFERENCES users(id)
workspace_id    UUID REFERENCES family_workspaces(id)
session_id      UUID REFERENCES quiz_sessions(id)
riasec_scores   JSONB  -- {"R":72,"I":88,"A":45,"S":60,"E:50","C":70}
branch_fit_scores JSONB -- {"CSE":91,"ECE":85,"MECH":60,...}
top_branches    JSONB  -- [{"branch":"CSE","score":91,"drivers":["I","C"]}]
created_at      TIMESTAMPTZ DEFAULT now()
```

## API Contract

```
GET /api/v1/aptitude/questions
Auth: Bearer (student)
Response: { session_id, questions: [{ id, text, options, riasec_dimension }] }

POST /api/v1/aptitude/sessions/{session_id}/responses
Auth: Bearer (student)
Body: { responses: [{ question_id, value }] }
200: { saved: true, progress: { answered: 10, total: 20 } }

POST /api/v1/aptitude/sessions/{session_id}/submit
Auth: Bearer (student)
200: AptitudeResultResponse

GET /api/v1/aptitude/results
Auth: Bearer (student)
200: [AptitudeResultResponse]  -- history, latest first

GET /api/v1/aptitude/results/latest
Auth: Bearer (student | parent via workspace)
200: AptitudeResultResponse
```

## Scoring Service
`backend/app/services/aptitude_service.py`
```python
def compute_riasec_scores(responses: list[QuizResponse], questions: list[QuizQuestion]) -> dict[str, float]
def compute_branch_fit(riasec: dict, branch_weights: dict) -> dict[str, BranchFitResult]
```
Both functions are pure (no I/O), deterministic, and fully unit-testable.

## Test Strategy
- `test_aptitude_service.py`: known responses → expected RIASEC scores → expected branch fit scores
- `test_aptitude_endpoints.py`: start session, save responses, submit, get results
- Parent access: can read latest result, cannot read individual responses
