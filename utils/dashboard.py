"""
utils/dashboard.py — Chart and KPI rendering for current-month tab.
Chart order fixed: Outstanding(start) → Target → Forecast → Achievement
All charts use plotly_white, legends below chart to avoid overlap.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.crm_metrics import demand_vs_collection, monthly_target_vs_achievement, top_defaulters, collection_efficiency
from utils.helpers import format_cr, pct_bar

BLUE  = "#1A3C6E"; GOLD  = "#C9A84C"; GREEN = "#2E7D32"
RED   = "#C62828"; AMBER = "#E65100"; TEAL  = "#00695C"; PURPLE= "#6A1B9A"
PC    = [BLUE, GOLD, GREEN, RED, AMBER, TEAL, PURPLE]
TPL   = "plotly_white"

def _legend_bottom():
    return dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5, font=dict(size=10))

def _layout(**kw):
    base = dict(template=TPL, height=420,
                margin=dict(t=60,b=100),
                legend=_legend_bottom())
    base.update(kw)
    return base

# ── KPI tiles ─────────────────────────────────────────────────────────────────
def create_kpi_section(kpis, project_df):
    total_demand      = kpis.get("total_demand",0)
    total_collection  = kpis.get("total_collection",0)
    total_outstanding = kpis.get("total_outstanding",0)
    eff               = collection_efficiency(total_collection, total_demand)
    monthly_coll      = kpis.get("monthly_coll",0)
    daily_coll        = kpis.get("daily_coll",0)
    live_bkgs         = int(kpis.get("total_live_bkgs",0))
    pend_reg          = int(kpis.get("pending_reg",0))
    pend_reg_45       = int(kpis.get("pending_reg_45",0))
    crm_tgt           = kpis.get("crm_monthly_tgt",0)
    crm_ach           = kpis.get("crm_monthly_ach",0)
    spillover         = kpis.get("spillover_total",0)

    st.markdown(
        f"<div style='font-size:0.82rem;color:#555;font-weight:500;padding:4px 0 6px;'>"
        f"📅 Report: <b>{kpis.get('report_date','—')}</b> &nbsp;|&nbsp; "
        f"Month: <b>{kpis.get('month_label','—')}</b></div>",
        unsafe_allow_html=True)

    r1 = st.columns(4)
    _tile(r1[0],"💰 Total Demand (Till Date)",    format_cr(total_demand),    "Cumulative demand raised",                BLUE)
    _tile(r1[1],"✅ Total Collection (Till Date)",  format_cr(total_collection),"Cumulative collection",                   GREEN)
    _tile(r1[2],"⚠️ Total Outstanding (Till Date)", format_cr(total_outstanding),"Amount still pending",                   RED)
    ec = GREEN if eff>=90 else (AMBER if eff>=70 else RED)
    _tile(r1[3],"📊 Collection Efficiency",        f"{eff:.1f}%",              "Collection ÷ Demand raised",             ec)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    r2 = st.columns(5)
    _tile(r2[0],"📅 Monthly CRM Target",    format_cr(crm_tgt),    "This month's CRM target",         BLUE)
    _tile(r2[1],"🏆 Monthly Achievement",   format_cr(crm_ach),    "Collected this month",             GREEN)
    _tile(r2[2],"🔄 Outstanding (Month Start)", format_cr(spillover),"Spill Over — opening balance",  AMBER)
    _tile(r2[3],"📋 Pending Registrations", str(pend_reg),         "Registrations awaited",           AMBER)
    _tile(r2[4],"🔴 Critical >45 Days",     str(pend_reg_45),      "Delayed > 45 days",               RED)

def _tile(col, label, value, subtitle="", color=BLUE):
    col.markdown(f"""
