# Requirements: Conflict Mediator AI

**Spec ID:** conflict-mediator-ai  
**Status:** Draft  
**Dependencies:** preference-questionnaires, family-alignment-dashboard

---

## Overview

AI-powered neutral mediator that analyzes family conflicts and suggests compromises based on FamPath data (college info, costs, placements).

**Key Principles:**
- **Neutral:** Never takes sides
- **Data-backed:** All suggestions grounded in platform data
- **Explainable:** Shows reasoning for each suggestion
- **Respectful:** Calm, non-judgmental language

---

## User Stories

### US-CM-001: Request Mediation for Conflict
**As a** family member  
**I want to** request AI mediation for a specific conflict area  
**So that** I get neutral suggestions for compromise

**Acceptance:**
- From alignment dashboard, click "See Mediation" on a conflict
- System analyzes preferences for that dimension
- Returns 2-3 compromise options with reasoning

### US-CM-002: View Compromise Options
**As a** family member  
**I want to** see multiple compromise suggestions  
**So that** I can choose what works best for my family

**Acceptance:**
- Each suggestion shows:
  - Compromise approach (e.g., "Consider autonomous colleges")
  - Why it works (e.g., "Balances budget and placement goals")
  - Data support (e.g., "Avg fee: ₹1.2L, Avg package: ₹5.5L")
  - Trade-offs (e.g., "May require hostel costs")

### US-CM-003: Save Mediation Suggestions
**As a** family member  
**I want to** save mediation suggestions to review later  
**So that** I can discuss them with my family

---

## Mediation Logic

### Input:
- Dimension with conflict (e.g., "branch_preference")
- All family member responses
- College data (fees, placements, cutoffs)

### Output:
- 2-3 compromise suggestions
- Each with: approach, reasoning, data, trade-offs

### LLM Prompt Structure:
```
System: You are a neutral family mediator for Indian engineering college admissions...

Context:
- Family: Rajitha's Family
- Conflict: Branch Preference (41% alignment)
- Student: Wants CSE/IT (HIGH priority)
- Parent: Considers CSE/ECE (MEDIUM priority)

Data:
- CSE colleges: [list with fees, placements]
- ECE colleges: [list with fees, placements]

Task: Suggest 2-3 compromises that respect both preferences.
Format: JSON {suggestions: [{approach, reasoning, data, tradeoffs}]}
```

---

## API

**POST /api/v1/mediation/request**
```json
{
  "workspace_id": "uuid",
  "dimension": "branch_preference"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "approach": "Consider CSE with ECE minor",
      "reasoning": "...",
      "data_support": "...",
      "tradeoffs": "..."
    }
  ]
}
```

---

## Acceptance Criteria

- EARS-CM-001: Mediator SHALL never use judgmental language
- EARS-CM-002: All suggestions SHALL be grounded in platform data
- EARS-CM-003: Response SHALL be generated in < 10 seconds

---

**Status:** Ready for design.md
