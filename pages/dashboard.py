"""
Page: Project Dashboard — detailed project comparison.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(page_title="Project Dashboard", page_icon="🏗️", layout="wide")
st.markdown("## 🏗️ Detailed Project Dashboard")

EXCEL_FILE = "data/Overall Collection Summary.xlsx"

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data(EXCEL_FILE)
    except Exception as e:
        st.error(f"Data load error: {e}")
        st.stop()

# Project selector
projects = sorted(project_df["Project"].unique().tolist())
sel = st.selectbox("Select Project", ["All Projects"] + projects)

df = project_df if sel == "All Projects" else project_df[project_df["Project"] == sel]

# KPI row
cols = st.columns(4)
cols[0].metric("Demand Raised", format_cr(df["Actual Demand Raised (Cr)"].sum()))
cols[1].metric("Collection", format_cr(df["Collection Till Date (Cr)"].sum()))
cols[2].metric("Outstanding", format_cr(df["Outstanding (Cr)"].sum()))
eff = df["Collection Till Date (Cr)"].sum() / df["Actual Demand Raised (Cr)"].sum() * 100 \
    if df["Actual Demand Raised (Cr)"].sum() > 0 else 0
cols[3].metric("Collection Efficiency", f"{eff:.1f}%")

st.markdown("---")

# Scatter: demand vs collection
fig = px.scatter(
    project_df,
    x="Actual Demand Raised (Cr)",
    y="Collection Till Date (Cr)",
    size="Total Live Bookings",
    color="Project",
    title="Demand vs Collection (Bubble = Live Bookings)",
    labels={
        "Actual Demand Raised (Cr)": "Demand (Cr)",
        "Collection Till Date (Cr)": "Collection (Cr)",
    },
    hover_data=["Outstanding (Cr)", "Pending Registrations"],
)
fig.update_layout(template="plotly_white", height=450)
st.plotly_chart(fig, use_container_width=True)

# Full data table
st.markdown("### Project Data Table")
display_cols = [c for c in [
    "Project", "Total Live Bookings",
    "Actual Demand Raised (Cr)", "Collection Till Date (Cr)", "Outstanding (Cr)",
    "Monthly Collection (Cr)", "Collection Target (Cr)", "Collection Achievement (Cr)",
    "Pending Registrations", "Pending Reg > 45 Days",
] if c in project_df.columns]

st.dataframe(project_df[display_cols], use_container_width=True)
