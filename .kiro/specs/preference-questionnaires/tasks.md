# Tasks: Preference Questionnaires

**Spec ID:** preference-questionnaires  
**Status:** Ready for Implementation  
**Estimated Effort:** 8-10 days  
**Priority:** P0 (Blocks alignment & mediator features)

---

## Task Execution Rules

1. **Execute in order** (dependencies managed)
2. **Each task must:**
   - Write code
   - Write tests (unit + integration where applicable)
   - Run linters and tests
   - Pass all checks before marking complete
3. **Commit after each task** with conventional commit message
4. **Stop if blocked** and report

---

## Backend Tasks

### TASK-PQ-BE-001: Create Database Model
**Depends on:** None  
**Estimated:** 1 hour  
**Files:**
- `backend/app/models/preference.py` (new)

**Implementation:**
- Create `PreferenceResponse` SQLAlchemy model
- Define `PreferenceDimension` enum
- Define `PreferenceWeight` enum (LOW=3, MEDIUM=6, HIGH=9)
- Add validation constraints
- Add relationships to User and FamilyWorkspace

**Acceptance:**
- Model imports without errors
- All columns defined with correct types
- Constraints defined (CHECK, UNIQUE)
- Enums work correctly

**Tests:**
- None (model definition only)

**Commit:**
```
feat(preferences): add PreferenceResponse model with enums
```

---

### TASK-PQ-BE-002: Create Alembic Migration
**Depends on:** TASK-PQ-BE-001  
**Estimated:** 30 minutes  
**Files:**
- `backend/alembic/versions/YYYYMMDD_add_preference_responses.py` (new)

**Implementation:**
- Generate Alembic migration
- Add `preference_responses` table
- Create indexes: `idx_pref_workspace_user`, `idx_pref_active`
- Add foreign key constraints with CASCADE delete

**Acceptance:**
- Migration runs without errors
- Table created with all columns
- Indexes created
- `alembic downgrade` works

**Tests:**
- Manual: Run `alembic upgrade head` and verify table exists

**Commit:**
```
feat(preferences): add database migration for preference_responses
```

---

### TASK-PQ-BE-003: Create Pydantic Schemas
**Depends on:** TASK-PQ-BE-001  
**Estimated:** 1 hour  
**Files:**
- `backend/app/schemas/preference_schema.py` (new)

**Implementation:**
- `PreferenceResponseInput` - For POST request
- `PreferenceResponseOutput` - For GET response
- `PreferenceSubmissionRequest` - Full submission
- `PreferenceSubmissionResult` - Submission result
- `UserPreferencesResponse` - User's all preferences
- `FamilyPreferencesSummary` - Family completion status
- Add validation: weight enum, non-empty options

**Acceptance:**
- All schemas validate correctly
- Invalid data raises Pydantic ValidationError
- Schemas serialize/deserialize JSON

**Tests:**
```python
# backend/tests/unit/test_preference_schemas.py
def test_preference_response_input_validation():
    # Valid input
    valid = PreferenceResponseInput(
        dimension="branch_preference",
        weight="HIGH",
        selected_options=["CSE"],
        additional_data=None
    )
    assert valid.weight == PreferenceWeight.HIGH
    
    # Invalid weight
    with pytest.raises(ValidationError):
        PreferenceResponseInput(
            dimension="branch_preference",
            weight="INVALID",
            selected_options=["CSE"]
        )
    
    # Empty options
    with pytest.raises(ValidationError):
        PreferenceResponseInput(
            dimension="branch_preference",
            weight="HIGH",
            selected_options=[]
        )
```

**Commit:**
```
feat(preferences): add Pydantic schemas with validation
```

---

### TASK-PQ-BE-004: Create Preference Service - Submit Function
**Depends on:** TASK-PQ-BE-002, TASK-PQ-BE-003  
**Estimated:** 3 hours  
**Files:**
- `backend/app/services/preference_service.py` (new)

