"""
utils/mom_charts.py — MoM charts
Fixes: legend overlap (moved inside chart area), month ordering,
       SpillOver as "Outstanding at Month Start", correct bar order.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

BLUE="#1A3C6E"; GREEN="#2E7D32"; RED="#C62828"; AMBER="#E65100"
GOLD="#C9A84C"; TEAL="#00695C"; PURPLE="#6A1B9A"; PINK="#AD1457"
PC=[BLUE,GREEN,RED,AMBER,GOLD,TEAL,PURPLE,PINK]
MN={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
    "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def _base():
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                template="plotly_white", font=dict(family="Inter,sans-serif", size=11),
                legend=dict(orientation="h", yanchor="top", y=-0.18,
                            xanchor="center", x=0.5, font=dict(size=10)),
                margin=dict(l=10, r=10, t=54, b=100), height=430)

def _months(df):
    ms = df["Month"].unique().tolist()
    def k(m):
        p=m.split(); return int(p[1])*100+MN.get(p[0],0) if len(p)==2 else 0
    return sorted(ms, key=k)

def _reindex(df, proj, months):
    return df[df["Project"]==proj].set_index("Month").reindex(months).reset_index()

# ── 1. Portfolio efficiency trend ─────────────────────────────────────────────
def portfolio_efficiency_trend(pf):
    mo = _months(pf)
    df = pf.set_index("Month").reindex(mo).reset_index()
    fig = go.Figure()
    fig.add_scatter(x=df["Month"], y=df["Collection_Efficiency_Pct"],
        mode="lines+markers+text", name="Efficiency %",
        line=dict(color=BLUE, width=3), marker=dict(size=9),
        text=[f"<b>{v:.1f}%</b>" for v in df["Collection_Efficiency_Pct"]],
        textposition="top center", fill="tozeroy", fillcolor="rgba(26,60,110,0.08)")
    fig.add_hline(y=90, line_dash="dash", line_color=GREEN, line_width=1.5,
        annotation_text="90% target", annotation_position="right")
    fig.update_layout(**_base(),
        title="<b>Portfolio Collection Efficiency %</b> — Month on Month",
        xaxis=dict(categoryorder="array", categoryarray=mo),
        yaxis=dict(ticksuffix="%", range=[0,115], gridcolor="#f0f0f0"),
        showlegend=False)
    return fig

# ── 2. Outstanding → Target → Forecast → Achievement ─────────────────────────
def portfolio_target_vs_achievement(pf):
    mo = _months(pf)
    df = pf.set_index("Month").reindex(mo).reset_index()
    fig = go.Figure()
    # Order: Outstanding at month start, Target, Forecast, Achievement
    fig.add_bar(name="Outstanding (Month Start)", x=df["Month"],
        y=df["SpillOver_Target_Cr"], marker_color="#EF9A9A",
        text=[f"₹{v:.1f}" for v in df["SpillOver_Target_Cr"]], textposition="inside",
        textfont=dict(size=10))
    fig.add_bar(name="Monthly Target", x=df["Month"],
        y=df["Monthly_Target_Cr"], marker_color="#90A4AE",
        text=[f"₹{v:.1f}" for v in df["Monthly_Target_Cr"]], textposition="inside",
        textfont=dict(size=10))
    fig.add_bar(name="Forecast", x=df["Month"],
        y=df["Forecast_Cr"], marker_color=GOLD,
        text=[f"₹{v:.1f}" for v in df["Forecast_Cr"]], textposition="inside",
        textfont=dict(size=10))
    fig.add_bar(name="Achievement", x=df["Month"],
        y=df["Monthly_Achievement_Cr"], marker_color=GREEN,
        text=[f"₹{v:.1f}" for v in df["Monthly_Achievement_Cr"]], textposition="inside",
        textfont=dict(size=10))
    fig.update_layout(**_base(),
        title="<b>Outstanding → Target → Forecast → Achievement</b> (₹ Cr)",
        barmode="group", yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array", categoryarray=mo))
    return fig

# ── 3. Project achievement % trend ───────────────────────────────────────────
def project_achievement_trend(mom):
    mo = _months(mom); projs = sorted(mom["Project"].unique())
    fig = go.Figure()
    for i, proj in enumerate(projs):
        d = _reindex(mom, proj, mo)
        fig.add_scatter(x=d["Month"], y=d["Achievement_Pct"],
            mode="lines+markers", name=proj, connectgaps=True,
            line=dict(color=PC[i%len(PC)], width=2.5), marker=dict(size=8))
    fig.add_hline(y=100, line_dash="dash", line_color=GREEN, annotation_text="100% target")
    fig.update_layout(**_base(),
        title="<b>Project Achievement % vs Target</b> — MoM",
        xaxis=dict(categoryorder="array", categoryarray=mo),
        yaxis=dict(ticksuffix="%", gridcolor="#f0f0f0"))
    return fig

# ── 4. Outstanding trend ──────────────────────────────────────────────────────
def outstanding_trend(mom):
    mo = _months(mom); projs = sorted(mom["Project"].unique())
    fig = go.Figure()
    for i, proj in enumerate(projs):
        d = _reindex(mom, proj, mo)
        fig.add_scatter(x=d["Month"], y=d["Outstanding_Cr"],
            mode="lines+markers", name=proj, connectgaps=True,
            line=dict(color=PC[i%len(PC)], width=2.5), marker=dict(size=8))
    fig.update_layout(**_base(),
        title="<b>Outstanding (₹ Cr)</b> — Month on Month by Project",
        xaxis=dict(categoryorder="array", categoryarray=mo),
        yaxis=dict(title="₹ Cr", gridcolor="#f0f0f0"))
    return fig

# ── 5. Spill Over collection ──────────────────────────────────────────────────
def spillover_trend(mom):
    mo = _months(mom); projs = sorted(mom["Project"].unique())
    fig = go.Figure()
    for i, proj in enumerate(projs):
        d = _reindex(mom, proj, mo)
        vals = [float(v) if pd.notna(v) else 0 for v in d["SpillOver_Achievement_Cr"]]
        fig.add_bar(name=proj, x=mo, y=vals, marker_color=PC[i%len(PC)])
    port = mom.groupby("Month")["SpillOver_Target_Cr"].sum().reindex(mo)
    fig.add_scatter(x=mo, y=port.values, mode="lines+markers",
        name="Outstanding at Month Start",
        line=dict(color=RED, width=2.5, dash="dash"), marker=dict(size=8))
    fig.update_layout(**_base(),
        title="<b>Spill Over Collection</b> (CRM Responsibility) — vs Outstanding Start (₹ Cr)",
        barmode="stack", yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array", categoryarray=mo))
    return fig

# ── 6. Sales team OCR & New Bookings ─────────────────────────────────────────
def sales_contribution_chart(mom):
    mo = _months(mom)
    port = mom.groupby("Month").agg(
        OCR_Tgt=("OCR_Target_Cr","sum"), OCR_Ach=("OCR_Achievement_Cr","sum"),
        NB_Tgt=("NewBooking_Target_Cr","sum"), NB_Ach=("NewBooking_Achievement_Cr","sum"),
    ).reindex(mo).reset_index()
    fig = go.Figure()
    fig.add_bar(name="OCR Target",x=port["Month"],y=port["OCR_Tgt"],
        marker_color="#B2EBF2",text=[f"₹{v:.2f}" for v in port["OCR_Tgt"]],textposition="inside")
    fig.add_bar(name="OCR Achievement",x=port["Month"],y=port["OCR_Ach"],
        marker_color=TEAL,text=[f"₹{v:.2f}" for v in port["OCR_Ach"]],textposition="inside")
    fig.add_bar(name="New Booking Target",x=port["Month"],y=port["NB_Tgt"],
        marker_color="#FFE0B2",text=[f"₹{v:.2f}" for v in port["NB_Tgt"]],textposition="inside")
    fig.add_bar(name="New Booking Ach",x=port["Month"],y=port["NB_Ach"],
        marker_color=AMBER,text=[f"₹{v:.2f}" for v in port["NB_Ach"]],textposition="inside")
    fig.update_layout(**_base(),
        title="<b>Sales Team — OCR & New Bookings</b> Target vs Achievement (₹ Cr)<br>"
              "<sup>OCR = Own Contribution. Collected by Sales Team; reported by CRM.</sup>",
        barmode="group", yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array", categoryarray=mo))
    return fig

# ── 7. Monthly collection stacked ────────────────────────────────────────────
def monthly_collection_stacked(mom):
    mo = _months(mom); projs = sorted(mom["Project"].unique())
    fig = go.Figure()
    for i, proj in enumerate(projs):
        d = mom[mom["Project"]==proj].set_index("Month")
        vals = [float(d.loc[m,"Monthly_Collection_Cr"]) if m in d.index else 0 for m in mo]
        fig.add_bar(name=proj, x=mo, y=vals, marker_color=PC[i%len(PC)])
    fig.update_layout(**_base(),
        title="<b>Monthly Collection by Project</b> (₹ Cr) — Stacked",
        barmode="stack", yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array", categoryarray=mo))
    return fig

# ── 8. Forecast accuracy ──────────────────────────────────────────────────────
def forecast_accuracy_chart(mom):
    fig = go.Figure()
    projs = sorted(mom["Project"].unique())
    for i, proj in enumerate(projs):
        d = mom[mom["Project"]==proj]
        fig.add_scatter(x=d["Forecast_Cr"], y=d["Monthly_Achievement_Cr"],
            mode="markers", name=proj,
            marker=dict(size=11, color=PC[i%len(PC)], line=dict(width=1.5, color="#fff")))
    mx = max(mom["Forecast_Cr"].max(), mom["Monthly_Achievement_Cr"].max()) * 1.1
    fig.add_scatter(x=[0,mx], y=[0,mx], mode="lines",
        line=dict(dash="dash", color="#aaa", width=1), name="Perfect forecast")
    fig.update_layout(**_base(),
        title="<b>Forecast Accuracy</b> — Forecast vs Actual (₹ Cr)",
        xaxis_title="Forecast (Cr)", yaxis_title="Achievement (Cr)")
    return fig

# ── 9. Pending registration trend ────────────────────────────────────────────
def pending_reg_trend(mom):
    mo = _months(mom); projs = sorted(mom["Project"].unique())
    fig = go.Figure()
    for i, proj in enumerate(projs):
        d = _reindex(mom, proj, mo)
        if d["Pending_Reg"].sum() == 0: continue
        fig.add_scatter(x=d["Month"], y=d["Pending_Reg"],
            mode="lines+markers", name=proj, connectgaps=True,
            line=dict(color=PC[i%len(PC)], width=2.5), marker=dict(size=8))
    fig.update_layout(**_base(),
        title="<b>Pending Registrations</b> — Month on Month",
        xaxis=dict(categoryorder="array", categoryarray=mo),
        yaxis=dict(title="Count", gridcolor="#f0f0f0"))
    return fig

# ── 10. MoM heatmap ───────────────────────────────────────────────────────────
def mom_heatmap(mom, metric="Achievement_Pct"):
    mo = _months(mom)
    pivot = mom.pivot_table(index="Project", columns="Month", values=metric, aggfunc="mean")
    pivot = pivot[[m for m in mo if m in pivot.columns]]
    sfx = "%" if "Pct" in metric else " Cr"
    txt = [[f"{v:.1f}{sfx}" if pd.notna(v) else "—" for v in row] for row in pivot.values]
    labels = {
        "Achievement_Pct":           "Achievement % vs Target",
        "Collection_Efficiency_Pct": "Collection Efficiency %",
        "Outstanding_Cr":            "Outstanding (₹ Cr)",
        "Monthly_Collection_Cr":     "Monthly Collection (₹ Cr)",
        "SpillOver_Achievement_Cr":  "Spill Over Collection (₹ Cr)",
    }
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        text=txt, texttemplate="%{text}",
        colorscale="RdYlGn" if "Pct" in metric else "Blues", showscale=True,
        hovertemplate="Project: %{y}<br>Month: %{x}<br>%{text}<extra></extra>"))
    base = _base()
    base["margin"] = dict(l=150, r=20, t=54, b=40)
    base["height"]  = 340
    base["showlegend"] = False
    fig.update_layout(**base,
        title=f"<b>MoM Heatmap</b> — {labels.get(metric, metric)}")
    return fig
