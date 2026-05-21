"""
Page: Customer Ledger — project-level customer summary.
Note: The Excel contains project-level (not unit-level) data.
This page provides a structured project ledger view.
"""
import streamlit as st
import pandas as pd
from utils.data_loader import load_excel_data
from utils.helpers import format_cr

st.set_page_config(page_title="Customer Ledger", page_icon="👤", layout="wide")
st.markdown("## 👤 CRM Project Ledger")
st.caption("Project-level collection ledger derived from Overall Collection Summary")

EXCEL_FILE = "data/Overall Collection Summary.xlsx"

with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data(EXCEL_FILE)
    except Exception as e:
        st.error(f"Data load error: {e}")
        st.stop()

# Search / filter
col1, col2 = st.columns([2, 1])
with col1:
    search = st.text_input("🔍 Search Project", placeholder="Type project name…")
with col2:
    sort_col = st.selectbox(
        "Sort by",
        ["Outstanding (Cr)", "Actual Demand Raised (Cr)",
         "Collection Till Date (Cr)", "Pending Registrations"],
    )

df = project_df.copy()
if search:
    df = df[df["Project"].str.contains(search, case=False, na=False)]

df = df.sort_values(sort_col, ascending=False)

st.markdown("---")
st.markdown(f"**{len(df)} projects** | Sorted by: {sort_col}")

# Ledger cards
for _, row in df.iterrows():
    proj = row["Project"]
    demand = row.get("Actual Demand Raised (Cr)", 0)
    coll   = row.get("Collection Till Date (Cr)", 0)
    out    = row.get("Outstanding (Cr)", 0)
    eff    = (coll / demand * 100) if demand else 0
    pend   = int(row.get("Pending Registrations", 0))
    pend45 = int(row.get("Pending Reg > 45 Days", 0))
    live   = int(row.get("Total Live Bookings", 0))

    eff_color = "#2E7D32" if eff >= 90 else ("#E65100" if eff >= 70 else "#C62828")

    st.markdown(f"""
    <div style="background:#fff;border-radius:8px;padding:16px 20px;
                margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,0.08);
                border-left:4px solid #1A3C6E;">
        <div style="font-size:1.05rem;font-weight:700;color:#1A3C6E;margin-bottom:8px;">
            🏢 {proj}
        </div>
        <div style="display:flex;gap:32px;flex-wrap:wrap;font-size:0.88rem;">
            <div><span style="color:#777;">Live Bookings</span><br>
                 <b>{live:,}</b></div>
            <div><span style="color:#777;">Demand Raised</span><br>
                 <b>{format_cr(demand)}</b></div>
            <div><span style="color:#777;">Collection</span><br>
                 <b style="color:#2E7D32;">{format_cr(coll)}</b></div>
            <div><span style="color:#777;">Outstanding</span><br>
                 <b style="color:#C62828;">{format_cr(out)}</b></div>
            <div><span style="color:#777;">Efficiency</span><br>
                 <b style="color:{eff_color};">{eff:.1f}%</b></div>
            <div><span style="color:#777;">Pending Reg</span><br>
                 <b style="color:#E65100;">{pend}</b></div>
            <div><span style="color:#777;">Pending >45d</span><br>
                 <b style="color:#C62828;">{pend45}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Export
st.markdown("---")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export Ledger CSV", csv, "crm_ledger.csv", "text/csv")
