"""
app.py
------
Main Streamlit application — AI Motor Claim Estimator (Full Feature Build)

Features:
  10. Multi-Image Aggregation       (aggregator.py)
  11. Repair vs Replace Engine      (repair_recommender.py)
  12. Fraud Detection               (fraud_detector.py)
  13. Visual Damage Heatmap         (OpenCV overlay)
  14. Car Type-Based Pricing        (cost_engine.py)
  15. Dynamic Cost Adjustment       (cost_engine.py)
  16. Confidence-Based Override     (decision_engine.py)
  17. Claim History Tracking        (database.py → SQLite)
  18. Analytics Dashboard           (pages/analytics.py — auto tab)
  19. AI Natural Language Explanation (nlp_explainer.py)

Run:
    streamlit run app.py
"""

import io
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import cv2
import numpy as np
import streamlit as st
from PIL import Image, UnidentifiedImageError

# ── Local modules ──────────────────────────────────────────────────────────────
from database       import initialize_db, get_all_parts, FIXED_LABOR_COST, save_claim
from detection      import detect_damage, draw_detections
from aggregator     import aggregate_detections
from repair_recommender import recommend_action
from fraud_detector import analyze_images, FraudSummary
from cost_engine    import estimate_costs, CAR_TYPE_MULTIPLIERS, INFLATION_FACTOR
from decision_engine import decide_claim
from report_generator import generate_pdf_report
from nlp_explainer  import generate_explanation

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title            = "Motor Claim Estimator",
    page_icon             = "🚗",
    layout                = "wide",
    initial_sidebar_state = "expanded",
)

# ── Premium CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%); color:#e2e8f0; }

.main-header { background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%); border-radius:16px;
    padding:2rem 2.5rem; margin-bottom:1.5rem; box-shadow:0 8px 32px rgba(37,99,235,.3); text-align:center; }