**Implementation:**
- Create `PreferenceService` class
- Implement `submit_preferences()` method:
  1. Validate workspace membership
  2. For each response:
     - Check if dimension already exists for user
     - If exists: mark old as inactive, create new version
     - If new: create with version=1
  3. Calculate completion percentage
  4. Return summary

**Acceptance:**
- Function saves preferences to database
- Versioning works (old marked inactive, new active)
- Completion percentage calculated correctly
- Workspace membership validated

**Tests:**
```python
# backend/tests/unit/test_preference_service.py
@pytest.mark.asyncio
async def test_submit_preferences_creates_records(db_session, test_workspace, test_user):
    service = PreferenceService()
    responses = [
        PreferenceResponseInput(
            dimension="branch_preference",
            weight="HIGH",
            selected_options=["CSE", "IT"]
        )
    ]
    
    result = await service.submit_preferences(
        db_session,
        test_workspace.id,
        test_user.id,
        responses
    )
    
    assert result.dimensions_submitted == 1
    assert result.completion_percentage == 12.5  # 1/8 * 100

@pytest.mark.asyncio
async def test_submit_preferences_creates_new_version_on_update(db_session, test_workspace, test_user):
    # Submit first time
    # Submit again with different weight
    # Assert: 2 records, old inactive, new active
```

**Commit:**
```
feat(preferences): implement submit_preferences service method
```

---

### TASK-PQ-BE-005: Create Preference Service - Get Functions
**Depends on:** TASK-PQ-BE-004  
**Estimated:** 2 hours  
**Files:**
- `backend/app/services/preference_service.py`

**Implementation:**
- `get_user_preferences()` - Get active preferences for one user
- `get_family_preferences_summary()` - Get completion status for all family members
- Both methods validate workspace membership

**Acceptance:**
- Returns only active responses
- Calculates completion % correctly
- Family summary doesn't leak preference details

**Tests:**
```python
@pytest.mark.asyncio
async def test_get_user_preferences_returns_active_only(db_session, test_user):
    # Create 2 versions of same dimension
    # Assert: only active version returned

@pytest.mark.asyncio
async def test_family_summary_shows_completion_only(db_session, test_workspace):
    # Create preferences for 2 family members
    # Assert: summary shows completion %, not details
```

**Commit:**
```
feat(preferences): implement get_user_preferences and get_family_summary
```

---

### TASK-PQ-BE-006: Create Preference Service - Update Function
**Depends on:** TASK-PQ-BE-005  
**Estimated:** 1.5 hours  
**Files:**
- `backend/app/services/preference_service.py`

**Implementation:**
- `update_dimension()` - Update single dimension
  1. Mark current active as inactive
  2. Create new row with version+1
  3. Return updated response

**Acceptance:**
- Old version marked inactive
- New version created with correct version number
- History preserved

**Tests:**
```python
@pytest.mark.asyncio
async def test_update_dimension_increments_version(db_session, test_user):
    # Create initial preference (version 1)
    # Update it
    # Assert: version 2 exists, version 1 inactive
```

**Commit:**
```
feat(preferences): implement update_dimension method
```

---

### TASK-PQ-BE-007: Create Preference Router - POST Endpoint
**Depends on:** TASK-PQ-BE-006  
**Estimated:** 2 hours  
**Files:**
- `backend/app/api/preference_router.py` (new)

**Implementation:**
- Create FastAPI router with prefix `/preferences`
- Implement `POST /api/v1/preferences` endpoint
- Add auth dependency `Depends(get_current_user)`
- Add workspace membership check
- Call `preference_service.submit_preferences()`
- Handle errors and return appropriate HTTP codes

**Acceptance:**
- Endpoint accepts valid requests
- Returns 201 Created on success
- Returns 401 if not authenticated
- Returns 403 if not workspace member
- Returns 422 on validation errors

**Tests:**
```python
# backend/tests/integration/test_preference_endpoints.py
@pytest.mark.asyncio
async def test_submit_preferences_success(client, auth_headers, test_workspace):
    response = await client.post(
        "/api/v1/preferences",
        json={
            "workspace_id": str(test_workspace.id),
            "responses": [...]
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["dimensions_submitted"] == 1

@pytest.mark.asyncio
async def test_submit_preferences_unauthenticated_returns_401(client):
    response = await client.post("/api/v1/preferences", json={...})
    assert response.status_code == 401
```

