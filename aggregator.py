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

Fix (Flaw 18): The bbox is now taken from the detection with the highest
  area_ratio (largest damage view), keeping it visually consistent with the
  reported averaged severity — previously it came from highest confidence
  which could be an unrelated angle.

Fix (Flaw 19): _severity_from_ratio is no longer duplicated here.
  Imported from severity.py (single source of truth).
"""

from typing import List, Dict, Any
from collections import defaultdict

from severity import severity_from_ratio


def aggregate_detections(all_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge detections from multiple images of the same vehicle.

    Strategy per part:
      - confidence   → AVERAGE across images (not just max, to avoid one lucky hit)
      - area_ratio   → AVERAGE (representative view of actual damage size)
      - severity     → RE-CLASSIFY from averaged area_ratio (via severity.py)
      - bbox         → keep from the detection with the largest area_ratio
                       (most prominent / clearest view of that part's damage)
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
        # Average confidence across all appearances
        avg_confidence = sum(d["confidence"] for d in dets) / len(dets)

        # Average area_ratio across all appearances
        avg_area_ratio = sum(d["severity"].area_ratio for d in dets) / len(dets)

        # Bbox from detection with the largest area_ratio — most prominent view
        # (Flaw 18 fix: previously used highest confidence which could mismatch severity)
        best = max(dets, key=lambda d: d["severity"].area_ratio)

        # Re-derive severity from averaged area_ratio (Flaw 19: single source of truth)
        avg_severity = severity_from_ratio(avg_area_ratio)

        aggregated.append({
            "part_name":      part_name,
            "confidence":     round(avg_confidence, 3),
            "bbox":           best["bbox"],
            "severity":       avg_severity,
            "image_count":    len(dets),         # how many images featured this part
            "raw_detections": dets,              # kept for heatmap drawing
        })

    return aggregated
