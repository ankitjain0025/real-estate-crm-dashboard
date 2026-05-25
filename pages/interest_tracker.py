"""
Page: Outstanding & Registration Risk Tracker
Renamed from "Interest Tracker" — the Excel has no per-unit interest columns.
This page covers:
  - Outstanding amount by project (risk-ranked)
  - Pending registration aging (total vs >45 days)
  - Risk matrix: outstanding vs delayed registrations
  - Registration targets vs completions
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(
    page_title="Outstanding & Registration Risk",
    page_icon="⚠️",
    layout="wide",
)

st.markdown("""
<div style="background:linear-gradient(135deg,#7B1FA2 0%,#4A148C 100%);
            color:#fff;padding:16px 24px;border-radius:8px;margin-bottom:16px;">
  <span style="font-size:1.3rem;font-weight:700;">⚠️ Outstanding & Registration Risk Tracker</span>
  <span style="font-size:0.82rem;color:#E1BEE7;margin-left:12px;">
    Risk-ranked outstanding amounts and registration delay aging
  </span>
</div>
""", unsafe_allow_html=True)

st.info(
    "ℹ️ **Note:** The Excel file does not contain per-unit interest charge data. "
    "This page tracks **outstanding collection risk** and **registration delays** — "
    "the two primary risk indicators available in the CRM report. "
    "Add an interest column to the Excel and share it to enable interest tracking."
)

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data()
    except Exception as e:
        st.error(f"Data load error: {e}")
        st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Outstanding",      format_cr(kpis["total_outstanding"]))
c2.metric("Total Pending Reg",      int(kpis["pending_reg"]))
c3.metric("Critical > 45 Days",     int(kpis["pending_reg_45"]))
c4.metric("Outstanding / Demand",
          f"{kpis['total_outstanding']/kpis['total_demand']*100:.1f}%"
          if kpis["total_demand"] else "—")

st.markdown("---")

# ── Risk classification ────────────────────────────────────────────────────────
df = project_df.copy()
df["Outstanding %"] = (
    df["Outstanding (Cr)"] / df["Actual Demand Raised (Cr)"] * 100
).fillna(0).round(1)
df["Risk Level"] = df["Pending Reg > 45 Days"].apply(
    lambda x: "🔴 High" if x >= 5 else ("🟡 Medium" if x >= 2 else "🟢 Low")
)

# ── Chart 1: Outstanding by project (horizontal bar, risk-coloured) ────────────
st.markdown("### Outstanding by Project")
df_sorted = df.sort_values("Outstanding (Cr)", ascending=True)
colors = [
    "#C62828" if r == "🔴 High" else ("#E65100" if r == "🟡 Medium" else "#2E7D32")
    for r in df_sorted["Risk Level"]
]
fig_out = go.Figure(go.Bar(
    x=df_sorted["Outstanding (Cr)"],
    y=df_sorted["Project"],
    orientation="h",
    marker_color=colors,
    text=[f"₹{v:.2f} Cr  ({p:.1f}%)" for v, p in
          zip(df_sorted["Outstanding (Cr)"], df_sorted["Outstanding %"])],
    textposition="outside",
))
fig_out.update_layout(
    title="Outstanding Amount & % of Demand (Red=High Risk, Orange=Medium, Green=Low)",
    template="plotly_white", height=380, showlegend=False,
    xaxis_title="₹ Crores", margin=dict(l=130),
)
st.plotly_chart(fig_out, use_container_width=True)

# ── Chart 2: Risk matrix bubble ────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    fig_bubble = px.scatter(
        df,
        x="Outstanding (Cr)",
        y="Pending Reg > 45 Days",
        size=df["Outstanding (Cr)"].clip(lower=0.1),
        color="Risk Level",
        text="Project",
        title="Risk Matrix: Outstanding vs Delayed Registrations",
        color_discrete_map={
            "🔴 High":   "#C62828",
            "🟡 Medium": "#E65100",
            "🟢 Low":    "#2E7D32",
        },
    )
    fig_bubble.update_traces(textposition="top center")
    fig_bubble.update_layout(template="plotly_white", height=400)
    st.plotly_chart(fig_bubble, use_container_width=True)

# ── Chart 3: Registration aging ────────────────────────────────────────────────
with c2:
    fig_reg = go.Figure()
    fig_reg.add_bar(
        name="Total Pending",
        x=df["Project"], y=df["Pending Registrations"],
        marker_color="#E65100",
        text=df["Pending Registrations"], textposition="outside",
    )
    fig_reg.add_bar(
        name="Critical > 45 Days",
        x=df["Project"], y=df["Pending Reg > 45 Days"],
        marker_color="#C62828",
        text=df["Pending Reg > 45 Days"], textposition="outside",
    )
    fig_reg.update_layout(
        barmode="overlay",
        title="Pending Registration Aging by Project",
        template="plotly_white", height=400,
        yaxis_title="Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_reg, use_container_width=True)

# ── Chart 4: Outstanding % of demand ──────────────────────────────────────────
st.markdown("---")
fig_pct = px.bar(
    df.sort_values("Outstanding %", ascending=False),
    x="Project", y="Outstanding %",
    color="Risk Level",
    text="Outstanding %",
    title="Outstanding as % of Demand Raised — Project Risk Ranking",
    color_discrete_map={
        "🔴 High":   "#C62828",
        "🟡 Medium": "#E65100",
        "🟢 Low":    "#2E7D32",
    },
)
fig_pct.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_pct.add_hline(y=5,  line_dash="dash", line_color="#E65100",
                  annotation_text="5% warning threshold")
fig_pct.add_hline(y=15, line_dash="dash", line_color="#C62828",
                  annotation_text="15% critical threshold")
fig_pct.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_pct, use_container_width=True)

# ── Registration targets vs completions ───────────────────────────────────────
st.markdown("---")
st.markdown("### Registration Targets vs Completions")
if "Registration Targets" in df.columns and "Monthly Registrations" in df.columns:
    fig_rt = go.Figure()
    fig_rt.add_bar(
        name="Registration Target",
        x=df["Project"], y=df["Registration Targets"],
        marker_color="#1A3C6E",
        text=df["Registration Targets"].apply(lambda v: int(v)),
        textposition="outside",
    )
    fig_rt.add_bar(
        name="Completed This Month",
        x=df["Project"], y=df["Monthly Registrations"],
        marker_color="#2E7D32",
        text=df["Monthly Registrations"].apply(lambda v: int(v)),
        textposition="outside",
    )
    fig_rt.update_layout(
        barmode="group", template="plotly_white", height=360,
        title="Monthly Registration Target vs Completions",
        yaxis_title="Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_rt, use_container_width=True)

# ── Detail table — plain format, no background_gradient ───────────────────────
st.markdown("### Outstanding & Risk Summary Table")
display = df[[
    "Project", "Actual Demand Raised (Cr)", "Collection Till Date (Cr)",
    "Outstanding (Cr)", "Outstanding %",
    "Pending Registrations", "Pending Reg > 45 Days", "Risk Level",
]].copy()

st.dataframe(
    display.style.format({
        "Actual Demand Raised (Cr)": "₹ {:.2f} Cr",
        "Collection Till Date (Cr)": "₹ {:.2f} Cr",
        "Outstanding (Cr)":          "₹ {:.2f} Cr",
        "Outstanding %":             "{:.1f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

# ── Export ─────────────────────────────────────────────────────────────────────
st.markdown("---")
csv = display.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Export Outstanding Risk Report CSV",
    csv, "outstanding_risk_report.csv", "text/csv",
)
