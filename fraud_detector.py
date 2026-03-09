"""
fraud_detector.py
-----------------
Feature 12: Fraud Detection Module

Three-layer fraud check:
  1. Duplicate image detection — MD5 (exact) + pHash (perceptual similarity)
  2. Blur detection           — Laplacian variance normalised by image resolution
  3. EXIF metadata analysis   — captures timestamp and GPS if present

Fixes applied:
  Flaw 13: Added perceptual hash (pHash) similarity check alongside MD5.
           Re-saved, compressed, or lightly-cropped versions of the same photo
           are now caught as duplicates (within a configurable Hamming distance).

  Flaw 14: Missing EXIF is no longer treated as a fraud risk flag by default.
           Many legitimate sources (WhatsApp, screenshots, PNG, WEBP) strip EXIF.
           It is now recorded as an info-level note and only escalated to a risk
           flag when combined with at least one other suspicious signal.

  Flaw 15: Blur threshold is now resolution-normalised using the image's
           pixel count so that a clean 480p image is not falsely flagged.

  Flaw 16: EXIF reading now uses PIL.ExifTags / getexif() (public API, Pillow ≥ 6)
           instead of the private _getexif() method; also handles PNG/WEBP gracefully.
"""

import hashlib
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import cv2
import numpy as np
from PIL import Image as PILImage, ExifTags

# ── Blur threshold ─────────────────────────────────────────────────────────────
# Flaw 15 fix: raw Laplacian variance scales with image resolution.
# We normalise by pixel count (in megapixels) before comparing to this constant.
# For reference: a sharp 1080p image → normalised score ≈ 100–400.
BLUR_THRESHOLD_NORMALISED = 60.0

# ── pHash settings ──────────────────────────────────────────────────────────────
# Flaw 13 fix: perceptual duplicate detection.
PHASH_SIZE         = 16       # internal DCT grid (higher = more sensitive)
PHASH_MAX_DISTANCE = 8        # Hamming distance ≤ this → flagged as duplicate
                              # (0 = identical, 64 = completely different for 8×8 hash)


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ImageFraudReport:
    filename:        str
    md5_hash:        str
    phash_hex:       str              = ""
    is_duplicate:    bool             = False
    duplicate_of:    Optional[str]    = None   # filename of the original
    is_blurry:       bool             = False
    blur_score:      float            = 0.0    # normalised; higher = sharper
    exif_timestamp:  Optional[str]    = None
    exif_gps:        Optional[str]    = None
    has_exif:        bool             = False
    no_exif_note:    bool             = False  # Flaw 14: info note, not risk flag
    risk_flags:      List[str]        = field(default_factory=list)

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


def _phash(np_image: np.ndarray) -> str:
    """
    Flaw 13 fix: compute a perceptual hash (DCT-based pHash).
    Returns a hex string. Two images with Hamming distance ≤ PHASH_MAX_DISTANCE
    are considered perceptual duplicates.
    """
    # Resize to (PHASH_SIZE*2 × PHASH_SIZE*2) for stable DCT
    size = PHASH_SIZE * 2
    small = cv2.resize(cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY), (size, size))
    dct   = cv2.dct(small.astype(np.float32))
    dct_low = dct[:PHASH_SIZE, :PHASH_SIZE]  # top-left low-frequency block
    mean  = dct_low.mean()
    bits  = (dct_low > mean).flatten()       # 256 bits
    # Encode as 64-char hex string
    packed = np.packbits(bits)
    return packed.tobytes().hex()


def _hamming_distance(hex1: str, hex2: str) -> int:
    """Hamming distance between two pHash hex strings (bit-level)."""
    b1 = bytes.fromhex(hex1)
    b2 = bytes.fromhex(hex2)
    return sum(bin(a ^ b).count("1") for a, b in zip(b1, b2))


def _normalised_blur_score(np_image: np.ndarray) -> float:
    """
    Flaw 15 fix: Laplacian variance normalised by image resolution.
    Divides raw variance by megapixel count so that the same threshold
    applies equally to 480p, 1080p, and 4K images.
    """
    gray = cv2.cvtColor(np_image, cv2.COLOR_RGB2GRAY)
    raw_var   = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    megapixels = (gray.shape[0] * gray.shape[1]) / 1_000_000
    return raw_var / max(megapixels, 0.01)


