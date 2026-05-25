"""
Page: Demand Tracker — demand raised vs collection target tracking.
Fix: removed background_gradient (requires matplotlib — now uses bar_color via map instead)
Fix: removed hardcoded Excel filename — uses auto-detect loader
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(page_title="Demand Tracker", page_icon="📋", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#1A3C6E 0%,#0D2040 100%);
            color:#fff;padding:16px 24px;border-radius:8px;margin-bottom:16px;">
  <span style="font-size:1.3rem;font-weight:700;">📋 Demand Tracker</span>
  <span style="font-size:0.82rem;color:#90CAF9;margin-left:12px;">
    Monthly & cumulative demand vs collection by project
  </span>
</div>
""", unsafe_allow_html=True)

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data()
    except Exception as e:
        st.error(f"Data load error: {e}")
        st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Demand Raised",  format_cr(kpis["total_demand"]))
c2.metric("Total Collection",     format_cr(kpis["total_collection"]))
c3.metric("Outstanding",          format_cr(kpis["total_outstanding"]))
c4.metric("Monthly Target",       format_cr(kpis["crm_monthly_tgt"]))

st.markdown("---")

# ── Waterfall: Demand → Collection → Outstanding ───────────────────────────────
fig_wf = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute", "relative", "total"],
    x=["Demand Raised", "Less: Collection", "Outstanding"],
    y=[kpis["total_demand"], -kpis["total_collection"], 0],
    totals={"marker": {"color": "#C62828"}},
    increasing={"marker": {"color": "#1A3C6E"}},
    decreasing={"marker": {"color": "#2E7D32"}},
    connector={"line": {"color": "#aaa"}},
    text=[format_cr(kpis["total_demand"]),
          format_cr(kpis["total_collection"]),
          format_cr(kpis["total_outstanding"])],
    textposition="outside",
))
fig_wf.update_layout(
    title="Portfolio: Demand → Collection → Outstanding (₹ Cr)",
    template="plotly_white", height=380, showlegend=False,
)
st.plotly_chart(fig_wf, use_container_width=True)

# ── Project-wise demand vs collection ─────────────────────────────────────────
st.markdown("### Project-wise Demand vs Collection")

df = project_df.copy()
df["Collection Gap (Cr)"] = (
    df["Actual Demand Raised (Cr)"] - df["Collection Till Date (Cr)"]
).round(2)
df["Coll Eff %"] = (
    df["Collection Till Date (Cr)"] / df["Actual Demand Raised (Cr)"] * 100
).fillna(0).round(1)

# Grouped bar chart — visual summary
fig_proj = go.Figure()
fig_proj.add_bar(
    name="Demand Raised",
    x=df["Project"], y=df["Actual Demand Raised (Cr)"],
    marker_color="#1A3C6E",
    text=df["Actual Demand Raised (Cr)"].apply(lambda v: f"₹{v:.2f}"),
    textposition="outside",
)
fig_proj.add_bar(
    name="Collection Till Date",
    x=df["Project"], y=df["Collection Till Date (Cr)"],
    marker_color="#2E7D32",
    text=df["Collection Till Date (Cr)"].apply(lambda v: f"₹{v:.2f}"),
    textposition="outside",
)
fig_proj.add_bar(
    name="Outstanding",
    x=df["Project"], y=df["Outstanding (Cr)"],
    marker_color="#C62828",
    text=df["Outstanding (Cr)"].apply(lambda v: f"₹{v:.2f}"),
    textposition="outside",
)
fig_proj.update_layout(
    barmode="group", template="plotly_white", height=400,
    title="Project-wise: Demand vs Collection vs Outstanding (₹ Cr)",
    yaxis_title="₹ Cr",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig_proj, use_container_width=True)

# ── Efficiency bar ─────────────────────────────────────────────────────────────
fig_eff = go.Figure(go.Bar(
    x=df["Coll Eff %"],
    y=df["Project"],
    orientation="h",
    marker_color=[
        "#2E7D32" if v >= 90 else ("#E65100" if v >= 70 else "#C62828")
        for v in df["Coll Eff %"]
    ],
    text=[f"{v:.1f}%" for v in df["Coll Eff %"]],
    textposition="outside",
))
fig_eff.add_vline(x=90, line_dash="dash", line_color="#2E7D32",
                  annotation_text="90% target", annotation_position="top right")
fig_eff.update_layout(
    title="Collection Efficiency % by Project",
    template="plotly_white", height=360,
    xaxis=dict(range=[0, 115], ticksuffix="%"),
    margin=dict(l=130),
    showlegend=False,
)
st.plotly_chart(fig_eff, use_container_width=True)

# ── Data table — plain format, no background_gradient ─────────────────────────
display = df[[
    "Project", "Total Live Bookings",
    "Actual Demand Raised (Cr)", "Collection Till Date (Cr)",
    "Collection Gap (Cr)", "Outstanding (Cr)",
    "Monthly Collection (Cr)", "Collection Target (Cr)", "Coll Eff %",
]].copy()

st.dataframe(
    display.style.format({
        "Actual Demand Raised (Cr)": "₹ {:.2f} Cr",
        "Collection Till Date (Cr)": "₹ {:.2f} Cr",
        "Collection Gap (Cr)":       "₹ {:.2f} Cr",
        "Outstanding (Cr)":          "₹ {:.2f} Cr",
        "Monthly Collection (Cr)":   "₹ {:.2f} Cr",
        "Collection Target (Cr)":    "₹ {:.2f} Cr",
        "Coll Eff %":                "{:.1f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

# ── Category breakdown ─────────────────────────────────────────────────────────
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
    cat_disp = category_df.copy()
    if "Achievement %" in cat_disp.columns:
        cat_disp["Achievement %"] = (cat_disp["Achievement %"] * 100).round(1)
    st.dataframe(cat_disp.style.format({
        "Target (Cr)":      "₹ {:.2f} Cr",
        "Achievement (Cr)": "₹ {:.2f} Cr",
        "Forecast (Cr)":    "₹ {:.2f} Cr",
        "Balance (Cr)":     "₹ {:.2f} Cr",
        "Achievement %":    "{:.1f}%",
    }), use_container_width=True, hide_index=True)

# ── Export ─────────────────────────────────────────────────────────────────────
st.markdown("---")
csv = display.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export Demand Tracker CSV", csv, "demand_tracker.csv", "text/csv")
