"""
Family alignment service: cosine similarity between preference vectors,
dimension-level agreement/conflict scoring.
"""
from __future__ import annotations

import math

PREFERENCE_DIMENSIONS = [
    "branch_interest",
    "location_flexibility",
    "budget_priority",
    "placement_focus",
    "higher_education",
    "job_stability",
    "startup_openness",
    "prestige_weight",
]


def compute_alignment_score(
    student_prefs: dict[str, float],
    parent_prefs: dict[str, float],
) -> float:
    """
    Compute family alignment score (0–100) as normalised cosine similarity
    between student and parent preference vectors.
    Returns 0.0 if either vector is zero.
    """
    dims = PREFERENCE_DIMENSIONS
    sv = [float(student_prefs.get(d, 0)) for d in dims]
    pv = [float(parent_prefs.get(d, 0)) for d in dims]

    dot = sum(a * b for a, b in zip(sv, pv))
    norm_s = math.sqrt(sum(a ** 2 for a in sv))
    norm_p = math.sqrt(sum(b ** 2 for b in pv))

    if norm_s == 0 or norm_p == 0:
        return 0.0

    cosine = dot / (norm_s * norm_p)
    return round(cosine * 100, 1)


def compute_dimension_scores(
    student_prefs: dict[str, float],
    parent_prefs_list: list[dict[str, float]],
) -> list[dict]:
    """
    Compute per-dimension agreement/conflict for student vs all parents.
    Returns list of {dimension, student_value, parent_avg, agreement, diff}.
    """
    results = []
    for dim in PREFERENCE_DIMENSIONS:
        sv = float(student_prefs.get(dim, 0))
        parent_values = [float(p.get(dim, 0)) for p in parent_prefs_list]
        parent_avg = sum(parent_values) / len(parent_values) if parent_values else 0.0
        diff = abs(sv - parent_avg)
        agreement = diff <= 1.0  # within 1 point on 1–5 scale = agree

        results.append({
            "dimension": dim,
            "student_value": sv,
            "parent_avg": round(parent_avg, 2),
            "agreement": agreement,
            "diff": round(diff, 2),
        })

    return results
