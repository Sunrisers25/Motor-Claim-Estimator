"""
severity.py
-----------
Classifies damage severity based on the bounding box area relative to
the total image area.

Severity levels:
  - Minor    → bbox area < 5% of image  → score 1-3
  - Moderate → bbox area 5-15%          → score 4-6
  - Severe   → bbox area > 15%          → score 7-10
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class SeverityResult:
    label: str        # "Minor", "Moderate", "Severe"
    score: int        # 1-10
    area_ratio: float # bbox / image area ratio (0.0 – 1.0)


def classify_severity(
    bbox: Tuple[int, int, int, int],
    image_width: int,
    image_height: int,
) -> SeverityResult:
    """
    Classify damage severity for a single detected bounding box.

    Parameters
    ----------
    bbox         : (x1, y1, x2, y2) in pixels
    image_width  : total width of the source image
    image_height : total height of the source image

    Returns
    -------
    SeverityResult with label, numeric score, and area ratio
    """
    x1, y1, x2, y2 = bbox
    box_area = abs((x2 - x1) * (y2 - y1))
    image_area = image_width * image_height

    if image_area == 0:
        return SeverityResult(label="Minor", score=1, area_ratio=0.0)

    ratio = box_area / image_area

    if ratio < 0.05:
        # Small bounding box → Minor
        score = max(1, int(ratio / 0.05 * 3))  # 1-3
        label = "Minor"
    elif ratio < 0.15:
        # Medium bounding box → Moderate
        normalized = (ratio - 0.05) / 0.10    # 0-1 within band
        score = 4 + int(normalized * 2)        # 4-6
        label = "Moderate"
    else:
        # Large bounding box → Severe
        normalized = min((ratio - 0.15) / 0.25, 1.0)
        score = 7 + int(normalized * 3)        # 7-10
        label = "Severe"

    score = max(1, min(score, 10))             # clamp to [1, 10]
    return SeverityResult(label=label, score=score, area_ratio=ratio)


def get_cost_multiplier(severity_label: str) -> float:
    """
    Return the fraction of base part cost to charge based on severity.

    Minor    → 40% of part cost
    Moderate → 70% of part cost
    Severe   → 100% (full replacement)
    """
    multipliers = {
        "Minor":    0.40,
        "Moderate": 0.70,
        "Severe":   1.00,
    }
    return multipliers.get(severity_label, 1.00)
