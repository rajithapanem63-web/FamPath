# Spec: Prediction Engine — Design

## ML Architecture

```
cutoff_records (DB)
      │
      ▼
Feature Engineering Pipeline (scikit-learn)
  - rank_percentile (rank / max_rank_for_exam_year)
  - category_encoded (ordinal: OC=0, EWS=1, BC_A=2…ST=6)
  - gender_encoded (0/1)
  - college_tier (computed from historical avg closing rank)
  - branch_demand_index (closing_rank trend over 3 years)
      │
      ▼
XGBoost Classifier
  target: band (0=Dream, 1=Target, 2=Safe)  [multiclass]
  — or —
XGBoost Regressor per (college, program, category, gender)
  target: predicted_closing_rank  → derive band from margin thresholds
      │
      ▼
SHAP TreeExplainer → top-3 feature importances per prediction
      │
      ▼
Prediction Response with band, probability, shap_factors, data_year
```

**Decision:** Use a per-row closing-rank regression model rather than a classifier. This gives a continuous predicted closing rank from which Safe/Target/Dream bands are derived using configurable margin percentages. Reason: more interpretable for end users ("your rank of 5000 is well inside the predicted closing rank of 7500").

### Band Thresholds (configurable via env vars)
```
SAFE_MARGIN_PERCENT = 20   # student_rank ≥ predicted_closing_rank * 1.20
TARGET_MARGIN_PERCENT = 10 # within ±10% of predicted_closing_rank
DREAM_MARGIN_PERCENT = 10  # student_rank < predicted_closing_rank * 0.90
```

## Feature Engineering Details

```python
# Input features for the model
features = [
    "rank_percentile",         # normalised rank
    "category_encoded",        # ordinal
    "gender_encoded",
    "exam_type_encoded",       # AP=0, TS=1, JEE=2
    "college_tier",            # 1–5 computed from historical avg rank
    "branch_demand_3yr_trend", # slope of closing rank over 3 years (negative = more competitive)
    "college_seat_intake",     # total seats for the program
    "is_government",           # boolean
]
```

## Training Pipeline

File: `backend/app/ml/training/train_predictor.py`

```
1. Load cutoff_records from DB (or CSV snapshot)
2. Filter: only rows with both opening_rank and closing_rank
3. Feature engineering (sklearn Pipeline)
4. Year-stratified split: train 2019-2022, val 2023, test 2024
5. Train XGBoostRegressor (one model per exam_type × gender)
   — or single model with exam/gender as features (chosen for lower complexity)
6. Evaluate: MAE, RMSE, accuracy of band assignment
7. Fairness check: accuracy per category
8. SHAP explainer fit
9. Log to MLflow: params, metrics, artifacts (model.pkl, shap_explainer.pkl, model_card.md)
10. Register model version in MLflow Model Registry
```

## Serving

File: `backend/app/ml/serving/predictor.py`

```python
class CollegePredictor:
    def load_model(version: str = "latest") -> None: ...
    def predict(request: PredictRequest) -> list[PredictionResult]: ...
```

Model loaded at startup via FastAPI lifespan; cached in memory. Reloaded on new version registration (Celery task signals via Redis pub/sub).

## API Contract

```
POST /api/v1/predict/colleges
Auth: Bearer (student)
Body: {
  exam_type: "AP_EAPCET",
  rank: 5000,
  category: "OC",
  gender: "male",
  filters: {
    branches: ["CSE", "ECE"],       // optional
    districts: ["Hyderabad"],       // optional
    college_types: ["government"],  // optional
    max_annual_fee: 150000          // optional
  }
}
Response: {
  predictions: [{
    college_id, college_name, branch_code, branch_name,
    band: "Safe" | "Target" | "Dream",
    probability: 0.87,
    predicted_closing_rank: 7500,
    data_year: 2024,
    shap_factors: [
      { feature: "rank_percentile", direction: "positive", contribution: 0.32 },
      { feature: "college_tier",    direction: "negative", contribution: -0.15 },
      { feature: "branch_demand",   direction: "negative", contribution: -0.12 }
    ],
    disclaimer: "Estimate, not a guarantee."
  }],
  model_version: "v2.1",
  data_year_range: "2019–2024"
}

GET /api/v1/predict/branches
Auth: Bearer (student)
Query: exam_type, rank, category, gender
Response: [{branch_code, branch_name, avg_closing_rank, band}]  -- simplified for branch comparison

POST /api/v1/admin/ml/retrain
Auth: Bearer (admin)
Body: { exam_type: "AP_EAPCET" | "all" }
202: { job_id }

GET /api/v1/admin/ml/models
Auth: Bearer (admin)
200: [{ version, exam_type, trained_at, accuracy, ece, metrics_by_category }]
```

## Database Additions

### `ml_model_versions` table
```sql
id              UUID PK
exam_type       VARCHAR(20)
version         VARCHAR(20)
mlflow_run_id   VARCHAR(100)
accuracy        NUMERIC(5,4)
ece             NUMERIC(5,4)
metrics_json    JSONB  -- per-category accuracy, fairness
is_active       BOOLEAN DEFAULT false
trained_at      TIMESTAMPTZ
artifact_path   TEXT
created_at      TIMESTAMPTZ DEFAULT now()
```

## Model Card (template)
Location: `backend/app/ml/model_cards/predictor_v{n}.md`
Sections: training data, feature list, training date, metrics, fairness analysis, known limitations, version changelog.

## Test Strategy
- `test_feature_engineering.py` — feature computation with known inputs
- `test_predictor_bands.py` — band assignment logic for edge cases
- `test_predict_endpoint.py` — API contract, auth, filters, disclaimer present
- `test_model_metrics.py` — loaded model meets accuracy/calibration thresholds (skipped if no trained model)
- `test_fairness.py` — per-category accuracy parity check
