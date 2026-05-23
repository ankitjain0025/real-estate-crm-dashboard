"""
utils/data_loader.py
Loads the LATEST monthly Excel file from data/ automatically.
No hardcoded filename — picks the most recent month found.

File naming convention:
    Overall Collection Summary - Mar 2026.xlsx
    Overall Collection Summary - Apr 2026.xlsx
    Overall Collection Summary - May 2026.xlsx
    (add more months in same format — loader always picks the latest)
"""

import os
import re
import math
import pandas as pd
import streamlit as st

DATA_DIR = "data"

MONTH_NUM = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# ── File detection ─────────────────────────────────────────────────────────────

def get_latest_file() -> str | None:
    """
    Scan data/ for monthly files and return the path to the most recent one.
    Pattern matched: 'Overall Collection Summary - Mon YYYY.xlsx'
    """
    pattern = re.compile(
        r"Overall Collection Summary - ([A-Za-z]+) (\d{4})\.xlsx$",
        re.IGNORECASE,
    )
    best_key  = -1
    best_path = None

    for fname in os.listdir(DATA_DIR):
        m = pattern.match(fname)
        if not m:
            continue
        mon_str  = m.group(1).capitalize()[:3]
        year_str = int(m.group(2))
        mon_num  = MONTH_NUM.get(mon_str, 0)
        sort_key = year_str * 100 + mon_num
        if sort_key > best_key:
            best_key  = sort_key
            best_path = os.path.join(DATA_DIR, fname)

    return best_path


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_num(val, default=0.0):
    try:
        v = float(val)
        return default if math.isnan(v) else v
    except Exception:
        return default


# ── Column index constants (Reporting sheet, 0-indexed, header=None) ──────────

RP_DATA_START     = 1
RP_DATA_END       = 8    # row 8 = Overall total
RP_PROJECT        = 1
RP_TARGET         = 2
RP_ACHIEVEMENT    = 3
RP_ACHIEVEMENT_PCT= 4
RP_FORECAST       = 5
RP_FORECAST_VAR   = 6
RP_PROJ_NAME2     = 7
RP_LIVE_BOOKINGS  = 8
RP_DAILY_COLL     = 9
RP_MONTHLY_COLL   = 10
RP_MONTHLY_REG    = 11
RP_DEMAND_TILL    = 12
RP_COLL_TILL      = 13
RP_OUTSTANDING    = 14
RP_PEND_REG       = 15
RP_PEND_REG_45    = 16
RP_REG_TARGETS    = 17

RP_CAT_LABEL_COL  = 47
RP_CAT_TARGET_COL = 48
RP_CAT_ACH_COL    = 49
RP_CAT_ACH_PCT    = 50
RP_CAT_FORECAST   = 51
RP_CAT_BALANCE    = 52

OD_DATE_ROW = 0


