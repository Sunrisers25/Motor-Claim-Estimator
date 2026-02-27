"""
fraud_detector.py
-----------------
Feature 12: Fraud Detection Module

Three-layer fraud check:
  1. Duplicate image detection — MD5 hash comparison across uploaded images
  2. Blur detection           — Laplacian variance; low variance = blurry / low quality
  3. EXIF metadata analysis   — extracts capture timestamp and GPS if present

Outputs a FraudReport per image and a consolidated summary.
"""

import hashlib
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import cv2
import numpy as np
from PIL import Image as PILImage


# Laplacian variance below this threshold → image flagged as blurry
BLUR_THRESHOLD = 80.0


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ImageFraudReport:
    filename:        str
    md5_hash:        str
    is_duplicate:    bool              = False
    duplicate_of:    Optional[str]     = None   # filename of the original
    is_blurry:       bool              = False
    blur_score:      float             = 0.0    # higher = sharper
    exif_timestamp:  Optional[str]     = None
    exif_gps:        Optional[str]     = None
    has_exif:        bool              = False
    risk_flags:      List[str]         = field(default_factory=list)

    @property
    def risk_level(self) -> str:
        n = len(self.risk_flags)
        if n == 0:   return "Low"
        if n == 1:   return "Medium"
        return "High"

    @property
    def risk_color(self) -> str:
        return {"Low": "green", "Medium": "orange", "High": "red"}.get(self.risk_level, "red")


@dataclass
class FraudSummary:
    image_reports:    List[ImageFraudReport] = field(default_factory=list)
    duplicate_groups: List[List[str]]        = field(default_factory=list)
    overall_risk:     str                    = "Low"
    flagged_count:    int                    = 0


# ──────────────────────────────────────────────────────────────────────────────
# Individual checks
# ──────────────────────────────────────────────────────────────────────────────

def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _laplacian_variance(np_image: np.ndarray) -> float:
    """Higher variance = sharper. Low variance = blurry."""
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _read_exif(pil_image: PILImage.Image) -> Dict[str, Any]:
    """Extract EXIF timestamp and GPS data from a PIL image."""
    exif_data: Dict[str, Any] = {"timestamp": None, "gps": None, "has_exif": False}
    try:
        raw_exif = pil_image._getexif()       # type: ignore[attr-defined]
        if not raw_exif:
            return exif_data

        exif_data["has_exif"] = True

        # Tag 36867 = DateTimeOriginal
        ts = raw_exif.get(36867) or raw_exif.get(306)
        if ts:
            exif_data["timestamp"] = str(ts)

        # Tag 34853 = GPSInfo
        gps_raw = raw_exif.get(34853)
        if gps_raw and isinstance(gps_raw, dict):
            # Tags: 1=LatRef, 2=Lat, 3=LonRef, 4=Lon
            try:
                lat_ref = gps_raw.get(1, "N")
                lat     = gps_raw.get(2)
                lon_ref = gps_raw.get(3, "E")
                lon     = gps_raw.get(4)
                if lat and lon:
                    def dms(vals):
                        d, m, s = [float(v) if isinstance(v, (int, float)) else v[0]/v[1] for v in vals]
                        return d + m/60 + s/3600
                    exif_data["gps"] = f"{dms(lat):.4f}°{lat_ref}, {dms(lon):.4f}°{lon_ref}"
            except Exception:
                exif_data["gps"] = "GPS data present (parse error)"

    except Exception:
        pass

    return exif_data


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def analyze_images(
    images: List[Dict[str, Any]]
) -> FraudSummary:
    """
    Run full fraud analysis on a list of image input dicts.

    Parameters
    ----------
    images : list of dicts, each with keys:
        - "filename" (str)
        - "bytes"    (bytes)
        - "np_image" (np.ndarray, RGB)
        - "pil_image" (PIL.Image)

    Returns
    -------
    FraudSummary with per-image reports and overall risk
    """
    summary = FraudSummary()
    seen_hashes: Dict[str, str] = {}   # hash → filename

    for img in images:
        filename  = img["filename"]
        raw_bytes = img["bytes"]
        np_image  = img["np_image"]
        pil_image = img["pil_image"]

        report = ImageFraudReport(filename=filename, md5_hash=_md5(raw_bytes))

        # ── 1. Duplicate detection ────────────────────────────────────────────
        if report.md5_hash in seen_hashes:
            report.is_duplicate = True
            report.duplicate_of = seen_hashes[report.md5_hash]
            report.risk_flags.append(
                f"Duplicate of '{report.duplicate_of}' — possible claim inflation"
            )
        else:
            seen_hashes[report.md5_hash] = filename

        # ── 2. Blur detection ─────────────────────────────────────────────────
        blur_score = _laplacian_variance(np_image)
        report.blur_score = round(blur_score, 1)
        if blur_score < BLUR_THRESHOLD:
            report.is_blurry = True
            report.risk_flags.append(
                f"Low image quality (blur score {blur_score:.0f} < {BLUR_THRESHOLD}) "
                "— photo may be intentionally blurred to hide damage details"
            )

        # ── 3. EXIF analysis ──────────────────────────────────────────────────
        exif = _read_exif(pil_image)
        report.has_exif       = exif["has_exif"]
        report.exif_timestamp = exif["timestamp"]
        report.exif_gps       = exif["gps"]

        if not report.has_exif:
            report.risk_flags.append(
                "No EXIF metadata — image may have been edited or screenshot-captured"
            )

        summary.image_reports.append(report)

    # ── Consolidate ──────────────────────────────────────────────────────────
    summary.flagged_count = sum(1 for r in summary.image_reports if r.risk_flags)
    total = len(summary.image_reports)
    if total == 0:
        summary.overall_risk = "Low"
    elif summary.flagged_count == 0:
        summary.overall_risk = "Low"
    elif summary.flagged_count / total < 0.5:
        summary.overall_risk = "Medium"
    else:
        summary.overall_risk = "High"

    return summary
