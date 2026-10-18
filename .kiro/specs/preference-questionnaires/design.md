# Design: Preference Questionnaires

**Spec ID:** preference-questionnaires  
**Status:** Draft  
**Version:** 1.0  
**Last Updated:** 2024-10-18

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     FamPath Platform                         │
│                                                              │
│  ┌──────────────┐      ┌─────────────────┐                 │
│  │   Frontend   │─────▶│   API Gateway    │                 │
│  │   (Next.js)  │◀─────│   (FastAPI)      │                 │
│  └──────────────┘      └─────────────────┘                 │
│         │                       │                            │
│         │                       ▼                            │
│         │              ┌──────────────────┐                 │
│         │              │ Preference Router│                 │
│         │              └──────────────────┘                 │
│         │                       │                            │
│         │                       ▼                            │
│         │              ┌──────────────────┐                 │
│         │              │Preference Service│                 │
│         │              └──────────────────┘                 │
│         │                       │                            │
│         │                       ▼                            │
│         │              ┌──────────────────┐                 │
│         │              │   PostgreSQL     │                 │
│         │              │  (preferences)   │                 │
│         │              └──────────────────┘                 │
│         │                                                    │
│         └──────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **Frontend Form** | Render questionnaire, validate input, submit responses |
| **Preference Router** | HTTP endpoint handling, auth validation |
| **Preference Service** | Business logic, versioning, aggregation |
| **Database** | Persist responses with history |

---

## Data Model Design

### Database Schema

#### Table: `preference_responses`

```sql
CREATE TABLE preference_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES family_workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dimension VARCHAR(50) NOT NULL,
    weight INTEGER NOT NULL CHECK (weight IN (3, 6, 9)), -- Low, Medium, High
    selected_options JSONB NOT NULL,
    additional_data JSONB,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    CONSTRAINT unique_active_preference 
        UNIQUE (workspace_id, user_id, dimension, version),
    
    CONSTRAINT valid_dimension CHECK (
        dimension IN (
            ''branch_preference'',
            ''location_preference'',
            ''college_type_preference'',
            ''budget_constraint'',
            ''placement_importance'',
            ''campus_facilities'',
            ''reputation_ranking'',
            ''career_goal''
        )
    )
);

CREATE INDEX idx_pref_workspace_user ON preference_responses(workspace_id, user_id);
CREATE INDEX idx_pref_active ON preference_responses(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_pref_dimension ON preference_responses(dimension);
```

#### Dimension Enum (Python)

```python
class PreferenceDimension(str, Enum):
    BRANCH = "branch_preference"
    LOCATION = "location_preference"
    COLLEGE_TYPE = "college_type_preference"
    BUDGET = "budget_constraint"
    PLACEMENT = "placement_importance"
    FACILITIES = "campus_facilities"
    REPUTATION = "reputation_ranking"
    CAREER_GOAL = "career_goal"
```

#### Weight Enum (Python)

```python
class PreferenceWeight(int, Enum):
    LOW = 3
    MEDIUM = 6
    HIGH = 9
```

### Sample Data

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "...",
  "user_id": "...",
  "dimension": "branch_preference",
  "weight": 9,
  "selected_options": ["CSE", "IT", "AI_ML"],
  "additional_data": null,
  "submitted_at": "2024-10-18T10:30:00Z",
  "updated_at": "2024-10-18T10:30:00Z",
  "version": 1,
  "is_active": true
}
```

---

## API Design

### Endpoint: Submit/Update Preferences

**POST /api/v1/preferences**

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "workspace_id": "uuid",
  "responses": [
    {
      "dimension": "branch_preference",
      "weight": "HIGH",
      "selected_options": ["CSE", "IT"],
      "additional_data": null
    },
    {
      "dimension": "budget_constraint",
      "weight": "MEDIUM",
      "selected_options": ["₹1,00,000 - ₹2,00,000/year"],
      "additional_data": null
    }
  ]
}
```

**Validation Rules:**
- `workspace_id` must exist and user must be a member
- `dimension` must be valid enum value
- `weight` must be LOW, MEDIUM, or HIGH
- `selected_options` must not be empty array
- Max 8 responses per request (one per dimension)

**Response (201 Created):**
```json
{
  "submission_id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "submitted_at": "2024-10-18T10:30:00Z",
  "dimensions_submitted": 2,
  "completion_percentage": 25.0
}
```

**Error Responses:**

| Code | Scenario | Response |
|------|----------|----------|
| 401 | Not authenticated | `{"error_code": "UNAUTHORIZED"}` |
| 403 | Not workspace member | `{"error_code": "FORBIDDEN", "message": "Not a member of this workspace"}` |
| 422 | Invalid dimension | `{"error_code": "INVALID_DIMENSION", "message": "Unknown dimension: xyz"}` |
| 422 | Empty options | `{"error_code": "EMPTY_OPTIONS", "message": "At least one option required"}` |

