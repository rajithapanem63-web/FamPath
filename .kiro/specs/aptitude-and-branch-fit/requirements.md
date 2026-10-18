# Spec: Aptitude & Branch Fit — Requirements

## Overview
A 15–20 question RIASEC-style psychometric quiz that produces a Branch Fit Score for each engineering branch, with transparent, rule-based scoring.

## User Stories
- US-APT-01: As a student, I can take a 15–20 question interest quiz in my preferred language.
- US-APT-02: As a student, I see my RIASEC profile (scores for Realistic/Investigative/Artistic/Social/Enterprising/Conventional) after completing the quiz.
- US-APT-03: As a student, I see a Branch Fit Score (0–100) for each major engineering branch, with an explanation of which RIASEC dimensions drive the score.
- US-APT-04: As a student, I can retake the quiz; previous results are stored with a timestamp for history.
- US-APT-05: As a parent, I can view my child's Branch Fit Scores (read-only) in the shared workspace.

## Acceptance Criteria

### Quiz Flow
- WHEN a student starts the quiz, THEN 15–20 active questions are served in a randomised order (fixed seed per session for reproducibility).
- WHEN a student answers all questions and submits, THEN RIASEC scores and Branch Fit Scores are computed within 200 ms.
- WHEN a student partially completes the quiz and returns later, THEN their progress is saved and they can resume from where they left off.

### Scoring
- Branch Fit Scores MUST be computed using a documented, deterministic rule mapping: RIASEC dimension scores → branch weights (stored in the question bank config).
- WHEN a Branch Fit Score is shown, THEN the top-2 contributing RIASEC dimensions are shown alongside the score.
- All scores are in the range 0–100; the scoring formula is documented in code and in the model card.

### History & Sharing
- WHEN a student retakes the quiz, THEN both old and new results are retained; the latest is used for recommendations.
- WHERE a parent views the workspace, THEN they can see the student's latest Branch Fit Scores but NOT the individual question answers.