**Commit:**
```
feat(preferences): add POST /api/v1/preferences endpoint
```

---

### TASK-PQ-BE-008: Create Preference Router - GET Endpoints
**Depends on:** TASK-PQ-BE-007  
**Estimated:** 1.5 hours  
**Files:**
- `backend/app/api/preference_router.py`

**Implementation:**
- `GET /api/v1/preferences/me` - Get own preferences
- `GET /api/v1/preferences/family` - Get family summary
- Add auth + workspace membership checks

**Acceptance:**
- GET /me returns user's active preferences
- GET /family returns completion summary only
- Both require authentication

**Tests:**
```python
@pytest.mark.asyncio
async def test_get_own_preferences(client, auth_headers, test_workspace):
    response = await client.get(
        f"/api/v1/preferences/me?workspace_id={test_workspace.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "responses" in response.json()

@pytest.mark.asyncio
async def test_get_family_summary(client, auth_headers, test_workspace):
    response = await client.get(
        f"/api/v1/preferences/family?workspace_id={test_workspace.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "members" in response.json()
```

**Commit:**
```
feat(preferences): add GET endpoints for preferences
```

---

### TASK-PQ-BE-009: Create Preference Router - PUT Endpoint
**Depends on:** TASK-PQ-BE-008  
**Estimated:** 1 hour  
**Files:**
- `backend/app/api/preference_router.py`

**Implementation:**
- `PUT /api/v1/preferences/{dimension}` - Update single dimension
- Call `preference_service.update_dimension()`

**Acceptance:**
- Updates existing dimension
- Returns 200 OK on success
- Returns 404 if dimension doesn't exist

**Tests:**
```python
@pytest.mark.asyncio
async def test_update_dimension(client, auth_headers, test_workspace):
    # First create a preference
    # Then update it
    response = await client.put(
        "/api/v1/preferences/branch_preference",
        json={...},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["version"] == 2
```

**Commit:**
```
feat(preferences): add PUT endpoint for dimension update
```

---

### TASK-PQ-BE-010: Register Router in Main App
**Depends on:** TASK-PQ-BE-009  
**Estimated:** 15 minutes  
**Files:**
- `backend/app/main.py`

**Implementation:**
- Import `preference_router`
- Add `app.include_router(preference_router, prefix="/api/v1")`

**Acceptance:**
- Router registered
- Endpoints visible in /docs
- Server starts without errors

**Tests:**
- Manual: Visit http://localhost:8000/docs and verify endpoints

**Commit:**
```
feat(preferences): register preference router in main app
```

---

## Frontend Tasks

### TASK-PQ-FE-001: Add i18n Translation Keys
**Depends on:** None  
**Estimated:** 1 hour  
**Files:**
- `frontend/src/i18n/messages/en.json`
- `frontend/src/i18n/messages/te.json`
- `frontend/src/i18n/messages/hi.json`

**Implementation:**
- Add `preferences` section with all dimension names, descriptions, options
- All 3 languages must have matching keys

**Acceptance:**
- All keys present in EN, TE, HI
- No missing translations
- CI hook passes (key matching check)

**Commit:**
```
feat(preferences): add i18n translations for questionnaire
```

---

### TASK-PQ-FE-002: Create API Client Functions
**Depends on:** None  
**Estimated:** 45 minutes  
**Files:**
- `frontend/src/lib/api.ts` (update)

**Implementation:**
- Add typed functions:
  - `submitPreferences()`
  - `getUserPreferences()`
  - `getFamilyPreferencesSummary()`
  - `updateDimension()`

**Acceptance:**
- Functions call correct endpoints
- TypeScript types match API schemas
- Error handling included

**Commit:**
```
feat(preferences): add API client functions
```

---

