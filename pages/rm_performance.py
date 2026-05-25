"""
Page: RM Performance Dashboard
Edit RM assignments in utils/rm_config.py
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils.data_loader import load_excel_data
from utils.multi_month_loader import load_all_months
from utils.rm_config import RM_MAP, RM_COLORS, all_rms
from utils.helpers import format_cr

st.set_page_config(page_title="RM Performance", page_icon="👤", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#1A3C6E 0%,#0D4A8A 100%);
            color:#fff;padding:20px 28px;border-radius:10px;margin-bottom:18px;">
  <div style="font-size:1.5rem;font-weight:700;">👤 Relationship Manager Performance Dashboard</div>
  <div style="font-size:0.83rem;color:#90CAF9;margin-top:4px;">
    RM accountability: Demand dispatch · Customer follow-up · Collection
    &nbsp;|&nbsp; Edit assignments in <code>utils/rm_config.py</code>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading…"):
    try:
        project_df, category_df, weekly_df, kpis = load_excel_data()
        mom_df = load_all_months()
    except Exception as e:
        st.error(f"Data load error: {e}"); st.stop()

# Attach RM
def _get_rm(p):
    for k, v in RM_MAP.items():
        if k.lower() in p.lower() or p.lower() in k.lower():
            return v
    return "Unassigned"

project_df["RM"] = project_df["Project"].apply(_get_rm)
project_df["Collection_Eff_Pct"] = (
    project_df["Collection Till Date (Cr)"] / project_df["Actual Demand Raised (Cr)"] * 100
).fillna(0).round(1)
project_df["Achievement_Pct_Disp"] = (project_df["Achievement %"] * 100).round(1)

rms = all_rms()

# ── RM Cards ───────────────────────────────────────────────────────────────────
st.markdown("### 🏆 RM Performance Cards — Current Month")
cols = st.columns(len(rms))
for col, rm in zip(cols, rms):
    d = project_df[project_df["RM"] == rm]
    if d.empty:
        col.info(f"{rm}\nNo data"); continue
    demand  = d["Actual Demand Raised (Cr)"].sum()
    coll    = d["Collection Till Date (Cr)"].sum()
    out     = d["Outstanding (Cr)"].sum()
    monthly = d["Monthly Collection (Cr)"].sum()
    tgt     = d["Collection Target (Cr)"].sum()
    ach     = d["Collection Achievement (Cr)"].sum()
    eff     = round(coll/demand*100,1) if demand else 0
    ach_pct = round(ach/tgt*100,1) if tgt else 0
    pend    = int(d["Pending Registrations"].sum())
    p45     = int(d["Pending Reg > 45 Days"].sum())
    proj_list = " · ".join(d["Project"].str.replace("RAGHAV ","").tolist())
    color   = RM_COLORS.get(rm,"#1A3C6E")
    ec      = "#2E7D32" if eff>=90 else ("#E65100" if eff>=70 else "#C62828")
    ac      = "#2E7D32" if ach_pct>=90 else ("#E65100" if ach_pct>=60 else "#C62828")
    col.markdown(f"""
<div style="background:linear-gradient(160deg,#fff 0%,#f8f9fa 100%);
     border-top:5px solid {color};border-radius:10px;padding:16px 14px;
     box-shadow:0 4px 14px rgba(0,0,0,0.10);margin-bottom:6px;">
  <div style="font-size:1rem;font-weight:700;color:{color};">{rm}</div>
  <div style="font-size:0.68rem;color:#999;margin-bottom:10px;">{proj_list}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.76rem;">
    <div style="background:#EEF2FF;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.62rem;font-weight:600;text-transform:uppercase;">Demand</div>
      <b style="color:#1A3C6E;">₹{demand:.2f} Cr</b></div>
    <div style="background:#E8F5E9;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.62rem;font-weight:600;text-transform:uppercase;">Collection</div>
      <b style="color:#2E7D32;">₹{coll:.2f} Cr</b></div>
    <div style="background:#FFEBEE;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.62rem;font-weight:600;text-transform:uppercase;">Outstanding</div>
      <b style="color:#C62828;">₹{out:.2f} Cr</b></div>
    <div style="background:#FFF8E1;border-radius:6px;padding:6px 8px;">
      <div style="color:#777;font-size:0.62rem;font-weight:600;text-transform:uppercase;">Monthly Ach</div>
      <b style="color:#E65100;">₹{monthly:.2f} Cr</b></div>
  </div>
  <div style="margin-top:10px;">
    <div style="font-size:0.68rem;color:#888;">Coll. Efficiency:
      <b style="color:{ec}">{eff:.1f}%</b></div>
    <div style="background:#e0e0e0;border-radius:4px;height:6px;margin:3px 0 8px;">
      <div style="background:{ec};width:{min(eff,100):.0f}%;height:6px;border-radius:4px;"></div></div>
    <div style="font-size:0.68rem;color:#888;">Monthly Target Ach:
      <b style="color:{ac}">{ach_pct:.1f}%</b></div>
    <div style="background:#e0e0e0;border-radius:4px;height:6px;margin:3px 0 8px;">
      <div style="background:{ac};width:{min(ach_pct,100):.0f}%;height:6px;border-radius:4px;"></div></div>
    <div style="font-size:0.68rem;color:#888;">
      Pending Reg: <b style="color:#E65100">{pend}</b>
      &nbsp;|&nbsp; >45d: <b style="color:#C62828">{p45}</b></div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ── RM Summary aggregation ────────────────────────────────────────────────────
