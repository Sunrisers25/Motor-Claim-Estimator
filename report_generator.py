"""
report_generator.py
--------------------
Generates a professional PDF claim report using ReportLab.

The report includes:
  - Claim header and date
  - Detected damage summary table
  - Cost breakdown table
  - Claim decision
  - Annotated image (if provided)
"""

import io
import os
from datetime import datetime
from typing import List, Optional

import numpy as np
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)

from cost_engine import CostEstimateResult
from decision_engine import ClaimDecision

# ──────────────────────────────────────────────────────────────────────────────
# Brand colours
# ──────────────────────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#1E3A5F")   # deep navy
ACCENT    = colors.HexColor("#2563EB")   # electric blue
SUCCESS   = colors.HexColor("#16A34A")   # green
WARNING   = colors.HexColor("#D97706")   # amber
DANGER    = colors.HexColor("#DC2626")   # red
LIGHT_BG  = colors.HexColor("#F1F5F9")   # light slate
WHITE     = colors.white


def _decision_color(status: str) -> colors.Color:
    if "Approved" in status:
        return SUCCESS
    if "Supervisor" in status:
        return WARNING
    return DANGER


def _severity_color(severity: str) -> colors.Color:
    mapping = {"Minor": SUCCESS, "Moderate": WARNING, "Severe": DANGER}
    return mapping.get(severity, colors.black)


