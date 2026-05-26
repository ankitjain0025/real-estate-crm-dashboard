import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_excel_data
from utils.multi_month_loader import load_all_months, get_portfolio_monthly
from utils.rm_config import RM_MAP, RM_COLORS, all_rms, get_rm
from utils.dashboard import (
    create_kpi_section, project_collection_chart, monthly_target_chart,
    collection_efficiency_chart, overdue_chart, demand_collection_trend,
    top_defaulters_table, pending_registration_chart, category_breakdown_chart,
)
from utils.mom_charts import (
    portfolio_efficiency_trend, portfolio_target_vs_achievement,
    project_achievement_trend, outstanding_trend, monthly_collection_stacked,
    forecast_accuracy_chart, pending_reg_trend, mom_heatmap,
    spillover_trend, sales_contribution_chart,
)
from utils.qa_engine import ask_gemini

st.set_page_config(page_title="RAGHAV Group — CRM MIS", page_icon="🏢",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#F0F4F8;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0D2040 0%,#1A3C6E 100%);}
[data-testid="stSidebar"] *{color:#ECEFF1!important;}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{color:#B0BEC5!important;}
h1,h2,h3{color:#1A3C6E;}
.block-container{padding-top:1rem;}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:transparent;}
.stTabs [data-baseweb="tab"]{background:#fff;border-radius:8px 8px 0 0;
    padding:10px 20px;font-weight:600;color:#1A3C6E;border:1px solid #ddd;}
.stTabs [aria-selected="true"]{background:#1A3C6E!important;
    color:#fff!important;border-color:#1A3C6E!important;}
</style>""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(135deg,#1A3C6E 0%,#0D2040 100%);
            color:#fff;padding:20px 28px;border-radius:12px;margin-bottom:18px;
            box-shadow:0 4px 20px rgba(0,0,0,0.15);">
  <div style="display:flex;align-items:center;gap:16px;">
    <div style="font-size:2.4rem;">🏢</div>
    <div>
      <div style="font-size:1.6rem;font-weight:800;">RAGHAV Group — CRM Collection MIS</div>
      <div style="font-size:0.82rem;color:#90CAF9;margin-top:3px;">
        Enterprise Collection Dashboard · Mumbai Real Estate · Powered by Gemini AI</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading CRM data…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data()
    except Exception as e:
        st.error(f"❌ {e}"); st.stop()

project_df["RM"] = project_df["Project"].apply(get_rm)

with st.spinner("Loading month-on-month data…"):
    try:
        mom_df       = load_all_months()
        portfolio_df = get_portfolio_monthly(mom_df) if not mom_df.empty else pd.DataFrame()
    except Exception as e:
        mom_df = pd.DataFrame(); portfolio_df = pd.DataFrame()

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🔍 Filters")
all_projects = sorted(project_df["Project"].dropna().unique().tolist())
sel_projects  = st.sidebar.multiselect("Projects", all_projects, default=all_projects)

sel_months = []
if not mom_df.empty:
    all_months = mom_df["Month"].unique().tolist()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Month-on-Month")
    sel_months = st.sidebar.multiselect("Months", all_months, default=all_months)

st.sidebar.markdown("---")
try:
    _k = st.secrets["GEMINI_API_KEY"]
    has_key = bool(_k and str(_k).strip() and str(_k).strip() != "your-gemini-api-key-here")
except Exception:
    has_key = False

bg = "#1B5E20" if has_key else "#7f1a1a"
tx = "🟢 Gemini AI — Connected" if has_key else "🔴 Gemini Key Not Set"
st.sidebar.markdown(
    f"<div style='background:{bg};border-radius:6px;padding:8px 12px;"
    f"font-size:0.78rem;'>{tx}</div>", unsafe_allow_html=True)
if not mom_df.empty:
    st.sidebar.markdown(
        f"<div style='font-size:0.74rem;opacity:0.6;margin-top:6px;'>"
        f"📂 {len(all_months)} monthly file(s) loaded</div>", unsafe_allow_html=True)

# ── Apply filters ──────────────────────────────────────────────────────────────
if not sel_projects: sel_projects = all_projects
fdf = project_df[project_df["Project"].isin(sel_projects)].copy()

fkpis = dict(kpis)
fkpis.update({
    "total_demand":      fdf["Actual Demand Raised (Cr)"].sum(),
    "total_collection":  fdf["Collection Till Date (Cr)"].sum(),
    "total_outstanding": fdf["Outstanding (Cr)"].sum(),
    "monthly_coll":      fdf["Monthly Collection (Cr)"].sum(),
    "daily_coll":        fdf["Daily Collection (Cr)"].sum(),
    "total_live_bkgs":   int(fdf["Total Live Bookings"].sum()),
    "pending_reg":       int(fdf["Pending Registrations"].sum()),
    "pending_reg_45":    int(fdf["Pending Reg > 45 Days"].sum()),
    "crm_monthly_tgt":   fdf["Collection Target (Cr)"].sum(),
    "crm_monthly_ach":   fdf["Collection Achievement (Cr)"].sum(),
    "spillover_total":   fdf["SpillOver_Target_Cr"].sum(),
    "collection_eff":    round(fdf["Collection Till Date (Cr)"].sum() /
                               fdf["Actual Demand Raised (Cr)"].sum() * 100, 2)
                         if fdf["Actual Demand Raised (Cr)"].sum() else 0,
})

fmom = pd.DataFrame(); fport = pd.DataFrame()
if not mom_df.empty:
    _months_use = sel_months if sel_months else mom_df["Month"].unique().tolist()
    _projs_use  = sel_projects if sel_projects else mom_df["Project"].unique().tolist()
    fmom  = mom_df[mom_df["Project"].isin(_projs_use) & mom_df["Month"].isin(_months_use)].copy()
    fport = get_portfolio_monthly(fmom)

if not mom_df.empty:
    mar = mom_df[mom_df["Month"].str.startswith("Mar")]
    apr = mom_df[mom_df["Month"].str.startswith("Apr")]
    if not mar.empty and not apr.empty and abs(mar["Collection_Cr"].sum()-apr["Collection_Cr"].sum())<0.01:
        st.warning("⚠️ March 2026 and April 2026 files contain identical data. Upload correct files for accurate MoM trends.")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Month",
    "📈 Month-on-Month Trends",
    "🤖 AI CRM Assistant",
    "👤 RM Performance",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CURRENT MONTH
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 📊 Collection Summary")
    create_kpi_section(fkpis, fdf)

    st.markdown("---")
    st.markdown("### 🏗️ Project-wise Analysis")
    c1, c2 = st.columns([3,2])
    with c1:
        try: st.plotly_chart(project_collection_chart(fdf), use_container_width=True)
        except Exception as e: st.warning(f"Chart error: {e}")
    with c2:
        try: st.plotly_chart(collection_efficiency_chart(fdf), use_container_width=True)
        except Exception as e: st.warning(f"Chart error: {e}")

    st.markdown("---")
    st.markdown("### 🎯 Outstanding (Month Start) → Target → Forecast → Achievement")
    try: st.plotly_chart(monthly_target_chart(fdf), use_container_width=True)
    except Exception as e: st.warning(f"Chart error: {e}")

    st.markdown("---")
    st.markdown("### ⚠️ Outstanding Distribution & Pending Registrations")
    c3, c4 = st.columns([2,3])
    with c3:
        try: st.plotly_chart(overdue_chart(fdf), use_container_width=True)
        except Exception as e: st.warning(f"Chart error: {e}")
    with c4:
        try: st.plotly_chart(pending_registration_chart(fdf), use_container_width=True)
        except Exception as e: st.warning(f"Chart error: {e}")

    if not category_df.empty:
        st.markdown("---")
        st.markdown("### 📂 Category-wise Breakdown (Target → Forecast → Achievement)")
        st.caption("OCR & New Bookings are Sales team collections — CRM team tracks & reports.")
        try: st.plotly_chart(category_breakdown_chart(category_df), use_container_width=True)
        except Exception as e: st.warning(f"Chart error: {e}")

    st.markdown("---")
    st.markdown("### 🔴 Top Projects by Outstanding")
    try:
        st.dataframe(top_defaulters_table(fdf).style.format({
            "Actual Demand Raised (Cr)":"₹ {:.2f} Cr",
            "Collection Till Date (Cr)":"₹ {:.2f} Cr",
            "Outstanding (Cr)":         "₹ {:.2f} Cr",
        }), use_container_width=True)
    except Exception as e: st.warning(f"Table error: {e}")

    st.markdown("---")
    with st.expander("📋 Full CRM Data Table"):
        disp_cols = ["Project","RM","Total Live Bookings","Actual Demand Raised (Cr)",
                     "Collection Till Date (Cr)","Outstanding (Cr)","SpillOver_Target_Cr",
                     "Monthly Collection (Cr)","Collection Target (Cr)",
                     "Collection Achievement (Cr)","Achievement %",
                     "Pending Registrations","Pending Reg > 45 Days"]
        dd = fdf[[c for c in disp_cols if c in fdf.columns]].copy()
        if "Achievement %" in dd.columns:
            dd["Achievement %"] = (dd["Achievement %"]*100).round(1)
        dd["Pending Registrations"] = dd["Pending Registrations"].astype(int)
        dd["Pending Reg > 45 Days"] = dd["Pending Reg > 45 Days"].astype(int)
        dd = dd.rename(columns={"SpillOver_Target_Cr":"Outstanding Start (Cr)"})
        st.dataframe(dd.style.format({
            "Actual Demand Raised (Cr)":  "₹ {:.2f} Cr",
            "Collection Till Date (Cr)":  "₹ {:.2f} Cr",
            "Outstanding (Cr)":           "₹ {:.2f} Cr",
            "Outstanding Start (Cr)":     "₹ {:.2f} Cr",
            "Monthly Collection (Cr)":    "₹ {:.2f} Cr",
            "Collection Target (Cr)":     "₹ {:.2f} Cr",
            "Collection Achievement (Cr)":"₹ {:.2f} Cr",
            "Achievement %":              "{:.1f}%",
        }), use_container_width=True)

    st.download_button("⬇️ Download CRM Data CSV",
        fdf.to_csv(index=False).encode("utf-8"), "raghav_crm.csv", "text/csv")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MONTH-ON-MONTH TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    if fmom.empty or fport.empty:
        st.info("📂 Upload monthly files:\n`Overall Collection Summary - Mar 2026.xlsx` etc.")
    else:
        months_in_view = fport["Month"].tolist()

        # Portfolio tiles
        st.markdown("### 📊 Portfolio — Monthly Performance")
        tcols = st.columns(min(len(months_in_view), 5))
        for i, row in fport.iterrows():
            if i >= len(tcols): break
            ap = row.get("Achievement_Pct",0)
            ef = row.get("Collection_Efficiency_Pct",0)
            cl = "#2E7D32" if ap>=90 else ("#E65100" if ap>=60 else "#C62828")
            tcols[i].markdown(
                f"""<div style="background:#fff;border-left:4px solid {cl};
                    border-radius:8px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                  <div style="font-size:0.72rem;color:#777;font-weight:700;
                      text-transform:uppercase;">{row['Month']}</div>
                  <div style="font-size:1.3rem;font-weight:800;color:{cl};">
                    ₹{row.get('Monthly_Achievement_Cr',0):.2f} Cr</div>
                  <div style="font-size:0.72rem;color:#999;">
                    {ap:.1f}% of ₹{row.get('Monthly_Target_Cr',0):.2f} Cr target</div>
                  <div style="font-size:0.72rem;color:#555;margin-top:2px;">
                    Efficiency: {ef:.1f}%</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📈 Core Performance Trends")
        r1, r2 = st.columns(2)
        with r1:
            try: st.plotly_chart(portfolio_efficiency_trend(fport), use_container_width=True)
            except Exception as e: st.warning(f"{e}")
        with r2:
            try: st.plotly_chart(portfolio_target_vs_achievement(fport), use_container_width=True)
            except Exception as e: st.warning(f"{e}")

        st.markdown("---")
        st.markdown("### 🏗️ Project-level Trends")
        r3, r4 = st.columns(2)
        with r3:
            try: st.plotly_chart(project_achievement_trend(fmom), use_container_width=True)
            except Exception as e: st.warning(f"{e}")
        with r4:
            try: st.plotly_chart(outstanding_trend(fmom), use_container_width=True)
            except Exception as e: st.warning(f"{e}")

        st.markdown("---")
        st.markdown("### 💰 Collection & Spill Over (CRM Responsibility)")
        r5, r6 = st.columns(2)
        with r5:
            try: st.plotly_chart(monthly_collection_stacked(fmom), use_container_width=True)
            except Exception as e: st.warning(f"{e}")
        with r6:
            try: st.plotly_chart(spillover_trend(fmom), use_container_width=True)
            except Exception as e: st.warning(f"{e}")

        st.markdown("---")
        st.markdown("### 🛒 Sales Team — OCR & New Bookings")
        st.caption("OCR & New Booking collection are Sales team responsibility. CRM tracks & reports.")
        try: st.plotly_chart(sales_contribution_chart(fmom), use_container_width=True)
        except Exception as e: st.warning(f"{e}")

        st.markdown("---")
        st.markdown("### 🎯 Forecast Accuracy & Registration Trends")
        r7, r8 = st.columns(2)
        with r7:
            try: st.plotly_chart(forecast_accuracy_chart(fmom), use_container_width=True)
            except Exception as e: st.warning(f"{e}")
        with r8:
            try: st.plotly_chart(pending_reg_trend(fmom), use_container_width=True)
            except Exception as e: st.warning(f"{e}")

        st.markdown("---")
        st.markdown("### 🗓️ MoM Heatmap")
        hc1, hc2 = st.columns([1,2])
        with hc1:
            metric_opts = {
                "Achievement % vs Target":      "Achievement_Pct",
                "Collection Efficiency %":      "Collection_Efficiency_Pct",
                "Outstanding (₹ Cr)":           "Outstanding_Cr",
                "Monthly Collection (₹ Cr)":    "Monthly_Collection_Cr",
                "Spill Over Collection (₹ Cr)": "SpillOver_Achievement_Cr",
            }
            chosen = st.selectbox("Heatmap Metric", list(metric_opts.keys()))
        with hc2:
            try: st.plotly_chart(mom_heatmap(fmom, metric_opts[chosen]), use_container_width=True)
            except Exception as e: st.warning(f"{e}")

        with st.expander("📄 Full MoM Data Table"):
            keep = [c for c in ["Month","Project","RM","Monthly_Target_Cr",
                                 "Monthly_Achievement_Cr","Achievement_Pct","Forecast_Cr",
                                 "Collection_Efficiency_Pct","Outstanding_Cr",
                                 "SpillOver_Target_Cr","SpillOver_Achievement_Cr",
                                 "OCR_Target_Cr","OCR_Achievement_Cr",
                                 "Pending_Reg","Pending_Reg_GT45"] if c in fmom.columns]
            st.dataframe(fmom[keep], use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download MoM CSV",
            fmom.to_csv(index=False).encode("utf-8"), "crm_mom.csv", "text/csv")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI Q&A
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🤖 AI CRM Assistant — Ask Gemini")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#E3F2FD,#EDE7F6);
                border-left:4px solid #1A3C6E;padding:14px 18px;
                border-radius:8px;margin-bottom:16px;font-size:0.88rem;">
    <b>Ask anything about your CRM data:</b><br>
    • Which project has the highest outstanding?<br>
    • Compare Priyanka vs Pratap collection efficiency<br>
    • Is spill over reducing month on month?<br>
    • Which RM has the highest monthly target achievement?<br>
    • What is OCR achievement for RAGHAV Avenue?<br>
    • Which RM has most pending registrations over 45 days?
    </div>""", unsafe_allow_html=True)

    chips = [
        "Which project has highest outstanding?",
        "Compare RM-wise collection efficiency",
        "Is spill over reducing month on month?",
        "Which project missed target most months?",
        "What is OCR achievement by project?",
        "Pending registrations over 45 days by RM?",
    ]
    cc = st.columns(3)
    if "preset_q" not in st.session_state: st.session_state["preset_q"] = ""
    for i, chip in enumerate(chips):
        with cc[i%3]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                st.session_state["preset_q"] = chip; st.rerun()

    user_q = st.text_area("Your question:",
        value=st.session_state.get("preset_q",""),
        placeholder="e.g. Which RM has the lowest collection efficiency?",
        height=85, key="qa_area")

    if st.button("🔍  Get AI Answer", type="primary"):
        if not user_q.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analysing with Gemini…"):
                try:
                    ans = ask_gemini(user_q, fdf, category_df, fkpis,
                                     fmom if not fmom.empty else None)
                    st.markdown(
                        f"""<div style="background:#fff;border-left:4px solid #2E7D32;
                            padding:18px;border-radius:8px;margin-top:12px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.08);line-height:1.8;">
                        {ans.replace(chr(10),'<br>')}</div>""",
                        unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RM PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#E8EAF6,#EDE7F6);
                border-left:4px solid #6A1B9A;padding:12px 18px;
                border-radius:8px;margin-bottom:16px;font-size:0.85rem;">
    <b>RM assignments configured in <code>utils/rm_config.py</code></b> —
    edit that file to add new RMs or reassign projects.
    </div>""", unsafe_allow_html=True)

    rms = all_rms()

    # ── RM Performance Cards ─────────────────────────────────────────────────
    st.markdown("### 🏆 RM Performance Cards — Current Month")
    rm_cols = st.columns(len(rms))

    for col, rm in zip(rm_cols, rms):
        d = fdf[fdf["RM"] == rm]
        if d.empty:
            col.markdown(
                f"<div style='background:#f8f9fa;border-radius:8px;padding:16px;"
                f"text-align:center;color:#999;'><b>{rm}</b><br>No projects assigned</div>",
                unsafe_allow_html=True)
            continue

        demand  = d["Actual Demand Raised (Cr)"].sum()
        coll    = d["Collection Till Date (Cr)"].sum()
        out     = d["Outstanding (Cr)"].sum()
        monthly = d["Monthly Collection (Cr)"].sum()
        tgt     = d["Collection Target (Cr)"].sum()
        ach     = d["Collection Achievement (Cr)"].sum()
        fore    = d["CRM Forecast (Cr)"].sum()
        eff     = round(coll/demand*100, 1) if demand else 0
        tgt_ach_pct  = round(ach/tgt*100, 1) if tgt else 0
        fore_ach_pct = round(ach/fore*100, 1) if fore else 0
        pend    = int(d["Pending Registrations"].sum())
        p45     = int(d["Pending Reg > 45 Days"].sum())
        projs   = " · ".join(d["Project"].str.replace("RAGHAV ","",regex=False).tolist())
        color   = RM_COLORS.get(rm, "#1A3C6E")
        ec      = "#2E7D32" if eff>=90 else ("#E65100" if eff>=70 else "#C62828")
        tc      = "#2E7D32" if tgt_ach_pct>=90 else ("#E65100" if tgt_ach_pct>=60 else "#C62828")
        fc      = "#2E7D32" if fore_ach_pct>=90 else ("#E65100" if fore_ach_pct>=60 else "#C62828")

        col.markdown(f"""
<div style="background:linear-gradient(160deg,#fff 0%,#f8f9fa 100%);
     border-top:5px solid {color};border-radius:10px;padding:16px 14px;
     box-shadow:0 4px 16px rgba(0,0,0,0.10);margin-bottom:6px;">
  <div style="font-size:1rem;font-weight:700;color:{color};">{rm}</div>
  <div style="font-size:0.67rem;color:#999;margin-bottom:10px;">{projs}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:0.74rem;margin-bottom:8px;">
    <div style="background:#EEF2FF;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Demand</div>
      <b style="color:#1A3C6E;">₹{demand:.2f} Cr</b></div>
    <div style="background:#E8F5E9;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Collection</div>
      <b style="color:#2E7D32;">₹{coll:.2f} Cr</b></div>
    <div style="background:#FFEBEE;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Outstanding</div>
      <b style="color:#C62828;">₹{out:.2f} Cr</b></div>
    <div style="background:#FFF8E1;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Monthly Ach</div>
      <b style="color:#E65100;">₹{monthly:.2f} Cr</b></div>
    <div style="background:#F3E5F5;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Target</div>
      <b style="color:#6A1B9A;">₹{tgt:.2f} Cr</b></div>
    <div style="background:#E0F7FA;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Forecast</div>
      <b style="color:#00695C;">₹{fore:.2f} Cr</b></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:0.72rem;margin-bottom:8px;">
    <div style="background:#fff;border:1px solid #e0e0e0;border-radius:6px;padding:6px 8px;text-align:center;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Target Ach%</div>
      <b style="color:{tc};font-size:1rem;">{tgt_ach_pct:.1f}%</b></div>
    <div style="background:#fff;border:1px solid #e0e0e0;border-radius:6px;padding:6px 8px;text-align:center;">
      <div style="color:#777;font-size:0.58rem;font-weight:700;text-transform:uppercase;">Forecast Ach%</div>
      <b style="color:{fc};font-size:1rem;">{fore_ach_pct:.1f}%</b></div>
  </div>
  <div style="font-size:0.68rem;color:#888;">Coll. Efficiency: <b style="color:{ec}">{eff:.1f}%</b></div>
  <div style="background:#e0e0e0;border-radius:4px;height:5px;margin:3px 0 7px;">
    <div style="background:{ec};width:{min(eff,100):.0f}%;height:5px;border-radius:4px;"></div></div>
  <div style="font-size:0.68rem;color:#888;">
    Pending Reg: <b style="color:#E65100">{pend}</b>
    &nbsp;|&nbsp; >45d: <b style="color:#C62828">{p45}</b></div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RM Head-to-Head Comparison ──────────────────────────────────────────
    st.markdown("### 📊 RM Head-to-Head Comparison")

    rm_sum = fdf.groupby("RM").agg(
        Demand  =("Actual Demand Raised (Cr)","sum"),
        Coll    =("Collection Till Date (Cr)","sum"),
        Out     =("Outstanding (Cr)","sum"),
        Monthly =("Monthly Collection (Cr)","sum"),
        Target  =("Collection Target (Cr)","sum"),
        Ach     =("Collection Achievement (Cr)","sum"),
        Forecast=("CRM Forecast (Cr)","sum"),
        PendReg =("Pending Registrations","sum"),
        Pend45  =("Pending Reg > 45 Days","sum"),
    ).reset_index()
    rm_sum["Eff%"]     = (rm_sum["Coll"]/rm_sum["Demand"]*100).fillna(0).round(1)
    rm_sum["TgtAch%"]  = (rm_sum["Ach"]/rm_sum["Target"].replace(0,float("nan"))*100).fillna(0).round(1)
    rm_sum["ForeAch%"] = (rm_sum["Ach"]/rm_sum["Forecast"].replace(0,float("nan"))*100).fillna(0).round(1)

    rc1, rc2 = st.columns(2)
    with rc1:
        fig = go.Figure()
        fig.add_bar(name="Demand", x=rm_sum["RM"], y=rm_sum["Demand"],
            marker_color="#90CAF9",
            text=[f"₹{v:.2f}" for v in rm_sum["Demand"]], textposition="outside")
        fig.add_bar(name="Collection", x=rm_sum["RM"], y=rm_sum["Coll"],
            marker_color="#A5D6A7",
            text=[f"₹{v:.2f}" for v in rm_sum["Coll"]], textposition="outside")
        fig.add_bar(name="Outstanding", x=rm_sum["RM"], y=rm_sum["Out"],
            marker_color="#EF9A9A",
            text=[f"₹{v:.2f}" for v in rm_sum["Out"]], textposition="outside")
        fig.update_layout(barmode="group", template="plotly_white", height=420,
            title="<b>RM: Demand vs Collection vs Outstanding</b> (₹ Cr)",
            legend=dict(orientation="h",yanchor="top",y=-0.18,xanchor="center",x=0.5),
            margin=dict(t=60,b=100))
        st.plotly_chart(fig, use_container_width=True)

    with rc2:
        fig2 = go.Figure()
        fig2.add_bar(name="Monthly Target", x=rm_sum["RM"], y=rm_sum["Target"],
            marker_color="#CFD8DC",
            text=[f"₹{v:.2f}" for v in rm_sum["Target"]], textposition="outside")
        fig2.add_bar(name="Forecast", x=rm_sum["RM"], y=rm_sum["Forecast"],
            marker_color="#C9A84C",
            text=[f"₹{v:.2f}" for v in rm_sum["Forecast"]], textposition="outside")
        fig2.add_bar(name="Achievement", x=rm_sum["RM"], y=rm_sum["Ach"],
            marker_color=[("#2E7D32" if v>=90 else ("#E65100" if v>=60 else "#C62828"))
                          for v in rm_sum["TgtAch%"]],
            text=[f"₹{v:.2f} ({p:.0f}%)" for v,p in zip(rm_sum["Ach"],rm_sum["TgtAch%"])],
            textposition="outside")
        fig2.update_layout(barmode="group", template="plotly_white", height=420,
            title="<b>RM: Monthly Target → Forecast → Achievement</b> (₹ Cr)",
            legend=dict(orientation="h",yanchor="top",y=-0.18,xanchor="center",x=0.5),
            margin=dict(t=60,b=100))
        st.plotly_chart(fig2, use_container_width=True)

    rc3, rc4 = st.columns(2)
    with rc3:
        tc_list = ["#2E7D32" if v>=90 else ("#E65100" if v>=60 else "#C62828") for v in rm_sum["TgtAch%"]]
        fig3 = go.Figure()
        fig3.add_bar(name="Target Ach%", x=rm_sum["RM"], y=rm_sum["TgtAch%"],
            marker_color=tc_list,
            text=[f"{v:.1f}%" for v in rm_sum["TgtAch%"]], textposition="outside")
        fig3.add_bar(name="Forecast Ach%", x=rm_sum["RM"], y=rm_sum["ForeAch%"],
            marker_color="#7986CB",
            text=[f"{v:.1f}%" for v in rm_sum["ForeAch%"]], textposition="outside")
        fig3.add_hline(y=100, line_dash="dash", line_color="#2E7D32",
            annotation_text="100% target")
        fig3.update_layout(barmode="group", template="plotly_white", height=420,
            title="<b>RM Target Achievement% vs Forecast Achievement%</b>",
            yaxis=dict(ticksuffix="%"),
            legend=dict(orientation="h",yanchor="top",y=-0.18,xanchor="center",x=0.5),
            margin=dict(t=60,b=100))
        st.plotly_chart(fig3, use_container_width=True)

    with rc4:
        fig4 = go.Figure()
        fig4.add_bar(name="Total Pending", x=rm_sum["RM"], y=rm_sum["PendReg"],
            marker_color="#FFB74D",
            text=rm_sum["PendReg"].astype(int), textposition="outside")
        fig4.add_bar(name="Critical >45 Days", x=rm_sum["RM"], y=rm_sum["Pend45"],
            marker_color="#C62828",
            text=rm_sum["Pend45"].astype(int), textposition="outside")
        fig4.update_layout(barmode="overlay", template="plotly_white", height=420,
            title="<b>RM Pending Registration Aging</b>",
            yaxis_title="Count",
            legend=dict(orientation="h",yanchor="top",y=-0.18,xanchor="center",x=0.5),
            margin=dict(t=60,b=100))
        st.plotly_chart(fig4, use_container_width=True)

    # ── MoM RM Target / Forecast / Achievement bar chart ────────────────────
    if not fmom.empty and "RM" in fmom.columns:
        st.markdown("---")
        st.markdown("### 📈 RM — Month-on-Month: Target vs Forecast vs Achievement")

        MN2 = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
               "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        def _sk(m):
            p=m.split(); return int(p[1])*100+MN2.get(p[0],0) if len(p)==2 else 0
        months_s = sorted(fmom["Month"].unique().tolist(), key=_sk)

        rm_mom = fmom.groupby(["Month","RM"]).agg(
            Monthly_Target_Cr       =("Monthly_Target_Cr","sum"),
            Forecast_Cr             =("Forecast_Cr","sum"),
            Monthly_Achievement_Cr  =("Monthly_Achievement_Cr","sum"),
            Collection_Efficiency_Pct=("Collection_Efficiency_Pct","mean"),
            Outstanding_Cr          =("Outstanding_Cr","sum"),
        ).reset_index()

        # One chart per RM (grouped bars per month: Target / Forecast / Achievement)
        rm_chart_cols = st.columns(2)
        for idx, rm in enumerate(rms):
            rm_data = rm_mom[rm_mom["RM"]==rm].set_index("Month").reindex(months_s).reset_index()
            if rm_data["Monthly_Achievement_Cr"].dropna().empty:
                continue
            color = RM_COLORS.get(rm, "#1A3C6E")
            fig_rm = go.Figure()
            fig_rm.add_bar(name="Target", x=rm_data["Month"],
                y=rm_data["Monthly_Target_Cr"],
                marker_color="#B0BEC5",
                text=[f"₹{v:.2f}" if pd.notna(v) else "" for v in rm_data["Monthly_Target_Cr"]],
                textposition="outside")
            fig_rm.add_bar(name="Forecast", x=rm_data["Month"],
                y=rm_data["Forecast_Cr"],
                marker_color="#C9A84C",
                text=[f"₹{v:.2f}" if pd.notna(v) else "" for v in rm_data["Forecast_Cr"]],
                textposition="outside")
            fig_rm.add_bar(name="Achievement", x=rm_data["Month"],
                y=rm_data["Monthly_Achievement_Cr"],
                marker_color=color,
                text=[f"₹{v:.2f}" if pd.notna(v) else "" for v in rm_data["Monthly_Achievement_Cr"]],
                textposition="outside")
            fig_rm.update_layout(
                barmode="group", template="plotly_white", height=380,
                title=f"<b>{rm}</b> — Monthly Target vs Forecast vs Achievement (₹ Cr)",
                xaxis=dict(categoryorder="array", categoryarray=months_s),
                yaxis_title="₹ Cr",
                legend=dict(orientation="h",yanchor="top",y=-0.22,xanchor="center",x=0.5),
                margin=dict(t=60,b=110))
            with rm_chart_cols[idx % 2]:
                st.plotly_chart(fig_rm, use_container_width=True)

    # ── Project Detail Table ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Project Detail by RM")
    td = fdf[["RM","Project","Actual Demand Raised (Cr)","Collection Till Date (Cr)",
               "Outstanding (Cr)","Collection Target (Cr)","CRM Forecast (Cr)",
               "Collection Achievement (Cr)","Pending Registrations","Pending Reg > 45 Days"]].copy()
    td["Eff %"]     = (td["Collection Till Date (Cr)"]/td["Actual Demand Raised (Cr)"]*100).fillna(0).round(1)
    td["Tgt Ach %"] = (td["Collection Achievement (Cr)"]/td["Collection Target (Cr)"].replace(0,float("nan"))*100).fillna(0).round(1)
    td["Fct Ach %"] = (td["Collection Achievement (Cr)"]/td["CRM Forecast (Cr)"].replace(0,float("nan"))*100).fillna(0).round(1)
    td["Pending Registrations"] = td["Pending Registrations"].astype(int)
    td["Pending Reg > 45 Days"] = td["Pending Reg > 45 Days"].astype(int)
    td = td[["RM","Project","Actual Demand Raised (Cr)","Collection Till Date (Cr)",
             "Outstanding (Cr)","Eff %","Collection Target (Cr)","CRM Forecast (Cr)",
             "Collection Achievement (Cr)","Tgt Ach %","Fct Ach %",
             "Pending Registrations","Pending Reg > 45 Days"]]
    td.columns = ["RM","Project","Demand (Cr)","Collection (Cr)","Outstanding (Cr)",
                  "Eff %","Target (Cr)","Forecast (Cr)","Achievement (Cr)",
                  "Tgt Ach%","Fct Ach%","Pending Reg","Pending >45d"]
    st.dataframe(td.sort_values("RM").style.format({
        "Demand (Cr)":      "₹ {:.2f} Cr",
        "Collection (Cr)":  "₹ {:.2f} Cr",
        "Outstanding (Cr)": "₹ {:.2f} Cr",
        "Target (Cr)":      "₹ {:.2f} Cr",
        "Forecast (Cr)":    "₹ {:.2f} Cr",
        "Achievement (Cr)": "₹ {:.2f} Cr",
        "Eff %":            "{:.1f}%",
        "Tgt Ach%":         "{:.1f}%",
        "Fct Ach%":         "{:.1f}%",
    }), use_container_width=True, hide_index=True)

    st.download_button("⬇️ Download RM Report CSV",
        td.to_csv(index=False).encode("utf-8"), "rm_report.csv", "text/csv")

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:0.75rem;padding:6px 0 12px;'>"
    "RAGHAV Group CRM MIS v4.0 &nbsp;|&nbsp; Streamlit + Gemini AI &nbsp;|&nbsp; Mumbai Real Estate"
    "</div>", unsafe_allow_html=True)
