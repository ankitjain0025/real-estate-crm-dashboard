"""
Page: Outstanding & Registration Risk Tracker
Fix: Outstanding % thresholds corrected, Risk Level based on outstanding %
     not pending reg count (which was causing Enclave to show wrong risk).
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(page_title="Outstanding & Risk", page_icon="⚠️", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#7B1FA2 0%,#4A148C 100%);
            color:#fff;padding:16px 24px;border-radius:8px;margin-bottom:16px;">
  <span style="font-size:1.3rem;font-weight:700;">⚠️ Outstanding & Registration Risk Tracker</span>
  <span style="font-size:0.82rem;color:#E1BEE7;margin-left:12px;">
    Risk-ranked outstanding amounts and registration delay aging
  </span>
</div>""", unsafe_allow_html=True)

st.info("ℹ️ **Note:** The Excel file does not contain per-unit interest charge data. "
        "This page tracks outstanding collection risk and registration delays — "
        "the two primary risk indicators in the CRM report.")

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data()
    except Exception as e:
        st.error(f"Data load error: {e}"); st.stop()

# KPIs
c1, c2, c3, c4 = st.columns(4)
total_demand = kpis["total_demand"]
total_out    = kpis["total_outstanding"]
out_pct      = round(total_out/total_demand*100, 1) if total_demand else 0
c1.metric("Total Outstanding",    format_cr(total_out))
c2.metric("Outstanding % of Demand", f"{out_pct}%")
c3.metric("Total Pending Reg",    int(kpis["pending_reg"]))
c4.metric("Critical > 45 Days",   int(kpis["pending_reg_45"]))

st.markdown("---")

# Build risk df — risk based on outstanding % of demand (correct metric)
df = project_df.copy()
df["Outstanding %"] = (
    df["Outstanding (Cr)"] / df["Actual Demand Raised (Cr)"] * 100
).fillna(0).round(1)

# Risk Level based on outstanding % thresholds
df["Risk Level"] = df["Outstanding %"].apply(
    lambda x: "🔴 High" if x > 15 else ("🟡 Medium" if x > 5 else "🟢 Low")
)

# Chart 1 — Outstanding amount by project
st.markdown("### Outstanding Amount by Project")
df_sorted = df.sort_values("Outstanding (Cr)", ascending=True)
bar_colors = [
    "#C62828" if r == "🔴 High" else ("#E65100" if r == "🟡 Medium" else "#2E7D32")
    for r in df_sorted["Risk Level"]
]
fig_out = go.Figure(go.Bar(
    x=df_sorted["Outstanding (Cr)"], y=df_sorted["Project"],
    orientation="h", marker_color=bar_colors,
    text=[f"₹{v:.2f} Cr  ({p:.1f}%)" for v, p in
          zip(df_sorted["Outstanding (Cr)"], df_sorted["Outstanding %"])],
    textposition="outside",
))
fig_out.update_layout(
    title="<b>Outstanding Amount & % of Demand</b> — 🔴 >15% High Risk | 🟡 5-15% Medium | 🟢 <5% Low",
    template="plotly_white", height=380, showlegend=False,
    xaxis_title="₹ Crores", margin=dict(l=140, r=20, t=60, b=40),
)
st.plotly_chart(fig_out, use_container_width=True)

# Chart 2 — Outstanding % of demand (risk view)
st.markdown("---")
st.markdown("### Outstanding as % of Demand Raised — Risk Ranking")
df_pct = df.sort_values("Outstanding %", ascending=False)
pct_colors = [
    "#C62828" if v > 15 else ("#E65100" if v > 5 else "#2E7D32")
    for v in df_pct["Outstanding %"]
]
fig_pct = go.Figure(go.Bar(
    x=df_pct["Project"], y=df_pct["Outstanding %"],
    marker_color=pct_colors,
    text=[f"{v:.1f}%" for v in df_pct["Outstanding %"]],
    textposition="outside",
))
fig_pct.add_hline(y=5,  line_dash="dash", line_color="#E65100",
                  annotation_text="5% — medium risk threshold", annotation_position="right")
