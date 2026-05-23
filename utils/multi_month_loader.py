"""
utils/multi_month_loader.py
Loads all monthly Excel files from data/ and returns a unified
month-on-month DataFrame for trend analysis.

File naming convention:
    Overall Collection Summary - Mar 2026.xlsx
    Overall Collection Summary - Apr 2026.xlsx
    Overall Collection Summary - May 2026.xlsx
    Overall Collection Summary.xlsx   ← always the latest / current month
"""

import os
import re
import pandas as pd
import streamlit as st

DATA_DIR = "data"

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTH_NUM = {m: i+1 for i, m in enumerate(MONTH_ORDER)}


def _safe_float(val, default=0.0):
    try:
        import math
        v = float(val)
        return default if math.isnan(v) else v
    except Exception:
        return default


def _parse_one_file(path: str, month_label: str) -> dict:
    """
    Parse a single monthly Excel file and return a flat dict of all metrics.
    Returns one row per project.
    """
    xl = pd.ExcelFile(path, engine="openpyxl")

    if "Reporting" not in xl.sheet_names or "Overall_Draft" not in xl.sheet_names:
        return []

    rp = xl.parse("Reporting", header=None)
    od = xl.parse("Overall_Draft", header=None)

    # Report date
    raw_date = od.iloc[0, 8]
    if hasattr(raw_date, "strftime"):
        report_date = raw_date.strftime("%d %b %Y")
    else:
        report_date = str(raw_date)[:10]

    # Overall target from Overall_Draft row 5 col 1
    overall_target = _safe_float(od.iloc[5, 1])

    rows = []
    # Reporting: project rows 1-7 (row 8 = Overall)
    for i in range(1, 8):
        r = rp.iloc[i]
        proj_name = str(r.iloc[1]).replace("\n", " ").strip()
        if not proj_name or proj_name.lower() in ["nan", "overall"]:
            continue

        # Standardise project names (handle ANANTA vs Ananta etc.)
        proj_name = _normalise_project(proj_name)

        rows.append({
            "Month":              month_label,
            "Report_Date":        report_date,
            "Project":            proj_name,
            # Monthly target vs achievement
            "Monthly_Target_Cr":       _safe_float(r.iloc[2]),
            "Monthly_Achievement_Cr":  _safe_float(r.iloc[3]),
            "Achievement_Pct":         round(_safe_float(r.iloc[4]) * 100, 2),
            "Forecast_Cr":             _safe_float(r.iloc[5]),
            "Forecast_Gap_Cr":         _safe_float(r.iloc[6]),
            # Cumulative / till-date
            "Total_Live_Bookings":     _safe_float(r.iloc[8]),
            "Daily_Collection_Cr":     _safe_float(r.iloc[9]),
            "Monthly_Collection_Cr":   _safe_float(r.iloc[10]),
            "Monthly_Registrations":   _safe_float(r.iloc[11]),
            "Actual_Demand_Cr":        _safe_float(r.iloc[12]),
            "Collection_Cr":           _safe_float(r.iloc[13]),
            "Outstanding_Cr":          _safe_float(r.iloc[14]),
            "Pending_Reg":             int(_safe_float(r.iloc[15])),
            "Pending_Reg_GT45":        int(_safe_float(r.iloc[16])),
            "Reg_Targets":             _safe_float(r.iloc[17]),
            # Derived
            "Collection_Efficiency_Pct": round(
                _safe_float(r.iloc[13]) / _safe_float(r.iloc[12]) * 100, 2
            ) if _safe_float(r.iloc[12]) > 0 else 0.0,
            "Outstanding_Pct_Demand": round(
                _safe_float(r.iloc[14]) / _safe_float(r.iloc[12]) * 100, 2
            ) if _safe_float(r.iloc[12]) > 0 else 0.0,
        })

    return rows