.main-header h1 { font-size:2.3rem; font-weight:700; color:#fff; margin:0; letter-spacing:-.02em; }
.main-header p  { color:#93c5fd; font-size:1rem; margin-top:.4rem; }

.card { background:rgba(30,41,59,.85); border:1px solid rgba(255,255,255,.08);
    border-radius:12px; padding:1.4rem 1.6rem; margin-bottom:1.2rem; backdrop-filter:blur(12px); }
.section-title { color:#60a5fa; font-size:.9rem; font-weight:700; letter-spacing:.08em;
    text-transform:uppercase; margin-bottom:.75rem; }

.metric-tile { background:rgba(37,99,235,.15); border:1px solid rgba(37,99,235,.3);
    border-radius:10px; padding:1rem; text-align:center; }
.metric-tile .value { font-size:1.6rem; font-weight:700; color:#60a5fa; }
.metric-tile .label { font-size:.75rem; color:#94a3b8; margin-top:.2rem; }

.badge-approved  { background:rgba(22,163,74,.2);  border:2px solid #16a34a; color:#4ade80;
    border-radius:10px; padding:1rem 1.5rem; font-size:1.3rem; font-weight:700; text-align:center; }
.badge-supervisor{ background:rgba(217,119,6,.2);  border:2px solid #d97706; color:#fbbf24;
    border-radius:10px; padding:1rem 1.5rem; font-size:1.3rem; font-weight:700; text-align:center; }
.badge-manual    { background:rgba(220,38,38,.2);  border:2px solid #dc2626; color:#f87171;
    border-radius:10px; padding:1rem 1.5rem; font-size:1.3rem; font-weight:700; text-align:center; }

.fraud-low    { background:rgba(22,163,74,.12);  border:1px solid rgba(22,163,74,.35);  color:#4ade80; }
.fraud-medium { background:rgba(217,119,6,.12);  border:1px solid rgba(217,119,6,.35);  color:#fbbf24; }
.fraud-high   { background:rgba(220,38,38,.12);  border:1px solid rgba(220,38,38,.35);  color:#f87171; }
.fraud-card   { border-radius:8px; padding:.7rem 1rem; font-size:.85rem; margin-bottom:.5rem; }

.sim-banner  { background:rgba(245,158,11,.12); border:1px solid rgba(245,158,11,.35);
    border-radius:8px; padding:.6rem 1rem; font-size:.85rem; color:#fbbf24; margin-bottom:.8rem; }
.real-banner { background:rgba(34,197,94,.12);  border:1px solid rgba(34,197,94,.35);
    border-radius:8px; padding:.6rem 1rem; font-size:.85rem; color:#4ade80;  margin-bottom:.8rem; }
.nlp-box { background:rgba(15,23,42,.6); border:1px solid rgba(96,165,250,.2);
    border-radius:10px; padding:1.2rem 1.4rem; font-size:.88rem; line-height:1.7;
    color:#cbd5e1; white-space:pre-wrap; font-family:'Inter',monospace; }
.repair-badge   { display:inline-block; background:rgba(5,150,105,.2);  color:#34d399;
    border:1px solid #10b981; border-radius:6px; padding:2px 10px; font-size:.8rem; font-weight:600; }
.replace-badge  { display:inline-block; background:rgba(220,38,38,.2);  color:#f87171;
    border:1px solid #dc2626; border-radius:6px; padding:2px 10px; font-size:.8rem; font-weight:600; }
.upload-hint { border:2px dashed rgba(96,165,250,.4); border-radius:12px; padding:1.5rem;
    text-align:center; color:#64748b; font-size:.9rem; }

/* Sidebar */
[data-testid="stSidebar"] { background:rgba(15,23,42,.97)!important; border-right:1px solid rgba(255,255,255,.06)!important; }
/* Buttons */
.stButton>button { background:linear-gradient(135deg,#1d4ed8 0%,#2563eb 100%);
    color:white; border:none; border-radius:8px; padding:.6rem 1.4rem; font-weight:600; transition:all .2s ease; }
.stButton>button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(37,99,235,.4); }
div[data-testid="stDownloadButton"]>button {
    background:linear-gradient(135deg,#065f46 0%,#059669 100%);
    color:white; border:none; border-radius:8px; padding:.6rem 1.4rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
initialize_db()
DEMO_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "demo_car_damage.png")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 Motor Claim Estimator")
    st.page_link("pages/analytics.py", label="📊 Analytics Dashboard", icon="📊")
    st.markdown("---")

    st.markdown("### ⚙️ Detection Settings")

    # Detection mode selector — 3 tiers
    detection_mode = st.radio(
        "Detection Mode",
        options=["🧠 Smart Simulation (Offline)", "🤖 HuggingFace Model (Download)", "📂 Local YOLOv8 Model"],
        index=0,
        help=(
            "Smart Simulation: OpenCV edge+texture analysis — works offline.\n"
            "HuggingFace: Downloads keremberke/yolov8m-car-damage-detection (~100MB, first run only).\n"
            "Local Model: Use your own trained weights in models/damage_yolov8.pt."
        )
    )

    use_simulation = detection_mode == "🧠 Smart Simulation (Offline)"
    use_hf_model   = detection_mode == "🤖 HuggingFace Model (Download)"

    if use_simulation:
        st.markdown('<div class="sim-banner">🧠 <b>Smart Simulation</b> — image-aware OpenCV</div>', unsafe_allow_html=True)
    elif use_hf_model:
        st.markdown('<div class="real-banner">🤖 <b>HuggingFace Model</b> — downloads on first use</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="real-banner">📂 <b>Local YOLOv8</b> — models/damage_yolov8.pt</div>', unsafe_allow_html=True)

    confidence_threshold = st.slider("Confidence Threshold", 0.10, 0.95, 0.40, 0.05,
        help="Minimum confidence to keep a detection (real model modes only).",
        disabled=use_simulation)

    st.markdown("---")
    st.markdown("### 🚘 Vehicle Class")
    car_type = st.selectbox("Car Type", list(CAR_TYPE_MULTIPLIERS.keys()), index=1,
        help="Affects part and labor cost multipliers.")
    mult = CAR_TYPE_MULTIPLIERS[car_type]
    st.caption(f"Cost multiplier: **{mult}×** | Inflation: **{INFLATION_FACTOR}×**")

    st.markdown("---")
    st.markdown("### 📊 Parts Base Prices")
    for part, cost in get_all_parts().items():
        adj = cost * mult * INFLATION_FACTOR
        st.markdown(f"- **{part.capitalize()}**: ₹{adj:,.0f}")
    st.markdown(f"- **Labor**: ₹{FIXED_LABOR_COST * mult:,.0f} / part")

    st.markdown("---")
    st.markdown("### ⚖️ Decision Thresholds")
    st.markdown("""
| Cost | Decision |
|---|---|
| < ₹25K | ✅ Auto Approved |
| ₹25K–60K | ⚠️ Supervisor |
| > ₹60K | 🔴 Manual |
| Conf < 60% | 🔴 Override |
    """)
    st.caption("Hackathon Prototype • Motor Claim AI")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚗 AI Motor Claim Estimator</h1>
    <p>Multi-image analysis · Fraud detection · Instant repair estimate · PDF report</p>
</div>
""", unsafe_allow_html=True)

# ── Claim Metadata ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Claim Information</p>', unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
mc1, mc2 = st.columns(2, gap="medium")
with mc1:
    customer_name = st.text_input("Customer Name",      placeholder="e.g. Ravi Kumar")
    vehicle_reg   = st.text_input("Vehicle Reg. No.",   placeholder="e.g. MH 12 AB 1234")
with mc2:
    policy_number = st.text_input("Policy Number",      placeholder="e.g. POL-2025-00123")
    vehicle_make  = st.text_input("Vehicle Make/Model", placeholder="e.g. Maruti Suzuki Swift VXI")
st.markdown('</div>', unsafe_allow_html=True)

claim_metadata = {
    "customer_name": customer_name or "N/A",
    "policy_number": policy_number or "N/A",
    "vehicle_reg":   vehicle_reg   or "N/A",
    "vehicle_make":  vehicle_make  or "N/A",
}

# ── Upload ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📤 Upload Damage Images</p>', unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)
load_demo = st.button("🖼️ Load Demo Image", help="Use bundled sample car damage photo for demo.")
uploaded_files = st.file_uploader(
    "Upload images", type=["jpg","jpeg","png","webp","bmp"],
    accept_multiple_files=True, label_visibility="collapsed")
if not uploaded_files and not load_demo:
    st.markdown("""
    <div class="upload-hint">
        📷 Drag & drop car damage photos here, or click <b>Browse files</b><br>
        Multiple images allowed — each angle analyzed, duplicates detected<br>
        <br>Or click <b>Load Demo Image</b> above for an instant demo.
    </div>""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def safe_load_image(file_bytes: bytes, filename: str):
    try:
        pil = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        arr = np.array(pil)
        if arr.size == 0: raise ValueError("Empty image")
        return pil, arr
    except UnidentifiedImageError:
        st.error(f"❌ **{filename}** — Cannot identify image file. May be corrupt.")
    except Exception as e:
        st.error(f"❌ **{filename}** — {e}")
    return None, None


def draw_heatmap(image: np.ndarray, detections: List[Dict]) -> np.ndarray:
    """
    Feature 13: Draw semi-transparent colored heatmap overlays on damage zones.
    🟢 Minor  🟡 Moderate  🔴 Severe
    """
    overlay = image.copy()
    COLOR_MAP = {
        "Minor":    (34,  197, 94),
        "Moderate": (234, 179, 8),
        "Severe":   (239, 68,  68),
    }
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        color = COLOR_MAP.get(det["severity"].label, (200, 200, 200))
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)

    # alpha blend: 35% overlay opacity
    heatmap = cv2.addWeighted(overlay, 0.35, image, 0.65, 0)
    return heatmap


# ── Build image list ───────────────────────────────────────────────────────────
image_sources: List[tuple] = []
if load_demo and os.path.exists(DEMO_IMAGE_PATH):
    with open(DEMO_IMAGE_PATH, "rb") as f:
        image_sources.append(("demo_car_damage.png", f.read()))
elif load_demo:
    st.warning("⚠️ Demo image not found. Make sure `demo_car_damage.png` is in the project folder.")

for uf in uploaded_files:
    image_sources.append((uf.name, uf.read()))

# ── Process ────────────────────────────────────────────────────────────────────
if image_sources:
    all_raw_detections: List[Dict]  = []
    all_annotated_np:   List        = []
    fraud_input_list:   List[Dict]  = []

    # ── Fraud check ─────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">🔍 Detection & Fraud Analysis</p>', unsafe_allow_html=True)

    valid_count = 0
    for filename, raw_bytes in image_sources:
        pil_img, np_img = safe_load_image(raw_bytes, filename)
        if pil_img is None:
            continue
        valid_count += 1
        fraud_input_list.append({
            "filename":  filename,
            "bytes":     raw_bytes,
            "np_image":  np_img,
            "pil_image": pil_img,
        })

    if valid_count == 0:
        st.error("No valid images could be processed.")
        st.stop()

    fraud_summary = analyze_images(fraud_input_list)

    # Show fraud summary banner
    risk_col = {"Low": "fraud-low", "Medium": "fraud-medium", "High": "fraud-high"}.get(
        fraud_summary.overall_risk, "fraud-high")
    st.markdown(f"""
    <div class="fraud-card {risk_col}">
        🛡️ <b>Fraud Risk Assessment: {fraud_summary.overall_risk}</b> 
        — {fraud_summary.flagged_count}/{valid_count} image(s) flagged
    </div>""", unsafe_allow_html=True)

    # Per-image detection
    for fraud_report, img_data in zip(fraud_summary.image_reports, fraud_input_list):
        filename = img_data["filename"]
        pil_img  = img_data["pil_image"]
        np_img   = img_data["np_image"]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**📁 {filename}**")

        # Fraud flags
        if fraud_report.risk_flags:
            for flag in fraud_report.risk_flags:
                st.warning(f"⚠️ {flag}")
        else:
            st.success("✅ No fraud indicators detected")

        exif_info = []
        if fraud_report.exif_timestamp: exif_info.append(f"📅 Captured: {fraud_report.exif_timestamp}")
        if fraud_report.exif_gps:       exif_info.append(f"📍 GPS: {fraud_report.exif_gps}")
        if exif_info: st.caption(" | ".join(exif_info))
        st.caption(f"Image sharpness score: **{fraud_report.blur_score:.0f}** {'✅' if not fraud_report.is_blurry else '⚠️ Blurry'}")

        tab1, tab2, tab3 = st.tabs(["🔍 Detections", "🔥 Heatmap", "🖼️ Original"])

        with tab3:
            st.image(pil_img, use_container_width=True)

        # Skip detection on confirmed duplicates
        if fraud_report.is_duplicate:
            st.info(f"⏭️ Skipping detection — duplicate of '{fraud_report.duplicate_of}'")
            st.markdown('</div>', unsafe_allow_html=True)
            continue

        # ── Run detection ──────────────────────────────────────────────────
        with st.spinner(f"Analyzing {filename}…"):
            try:
                detections = detect_damage(
                    np_img,
                    use_simulation       = use_simulation,
                    confidence_threshold = confidence_threshold,
                    use_hf_model         = use_hf_model,
                )
            except Exception as e:
                st.error(f"⚠️ Detection error: {e}")
                detections = []

        all_raw_detections.extend(detections)

        # Annotated
        try:
            ann_np = draw_detections(np_img, detections)
        except Exception:
            ann_np = np_img.copy()
        all_annotated_np.append(ann_np)

        with tab1:
            st.image(Image.fromarray(ann_np), use_container_width=True,
                     caption=f"{len(detections)} zone(s) detected")
            if detections:
                st.dataframe([{
                    "Part":       d["part_name"].capitalize(),
                    "Severity":   d["severity"].label,
                    "Score":      f"{d['severity'].score}/10",
                    "Confidence": f"{d['confidence']:.0%}",
                    "Area":       f"{d['severity'].area_ratio:.1%}",
                } for d in detections], hide_index=True, use_container_width=True)
            else:
                st.info("No damage detected.")

        with tab2:
            # Feature 13: Heatmap
            heatmap_np = draw_heatmap(np_img, detections)
            st.image(Image.fromarray(heatmap_np), use_container_width=True,
                     caption="🟢 Minor  🟡 Moderate  🔴 Severe overlay")

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Feature 10: Aggregate detections ──────────────────────────────────────
    aggregated = aggregate_detections(all_raw_detections)

    if not aggregated:
        st.warning("No damage detected. Try uploading clearer photos or enable Simulation Mode.")
        st.stop()

    # Attach repair/replace recommendations (Feature 11)
    for det in aggregated:
        rec = recommend_action(det["part_name"], det["severity"].label, det["severity"].area_ratio)
        det["action"]        = rec.action
        det["justification"] = rec.justification
        det["rec_icon"]      = rec.icon

    # ── Aggregation info banner ────────────────────────────────────────────────
    if len(all_raw_detections) > len(aggregated):
        st.info(
            f"🔗 **Multi-Image Aggregation**: {len(all_raw_detections)} raw detections across "
            f"{valid_count} image(s) → merged into **{len(aggregated)} unique damaged part(s)**. "
            "Duplicate detections averaged; highest confidence kept."
        )

    # ── Cost estimation ────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">💰 Cost Estimation</p>', unsafe_allow_html=True)

    estimate = estimate_costs(aggregated, car_type=car_type)
    decision = decide_claim(estimate.grand_total, detections=aggregated)
    claim_id = f"CLM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    # KPI tiles
    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, str(len(estimate.parts)),         "Parts Damaged"),
        (m2, f"₹{estimate.subtotal:,.0f}",     "Repair Cost"),
        (m3, f"₹{estimate.total_labor:,.0f}",  "Labor Cost"),
        (m4, f"₹{estimate.grand_total:,.0f}",  "Grand Total"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="value">{val}</div>
                <div class="label">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Cost breakdown table with Feature 11: Repair/Replace
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"**📋 Part-wise Cost Breakdown** — {car_type} class ({CAR_TYPE_MULTIPLIERS[car_type]}× multiplier, {INFLATION_FACTOR}× inflation)")

    cost_rows = []
    for p in estimate.parts:
        det_match = next((d for d in aggregated if d["part_name"] == p.part_name), {})
        img_cnt   = det_match.get("image_count", 1)
        action    = p.action
        badge     = f'<span class="repair-badge">🔧 Repair</span>' if action == "Repair" else \
                   f'<span class="replace-badge">🔄 Replace</span>'
        cost_rows.append({
            "Part":              p.part_name.capitalize(),
            "Severity":          p.severity_label,
            "Score":             f"{p.severity_score}/10",
            "Seen in":           f"{img_cnt} img(s)",
            "Base Cost":         f"₹{p.base_cost:,.0f}",
            "Repair/Labor":      f"₹{p.repair_cost:,.0f} + ₹{p.labor_cost:,.0f}",
            "Part Total":        f"₹{p.total_cost:,.0f}",
            "Recommendation":    action,
        })
    st.dataframe(cost_rows, hide_index=True, use_container_width=True)

    # Repair vs Replace justifications
    with st.expander("📖 Repair/Replace Justifications"):
        for p in estimate.parts:
            det_match = next((d for d in aggregated if d["part_name"] == p.part_name), {})
            icon = det_match.get("rec_icon", "🔧")
            st.markdown(f"**{icon} {p.part_name.capitalize()}** — {det_match.get('justification','')}")

    tc1, tc2, tc3 = st.columns(3)
    with tc1: st.metric("Repair Subtotal", f"₹{estimate.subtotal:,.0f}")
    with tc2: st.metric("Total Labor",     f"₹{estimate.total_labor:,.0f}")
    with tc3: st.metric("🏷️ Grand Total",  f"₹{estimate.grand_total:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Claim Decision ─────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">⚖️ Claim Decision</p>', unsafe_allow_html=True)
    badge_cls = {"green":"badge-approved","orange":"badge-supervisor","red":"badge-manual"}.get(
        decision.color, "badge-manual")
    st.markdown(f'<div class="{badge_cls}">{decision.status}</div><br>', unsafe_allow_html=True)
    if decision.low_confidence_flag:
        st.warning("⚠️ **Responsible AI Override**: Low detection confidence triggered mandatory manual review.")
    st.info(decision.description)

    # ── Feature 19: NLP Explanation ───────────────────────────────────────────
    st.markdown('<p class="section-title">🤖 AI Natural Language Explanation</p>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    nlp_text = generate_explanation(estimate, decision, aggregated)
    st.markdown(f'<div class="nlp-box">{nlp_text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── PDF + Claim Save ───────────────────────────────────────────────────────
    st.markdown('<p class="section-title">📄 Download Report</p>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if customer_name or policy_number:
        st.success("✅ Claim metadata included in PDF.")
    else:
        st.caption("💡 Fill in claim information above to personalize the PDF.")

    with st.spinner("Generating PDF report…"):
        try:
            pdf_bytes = generate_pdf_report(
                estimate         = estimate,
                decision         = decision,
                annotated_images = all_annotated_np,
                claim_id         = claim_id,
                metadata         = claim_metadata,
            )
            pdf_ok = True
        except Exception as e:
            st.error(f"⚠️ PDF error: {e}")
            pdf_ok = False

    if pdf_ok:
        st.download_button(
            label               = "⬇️  Download PDF Report",
            data                = pdf_bytes,
            file_name           = f"claim_report_{claim_id}.pdf",
            mime                = "application/pdf",
            use_container_width = True,
        )

        # Feature 17: Auto-save claim to SQLite on PDF generation
        parts_for_db = [
            {"part_name": p.part_name, "severity": p.severity_label,
             "total": p.total_cost, "action": p.action}
            for p in estimate.parts
        ]
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
        st.caption(f"✅ Claim `{claim_id}` saved to history. View in **Analytics Dashboard ↗**")

    st.markdown('</div>', unsafe_allow_html=True)

else:
    # ── Landing state ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    for col, icon, title, desc in [
        (f1,"🔍","AI Detection + Fraud Check",
         "YOLOv8 detects 7 damage types. Duplicate image hashing, blur scoring & EXIF analysis run simultaneously."),
        (f2,"💰","Smart Cost Engine",
         "Car-type multipliers (Hatchback→Luxury), inflation factor & repair vs replace logic make pricing realistic."),
        (f3,"📄","PDF Report + Analytics",
         "Download a full report with NLP explanation. Every claim is saved to SQLite for the Analytics Dashboard."),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2.5rem;">{icon}</div>
                <div class="section-title" style="text-align:center;">{title}</div>
                <p style="color:#94a3b8; font-size:.9rem;">{desc}</p>
            </div>""", unsafe_allow_html=True)
