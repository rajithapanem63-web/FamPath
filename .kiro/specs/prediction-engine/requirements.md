# Spec: Prediction Engine — Requirements

## Overview
ML-powered college and branch predictor that takes a student's rank, exam, category, and gender and returns Safe/Target/Dream band assignments with probability and explainability.

## User Stories
- US-PRED-01: As a student, I can enter my exam, rank, category, and gender to get a personalised college list.
- US-PRED-02: As a student, I see each college/branch labelled as Safe, Target, or Dream with a probability.
- US-PRED-03: As a student, I see an explanation of why each college is in a particular band (key factors).
- US-PRED-04: As a student, I can filter results by branch, location, college type, and fee range.
- US-PRED-05: As a student, every prediction card shows the data year used and the disclaimer "Estimate, not a guarantee."
- US-PRED-06: As an admin, I can trigger model retraining from the admin panel after new cutoff data is imported.
- US-PRED-07: As an admin, I can view model metrics (accuracy, calibration, per-category performance) in the admin panel.

## Acceptance Criteria

### Prediction Results
- WHEN a student submits rank=5000, category=OC, exam=AP_EAPCET, gender=male, THEN the system returns a list of college/branch pairs sorted by band (Safe first) within 500 ms (p95).
- WHEN Safe band is assigned, THEN the historical closing rank for that category in the latest available year MUST be higher (worse) than the student's rank by at least a configurable margin.
- WHEN Target band is assigned, THEN the student's rank falls near (within configurable window) the historical closing rank.
- WHEN Dream band is assigned, THEN the student's rank is higher (better number) than the historical closing rank.
- WHERE no cutoff data exists for a college/branch/category combination, THEN that row is omitted from results (not shown as Safe/Target/Dream).
- EVERY prediction card MUST display: college name, branch, band label, probability (0–100 %), data year, "Estimate, not a guarantee" text, and at least one SHAP-derived explanation factor.

### Model Quality (before production promotion)
- Overall accuracy ≥ 80 % on held-out test year data.
- Per-category accuracy ≥ 75 % for OC, BC, SC, ST.
- Expected Calibration Error (ECE) ≤ 0.05.
- Gender accuracy gap ≤ 5 percentage points.

### Explainability
- WHEN a prediction is returned, THEN the top-3 SHAP features and their direction (increases/decreases probability) MUST be included in the response.

### Retraining
- WHEN an admin triggers retraining and it completes, THEN the new model version is registered in MLflow and metrics are updated in the admin panel.
- WHERE retraining fails, THEN the previous model remains active and an error is logged.
