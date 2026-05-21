import streamlit as st
import plotly.express as px
import pandas as pd


def create_kpi_section(overall_df):

    st.subheader("CRM Dashboard Summary")

    numeric_cols = overall_df.select_dtypes(include='number')

    total_value = numeric_cols.sum().sum()

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Records",
        len(overall_df)
    )

    col2.metric(
        "Overall Collection Value",
        f"₹ {round(total_value, 2):,.0f}"
    )


def project_collection_chart(overall_df):

    st.subheader("Project Collection Analysis")

    numeric_cols = overall_df.select_dtypes(include='number')

    if len(numeric_cols.columns) > 0:

        chart_data = numeric_cols.sum().reset_index()

        chart_data.columns = [
            "Category",
            "Value"
        ]

        fig = px.bar(
            chart_data,
            x="Category",
            y="Value"
        )

        st.plotly_chart(
            fig,
            width='stretch'
        )


def overdue_chart(overall_df):

    st.subheader("Outstanding / Overdue Analysis")

    numeric_cols = overall_df.select_dtypes(include='number')

    if len(numeric_cols.columns) > 0:

        fig = px.pie(
            values=numeric_cols.sum().values,
            names=numeric_cols.columns
        )

        st.plotly_chart(
            fig,
            width='stretch'
        )


def monthly_trend_chart(reports_df):

    st.subheader("Monthly Collection Trends")

    numeric_cols = reports_df.select_dtypes(include='number')

    if len(numeric_cols.columns) > 0:

        trend_data = numeric_cols.sum().reset_index()

        trend_data.columns = [
            "Metric",
            "Value"
        ]

        fig = px.line(
            trend_data,
            x="Metric",
            y="Value"
        )

        st.plotly_chart(
            fig,
            width='stretch'
        )


def ask_ai_question(question, overall_df, reports_df):

    question = question.lower()

    if "total collection" in question:
        total = overall_df.select_dtypes(include='number').sum().sum()
        return f"Total collection related numeric value is ₹ {round(total,2):,.0f}"

    elif "records" in question:
        return f"Total records available are {len(overall_df)}"

    elif "overdue" in question:
        return "Overdue analysis is available in dashboard charts."

    else:
        return "AI assistant is active. Detailed project-specific intelligence can be enhanced further."