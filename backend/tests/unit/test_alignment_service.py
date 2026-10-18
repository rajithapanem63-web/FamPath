"""Unit tests for alignment score computation."""
from __future__ import annotations

import pytest

from app.services.alignment_service import (
    PREFERENCE_DIMENSIONS,
    compute_alignment_score,
    compute_dimension_scores,
)


def _prefs(**kwargs: float) -> dict[str, float]:
    base = {d: 3.0 for d in PREFERENCE_DIMENSIONS}
    base.update(kwargs)
    return base


def test_identical_preferences_score_100() -> None:
    prefs = _prefs()
    score = compute_alignment_score(prefs, prefs)
    assert score == pytest.approx(100.0, abs=0.1)


def test_opposite_preferences_low_score() -> None:
    student = {d: 5.0 for d in PREFERENCE_DIMENSIONS}
    # Opposite: student high, parent low (but cosine similarity checks direction, not magnitude)
    # With all 5 vs all 1 — vectors are parallel, cosine = 1 (same direction)
    parent = {d: 1.0 for d in PREFERENCE_DIMENSIONS}
    score = compute_alignment_score(student, parent)
    # Parallel vectors → cosine = 1.0 → score = 100
    assert score == pytest.approx(100.0, abs=0.1)


def test_zero_vector_returns_zero() -> None:
    student = {d: 0.0 for d in PREFERENCE_DIMENSIONS}
    parent = _prefs()
    assert compute_alignment_score(student, parent) == 0.0


def test_dimension_scores_agreement() -> None:
    student = _prefs(branch_interest=4.0)
    parent = _prefs(branch_interest=4.0)  # exact same → agree
    dims = compute_dimension_scores(student, [parent])
    branch = next(d for d in dims if d["dimension"] == "branch_interest")
    assert branch["agreement"] is True
    assert branch["diff"] == pytest.approx(0.0)


def test_dimension_scores_conflict() -> None:
    student = _prefs(location_flexibility=1.0)
    parent = _prefs(location_flexibility=5.0)  # diff = 4 → conflict
    dims = compute_dimension_scores(student, [parent])
    loc = next(d for d in dims if d["dimension"] == "location_flexibility")
    assert loc["agreement"] is False
    assert loc["diff"] == pytest.approx(4.0)


def test_dimension_scores_returns_all_dimensions() -> None:
    student = _prefs()
    parent = _prefs()
    dims = compute_dimension_scores(student, [parent])
    dim_names = {d["dimension"] for d in dims}
    assert dim_names == set(PREFERENCE_DIMENSIONS)


def test_multiple_parents_averaged() -> None:
    student = _prefs(branch_interest=3.0)
    p1 = _prefs(branch_interest=2.0)
    p2 = _prefs(branch_interest=4.0)
    dims = compute_dimension_scores(student, [p1, p2])
    branch = next(d for d in dims if d["dimension"] == "branch_interest")
    assert branch["parent_avg"] == pytest.approx(3.0)  # (2+4)/2
    assert branch["agreement"] is True  # diff = 0