fig_pct.add_hline(y=15, line_dash="dash", line_color="#C62828",
                  annotation_text="15% — high risk threshold",  annotation_position="right")
fig_pct.update_layout(
    template="plotly_white", height=400, showlegend=False,
    yaxis=dict(ticksuffix="%", range=[0, max(df_pct["Outstanding %"].max()*1.2, 20)]),
    margin=dict(t=60, b=60),
)
st.plotly_chart(fig_pct, use_container_width=True)

# Charts 3 & 4 — Risk matrix + Registration aging
c1, c2 = st.columns(2)
with c1:
    fig_b = px.scatter(df, x="Outstanding (Cr)", y="Pending Reg > 45 Days",
        size=df["Outstanding (Cr)"].clip(lower=0.1),
        color="Risk Level", text="Project",
        title="<b>Risk Matrix:</b> Outstanding vs Delayed Registrations",
        color_discrete_map={"🔴 High":"#C62828","🟡 Medium":"#E65100","🟢 Low":"#2E7D32"})
    fig_b.update_traces(textposition="top center")
    fig_b.update_layout(template="plotly_white", height=400,
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(t=60, b=100))
    st.plotly_chart(fig_b, use_container_width=True)

with c2:
    fig_reg = go.Figure()
    fig_reg.add_bar(name="Total Pending", x=df["Project"], y=df["Pending Registrations"],
        marker_color="#FFB74D", text=df["Pending Registrations"].astype(int),
        textposition="outside")
    fig_reg.add_bar(name="Critical >45 Days", x=df["Project"], y=df["Pending Reg > 45 Days"],
        marker_color="#C62828", text=df["Pending Reg > 45 Days"].astype(int),
        textposition="outside")
    fig_reg.update_layout(barmode="overlay", template="plotly_white", height=400,
        title="<b>Pending Registration Aging</b> by Project", yaxis_title="Count",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(t=60, b=100))
    st.plotly_chart(fig_reg, use_container_width=True)

# Registration targets vs completions
if "Registration Targets" in df.columns:
    st.markdown("---")
    st.markdown("### Registration Targets vs Completions")
    fig_rt = go.Figure()
    fig_rt.add_bar(name="Registration Target", x=df["Project"],
        y=df["Registration Targets"], marker_color="#1A3C6E",
        text=df["Registration Targets"].astype(int), textposition="outside")
    fig_rt.add_bar(name="Completed This Month", x=df["Project"],
        y=df["Monthly Registrations"], marker_color="#2E7D32",
        text=df["Monthly Registrations"].astype(int), textposition="outside")
    fig_rt.update_layout(barmode="group", template="plotly_white", height=360,
        title="<b>Monthly Registration Target vs Completions</b>",
        yaxis_title="Count",
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(t=60, b=100))
    st.plotly_chart(fig_rt, use_container_width=True)

# Summary table
st.markdown("---")
st.markdown("### Outstanding & Risk Summary Table")
display = df[["Project","Actual Demand Raised (Cr)","Collection Till Date (Cr)",
              "Outstanding (Cr)","Outstanding %","Pending Registrations",
              "Pending Reg > 45 Days","Risk Level"]].copy()
display["Pending Registrations"]  = display["Pending Registrations"].astype(int)
display["Pending Reg > 45 Days"]  = display["Pending Reg > 45 Days"].astype(int)
st.dataframe(display.style.format({
    "Actual Demand Raised (Cr)": "₹ {:.2f} Cr",
    "Collection Till Date (Cr)": "₹ {:.2f} Cr",
    "Outstanding (Cr)":          "₹ {:.2f} Cr",
    "Outstanding %":             "{:.1f}%",
}), use_container_width=True, hide_index=True)

csv = display.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export Outstanding Risk Report CSV",
    csv, "outstanding_risk_report.csv", "text/csv")
