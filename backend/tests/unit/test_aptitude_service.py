"""Unit tests for RIASEC scoring and branch fit computation."""
from __future__ import annotations

import pytest

from app.services.aptitude_service import (
    BRANCH_RIASEC_WEIGHTS,
    compute_branch_fit,
    compute_riasec_scores,
    format_top_branches,
)


def _make_responses(dimension_values: dict[str, int]) -> list[dict]:
    """Build mock response list for given RIASEC dimension → score mapping."""
    responses = []
    for dim, value in dimension_values.items():
        responses.append({
            "question_id": f"q-{dim}",
            "riasec_dimension": dim,
            "response_value": value,
            "weight": 1.0,
        })
    return responses


def test_all_max_responses_score_100() -> None:
    responses = _make_responses({"R": 5, "I": 5, "A": 5, "S": 5, "E": 5, "C": 5})
    scores = compute_riasec_scores(responses)
    for dim in ["R", "I", "A", "S", "E", "C"]:
        assert scores[dim] == 100.0


def test_all_min_responses_score_20() -> None:
    """Minimum response of 1 on a 1–5 scale = 20%."""
    responses = _make_responses({"R": 1, "I": 1, "A": 1, "S": 1, "E": 1, "C": 1})
    scores = compute_riasec_scores(responses)
    for dim in ["R", "I", "A", "S", "E", "C"]:
        assert scores[dim] == pytest.approx(20.0, abs=1.0)


def test_empty_dimension_scores_zero() -> None:
    responses = _make_responses({"I": 5, "C": 5})  # Missing R, A, S, E
    scores = compute_riasec_scores(responses)
    assert scores["R"] == 0.0
    assert scores["A"] == 0.0
    assert scores["I"] == 100.0


def test_branch_fit_cse_high_for_investigative() -> None:
    """High Investigative and Conventional scores should give high CSE fit."""
    riasec = {"R": 0, "I": 100, "A": 0, "S": 0, "E": 0, "C": 100}
    results = compute_branch_fit(riasec)
    cse = next(r for r in results if r.branch_code == "CSE")
    assert cse.score == pytest.approx(100.0, abs=1.0)


def test_branch_fit_returns_all_branches() -> None:
    riasec = {d: 50.0 for d in ["R", "I", "A", "S", "E", "C"]}
    results = compute_branch_fit(riasec)
    branch_codes = {r.branch_code for r in results}
    assert "CSE" in branch_codes
    assert "MECH" in branch_codes
    assert "CIVIL" in branch_codes


def test_branch_fit_sorted_descending() -> None:
    riasec = {"R": 80, "I": 90, "A": 30, "S": 40, "E": 50, "C": 70}
    results = compute_branch_fit(riasec)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_format_top_branches_returns_n() -> None:
    riasec = {d: 60.0 for d in ["R", "I", "A", "S", "E", "C"]}
    results = compute_branch_fit(riasec)
    top3 = format_top_branches(results, top_n=3)
    assert len(top3) == 3
    for item in top3:
        assert "branch" in item
        assert "score" in item
        assert "drivers" in item


def test_branch_fit_drivers_are_riasec_dimensions() -> None:
    riasec = {d: 50.0 for d in ["R", "I", "A", "S", "E", "C"]}
    results = compute_branch_fit(riasec)
    valid_dims = {"R", "I", "A", "S", "E", "C"}
    for r in results:
        for driver in r.top_drivers:
            assert driver in valid_dims
