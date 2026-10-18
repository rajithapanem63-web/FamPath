# Spec: Family Alignment & Mediator — Design

## Preference Dimensions (8 dimensions, each scored 1–5 by weight)

| Dimension | Student can set | Parent can set | Description |
|-----------|----------------|----------------|-------------|
| branch_interest | ✓ | ✓ | Importance of specific branch preference |
| location_flexibility | ✓ | ✓ | Willingness to study far from home |
| budget_priority | ✓ | ✓ | Importance of staying within budget |
| placement_focus | ✓ | ✓ | Priority of high placement % |
| higher_education | ✓ | ✓ | Likelihood/desire for postgraduate study |
| job_stability | ✓ | ✓ | Preference for stable government/PSU jobs |
| startup_openness | ✓ | ✓ | Openness to startup/entrepreneurship |
| prestige_weight | ✓ | ✓ | Importance of college reputation/ranking |

## Data Models

### `preference_submissions` table
```sql
id              UUID PK
workspace_id    UUID REFERENCES family_workspaces(id)
user_id         UUID REFERENCES users(id)
preferences     JSONB  -- {"branch_interest": 5, "location_flexibility": 2, ...}
submitted_at    TIMESTAMPTZ
updated_at      TIMESTAMPTZ
```

### `alignment_snapshots` table  (cached, recomputed on preference change)
```sql
id              UUID PK
workspace_id    UUID REFERENCES family_workspaces(id)
alignment_score NUMERIC(5,2)  -- 0–100
dimension_scores JSONB  -- {"branch_interest": {"agreement": true, "diff": 0.1}, ...}
computed_at     TIMESTAMPTZ
```

### `mediation_sessions` table
```sql
id              UUID PK
workspace_id    UUID REFERENCES family_workspaces(id)
conflict_dimension VARCHAR(50)
request_text    TEXT
response        JSONB  -- {student_summary, parent_summary, compromises, citations}
model_version   VARCHAR(50)
created_at      TIMESTAMPTZ
```

## Alignment Score Formula

```python
# Treat preferences as vectors
student_vec = [pref[d] for d in DIMENSIONS]
parent_vec  = [pref[d] for d in DIMENSIONS]

cosine_sim = dot(student_vec, parent_vec) / (norm(student_vec) * norm(parent_vec))
alignment_score = round(cosine_sim * 100, 1)  # 0–100

# Per-dimension agreement: abs difference ≤ 1 → agree, > 1 → conflict
```

## API Contract

```
POST /api/v1/alignment/preferences
Auth: Bearer (student | parent)
Body: { preferences: { branch_interest: 5, ... } }
200: PreferenceResponse

GET /api/v1/alignment/dashboard
Auth: Bearer (workspace member)
200: {
  student_preferences: {...},
  parent_preferences: [{user_id, name, preferences: {...}}],
  alignment_score: 72.5,
  dimension_scores: [{dimension, student_value, parent_avg, agreement, diff}],
  both_submitted: true
}

POST /api/v1/alignment/mediate
Auth: Bearer (workspace member)
Body: { conflict_dimension: "location_flexibility", additional_context: "..." }
200: {
  student_summary: "The student values...",
  parent_summary: "The parent prioritises...",
  compromises: ["...", "...", "..."],
  citations: [{ source, year, data_point }]
}
```

## Mediator AI Prompt Design

System prompt:
```
You are a neutral family counselling assistant helping a family choose an engineering college in India.
You do NOT take sides. You help both parties understand each other's perspective.
You MUST cite platform data for any factual claims.
You MUST respond in the language requested.
If you cannot verify a claim with platform data, say: "I don't have sufficient data to verify this."
Respond in JSON: { "student_summary": "...", "parent_summary": "...", "compromises": [...], "citations": [...] }
```

User prompt template:
```
Family context (do not reveal individual names):
- Student preference for {dimension}: {student_value}/5 — reasoning: {student_context}
- Parent preference for {dimension}: {parent_value}/5 — reasoning: {parent_context}
- Relevant data: {retrieved_chunks}

Generate a neutral mediation response.
```

## Test Strategy
- `test_alignment_service.py`: cosine similarity, dimension diff computation
- `test_alignment_endpoints.py`: preference submit, dashboard, mediation
- Mock LLM in tests; verify prompt structure does not leak PII
- Mediator response parser: verify citations field always present
