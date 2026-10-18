# Requirements: Preference Questionnaires

**Spec ID:** preference-questionnaires  
**Status:** Draft  
**Created:** 2024-10-18  
**Owner:** Engineering Team  
**Related Specs:** family-alignment-dashboard, conflict-mediator-ai

---

## Overview

Family members (students and parents) need to express their preferences for college selection in a structured, weighted manner. These preferences form the foundation for the Family Alignment Dashboard and Conflict Mediator AI.

**In Scope:**
- Weighted preference collection for students and parents
- 8 preference dimensions with priority scoring
- Save/update preferences per family member
- View own and family members' preferences
- Multi-language support (EN, TE, HI)

**Out of Scope (Phase 2):**
- Counsellor preferences
- Preference history/versioning
- Recommendation based on preferences alone
- Preference templates

---

## User Stories

### US-PQ-001: Student Fills Preference Questionnaire
**As a** student  
**I want to** fill a weighted preference questionnaire  
**So that** my priorities are recorded and can be compared with my family's preferences

**Acceptance Criteria:**
- GIVEN I am a logged-in student with an active workspace
- WHEN I navigate to the preferences page
- THEN I see a questionnaire with 8 preference dimensions
- AND each dimension has a weight slider (1-10 or Low/Medium/High)
- AND each dimension has specific options to select
- AND I can save my preferences
- AND I see a confirmation message
- AND my preferences are stored with a timestamp

### US-PQ-002: Parent Fills Preference Questionnaire
**As a** parent  
**I want to** fill the same preference questionnaire as my child  
**So that** the system can compare our priorities

**Acceptance Criteria:**
- GIVEN I am a logged-in parent in a family workspace
- WHEN I navigate to the preferences page
- THEN I see the same 8 dimensions as the student
- AND I can set my own weights and selections
- AND my preferences are saved independently
- AND I can update them later

### US-PQ-003: Update Existing Preferences
**As a** family member  
**I want to** update my previously saved preferences  
**So that** I can refine my choices as I learn more

**Acceptance Criteria:**
- GIVEN I have previously saved preferences
- WHEN I navigate to the preferences page
- THEN my previous selections are pre-filled
- AND I can modify any dimension
- AND saving updates the timestamp
- AND previous version is archived (soft update)

### US-PQ-004: View Own Preferences Summary
**As a** family member  
**I want to** see a summary of my saved preferences  
**So that** I can review what I've prioritized

**Acceptance Criteria:**
- GIVEN I have saved preferences
- WHEN I view my preferences
- THEN I see each dimension with my weight and selection
- AND I see when I last updated them
- AND I have an "Edit" button to modify

### US-PQ-005: Admin Views All Preferences (Read-Only)
**As an** admin  
**I want to** view aggregated anonymized preference data  
**So that** I can understand common family priorities

**Acceptance Criteria:**
- GIVEN I am an admin
- WHEN I view the analytics dashboard
- THEN I see aggregated preference statistics
- AND no individual identifiable data is shown
- AND I see common conflicts across families

---

## Preference Dimensions

### 1. Branch Preference
**Weight:** 1-10  
**Options:** CSE, ECE, MECH, EEE, CIVIL, IT, AI/ML, Other  
**Description:** Which engineering branch do you prefer?

### 2. Location Preference
**Weight:** 1-10  
**Options:**
- Same city
- Same district
- Same state
- Anywhere in India
- Specific cities: [Hyderabad, Vijayawada, Visakhapatnam, Warangal, Tirupati, Other]

**Description:** How important is location?

### 3. College Type Preference
**Weight:** 1-10  
**Options:**
- Government
- Government-aided
- Private (Autonomous)
- Private (Non-autonomous)
- Deemed university
- No preference

**Description:** What type of college do you prefer?

### 4. Budget Constraint
**Weight:** 1-10  
**Options:**
- Up to ₹50,000/year
- ₹50,000 - ₹1,00,000/year
- ₹1,00,000 - ₹2,00,000/year
- ₹2,00,000+/year
- No constraint

**Description:** What is your annual budget limit?

