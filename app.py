import streamlit as st
import pandas as pd

from utils.data_loader import load_excel_data
from utils.dashboard import (
    create_kpi_section,
    project_collection_chart,
    monthly_target_chart,
    collection_efficiency_chart,
    overdue_chart,
    demand_collection_trend,
    top_defaulters_table,
    pending_registration_chart,
    category_breakdown_chart,
)
from utils.qa_engine import ask_gemini

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RAGHAV Group — CRM MIS Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #F4F6F9; }
    [data-testid="stSidebar"] { background: #1A3C6E; }
    [data-testid="stSidebar"] * { color: #fff !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stTextInput label { color: #CFD8DC !important; }
    h1, h2, h3 { color: #1A3C6E; }
    .block-container { padding-top: 1.5rem; }
    div[data-testid="metric-container"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────

st.markdown("""
<div style="
    background: linear-gradient(135deg,#1A3C6E 0%,#0D2040 100%);
    color:#fff; padding:22px 28px; border-radius:10px;
    margin-bottom:18px;
    display:flex; align-items:center; gap:14px;
">
    <div style="font-size:2.4rem;">🏢</div>
    <div>
        <div style="font-size:1.55rem;font-weight:700;
                    letter-spacing:0.5px;">
            RAGHAV Group — CRM Collection MIS
        </div>
        <div style="font-size:0.85rem;color:#90CAF9;margin-top:2px;">
            Enterprise-Grade Collection Dashboard | Mumbai Real Estate
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────

EXCEL_FILE = "data/Overall Collection Summary.xlsx"

with st.spinner("Loading CRM data from Excel…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data(EXCEL_FILE)
    except Exception as e:
        st.error(f"❌ Failed to load Excel: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────

st.sidebar.markdown("## 🔍 Filters")

all_projects = sorted(project_df["Project"].dropna().unique().tolist())
selected_projects = st.sidebar.multiselect(
    "Project",
    options=all_projects,
    default=all_projects,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size:0.78rem;opacity:0.7;margin-top:8px'>"
    "Real Estate CRM MIS v2.0<br>Powered by Streamlit + Gemini AI"
    "</div>",
    unsafe_allow_html=True,
)

# Apply filters
if selected_projects:
    filtered_df = project_df[project_df["Project"].isin(selected_projects)].copy()
else:
    filtered_df = project_df.copy()

# Recompute KPIs for filtered set
filtered_kpis = dict(kpis)
filtered_kpis["total_demand"]      = filtered_df["Actual Demand Raised (Cr)"].sum()
filtered_kpis["total_collection"]  = filtered_df["Collection Till Date (Cr)"].sum()
filtered_kpis["total_outstanding"] = filtered_df["Outstanding (Cr)"].sum()
filtered_kpis["monthly_coll"]      = filtered_df["Monthly Collection (Cr)"].sum()
filtered_kpis["daily_coll"]        = filtered_df["Daily Collection (Cr)"].sum()
filtered_kpis["total_live_bkgs"]   = int(filtered_df["Total Live Bookings"].sum())
filtered_kpis["pending_reg"]       = int(filtered_df["Pending Registrations"].sum())
filtered_kpis["pending_reg_45"]    = int(filtered_df["Pending Reg > 45 Days"].sum())
filtered_kpis["crm_monthly_tgt"]   = filtered_df["Collection Target (Cr)"].sum()
filtered_kpis["crm_monthly_ach"]   = filtered_df["Collection Achievement (Cr)"].sum()

# ─────────────────────────────────────────────────────────
# A — COLLECTION SUMMARY KPIs
# ─────────────────────────────────────────────────────────

st.markdown("## 📊 Collection Summary")
create_kpi_section(filtered_kpis, filtered_df)

# ─────────────────────────────────────────────────────────
# B — PROJECT WISE ANALYSIS
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 🏗️ Project-wise Analysis")

col_left, col_right = st.columns([3, 2])

with col_left:
    try:
        st.plotly_chart(
            project_collection_chart(filtered_df),
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"Chart unavailable: {e}")

with col_right:
    try:
        st.plotly_chart(
            collection_efficiency_chart(filtered_df),
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"Chart unavailable: {e}")

# ─────────────────────────────────────────────────────────
# C — MONTHLY TARGET vs ACHIEVEMENT
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 🎯 Monthly Target vs Achievement")

try:
    st.plotly_chart(monthly_target_chart(filtered_df), use_container_width=True)
except Exception as e:
    st.warning(f"Chart unavailable: {e}")

# ─────────────────────────────────────────────────────────
# D — OVERDUE / OUTSTANDING ANALYSIS
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## ⚠️ Outstanding & Overdue Analysis")

col_a, col_b = st.columns([2, 3])

with col_a:
    try:
        st.plotly_chart(overdue_chart(filtered_df), use_container_width=True)
    except Exception as e:
        st.warning(f"Chart unavailable: {e}")

with col_b:
    try:
        st.plotly_chart(pending_registration_chart(filtered_df), use_container_width=True)
    except Exception as e:
        st.warning(f"Chart unavailable: {e}")

# ─────────────────────────────────────────────────────────
# E — DEMAND vs COLLECTION TREND
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 📈 Demand vs Collection Trend")

try:
    st.plotly_chart(demand_collection_trend(filtered_df), use_container_width=True)
except Exception as e:
    st.warning(f"Chart unavailable: {e}")

# ─────────────────────────────────────────────────────────
# F — CATEGORY BREAKDOWN
# ─────────────────────────────────────────────────────────

if not category_df.empty:
    st.markdown("---")
    st.markdown("## 📂 Category-wise Collection Breakdown")
    try:
        st.plotly_chart(category_breakdown_chart(category_df), use_container_width=True)
    except Exception as e:
        st.warning(f"Chart unavailable: {e}")

    with st.expander("View Category Data Table"):
        st.dataframe(category_df, use_container_width=True)

# ─────────────────────────────────────────────────────────
# G — TOP DEFAULTERS / OUTSTANDING
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 🔴 Top Outstanding Projects")

try:
    defaulters = top_defaulters_table(filtered_df)
    st.dataframe(
        defaulters.style.background_gradient(
            subset=["Outstanding (Cr)"], cmap="Reds"
        ).format({
            "Actual Demand Raised (Cr)": "₹{:.2f} Cr",
            "Collection Till Date (Cr)": "₹{:.2f} Cr",
            "Outstanding (Cr)":          "₹{:.2f} Cr",
        }),
        use_container_width=True,
    )
except Exception as e:
    st.warning(f"Table unavailable: {e}")

# ─────────────────────────────────────────────────────────
# H — CRM DATA TABLE
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 📋 Full CRM Project Data")

with st.expander("Expand to view full project data table"):
    try:
        display_cols = [
            "Project", "Total Live Bookings",
            "Actual Demand Raised (Cr)", "Collection Till Date (Cr)",
            "Outstanding (Cr)", "Monthly Collection (Cr)",
            "Collection Target (Cr)", "Collection Achievement (Cr)",
            "Achievement %", "Pending Registrations", "Pending Reg > 45 Days",
        ]
        disp_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()
        disp_df["Achievement %"] = (disp_df["Achievement %"] * 100).round(1)
        st.dataframe(
            disp_df.style.format({
                "Actual Demand Raised (Cr)":    "₹{:.2f} Cr",
                "Collection Till Date (Cr)":    "₹{:.2f} Cr",
                "Outstanding (Cr)":             "₹{:.2f} Cr",
                "Monthly Collection (Cr)":      "₹{:.2f} Cr",
                "Collection Target (Cr)":       "₹{:.2f} Cr",
                "Collection Achievement (Cr)":  "₹{:.2f} Cr",
                "Achievement %":                "{:.1f}%",
            }),
            use_container_width=True,
        )
    except Exception as e:
        st.dataframe(filtered_df, use_container_width=True)
        st.caption(f"Note: Styling skipped — {e}")

# ─────────────────────────────────────────────────────────
# I — EXPORT
# ─────────────────────────────────────────────────────────

st.markdown("---")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered CRM Data (CSV)",
    data=csv_data,
    file_name="raghav_crm_export.csv",
    mime="text/csv",
)

# ─────────────────────────────────────────────────────────
# J — GEMINI AI Q&A
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## 🤖 AI CRM Q&A — Ask Gemini")

st.markdown("""
<div style="background:#E3F2FD;border-left:4px solid #1A3C6E;
            padding:12px 16px;border-radius:6px;margin-bottom:12px;">
    <b>Ask questions about your CRM data:</b><br>
    <span style="color:#555;font-size:0.88rem;">
    • Which project has the highest outstanding?<br>
    • What is the collection efficiency of each project?<br>
    • How many pending registrations are > 45 days?<br>
    • Which project is closest to its monthly target?<br>
    • Summarise the overall CRM performance.
    </span>
</div>
""", unsafe_allow_html=True)

user_question = st.text_area(
    "Your question:",
    placeholder="e.g. Which project has the lowest collection efficiency?",
    height=100,
)

if st.button("🔍 Get AI Answer", type="primary"):
    if not user_question.strip():
        st.warning("Please enter a question before submitting.")
    else:
        # Check API key present
        try:
            _key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            st.error(
                "⚠️ **GEMINI_API_KEY not configured.**  \n"
                "Add it under **Settings → Secrets** as `GEMINI_API_KEY = 'your-key'`."
            )
            st.stop()

        with st.spinner("Analysing CRM data with Gemini…"):
            try:
                answer = ask_gemini(
                    question=user_question,
                    project_df=filtered_df,
                    category_df=category_df,
                    kpis=filtered_kpis,
                )
                st.success("✅ Answer ready")
                st.markdown(
                    f"""
                    <div style="background:#fff;border-left:4px solid #2E7D32;
                                padding:16px;border-radius:6px;
                                box-shadow:0 1px 4px rgba(0,0,0,0.08);">
                    {answer.replace(chr(10),'<br>')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"Gemini error: {e}")

# ─────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:0.78rem;'>"
    "RAGHAV Group CRM MIS Dashboard | Powered by Streamlit + Gemini AI | Mumbai Real Estate"
    "</div>",
    unsafe_allow_html=True,
)