### TASK-PQ-FE-003: Create React Query Hooks
**Depends on:** TASK-PQ-FE-002  
**Estimated:** 1 hour  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/hooks/usePreferences.ts` (new)

**Implementation:**
- `useSubmitPreferences()` - useMutation for submission
- `useUserPreferences()` - useQuery for getting own
- `useFamilyPreferencesSummary()` - useQuery for family
- `useUpdateDimension()` - useMutation for single update

**Acceptance:**
- Hooks work with React Query
- Cache invalidation on mutations
- Loading and error states handled

**Commit:**
```
feat(preferences): add React Query hooks
```

---

### TASK-PQ-FE-004: Create WeightSelector Component
**Depends on:** TASK-PQ-FE-001  
**Estimated:** 1.5 hours  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/components/WeightSelector.tsx` (new)

**Implementation:**
- Three buttons: Low, Medium, High
- Active state styling
- Keyboard accessible
- i18n labels

**Acceptance:**
- Renders 3 buttons
- Clicking changes selection
- Active button highlighted
- Accessible (keyboard + screen reader)

**Tests:**
```typescript
// frontend/tests/unit/WeightSelector.test.tsx
test(''renders three weight options'', () => {
  render(<WeightSelector value="LOW" onChange={jest.fn()} />);
  expect(screen.getByText(''Low'')).toBeInTheDocument();
  expect(screen.getByText(''Medium'')).toBeInTheDocument();
  expect(screen.getByText(''High'')).toBeInTheDocument();
});

test(''calls onChange when button clicked'', () => {
  const onChange = jest.fn();
  render(<WeightSelector value="LOW" onChange={onChange} />);
  fireEvent.click(screen.getByText(''Medium''));
  expect(onChange).toHaveBeenCalledWith(''MEDIUM'');
});
```

**Commit:**
```
feat(preferences): create WeightSelector component
```

---

### TASK-PQ-FE-005: Create OptionSelector Component
**Depends on:** TASK-PQ-FE-001  
**Estimated:** 2 hours  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/components/OptionSelector.tsx` (new)

**Implementation:**
- Renders checkboxes for multi-select options
- i18n labels
- Validation: at least one required
- Accessible

**Acceptance:**
- Renders all options as checkboxes
- Multi-select works
- Shows error if none selected
- Keyboard navigable

**Tests:**
```typescript
test(''allows multiple selections'', () => {
  const onChange = jest.fn();
  render(<OptionSelector options={[...]} selected={[]} onChange={onChange} />);
  fireEvent.click(screen.getByLabelText(''CSE''));
  fireEvent.click(screen.getByLabelText(''IT''));
  expect(onChange).toHaveBeenCalledWith([''CSE'', ''IT'']);
});
```

**Commit:**
```
feat(preferences): create OptionSelector component
```

---

### TASK-PQ-FE-006: Create DimensionCard Component
**Depends on:** TASK-PQ-FE-004, TASK-PQ-FE-005  
**Estimated:** 2 hours  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/components/DimensionCard.tsx` (new)

**Implementation:**
- Card layout with icon, title, description
- Embeds WeightSelector and OptionSelector
- Collapsible/expandable
- Shows saved indicator

**Acceptance:**
- Renders dimension info
- Contains weight and option selectors
- Visual feedback when saved
- Mobile responsive

**Commit:**
```
feat(preferences): create DimensionCard component
```

---

### TASK-PQ-FE-007: Create ProgressBar Component
**Depends on:** None  
**Estimated:** 1 hour  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/components/ProgressBar.tsx` (new)

**Implementation:**
- Visual progress bar (0-100%)
- Shows "X/8 dimensions completed"
- Accessible (aria-valuenow, aria-valuemin, aria-valuemax)

**Acceptance:**
- Bar fills proportionally
- Text shows correct count
- Accessible

**Commit:**
```
feat(preferences): create ProgressBar component
```

---

### TASK-PQ-FE-008: Create PreferenceForm Component
**Depends on:** TASK-PQ-FE-006, TASK-PQ-FE-007  
**Estimated:** 3 hours  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/components/PreferenceForm.tsx` (new)