### 5. Placement Importance
**Weight:** 1-10  
**Options:**
- Very important (top priority)
- Important (consider strongly)
- Moderate (nice to have)
- Low priority

**Additional Fields:**
- Minimum expected package: [dropdown]
- Preferred sectors: [IT, Core Engineering, Consulting, Research, Startups, Government]

**Description:** How important are campus placements?

### 6. Campus Facilities Importance
**Weight:** 1-10  
**Options:**
- Very important
- Important
- Moderate
- Not important

**Sub-factors:**
- Hostel quality
- Library and labs
- Sports facilities
- Transportation
- Safety and security

**Description:** How important are campus facilities?

### 7. Reputation and Ranking
**Weight:** 1-10  
**Options:**
- Must be top-ranked (NIRF top 50)
- Good ranking preferred (NIRF top 100)
- Moderate ranking acceptable
- Ranking not important

**Description:** How important is the college's reputation?

### 8. Career Goal Alignment
**Weight:** 1-10  
**Options:**
- Software development
- Core engineering (domain-specific)
- Higher studies (MS/PhD)
- Entrepreneurship
- Government job (PSU/UPSC)
- Undecided

**Description:** What is your career goal after graduation?

---

## Data Model Requirements

### PreferenceResponse Table
```
id: UUID (primary key)
workspace_id: UUID (foreign key → family_workspaces)
user_id: UUID (foreign key → users)
dimension: VARCHAR(50) (e.g., "branch_preference")
weight: INTEGER (1-10)
selected_options: JSONB (array of selected values)
additional_data: JSONB (for sub-factors)
submitted_at: TIMESTAMP
updated_at: TIMESTAMP
version: INTEGER (for soft versioning)
is_active: BOOLEAN (current version)
```

### Composite Unique Constraint
`(workspace_id, user_id, dimension, version)` must be unique.

---

## API Requirements

### POST /api/v1/preferences
**Request Body:**
```json
{
  "workspace_id": "uuid",
  "responses": [
    {
      "dimension": "branch_preference",
      "weight": 9,
      "selected_options": ["CSE", "IT"],
      "additional_data": null
    },
    {
      "dimension": "budget_constraint",
      "weight": 8,
      "selected_options": ["₹1,00,000 - ₹2,00,000/year"],
      "additional_data": null
    }
  ]
}
```