rm_summary = project_df.groupby("RM").agg(
    Demand  =("Actual Demand Raised (Cr)","sum"),
    Coll    =("Collection Till Date (Cr)","sum"),
    Out     =("Outstanding (Cr)","sum"),
    Monthly =("Monthly Collection (Cr)","sum"),
    Target  =("Collection Target (Cr)","sum"),
    Ach     =("Collection Achievement (Cr)","sum"),
    PendReg =("Pending Registrations","sum"),
    Pend45  =("Pending Reg > 45 Days","sum"),
).reset_index()
rm_summary["Eff_Pct"] = (rm_summary["Coll"]/rm_summary["Demand"]*100).round(1)
rm_summary["Ach_Pct"] = (rm_summary["Ach"]/rm_summary["Target"].replace(0,float("nan"))*100).fillna(0).round(1)

# ── Charts ─────────────────────────────────────────────────────────────────────
st.markdown("### 📊 RM Head-to-Head Comparison — Current Month")
c1, c2 = st.columns(2)

with c1:
    fig = go.Figure()
    fig.add_bar(name="Demand", x=rm_summary["RM"], y=rm_summary["Demand"],
        marker_color="#90CAF9", text=[f"₹{v:.2f}" for v in rm_summary["Demand"]], textposition="outside")
    fig.add_bar(name="Collection", x=rm_summary["RM"], y=rm_summary["Coll"],
        marker_color="#A5D6A7", text=[f"₹{v:.2f}" for v in rm_summary["Coll"]], textposition="outside")
    fig.add_bar(name="Outstanding", x=rm_summary["RM"], y=rm_summary["Out"],
        marker_color="#EF9A9A", text=[f"₹{v:.2f}" for v in rm_summary["Out"]], textposition="outside")
    fig.update_layout(barmode="group", template="plotly_white", height=420,
        title="<b>RM: Demand vs Collection vs Outstanding</b> (₹ Cr)",
        legend=dict(orientation="h", y=1.08), margin=dict(t=70, b=50))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    eff_colors = ["#2E7D32" if v>=90 else ("#E65100" if v>=70 else "#C62828") for v in rm_summary["Eff_Pct"]]
    fig2 = go.Figure(go.Bar(
        x=rm_summary["Eff_Pct"], y=rm_summary["RM"], orientation="h",
        marker_color=eff_colors,
        text=[f"{v:.1f}%" for v in rm_summary["Eff_Pct"]], textposition="outside"))
    fig2.add_vline(x=90, line_dash="dash", line_color="#2E7D32", annotation_text="90% target")
    fig2.update_layout(template="plotly_white", height=420,
        title="<b>RM Collection Efficiency %</b>",
        xaxis=dict(range=[0,115], ticksuffix="%"),
        margin=dict(l=150, t=70, b=50), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    ach_colors = ["#2E7D32" if v>=90 else ("#E65100" if v>=60 else "#C62828") for v in rm_summary["Ach_Pct"]]
    fig3 = go.Figure()
    fig3.add_bar(name="Monthly Target", x=rm_summary["RM"], y=rm_summary["Target"],
        marker_color="#B0BEC5", text=[f"₹{v:.2f}" for v in rm_summary["Target"]], textposition="outside")
    fig3.add_bar(name="Monthly Achievement", x=rm_summary["RM"], y=rm_summary["Ach"],
        marker_color=ach_colors,
        text=[f"₹{v:.1f}({p:.0f}%)" for v,p in zip(rm_summary["Ach"],rm_summary["Ach_Pct"])],
        textposition="outside")
    fig3.update_layout(barmode="group", template="plotly_white", height=420,
        title="<b>RM Monthly Target vs Achievement</b> (₹ Cr)",
        legend=dict(orientation="h", y=1.08), margin=dict(t=70, b=50))
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    fig4 = go.Figure()
    fig4.add_bar(name="Total Pending", x=rm_summary["RM"], y=rm_summary["PendReg"],
        marker_color="#FFB74D", text=rm_summary["PendReg"].astype(int), textposition="outside")
    fig4.add_bar(name="Critical >45 Days", x=rm_summary["RM"], y=rm_summary["Pend45"],
        marker_color="#C62828", text=rm_summary["Pend45"].astype(int), textposition="outside")
    fig4.update_layout(barmode="overlay", template="plotly_white", height=420,
        title="<b>RM Pending Registration Aging</b>", yaxis_title="Count",
        legend=dict(orientation="h", y=1.08), margin=dict(t=70, b=50))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── MoM RM trend ──────────────────────────────────────────────────────────────
if not mom_df.empty and "RM" in mom_df.columns:
    st.markdown("### 📈 RM Month-on-Month Collection Trend")
    MN={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
        "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    def _sk(m):
        p=m.split(); return int(p[1])*100+MN.get(p[0],0) if len(p)==2 else 0
    months=sorted(mom_df["Month"].unique().tolist(),key=_sk)

    rm_mom = mom_df.groupby(["Month","RM"]).agg(
        Monthly_Achievement_Cr=("Monthly_Achievement_Cr","sum"),
        Collection_Efficiency_Pct=("Collection_Efficiency_Pct","mean"),
        Outstanding_Cr=("Outstanding_Cr","sum"),
        Achievement_Pct=("Achievement_Pct","mean"),
    ).reset_index()

    mc1, mc2 = st.columns(2)
    with mc1:
        fig5 = go.Figure()
        for rm in rms:
            d = rm_mom[rm_mom["RM"]==rm].set_index("Month").reindex(months).reset_index()
            fig5.add_scatter(x=d["Month"], y=d["Monthly_Achievement_Cr"],
                mode="lines+markers+text", name=rm,
                line=dict(color=RM_COLORS.get(rm,"#1A3C6E"), width=2.5),
                marker=dict(size=8),
                text=[f"₹{v:.1f}" if pd.notna(v) else "" for v in d["Monthly_Achievement_Cr"]],
                textposition="top center", connectgaps=True)
        fig5.update_layout(template="plotly_white", height=420,
            title="<b>RM Monthly Collection Achievement</b> (₹ Cr) — MoM",
            xaxis=dict(categoryorder="array", categoryarray=months),
            yaxis_title="₹ Cr", legend=dict(orientation="h", y=1.08),
            margin=dict(t=70, b=50))
        st.plotly_chart(fig5, use_container_width=True)

    with mc2:
        fig6 = go.Figure()
        for rm in rms:
            d = rm_mom[rm_mom["RM"]==rm].set_index("Month").reindex(months).reset_index()
            fig6.add_scatter(x=d["Month"], y=d["Collection_Efficiency_Pct"],
                mode="lines+markers", name=rm,
                line=dict(color=RM_COLORS.get(rm,"#1A3C6E"), width=2.5),
                marker=dict(size=8), connectgaps=True)
        fig6.add_hline(y=90, line_dash="dash", line_color="#2E7D32",
            annotation_text="90% target")
        fig6.update_layout(template="plotly_white", height=420,
            title="<b>RM Collection Efficiency %</b> — MoM",
            xaxis=dict(categoryorder="array", categoryarray=months),
            yaxis=dict(ticksuffix="%", range=[0,115]),
            legend=dict(orientation="h", y=1.08), margin=dict(t=70, b=50))
        st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ── Detailed project-level table ──────────────────────────────────────────────
st.markdown("### 📋 Project-level Detail by RM")
disp = project_df[[
    "RM","Project","Actual Demand Raised (Cr)","Collection Till Date (Cr)",
    "Outstanding (Cr)","Collection_Eff_Pct","Collection Target (Cr)",
    "Achievement_Pct_Disp","Pending Registrations","Pending Reg > 45 Days",
]].copy()
disp.columns=[
    "RM","Project","Demand (Cr)","Collection (Cr)","Outstanding (Cr)",
    "Eff %","Monthly Target (Cr)","Ach %","Pending Reg","Pending >45d"
]
st.dataframe(
    disp.sort_values("RM").style.format({
        "Demand (Cr)":        "₹ {:.2f} Cr",
        "Collection (Cr)":    "₹ {:.2f} Cr",
        "Outstanding (Cr)":   "₹ {:.2f} Cr",
        "Monthly Target (Cr)":"₹ {:.2f} Cr",
        "Eff %":              "{:.1f}%",
        "Ach %":              "{:.1f}%",
    }),
    use_container_width=True, hide_index=True,
)

csv = disp.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export RM Report CSV", csv, "rm_performance.csv", "text/csv")
