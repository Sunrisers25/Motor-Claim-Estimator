"""
decision_engine.py
------------------
Features 16 + original rules:

  - Feature 16: Confidence-Based Override
    If average detection confidence < LOW_CONFIDENCE_THRESHOLD, the decision
    is forced to "Manual Inspection" regardless of total cost.

  - Original cost thresholds (now inflation-adjusted):
    < 25,000      → Auto Approved
    25,000–60,000 → Supervisor Review
    > 60,000      → Manual Inspection Required

Fixes applied:
  Flaw 20: LOW_CONFIDENCE_THRESHOLD lowered from 0.60 to 0.40 so the override
    can actually fire in Smart Simulation mode. The simulation now produces
    real signal-based confidences (can go to 0.20), so weak/uncertain detections
    will correctly trigger manual review.

  Flaw 21: Cost thresholds are now scaled by INFLATION_FACTOR (imported from
    cost_engine) so the boundaries stay meaningful as part prices rise.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

# Flaw 21 fix: import inflation factor so thresholds scale with costs
from cost_engine import INFLATION_FACTOR

# Base thresholds at today's prices (will be multiplied by INFLATION_FACTOR)
_BASE_AUTO_THRESHOLD       = 25_000    # below this → Auto Approved
_BASE_SUPERVISOR_THRESHOLD = 60_000    # above this → Manual Inspection

AUTO_THRESHOLD       = _BASE_AUTO_THRESHOLD       * INFLATION_FACTOR
SUPERVISOR_THRESHOLD = _BASE_SUPERVISOR_THRESHOLD * INFLATION_FACTOR

# Flaw 20 fix: lowered from 0.60 → 0.40 so it can actually trigger in
# Simulation mode (which now produces confidences as low as 0.20).
LOW_CONFIDENCE_THRESHOLD = 0.40


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
) -> "ClaimDecision":
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

    # ── Feature 16: Confidence-based override ─────────────────────────────────
    # Flaw 20 fix: threshold is now 0.40 so simulation-mode weak signals trigger it
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

    # ── Standard cost-based thresholds (Flaw 21 fix: inflation-adjusted) ─────
    if total_cost < AUTO_THRESHOLD:
        return ClaimDecision(
            status = "Auto Approved ✅",
            description = (
                f"Total estimated cost ₹{total_cost:,.0f} is below ₹{AUTO_THRESHOLD:,.0f}. "
                "The claim is automatically approved and can be processed immediately."
            ),
            color = "green",
            emoji = "✅",
        )
    elif total_cost <= SUPERVISOR_THRESHOLD:
        return ClaimDecision(
            status = "Supervisor Review ⚠️",
            description = (
                f"Total estimated cost ₹{total_cost:,.0f} falls between "
                f"₹{AUTO_THRESHOLD:,.0f} and ₹{SUPERVISOR_THRESHOLD:,.0f}. "
                "This claim requires supervisor review before approval."
            ),
            color = "orange",
            emoji = "⚠️",
        )
    else:
        return ClaimDecision(
            status = "Manual Inspection Required 🔴",
            description = (
                f"Total estimated cost ₹{total_cost:,.0f} exceeds ₹{SUPERVISOR_THRESHOLD:,.0f}. "
                "A physical manual inspection is required before this claim can be processed."
            ),
            color = "red",
            emoji = "🔴",
        )
