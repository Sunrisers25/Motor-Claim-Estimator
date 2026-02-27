"""
decision_engine.py
------------------
Features 16 + original rules:

  - Feature 16: Confidence-Based Override
    If average detection confidence < 60%, the decision is forced to
    "Manual Inspection" regardless of total cost, flagging it as
    a responsible AI safeguard.

  - Original cost thresholds:
    < 25,000      → Auto Approved
    25,000–60,000 → Supervisor Review
    > 60,000      → Manual Inspection Required
"""

from dataclasses import dataclass
from typing import List, Dict, Any

# Threshold below which low-confidence claims are escalated (Feature 16)
LOW_CONFIDENCE_THRESHOLD = 0.60


@dataclass
class ClaimDecision:
    status:               str     # Short label
    description:          str     # Detailed explanation
    color:                str     # "green", "orange", or "red"
    emoji:                str
    low_confidence_flag:  bool = False   # Feature 16: AI override triggered


def decide_claim(
    total_cost:  float,
    detections:  List[Dict[str, Any]] = None,
) -> ClaimDecision:
    """
    Evaluate total repair cost (and optionally detection confidence) to
    return a structured ClaimDecision.

    Parameters
    ----------
    total_cost  : float — Grand total from cost_engine
    detections  : optional list of detection dicts; used for confidence check

    Returns
    -------
    ClaimDecision dataclass
    """
    detections = detections or []

    # ── Feature 16: Confidence-based override ────────────────────────────────
    if detections:
        avg_conf = sum(d.get("confidence", 1.0) for d in detections) / len(detections)
        if avg_conf < LOW_CONFIDENCE_THRESHOLD:
            return ClaimDecision(
                status = "Manual Inspection Required 🔴",
                description = (
                    f"⚠️ Responsible AI Override: The average detection confidence was "
                    f"{avg_conf:.0%}, which is below the {LOW_CONFIDENCE_THRESHOLD:.0%} threshold. "
                    f"Regardless of the cost estimate (₹{total_cost:,.0f}), this claim has been "
                    f"escalated for manual inspection to ensure accuracy and prevent underpayment."
                ),
                color               = "red",
                emoji               = "🔴",
                low_confidence_flag = True,
            )

    # ── Standard cost-based thresholds ───────────────────────────────────────
    if total_cost < 25_000:
        return ClaimDecision(
            status = "Auto Approved ✅",
            description = (
                f"Total estimated cost ₹{total_cost:,.0f} is below ₹25,000. "
                "The claim is automatically approved and can be processed immediately."
            ),
            color = "green",
            emoji = "✅",
        )
    elif total_cost <= 60_000:
        return ClaimDecision(
            status = "Supervisor Review ⚠️",
            description = (
                f"Total estimated cost ₹{total_cost:,.0f} falls between ₹25,000 and ₹60,000. "
                "This claim requires supervisor review before approval."
            ),
            color = "orange",
            emoji = "⚠️",
        )
    else:
        return ClaimDecision(
            status = "Manual Inspection Required 🔴",
            description = (
                f"Total estimated cost ₹{total_cost:,.0f} exceeds ₹60,000. "
                "A physical manual inspection is required before this claim can be processed."
            ),
            color = "red",
            emoji = "🔴",
        )
