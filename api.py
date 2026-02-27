"""
api.py
------
FastAPI backend server that bridges the React frontend (claim-analyzer-ai-main)
with the Python AI backend modules.

Endpoints:
  POST /api/analyze     — upload images, run fraud + detection + cost + decision
  GET  /api/claims      — return all saved claims for analytics
  GET  /api/stats       — aggregate stats for analytics dashboard
  GET  /api/parts       — parts base prices
  POST /api/pdf         — generate and return PDF report bytes

Run:
  pip install fastapi uvicorn python-multipart
  uvicorn api:app --reload --port 8000
"""

import io
import uuid
import json
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image as PILImage

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

# ── Local modules ──────────────────────────────────────────────────────────────
from database        import initialize_db, get_all_parts, get_all_claims, get_claim_stats, save_claim, FIXED_LABOR_COST
from detection       import detect_damage, draw_detections
from aggregator      import aggregate_detections
from repair_recommender import recommend_action
from fraud_detector  import analyze_images
from cost_engine     import estimate_costs, CAR_TYPE_MULTIPLIERS, INFLATION_FACTOR
from decision_engine import decide_claim
from report_generator import generate_pdf_report
from nlp_explainer   import generate_explanation

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Motor Claim Estimator API",
    description = "AI-powered car damage detection and cost estimation backend",
    version     = "1.0.0",
)

# Allow the React dev server (localhost:5173 / 8080 etc.) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # tighten in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

