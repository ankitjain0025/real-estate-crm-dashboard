import streamlit as st
import plotly.express as px
import pandas as pd


# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------

def create_kpi_section(df):

    numeric_df = df.select_dtypes(include='number')

    total_value = numeric_df.sum().sum()

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Records",
        len(df)
    )

    col2.metric(
        "Overall Value",
        f"₹ {round(total_value, 2):,.0f}"
    )


# ---------------------------------------------------
# PROJECT COLLECTION CHART
# ---------------------------------------------------

def project_collection_chart(df):

    numeric_df = df.select_dtypes(include='number')

    chart_data = numeric_df.sum().reset_index()

    chart_data.columns = [
        "Category",
        "Value"
    ]

    fig = px.bar(
        chart_data,
        x="Category",
        y="Value",
        title="Project Collection Analysis"
    )

    return fig


# ---------------------------------------------------
# OVERDUE CHART
# ---------------------------------------------------

def overdue_chart(df):

    numeric_df = df.select_dtypes(include='number')

    fig = px.pie(
        values=numeric_df.sum().values,
        names=numeric_df.columns,
        title="Outstanding Analysis"
    )

    return fig


# ---------------------------------------------------
# DEMAND VS COLLECTION TREND
# ---------------------------------------------------

def demand_collection_trend(df):

    numeric_df = df.select_dtypes(include='number')

    trend_data = numeric_df.sum().reset_index()

    trend_data.columns = [
        "Metric",
        "Value"
    ]

    fig = px.line(
        trend_data,
        x="Metric",
        y="Value",
        markers=True,
        title="Demand vs Collection Trend"
    )

    return fig


# ---------------------------------------------------
# TOP DEFAULTERS TABLE
# ---------------------------------------------------

def top_defaulters_table(df):

    numeric_cols = df.select_dtypes(include='number').columns

    if len(numeric_cols) == 0:
        return pd.DataFrame()

    df_copy = df.copy()

    df_copy["Total Outstanding"] = (
        df_copy[numeric_cols]
        .sum(axis=1)
    )

    top_df = df_copy.sort_values(
        by="Total Outstanding",
        ascending=False
    ).head(10)

    return top_df


# ---------------------------------------------------
# AI QUESTION ANSWER
# ---------------------------------------------------

def ask_ai_question(question, overall_df, reports_df):

    question = question.lower()

    if "total collection" in question:

        total = overall_df.select_dtypes(
            include='number'
        ).sum().sum()

        return f"Total collection value is ₹ {round(total,2):,.0f}"

    elif "records" in question:

        return f"Total records available are {len(overall_df)}"

    elif "overdue" in question:

        return "Overdue analysis available in dashboard charts."

    else:

        return "AI assistant active. More advanced CRM intelligence can be added."