---

### Endpoint: Get Own Preferences

**GET /api/v1/preferences/me?workspace_id={uuid}**

**Response (200 OK):**
```json
{
  "user_id": "uuid",
  "workspace_id": "uuid",
  "full_name": "Rajitha Panem",
  "role": "student",
  "responses": [
    {
      "dimension": "branch_preference",
      "dimension_label": "Branch Preference",
      "weight": "HIGH",
      "weight_numeric": 9,
      "selected_options": ["CSE", "IT"],
      "submitted_at": "2024-10-18T10:30:00Z",
      "updated_at": "2024-10-18T10:30:00Z"
    }
  ],
  "completion_percentage": 25.0,
  "completed_dimensions": 2,
  "total_dimensions": 8,
  "last_updated": "2024-10-18T10:30:00Z"
}
```

---

### Endpoint: Get Family Preferences Summary

**GET /api/v1/preferences/family?workspace_id={uuid}**

**Purpose:** Show which family members have completed the questionnaire (for dashboard)

**Response (200 OK):**
```json
{
  "workspace_id": "uuid",
  "workspace_name": "Rajitha''s Family",
  "members": [
    {
      "user_id": "uuid",
      "full_name": "Rajitha Panem",
      "role": "student",
      "completion_percentage": 100.0,
      "completed_dimensions": 8,
      "last_updated": "2024-10-18T10:30:00Z",
      "has_completed": true
    },
    {
      "user_id": "uuid",
      "full_name": "Parent Name",
      "role": "parent",
      "completion_percentage": 50.0,
      "completed_dimensions": 4,
      "last_updated": "2024-10-18T11:00:00Z",
      "has_completed": false
    }
  ],
  "family_completion_rate": 75.0
}
```

**Note:** This endpoint does NOT return individual preference details, only completion status.

---

### Endpoint: Update Single Dimension

**PUT /api/v1/preferences/{dimension}**

**Request Body:**
```json
{
  "workspace_id": "uuid",
  "weight": "HIGH",
  "selected_options": ["ECE", "EEE"],
  "additional_data": null
}
```

**Logic:**
1. Mark current active response for this dimension as `is_active=false`
2. Create new row with `version = previous_version + 1`, `is_active=true`
3. Preserve history

**Response (200 OK):**
```json
{
  "dimension": "branch_preference",
  "updated_at": "2024-10-18T12:00:00Z",
  "version": 2
}
```

---

## Business Logic

### Service: PreferenceService

**File:** `backend/app/services/preference_service.py`

**Methods:**

#### 1. `submit_preferences()`
```python
async def submit_preferences(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    responses: List[PreferenceResponseInput]
) -> PreferenceSubmissionResult:
    """
    Submit multiple preference responses.
    
    Logic:
    1. Validate workspace membership
    2. For each response:
       - Check if dimension already exists
       - If exists: create new version, mark old as inactive
       - If new: create with version=1
    3. Calculate completion percentage
    4. Return summary
    """
```

#### 2. `get_user_preferences()`
```python
async def get_user_preferences(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID
) -> UserPreferencesResponse:
    """
    Get active preferences for a specific user.
    
    Logic:
    1. Query all active responses for user in workspace
    2. Calculate completion %
    3. Return with metadata
    """
```

#### 3. `get_family_preferences_summary()`
```python
async def get_family_preferences_summary(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    requester_id: uuid.UUID
) -> FamilyPreferencesSummary:
    """
    Get completion status for all family members.
    
    Logic:
    1. Verify requester is workspace member
    2. Get all members
    3. For each member, count completed dimensions
    4. Return summary (no detailed preferences)
    """
```

#### 4. `update_dimension()`
```python
async def update_dimension(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    dimension: PreferenceDimension,
    weight: PreferenceWeight,
    selected_options: List[str],
    additional_data: Optional[Dict]
) -> PreferenceResponse:
    """
    Update a single dimension.
    
    Logic:
    1. Mark current active as inactive
    2. Create new version
    3. Return updated response
    """
```

---

## Frontend Design

### Component Structure

```
src/app/[locale]/(workspace)/preferences/
├── page.tsx                    # Main questionnaire page
├── components/
│   ├── PreferenceForm.tsx      # Form wrapper
│   ├── DimensionCard.tsx       # Single dimension UI
│   ├── WeightSelector.tsx      # Low/Medium/High buttons
│   ├── OptionSelector.tsx      # Checkboxes/radio for options
│   ├── ProgressBar.tsx         # Completion indicator
│   └── SubmitButton.tsx        # Save button with loading state
└── hooks/
    └── usePreferences.ts       # React Query hooks
```

