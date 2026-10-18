# Spec: Prediction Engine — Tasks

### TASK-ML-01: Feature engineering pipeline
- `backend/app/ml/training/features.py`: all 8 feature transformers as sklearn Pipeline
- Unit tests: known input → expected feature vector

### TASK-ML-02: XGBoost training script
- `backend/app/ml/training/train_predictor.py`: year-stratified split, train, evaluate, log to MLflow
- `backend/app/ml/model_cards/predictor_v1.md`: initial model card template
- Acceptance: script runs on seed data without error, logs metrics to MLflow

### TASK-ML-03: SHAP explainer integration
- Fit `TreeExplainer` after model training; save as artifact
- `backend/app/ml/serving/explainer.py`: `explain_prediction(row) -> list[ShapFactor]`
- Unit tests: returns top-3 factors with direction

### TASK-ML-04: Model serving class & FastAPI lifespan loader
- `backend/app/ml/serving/predictor.py`: `CollegePredictor.predict()`
- Load model on startup; Redis pub/sub reload signal handler
- `ml_model_versions` migration
- Unit tests: predict returns correct band for synthetic data

### TASK-ML-05: Prediction API endpoint
- `POST /api/v1/predict/colleges` with all filters
- `GET /api/v1/predict/branches`
- Auth, input validation, disclaimer enforcement, response schema
- Tests: happy path, missing rank, no-data omission, filter combinations

### TASK-ML-06: Admin ML endpoints
- `POST /api/v1/admin/ml/retrain` (Celery task trigger)
- `GET /api/v1/admin/ml/models`
- Retrain task: calls training script, registers model, signals reload
- Tests: retrain job created, model list returned

### TASK-ML-07: Fairness & calibration test suite
- `backend/tests/ml/test_model_metrics.py`: thresholds checked against seed-trained model
- `backend/tests/ml/test_fairness.py`: per-category accuracy gap check

### TASK-FE-PRED-01: College predictor UI
- Rank input form with exam/category/gender selectors
- Results page with Safe/Target/Dream band cards
- Filter sidebar (branch, district, college type, fee)
- SHAP factors collapsible section per card
- Disclaimer banner, data year badge
- i18n all strings