# ── Main loader ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def load_excel_data(file_path: str | None = None):
    """
    Load and parse the latest monthly Excel file.

    Parameters
    ----------
    file_path : str | None
        If None, auto-detects the latest monthly file in data/.

    Returns
    -------
    project_df  : pd.DataFrame  — project-level CRM summary
    category_df : pd.DataFrame  — category-wise target breakdown
    weekly_df   : pd.DataFrame  — weekly forecast
    kpis        : dict          — high-level KPI scalars
    """
    # Auto-detect if no path supplied
    if file_path is None or not os.path.exists(str(file_path)):
        file_path = get_latest_file()

    if file_path is None:
        raise FileNotFoundError(
            "No monthly Excel file found in data/.\n"
            "Expected format: 'Overall Collection Summary - May 2026.xlsx'"
        )

    xl     = pd.ExcelFile(file_path, engine="openpyxl")
    raw_od = xl.parse("Overall_Draft", header=None)
    raw_rp = xl.parse("Reporting",     header=None)

    # ── 1. Project summary ────────────────────────────────────────────────────
    proj_headers = [
        "Project",
        "Collection Target (Cr)",
        "Collection Achievement (Cr)",
        "Achievement %",
        "CRM Forecast (Cr)",
        "Forecast Variance (Cr)",
        "Project Name",
        "Total Live Bookings",
        "Daily Collection (Cr)",
        "Monthly Collection (Cr)",
        "Monthly Registrations",
        "Actual Demand Raised (Cr)",
        "Collection Till Date (Cr)",
        "Outstanding (Cr)",
        "Pending Registrations",
        "Pending Reg > 45 Days",
        "Registration Targets",
    ]

    proj_rows = []
    for i in range(RP_DATA_START, RP_DATA_END + 1):
        row = raw_rp.iloc[i]
        proj_rows.append([
            str(row.iloc[RP_PROJECT]).replace("\n", " ").strip(),
            _safe_num(row.iloc[RP_TARGET]),
            _safe_num(row.iloc[RP_ACHIEVEMENT]),
            _safe_num(row.iloc[RP_ACHIEVEMENT_PCT]),
            _safe_num(row.iloc[RP_FORECAST]),
            _safe_num(row.iloc[RP_FORECAST_VAR]),
            str(row.iloc[RP_PROJ_NAME2]).replace("\n", " ").strip(),
            _safe_num(row.iloc[RP_LIVE_BOOKINGS]),
            _safe_num(row.iloc[RP_DAILY_COLL]),
            _safe_num(row.iloc[RP_MONTHLY_COLL]),
            _safe_num(row.iloc[RP_MONTHLY_REG]),
            _safe_num(row.iloc[RP_DEMAND_TILL]),
            _safe_num(row.iloc[RP_COLL_TILL]),
            _safe_num(row.iloc[RP_OUTSTANDING]),
            _safe_num(row.iloc[RP_PEND_REG]),
            _safe_num(row.iloc[RP_PEND_REG_45]),
            _safe_num(row.iloc[RP_REG_TARGETS]),
        ])

    project_df = pd.DataFrame(proj_rows, columns=proj_headers)

    # Separate project rows from totals row
    is_total = project_df["Project"].str.lower().isin(["overall", "total", "nan", ""])
    project_df_clean = project_df[~is_total].copy().reset_index(drop=True)
    totals_row       = project_df[is_total]
    totals           = totals_row.iloc[0] if len(totals_row) > 0 else None

    # ── 2. Category breakdown ─────────────────────────────────────────────────
    cat_rows = []
    for i in range(RP_DATA_START, RP_DATA_END + 1):
        row = raw_rp.iloc[i]
        lbl = row.iloc[RP_CAT_LABEL_COL]
        if pd.notna(lbl) and str(lbl).strip():
            cat_rows.append({
                "Category":        str(lbl).replace("\n", " ").strip(),
                "Target (Cr)":     _safe_num(row.iloc[RP_CAT_TARGET_COL]),
                "Achievement (Cr)":_safe_num(row.iloc[RP_CAT_ACH_COL]),
                "Achievement %":   _safe_num(row.iloc[RP_CAT_ACH_PCT]),
                "Forecast (Cr)":   _safe_num(row.iloc[RP_CAT_FORECAST]),
                "Balance (Cr)":    _safe_num(row.iloc[RP_CAT_BALANCE]),
            })
    category_df = pd.DataFrame(cat_rows)

    # ── 3. Weekly forecast ────────────────────────────────────────────────────
    wk_header_row = 52
    wk_data_start = 53
    wk_data_end   = 59
    wk_projects   = [
        str(raw_od.iloc[wk_header_row, c]).replace("\n", " ").strip()
        for c in range(12, 19)
    ]
    weekly_rows = []
    for i in range(wk_data_start, wk_data_end + 1):
        row      = raw_od.iloc[i]
        week_lbl = str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else ""
        if not week_lbl:
            continue
        r = {"Week": week_lbl}
        for idx, proj in enumerate(wk_projects):
            r[proj] = _safe_num(row.iloc[12 + idx])
        weekly_rows.append(r)
    weekly_df = pd.DataFrame(weekly_rows)

    # ── 4. KPIs ───────────────────────────────────────────────────────────────
    total_demand      = project_df_clean["Actual Demand Raised (Cr)"].sum()
    total_collection  = project_df_clean["Collection Till Date (Cr)"].sum()
    total_outstanding = project_df_clean["Outstanding (Cr)"].sum()
    total_pend_reg    = int(project_df_clean["Pending Registrations"].sum())
    total_pend_reg_45 = int(project_df_clean["Pending Reg > 45 Days"].sum())
    total_live_bkgs   = int(project_df_clean["Total Live Bookings"].sum())
    monthly_coll      = project_df_clean["Monthly Collection (Cr)"].sum()
    daily_coll        = project_df_clean["Daily Collection (Cr)"].sum()

    crm_monthly_ach = totals["Collection Achievement (Cr)"] if totals is not None else 0
    crm_monthly_tgt = totals["Collection Target (Cr)"]      if totals is not None else 0

    report_date = raw_od.iloc[OD_DATE_ROW, 8]
    report_date_str = (
        report_date.strftime("%d %b %Y")
        if hasattr(report_date, "strftime")
        else str(report_date)[:10]
    )

    # Derive month label from filename
    fname    = os.path.basename(file_path)
    m_match  = re.search(r"([A-Za-z]+)\s+(\d{4})", fname)
    month_label = (
        f"{m_match.group(1)[:3].capitalize()} {m_match.group(2)}"
        if m_match else "Current"
    )

    kpis = {
        "report_date":      report_date_str,
        "month_label":      month_label,
        "source_file":      fname,
        "total_demand":     total_demand,
        "total_collection": total_collection,
        "total_outstanding":total_outstanding,
        "monthly_coll":     monthly_coll,
        "daily_coll":       daily_coll,
        "total_live_bkgs":  total_live_bkgs,
        "pending_reg":      total_pend_reg,
        "pending_reg_45":   total_pend_reg_45,
        "crm_monthly_tgt":  crm_monthly_tgt,
        "crm_monthly_ach":  crm_monthly_ach,
        "collection_eff":   round(total_collection / total_demand * 100, 2)
                            if total_demand else 0.0,
    }

    return project_df_clean, category_df, weekly_df, kpis
