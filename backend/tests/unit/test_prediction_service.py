"""Unit tests for college predictor band assignment logic."""
from __future__ import annotations

import pytest

from app.services.prediction_service import CollegePredictor


@pytest.fixture
def predictor() -> CollegePredictor:
    return CollegePredictor(safe_margin=20.0, target_margin=10.0)


def test_safe_band_when_rank_well_above_closing(predictor: CollegePredictor) -> None:
    """Rank 9000 vs closing rank 7000 → rank > 7000 * 1.2 = 8400 → Safe"""
    band, prob = predictor._assign_band(9000, 7000)
    assert band == "Safe"
    assert 0.75 <= prob <= 0.95


def test_dream_band_when_rank_far_below_closing(predictor: CollegePredictor) -> None:
    """Rank 3000 vs closing rank 7000 → rank < 7000 * 0.9 = 6300 → Dream"""
    band, prob = predictor._assign_band(3000, 7000)
    assert band == "Dream"
    assert 0.10 <= prob <= 0.45


def test_target_band_within_window(predictor: CollegePredictor) -> None:
    """Rank 7100 vs closing rank 7000 → within ±10% → Target"""
    band, prob = predictor._assign_band(7100, 7000)
    assert band == "Target"
    assert 0.40 <= prob <= 0.65


def test_safe_band_exactly_at_threshold(predictor: CollegePredictor) -> None:
    """Rank exactly at 1.2 × closing rank"""
    closing = 5000
    student = int(closing * 1.2)  # = 6000
    band, _ = predictor._assign_band(student, closing)
    assert band in ("Safe", "Target")  # boundary


def test_probability_between_0_and_1(predictor: CollegePredictor) -> None:
    for student_rank in [1000, 5000, 7000, 9000, 15000]:
        _, prob = predictor._assign_band(student_rank, 7000)
        assert 0.0 <= prob <= 1.0


def test_shap_factors_returned(predictor: CollegePredictor) -> None:
    factors = predictor._rule_based_shap(9000, 7000, "Safe")
    assert len(factors) >= 1
    for f in factors:
        assert f.direction in ("positive", "negative")
        assert 0.0 <= f.contribution <= 1.0


def test_band_order_safe_first() -> None:
    """Safe should always sort before Dream."""
    p = CollegePredictor()
    from app.services.prediction_service import PredictionResult, ShapFactor
    results = [
        PredictionResult("a", "A", "CSE", "Computer Science", "Dream", 0.2, 5000, 2024, []),
        PredictionResult("b", "B", "ECE", "Electronics", "Safe", 0.9, 9000, 2024, []),
        PredictionResult("c", "C", "MECH", "Mechanical", "Target", 0.55, 7000, 2024, []),
    ]
    band_order = {"Safe": 0, "Target": 1, "Dream": 2}
    results.sort(key=lambda r: (band_order[r.band], -r.probability))
    assert results[0].band == "Safe"
    assert results[-1].band == "Dream"
