"""
utils/mom_charts.py
Month-on-month trend charts using the multi-month loader data.
All functions accept the combined DataFrame from load_all_months().
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

BLUE   = "#1A3C6E"
GREEN  = "#2E7D32"
RED    = "#C62828"
AMBER  = "#E65100"
GOLD   = "#C9A84C"
TEAL   = "#00695C"
PURPLE = "#6A1B9A"

PROJECT_COLORS = [BLUE, GREEN, RED, AMBER, GOLD, TEAL, PURPLE]

LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    template="plotly_white",
    font=dict(family="Inter,sans-serif", size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=50, b=40),
    height=400,
)


# ── 1. Portfolio collection efficiency trend ───────────────────────────────────
def portfolio_efficiency_trend(portfolio_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(
        x=portfolio_df["Month"],
        y=portfolio_df["Collection_Efficiency_Pct"],
        mode="lines+markers+text",
        name="Efficiency %",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=8),
        text=[f"{v:.1f}%" for v in portfolio_df["Collection_Efficiency_Pct"]],
        textposition="top center",
    )
    fig.add_hline(y=90, line_dash="dash", line_color=GREEN,
                  annotation_text="90% target", annotation_position="right")
    fig.update_layout(**LAYOUT, title="Portfolio Collection Efficiency % — Month on Month",
                      yaxis=dict(ticksuffix="%", range=[0, 110]))
    return fig


# ── 2. Target vs Achievement vs Forecast (portfolio) ──────────────────────────
def portfolio_target_vs_achievement(portfolio_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(name="Target (Cr)",      x=portfolio_df["Month"],
                y=portfolio_df["Monthly_Target_Cr"],      marker_color="#B0BEC5")
    fig.add_bar(name="Forecast (Cr)",    x=portfolio_df["Month"],
                y=portfolio_df["Forecast_Cr"],    marker_color=GOLD)
    fig.add_bar(name="Achievement (Cr)", x=portfolio_df["Month"],
                y=portfolio_df["Monthly_Achievement_Cr"], marker_color=GREEN)
    fig.update_layout(**LAYOUT, title="Portfolio: Target vs Forecast vs Achievement (₹ Cr)",
                      barmode="group", yaxis_title="₹ Cr")
    return fig


# ── 3. Achievement % vs target — all projects all months ──────────────────────
def project_achievement_trend(mom_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    projects = sorted(mom_df["Project"].unique())
    for i, proj in enumerate(projects):
        pdata = mom_df[mom_df["Project"] == proj].copy()
        fig.add_scatter(
            x=pdata["Month"],
            y=pdata["Achievement_Pct"],
            mode="lines+markers",
            name=proj,
            line=dict(color=PROJECT_COLORS[i % len(PROJECT_COLORS)], width=2),
            marker=dict(size=7),
        )
    fig.add_hline(y=100, line_dash="dash", line_color=GREEN,
                  annotation_text="100% target")
    fig.update_layout(**LAYOUT, title="Project Achievement % vs Target — MoM",
                      yaxis=dict(ticksuffix="%"))
    return fig


# ── 4. Outstanding trend (₹ Cr) ───────────────────────────────────────────────
def outstanding_trend(mom_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    projects = sorted(mom_df["Project"].unique())
    for i, proj in enumerate(projects):
        pdata = mom_df[mom_df["Project"] == proj].copy()
        fig.add_scatter(
            x=pdata["Month"],
            y=pdata["Outstanding_Cr"],
            mode="lines+markers",
            name=proj,
            line=dict(color=PROJECT_COLORS[i % len(PROJECT_COLORS)], width=2),
            marker=dict(size=7),
        )
    fig.update_layout(**LAYOUT, title="Outstanding (₹ Cr) — Month on Month by Project",
                      yaxis_title="₹ Cr")
    return fig


# ── 5. Monthly collection by project (stacked bar) ────────────────────────────
def monthly_collection_stacked(mom_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    projects = sorted(mom_df["Project"].unique())
    months   = mom_df["Month"].unique().tolist()
    for i, proj in enumerate(projects):
        pdata = mom_df[mom_df["Project"] == proj].set_index("Month")
        vals = [pdata.loc[m, "Monthly_Collection_Cr"] if m in pdata.index else 0
                for m in months]
        fig.add_bar(name=proj, x=months, y=vals,
                    marker_color=PROJECT_COLORS[i % len(PROJECT_COLORS)])
    fig.update_layout(**LAYOUT, title="Monthly Collection by Project (₹ Cr) — Stacked",
                      barmode="stack", yaxis_title="₹ Cr")
    return fig


# ── 6. Forecast accuracy (Forecast vs Achievement scatter) ────────────────────
def forecast_accuracy_chart(mom_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    projects = sorted(mom_df["Project"].unique())
    for i, proj in enumerate(projects):
        pdata = mom_df[mom_df["Project"] == proj]
        fig.add_scatter(
            x=pdata["Forecast_Cr"],
            y=pdata["Monthly_Achievement_Cr"],
            mode="markers+text",
            name=proj,
            marker=dict(size=10, color=PROJECT_COLORS[i % len(PROJECT_COLORS)]),
            text=pdata["Month"],
            textposition="top center",
        )
    # Perfect forecast line
    max_val = max(mom_df["Forecast_Cr"].max(), mom_df["Monthly_Achievement_Cr"].max()) * 1.1
    fig.add_scatter(x=[0, max_val], y=[0, max_val], mode="lines",
                    line=dict(dash="dash", color="gray", width=1),
                    name="Perfect forecast", showlegend=True)
    fig.update_layout(**LAYOUT, title="Forecast vs Actual Achievement (₹ Cr) — Accuracy",
                      xaxis_title="Forecast (Cr)", yaxis_title="Achievement (Cr)")
    return fig


# ── 7. Pending registration trend ─────────────────────────────────────────────
def pending_reg_trend(mom_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    projects = sorted(mom_df["Project"].unique())
    for i, proj in enumerate(projects):
        pdata = mom_df[mom_df["Project"] == proj]
        if pdata["Pending_Reg"].sum() == 0:
            continue
        fig.add_scatter(
            x=pdata["Month"],
            y=pdata["Pending_Reg"],
            mode="lines+markers",
            name=proj,
            line=dict(color=PROJECT_COLORS[i % len(PROJECT_COLORS)], width=2),
            marker=dict(size=7),
        )
    fig.update_layout(**LAYOUT, title="Pending Registrations — Month on Month",
                      yaxis_title="Count")
    return fig


# ── 8. MoM summary heatmap table ──────────────────────────────────────────────
def mom_heatmap(mom_df: pd.DataFrame, metric: str = "Achievement_Pct") -> go.Figure:
    pivot = mom_df.pivot_table(index="Project", columns="Month",
                               values=metric, aggfunc="mean")
    # Sort columns chronologically (already sorted in df)
    month_order = mom_df["Month"].unique().tolist()
    pivot = pivot[[m for m in month_order if m in pivot.columns]]

    title_map = {
        "Achievement_Pct":        "Achievement % vs Target",
        "Collection_Efficiency_Pct": "Collection Efficiency %",
        "Outstanding_Cr":         "Outstanding (₹ Cr)",
        "Monthly_Collection_Cr":  "Monthly Collection (₹ Cr)",
    }

    suffix = "%" if "Pct" in metric else " Cr"
    text_fmt = [[f"{v:.1f}{suffix}" if pd.notna(v) else "—"
                 for v in row] for row in pivot.values]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        text=text_fmt,
        texttemplate="%{text}",
        colorscale="RdYlGn" if "Pct" in metric else "Blues",
        showscale=True,
        hovertemplate="Project: %{y}<br>Month: %{x}<br>Value: %{text}<extra></extra>",
    ))
    fig.update_layout(
        **{**LAYOUT, "height": 320, "margin": dict(l=130, r=20, t=50, b=60)},
        title=f"MoM Heatmap — {title_map.get(metric, metric)}",
    )
    return fig
