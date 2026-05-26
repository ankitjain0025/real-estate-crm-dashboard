"""
utils/multi_month_loader.py
Loads all monthly Excel files and returns unified month-on-month DataFrame.
Includes: Spill Over Target (= Outstanding at start of month), OCR, New Bookings.
"""
import os, re, math
import pandas as pd
import streamlit as st
from utils.rm_config import get_rm

DATA_DIR   = "data"
MONTH_NUM  = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
              "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def _safe(val, default=0.0):
    try:
        v = float(val)
        return default if math.isnan(v) else v
    except: return default

def _normalise(name: str) -> str:
    """Collapse newlines + multiple spaces, then map to canonical name."""
    import re as _re
    cleaned = _re.sub(r'\s+', ' ', str(name).replace('\n', ' ')).strip()
    mapping = {
        "raghav paradise": "RAGHAV Paradise",
        "raghav parijat":  "RAGHAV Parijat",
        "raghav ananta":   "RAGHAV Ananta",
        "raghav anata":    "RAGHAV Ananta",
        "raghav vista":    "RAGHAV Vista",
        "raghav avenue":   "RAGHAV Avenue",
        "raghav utopia":   "RAGHAV Utopia",
        "raghav enclave":  "RAGHAV Enclave",
    }
    return mapping.get(cleaned.lower(), cleaned)

def _detect_files():
    pat = re.compile(r"Overall Collection Summary - ([A-Za-z]+) (\d{4})\.xlsx$", re.I)
    results = []
    for fname in os.listdir(DATA_DIR):
        m = pat.match(fname)
        if not m: continue
        mon = m.group(1).capitalize()[:3]
        yr  = int(m.group(2))
        key = yr * 100 + MONTH_NUM.get(mon, 0)
        results.append((f"{mon} {yr}", key, os.path.join(DATA_DIR, fname)))
    return sorted(results, key=lambda x: x[1])

def _parse_file(path, label):
    xl = pd.ExcelFile(path, engine="openpyxl")
    if "Reporting" not in xl.sheet_names: return []
    rp = xl.parse("Reporting", header=None)
    od = xl.parse("Overall_Draft", header=None) if "Overall_Draft" in xl.sheet_names else None

    raw_date = od.iloc[0,8] if od is not None else None
    report_date = raw_date.strftime("%d %b %Y") if hasattr(raw_date,"strftime") else str(raw_date)[:10]

    rows = []
    for i in range(1, 8):
        r    = rp.iloc[i]
        proj = _normalise(str(r.iloc[1]))
        if not proj or proj.lower() in ["nan","overall",""]: continue
        demand = _safe(r.iloc[12])
        coll   = _safe(r.iloc[13])
        rows.append({
            "Month":                      label,
            "Report_Date":                report_date,
            "Project":                    proj,
            "RM":                         get_rm(proj),
            # Monthly target / achievement
            "Monthly_Target_Cr":          _safe(r.iloc[2]),
            "Monthly_Achievement_Cr":     _safe(r.iloc[3]),
            "Achievement_Pct":            round(_safe(r.iloc[4])*100, 2),
            "Forecast_Cr":                _safe(r.iloc[5]),
            "Forecast_Gap_Cr":            _safe(r.iloc[6]),
            # Cumulative
            "Total_Live_Bookings":        _safe(r.iloc[8]),
            "Daily_Collection_Cr":        _safe(r.iloc[9]),
            "Monthly_Collection_Cr":      _safe(r.iloc[10]),
            "Monthly_Registrations":      _safe(r.iloc[11]),
            "Actual_Demand_Cr":           demand,
            "Collection_Cr":              coll,
            "Outstanding_Cr":             _safe(r.iloc[14]),
            "Pending_Reg":                int(_safe(r.iloc[15])),
            "Pending_Reg_GT45":           int(_safe(r.iloc[16])),
            "Reg_Targets":                _safe(r.iloc[17]),
            # Spill Over = Outstanding at START of month (CRM team responsible)
            "SpillOver_Target_Cr":        _safe(r.iloc[21]),
            "SpillOver_Achievement_Cr":   _safe(r.iloc[22]),
            "SpillOver_Ach_Pct":          round(_safe(r.iloc[23])*100, 2),
            # OCR = Own Contribution Unregistered (CRM reports, Sales collects)
            "OCR_Target_Cr":              _safe(r.iloc[25]),
            "OCR_Achievement_Cr":         _safe(r.iloc[26]),
            "OCR_Ach_Pct":                round(_safe(r.iloc[27])*100, 2),
            # New Bookings = OCR New Bookings (Sales team responsible)
            "NewBooking_Target_Cr":       _safe(r.iloc[29]),
            "NewBooking_Achievement_Cr":  _safe(r.iloc[30]),
            "NewBooking_Ach_Pct":         round(_safe(r.iloc[31])*100, 2),
            # Derived
            "Collection_Efficiency_Pct":  round(coll/demand*100,2) if demand else 0.0,
            "Outstanding_Pct_Demand":     round(_safe(r.iloc[14])/demand*100,2) if demand else 0.0,
        })
    return rows

