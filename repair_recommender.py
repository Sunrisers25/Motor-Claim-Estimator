"""
repair_recommender.py
---------------------
Feature 11: Repair vs Replace Recommendation Engine

Decision rule:
  area_ratio < 0.30  → Repair   (damage is less than 30% of image area)
  area_ratio >= 0.30 → Replace  (damage covers 30%+ of image area)

Additionally factors in severity:
  - Minor   always → Repair
  - Severe  always → Replace
  - Moderate       → follows area_ratio rule
"""

from dataclasses import dataclass


@dataclass
class RepairRecommendation:
    action:        str    # "Repair" or "Replace"
    justification: str    # Natural language reasoning
    icon:          str    # emoji for UI


def recommend_action(
    part_name:  str,
    severity:   str,
    area_ratio: float,
) -> RepairRecommendation:
    """
    Recommend whether to repair or replace a damaged part.

    Parameters
    ----------
    part_name  : name of the damaged part (e.g. "bumper")
    severity   : "Minor", "Moderate", or "Severe"
    area_ratio : fraction of image covered by bounding box (0.0 – 1.0)

    Returns
    -------
    RepairRecommendation dataclass
    """
    part = part_name.capitalize()
    pct  = f"{area_ratio:.0%}"

    # ── Severity-based overrides ─────────────────────────────────────────────
    if severity == "Minor":
        return RepairRecommendation(
            action        = "Repair",
            justification = (
                f"{part} shows minor damage ({pct} of surface affected). "
                "Panel beating and touch-up painting are sufficient. Replacement is not required."
            ),
            icon = "🔧",
        )

    if severity == "Severe":
        return RepairRecommendation(
            action        = "Replace",
            justification = (
                f"{part} shows severe damage ({pct} of surface affected). "
                "The structural integrity is compromised; full replacement is mandatory "
                "to ensure vehicle safety."
            ),
            icon = "🔄",
        )

    # ── Moderate: use area_ratio threshold ───────────────────────────────────
    if area_ratio < 0.30:
        return RepairRecommendation(
            action        = "Repair",
            justification = (
                f"{part} damage area is {pct} — below the 30% replacement threshold. "
                "Repair with filler, sanding, and repainting is recommended."
            ),
            icon = "🔧",
        )
    else:
        return RepairRecommendation(
            action        = "Replace",
            justification = (
                f"{part} damage area is {pct} — exceeds the 30% replacement threshold. "
                "The extent of damage makes repair uneconomical; replacement is advised."
            ),
            icon = "🔄",
        )