**Implementation:**
- Form wrapper with React Hook Form
- Renders 8 DimensionCards
- Progress bar at top
- Submit button with loading state
- Auto-save every 2 minutes (optional)

**Acceptance:**
- All 8 dimensions render
- Form submits correctly
- Loading state during submission
- Success toast on save

**Commit:**
```
feat(preferences): create PreferenceForm component
```

---

### TASK-PQ-FE-009: Create Preferences Page
**Depends on:** TASK-PQ-FE-008, TASK-PQ-FE-003  
**Estimated:** 2 hours  
**Files:**
- `frontend/src/app/[locale]/(workspace)/preferences/page.tsx` (new)

**Implementation:**
- Page wrapper
- Load existing preferences if available
- Render PreferenceForm
- Handle submission via useSubmitPreferences hook
- Redirect to dashboard on completion

**Acceptance:**
- Page loads without errors
- Existing preferences pre-filled
- New preferences can be submitted
- Redirects after save

**Tests (E2E):**
```typescript
// frontend/tests/e2e/preferences.spec.ts
test(''student completes questionnaire'', async ({ page }) => {
  await page.goto(''/en/preferences'');
  
  // Fill all 8 dimensions
  await page.click(''text=High''); // Branch weight
  await page.check(''text=CSE'');  // Branch option
  // ... fill remaining 7 dimensions
  
  await page.click(''text=Submit'');
  
  // Should redirect to dashboard
  await expect(page).toHaveURL(''/en/dashboard'');
  
  // Should show completion
  await expect(page.locator(''text=100% complete'')).toBeVisible();
});
```

**Commit:**
```
feat(preferences): create preferences page
```

---

### TASK-PQ-FE-010: Add Preferences Link to Dashboard
**Depends on:** TASK-PQ-FE-009  
**Estimated:** 30 minutes  
**Files:**
- `frontend/src/app/[locale]/(workspace)/dashboard/page.tsx`

**Implementation:**
- Add "Set Preferences" card if not completed
- Show completion status if completed
- Link to `/preferences` page

**Acceptance:**
- Card shows on dashboard
- Link works
- Completion status accurate

**Commit:**
```
feat(preferences): add link to preferences from dashboard
```

---

## Documentation Tasks

### TASK-PQ-DOC-001: Update API Documentation
**Depends on:** TASK-PQ-BE-010  
**Estimated:** 1 hour  
**Files:**
- `docs/api/preferences.md` (new)

**Implementation:**
- Document all 4 endpoints
- Include request/response examples
- Document error codes

**Commit:**
```
docs(preferences): add API documentation
```

---

### TASK-PQ-DOC-002: Update User Guide
**Depends on:** TASK-PQ-FE-010  
**Estimated:** 1 hour  
**Files:**
- `docs/user-guide.md`

**Implementation:**
- Add section on filling preferences
- Screenshots of questionnaire
- Explain dimension meanings

**Commit:**
```
docs(preferences): update user guide with questionnaire instructions
```

---

## Testing Tasks

### TASK-PQ-TEST-001: Run Full Test Suite
**Depends on:** All implementation tasks  
**Estimated:** 1 hour  
**Files:** N/A

**Implementation:**
- Run `pytest --cov` - verify ≥ 80% coverage
- Run `npm test` - verify frontend tests pass
- Run `playwright test` - verify E2E passes

**Acceptance:**
- All tests pass
- Coverage meets threshold
- No linting errors

**Commit:**
```
test(preferences): verify full test suite passes
```

---

## Summary

**Total Tasks:** 22  
**Backend:** 10 tasks  
**Frontend:** 10 tasks  
**Documentation:** 2 tasks  
**Testing:** 1 task (final validation)

**Estimated Timeline:**
- Backend: 3-4 days
- Frontend: 4-5 days
- Documentation: 1 day
- Total: **8-10 days**

**Critical Path:**
1. Backend model & migration (1-2)
2. Backend service (4-6)
3. Backend router (7-10)
4. Frontend components (4-8)
5. Frontend page (9-10)

---

**Status:** Ready to Execute  
**Next:** Begin with TASK-PQ-BE-001
