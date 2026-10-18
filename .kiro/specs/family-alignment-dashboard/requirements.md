# Requirements: Family Alignment Dashboard

**Spec ID:** family-alignment-dashboard  
**Status:** Draft  
**Created:** 2024-10-18  
**Owner:** Engineering Team  
**Related Specs:** preference-questionnaires, conflict-mediator-ai

---

## Overview

The Family Alignment Dashboard visualizes where family members agree and disagree on college selection preferences. It provides clear, data-driven insights into alignment scores, conflict areas, and consensus points.

**In Scope:**
- Visual comparison of family preferences across 8 dimensions
- Agreement/disagreement scoring per dimension
- Overall family alignment percentage
- Plain-language conflict summaries
- Interactive charts (diverging bar charts, radar charts)
- Export alignment report as PDF

**Out of Scope (Phase 2):**
- Time-series tracking of alignment changes
- Alignment with external benchmarks
- Automated conflict resolution suggestions (see conflict-mediator-ai spec)

---

## User Stories

### US-FAD-001: View Family Alignment Overview
**As a** family member  
**I want to** see an overview of how aligned my family is on college preferences  
**So that** I understand where we agree and where we need to discuss further

**Acceptance Criteria:**
- GIVEN multiple family members have submitted preferences
- WHEN I view the alignment dashboard
- THEN I see an overall alignment score (0-100%)
- AND I see a breakdown by dimension (8 dimensions)
- AND I see visual indicators (green = high alignment, amber = partial, red = low)
- AND I see which dimensions have the most disagreement

### US-FAD-002: Compare Preferences by Dimension
**As a** family member  
**I want to** see how each family member weighted each dimension  
**So that** I understand whose priorities differ from mine

**Acceptance Criteria:**
- GIVEN all family members have submitted preferences
- WHEN I view a specific dimension (e.g., Branch Preference)
- THEN I see a diverging bar chart comparing weights
- AND I see each member's selected options
- AND I see the alignment score for this dimension (0-100%)
- AND I see a plain-language summary (e.g., "Student prioritizes CSE highly, Parent prioritizes budget more")

### US-FAD-003: Identify Conflict Areas
**As a** family member  
**I want to** quickly identify the top 3 areas of disagreement  
**So that** I know what to discuss with my family

**Acceptance Criteria:**
- GIVEN family preferences with varying alignment scores
- WHEN I view the dashboard
- THEN I see a "Top Conflicts" section
- AND the top 3 dimensions with lowest alignment are highlighted
- AND each conflict shows:
  - Dimension name
  - Alignment score
  - Brief explanation (e.g., "Student wants CSE, Parent prefers EEE")
  - Link to mediation suggestions

### US-FAD-004: View Consensus Areas
**As a** family member  
**I want to** see where we all agree  
**So that** I feel confident about those aspects of the decision

**Acceptance Criteria:**
- GIVEN family preferences with high alignment on some dimensions
- WHEN I view the dashboard
- THEN I see a "Areas of Agreement" section
- AND dimensions with >80% alignment are listed
- AND each shows what we agree on (e.g., "Everyone agrees location should be Hyderabad")

### US-FAD-005: Download Alignment Report
**As a** family member  
**I want to** download a PDF of the alignment dashboard  
**So that** I can discuss it offline or share with a counsellor

**Acceptance Criteria:**
- GIVEN I am viewing the alignment dashboard
- WHEN I click "Download Report"
- THEN a PDF is generated containing:
  - Overall alignment score
  - All 8 dimension comparisons
  - Top conflicts and agreements
  - Family member names and roles
  - Timestamp
- AND the PDF is professionally formatted
- AND it downloads immediately

---

## Alignment Calculation Logic

### Overall Alignment Score

**Formula:**
```
Overall Alignment = Average of (8 dimension alignment scores)

Dimension Alignment Score = (
  Weight Alignment (50%) + 
  Option Overlap Alignment (50%)
)

Weight Alignment = 100 - (|Weight_A - Weight_B| / 6) * 100
  (6 = max difference between LOW=3 and HIGH=9)

Option Overlap Alignment:
  If same options selected: 100%
  If partial overlap: (Overlap count / Total unique options) * 100
  If no overlap: 0%
```

**Example:**
- Student: Branch = HIGH (9), Options = [CSE, IT]
- Parent: Branch = MEDIUM (6), Options = [CSE, ECE]

Weight Alignment = 100 - (|9-6| / 6) * 100 = 100 - 50 = 50%
Option Overlap = 1 common (CSE) / 3 unique total = 33.33%
Dimension Alignment = (50% + 33.33%) / 2 = 41.67%

### Alignment Bands

