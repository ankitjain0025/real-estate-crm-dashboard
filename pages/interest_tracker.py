"""
Page: Interest / Overdue Tracker — outstanding & pending registration aging.
The Excel does not have per-unit interest columns, so this page derives
interest-risk proxies from outstanding amounts and pending registration delays.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(page_title="Interest & Overdue Tracker", page_icon="📉", layout="wide")
st.markdown("## 📉 Interest & Overdue Tracker")
st.caption(
    "Outstanding amounts and registration delay analysis across projects. "
    "Projects with pending registrations > 45 days are flagged as high-risk."
)

EXCEL_FILE = "data/Overall Collection Summary.xlsx"

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data(EXCEL_FILE)
    except Exception as e:
        st.error(f"Data load error: {e}")
        st.stop()

# ── KPIs ──────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Total Outstanding", format_cr(kpis["total_outstanding"]))
c2.metric("Pending Registrations", int(kpis["pending_reg"]))
c3.metric("Critical (> 45 Days)", int(kpis["pending_reg_45"]))

st.markdown("---")

# ── Risk classification ───────────────────────────────────
df = project_df.copy()
df["Risk Level"] = df["Pending Reg > 45 Days"].apply(
    lambda x: "🔴 High Risk" if x >= 5 else ("🟡 Medium Risk" if x >= 2 else "🟢 Low Risk")
)
df["Outstanding %"] = (
    df["Outstanding (Cr)"] / df["Actual Demand Raised (Cr)"] * 100
).fillna(0).round(1)

# ── Overdue bubble chart ──────────────────────────────────
fig_bubble = px.scatter(
    df,
    x="Outstanding (Cr)",
    y="Pending Reg > 45 Days",
    size="Outstanding (Cr)",
    color="Risk Level",
    text="Project",
    title="Outstanding (Cr) vs Delayed Registrations (>45 days) — Risk Matrix",
    color_discrete_map={
        "🔴 High Risk": "#C62828",
        "🟡 Medium Risk": "#E65100",
        "🟢 Low Risk": "#2E7D32",
    },
)
fig_bubble.update_traces(textposition="top center")
fig_bubble.update_layout(template="plotly_white", height=420)
st.plotly_chart(fig_bubble, use_container_width=True)

# ── Pending registration aging bar ───────────────────────
fig_reg = go.Figure()
fig_reg.add_bar(
    name="Total Pending Registrations",
    x=df["Project"],
    y=df["Pending Registrations"],
    marker_color="#E65100",
    text=df["Pending Registrations"],
    textposition="outside",
)
fig_reg.add_bar(
    name="Critical Pending (> 45 Days)",
    x=df["Project"],
    y=df["Pending Reg > 45 Days"],
    marker_color="#C62828",
    text=df["Pending Reg > 45 Days"],
    textposition="outside",
)
fig_reg.update_layout(
    barmode="overlay",
    title="Registration Delay Aging by Project",
    template="plotly_white",
    height=380,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    yaxis_title="Count",
)
st.plotly_chart(fig_reg, use_container_width=True)

# ── Outstanding % bar ─────────────────────────────────────
fig_out = px.bar(
    df.sort_values("Outstanding %", ascending=False),
    x="Project",
    y="Outstanding %",
    color="Risk Level",
    text="Outstanding %",
    title="Outstanding as % of Demand Raised",
    color_discrete_map={
        "🔴 High Risk": "#C62828",
        "🟡 Medium Risk": "#E65100",
        "🟢 Low Risk": "#2E7D32",
    },
)
fig_out.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_out.add_hline(y=20, line_dash="dash", line_color="grey",
                   annotation_text="20% threshold")
fig_out.update_layout(template="plotly_white", height=380)
st.plotly_chart(fig_out, use_container_width=True)

# ── Detail table ─────────────────────────────────────────
st.markdown("### Outstanding & Risk Summary Table")
display = df[[
    "Project", "Actual Demand Raised (Cr)", "Collection Till Date (Cr)",
    "Outstanding (Cr)", "Outstanding %",
    "Pending Registrations", "Pending Reg > 45 Days", "Risk Level",
]]
st.dataframe(
    display.style
    .background_gradient(subset=["Outstanding (Cr)"], cmap="Reds")
    .background_gradient(subset=["Pending Reg > 45 Days"], cmap="Oranges")
    .format({
        "Actual Demand Raised (Cr)": "₹{:.2f} Cr",
        "Collection Till Date (Cr)": "₹{:.2f} Cr",
        "Outstanding (Cr)":          "₹{:.2f} Cr",
        "Outstanding %":             "{:.1f}%",
    }),
    use_container_width=True,
)

# ── Export ────────────────────────────────────────────────
st.markdown("---")
csv = display.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export Overdue Report CSV", csv, "overdue_report.csv", "text/csv")