### Page Layout (Mobile-First)

```
┌────────────────────────────────┐
│  Your Preferences              │ ← Header
│  ──────────────────────────    │
│  [■■■■■■□□] 75% Complete       │ ← Progress bar
├────────────────────────────────┤
│  ┌──────────────────────────┐ │
│  │ 🎓 Branch Preference     │ │ ← Dimension 1
│  │                          │ │
│  │ How important?           │ │
│  │ [ Low ] [Medium] [High]  │ │ ← Weight buttons
│  │                          │ │
│  │ Select branches:         │ │
│  │ ☑ CSE  ☑ IT  ☐ ECE      │ │ ← Options
│  └──────────────────────────┘ │
│                                │
│  ┌──────────────────────────┐ │
│  │ 📍 Location Preference   │ │ ← Dimension 2
│  │ ...                      │ │
│  └──────────────────────────┘ │
│                                │
│  [Save Progress]  [Submit All] │ ← Actions
└────────────────────────────────┘
```

### State Management

**Using React Query + Zustand:**

```typescript
// hooks/usePreferences.ts
export function useSubmitPreferences() {
  return useMutation({
    mutationFn: (data: PreferenceSubmission) => 
      post(''/api/v1/preferences'', data),
    onSuccess: () => {
      queryClient.invalidateQueries([''preferences'']);
      toast.success(''Preferences saved!'');
    }
  });
}

export function useUserPreferences(workspaceId: string) {
  return useQuery({
    queryKey: [''preferences'', ''me'', workspaceId],
    queryFn: () => get(`/api/v1/preferences/me?workspace_id=${workspaceId}`)
  });
}
```

### Validation (Client-Side)

**Using Zod:**

```typescript
const PreferenceResponseSchema = z.object({
  dimension: z.enum([
    ''branch_preference'',
    ''location_preference'',
    // ... all dimensions
  ]),
  weight: z.enum([''LOW'', ''MEDIUM'', ''HIGH'']),
  selected_options: z.array(z.string()).min(1, ''At least one option required''),
  additional_data: z.record(z.any()).optional()
});

const PreferenceSubmissionSchema = z.object({
  workspace_id: z.string().uuid(),
  responses: z.array(PreferenceResponseSchema).max(8)
});
```

---

## Security Design

### Authentication & Authorization

| Endpoint | Required Role | Additional Checks |
|----------|--------------|-------------------|
| POST /preferences | student, parent | Must be workspace member |
| GET /preferences/me | student, parent | Can only view own |
| GET /preferences/family | student, parent, counsellor | Must be workspace member |
| PUT /preferences/{dim} | student, parent | Can only edit own |

### Data Access Rules

```python
async def verify_workspace_membership(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID
) -> bool:
    """
    Check if user is member of workspace.
    Raises 403 if not member.
    """
```

### Rate Limiting

- **POST /preferences:** 10 requests / 5 minutes per user
- **GET endpoints:** 100 requests / 5 minutes per user

### Input Sanitization

- All string inputs stripped and truncated (max 500 chars per option)
- JSONB fields validated against schema
- No HTML allowed in text fields

---

## Error Handling

### Service-Level Exceptions

```python
class PreferenceError(Exception):
    """Base exception for preference operations"""

class InvalidDimensionError(PreferenceError):
    """Unknown dimension provided"""

class InvalidWeightError(PreferenceError):
    """Weight not in LOW, MEDIUM, HIGH"""

class WorkspaceMembershipError(PreferenceError):
    """User not member of workspace"""

class EmptyOptionsError(PreferenceError):
    """No options selected for dimension"""
```

### Error Mapping (FastAPI)

```python
@router.post("/preferences")
async def submit_preferences(...):
    try:
        result = await service.submit_preferences(...)
        return result
    except WorkspaceMembershipError:
        raise HTTPException(403, detail={"error_code": "NOT_WORKSPACE_MEMBER"})
    except InvalidDimensionError as e:
        raise HTTPException(422, detail={"error_code": "INVALID_DIMENSION", "message": str(e)})
    except EmptyOptionsError:
        raise HTTPException(422, detail={"error_code": "EMPTY_OPTIONS"})
```

---

## Testing Strategy

### Unit Tests (pytest)

**File:** `backend/tests/unit/test_preference_service.py`

**Test Cases:**
1. `test_submit_preferences_success()` - Happy path
2. `test_submit_preferences_invalid_dimension()` - Validation failure
3. `test_submit_preferences_not_workspace_member()` - Authorization failure
4. `test_update_dimension_creates_new_version()` - Versioning logic
5. `test_get_user_preferences_returns_active_only()` - Filtering
6. `test_calculate_completion_percentage()` - Math correctness

