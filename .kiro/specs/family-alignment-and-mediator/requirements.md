# Spec: Family Alignment & Mediator — Requirements

## Overview
Visual comparison of student and parent preferences with AI-powered neutral conflict mediation and compromise suggestions.

## User Stories
- US-ALIGN-01: As a family, we can see a visual dashboard comparing student and parent preference weights side by side.
- US-ALIGN-02: As a student, I see which preferences align with my parents' and which conflict.
- US-ALIGN-03: As a family, we can request an AI explanation of why each side holds a particular preference and what a compromise might look like.
- US-ALIGN-04: As a family, we can see an overall Family Alignment Score (0–100) that updates as preferences change.
- US-ALIGN-05: As a counsellor, I can view the alignment dashboard for a client family (read-only).

## Acceptance Criteria

### Alignment Dashboard
- WHEN both student and at least one parent have submitted preferences, THEN the alignment dashboard shows a side-by-side comparison with an agreement/conflict indicator per dimension (colour + label).
- WHEN only one member has submitted, THEN the dashboard shows that member's preferences and a prompt for the other to complete theirs.
- The Family Alignment Score MUST be computed as a weighted cosine similarity between student and parent preference vectors, normalised to 0–100.

### Conflict Mediator AI
- WHEN a family requests mediation for a specific conflict dimension, THEN the AI returns: (a) a neutral summary of each side's reasoning, (b) 2–3 compromise options, (c) relevant data from the platform (e.g., placement data supporting the student's branch preference).
- ALL mediator responses MUST cite at least one platform data source.
- WHEN a mediation request is made, THEN the response MUST NOT assign blame or take sides.
- WHERE the AI cannot find platform data to support a claim, THEN it MUST say "I don't have sufficient data to verify this claim."
