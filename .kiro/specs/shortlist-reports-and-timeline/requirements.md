# Spec: Shortlist, Reports & Timeline — Requirements

## Overview
Shared college shortlist with family voting, a downloadable PDF decision report, and a counselling timeline with document checklist.

## User Stories
- US-SHORT-01: As a student, I can add colleges to a shared family shortlist.
- US-SHORT-02: As any family member, I can vote (thumbs up/down) on shortlisted colleges and add comments.
- US-SHORT-03: As a family, I can see a decision history showing when items were added, voted on, or removed.
- US-SHORT-04: As a student, I can mark one college/branch as the final decision.
- US-SHORT-05: As any family member, I can download a PDF report summarising the profile, shortlist, prediction results, cost, and family alignment.
- US-SHORT-06: As a student, I can see a personalised counselling timeline with deadlines for my exam type.
- US-SHORT-07: As a student, I can see a category-wise document checklist and mark items as completed.
- US-SHORT-08: As a student, I can set deadline reminders (email + in-app notification).

## Acceptance Criteria

### Shortlist
- WHEN a college is added to the shortlist, THEN it appears for all workspace members within 5 seconds (or on next page load).
- Shortlist maximum: 20 colleges per workspace.
- WHEN a family member votes, THEN their vote and optional comment are stored with timestamp and shown to all members.

### PDF Report
- WHEN a student requests a PDF, THEN it is generated within 30 seconds and downloaded.
- The PDF MUST include: student profile summary, aptitude results, top-5 shortlisted colleges with band/cost/alignment scores, family alignment score, final decision (if set), and all disclaimers.
- The PDF MUST be generated in the user's preferred language.

### Timeline & Checklist
- WHEN a student's profile has exam_type set, THEN a timeline is shown with counselling round dates (from seed data) and days remaining.
- Document checklist is category-specific (e.g., caste certificate for BC/SC/ST).
- WHEN a document is marked complete, THEN the status is saved and shown to all workspace members.
