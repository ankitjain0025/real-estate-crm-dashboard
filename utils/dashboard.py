"""
Dashboard chart and KPI rendering functions.
All monetary values in Crores (Cr).
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.crm_metrics import (
    demand_vs_collection,
    monthly_target_vs_achievement,
    top_defaulters,
    collection_efficiency,
)
from utils.helpers import format_cr, pct_bar

# ── Colour palette ──────────────────────────────────────
RAGHAV_BLUE   = "#1A3C6E"
RAGHAV_GOLD   = "#C9A84C"
RAGHAV_GREEN  = "#2E7D32"
RAGHAV_RED    = "#C62828"
RAGHAV_ORANGE = "#E65100"
RAGHAV_TEAL   = "#00695C"
RAGHAV_PURPLE = "#6A1B9A"
PROJECT_COLORS = [
    RAGHAV_BLUE, RAGHAV_GOLD, RAGHAV_GREEN,
    RAGHAV_RED, RAGHAV_ORANGE, RAGHAV_TEAL, RAGHAV_PURPLE,
]

CHART_TEMPLATE = "plotly_white"


# ─────────────────────────────────────────────────────────
# KPI SECTION
# ─────────────────────────────────────────────────────────

def create_kpi_section(kpis: dict, project_df: pd.DataFrame):
    """Render the top KPI tiles."""
    total_demand      = kpis.get("total_demand", 0)
    total_collection  = kpis.get("total_collection", 0)
    total_outstanding = kpis.get("total_outstanding", 0)
    eff               = collection_efficiency(total_collection, total_demand)
    monthly_coll      = kpis.get("monthly_coll", 0)
    daily_coll        = kpis.get("daily_coll", 0)
    live_bkgs         = int(kpis.get("total_live_bkgs", 0))
    pend_reg          = int(kpis.get("pending_reg", 0))
    pend_reg_45       = int(kpis.get("pending_reg_45", 0))
    crm_tgt           = kpis.get("crm_monthly_tgt", 0)
    crm_ach           = kpis.get("crm_monthly_ach", 0)

    st.markdown(
        f"""
        <div style='padding:6px 0 2px 0;
                    font-size:0.82rem;color:#555;font-weight:500;'>
            📅 Report Date: <strong>{kpis.get("report_date","—")}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    row1 = st.columns(4)
    _kpi_tile(row1[0], "💰 Total Demand (Till Date)",
              format_cr(total_demand), "Actual demand raised across all projects")
    _kpi_tile(row1[1], "✅ Total Collection (Till Date)",
              format_cr(total_collection), "Cumulative collection from all projects",
              color=RAGHAV_GREEN)
    _kpi_tile(row1[2], "⚠️ Outstanding (Till Date)",
              format_cr(total_outstanding), "Total amount still pending",
              color=RAGHAV_RED)
    eff_color = RAGHAV_GREEN if eff >= 90 else (RAGHAV_ORANGE if eff >= 70 else RAGHAV_RED)
    _kpi_tile(row1[3], "📊 Collection Efficiency",
              f"{eff:.1f}%", "Collection / Demand raised",
              color=eff_color)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    row2 = st.columns(5)
    _kpi_tile(row2[0], "📅 Monthly Collection",
              format_cr(monthly_coll), "This month's collection")
    _kpi_tile(row2[1], "📆 Daily Collection",
              format_cr(daily_coll), "Today's collection")
    _kpi_tile(row2[2], "🏠 Live Bookings",
              f"{live_bkgs:,}", "Total active bookings")
    _kpi_tile(row2[3], "📋 Pending Registrations",
              f"{pend_reg}", "Registrations awaited",
              color=RAGHAV_ORANGE)
    _kpi_tile(row2[4], "🔴 Pending Reg > 45 Days",
              f"{pend_reg_45}", "Critical delayed registrations",
              color=RAGHAV_RED)


