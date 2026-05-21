import streamlit as st
import plotly.express as px

def show_kpis(df):
    st.subheader("CRM Collection Summary")

    total_demand = df.select_dtypes(include='number').sum().sum()

    col1, col2 = st.columns(2)

    col1.metric("Total Records", len(df))
    col2.metric("Overall Value", f"₹ {round(total_demand,2):,.0f}")

def show_project_analysis(df):
    st.subheader("Project Analysis")

    numeric_cols = df.select_dtypes(include='number').columns

    if len(numeric_cols) > 0:
        chart_data = df[numeric_cols].sum().reset_index()
        chart_data.columns = ["Category", "Value"]

        fig = px.bar(
            chart_data,
            x="Category",
            y="Value"
        )

        st.plotly_chart(fig, width='stretch')

def show_overdue_analysis(df):
    st.subheader("Overdue Analysis")

    numeric_cols = df.select_dtypes(include='number').columns

    if len(numeric_cols) > 0:
        fig = px.pie(
            values=df[numeric_cols].sum().values,
            names=numeric_cols
        )

        st.plotly_chart(fig, width='stretch')

def show_collection_trends(df):
    st.subheader("Collection Trends")

    numeric_cols = df.select_dtypes(include='number').columns

    if len(numeric_cols) > 0:
        trend_data = df[numeric_cols].sum().reset_index()
        trend_data.columns = ["Metric", "Value"]

        fig = px.line(
            trend_data,
            x="Metric",
            y="Value"
        )

        st.plotly_chart(fig, width='stretch')