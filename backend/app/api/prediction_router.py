"""College prediction API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_payload
from app.services.prediction_service import predictor

router = APIRouter(prefix="/predict", tags=["Prediction"])


class PredictionFilters(BaseModel):
    branches: list[str] | None = None
    districts: list[str] | None = None
    college_types: list[str] | None = None
    max_annual_fee: int | None = None


class CollegePredictRequest(BaseModel):
    exam_type: str = Field(pattern="^(AP_EAPCET|TS_EAPCET|JEE_MAINS|JEE_ADV)$")
    rank: int = Field(ge=1, le=500000)
    category: str = Field(pattern="^(OC|BC_A|BC_B|BC_C|BC_D|BC_E|SC|ST|EWS)$")
    gender: str = Field(default="any", pattern="^(male|female|other|any)$")
    filters: PredictionFilters = PredictionFilters()


class ShapFactorResponse(BaseModel):
    feature: str
    direction: str
    contribution: float


class CollegePredictionResponse(BaseModel):
    college_id: str
    college_name: str
    branch_code: str
    branch_name: str
    band: str
    probability: float
    predicted_closing_rank: int
    data_year: int
    shap_factors: list[ShapFactorResponse]
    disclaimer: str


class PredictResponse(BaseModel):
    predictions: list[CollegePredictionResponse]
    model_version: str
    data_year_range: str


@router.post("/colleges", response_model=PredictResponse, summary="Predict college admissions")
async def predict_colleges(
    data: CollegePredictRequest,
    db: AsyncSession = Depends(get_db),
    token=Depends(get_token_payload),
) -> PredictResponse:
    """
    Returns Safe/Target/Dream band predictions for all matching college/branch combinations.
    Every result includes SHAP explanations and the data source disclaimer.
    """
    filters = {
        "branches": data.filters.branches,
        "districts": data.filters.districts,
        "college_types": data.filters.college_types,
    }
    results = await predictor.predict(
        student_rank=data.rank,
        exam_type=data.exam_type,
        category=data.category,
        gender=data.gender,
        db=db,
        filters=filters,
    )

    predictions = [
        CollegePredictionResponse(
            college_id=r.college_id,
            college_name=r.college_name,
            branch_code=r.branch_code,
            branch_name=r.branch_name,
            band=r.band,
            probability=r.probability,
            predicted_closing_rank=r.predicted_closing_rank,
            data_year=r.data_year,
            shap_factors=[
                ShapFactorResponse(
                    feature=f.feature,
                    direction=f.direction,
                    contribution=f.contribution,
                )
                for f in r.shap_factors
            ],
            disclaimer=r.disclaimer,
        )
        for r in results
    ]

    return PredictResponse(
        predictions=predictions,
        model_version="rule-based-v1",
        data_year_range="historical",
    )
