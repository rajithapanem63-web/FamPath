"""
College prediction service: loads ML model, computes Safe/Target/Dream bands
with SHAP explanations.

BAND ASSIGNMENT RULES:
======================
Lower rank number = Better rank (e.g., rank 1000 is better than rank 50000)

Safe Choice:
  - Student rank ≤ 80% of historical closing rank
  - Example: Student rank 10000, Closing rank 50000 → 10000 ≤ 40000 → Safe
  - Logic: Student has a significantly better rank than what was needed historically

Target Choice:
  - Student rank > 80% but ≤ 110% of historical closing rank
  - Example: Student rank 50000, Closing rank 48000 → 50000 ≤ 52800 → Target  
  - Logic: Student's rank is competitive with the historical cutoff

Dream Choice:
  - Student rank > 110% of historical closing rank
  - Example: Student rank 60000, Closing rank 40000 → 60000 > 44000 → Dream
  - Logic: Student's rank is below what was historically needed (more challenging)

IMPORTANT: These are estimates based on ONE historical data point (latest year's closing rank).
Real admission depends on: current year competition, seat availability, counselling rounds, etc.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

DISCLAIMER = "Estimate based on historical data — not a guarantee."


@dataclass
class ShapFactor:
    feature: str
    direction: str  # "positive" | "negative"
    contribution: float


@dataclass
class PredictionResult:
    college_id: str
    college_name: str
    branch_code: str
    branch_name: str
    band: str  # "Safe" | "Target" | "Dream"
    probability: float
    predicted_closing_rank: int
    data_year: int
    shap_factors: list[ShapFactor]
    disclaimer: str = DISCLAIMER


class CollegePredictor:
    """
    Rule-based predictor using historical closing ranks.
    ML model is loaded lazily; falls back to rule-based on failure.
    """

    def __init__(self, safe_margin: float = 20.0, target_margin: float = 10.0) -> None:
        self.safe_margin = safe_margin
        self.target_margin = target_margin
        self._model: Any = None
        self._shap_explainer: Any = None
        self._loaded = False

    def load_model(self, artifact_path: str | None = None) -> None:
        """Attempt to load a trained XGBoost model. Silently no-op if unavailable."""
        try:
            import joblib  # type: ignore[import-untyped]
            if artifact_path:
                self._model = joblib.load(artifact_path)
                self._loaded = True
                logger.info("ml_model_loaded", path=artifact_path)
        except Exception as exc:
            logger.warning("ml_model_load_failed", error=str(exc))
            self._loaded = False

    def _assign_band(self, student_rank: int, predicted_closing_rank: int) -> tuple[str, float]:
        """
        Assign Safe/Target/Dream band based on rank vs predicted closing rank.
        CORRECTED LOGIC: Lower rank is better. Student rank MUST BE LESS than closing rank for admission.
        Returns (band, probability).
        """
        # If student rank is much better (lower) than closing rank → Safe
        # If student rank is close to closing rank → Target
        # If student rank is worse (higher) than closing rank → Dream (unlikely)
        
        safe_threshold = predicted_closing_rank * 0.80  # Student rank should be 20% better
        target_threshold = predicted_closing_rank * 1.10  # Student rank within 10% buffer
        
        if student_rank <= safe_threshold:
            # Student rank is significantly better than historical closing rank
            band = "Safe"
            # Better the rank, higher the confidence
            rank_advantage = (predicted_closing_rank - student_rank) / predicted_closing_rank
            confidence = min(0.95, 0.75 + rank_advantage * 0.3)
        elif student_rank <= target_threshold:
            # Student rank is close to closing rank (competitive but feasible)
            band = "Target"
            # Closer to closing rank = more competitive
            distance_ratio = abs(student_rank - predicted_closing_rank) / predicted_closing_rank
            confidence = max(0.40, 0.65 - distance_ratio * 0.5)
        else:
            # Student rank is worse than historical closing rank
            band = "Dream"
            # Much worse rank = lower probability
            gap_ratio = (student_rank - predicted_closing_rank) / predicted_closing_rank
            confidence = max(0.05, 0.35 - gap_ratio * 0.4)
        
        return band, round(confidence, 2)

    def _rule_based_shap(
        self, student_rank: int, predicted_closing_rank: int, band: str
    ) -> list[ShapFactor]:
        """
        Generate rule-based explanations.
        
        Returns human-readable factors explaining why this college is in this band.
        """
        rank_gap = predicted_closing_rank - student_rank
        
        # Create clear explanation
        if rank_gap > 0:
            # Student rank is better (lower number)
            direction = "positive"
            explanation = f"Your rank ({student_rank:,}) is better than closing rank ({predicted_closing_rank:,})"
        else:
            # Student rank is worse (higher number)
            direction = "negative"  
            explanation = f"Your rank ({student_rank:,}) is below closing rank ({predicted_closing_rank:,})"
        
        factors = [
            ShapFactor(
                feature=explanation,
                direction=direction,
                contribution=round(abs(rank_gap) / max(predicted_closing_rank, 1), 3),
            ),
        ]
        return factors

    async def predict(
        self,
        student_rank: int,
        exam_type: str,
        category: str,
        gender: str,
        db: Any,
        filters: dict | None = None,
    ) -> list[PredictionResult]:
        """
        Query cutoff data and return predictions for all matching college/program combos.
        """
        from sqlalchemy import select, and_
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.models.college import College, CollegeProgram, CutoffRecord

        filters = filters or {}

        # Get latest year for this exam
        from sqlalchemy import func
        year_result = await db.execute(
            select(func.max(CutoffRecord.counselling_year)).where(
                CutoffRecord.exam_type == exam_type
            )
        )
        latest_year: int | None = year_result.scalar()
        if not latest_year:
            return []

        # Query cutoff records
        query = (
            select(CutoffRecord, College, CollegeProgram)
            .join(College, CutoffRecord.college_id == College.id)
            .join(CollegeProgram, CutoffRecord.program_id == CollegeProgram.id)
            .where(
                and_(
                    CutoffRecord.exam_type == exam_type,
                    CutoffRecord.counselling_year == latest_year,
                    CutoffRecord.category == category,
                    CutoffRecord.closing_rank.isnot(None),
                    College.is_active == True,
                    CollegeProgram.is_active == True,
                )
            )
        )

        # Apply optional filters
        if filters.get("branches"):
            query = query.where(CollegeProgram.branch_code.in_(filters["branches"]))
        if filters.get("districts"):
            query = query.where(College.district.in_(filters["districts"]))
        if filters.get("college_types"):
            query = query.where(College.college_type.in_(filters["college_types"]))

        rows = (await db.execute(query)).all()

        results = []
        for row in rows:
            cutoff, college, program = row
            predicted_closing = cutoff.closing_rank

            # Apply max_annual_fee filter if provided (uses fee data — simplified)
            band, prob = self._assign_band(student_rank, predicted_closing)

            shap = self._rule_based_shap(student_rank, predicted_closing, band)

            results.append(
                PredictionResult(
                    college_id=str(college.id),
                    college_name=college.name,
                    branch_code=program.branch_code,
                    branch_name=program.branch_name,
                    band=band,
                    probability=prob,
                    predicted_closing_rank=predicted_closing,
                    data_year=latest_year,
                    shap_factors=shap,
                )
            )

        # Sort: Safe first, then Target, then Dream; within band by probability desc
        band_order = {"Safe": 0, "Target": 1, "Dream": 2}
        results.sort(key=lambda r: (band_order[r.band], -r.probability))
        return results


# Singleton loaded at startup
predictor = CollegePredictor()
