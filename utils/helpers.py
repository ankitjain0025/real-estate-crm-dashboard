import pandas as pd
import numpy as np


def safe_numeric_conversion(df: pd.DataFrame) -> pd.DataFrame:
    """Convert object columns to numeric where possible."""
    converted = df.copy()
    for col in converted.columns:
        try:
            converted[col] = pd.to_numeric(converted[col], errors="ignore")
        except Exception:
            pass
    return converted


def find_column(df: pd.DataFrame, keywords: list) -> str | None:
    """Return first column name matching any keyword (case-insensitive)."""
    for col in df.columns:
        lower = str(col).lower()
        for kw in keywords:
            if kw.lower() in lower:
                return col
    return None


def safe_sum(df: pd.DataFrame, keywords: list) -> float:
    """Sum a column found by keywords."""
    col = find_column(df, keywords)
    if col:
        try:
            return pd.to_numeric(df[col], errors="coerce").fillna(0).sum()
        except Exception:
            return 0.0
    return 0.0


def format_cr(value: float) -> str:
    """Format as Indian Crore with ₹ symbol."""
    try:
        if abs(value) >= 1:
            return f"₹ {value:,.2f} Cr"
        lakh = value * 100
        return f"₹ {lakh:,.2f} L"
    except Exception:
        return "₹ 0"


def format_currency(value: float) -> str:
    """Generic INR format."""
    try:
        return f"₹ {value:,.0f}"
    except Exception:
        return "₹ 0"


def overdue_bucket(days) -> str:
    """Categorise overdue days into ageing buckets."""
    try:
        d = float(days)
        if d <= 0:
            return "Current"
        elif d <= 30:
            return "0-30 Days"
        elif d <= 60:
            return "31-60 Days"
        elif d <= 90:
            return "61-90 Days"
        else:
            return "90+ Days"
    except Exception:
        return "Unknown"


def pct_bar(value: float, total: float) -> str:
    """Return a text progress bar string."""
    try:
        pct = min(max(value / total, 0), 1) if total else 0
        filled = int(pct * 20)
        return "█" * filled + "░" * (20 - filled) + f"  {pct*100:.1f}%"
    except Exception:
        return "░" * 20 + "  0.0%"
