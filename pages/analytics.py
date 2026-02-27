"""
pages/analytics.py
------------------
Feature 18: Analytics Dashboard — Streamlit Multi-Page (Page 2)

Streamlit automatically discovers files in the `pages/` directory and
adds them as navigation tabs. No routing code needed.

Displays:
  - Total claims processed
  - Average claim cost
  - Approval rate
  - Most damaged part
  - Decision breakdown bar chart
  - Part frequency bar chart
  - Full claim history table
"""

import sys
import os

# Ensure parent directory is on sys.path so local modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

from database import get_all_claims, get_claim_stats

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "Analytics Dashboard",
    page_icon   = "📊",
    layout      = "wide",
    initial_sidebar_state = "collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #e2e8f0;
}
.dash-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #6d28d9 100%);
    border-radius: 16px; padding: 1.8rem 2.5rem; margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(109, 40, 217, 0.3); text-align: center;
}
.dash-header h1 { font-size: 2.2rem; font-weight: 700; color: #fff; margin: 0; }
.dash-header p  { color: #c4b5fd; font-size: 1rem; margin-top: 0.4rem; }
.kpi-card {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 1.2rem 1rem; text-align: center;
    backdrop-filter: blur(12px);
}
.kpi-value { font-size: 2rem; font-weight: 700; color: #a78bfa; }
.kpi-label { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }
.section-title {
    color: #a78bfa; font-size: 0.9rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; margin: 1rem 0 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <h1>📊 Claims Analytics Dashboard</h1>
    <p>Real-time insights from processed motor insurance claims</p>
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
stats  = get_claim_stats()
claims = get_all_claims()

if stats["total_claims"] == 0:
    st.info("📭 No claims have been processed yet. Upload car damage images on the main page and generate a PDF report to save your first claim.")
    st.stop()

# ── KPI Row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
for col, value, label in [
    (k1, str(stats["total_claims"]),                "Total Claims"),
    (k2, f"₹{stats['avg_cost']:,.0f}",              "Avg Claim Cost"),
    (k3, f"{stats['approval_rate']:.1f}%",           "Auto-Approval Rate"),
    (k4, stats["most_damaged_part"].capitalize(),    "Most Damaged Part"),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2, gap="large")

with chart_col1:
    st.markdown('<p class="section-title">⚖️ Decision Breakdown</p>', unsafe_allow_html=True)
    if stats["decision_breakdown"]:
        dec_df = pd.DataFrame(
            list(stats["decision_breakdown"].items()),
            columns=["Decision", "Count"]
        ).set_index("Decision")
        st.bar_chart(dec_df, use_container_width=True, color="#a78bfa")

with chart_col2:
    st.markdown('<p class="section-title">🔩 Most Frequently Damaged Parts</p>', unsafe_allow_html=True)
    if stats.get("part_frequency"):
        part_df = pd.DataFrame(
            sorted(stats["part_frequency"].items(), key=lambda x: x[1], reverse=True),
            columns=["Part", "Frequency"]
        ).set_index("Part")
        st.bar_chart(part_df, use_container_width=True, color="#38bdf8")

# ── Cost Distribution ─────────────────────────────────────────────────────────
if claims:
    st.markdown('<p class="section-title">💰 Claim Cost Distribution</p>', unsafe_allow_html=True)
    cost_df = pd.DataFrame(claims)
    if "total_cost" in cost_df.columns and len(cost_df) > 1:
        st.bar_chart(
            cost_df[["claim_id", "total_cost"]].set_index("claim_id"),
            use_container_width=True,
            color="#10b981",
        )

# ── Full History Table ────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📋 Full Claim History</p>', unsafe_allow_html=True)
if claims:
    display_df = pd.DataFrame(claims)
    # Rename and format for display
    display_df["total_cost"] = display_df["total_cost"].apply(lambda x: f"₹{x:,.0f}")
    display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.caption(f"Data sourced from local SQLite database • {stats['total_claims']} records • Auto-refreshed on page load")