def _read_exif(pil_image: PILImage.Image) -> Dict[str, Any]:
    """
    Flaw 16 fix: use PIL's public getexif() API (Pillow ≥ 6.0.0) instead of
    the private _getexif() method. Also handles PNG/WEBP/BMP gracefully —
    those formats either return an empty ExifData object or raise AttributeError,
    both of which are caught cleanly.
    """
    exif_data: Dict[str, Any] = {"timestamp": None, "gps": None, "has_exif": False}
    try:
        raw_exif = pil_image.getexif()   # public API, works across formats
        if not raw_exif:
            return exif_data

        exif_data["has_exif"] = True

        # DateTimeOriginal (tag 36867) or DateTime (tag 306)
        ts = raw_exif.get(36867) or raw_exif.get(306)
        if ts:
            exif_data["timestamp"] = str(ts)

        # GPSInfo (tag 34853)
        gps_raw = raw_exif.get(34853)
        if gps_raw and isinstance(gps_raw, dict):
            try:
                lat_ref = gps_raw.get(1, "N")
                lat     = gps_raw.get(2)
                lon_ref = gps_raw.get(3, "E")
                lon     = gps_raw.get(4)
                if lat and lon:
                    def dms(vals):
                        d, m, s = [
                            float(v) if isinstance(v, (int, float)) else v[0] / v[1]
                            for v in vals
                        ]
                        return d + m / 60 + s / 3600
                    exif_data["gps"] = f"{dms(lat):.4f}°{lat_ref}, {dms(lon):.4f}°{lon_ref}"
            except Exception:
                exif_data["gps"] = "GPS data present (parse error)"

    except (AttributeError, Exception):
        pass   # PNG/WEBP/BMP or any other format that has no EXIF support

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
    seen_md5:    Dict[str, str] = {}   # md5  → filename
    seen_phash:  List[tuple]    = []   # list of (phash_hex, filename)

    for img in images:
        filename  = img["filename"]
        raw_bytes = img["bytes"]
        np_image  = img["np_image"]
        pil_image = img["pil_image"]

        ph = _phash(np_image)
        report = ImageFraudReport(
            filename  = filename,
            md5_hash  = _md5(raw_bytes),
            phash_hex = ph,
        )

        # ── 1. Duplicate detection ─────────────────────────────────────────────
        # Flaw 13 fix: check both MD5 (exact) and pHash (perceptual similarity)
        if report.md5_hash in seen_md5:
            report.is_duplicate = True
            report.duplicate_of = seen_md5[report.md5_hash]
            report.risk_flags.append(
                f"Exact duplicate of '{report.duplicate_of}' — possible claim inflation"
            )
        else:
            # Check perceptual similarity with all previously seen images
            for prev_hash, prev_name in seen_phash:
                dist = _hamming_distance(ph, prev_hash)
                if dist <= PHASH_MAX_DISTANCE:
                    report.is_duplicate = True
                    report.duplicate_of = prev_name
                    report.risk_flags.append(
                        f"Near-duplicate of '{prev_name}' (similarity distance: {dist}) "
                        "— same photo may have been re-saved, cropped, or lightly edited"
                    )
                    break

            seen_md5[report.md5_hash]  = filename
            seen_phash.append((ph, filename))

        # ── 2. Blur detection ──────────────────────────────────────────────────
        # Flaw 15 fix: resolution-normalised score
        blur_score = _normalised_blur_score(np_image)
        report.blur_score = round(blur_score, 1)
        if blur_score < BLUR_THRESHOLD_NORMALISED:
            report.is_blurry = True
            report.risk_flags.append(
                f"Low image quality (normalised blur score {blur_score:.0f} "
                f"< {BLUR_THRESHOLD_NORMALISED}) "
                "— photo may be intentionally blurred to hide damage details"
            )

        # ── 3. EXIF analysis ───────────────────────────────────────────────────
        # Flaw 16 fix: uses public getexif() API
        exif = _read_exif(pil_image)
        report.has_exif       = exif["has_exif"]
        report.exif_timestamp = exif["timestamp"]
        report.exif_gps       = exif["gps"]

        # Flaw 14 fix: missing EXIF is an info note, not an automatic risk flag.
        # It is only escalated to a risk flag if the image is ALSO blurry
        # (two signals together indicate higher likelihood of tampering).
        if not report.has_exif:
            report.no_exif_note = True
            if report.is_blurry:
                report.risk_flags.append(
                    "No EXIF metadata AND low image quality — combined signals "
                    "suggest possible tampering or screenshot-captured image"
                )
            # else: just note it, don't count as a risk flag

        summary.image_reports.append(report)

    # ── Consolidate ─────────────────────────────────────────────────────────────
    summary.flagged_count = sum(1 for r in summary.image_reports if r.risk_flags)
    total = len(summary.image_reports)
    if total == 0 or summary.flagged_count == 0:
        summary.overall_risk = "Low"
    elif summary.flagged_count / total < 0.5:
        summary.overall_risk = "Medium"
    else:
        summary.overall_risk = "High"

    return summary
