"""
utils/data_loader.py
Auto-detects latest monthly Excel, normalises all project names
(collapses newlines + double spaces), adds SpillOver_Target_Cr column.
"""
import os, re, math
import pandas as pd
import streamlit as st

DATA_DIR  = "data"
MONTH_NUM = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
             "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def _safe(val, default=0.0):
    try:
        v = float(val)
        return default if math.isnan(v) else v
    except: return default

def _clean(name):
    """Normalise project name: strip newlines, collapse multiple spaces."""
    return re.sub(r'\s+', ' ', str(name).replace('\n',' ')).strip()

def get_latest_file():
    pat = re.compile(r"Overall Collection Summary - ([A-Za-z]+) (\d{4})\.xlsx$", re.I)
    best_key, best_path = -1, None
    for fname in os.listdir(DATA_DIR):
        m = pat.match(fname)
        if not m: continue
        mon = m.group(1).capitalize()[:3]
        yr  = int(m.group(2))
        key = yr * 100 + MONTH_NUM.get(mon, 0)
        if key > best_key:
            best_key, best_path = key, os.path.join(DATA_DIR, fname)
    return best_path

@st.cache_data(ttl=300, show_spinner=False)
def load_excel_data(file_path=None):
    if file_path is None or not os.path.exists(str(file_path)):
        file_path = get_latest_file()
    if file_path is None:
        raise FileNotFoundError(
            "No monthly Excel file found in data/.\n"
            "Expected: 'Overall Collection Summary - May 2026.xlsx'")

    xl     = pd.ExcelFile(file_path, engine="openpyxl")
    raw_od = xl.parse("Overall_Draft", header=None)
    raw_rp = xl.parse("Reporting",     header=None)

    # ── Project rows (Reporting sheet rows 1-7, row 8 = Overall) ─────────────
    proj_rows = []
    for i in range(1, 9):
        r = raw_rp.iloc[i]
        proj_name = _clean(r.iloc[1])
        if not proj_name or proj_name.lower() in ["nan","overall",""]:
            continue
        demand = _safe(r.iloc[12])
        coll   = _safe(r.iloc[13])
        proj_rows.append({
            "Project":                    proj_name,
            "Collection Target (Cr)":     _safe(r.iloc[2]),
            "Collection Achievement (Cr)":_safe(r.iloc[3]),
            "Achievement %":              _safe(r.iloc[4]),
            "CRM Forecast (Cr)":          _safe(r.iloc[5]),
            "Total Live Bookings":        _safe(r.iloc[8]),
            "Daily Collection (Cr)":      _safe(r.iloc[9]),
            "Monthly Collection (Cr)":    _safe(r.iloc[10]),
            "Monthly Registrations":      _safe(r.iloc[11]),
            "Actual Demand Raised (Cr)":  demand,
            "Collection Till Date (Cr)":  coll,
            "Outstanding (Cr)":           _safe(r.iloc[14]),
            "Pending Registrations":      _safe(r.iloc[15]),
            "Pending Reg > 45 Days":      _safe(r.iloc[16]),
            "Registration Targets":       _safe(r.iloc[17]),
            # SpillOver Target = Outstanding at start of this month
            "SpillOver_Target_Cr":        _safe(r.iloc[21]),
            "SpillOver_Achievement_Cr":   _safe(r.iloc[22]),
            "OCR_Target_Cr":              _safe(r.iloc[25]),
            "OCR_Achievement_Cr":         _safe(r.iloc[26]),
            "NewBooking_Target_Cr":       _safe(r.iloc[29]),
            "NewBooking_Achievement_Cr":  _safe(r.iloc[30]),
        })

    project_df = pd.DataFrame(proj_rows)
    is_total   = project_df["Project"].str.lower().isin(["overall","total","nan",""])
    project_df = project_df[~is_total].reset_index(drop=True)

    # ── Category breakdown (Reporting sheet cols 47-52) ───────────────────────
    cat_rows = []
    for i in range(1, 9):
        r   = raw_rp.iloc[i]
        lbl = r.iloc[47]
        if pd.notna(lbl) and str(lbl).strip():
            cat_rows.append({
                "Category":         _clean(lbl),
                "Target (Cr)":      _safe(r.iloc[48]),
                "Achievement (Cr)": _safe(r.iloc[49]),
                "Achievement %":    _safe(r.iloc[50]),
                "Forecast (Cr)":    _safe(r.iloc[51]),
                "Balance (Cr)":     _safe(r.iloc[52]),
            })
    category_df = pd.DataFrame(cat_rows)

    # ── Weekly forecast (Overall_Draft rows 52-59) ────────────────────────────
    wk_projects = [_clean(raw_od.iloc[52, c]) for c in range(12, 19)]
    weekly_rows = []
    for i in range(53, 60):
        row  = raw_od.iloc[i]
        week = _clean(row.iloc[11])
        if not week: continue
        r = {"Week": week}
        for idx, proj in enumerate(wk_projects):
            r[proj] = _safe(row.iloc[12+idx])
        weekly_rows.append(r)
    weekly_df = pd.DataFrame(weekly_rows)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_demand      = project_df["Actual Demand Raised (Cr)"].sum()
    total_collection  = project_df["Collection Till Date (Cr)"].sum()
    total_outstanding = project_df["Outstanding (Cr)"].sum()

    raw_date    = raw_od.iloc[0, 8]
    report_date = raw_date.strftime("%d %b %Y") if hasattr(raw_date,"strftime") else str(raw_date)[:10]

    fname = os.path.basename(file_path)
    m_match = re.search(r"([A-Za-z]+)\s+(\d{4})", fname)
    month_label = f"{m_match.group(1)[:3].capitalize()} {m_match.group(2)}" if m_match else "Current"

    kpis = {
        "report_date":       report_date,
        "month_label":       month_label,
        "source_file":       fname,
        "total_demand":      total_demand,
        "total_collection":  total_collection,
        "total_outstanding": total_outstanding,
        "monthly_coll":      project_df["Monthly Collection (Cr)"].sum(),
        "daily_coll":        project_df["Daily Collection (Cr)"].sum(),
        "total_live_bkgs":   int(project_df["Total Live Bookings"].sum()),
        "pending_reg":       int(project_df["Pending Registrations"].sum()),
        "pending_reg_45":    int(project_df["Pending Reg > 45 Days"].sum()),
        "crm_monthly_tgt":   project_df["Collection Target (Cr)"].sum(),
        "crm_monthly_ach":   project_df["Collection Achievement (Cr)"].sum(),
        "spillover_total":   project_df["SpillOver_Target_Cr"].sum(),
        "collection_eff":    round(total_collection/total_demand*100,2) if total_demand else 0.0,
    }
    return project_df, category_df, weekly_df, kpis