<div style="background:#fff;border-left:4px solid {color};border-radius:6px;
            padding:13px 15px;box-shadow:0 1px 4px rgba(0,0,0,0.07);margin-bottom:6px;">
  <div style="font-size:0.72rem;color:#777;font-weight:600;
              text-transform:uppercase;letter-spacing:0.4px;">{label}</div>
  <div style="font-size:1.45rem;font-weight:700;color:{color};margin:4px 0 2px;">{value}</div>
  <div style="font-size:0.70rem;color:#999;">{subtitle}</div>
</div>""", unsafe_allow_html=True)


# ── Project demand vs collection bar ──────────────────────────────────────────
def project_collection_chart(project_df):
    df = demand_vs_collection(project_df)
    fig = go.Figure()
    fig.add_bar(name="Demand Raised", x=df["Project"], y=df["Demand (Cr)"],
        marker_color=BLUE, text=df["Demand (Cr)"].apply(lambda v: f"₹{v:.1f}"), textposition="outside")
    fig.add_bar(name="Collection Till Date", x=df["Project"], y=df["Collection (Cr)"],
        marker_color=GREEN, text=df["Collection (Cr)"].apply(lambda v: f"₹{v:.1f}"), textposition="outside")
    fig.add_bar(name="Outstanding", x=df["Project"], y=df["Outstanding (Cr)"],
        marker_color=RED, text=df["Outstanding (Cr)"].apply(lambda v: f"₹{v:.1f}"), textposition="outside")
    fig.update_layout(**_layout(
        title="<b>Project-wise: Demand vs Collection vs Outstanding</b> (₹ Cr)",
        barmode="group", yaxis_title="₹ Cr"))
    return fig


# ── Monthly Target → Forecast → Achievement (CORRECT ORDER) ───────────────────
def monthly_target_chart(project_df):
    """
    Bar order: Outstanding at Month Start → Monthly Target → Forecast → Achievement
    This gives leadership the full picture: what was pending, what was targeted,
    what was forecast, and what was actually collected.
    """
    df = monthly_target_vs_achievement(project_df)

    fig = go.Figure()
    # 1. Outstanding at month start (Spill Over Target)
    if "SpillOver_Target_Cr" in project_df.columns:
        spill = project_df.set_index("Project")["SpillOver_Target_Cr"].reindex(df["Project"]).fillna(0).values
        fig.add_bar(name="Outstanding (Month Start)", x=df["Project"], y=spill,
            marker_color="#EF9A9A",
            text=[f"₹{v:.2f}" for v in spill], textposition="outside")
    # 2. Monthly Target
    fig.add_bar(name="Monthly Target", x=df["Project"], y=df["Target (Cr)"],
        marker_color=BLUE,
        text=df["Target (Cr)"].apply(lambda v: f"₹{v:.2f}"), textposition="outside")
    # 3. Forecast
    fig.add_bar(name="Forecast", x=df["Project"], y=df["Forecast (Cr)"],
        marker_color=GOLD,
        text=df["Forecast (Cr)"].apply(lambda v: f"₹{v:.2f}"), textposition="outside")
    # 4. Achievement
    fig.add_bar(name="Achievement", x=df["Project"], y=df["Achievement (Cr)"],
        marker_color=GREEN,
        text=df["Achievement (Cr)"].apply(lambda v: f"₹{v:.2f}"), textposition="outside")

    fig.update_layout(**_layout(
        title="<b>Outstanding (Start) → Target → Forecast → Achievement</b> (₹ Cr)",
        barmode="group", yaxis_title="₹ Cr"))
    return fig


# ── Collection efficiency horizontal bar ──────────────────────────────────────
def collection_efficiency_chart(project_df):
    df = demand_vs_collection(project_df).sort_values("Collection Eff %", ascending=True)
    colors = [GREEN if v>=90 else (AMBER if v>=70 else RED) for v in df["Collection Eff %"]]
    fig = go.Figure(go.Bar(
        x=df["Collection Eff %"], y=df["Project"], orientation="h",
        marker_color=colors,
        text=df["Collection Eff %"].apply(lambda v: f"{v:.1f}%"), textposition="outside"))
    fig.add_vline(x=90, line_dash="dash", line_color=GREEN,
        annotation_text="90% Target", annotation_position="top right")
    fig.update_layout(**{**_layout(), "title":"<b>Collection Efficiency % by Project</b>",
        "xaxis":dict(range=[0,115], ticksuffix="%"),
        "margin":dict(t=60,b=40,l=130), "height":380, "showlegend":False})
    return fig


# ── Outstanding donut ─────────────────────────────────────────────────────────
def overdue_chart(project_df):
    df = project_df[project_df["Outstanding (Cr)"]>0].copy()
    if df.empty: df = project_df.copy()
    fig = px.pie(df, names="Project", values="Outstanding (Cr)",
        title="<b>Outstanding Distribution by Project</b> (₹ Cr)",
        color_discrete_sequence=PC, hole=0.42)
    fig.update_traces(textposition="inside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>₹%{value:.2f} Cr<br>%{percent}")
    fig.update_layout(template=TPL, height=400,
        margin=dict(t=60,b=20), showlegend=False)
    return fig


# ── Pending registration bar ──────────────────────────────────────────────────
def pending_registration_chart(project_df):
    df = project_df.copy()
    fig = go.Figure()
    fig.add_bar(name="Total Pending", x=df["Project"], y=df["Pending Registrations"],
        marker_color=AMBER, text=df["Pending Registrations"].astype(int), textposition="outside")
    fig.add_bar(name="Critical >45 Days", x=df["Project"], y=df["Pending Reg > 45 Days"],
        marker_color=RED, text=df["Pending Reg > 45 Days"].astype(int), textposition="outside")
    fig.update_layout(**_layout(
        title="<b>Pending Registration Aging by Project</b>",
        barmode="overlay", yaxis_title="Count"))
    return fig


# ── Demand vs Collection line (project trend) ─────────────────────────────────
def demand_collection_trend(project_df):
    df = demand_vs_collection(project_df)
    melted = df.melt(id_vars=["Project"],
        value_vars=["Demand (Cr)","Collection (Cr)","Outstanding (Cr)"],
        var_name="Metric", value_name="₹ Cr")
    fig = px.line(melted, x="Project", y="₹ Cr", color="Metric", markers=True,
        title="<b>Demand vs Collection vs Outstanding — Project Snapshot</b>",
        color_discrete_map={"Demand (Cr)":BLUE,"Collection (Cr)":GREEN,"Outstanding (Cr)":RED})
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_layout(**{**_layout(), "yaxis_title":"₹ Cr","xaxis_title":""})
    return fig


# ── Category breakdown ────────────────────────────────────────────────────────
def category_breakdown_chart(category_df):
    if category_df.empty: return go.Figure()
    fig = go.Figure()
    fig.add_bar(name="Target", x=category_df["Category"], y=category_df["Target (Cr)"],
        marker_color=BLUE,
        text=category_df["Target (Cr)"].apply(lambda v: f"₹{v:.2f}"), textposition="outside")
    fig.add_bar(name="Forecast", x=category_df["Category"], y=category_df["Forecast (Cr)"],
        marker_color=GOLD,
        text=category_df["Forecast (Cr)"].apply(lambda v: f"₹{v:.2f}"), textposition="outside")
    fig.add_bar(name="Achievement", x=category_df["Category"], y=category_df["Achievement (Cr)"],
        marker_color=GREEN,
        text=category_df["Achievement (Cr)"].apply(lambda v: f"₹{v:.2f}"), textposition="outside")
    fig.update_layout(**_layout(
        title="<b>Category-wise: Target → Forecast → Achievement</b> (₹ Cr)",
        barmode="group", yaxis_title="₹ Cr",
        xaxis=dict(tickangle=-25),
        margin=dict(t=60,b=110)))
    return fig


# ── Top defaulters table ──────────────────────────────────────────────────────
def top_defaulters_table(project_df):
    return top_defaulters(project_df)
