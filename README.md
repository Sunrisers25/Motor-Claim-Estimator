# 🚗 AI Motor Claim Estimator

An AI-powered hackathon prototype that analyzes car damage photos and instantly generates an automated repair cost estimate with a downloadable PDF report.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📤 Image Upload | Single or multiple images (JPG, PNG, WEBP) |
| 🔍 Damage Detection | YOLOv8 detects bumper, headlight, door, windshield, hood, scratch, dent |
| 📊 Severity Classification | Minor / Moderate / Severe with a 1–10 score |
| 💰 Cost Estimation | Parts cost + fixed labor per damaged part |
| ⚖️ Claim Decision | Auto-approved / Supervisor review / Manual inspection |
| 📄 PDF Report | Professional downloadable report with annotated images |

---

## 📁 Project Structure

```
Motor-Claim Estimator/
├── app.py               ← Streamlit UI (entry point)
├── detection.py         ← YOLOv8 damage detection
├── severity.py          ← Severity classification logic
├── cost_engine.py       ← Repair cost calculation
├── decision_engine.py   ← Claim decision rules
├── report_generator.py  ← PDF report generation
├── database.py          ← SQLite parts cost database
├── requirements.txt     ← Python dependencies
└── README.md
```

---

## 🚀 How to Run Locally

### Step 1 — Install Python 3.10+

Make sure Python 3.10 or above is installed:
```bash
python --version
```

### Step 2 — (Optional) Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⏳ First-time install downloads PyTorch + Ultralytics (~1–2 GB). Ensure a stable internet connection.

### Step 4 — Run the app

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

---

## 🖼️ Demo Instructions

### Using Simulation Mode (Default)
By default, `detection.py` runs in **SIMULATION MODE** — it generates realistic random damage detections without needing a trained model. This is perfect for hackathon demos.

Upload **any car image** (even a stock photo) and the system will:
1. Detect 1–4 random damage zones
2. Draw bounding boxes
3. Calculate costs
4. Generate a PDF report

### Using a Real YOLOv8 Model
To use a real fine-tuned model:
1. Place your model weights at `models/damage_yolov8.pt`
2. In `detection.py`, set `USE_SIMULATION = False`

---

## 💰 Parts Cost Database

| Part | Replacement Cost |
|---|---|
| Hood | ₹9,000 |
| Door | ₹8,000 |
| Windshield | ₹7,000 |
| Bumper | ₹6,000 |
| Headlight | ₹3,500 |
| Dent (repair) | ₹2,500 |
| Scratch (repair) | ₹1,500 |
| **Labor (per part)** | **₹2,000** |

### Severity multipliers
| Severity | Multiplier |
|---|---|
| Minor (< 5% image) | 40% of part cost |
| Moderate (5–15% image) | 70% of part cost |
| Severe (> 15% image) | 100% (full replacement) |

---

## ⚖️ Claim Decision Rules

| Total Estimate | Decision |
|---|---|
| < ₹25,000 | ✅ Auto Approved |
| ₹25,000 – ₹60,000 | ⚠️ Supervisor Review |
| > ₹60,000 | 🔴 Manual Inspection Required |

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **YOLOv8** (Ultralytics) — Damage detection
- **OpenCV** — Image preprocessing & annotation
- **Streamlit** — Web UI
- **SQLite** — Local parts cost database
- **ReportLab** — PDF generation
- **PyTorch** — YOLO backend

---

*Built for hackathon demonstration. No cloud, no Docker, runs 100% locally.*