| Score | Label | Color | Meaning |
|-------|-------|-------|---------|
| 80-100% | High Alignment | 🟢 Green | Strong consensus |
| 50-79% | Moderate Alignment | 🟡 Amber | Some differences |
| 0-49% | Low Alignment | 🔴 Red | Significant conflict |

---

## Visual Design Requirements

### 1. Overall Alignment Card

```
┌─────────────────────────────────────────┐
│  Family Alignment Score                 │
│                                         │
│         ╔════════╗                      │
│         ║  68%   ║  Moderate Alignment │
│         ╚════════╝                      │
│                                         │
│  [■■■■■■■□□□] Progress bar              │
│                                         │
│  Based on preferences from:             │
│  • Rajitha (Student) ✓                  │
│  • Parent Name (Parent) ✓               │
└─────────────────────────────────────────┘
```

### 2. Dimension Comparison (Diverging Bar Chart)

```
Branch Preference                    41% Aligned 🔴

Student ████████████▌ HIGH (9)
Parent  ████████▌ MEDIUM (6)

Options:
  ✓ CSE (both selected)
  × IT (student only)
  × ECE (parent only)

Summary: Student prioritizes technology branches highly,
while parent has moderate priority with broader options.
```

### 3. Top Conflicts Panel

```
┌─────────────────────────────────────────┐
│  🔴 Top Areas of Disagreement           │
├─────────────────────────────────────────┤
│  1. Branch Preference (41% aligned)     │
│     Student wants CSE/IT, Parent        │
│     considers CSE/ECE                   │
│     [See Mediation Suggestions →]       │
├─────────────────────────────────────────┤
│  2. Budget (35% aligned)                │
│     Student: Any budget                 │
│     Parent: ₹50k-1L/year max            │
│     [See Mediation Suggestions →]       │
├─────────────────────────────────────────┤
│  3. Location (52% aligned)              │
│     Student: Anywhere in India          │
│     Parent: Same city only              │
│     [See Mediation Suggestions →]       │
└─────────────────────────────────────────┘
```

### 4. Consensus Panel

```
┌─────────────────────────────────────────┐
│  ✅ Areas of Agreement                  │
├─────────────────────────────────────────┤
│  • Placement Importance (95%)           │
│    Everyone agrees placements are high  │
│    priority with IT sector preference   │
├─────────────────────────────────────────┤
│  • College Type (88%)                   │
│    Family prefers government or         │
│    autonomous colleges                  │
├─────────────────────────────────────────┤
│  • Reputation (82%)                     │
│    NIRF top 100 ranking important       │
└─────────────────────────────────────────┘
```

---

## Data Model Requirements

### No new tables required
Uses existing `preference_responses` table from preference-questionnaires spec.

### Computed Fields (API Response)

```typescript
interface AlignmentDashboard {
  workspace_id: string;
  overall_alignment_score: number;  // 0-100
  alignment_band: "HIGH" | "MODERATE" | "LOW";
  dimensions: DimensionAlignment[];
  top_conflicts: ConflictSummary[];
  agreements: AgreementSummary[];
  members: MemberStatus[];
  generated_at: string;
}

interface DimensionAlignment {
  dimension: string;
  dimension_label: string;
  alignment_score: number;
  alignment_band: "HIGH" | "MODERATE" | "LOW";
  member_responses: MemberResponse[];
  summary: string;  // Plain language
}

interface MemberResponse {
  user_id: string;
  full_name: string;
  role: "student" | "parent";
  weight: "LOW" | "MEDIUM" | "HIGH";
  weight_numeric: number;
  selected_options: string[];
}

interface ConflictSummary {
  dimension: string;
  alignment_score: number;
  description: string;
  mediation_available: boolean;
}

interface AgreementSummary {
  dimension: string;
  alignment_score: number;
  description: string;
}
```

---

## API Requirements

### GET /api/v1/alignment/dashboard

**Query Params:** `workspace_id`

**Response (200 OK):**
```json
{
  "workspace_id": "uuid",
  "overall_alignment_score": 68.5,
  "alignment_band": "MODERATE",
  "dimensions": [
    {
      "dimension": "branch_preference",
      "dimension_label": "Branch Preference",
      "alignment_score": 41.7,
      "alignment_band": "LOW",
      "member_responses": [
        {
          "user_id": "uuid",
          "full_name": "Rajitha",
          "role": "student",
          "weight": "HIGH",
          "weight_numeric": 9,
          "selected_options": ["CSE", "IT"]
        },
        {
          "user_id": "uuid",
          "full_name": "Parent",
          "role": "parent",
          "weight": "MEDIUM",
          "weight_numeric": 6,
          "selected_options": ["CSE", "ECE"]
        }
      ],
      "summary": "Student prioritizes technology branches highly, while parent has moderate priority with broader options."
    }
  ],
  "top_conflicts": [
    {
      "dimension": "branch_preference",
      "alignment_score": 41.7,
      "description": "Student wants CSE/IT, Parent considers CSE/ECE",
      "mediation_available": true
    }
  ],
  "agreements": [
    {
      "dimension": "placement_importance",
      "alignment_score": 95.0,
      "description": "Everyone agrees placements are high priority"
    }
  ],
  "members": [
    {
      "user_id": "uuid",
      "full_name": "Rajitha",
      "role": "student",
      "completion_percentage": 100
    }
  ],
  "generated_at": "2024-10-18T14:30:00Z"
}
```