**Mocking:**
- Mock database session
- Mock workspace membership check
- Use factory_boy for test data

### Integration Tests

**File:** `backend/tests/integration/test_preference_endpoints.py`

**Test Cases:**
1. `test_submit_preferences_e2e()` - Full flow with real DB
2. `test_get_preferences_authenticated()` - Auth required
3. `test_get_preferences_unauthenticated_returns_401()` - Security
4. `test_update_dimension_preserves_history()` - Versioning with DB
5. `test_family_summary_excludes_other_workspaces()` - Isolation

### Frontend Tests (Vitest + Testing Library)

**File:** `frontend/tests/unit/PreferenceForm.test.tsx`

**Test Cases:**
1. `test_renders_all_8_dimensions()` - UI completeness
2. `test_weight_button_toggle()` - Interaction
3. `test_form_validation_requires_options()` - Client validation
4. `test_submit_shows_loading_state()` - UX feedback
5. `test_shows_error_toast_on_failure()` - Error handling

### E2E Tests (Playwright)

**File:** `frontend/tests/e2e/preference-questionnaire.spec.ts`

**Scenarios:**
1. Student completes full questionnaire → Sees 100% complete
2. Parent updates single dimension → Version increments
3. Student views family summary → Sees parent's completion %

---

## Performance Considerations

### Query Optimization

**Get User Preferences (Single Query):**
```sql
SELECT *
FROM preference_responses
WHERE workspace_id = ? 
  AND user_id = ? 
  AND is_active = TRUE
ORDER BY dimension;
```

**Index:** `idx_pref_workspace_user` (compound index on workspace_id, user_id)

### Caching Strategy

- **User preferences:** Cache for 5 minutes (low churn)
- **Family summary:** Cache for 2 minutes
- Invalidate on any preference update

**Redis Key Pattern:**
```
pref:user:{workspace_id}:{user_id}
pref:family:{workspace_id}:summary
```

### Response Payload Size

- Average response: ~2 KB (8 dimensions × ~250 bytes)
- Gzip compression: ~500 bytes
- No pagination needed (max 8 items per user)

---

## Observability

### Metrics (Prometheus)

```python
preference_submissions_total = Counter(
    ''preference_submissions_total'',
    ''Total number of preference submissions'',
    [''workspace_id'', ''user_role'']
)

preference_completion_rate = Histogram(
    ''preference_completion_rate'',
    ''Distribution of completion percentages'',
    buckets=[0, 25, 50, 75, 100]
)

preference_update_latency = Histogram(
    ''preference_update_latency_seconds'',
    ''Time to update a single dimension''
)
```

### Structured Logging

```python
logger.info(
    "preference_submitted",
    workspace_id=str(workspace_id),
    user_id=str(user_id),
    dimensions_count=len(responses),
    completion_percentage=result.completion_percentage
)
```

### Alerts

- If completion rate < 50% after 7 days → Send reminder emails
- If API error rate > 5% → Page on-call engineer

---

## Migration Plan

### Alembic Migration

**File:** `backend/alembic/versions/YYYYMMDD_add_preference_responses.py`

```python
def upgrade():
    op.create_table(
        ''preference_responses'',
        sa.Column(''id'', postgresql.UUID(), nullable=False),
        sa.Column(''workspace_id'', postgresql.UUID(), nullable=False),
        sa.Column(''user_id'', postgresql.UUID(), nullable=False),
        # ... rest of columns
        sa.ForeignKeyConstraint([''workspace_id''], [''family_workspaces.id''], ondelete=''CASCADE''),
        sa.ForeignKeyConstraint([''user_id''], [''users.id''], ondelete=''CASCADE''),
        sa.PrimaryKeyConstraint(''id'')
    )
    
    op.create_index(''idx_pref_workspace_user'', ''preference_responses'', [''workspace_id'', ''user_id''])
    op.create_index(''idx_pref_active'', ''preference_responses'', [''is_active''], postgresql_where=sa.text(''is_active = TRUE''))

def downgrade():
    op.drop_index(''idx_pref_active'')
    op.drop_index(''idx_pref_workspace_user'')
    op.drop_table(''preference_responses'')
```

---

## Deployment Checklist

- [ ] Database migration executed
- [ ] Indexes created
- [ ] Service deployed with new endpoints
- [ ] Frontend deployed with new pages
- [ ] Translations verified (EN, TE, HI)
- [ ] Smoke test: Student can submit preferences
- [ ] Monitoring dashboard configured
- [ ] Alert rules active

---

**Status:** Ready for Review  
**Next:** Create `tasks.md` after design approval