@st.cache_data(ttl=300, show_spinner=False)
def load_all_months() -> pd.DataFrame:
    files = _detect_files()
    if not files: return pd.DataFrame()
    all_rows = []
    for label, _, path in files:
        all_rows.extend(_parse_file(path, label))
    if not all_rows: return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    def _sk(m):
        p = m.split()
        return int(p[1])*100 + MONTH_NUM.get(p[0],0) if len(p)==2 else 0
    df["_s"] = df["Month"].apply(_sk)
    return df.sort_values(["_s","Project"]).drop(columns=["_s"]).reset_index(drop=True)

def get_available_months():
    return [f[0] for f in _detect_files()]

def get_portfolio_monthly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    grp = df.groupby("Month").agg(
        Report_Date            =("Report_Date","first"),
        Monthly_Target_Cr      =("Monthly_Target_Cr","sum"),
        Monthly_Achievement_Cr =("Monthly_Achievement_Cr","sum"),
        Forecast_Cr            =("Forecast_Cr","sum"),
        Monthly_Collection_Cr  =("Monthly_Collection_Cr","sum"),
        Actual_Demand_Cr       =("Actual_Demand_Cr","sum"),
        Collection_Cr          =("Collection_Cr","sum"),
        Outstanding_Cr         =("Outstanding_Cr","sum"),
        Pending_Reg            =("Pending_Reg","sum"),
        Pending_Reg_GT45       =("Pending_Reg_GT45","sum"),
        Total_Live_Bookings    =("Total_Live_Bookings","sum"),
        SpillOver_Target_Cr    =("SpillOver_Target_Cr","sum"),
        SpillOver_Achievement_Cr=("SpillOver_Achievement_Cr","sum"),
        OCR_Target_Cr          =("OCR_Target_Cr","sum"),
        OCR_Achievement_Cr     =("OCR_Achievement_Cr","sum"),
        NewBooking_Target_Cr   =("NewBooking_Target_Cr","sum"),
        NewBooking_Achievement_Cr=("NewBooking_Achievement_Cr","sum"),
    ).reset_index()
    grp["Achievement_Pct"] = (grp["Monthly_Achievement_Cr"]/grp["Monthly_Target_Cr"].replace(0,float("nan"))*100).fillna(0).round(2)
    grp["Collection_Efficiency_Pct"] = (grp["Collection_Cr"]/grp["Actual_Demand_Cr"].replace(0,float("nan"))*100).fillna(0).round(2)
    def _sk(m):
        p=m.split(); return int(p[1])*100+MONTH_NUM.get(p[0],0) if len(p)==2 else 0
    grp["_s"]=grp["Month"].apply(_sk)
    return grp.sort_values("_s").drop(columns=["_s"]).reset_index(drop=True)