### GET /api/v1/alignment/export

**Query Params:** `workspace_id`, `format=pdf`

**Response:** PDF file download

---

## Acceptance Criteria (EARS Format)

### EARS-FAD-001: Calculate Overall Alignment
**WHEN** a family has multiple members with complete preferences  
**THEN** the system SHALL calculate overall alignment as the average of 8 dimension scores  
**AND** the score SHALL be between 0 and 100  
**AND** the alignment band SHALL be HIGH (80-100), MODERATE (50-79), or LOW (0-49)

### EARS-FAD-002: Calculate Dimension Alignment
**WHEN** comparing two family members' responses for a dimension  
**THEN** the system SHALL calculate weight alignment based on numeric difference  
**AND** the system SHALL calculate option overlap alignment  
**AND** the final dimension score SHALL be the average of weight and option alignments

### EARS-FAD-003: Identify Top Conflicts
**WHEN** generating the dashboard  
**THEN** the system SHALL sort dimensions by alignment score ascending  
**AND** the system SHALL return the 3 dimensions with lowest scores as "top conflicts"  
**AND** each conflict SHALL include a plain-language description

### EARS-FAD-004: Identify Agreements
**WHEN** generating the dashboard  
**THEN** the system SHALL identify dimensions with alignment ≥ 80%  
**AND** the system SHALL list them as "areas of agreement"  
**AND** each agreement SHALL include what the family agrees on

### EARS-FAD-005: Handle Incomplete Preferences
**IF** any family member has not completed preferences  
**THEN** the system SHALL show a warning: "Alignment incomplete - waiting for X to submit preferences"  
**AND** the system SHALL NOT calculate scores for missing members  
**AND** the system SHALL allow viewing partial alignment

### EARS-FAD-006: Generate PDF Report
**WHEN** a user requests PDF export  
**THEN** the system SHALL generate a PDF containing all dashboard elements  
**AND** the PDF SHALL be ≤ 5 pages  
**AND** the PDF SHALL include workspace name, member names, and timestamp

---

## Non-Functional Requirements

### Performance
- Dashboard generation SHALL complete in < 2 seconds for 2-4 family members
- PDF generation SHALL complete in < 5 seconds
- Support up to 10 family members per workspace (future-proof)

### Security
- Only workspace members can view alignment dashboard
- PDF export requires authentication
- No alignment data cached beyond 5 minutes

### Usability
- Mobile-first design (readable on 375px screens)
- Color-blind friendly (use patterns + colors)
- Tooltips explain alignment scores
- Print-friendly layout

### Accessibility
- Charts have text alternatives
- Color is not the only differentiator (icons, patterns)
- Keyboard navigable
- Screen reader friendly

---

## Success Metrics

- **Engagement:** ≥ 70% of families view the alignment dashboard within 7 days of completing preferences
- **Understanding:** ≥ 80% of users correctly identify their top conflict area (measured via survey)
- **Action:** ≥ 50% of families with <70% alignment request mediation
- **Export Rate:** ≥ 30% of families download the PDF report

---

## Dependencies

### Upstream (Must exist first):
- ✅ User authentication
- ✅ Family workspace
- ⚠️ Preference questionnaires (MUST complete first)

### Downstream (Will use this):
- ⚠️ Conflict Mediator AI (uses alignment data)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex scoring confuses users | High | Provide plain-language explanations, tooltips |
| Charts not mobile-friendly | Medium | Use stacked bars on mobile, side-by-side on desktop |
| PDF export slow with many members | Low | Limit to 10 members, optimize rendering |
| Alignment score feels judgmental | Medium | Frame as "areas to discuss" not "problems" |

---

## Open Questions

1. Should we show historical alignment changes over time? → **Decision: No (Phase 2)**
2. Should counsellors see alignment dashboards? → **Decision: Yes, read-only**
3. Should we allow filtering by specific family members? → **Decision: No, show all**
4. Should we notify families when alignment improves? → **Decision: Yes, after preference updates**

---

## Translation Requirements

All labels, summaries, and chart text must be translated into:
- English (source)
- Telugu
- Hindi

**Plain-language summaries** must be culturally appropriate and neutral (no judgment).

---

**Status:** Ready for Review  
**Next Steps:** Create `design.md` after approval
