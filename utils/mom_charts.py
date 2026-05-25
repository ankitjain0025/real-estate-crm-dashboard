"""
utils/mom_charts.py  — Month-on-month premium charts
Fixes: chronological month order, SpillOver as "Outstanding at Month Start",
       OCR/NewBooking labelled correctly (Sales team).
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

BLUE="#1A3C6E"; GREEN="#2E7D32"; RED="#C62828"; AMBER="#E65100"
GOLD="#C9A84C"; TEAL="#00695C"; PURPLE="#6A1B9A"; PINK="#AD1457"
PC=[BLUE,GREEN,RED,AMBER,GOLD,TEAL,PURPLE,PINK]
MN={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
    "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

LAYOUT=dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
    template="plotly_white",font=dict(family="Inter,sans-serif",size=12),
    legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
    margin=dict(l=10,r=10,t=54,b=40),height=420)

def _months(df):
    ms=df["Month"].unique().tolist()
    def k(m):
        p=m.split(); return int(p[1])*100+MN.get(p[0],0) if len(p)==2 else 0
    return sorted(ms,key=k)

def _reindex(df,proj,months):
    return df[df["Project"]==proj].set_index("Month").reindex(months).reset_index()

# ── 1. Portfolio efficiency ────────────────────────────────────────────────────
def portfolio_efficiency_trend(pf):
    mo=_months(pf)
    df=pf.set_index("Month").reindex(mo).reset_index()
    fig=go.Figure()
    fig.add_scatter(x=df["Month"],y=df["Collection_Efficiency_Pct"],
        mode="lines+markers+text",name="Efficiency %",
        line=dict(color=BLUE,width=3),marker=dict(size=9,color=BLUE),
        text=[f"<b>{v:.1f}%</b>" for v in df["Collection_Efficiency_Pct"]],
        textposition="top center",fill="tozeroy",fillcolor="rgba(26,60,110,0.08)")
    fig.add_hline(y=90,line_dash="dash",line_color=GREEN,line_width=1.5,
        annotation_text="90% target",annotation_position="right")
    fig.update_layout(**LAYOUT,title="<b>Portfolio Collection Efficiency %</b> — Month on Month",
        xaxis=dict(categoryorder="array",categoryarray=mo),
        yaxis=dict(ticksuffix="%",range=[0,115],gridcolor="#f0f0f0"))
    return fig

# ── 2. Target vs SpillOver vs Achievement vs Forecast ─────────────────────────
def portfolio_target_vs_achievement(pf):
    mo=_months(pf)
    df=pf.set_index("Month").reindex(mo).reset_index()
    fig=go.Figure()
    fig.add_bar(name="Outstanding (Month Start)",x=df["Month"],
        y=df["SpillOver_Target_Cr"],marker_color="#EF9A9A",
        text=[f"₹{v:.1f}" for v in df["SpillOver_Target_Cr"]],textposition="inside")
    fig.add_bar(name="Monthly Target",x=df["Month"],
        y=df["Monthly_Target_Cr"],marker_color="#90A4AE",
        text=[f"₹{v:.1f}" for v in df["Monthly_Target_Cr"]],textposition="inside")
    fig.add_bar(name="Forecast",x=df["Month"],
        y=df["Forecast_Cr"],marker_color=GOLD,
        text=[f"₹{v:.1f}" for v in df["Forecast_Cr"]],textposition="inside")
    fig.add_bar(name="Achievement",x=df["Month"],
        y=df["Monthly_Achievement_Cr"],marker_color=GREEN,
        text=[f"₹{v:.1f}" for v in df["Monthly_Achievement_Cr"]],textposition="inside")
    fig.update_layout(**LAYOUT,
        title="<b>Outstanding (Month Start) → Target → Forecast → Achievement</b> (₹ Cr)",
        barmode="group",yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array",categoryarray=mo))
    return fig

# ── 3. Project achievement % trend ────────────────────────────────────────────
def project_achievement_trend(mom):
    mo=_months(mom); projs=sorted(mom["Project"].unique())
    fig=go.Figure()
    for i,proj in enumerate(projs):
        d=_reindex(mom,proj,mo)
        fig.add_scatter(x=d["Month"],y=d["Achievement_Pct"],
            mode="lines+markers",name=proj,connectgaps=True,
            line=dict(color=PC[i%len(PC)],width=2.5),marker=dict(size=8))
    fig.add_hline(y=100,line_dash="dash",line_color=GREEN,annotation_text="100% target")
    fig.update_layout(**LAYOUT,
        title="<b>Project Achievement % vs Target</b> — MoM",
        xaxis=dict(categoryorder="array",categoryarray=mo),
        yaxis=dict(ticksuffix="%",gridcolor="#f0f0f0"))
    return fig

# ── 4. Outstanding trend ──────────────────────────────────────────────────────
def outstanding_trend(mom):
    mo=_months(mom); projs=sorted(mom["Project"].unique())
    fig=go.Figure()
    for i,proj in enumerate(projs):
        d=_reindex(mom,proj,mo)
        fig.add_scatter(x=d["Month"],y=d["Outstanding_Cr"],
            mode="lines+markers",name=proj,connectgaps=True,
            line=dict(color=PC[i%len(PC)],width=2.5),marker=dict(size=8))
    fig.update_layout(**LAYOUT,
        title="<b>Outstanding (₹ Cr)</b> — Month on Month by Project",
        xaxis=dict(categoryorder="array",categoryarray=mo),
        yaxis=dict(title="₹ Cr",gridcolor="#f0f0f0"))
    return fig

# ── 5. Spill Over: CRM collection of outstanding ─────────────────────────────
def spillover_trend(mom):
    mo=_months(mom); projs=sorted(mom["Project"].unique())
    fig=go.Figure()
    for i,proj in enumerate(projs):
        d=_reindex(mom,proj,mo)
        fig.add_bar(name=proj,x=d["Month"],
            y=d["SpillOver_Achievement_Cr"],marker_color=PC[i%len(PC)])
    # Add line for total target
    port=mom.groupby("Month")["SpillOver_Target_Cr"].sum().reindex(mo).reset_index()
    fig.add_scatter(x=port["Month"],y=port["SpillOver_Target_Cr"],
        mode="lines+markers",name="Total Outstanding (Start)",
        line=dict(color=RED,width=2.5,dash="dash"),marker=dict(size=8))
    fig.update_layout(**LAYOUT,
        title="<b>Spill Over Collection</b> (CRM Responsibility) — Target vs Achievement (₹ Cr)",
        barmode="stack",yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array",categoryarray=mo))
    return fig

# ── 6. OCR & New Bookings (Sales team) ───────────────────────────────────────
def sales_contribution_chart(mom):
    mo=_months(mom)
    port=mom.groupby("Month").agg(
        OCR_Tgt=("OCR_Target_Cr","sum"),OCR_Ach=("OCR_Achievement_Cr","sum"),
        NB_Tgt=("NewBooking_Target_Cr","sum"),NB_Ach=("NewBooking_Achievement_Cr","sum"),
    ).reindex(mo).reset_index()
    fig=go.Figure()
    fig.add_bar(name="OCR Target",x=port["Month"],y=port["OCR_Tgt"],
        marker_color="#B2EBF2",text=[f"₹{v:.2f}" for v in port["OCR_Tgt"]],textposition="inside")
    fig.add_bar(name="OCR Achievement",x=port["Month"],y=port["OCR_Ach"],
        marker_color=TEAL,text=[f"₹{v:.2f}" for v in port["OCR_Ach"]],textposition="inside")
    fig.add_bar(name="New Booking Target",x=port["Month"],y=port["NB_Tgt"],
        marker_color="#FFE0B2",text=[f"₹{v:.2f}" for v in port["NB_Tgt"]],textposition="inside")
    fig.add_bar(name="New Booking Achievement",x=port["Month"],y=port["NB_Ach"],
        marker_color=AMBER,text=[f"₹{v:.2f}" for v in port["NB_Ach"]],textposition="inside")
    fig.update_layout(**LAYOUT,
        title="<b>Sales Team — OCR & New Bookings</b> Target vs Achievement (₹ Cr)<br>"
              "<sup style='color:#999'>OCR = Own Contribution. Collected by Sales Team; reported by CRM.</sup>",
        barmode="group",yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array",categoryarray=mo))
    return fig

# ── 7. Monthly collection stacked ────────────────────────────────────────────
def monthly_collection_stacked(mom):
    mo=_months(mom); projs=sorted(mom["Project"].unique())
    fig=go.Figure()
    for i,proj in enumerate(projs):
        d=mom[mom["Project"]==proj].set_index("Month")
        vals=[float(d.loc[m,"Monthly_Collection_Cr"]) if m in d.index else 0 for m in mo]
        fig.add_bar(name=proj,x=mo,y=vals,marker_color=PC[i%len(PC)])
    fig.update_layout(**LAYOUT,
        title="<b>Monthly Collection by Project</b> (₹ Cr) — Stacked",
        barmode="stack",yaxis_title="₹ Cr",
        xaxis=dict(categoryorder="array",categoryarray=mo))
    return fig

# ── 8. Forecast accuracy ──────────────────────────────────────────────────────
def forecast_accuracy_chart(mom):
    fig=go.Figure()
    projs=sorted(mom["Project"].unique())
    for i,proj in enumerate(projs):
        d=mom[mom["Project"]==proj]
        fig.add_scatter(x=d["Forecast_Cr"],y=d["Monthly_Achievement_Cr"],
            mode="markers+text",name=proj,
            marker=dict(size=11,color=PC[i%len(PC)],
                        line=dict(width=1.5,color="#fff")),
            text=d["Month"],textposition="top center")
    mx=max(mom["Forecast_Cr"].max(),mom["Monthly_Achievement_Cr"].max())*1.1
    fig.add_scatter(x=[0,mx],y=[0,mx],mode="lines",
        line=dict(dash="dash",color="#aaa",width=1),name="Perfect forecast")
    fig.update_layout(**LAYOUT,
        title="<b>Forecast Accuracy</b> — Forecast vs Actual Achievement (₹ Cr)",
        xaxis_title="Forecast (Cr)",yaxis_title="Achievement (Cr)")
    return fig

# ── 9. Pending registration trend ────────────────────────────────────────────
def pending_reg_trend(mom):
    mo=_months(mom); projs=sorted(mom["Project"].unique())
    fig=go.Figure()
    for i,proj in enumerate(projs):
        d=_reindex(mom,proj,mo)
        if d["Pending_Reg"].sum()==0: continue
        fig.add_scatter(x=d["Month"],y=d["Pending_Reg"],
            mode="lines+markers",name=proj,connectgaps=True,
            line=dict(color=PC[i%len(PC)],width=2.5),marker=dict(size=8))
    fig.update_layout(**LAYOUT,
        title="<b>Pending Registrations</b> — Month on Month",
        xaxis=dict(categoryorder="array",categoryarray=mo),
        yaxis=dict(title="Count",gridcolor="#f0f0f0"))
    return fig

# ── 10. MoM heatmap ──────────────────────────────────────────────────────────
def mom_heatmap(mom,metric="Achievement_Pct"):
    mo=_months(mom)
    pivot=mom.pivot_table(index="Project",columns="Month",values=metric,aggfunc="mean")
    pivot=pivot[[m for m in mo if m in pivot.columns]]
    sfx="%" if "Pct" in metric else " Cr"
    txt=[[f"{v:.1f}{sfx}" if pd.notna(v) else "—" for v in row] for row in pivot.values]
    labels={"Achievement_Pct":"Achievement % vs Target",
             "Collection_Efficiency_Pct":"Collection Efficiency %",
             "Outstanding_Cr":"Outstanding (₹ Cr)",
             "Monthly_Collection_Cr":"Monthly Collection (₹ Cr)",
             "SpillOver_Achievement_Cr":"Spill Over Collection (₹ Cr)"}
    fig=go.Figure(go.Heatmap(
        z=pivot.values,x=pivot.columns.tolist(),y=pivot.index.tolist(),
        text=txt,texttemplate="%{text}",
        colorscale="RdYlGn" if "Pct" in metric else "Blues",showscale=True,
        hovertemplate="Project: %{y}<br>Month: %{x}<br>%{text}<extra></extra>"))
    fig.update_layout(**{**LAYOUT,"height":330,"margin":dict(l=150,r=20,t=54,b=60)},
        title=f"<b>MoM Heatmap</b> — {labels.get(metric,metric)}")
    return fig