**Response:** 201 Created
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "user_id": "uuid",
  "submitted_at": "2024-10-18T10:30:00Z",
  "total_dimensions": 8,
  "completed_dimensions": 8
}
```

### GET /api/v1/preferences/me
**Query Params:** `workspace_id`  
**Response:** 200 OK
```json
{
  "user_id": "uuid",
  "workspace_id": "uuid",
  "responses": [
    {
      "dimension": "branch_preference",
      "weight": 9,
      "selected_options": ["CSE", "IT"],
      "submitted_at": "2024-10-18T10:30:00Z"
    }
  ],
  "completion_percentage": 100
}
```

### GET /api/v1/preferences/family
**Query Params:** `workspace_id`  
**Response:** 200 OK
```json
{
  "workspace_id": "uuid",
  "members": [
    {
      "user_id": "uuid",
      "full_name": "Rajitha",
      "role": "student",
      "completion_percentage": 100,
      "submitted_at": "2024-10-18T10:30:00Z"
    },
    {
      "user_id": "uuid",
      "full_name": "Parent",
      "role": "parent",
      "completion_percentage": 75,
      "submitted_at": "2024-10-18T11:00:00Z"
    }
  ]
}
```

### PUT /api/v1/preferences/{dimension}
**Request Body:**
```json
{
  "workspace_id": "uuid",
  "weight": 7,
  "selected_options": ["ECE"],
  "additional_data": null
}
```

**Response:** 200 OK

---

## Acceptance Criteria (EARS Format)

### EARS-PQ-001: Save Complete Questionnaire
**WHEN** a family member submits all 8 preference dimensions with valid weights and options  
**THEN** the system SHALL store each preference response with a timestamp  
**AND** the system SHALL mark the questionnaire as 100% complete  
**AND** the system SHALL return a success confirmation

### EARS-PQ-002: Update Single Dimension
**WHEN** a family member updates a single preference dimension  
**THEN** the system SHALL create a new version with `is_active=true`  
**AND** the system SHALL mark the previous version as `is_active=false`  
**AND** the system SHALL preserve the history

### EARS-PQ-003: Validation - Weight Range
**IF** a family member submits a weight outside 1-10  
**THEN** the system SHALL reject the request with HTTP 422  
**AND** return error message: "Weight must be between 1 and 10"

### EARS-PQ-004: Validation - Required Fields
**IF** a family member submits without selecting at least one option for a dimension  
**THEN** the system SHALL reject the request with HTTP 422  
**AND** return error message: "At least one option must be selected"

### EARS-PQ-005: Multi-language Support
**WHEN** a family member views the questionnaire in Telugu or Hindi  
**THEN** the system SHALL display all dimension labels and options in the selected language  
**AND** the system SHALL store responses in a language-agnostic format

### EARS-PQ-006: Family Member Isolation
**WHEN** a family member views their preferences  
**THEN** the system SHALL show only their own responses  
**AND** the system SHALL NOT show other members' responses (unless on alignment page)

### EARS-PQ-007: Incomplete Questionnaire Handling
**IF** a family member saves only partial preferences (e.g., 5 out of 8 dimensions)  
**THEN** the system SHALL accept the partial submission  
**AND** the system SHALL show completion percentage (e.g., 62.5%)  
**AND** the system SHALL allow them to complete remaining dimensions later

---

## Non-Functional Requirements

### Performance
- Questionnaire page SHALL load in < 2 seconds
- Save operation SHALL complete in < 500ms
- Support 1000 concurrent questionnaire submissions

### Security
- Only authenticated family members can submit preferences
- Users can only view/edit their own preferences
- Admin can view only aggregated anonymized data

### Usability
- Mobile-first design (375px viewport)
- Touch targets ≥ 44×44px
- Progress indicator showing completion %
- Auto-save on each dimension (optional)

### Accessibility
- WCAG 2.1 AA compliant
- Keyboard navigable
- Screen reader compatible
- Clear labels for all form fields

---

## Success Metrics

- **Adoption Rate:** ≥ 80% of family members complete the questionnaire within 7 days of workspace creation
- **Completion Time:** Median time to complete all 8 dimensions ≤ 10 minutes
- **Update Rate:** ≥ 30% of users update their preferences at least once
- **Data Quality:** ≥ 95% of submissions have valid, non-conflicting data

---

## Dependencies

### Upstream (Must exist first):
- ✅ User authentication system
- ✅ Family workspace system
- ✅ Multi-language (i18n) framework

### Downstream (Will use this):
- Family Alignment Dashboard
- Conflict Mediator AI

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Users don't understand dimension meanings | High | Add tooltip explanations and examples |
| Too many dimensions (survey fatigue) | Medium | Progressive disclosure; save after each section |
| Conflicting preferences cause confusion | Medium | Clear labeling: "This is YOUR preference, not the family decision" |
| Data loss on partial submission | Low | Auto-save every 2 minutes |

---

## Open Questions

1. Should we allow "skipping" dimensions? → **Decision needed**
2. Should weights be 1-10 slider or Low/Medium/High? → **Propose: Low/Medium/High (maps to 3/6/9)**
3. Should we show real-time comparison with family while filling? → **Propose: No, show only on alignment page**
4. Should we send reminder emails to incomplete questionnaires? → **Propose: Yes, after 3 days**

---

## Translation Requirements

All dimension names, options, and descriptions must be translated into:
- English (source)
- Telugu
- Hindi

Translation keys in `messages/en.json`:
```json
{
  "preferences": {
    "title": "Your Preferences",
    "dimensions": {
      "branch_preference": {
        "label": "Branch Preference",
        "description": "Which engineering branch do you prefer?",
        "options": {
          "cse": "Computer Science",
          "ece": "Electronics & Communication"
        }
      }
    }
  }
}
```

---

**Status:** Ready for Review  
**Next Steps:** Await approval before proceeding to `design.md`
