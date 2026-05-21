import pandas as pd
import streamlit as st


EXCEL_FILE = "data/Overall Collection Summary.xlsx"

# ---------------------------------------------------------
# SHEET NAMES (exact as in file)
# ---------------------------------------------------------
SHEET_OVERALL_DRAFT = "Overall_Draft"
SHEET_REPORTING     = "Reporting"

# ---------------------------------------------------------
# ROW / COLUMN CONSTANTS  (0-indexed, header=None)
# ---------------------------------------------------------
# Overall_Draft: project summary table
OD_PROJ_HEADER_ROW = 2
OD_PROJ_DATA_START = 3
OD_PROJ_DATA_END   = 10   # row 10 = Total (inclusive)
OD_PROJ_COL_START  = 11
OD_PROJ_COL_END    = 23   # exclusive

# Overall_Draft: KPI labels / values
OD_FORECAST_ROW    = 5    # col 1 => CRM Forecast
OD_OUTSTANDING_ROW = 5    # col 3 => Outstanding
OD_DAILY_COLL_ROW  = 5    # col 8 => Daily Collection
OD_DATE_ROW        = 0    # col 8 => report date

# Reporting: clean project table (header row 0)
RP_HEADER_ROW  = 0
RP_DATA_START  = 1
RP_DATA_END    = 8        # row 8 = Overall total (inclusive)

# Reporting column indices for project-level fields
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

# Reporting: category breakdown (cols 20-52)
RP_CAT_LABEL_COL  = 47
RP_CAT_TARGET_COL = 48
RP_CAT_ACH_COL    = 49
RP_CAT_ACH_PCT    = 50
RP_CAT_FORECAST   = 51
RP_CAT_BALANCE    = 52


# ---------------------------------------------------------
# CACHING
# ---------------------------------------------------------

@st.cache_data(ttl=300)
def load_excel_data(file_path: str = EXCEL_FILE):
    """
    Load and parse the Overall Collection Summary Excel.

    Returns
    -------
    project_df   : project-level CRM summary (7 projects + Total)
    target_df    : monthly target vs achievement by project
    category_df  : category-wise target breakdown
    kpis         : dict of high-level KPI scalars
    """
    xl = pd.ExcelFile(file_path, engine="openpyxl")

    raw_od = xl.parse(SHEET_OVERALL_DRAFT, header=None)
    raw_rp = xl.parse(SHEET_REPORTING,     header=None)

    # ---- 1. Project Summary from Reporting sheet -------------------
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

    # Separate projects vs total row
    project_df_clean = project_df[
        ~project_df["Project"].str.lower().isin(["overall", "total", "nan"])
    ].copy().reset_index(drop=True)

    totals_row = project_df[
        project_df["Project"].str.lower().isin(["overall", "total"])
    ]
    totals = totals_row.iloc[0] if len(totals_row) > 0 else None

    # ---- 2. Category-wise breakdown from Reporting ----------------
    cat_labels = []
    for i in range(RP_DATA_START, RP_DATA_END + 1):
        row = raw_rp.iloc[i]
        lbl = row.iloc[RP_CAT_LABEL_COL]
        if pd.notna(lbl) and str(lbl).strip():
            cat_labels.append({
                "Category": str(lbl).replace("\n", " ").strip(),
                "Target (Cr)":      _safe_num(row.iloc[RP_CAT_TARGET_COL]),
                "Achievement (Cr)": _safe_num(row.iloc[RP_CAT_ACH_COL]),
                "Achievement %":    _safe_num(row.iloc[RP_CAT_ACH_PCT]),
                "Forecast (Cr)":    _safe_num(row.iloc[RP_CAT_FORECAST]),
                "Balance (Cr)":     _safe_num(row.iloc[RP_CAT_BALANCE]),
            })
    category_df = pd.DataFrame(cat_labels)

    # ---- 3. Weekly Forecast from Overall_Draft --------------------
    od_wk_header_row = 52
    od_wk_data_start = 53
    od_wk_data_end   = 59
    wk_projects = []
    for c in range(12, 19):
        v = raw_od.iloc[od_wk_header_row, c]
        wk_projects.append(str(v).replace("\n", " ").strip() if pd.notna(v) else f"Col{c}")

    weekly_rows = []
    for i in range(od_wk_data_start, od_wk_data_end + 1):
        row = raw_od.iloc[i]
        week_lbl = str(row.iloc[11]).strip() if pd.notna(row.iloc[11]) else ""
        if not week_lbl:
            continue
        r = {"Week": week_lbl}
        for idx, proj in enumerate(wk_projects):
            r[proj] = _safe_num(row.iloc[12 + idx])
        weekly_rows.append(r)
    weekly_df = pd.DataFrame(weekly_rows)

    # ---- 4. KPIs --------------------------------------------------
    # Total rows
    total_demand      = _safe_num(project_df_clean["Actual Demand Raised (Cr)"].sum())
    total_collection  = _safe_num(project_df_clean["Collection Till Date (Cr)"].sum())
    total_outstanding = _safe_num(project_df_clean["Outstanding (Cr)"].sum())
    total_pend_reg    = int(project_df_clean["Pending Registrations"].sum())
    total_pend_reg_45 = int(project_df_clean["Pending Reg > 45 Days"].sum())
    total_live_bkgs   = int(project_df_clean["Total Live Bookings"].sum())
    monthly_coll      = _safe_num(project_df_clean["Monthly Collection (Cr)"].sum())
    daily_coll        = _safe_num(project_df_clean["Daily Collection (Cr)"].sum())

    # CRM Monthly Target vs Achievement from Overall_Draft row 2 col1
    crm_summary_str = str(raw_od.iloc[2, 1]) if pd.notna(raw_od.iloc[2, 1]) else ""
    # "₹ 10.99 / 38.72 (28.4%)" -> parse
    crm_monthly_ach  = totals["Collection Achievement (Cr)"] if totals is not None else 0
    crm_monthly_tgt  = totals["Collection Target (Cr)"]      if totals is not None else 0
    collection_eff   = (crm_monthly_ach / crm_monthly_tgt * 100) if crm_monthly_tgt else 0

    # Report date
    report_date = raw_od.iloc[OD_DATE_ROW, 8]
    if hasattr(report_date, "strftime"):
        report_date_str = report_date.strftime("%d %b %Y")
    else:
        report_date_str = str(report_date)

    kpis = {
        "report_date":      report_date_str,
        "total_demand":     total_demand,
        "total_collection": total_collection,
        "total_outstanding":total_outstanding,
        "collection_eff":   collection_eff,
        "monthly_coll":     monthly_coll,
        "daily_coll":       daily_coll,
        "total_live_bkgs":  total_live_bkgs,
        "pending_reg":      total_pend_reg,
        "pending_reg_45":   total_pend_reg_45,
        "crm_monthly_tgt":  crm_monthly_tgt,
        "crm_monthly_ach":  crm_monthly_ach,
    }

    return project_df_clean, category_df, weekly_df, kpis


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _safe_num(val, default=0.0):
    try:
        v = float(val)
        import math
        return default if math.isnan(v) else v
    except Exception:
        return default
