"""
cost_engine.py
--------------
Features 14 + 15: Car Type-Based Pricing + Dynamic Cost Adjustment Engine

Cost formula per part:
  repair_cost  = base_cost × severity_multiplier × car_type_multiplier × inflation_factor
  labor_cost   = FIXED_LABOR_COST × car_type_multiplier
  total_cost   = repair_cost + labor_cost

Car type multipliers:
  Hatchback → 1.0x   (base)
  Sedan     → 1.1x
  SUV       → 1.3x
  Luxury    → 1.8x

Inflation factor: 1.05 (5% applied globally to reflect current parts market)
"""

from dataclasses import dataclass, field
from typing import List

from database import get_part_cost, FIXED_LABOR_COST
from severity import get_cost_multiplier

# ── Car Type Multipliers (Feature 14) ─────────────────────────────────────────
CAR_TYPE_MULTIPLIERS: dict = {
    "Hatchback": 1.0,
    "Sedan":     1.1,
    "SUV":       1.3,
    "Luxury":    1.8,
}

# ── Inflation / Market Adjustment Factor (Feature 15) ─────────────────────────
INFLATION_FACTOR: float = 1.05  # 5% adjustment for current parts market
COST_DISCOUNT:    float = 0.75  # 25% reduction applied to repair + labor costs


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PartEstimate:
    part_name:          str
    severity_label:     str
    severity_score:     int
    base_cost:          float
    repair_cost:        float    # base × severity_mult × car_mult × inflation
    labor_cost:         float    # fixed × car_mult
    total_cost:         float    # repair + labor
    confidence:         float
    bbox:               tuple
    car_type_mult:      float    # applied car type multiplier
    action:             str      # "Repair" or "Replace" (from repair_recommender)
    justification:      str      # repair/replace reason text


@dataclass
class CostEstimateResult:
    parts:           List[PartEstimate] = field(default_factory=list)
    subtotal:        float = 0.0
    total_labor:     float = 0.0
    grand_total:     float = 0.0
    car_type:        str   = "Sedan"
    inflation_factor:float = INFLATION_FACTOR


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def estimate_costs(detections: list, car_type: str = "Sedan") -> CostEstimateResult:
    """
    Calculate repair costs for a list of (aggregated) damage detections.

    Parameters
    ----------
    detections : list of dicts from aggregator.py / detection.py, each containing:
        { "part_name", "confidence", "bbox", "severity", "action", "justification" }
    car_type   : one of "Hatchback", "Sedan", "SUV", "Luxury"

    Returns
    -------
    CostEstimateResult with per-part breakdown and totals.
    """
    car_mult = CAR_TYPE_MULTIPLIERS.get(car_type, 1.0)
    result   = CostEstimateResult(car_type=car_type, inflation_factor=INFLATION_FACTOR)

    for det in detections:
        part_name      = det["part_name"].lower()
        severity       = det["severity"]
        confidence     = det["confidence"]
        bbox           = det["bbox"]
        action         = det.get("action", "Repair")
        justification  = det.get("justification", "")

        base_cost      = get_part_cost(part_name)
        sev_mult       = get_cost_multiplier(severity.label)
        repair_cost    = base_cost * sev_mult * car_mult * INFLATION_FACTOR * COST_DISCOUNT
        labor_cost     = float(FIXED_LABOR_COST) * car_mult * COST_DISCOUNT
        total_cost     = repair_cost + labor_cost

        part_est = PartEstimate(
            part_name      = part_name,
            severity_label = severity.label,
            severity_score = severity.score,
            base_cost      = base_cost,
            repair_cost    = repair_cost,
            labor_cost     = labor_cost,
            total_cost     = total_cost,
            confidence     = confidence,
            bbox           = bbox,
            car_type_mult  = car_mult,
            action         = action,
            justification  = justification,
        )
        result.parts.append(part_est)
        result.subtotal    += repair_cost
        result.total_labor += labor_cost

    result.grand_total = result.subtotal + result.total_labor
    return result
