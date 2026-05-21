import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_excel_data
from utils.dashboard import (
    create_kpi_section,
    project_collection_chart,
    overdue_chart,
    demand_collection_trend,
    top_defaulters_table,
)
from utils.qa_engine import ask_gemini
from utils.helpers import safe_numeric_conversion

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Real Estate CRM Dashboard",
    page_icon="🏢",
    layout="wide",
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("🏢 Real Estate CRM Collection Dashboard")
st.markdown("Mumbai Real Estate CRM MIS Dashboard")

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

EXCEL_FILE = "data/Overall Collection Summary.xlsx"

try:
    with st.spinner("Loading CRM data..."):
        overall_draft_df, reports_df = load_excel_data(EXCEL_FILE)

except Exception as e:
    st.error(f"Error loading Excel file: {e}")
    st.stop()

# ---------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------

overall_draft_df = safe_numeric_conversion(overall_draft_df)

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------

st.sidebar.header("Filters")

project_column = None
customer_column = None
wing_column = None

for col in overall_draft_df.columns:
    lower_col = col.lower()

    if "project" in lower_col and project_column is None:
        project_column = col

    if "customer" in lower_col and customer_column is None:
        customer_column = col

    if "wing" in lower_col and wing_column is None:
        wing_column = col

filtered_df = overall_draft_df.copy()

# PROJECT FILTER
if project_column:
    project_options = sorted(
        filtered_df[project_column].dropna().astype(str).unique()
    )

    selected_projects = st.sidebar.multiselect(
        "Select Project",
        options=project_options,
        default=project_options,
    )

    filtered_df = filtered_df[
        filtered_df[project_column].astype(str).isin(selected_projects)
    ]

# WING FILTER
if wing_column:
    wing_options = sorted(
        filtered_df[wing_column].dropna().astype(str).unique()
    )

    selected_wings = st.sidebar.multiselect(
        "Select Wing",
        options=wing_options,
        default=wing_options,
    )

    filtered_df = filtered_df[
        filtered_df[wing_column].astype(str).isin(selected_wings)
    ]

# CUSTOMER FILTER
if customer_column:
    customer_search = st.sidebar.text_input("Search Customer")

    if customer_search:
        filtered_df = filtered_df[
            filtered_df[customer_column]
            .astype(str)
            .str.contains(customer_search, case=False, na=False)
        ]

# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------

st.markdown("## Collection Summary")

create_kpi_section(filtered_df)

# ---------------------------------------------------
# CHARTS
# ---------------------------------------------------

st.markdown("---")
st.markdown("## Project Wise Collection Analysis")

try:
    fig_project = project_collection_chart(filtered_df)
    st.plotly_chart(fig_project, width='stretch')
except Exception as e:
    st.warning(f"Project chart unavailable: {e}")

# ---------------------------------------------------

st.markdown("---")
st.markdown("## Overdue Analysis")

try:
    fig_overdue = overdue_chart(filtered_df)
    st.plotly_chart(fig_overdue, width='stretch')
except Exception as e:
    st.warning(f"Overdue chart unavailable: {e}")

# ---------------------------------------------------

st.markdown("---")
st.markdown("## Demand vs Collection Trend")

try:
    fig_trend = demand_collection_trend(filtered_df)
    st.plotly_chart(fig_trend, width='stretch')
except Exception as e:
    st.warning(f"Trend chart unavailable: {e}")

# ---------------------------------------------------

st.markdown("---")
st.markdown("## Top Defaulters")

try:
    top_defaulters = top_defaulters_table(filtered_df)
    st.dataframe(top_defaulters, width='stretch')
except Exception as e:
    st.warning(f"Defaulters table unavailable: {e}")

# ---------------------------------------------------
# DATA TABLE
# ---------------------------------------------------

st.markdown("---")
st.markdown("## CRM Data")

st.dataframe(filtered_df, width='stretch')

# ---------------------------------------------------
# EXPORT CSV
# ---------------------------------------------------

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name="filtered_crm_data.csv",
    mime="text/csv",
)

# ---------------------------------------------------
# GEMINI AI Q&A SECTION
# ---------------------------------------------------

st.markdown("---")
st.markdown("# 🤖 AI CRM Q&A")

st.markdown(
    """
Ask questions like:
- Which customers have highest overdue?
- Show top defaulters
- Collection project wise
- Which units have pending interest?
"""
)

user_question = st.text_area(
    "Ask a question about CRM data",
    height=120,
)

if st.button("Get Answer"):

    if not user_question.strip():
        st.warning("Please enter a question.")

    else:
        try:
            with st.spinner("Analyzing CRM data using Gemini..."):

                response = ask_gemini(
                    question=user_question,
                    dataframe=filtered_df,
                )

            st.success("Answer Generated")

            st.markdown(response)

        except Exception as e:
            st.error(f"Error generating answer: {e}")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")
st.caption("Real Estate CRM Dashboard | Powered by Streamlit + Gemini AI")