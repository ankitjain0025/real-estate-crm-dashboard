import pandas as pd


def load_excel_data(file_path):

    overall_draft_df = pd.read_excel(
        file_path,
        sheet_name="Overall_Draft"
    )

    reports_df = pd.read_excel(
        file_path,
        sheet_name="Reporting"
    )

    return overall_draft_df, reports_df