import pandas as pd
import numpy as np


def safe_numeric_conversion(df):
    """
    Convert possible numeric columns safely.
    """

    converted_df = df.copy()

    for col in converted_df.columns:

        try:
            converted_df[col] = pd.to_numeric(
                converted_df[col],
                errors="ignore",
            )

        except Exception:
            pass

    return converted_df


def find_column(df, keywords):
    """
    Find first matching column based on keywords.
    """

    for col in df.columns:

        lower_col = str(col).lower()

        for keyword in keywords:

            if keyword.lower() in lower_col:
                return col

    return None


def safe_sum(df, keywords):
    """
    Safely calculate sum for matching column.
    """

    column = find_column(df, keywords)

    if column:

        try:
            return pd.to_numeric(
                df[column],
                errors="coerce",
            ).fillna(0).sum()

        except Exception:
            return 0

    return 0


def format_currency(value):
    """
    Format INR values professionally.
    """

    try:
        return f"₹ {value:,.0f}"

    except Exception:
        return "₹ 0"


def overdue_bucket(days):
    """
    Categorize overdue buckets.
    """

    try:

        days = float(days)

        if days <= 30:
            return "0-30"

        elif days <= 60:
            return "31-60"

        elif days <= 90:
            return "61-90"

        else:
            return "90+"

    except Exception:
        return "Unknown"