"""
Aptitude and branch-fit service: RIASEC scoring and branch fit computation.
All functions are pure (no I/O) for easy testing.
"""
from __future__ import annotations

from dataclasses import dataclass

# RIASEC dimension abbreviations
DIMENSIONS = ["R", "I", "A", "S", "E", "C"]

# Branch → RIASEC weights: {branch_code: {dimension: weight}}
BRANCH_RIASEC_WEIGHTS: dict[str, dict[str, float]] = {
    "CSE":   {"I": 0.6, "C": 0.4},
    "IT":    {"I": 0.6, "C": 0.4},
    "ECE":   {"I": 0.55, "R": 0.45},
    "EEE":   {"I": 0.5, "R": 0.5},
    "MECH":  {"R": 0.6, "I": 0.4},
    "CIVIL": {"R": 0.55, "C": 0.45},
    "CHEM":  {"I": 0.6, "R": 0.4},
    "BIO":   {"I": 0.5, "A": 0.3, "S": 0.2},
    "ARCH":  {"A": 0.5, "R": 0.3, "I": 0.2},
    "MBA":   {"E": 0.5, "S": 0.3, "C": 0.2},
}


@dataclass
class BranchFitResult:
    branch_code: str
    score: float  # 0–100
    top_drivers: list[str]  # RIASEC dimensions driving the score


def compute_riasec_scores(
    responses: list[dict],  # [{question_id, riasec_dimension, response_value, weight}]
) -> dict[str, float]:
    """
    Compute raw RIASEC scores (0–100) from quiz responses.

    Args:
        responses: list of dicts with riasec_dimension, response_value (1–5), weight

    Returns:
        dict mapping dimension (R/I/A/S/E/C) to normalised score 0–100
    """
    raw: dict[str, list[float]] = {d: [] for d in DIMENSIONS}

    for r in responses:
        dim = r["riasec_dimension"]
        if dim in raw:
            raw[dim].append(r["response_value"] * r.get("weight", 1.0))

    scores: dict[str, float] = {}
    for dim in DIMENSIONS:
        values = raw[dim]
        if not values:
            scores[dim] = 0.0
        else:
            # Max possible score per response = 5 * weight (assume weight=1 → max=5)
            max_possible = len(values) * 5.0
            scores[dim] = round(sum(values) / max_possible * 100, 1)

    return scores


def compute_branch_fit(riasec: dict[str, float]) -> list[BranchFitResult]:
    """
    Compute Branch Fit Score (0–100) for each known branch using RIASEC scores.

    Returns list sorted by score descending.
    """
    results: list[BranchFitResult] = []

    for branch_code, weights in BRANCH_RIASEC_WEIGHTS.items():
        total_weight = sum(weights.values())
        weighted_score = sum(
            riasec.get(dim, 0.0) * w for dim, w in weights.items()
        )
        score = round(weighted_score / total_weight, 1)

        # Top-2 drivers (dimensions with highest contribution)
        drivers = sorted(
            weights.keys(),
            key=lambda d: riasec.get(d, 0.0) * weights[d],
            reverse=True,
        )[:2]

        results.append(BranchFitResult(branch_code=branch_code, score=score, top_drivers=drivers))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def format_top_branches(results: list[BranchFitResult], top_n: int = 5) -> list[dict]:
    """Format top-N branch fit results for API response."""
    return [
        {
            "branch": r.branch_code,
            "score": r.score,
            "drivers": r.top_drivers,
        }
        for r in results[:top_n]
    ]