initialize_db()


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _bytes_to_np(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _np_to_base64(img: np.ndarray) -> str:
    import base64
    pil = PILImage.fromarray(img)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/parts — parts base prices
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/parts")
def get_parts():
    return {
        "parts":            get_all_parts(),
        "laborCost":        FIXED_LABOR_COST,
        "inflationFactor":  INFLATION_FACTOR,
        "carMultipliers":   CAR_TYPE_MULTIPLIERS,
    }


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/analyze — main analysis pipeline
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze(
    images:               List[UploadFile] = File(...),
    customer_name:        str  = Form(""),
    policy_number:        str  = Form(""),
    vehicle_reg:          str  = Form(""),
    vehicle_make:         str  = Form(""),
    car_type:             str  = Form("Sedan"),
    detection_mode:       str  = Form("simulation"),   # simulation | huggingface | local
    confidence_threshold: float = Form(0.40),
):
    if not images:
        raise HTTPException(status_code=400, detail="No images provided.")

    use_simulation = detection_mode == "simulation"
    use_hf_model   = detection_mode == "huggingface"

    # ── 1. Read and validate all images ───────────────────────────────────────
    fraud_input_list = []
    for upload in images:
        raw = await upload.read()
        try:
            pil_img = PILImage.open(io.BytesIO(raw)).convert("RGB")
            np_img  = np.array(pil_img)
        except Exception:
            continue   # skip unreadable files

        fraud_input_list.append({
            "filename":  upload.filename,
            "bytes":     raw,
            "np_image":  np_img,
            "pil_image": pil_img,
        })

    if not fraud_input_list:
        raise HTTPException(status_code=422, detail="No valid images could be decoded.")

    # ── 2. Fraud analysis ─────────────────────────────────────────────────────
    fraud_summary = analyze_images(fraud_input_list)

    fraud_results_out = []
    for report in fraud_summary.image_reports:
        fraud_results_out.append({
            "filename":    report.filename,
            "isDuplicate": report.is_duplicate,
            "duplicateOf": report.duplicate_of,
            "isBlurry":    report.is_blurry,
            "blurScore":   report.blur_score,
            "isSharp":     not report.is_blurry,
            "exifDate":    report.exif_timestamp,
            "exifGps":     report.exif_gps,
            "hasExif":     report.has_exif,
            "riskLevel":   report.risk_level,
            "riskFlags":   report.risk_flags,
        })

    # ── 3. Damage detection per non-duplicate image ────────────────────────────
    all_raw_detections = []
    annotated_images   = []

    for report, img_data in zip(fraud_summary.image_reports, fraud_input_list):
        if report.is_duplicate:
            continue

        np_img = img_data["np_image"]
        try:
            dets = detect_damage(
                np_img,
                use_simulation       = use_simulation,
                confidence_threshold = confidence_threshold,
                use_hf_model         = use_hf_model,
            )
        except Exception as e:
            dets = []

        all_raw_detections.extend(dets)

        ann_np = draw_detections(np_img, dets) if dets else np_img.copy()
        annotated_images.append(ann_np)

    # ── 4. Aggregate detections ───────────────────────────────────────────────
    aggregated = aggregate_detections(all_raw_detections)

    # Attach repair/replace recommendations
    for det in aggregated:
        rec = recommend_action(det["part_name"], det["severity"].label, det["severity"].area_ratio)
        det["action"]        = rec.action
        det["justification"] = rec.justification
        det["rec_icon"]      = rec.icon

    # ── 5. Cost estimation ────────────────────────────────────────────────────
    estimate = estimate_costs(aggregated, car_type=car_type)

    # ── 6. Claim decision ─────────────────────────────────────────────────────
    decision = decide_claim(estimate.grand_total, detections=aggregated)
    claim_id = f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    # ── 7. NLP explanation ────────────────────────────────────────────────────
    nlp_text = generate_explanation(estimate, decision, aggregated)

    # ── 8. Build response ─────────────────────────────────────────────────────
    detections_out = [{
        "part":          d["part_name"].capitalize(),
        "severity":      d["severity"].label,
        "score":         d["severity"].score,
        "confidence":    int(d["confidence"] * 100),
        "areaCoverage":  int(d["severity"].area_ratio * 100),
        "imageCount":    d.get("image_count", 1),
        "action":        d.get("action", "Repair"),
        "justification": d.get("justification", ""),
    } for d in aggregated]

    cost_breakdown_out = [{
        "part":           p.part_name.capitalize(),
        "severity":       p.severity_label,
        "score":          p.severity_score,
        "baseCost":       p.base_cost,
        "repairCost":     round(p.repair_cost),
        "labor":          round(p.labor_cost),
        "total":          round(p.total_cost),
        "recommendation": p.action,
        "justification":  next(
            (d.get("justification","") for d in aggregated if d["part_name"]==p.part_name), ""
        ),
    } for p in estimate.parts]

    # Convert annotated images to base64 for the React frontend
    annotated_b64 = [_np_to_base64(img) for img in annotated_images]

    return {
        "claimId":       claim_id,
        "fraudSummary": {
            "overallRisk":  fraud_summary.overall_risk,
            "flaggedCount": fraud_summary.flagged_count,
            "results":      fraud_results_out,
        },
        "detections":     detections_out,
        "annotatedImages": annotated_b64,
        "costBreakdown":  cost_breakdown_out,
        "totals": {
            "repairSubtotal": round(estimate.subtotal),
            "totalLabor":     round(estimate.total_labor),
            "grandTotal":     round(estimate.grand_total),
            "carType":        car_type,
            "multiplier":     CAR_TYPE_MULTIPLIERS.get(car_type, 1.0),
        },
        "decision": {
            "status":              decision.status,
            "description":         decision.description,
            "color":               decision.color,
            "lowConfidenceFlag":   decision.low_confidence_flag,
        },
        "nlpExplanation": nlp_text,
    }


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/pdf — generate and return PDF
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/pdf")
async def generate_pdf(
    images:        List[UploadFile] = File(default=[]),
    payload:       str              = Form(...),   # JSON string of analyze result
    customer_name: str              = Form(""),
    policy_number: str              = Form(""),
    vehicle_reg:   str              = Form(""),
    vehicle_make:  str              = Form(""),
    car_type:      str              = Form("Sedan"),
):
    """
    Accept the analysis payload from /api/analyze and generate a PDF.
    The frontend sends the analysis result JSON + optional annotated images.
    """
    try:
        data = json.loads(payload)
    except Exception:
        raise HTTPException(400, "Invalid payload JSON")

    # Re-run analysis if images provided, otherwise use payload data
    # For simplicity, rebuild estimate/decision objects from payload
    from cost_engine   import CostEstimateResult, PartEstimate
    from decision_engine import ClaimDecision
    from severity import SeverityResult

    totals        = data.get("totals", {})
    cost_data     = data.get("costBreakdown", [])
    decision_data = data.get("decision", {})
    claim_id      = data.get("claimId", f"CLM-{uuid.uuid4().hex[:8].upper()}")

    # Reconstruct minimal estimate and decision objects
    parts = []
    for c in cost_data:
        sev = SeverityResult(label=c["severity"], score=c["score"], area_ratio=0.2)
        parts.append(PartEstimate(
            part_name      = c["part"].lower(),
            severity_label = c["severity"],
            severity_score = c["score"],
            base_cost      = c["baseCost"],
            repair_cost    = c["repairCost"],
            labor_cost     = c["labor"],
            total_cost     = c["total"],
            confidence     = 0.8,
            bbox           = (0,0,100,100),
            car_type_mult  = totals.get("multiplier", 1.0),
            action         = c.get("recommendation", "Repair"),
            justification  = c.get("justification", ""),
        ))

    estimate = CostEstimateResult(
        parts        = parts,
        subtotal     = totals.get("repairSubtotal", 0),
        total_labor  = totals.get("totalLabor", 0),
        grand_total  = totals.get("grandTotal", 0),
        car_type     = car_type,
    )

    decision = ClaimDecision(
        status              = decision_data.get("status", "Manual Inspection Required"),
        description         = decision_data.get("description", ""),
        color               = decision_data.get("color", "red"),
        emoji               = "⚖️",
        low_confidence_flag = decision_data.get("lowConfidenceFlag", False),
    )

    metadata = {
        "customer_name": customer_name or "N/A",
        "policy_number": policy_number or "N/A",
        "vehicle_reg":   vehicle_reg   or "N/A",
        "vehicle_make":  vehicle_make  or "N/A",
    }

    # Read uploaded annotated images (optional)
    ann_images = []
    for upload in images:
        raw = await upload.read()
        try:
            pil = PILImage.open(io.BytesIO(raw)).convert("RGB")
            ann_images.append(np.array(pil))
        except Exception:
            pass

    pdf_bytes = generate_pdf_report(
        estimate         = estimate,
        decision         = decision,
        annotated_images = ann_images,
        claim_id         = claim_id,
        metadata         = metadata,
    )

    # Save claim to database
    parts_for_db = [{"part_name": p.part_name, "severity": p.severity_label,
                     "total": p.total_cost, "action": p.action} for p in parts]
    save_claim(
        claim_id      = claim_id,
        total_cost    = estimate.grand_total,
        decision      = decision.status,
        customer_name = customer_name,
        policy_number = policy_number,
        vehicle_reg   = vehicle_reg,
        vehicle_make  = vehicle_make,
        car_type      = car_type,
        parts         = parts_for_db,
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type = "application/pdf",
        headers    = {"Content-Disposition": f'attachment; filename="claim_{claim_id}.pdf"'},
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/claims — claim history for analytics
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/claims")
def get_claims():
    return get_all_claims()


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/stats — aggregate analytics stats
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    return get_claim_stats()


# ──────────────────────────────────────────────────────────────────────────────
# Run with: uvicorn api:app --reload --port 8000
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
