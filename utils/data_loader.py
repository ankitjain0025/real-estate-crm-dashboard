import pandas as pd
import streamlit as st


@st.cache_data
def load_excel_data(file_path):
    """
    Load CRM Excel sheets.
    """

    # Load all visible sheets
    excel_file = pd.ExcelFile(file_path)

    visible_sheets = []

    for sheet in excel_file.sheet_names:
        visible_sheets.append(sheet)

    # MAIN SHEETS
    overall_draft_df = pd.read_excel(
        file_path,
        sheet_name="Overall Draft",
    )

    reports_df = pd.read_excel(
        file_path,
        sheet_name="Reports",
    )

    # Remove completely empty rows
    overall_draft_df = overall_draft_df.dropna(how="all")
    reports_df = reports_df.dropna(how="all")

    # Clean column names
    overall_draft_df.columns = [
        str(col).strip() for col in overall_draft_df.columns
    ]

    reports_df.columns = [
        str(col).strip() for col in reports_df.columns
    ]

    return overall_draft_df, reports_df