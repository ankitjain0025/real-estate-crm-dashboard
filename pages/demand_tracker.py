"""
Page: Demand Tracker — demand raised vs collection target tracking.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(page_title="Demand Tracker", page_icon="📋", layout="wide")
st.markdown("## 📋 Demand Tracker")
st.caption("Monthly & cumulative demand vs collection tracking by project")

EXCEL_FILE = "data/Overall Collection Summary.xlsx"

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data(EXCEL_FILE)
    except Exception as e:
        st.error(f"Data load error: {e}")
        st.stop()

# ── KPIs ──────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Demand Raised", format_cr(kpis["total_demand"]))
c2.metric("Total Collection", format_cr(kpis["total_collection"]))
c3.metric("Outstanding", format_cr(kpis["total_outstanding"]))
c4.metric("Monthly Target", format_cr(kpis["crm_monthly_tgt"]))

st.markdown("---")

# ── Waterfall: demand → collection → outstanding ─────────
fig_wf = go.Figure(go.Waterfall(
    name="CRM",
    orientation="v",
    measure=["absolute", "relative", "total"],
    x=["Demand Raised", "Collection", "Outstanding"],
    y=[
        kpis["total_demand"],
        -kpis["total_collection"],
        0,
    ],
    totals={"marker": {"color": "#C62828"}},
    increasing={"marker": {"color": "#1A3C6E"}},
    decreasing={"marker": {"color": "#2E7D32"}},
    connector={"line": {"color": "#aaa"}},
    text=[
        format_cr(kpis["total_demand"]),
        format_cr(kpis["total_collection"]),
        format_cr(kpis["total_outstanding"]),
    ],
    textposition="outside",
))
fig_wf.update_layout(
    title="Demand → Collection → Outstanding (₹ Cr)",
    template="plotly_white",
    height=380,
    showlegend=False,
)
st.plotly_chart(fig_wf, use_container_width=True)

# ── Project-wise demand vs collection table ───────────────
st.markdown("### Project-wise Demand vs Collection")

df = project_df.copy()
df["Collection Gap (Cr)"] = (df["Actual Demand Raised (Cr)"] - df["Collection Till Date (Cr)"]).round(4)
df["Achievement %"] = (df["Collection Till Date (Cr)"] / df["Actual Demand Raised (Cr)"] * 100).fillna(0).round(1)

display = df[[
    "Project", "Total Live Bookings",
    "Actual Demand Raised (Cr)", "Collection Till Date (Cr)",
    "Collection Gap (Cr)", "Outstanding (Cr)",
    "Monthly Collection (Cr)", "Collection Target (Cr)",
    "Achievement %",
]].copy()

st.dataframe(
    display.style
    .background_gradient(subset=["Collection Gap (Cr)"], cmap="Reds")
    .background_gradient(subset=["Achievement %"], cmap="Greens")
    .format({
        "Actual Demand Raised (Cr)": "₹{:.2f} Cr",
        "Collection Till Date (Cr)": "₹{:.2f} Cr",
        "Collection Gap (Cr)":       "₹{:.2f} Cr",
        "Outstanding (Cr)":          "₹{:.2f} Cr",
        "Monthly Collection (Cr)":   "₹{:.2f} Cr",
        "Collection Target (Cr)":    "₹{:.2f} Cr",
        "Achievement %":             "{:.1f}%",
    }),
    use_container_width=True,
)

# ── Category breakdown ────────────────────────────────────
if not category_df.empty:
    st.markdown("---")
    st.markdown("### Category-wise Demand Breakdown")
    fig_cat = px.bar(
        category_df,
        x="Category",
        y=["Target (Cr)", "Achievement (Cr)", "Forecast (Cr)"],
        barmode="group",
        title="Category-wise Target vs Achievement vs Forecast",
        color_discrete_sequence=["#1A3C6E", "#C9A84C", "#00695C"],
    )
    fig_cat.update_layout(
        template="plotly_white", height=400,
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_cat, use_container_width=True)
    st.dataframe(category_df, use_container_width=True)

# ── Export ────────────────────────────────────────────────
st.markdown("---")
csv = display.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export Demand Tracker CSV", csv, "demand_tracker.csv", "text/csv")