def generate_pdf_report(
    estimate:          CostEstimateResult,
    decision:          ClaimDecision,
    annotated_images:  Optional[List[np.ndarray]] = None,
    claim_id:          str = "CLM-DEMO-001",
    metadata:          Optional[dict] = None,
) -> bytes:
    """
    Build and return the PDF report as raw bytes.

    Parameters
    ----------
    estimate          : CostEstimateResult from cost_engine
    decision          : ClaimDecision from decision_engine
    annotated_images  : list of RGB numpy arrays with bounding boxes drawn
    claim_id          : identifier string shown on the report header
    metadata          : optional dict with keys: customer_name, policy_number,
                        vehicle_reg, vehicle_make

    Returns
    -------
    bytes — ready-to-download PDF content
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize    = A4,
        topMargin   = 1.5 * cm,
        bottomMargin= 1.5 * cm,
        leftMargin  = 2   * cm,
        rightMargin = 2   * cm,
    )

    styles = getSampleStyleSheet()
    story  = []
    meta   = metadata or {}

    # ── Header ──────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent    = styles["Title"],
        textColor = PRIMARY,
        fontSize  = 22,
        spaceAfter= 4,
    )
    sub_style = ParagraphStyle(
        "Sub",
        parent    = styles["Normal"],
        textColor = ACCENT,
        fontSize  = 10,
        spaceAfter= 2,
    )
    normal_style = styles["Normal"]

    story.append(Paragraph("🚗  Motor Claim Estimator Report", title_style))
    story.append(Paragraph("AI-Powered Damage Analysis & Cost Estimate", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))

    # Claim meta info
    now = datetime.now().strftime("%d %B %Y  %H:%M")
    meta_data = [
        ["Claim ID:",     claim_id,                       "Report Date:",   now],
        ["Customer:",     meta.get("customer_name", "N/A"), "Policy No.:",   meta.get("policy_number", "N/A")],
        ["Vehicle Reg.:", meta.get("vehicle_reg", "N/A"),  "Make/Model:",   meta.get("vehicle_make", "N/A")],
    ]
    meta_table = Table(meta_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
    meta_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, -1), PRIMARY),
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Annotated images ─────────────────────────────────────────────────────
    if annotated_images:
        story.append(Paragraph("<b>Detected Damage Images</b>", sub_style))
        for idx, ann_img in enumerate(annotated_images, 1):
            try:
                pil_img    = PILImage.fromarray(ann_img)
                img_buffer = io.BytesIO()
                pil_img.save(img_buffer, format="PNG")
                img_buffer.seek(0)
                rl_img = RLImage(img_buffer, width=14*cm, height=8*cm, kind="proportional")
                story.append(Paragraph(f"<i>Image {idx}</i>", normal_style))
                story.append(rl_img)
                story.append(Spacer(1, 0.3 * cm))
            except Exception:
                pass  # skip any image that fails
        story.append(Spacer(1, 0.1 * cm))

    # ── Damage Detection Table ───────────────────────────────────────────────
    story.append(Paragraph("<b>Damage Detection Summary</b>", sub_style))
    story.append(Spacer(1, 0.2 * cm))

    det_header = ["#", "Part", "Severity", "Severity Score", "Confidence"]
    det_rows   = [det_header]
    for i, part in enumerate(estimate.parts, 1):
        det_rows.append([
            str(i),
            part.part_name.capitalize(),
            part.severity_label,
            f"{part.severity_score} / 10",
            f"{part.confidence:.0%}",
        ])

    det_table = Table(det_rows, colWidths=[1*cm, 4*cm, 3*cm, 3.5*cm, 3.5*cm])
    det_style = [
        ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
    ]
    # Color-code severity cells
    for i, part in enumerate(estimate.parts, 1):
        sc = _severity_color(part.severity_label)
        det_style.append(("TEXTCOLOR", (2, i), (2, i), sc))
        det_style.append(("FONTNAME",  (2, i), (2, i), "Helvetica-Bold"))
    det_table.setStyle(TableStyle(det_style))
    story.append(det_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Cost Breakdown Table ─────────────────────────────────────────────────
    story.append(Paragraph("<b>Cost Breakdown</b>", sub_style))
    story.append(Spacer(1, 0.2 * cm))

    cost_header = ["Part", "Severity", "Base Cost (₹)", "Labor (₹)", "Total (₹)"]
    cost_rows   = [cost_header]
    for part in estimate.parts:
        cost_rows.append([
            part.part_name.capitalize(),
            part.severity_label,
            f"{part.repair_cost:,.0f}",
            f"{part.labor_cost:,.0f}",
            f"{part.total_cost:,.0f}",
        ])

    # Summary rows
    cost_rows.append(["", "", "", "Subtotal (Repairs)", f"₹{estimate.subtotal:,.0f}"])
    cost_rows.append(["", "", "", "Total Labor",        f"₹{estimate.total_labor:,.0f}"])
    cost_rows.append(["", "", "", "GRAND TOTAL",        f"₹{estimate.grand_total:,.0f}"])

    cost_table = Table(cost_rows, colWidths=[3.5*cm, 3*cm, 3*cm, 3.5*cm, 3*cm])
    n = len(cost_rows)
    cost_style = [
        ("BACKGROUND",   (0, 0),    (-1, 0),     PRIMARY),
        ("TEXTCOLOR",    (0, 0),    (-1, 0),     WHITE),
        ("FONTNAME",     (0, 0),    (-1, 0),     "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0),    (-1, -1),    9),
        ("ALIGN",        (2, 0),    (-1, -1),    "RIGHT"),
        ("GRID",         (0, 0),    (-1, n-4),   0.5, colors.grey),
        ("LINEABOVE",    (0, n-3),  (-1, n-3),   1,   PRIMARY),
        ("FONTNAME",     (3, n-1),  (-1, n-1),   "Helvetica-Bold"),
        ("FONTSIZE",     (3, n-1),  (-1, n-1),   10),
        ("TEXTCOLOR",    (3, n-1),  (-1, n-1),   ACCENT),
        ("ROWBACKGROUNDS", (0, 1),  (-1, n-4),   [WHITE, LIGHT_BG]),
        ("BOTTOMPADDING",  (0, 0),  (-1, -1),    5),
    ]
    cost_table.setStyle(TableStyle(cost_style))
    story.append(cost_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Claim Decision ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BG, spaceBefore=4, spaceAfter=8))
    dec_color = _decision_color(decision.status)
    dec_style = ParagraphStyle(
        "Dec",
        parent    = styles["Normal"],
        textColor = dec_color,
        fontSize  = 13,
        fontName  = "Helvetica-Bold",
        spaceAfter= 6,
    )
    story.append(Paragraph(f"Claim Decision: {decision.status}", dec_style))
    story.append(Paragraph(decision.description, normal_style))
    story.append(Spacer(1, 0.5 * cm))

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    footer_style = ParagraphStyle(
        "Footer",
        parent    = styles["Normal"],
        textColor = colors.grey,
        fontSize  = 7,
        alignment = 1,
    )
    story.append(Paragraph(
        "This report is generated automatically by the AI Motor Claim Estimator. "
        "For official use, please have it reviewed by a certified assessor.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()