def _normalise_project(name: str) -> str:
    """Standardise project name casing (ANANTA → Ananta etc.)"""
    mapping = {
        "raghav paradise":  "RAGHAV Paradise",
        "raghav parijat":   "RAGHAV Parijat",
        "raghav ananta":    "RAGHAV Ananta",
        "raghav anata":     "RAGHAV Ananta",
        "raghav vista":     "RAGHAV Vista",
        "raghav avenue":    "RAGHAV Avenue",
        "raghav utopia":    "RAGHAV Utopia",
        "raghav enclave":   "RAGHAV Enclave",
    }
    return mapping.get(name.lower(), name)


def _detect_monthly_files() -> list[tuple[str, str, str]]:
    """
    Scan data/ for monthly files.
    Returns list of (month_label, sort_key, filepath) sorted chronologically.
    Pattern: 'Overall Collection Summary - Mon YYYY.xlsx'
    """
    results = []
    pattern = re.compile(
        r"Overall Collection Summary - ([A-Za-z]+) (\d{4})\.xlsx$", re.IGNORECASE
    )

    for fname in os.listdir(DATA_DIR):
        m = pattern.match(fname)
        if m:
            mon_str  = m.group(1).capitalize()[:3]  # Mar, Apr, May…
            year_str = m.group(2)
            mon_num  = MONTH_NUM.get(mon_str, 0)
            sort_key = f"{year_str}{mon_num:02d}"
            label    = f"{mon_str} {year_str}"
            results.append((label, sort_key, os.path.join(DATA_DIR, fname)))

    results.sort(key=lambda x: x[1])
    return results


@st.cache_data(ttl=300, show_spinner=False)
def load_all_months() -> pd.DataFrame:
    """
    Load all monthly files and return a single combined DataFrame.
    Each row = one project for one month.
    """
    files = _detect_monthly_files()

    if not files:
        return pd.DataFrame()

    all_rows = []
    for label, _, path in files:
        rows = _parse_one_file(path, label)
        all_rows.extend(rows)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)

    # Add sort order
    def _sort_key(month_str):
        parts = month_str.split()
        if len(parts) == 2:
            return int(parts[1]) * 100 + MONTH_NUM.get(parts[0], 0)
        return 0

    df["_sort"] = df["Month"].apply(_sort_key)
    df = df.sort_values(["_sort", "Project"]).drop(columns=["_sort"]).reset_index(drop=True)

    return df


def get_available_months() -> list[str]:
    """Return ordered list of month labels available in data/."""
    files = _detect_monthly_files()
    return [f[0] for f in files]


def get_portfolio_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate project-level monthly data to portfolio level."""
    if df.empty:
        return pd.DataFrame()

    grp = df.groupby("Month").agg(
        Report_Date         = ("Report_Date",        "first"),
        Monthly_Target_Cr   = ("Monthly_Target_Cr",  "sum"),
        Monthly_Achievement_Cr=("Monthly_Achievement_Cr","sum"),
        Forecast_Cr         = ("Forecast_Cr",        "sum"),
        Monthly_Collection_Cr=("Monthly_Collection_Cr","sum"),
        Actual_Demand_Cr    = ("Actual_Demand_Cr",   "sum"),
        Collection_Cr       = ("Collection_Cr",      "sum"),
        Outstanding_Cr      = ("Outstanding_Cr",     "sum"),
        Pending_Reg         = ("Pending_Reg",        "sum"),
        Pending_Reg_GT45    = ("Pending_Reg_GT45",   "sum"),
        Total_Live_Bookings = ("Total_Live_Bookings","sum"),
    ).reset_index()

    grp["Achievement_Pct"] = (
        grp["Monthly_Achievement_Cr"] / grp["Monthly_Target_Cr"].replace(0, float("nan")) * 100
    ).fillna(0).round(2)

    grp["Collection_Efficiency_Pct"] = (
        grp["Collection_Cr"] / grp["Actual_Demand_Cr"].replace(0, float("nan")) * 100
    ).fillna(0).round(2)

    # Sort chronologically
    def _sk(m):
        p = m.split()
        return int(p[1]) * 100 + MONTH_NUM.get(p[0], 0) if len(p) == 2 else 0

    grp["_s"] = grp["Month"].apply(_sk)
    grp = grp.sort_values("_s").drop(columns=["_s"]).reset_index(drop=True)

    return grp
