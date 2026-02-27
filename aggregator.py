"""
aggregator.py
-------------
Feature 10: Multi-Image Aggregation

When multiple images of the same vehicle are uploaded, this module:
  1. Deduplicates detections by part name (keeps the highest-confidence
     detection when the same part appears in more than one image)
  2. Averages area ratios across all detections of the same part
  3. Recalculates severity based on the averaged area ratio
  4. Returns a clean list of unique part detections ready for cost estimation
"""

from typing import List, Dict, Any
from collections import defaultdict

from severity import classify_severity, SeverityResult


def aggregate_detections(all_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge detections from multiple images of the same vehicle.

    Strategy per part:
      - confidence   → take the MAXIMUM (most certain reading)
      - area_ratio   → AVERAGE (representative view of actual damage size)
      - severity     → RE-CLASSIFY from averaged area_ratio
      - bbox         → keep the one with the highest confidence
      - image_count  → count how many images the part appeared in

    Parameters
    ----------
    all_detections : flat list of detection dicts from detect_damage()

    Returns
    -------
    Deduplicated, aggregated list of detection dicts (one per unique part).
    Each dict contains an extra key `image_count` (int).
    """
    if not all_detections:
        return []

    # Group by part name
    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for det in all_detections:
        grouped[det["part_name"].lower()].append(det)

    aggregated: List[Dict[str, Any]] = []

    for part_name, dets in grouped.items():
        # Best confidence detection (used for bbox)
        best = max(dets, key=lambda d: d["confidence"])

        # Average area_ratio across all appearances
        avg_area_ratio = sum(d["severity"].area_ratio for d in dets) / len(dets)

        # Average confidence
        avg_confidence = sum(d["confidence"] for d in dets) / len(dets)

        # Re-derive severity from averaged area_ratio using existing thresholds
        # We adapt severity manually here since classify_severity needs a bbox + image dims
        avg_severity = _severity_from_ratio(avg_area_ratio, part_name)

        aggregated.append({
            "part_name":   part_name,
            "confidence":  round(avg_confidence, 3),
            "bbox":        best["bbox"],
            "severity":    avg_severity,
            "image_count": len(dets),              # how many images featured this part
            "raw_detections": dets,                # kept for heatmap drawing
        })

    return aggregated


def _severity_from_ratio(ratio: float, part_name: str) -> SeverityResult:
    """
    Derive a SeverityResult directly from an area ratio value
    (bypassing the need for image dimensions).
    """
    if ratio < 0.05:
        score = max(1, int(ratio / 0.05 * 3))
        label = "Minor"
    elif ratio < 0.15:
        normalized = (ratio - 0.05) / 0.10
        score = 4 + int(normalized * 2)
        label = "Moderate"
    else:
        normalized = min((ratio - 0.15) / 0.25, 1.0)
        score = 7 + int(normalized * 3)
        label = "Severe"

    score = max(1, min(score, 10))
    return SeverityResult(label=label, score=score, area_ratio=ratio)
