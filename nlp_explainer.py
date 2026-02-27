"""
nlp_explainer.py
----------------
Feature 19: AI Natural Language Explanation Generator

Produces human-readable, insurance-grade explanation text covering:
  - Per-part damage assessment
  - Cost reasoning
  - Claim decision justification
  - Overall summary

Fully rule-based — no external API or LLM required.
Works 100% offline for hackathon demo.
"""

from typing import List, Dict, Any

from cost_engine import CostEstimateResult
from decision_engine import ClaimDecision


# ──────────────────────────────────────────────────────────────────────────────
# Sentence templates
# ──────────────────────────────────────────────────────────────────────────────

_SEVERITY_OPENERS = {
    "Minor": [
        "shows superficial damage",
        "has minor surface abrasions",
        "exhibits light impact marks",
    ],
    "Moderate": [
        "has sustained notable damage",
        "shows significant deformation",
        "exhibits moderate structural impact",
    ],
    "Severe": [
        "has sustained severe structural damage",
        "shows critical deformation requiring immediate attention",
        "exhibits extensive damage consistent with high-impact collision",
    ],
}

_AREA_DESCRIPTORS = {
    "Minor":    "a small portion",
    "Moderate": "a notable portion",
    "Severe":   "a large portion",
}

_REPAIR_PHRASES = {
    "Repair":  "Targeted repair work — including panel beating and repainting — is sufficient.",
    "Replace": "Due to the extent of damage, full part replacement is the recommended course of action.",
}

_DECISION_EXPLANATIONS = {
    "Auto Approved": (
        "The total estimated cost falls within the auto-approval threshold. "
        "This claim can be processed and disbursed without manual intervention, "
        "reducing settlement time and administrative overhead."
    ),
    "Supervisor Review": (
        "The claim value exceeds the auto-approval limit but remains within manageable bounds. "
        "A supervisor review is required to validate the damage assessment "
        "before funds are released."
    ),
    "Manual Inspection": (
        "The claim value is high enough to warrant a physical on-site inspection. "
        "A certified insurance assessor must verify the damage before approval. "
        "This ensures the accuracy of the estimate and prevents fraudulent claims."
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_explanation(
    estimate:    CostEstimateResult,
    decision:    ClaimDecision,
    detections:  List[Dict[str, Any]],
) -> str:
    """
    Generate a structured natural language explanation of the claim analysis.

    Parameters
    ----------
    estimate   : CostEstimateResult from cost_engine
    decision   : ClaimDecision from decision_engine
    detections : aggregated detection list (each dict with part_name, severity, confidence)

    Returns
    -------
    Multi-paragraph explanation string (plain text with section headers).
    """
    lines: List[str] = []

    # ── Section 1: Damage Assessment ─────────────────────────────────────────
    lines.append("📋 DAMAGE ASSESSMENT")
    lines.append("─" * 48)

    for i, det in enumerate(detections):
        part     = det["part_name"].capitalize()
        sev_obj  = det["severity"]
        sev      = sev_obj.label
        ratio    = sev_obj.area_ratio
        conf     = det["confidence"]
        n_imgs   = det.get("image_count", 1)

        # Choose opener based on severity (cycle through templates)
        opener = _SEVERITY_OPENERS[sev][i % len(_SEVERITY_OPENERS[sev])]
        area_desc = _AREA_DESCRIPTORS[sev]

        img_note = (
            f" (detected across {n_imgs} image{'s' if n_imgs > 1 else ''})"
            if n_imgs > 1 else ""
        )

        lines.append(
            f"• {part}: The {part.lower()} {opener}, covering approximately "
            f"{ratio:.0%} of the inspected surface area — classified as {sev} damage "
            f"with a detection confidence of {conf:.0%}{img_note}. "
            f"{_REPAIR_PHRASES.get(_get_rec(sev, ratio), _REPAIR_PHRASES['Repair'])}"
        )

    lines.append("")

    # ── Section 2: Cost Reasoning ─────────────────────────────────────────────
    lines.append("💰 COST REASONING")
    lines.append("─" * 48)

    for part in estimate.parts:
        multiplier_pct = int((part.repair_cost / part.base_cost) * 100)
        lines.append(
            f"• {part.part_name.capitalize()} ({part.severity_label}): "
            f"Base replacement cost ₹{part.base_cost:,.0f} × {multiplier_pct}% severity factor "
            f"= ₹{part.repair_cost:,.0f} repair cost + ₹{part.labor_cost:,.0f} labor "
            f"= ₹{part.total_cost:,.0f} total."
        )

    lines.append(
        f"\nThe aggregate repair subtotal is ₹{estimate.subtotal:,.0f} with total labor "
        f"charges of ₹{estimate.total_labor:,.0f}, bringing the grand total estimate "
        f"to ₹{estimate.grand_total:,.0f}."
    )
    lines.append("")

    # ── Section 3: Claim Decision Justification ───────────────────────────────
    lines.append("⚖️ CLAIM DECISION JUSTIFICATION")
    lines.append("─" * 48)

    # Determine decision key
    dec_key = "Auto Approved"
    if "Supervisor" in decision.status:
        dec_key = "Supervisor Review"
    elif "Manual" in decision.status:
        dec_key = "Manual Inspection"

    lines.append(f"Decision: {decision.status}")
    lines.append("")
    lines.append(_DECISION_EXPLANATIONS.get(dec_key, decision.description))

    if getattr(decision, "low_confidence_flag", False):
        lines.append(
            "\n⚠️ Note: One or more detections had confidence below 60%. "
            "The claim decision has been escalated to Manual Inspection as a responsible AI safeguard."
        )

    lines.append("")

    # ── Section 4: Summary ────────────────────────────────────────────────────
    lines.append("📝 SUMMARY")
    lines.append("─" * 48)

    part_list = ", ".join(p.part_name.capitalize() for p in estimate.parts)
    severe_parts = [p for p in estimate.parts if p.severity_label == "Severe"]
    severity_note = (
        f"Of these, {len(severe_parts)} part(s) — "
        f"{', '.join(p.part_name.capitalize() for p in severe_parts)} — "
        "require full replacement due to severe damage."
        if severe_parts else
        "No parts require full replacement; all damage can be repaired."
    )

    lines.append(
        f"The AI inspection identified damage to {len(estimate.parts)} vehicle component(s): "
        f"{part_list}. {severity_note} "
        f"The total estimated repair cost of ₹{estimate.grand_total:,.0f} has been reviewed "
        f"against the insurer's approval thresholds, resulting in the decision: {decision.status}."
    )

    return "\n".join(lines)


def _get_rec(severity: str, area_ratio: float) -> str:
    """Internal helper: determine Repair/Replace for sentence construction."""
    if severity == "Severe" or area_ratio >= 0.30:
        return "Replace"
    return "Repair"
