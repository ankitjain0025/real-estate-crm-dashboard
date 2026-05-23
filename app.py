import streamlit as st
import pandas as pd

from utils.data_loader import load_excel_data
from utils.multi_month_loader import load_all_months, get_portfolio_monthly
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
from utils.mom_charts import (
    portfolio_efficiency_trend,
    portfolio_target_vs_achievement,
    project_achievement_trend,
    outstanding_trend,
    monthly_collection_stacked,
    forecast_accuracy_chart,
    pending_reg_trend,
    mom_heatmap,
)
from utils.qa_engine import ask_gemini

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="RAGHAV Group — CRM MIS Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F4F6F9; }
[data-testid="stSidebar"] { background: #1A3C6E; }
[data-testid="stSidebar"] * { color: #ECEFF1 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #CFD8DC !important; }
h1, h2, h3 { color: #1A3C6E; }
.block-container { padding-top: 1.2rem; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background: #fff; border-radius: 6px 6px 0 0;
    padding: 8px 18px; font-weight: 600; color: #1A3C6E;
}
.stTabs [aria-selected="true"] {
    background: #1A3C6E !important; color: #fff !important;
}
div[data-testid="stHorizontalBlock"] { gap: 0.6rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1A3C6E 0%,#0D2040 100%);
            color:#fff;padding:20px 28px;border-radius:10px;
            margin-bottom:16px;display:flex;align-items:center;gap:16px;">
  <div style="font-size:2.2rem;">🏢</div>
  <div>
    <div style="font-size:1.5rem;font-weight:700;letter-spacing:0.4px;">
      RAGHAV Group — CRM Collection MIS
    </div>
    <div style="font-size:0.82rem;color:#90CAF9;margin-top:3px;">
      Enterprise Collection Dashboard · Mumbai Real Estate
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
with st.spinner("Loading CRM data…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data()
    except Exception as e:
        st.error(f"❌ Failed to load Excel file: {e}")
        st.info("Make sure **'data/Overall Collection Summary.xlsx'** exists in your repo.")
        st.stop()

with st.spinner("Loading month-on-month data…"):
    try:
        mom_df       = load_all_months()
        portfolio_df = get_portfolio_monthly(mom_df) if not mom_df.empty else pd.DataFrame()
    except Exception as e:
        mom_df       = pd.DataFrame()
        portfolio_df = pd.DataFrame()

# ─────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────
st.sidebar.markdown("## 🔍 Filters")

all_projects = sorted(project_df["Project"].dropna().unique().tolist())
selected_projects = st.sidebar.multiselect(
    "Select Projects", options=all_projects, default=all_projects
)

if not mom_df.empty:
    all_months = mom_df["Month"].unique().tolist()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Month-on-Month")
    selected_months = st.sidebar.multiselect(
        "Select Months", options=all_months, default=all_months
    )
else:
    selected_months = []

st.sidebar.markdown("---")

# Gemini status badge
try:
    _k = st.secrets.get("GEMINI_API_KEY", "")
    has_key = bool(_k and str(_k).strip() and _k != "your-gemini-api-key-here")
except Exception:
    has_key = False

if has_key:
    st.sidebar.markdown(
        "<div style='background:#1B5E20;border-radius:6px;padding:8px 12px;"
        "font-size:0.78rem;'>🟢 Gemini AI — Connected</div>",
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        "<div style='background:#7f1a1a;border-radius:6px;padding:8px 12px;"
        "font-size:0.78rem;'>🔴 Gemini Key Not Set — Add in Secrets</div>",
        unsafe_allow_html=True,
    )

if not mom_df.empty:
    st.sidebar.markdown(
        f"<div style='font-size:0.76rem;opacity:0.65;margin-top:8px;'>"
        f"📂 {len(all_months)} monthly file(s) loaded</div>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown(
    "<div style='font-size:0.74rem;opacity:0.55;margin-top:14px;'>"
    "RAGHAV CRM MIS v3.0<br>Streamlit + Gemini AI</div>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────
if not selected_projects:
    selected_projects = all_projects

filtered_df = project_df[project_df["Project"].isin(selected_projects)].copy()

# Recalculate KPIs from filtered data
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

filtered_mom       = pd.DataFrame()
filtered_portfolio = pd.DataFrame()
if not mom_df.empty and selected_months:
    filtered_mom = mom_df[
        mom_df["Project"].isin(selected_projects) &
        mom_df["Month"].isin(selected_months)
    ].copy()
    filtered_portfolio = get_portfolio_monthly(filtered_mom)

# ─────────────────────────────────────────
# DATA QUALITY NOTICE
# ─────────────────────────────────────────
if not mom_df.empty:
    mar_data = mom_df[mom_df["Month"].str.startswith("Mar")]
    apr_data = mom_df[mom_df["Month"].str.startswith("Apr")]
    if not mar_data.empty and not apr_data.empty:
        mar_val = mar_data["Collection_Cr"].sum()
        apr_val = apr_data["Collection_Cr"].sum()
        if abs(mar_val - apr_val) < 0.01:
            st.warning(
                "⚠️ **Data Notice:** The March 2026 and April 2026 files contain "
                "identical data (both dated 07 May 2026). "
                "Please upload the correct monthly files when available for accurate MoM trends."
            )

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Current Month Dashboard",
    "📈 Month-on-Month Trends",
    "🤖 AI CRM Assistant",
])

# ═══════════════════════════════════════════
# TAB 1 — CURRENT MONTH
# ═══════════════════════════════════════════
with tab1:

    # A. KPI Row
    st.markdown("### 📊 Collection Summary")
    create_kpi_section(filtered_kpis, filtered_df)

    # B. Project Analysis
    st.markdown("---")
    st.markdown("### 🏗️ Project-wise Analysis")
    c1, c2 = st.columns([3, 2])
    with c1:
        try:
            st.plotly_chart(project_collection_chart(filtered_df), use_container_width=True)
        except Exception as e:
            st.warning(f"Chart error: {e}")
    with c2:
        try:
            st.plotly_chart(collection_efficiency_chart(filtered_df), use_container_width=True)
        except Exception as e:
            st.warning(f"Chart error: {e}")

    # C. Monthly Target vs Achievement
    st.markdown("---")
    st.markdown("### 🎯 Monthly Target vs Achievement vs Forecast")
    try:
        st.plotly_chart(monthly_target_chart(filtered_df), use_container_width=True)
    except Exception as e:
        st.warning(f"Chart error: {e}")

    # D. Outstanding & Pending Reg
    st.markdown("---")
    st.markdown("### ⚠️ Outstanding & Pending Registrations")
    c3, c4 = st.columns([2, 3])
    with c3:
        try:
            st.plotly_chart(overdue_chart(filtered_df), use_container_width=True)
        except Exception as e:
            st.warning(f"Chart error: {e}")
    with c4:
        try:
            st.plotly_chart(pending_registration_chart(filtered_df), use_container_width=True)
        except Exception as e:
            st.warning(f"Chart error: {e}")

    # E. Demand vs Collection Trend
    st.markdown("---")
    st.markdown("### 📈 Demand vs Collection vs Outstanding — Project Trend")
    try:
        st.plotly_chart(demand_collection_trend(filtered_df), use_container_width=True)
    except Exception as e:
        st.warning(f"Chart error: {e}")

    # F. Category Breakdown
    if not category_df.empty:
        st.markdown("---")
        st.markdown("### 📂 Category-wise Collection Breakdown")
        try:
            st.plotly_chart(category_breakdown_chart(category_df), use_container_width=True)
        except Exception as e:
            st.warning(f"Chart error: {e}")
        with st.expander("📋 View Category Data Table"):
            disp_cat = category_df.copy()
            if "Achievement %" in disp_cat.columns:
                disp_cat["Achievement %"] = (disp_cat["Achievement %"] * 100).round(1)
            st.dataframe(disp_cat, use_container_width=True, hide_index=True)

    # G. Top Outstanding
    st.markdown("---")
    st.markdown("### 🔴 Top Projects by Outstanding")
    try:
        defaulters = top_defaulters_table(filtered_df)
        st.dataframe(
            defaulters.style
                .background_gradient(subset=["Outstanding (Cr)"], cmap="Reds")
                .format({
                    "Actual Demand Raised (Cr)": "₹ {:.2f} Cr",
                    "Collection Till Date (Cr)": "₹ {:.2f} Cr",
                    "Outstanding (Cr)":          "₹ {:.2f} Cr",
                }),
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"Table error: {e}")

    # H. Full CRM Table
    st.markdown("---")
    with st.expander("📋 Full CRM Project Data Table"):
        try:
            disp_cols = [
                "Project", "Total Live Bookings",
                "Actual Demand Raised (Cr)", "Collection Till Date (Cr)",
                "Outstanding (Cr)", "Monthly Collection (Cr)",
                "Collection Target (Cr)", "Collection Achievement (Cr)",
                "Achievement %", "Pending Registrations", "Pending Reg > 45 Days",
            ]
            disp_df = filtered_df[[c for c in disp_cols if c in filtered_df.columns]].copy()
            if "Achievement %" in disp_df.columns:
                disp_df["Achievement %"] = (disp_df["Achievement %"] * 100).round(1)
            st.dataframe(
                disp_df.style.format({
                    "Actual Demand Raised (Cr)":   "₹ {:.2f} Cr",
                    "Collection Till Date (Cr)":   "₹ {:.2f} Cr",
                    "Outstanding (Cr)":            "₹ {:.2f} Cr",
                    "Monthly Collection (Cr)":     "₹ {:.2f} Cr",
                    "Collection Target (Cr)":      "₹ {:.2f} Cr",
                    "Collection Achievement (Cr)": "₹ {:.2f} Cr",
                    "Achievement %":               "{:.1f}%",
                }),
                use_container_width=True,
            )
        except Exception:
            st.dataframe(filtered_df, use_container_width=True)

    # I. Export
    st.markdown("---")
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️  Download Filtered CRM Data as CSV",
        data=csv_bytes,
        file_name="raghav_crm_export.csv",
        mime="text/csv",
    )

# ═══════════════════════════════════════════
# TAB 2 — MONTH-ON-MONTH TRENDS
# ═══════════════════════════════════════════
with tab2:

    if filtered_mom.empty or filtered_portfolio.empty:
        st.info(
            "📂 **No multi-month data loaded.**\n\n"
            "Ensure files are named correctly inside `data/`:\n\n"
            "```\nOverall Collection Summary - Mar 2026.xlsx\n"
            "Overall Collection Summary - Apr 2026.xlsx\n"
            "Overall Collection Summary - May 2026.xlsx\n```"
        )
    else:
        months_in_view = filtered_portfolio["Month"].tolist()

        # Portfolio MoM snapshot tiles
        st.markdown("### 📊 Portfolio — Month-on-Month Performance")
        tile_cols = st.columns(min(len(months_in_view), 5))
        for i, row in filtered_portfolio.iterrows():
            if i >= len(tile_cols):
                break
            ach_pct = row.get("Achievement_Pct", 0)
            eff     = row.get("Collection_Efficiency_Pct", 0)
            ach     = row.get("Monthly_Achievement_Cr", 0)
            tgt     = row.get("Monthly_Target_Cr", 0)
            col_hex = "#2E7D32" if ach_pct >= 90 else ("#E65100" if ach_pct >= 60 else "#C62828")
            tile_cols[i].markdown(
                f"""<div style="background:#fff;border-left:4px solid {col_hex};
                    border-radius:6px;padding:12px 14px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.08);">
                  <div style="font-size:0.72rem;color:#777;font-weight:600;
                              text-transform:uppercase;">{row['Month']}</div>
                  <div style="font-size:1.25rem;font-weight:700;color:{col_hex};">
                    ₹{ach:.2f} Cr</div>
                  <div style="font-size:0.72rem;color:#999;">
                    {ach_pct:.1f}% of ₹{tgt:.2f} Cr</div>
                  <div style="font-size:0.72rem;color:#555;margin-top:2px;">
                    Eff: {eff:.1f}%</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Row 1: Efficiency + Target vs Achievement
        st.markdown("### 📈 Core Performance")
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            try:
                st.plotly_chart(portfolio_efficiency_trend(filtered_portfolio), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")
        with r1c2:
            try:
                st.plotly_chart(portfolio_target_vs_achievement(filtered_portfolio), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")

        # Row 2: Project achievement + Outstanding trend
        st.markdown("---")
        st.markdown("### 🏗️ Project-level Trends")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            try:
                st.plotly_chart(project_achievement_trend(filtered_mom), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")
        with r2c2:
            try:
                st.plotly_chart(outstanding_trend(filtered_mom), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")

        # Row 3: Stacked collection + Forecast accuracy
        st.markdown("---")
        st.markdown("### 💰 Collection & Forecast Analysis")
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            try:
                st.plotly_chart(monthly_collection_stacked(filtered_mom), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")
        with r3c2:
            try:
                st.plotly_chart(forecast_accuracy_chart(filtered_mom), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")

        # Row 4: Pending reg trend + Heatmap
        st.markdown("---")
        st.markdown("### 📋 Registrations & MoM Heatmap")
        r4c1, r4c2 = st.columns(2)
        with r4c1:
            try:
                st.plotly_chart(pending_reg_trend(filtered_mom), use_container_width=True)
            except Exception as e:
                st.warning(f"Chart error: {e}")
        with r4c2:
            metric_options = {
                "Achievement % vs Target":    "Achievement_Pct",
                "Collection Efficiency %":    "Collection_Efficiency_Pct",
                "Outstanding (₹ Cr)":         "Outstanding_Cr",
                "Monthly Collection (₹ Cr)":  "Monthly_Collection_Cr",
            }
            chosen_label = st.selectbox("Heatmap Metric", list(metric_options.keys()))
            try:
                st.plotly_chart(
                    mom_heatmap(filtered_mom, metric_options[chosen_label]),
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Chart error: {e}")

        # MoM data table
        st.markdown("---")
        with st.expander("📄 Full Month-on-Month Data Table"):
            disp_mom = filtered_mom[[c for c in [
                "Month", "Project",
                "Monthly_Target_Cr", "Monthly_Achievement_Cr", "Achievement_Pct",
                "Forecast_Cr", "Collection_Efficiency_Pct",
                "Outstanding_Cr", "Pending_Reg", "Pending_Reg_GT45",
            ] if c in filtered_mom.columns]].copy()
            disp_mom.columns = [
                "Month", "Project",
                "Target (Cr)", "Achievement (Cr)", "Ach %",
                "Forecast (Cr)", "Efficiency %",
                "Outstanding (Cr)", "Pending Reg", "Pending >45d",
            ][:len(disp_mom.columns)]
            st.dataframe(disp_mom, use_container_width=True, hide_index=True)

        mom_csv = filtered_mom.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️  Download MoM Data as CSV",
            data=mom_csv,
            file_name="raghav_crm_mom_export.csv",
            mime="text/csv",
        )

# ═══════════════════════════════════════════
# TAB 3 — AI Q&A
# ═══════════════════════════════════════════
with tab3:

    st.markdown("### 🤖 AI CRM Assistant — Ask Gemini")
    st.markdown("""
    <div style="background:#E3F2FD;border-left:4px solid #1A3C6E;
                padding:12px 16px;border-radius:6px;margin-bottom:14px;
                font-size:0.88rem;color:#333;">
        <b>Ask questions about your CRM data — current month or month-on-month trends:</b><br>
        • Which project has the highest outstanding?<br>
        • What is the collection efficiency of each project?<br>
        • Which project consistently missed its monthly target?<br>
        • Compare March vs May collection for RAGHAV Ananta<br>
        • Which month had the best forecast accuracy portfolio-wide?<br>
        • Is the outstanding for RAGHAV Avenue improving month on month?
    </div>
    """, unsafe_allow_html=True)

    # Quick-question chips
    st.markdown("**Quick questions — click to populate:**")
    chips = [
        "Which project has the highest outstanding?",
        "What is collection efficiency by project?",
        "Which project missed its monthly target?",
        "Show outstanding trend month on month",
        "Which category has the lowest achievement %?",
        "How many pending registrations are over 45 days?",
    ]
    chip_cols = st.columns(3)
    preset_q = st.session_state.get("preset_q", "")
    for i, chip in enumerate(chips):
        with chip_cols[i % 3]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                st.session_state["preset_q"] = chip
                st.rerun()

    user_q = st.text_area(
        "Your question:",
        value=st.session_state.get("preset_q", ""),
        placeholder="e.g. Which project has the lowest collection efficiency this month?",
        height=85,
        key="qa_textarea",
    )

    if st.button("🔍  Get AI Answer", type="primary", use_container_width=False):
        if not user_q.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analysing CRM data with Gemini…"):
                try:
                    answer = ask_gemini(
                        question=user_q,
                        project_df=filtered_df,
                        category_df=category_df,
                        kpis=filtered_kpis,
                        mom_df=filtered_mom if not filtered_mom.empty else None,
                    )
                    st.markdown(
                        f"""<div style="background:#fff;border-left:4px solid #2E7D32;
                            padding:16px 18px;border-radius:6px;margin-top:10px;
                            box-shadow:0 1px 4px rgba(0,0,0,0.07);
                            line-height:1.75;font-size:0.92rem;">
                        {answer.replace(chr(10), '<br>')}
                        </div>""",
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.error(f"Error calling Gemini: {e}")

# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:0.76rem;padding:6px 0 12px;'>"
    "RAGHAV Group CRM MIS Dashboard v3.0 &nbsp;|&nbsp; "
    "Powered by Streamlit + Gemini AI &nbsp;|&nbsp; Mumbai Real Estate"
    "</div>",
    unsafe_allow_html=True,
)