def _kpi_tile(col, label: str, value: str, subtitle: str = "", color: str = RAGHAV_BLUE):
    col.markdown(
        f"""
        <div style="
            background:#fff;
            border-left:4px solid {color};
            border-radius:6px;
            padding:14px 16px;
            box-shadow:0 1px 4px rgba(0,0,0,0.08);
            margin-bottom:6px;
        ">
            <div style="font-size:0.75rem;color:#777;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.5px;">
                {label}
            </div>
            <div style="font-size:1.55rem;font-weight:700;color:{color};
                        margin:4px 0 2px 0;">
                {value}
            </div>
            <div style="font-size:0.72rem;color:#999;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────
# PROJECT COLLECTION CHART
# ─────────────────────────────────────────────────────────

def project_collection_chart(project_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: Demand vs Collection by project."""
    df = demand_vs_collection(project_df)
    fig = go.Figure()
    fig.add_bar(
        name="Demand Raised (Cr)",
        x=df["Project"],
        y=df["Demand (Cr)"],
        marker_color=RAGHAV_BLUE,
        text=df["Demand (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.add_bar(
        name="Collection Till Date (Cr)",
        x=df["Project"],
        y=df["Collection (Cr)"],
        marker_color=RAGHAV_GREEN,
        text=df["Collection (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.add_bar(
        name="Outstanding (Cr)",
        x=df["Project"],
        y=df["Outstanding (Cr)"],
        marker_color=RAGHAV_RED,
        text=df["Outstanding (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.update_layout(
        barmode="group",
        title="Project-wise: Demand vs Collection vs Outstanding (₹ Cr)",
        template=CHART_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="₹ Crores",
        xaxis_title="",
        height=420,
        margin=dict(t=60, b=40),
    )
    return fig


# ─────────────────────────────────────────────────────────
# MONTHLY TARGET vs ACHIEVEMENT
# ─────────────────────────────────────────────────────────

def monthly_target_chart(project_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: Monthly Target vs Achievement."""
    df = monthly_target_vs_achievement(project_df)
    fig = go.Figure()
    fig.add_bar(
        name="Target (Cr)",
        x=df["Project"],
        y=df["Target (Cr)"],
        marker_color=RAGHAV_BLUE,
        text=df["Target (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.add_bar(
        name="Achievement (Cr)",
        x=df["Project"],
        y=df["Achievement (Cr)"],
        marker_color=RAGHAV_GOLD,
        text=df["Achievement (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.add_bar(
        name="Forecast (Cr)",
        x=df["Project"],
        y=df["Forecast (Cr)"],
        marker_color=RAGHAV_TEAL,
        text=df["Forecast (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.update_layout(
        barmode="group",
        title="Monthly CRM Target vs Achievement vs Forecast (₹ Cr)",
        template=CHART_TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="₹ Crores",
        height=420,
        margin=dict(t=60, b=40),
    )
    return fig


# ─────────────────────────────────────────────────────────
# COLLECTION EFFICIENCY CHART
# ─────────────────────────────────────────────────────────

def collection_efficiency_chart(project_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: collection efficiency % by project."""
    df = demand_vs_collection(project_df)
    df = df.sort_values("Collection Eff %", ascending=True)
    colors = [
        RAGHAV_GREEN if v >= 90 else (RAGHAV_ORANGE if v >= 70 else RAGHAV_RED)
        for v in df["Collection Eff %"]
    ]
    fig = go.Figure(go.Bar(
        x=df["Collection Eff %"],
        y=df["Project"],
        orientation="h",
        marker_color=colors,
        text=df["Collection Eff %"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig.add_vline(x=90, line_dash="dash", line_color=RAGHAV_GREEN,
                  annotation_text="90% Target", annotation_position="top right")
    fig.update_layout(
        title="Collection Efficiency % by Project",
        template=CHART_TEMPLATE,
        xaxis_title="Efficiency %",
        xaxis_range=[0, 110],
        height=360,
        margin=dict(t=60, b=40, l=120),
    )
    return fig


# ─────────────────────────────────────────────────────────
# OUTSTANDING CHART (OVERDUE PROXY)
# ─────────────────────────────────────────────────────────

def overdue_chart(project_df: pd.DataFrame) -> go.Figure:
    """Pie chart of outstanding by project."""
    df = project_df[project_df["Outstanding (Cr)"] > 0].copy()
    if df.empty:
        df = project_df.copy()
    fig = px.pie(
        df,
        names="Project",
        values="Outstanding (Cr)",
        title="Outstanding Distribution by Project (₹ Cr)",
        color_discrete_sequence=PROJECT_COLORS,
        hole=0.4,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Outstanding: ₹%{value:.2f} Cr<br>Share: %{percent}",
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=400,
        margin=dict(t=60, b=20),
    )
    return fig


# ─────────────────────────────────────────────────────────
# PENDING REGISTRATIONS CHART
# ─────────────────────────────────────────────────────────

def pending_registration_chart(project_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: pending registrations — total vs > 45 days."""
    df = project_df.copy()
    fig = go.Figure()
    fig.add_bar(
        name="Pending Reg (Total)",
        x=df["Project"],
        y=df["Pending Registrations"],
        marker_color=RAGHAV_ORANGE,
        text=df["Pending Registrations"],
        textposition="outside",
    )
    fig.add_bar(
        name="Pending Reg > 45 Days",
        x=df["Project"],
        y=df["Pending Reg > 45 Days"],
        marker_color=RAGHAV_RED,
        text=df["Pending Reg > 45 Days"],
        textposition="outside",
    )
    fig.update_layout(
        barmode="overlay",
        title="Pending Registrations by Project",
        template=CHART_TEMPLATE,
        yaxis_title="Count",
        height=380,
        margin=dict(t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ─────────────────────────────────────────────────────────
# DEMAND vs COLLECTION TREND (project line chart)
# ─────────────────────────────────────────────────────────

def demand_collection_trend(project_df: pd.DataFrame) -> go.Figure:
    """Line chart comparing demand, collection & outstanding per project."""
    df = demand_vs_collection(project_df)
    melted = df.melt(
        id_vars=["Project"],
        value_vars=["Demand (Cr)", "Collection (Cr)", "Outstanding (Cr)"],
        var_name="Metric",
        value_name="₹ Crores",
    )
    color_map = {
        "Demand (Cr)":      RAGHAV_BLUE,
        "Collection (Cr)":  RAGHAV_GREEN,
        "Outstanding (Cr)": RAGHAV_RED,
    }
    fig = px.line(
        melted,
        x="Project",
        y="₹ Crores",
        color="Metric",
        markers=True,
        title="Demand vs Collection vs Outstanding — Project Trend",
        color_discrete_map=color_map,
    )
    fig.update_traces(line_width=2.5, marker_size=8)
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=400,
        yaxis_title="₹ Crores",
        xaxis_title="",
        margin=dict(t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ─────────────────────────────────────────────────────────
# CATEGORY BREAKDOWN CHART
# ─────────────────────────────────────────────────────────

def category_breakdown_chart(category_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: category-wise target vs achievement."""
    if category_df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_bar(
        name="Target (Cr)",
        x=category_df["Category"],
        y=category_df["Target (Cr)"],
        marker_color=RAGHAV_BLUE,
        text=category_df["Target (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.add_bar(
        name="Achievement (Cr)",
        x=category_df["Category"],
        y=category_df["Achievement (Cr)"],
        marker_color=RAGHAV_GOLD,
        text=category_df["Achievement (Cr)"].apply(lambda v: f"₹{v:.2f}"),
        textposition="outside",
    )
    fig.update_layout(
        barmode="group",
        title="Category-wise Collection: Target vs Achievement (₹ Cr)",
        template=CHART_TEMPLATE,
        xaxis_title="",
        yaxis_title="₹ Crores",
        height=420,
        margin=dict(t=60, b=80),
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ─────────────────────────────────────────────────────────
# TOP DEFAULTERS TABLE
# ─────────────────────────────────────────────────────────

def top_defaulters_table(project_df: pd.DataFrame) -> pd.DataFrame:
    """Return top projects by outstanding (highest first)."""
    return top_defaulters(project_df)
