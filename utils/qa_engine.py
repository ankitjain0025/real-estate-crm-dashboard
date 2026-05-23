"""
utils/qa_engine.py
Gemini AI Q&A engine — fixed for 429 quota errors.

Key fixes vs original:
  - Uses google-generativeai SDK (not google-genai)
  - Model priority list: gemini-1.5-flash → gemini-1.5-flash-8b → gemini-1.0-pro
  - Compact context builder (avoids token quota exhaustion)
  - Retry logic with backoff on 429 / 503
  - Clear, actionable error messages shown to user
  - Supports both single-month and multi-month context
"""

import time
import streamlit as st
import pandas as pd

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

MODEL_PRIORITY = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.0-pro",
]
MAX_RETRIES  = 3
RETRY_DELAYS = [5, 15, 30]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _get_api_key():
    try:
        k = st.secrets["GEMINI_API_KEY"]
        return k if k and str(k).strip() else None
    except Exception:
        return None


def _get_model():
    if not GENAI_AVAILABLE:
        return None, None
    key = _get_api_key()
    if not key:
        return None, None
    genai.configure(api_key=key)
    cfg = genai.types.GenerationConfig(temperature=0.05, max_output_tokens=800, top_p=0.9)
    for name in MODEL_PRIORITY:
        try:
            return genai.GenerativeModel(name, generation_config=cfg), name
        except Exception:
            continue
    return None, None


def _build_context(project_df, category_df, kpis, mom_df=None, question=""):
    """Build compact context — only include what the question needs."""
    q = question.lower()
    parts = []

    # Portfolio KPIs always included
    parts.append(
        f"PORTFOLIO SNAPSHOT | Date: {kpis.get('report_date','—')}\n"
        f"Demand: ₹{kpis.get('total_demand',0):.2f}Cr | "
        f"Collection: ₹{kpis.get('total_collection',0):.2f}Cr | "
        f"Outstanding: ₹{kpis.get('total_outstanding',0):.2f}Cr | "
        f"Monthly: ₹{kpis.get('monthly_coll',0):.2f}Cr | "
        f"Live Bookings: {int(kpis.get('total_live_bkgs',0))} | "
        f"Pending Reg: {int(kpis.get('pending_reg',0))} | "
        f"Pending>45d: {int(kpis.get('pending_reg_45',0))} | "
        f"CRM Target: ₹{kpis.get('crm_monthly_tgt',0):.2f}Cr | "
        f"CRM Achievement: ₹{kpis.get('crm_monthly_ach',0):.2f}Cr"
    )

    # Current month project table — always included
    rows = []
    for _, r in project_df.iterrows():
        demand = r.get("Actual Demand Raised (Cr)", 0)
        coll   = r.get("Collection Till Date (Cr)", 0)
        eff    = round(coll / demand * 100, 1) if demand else 0
        rows.append(
            f"{r.get('Project','')} | "
            f"Demand:₹{demand:.2f} | Collected:₹{coll:.2f} | "
            f"Outstanding:₹{r.get('Outstanding (Cr)',0):.2f} | Eff:{eff}% | "
            f"Target:₹{r.get('Collection Target (Cr)',0):.2f} | "
            f"Ach:₹{r.get('Collection Achievement (Cr)',0):.2f}({r.get('Achievement %',0)*100:.1f}%) | "
            f"PendReg:{int(r.get('Pending Registrations',0))} | "
            f"Pend>45:{int(r.get('Pending Reg > 45 Days',0))}"
        )
    parts.append("CURRENT MONTH PROJECTS\n" + "\n".join(rows))

    # Category breakdown — only when relevant
    if any(k in q for k in ["category","ocr","slab","spill","segment","type"]):
        if not category_df.empty:
            cat_rows = [
                f"{r.get('Category','')} | Target:₹{r.get('Target (Cr)',0):.2f} | "
                f"Ach:₹{r.get('Achievement (Cr)',0):.2f} | {r.get('Achievement %',0)*100:.1f}%"
                for _, r in category_df.iterrows()
            ]
            parts.append("CATEGORY BREAKDOWN\n" + "\n".join(cat_rows))

    # Multi-month data — only when trend/month question
    if mom_df is not None and not mom_df.empty:
        if any(k in q for k in ["month","trend","mom","march","april","may","jan","feb",
                                  "history","compare","over time","improve","worsen",
                                  "efficiency","target","forecast","outstanding"]):
            # Summarise by month+project (compact)
            keep = ["Month","Project","Monthly_Achievement_Cr","Achievement_Pct",
                    "Forecast_Cr","Collection_Efficiency_Pct","Outstanding_Cr",
                    "Pending_Reg"]
            sub = mom_df[[c for c in keep if c in mom_df.columns]]
            mom_lines = []
            for _, r in sub.iterrows():
                mom_lines.append(
                    f"{r['Month']} | {r['Project']} | "
                    f"Ach:₹{r.get('Monthly_Achievement_Cr',0):.2f}Cr({r.get('Achievement_Pct',0):.1f}%) | "
                    f"Forecast:₹{r.get('Forecast_Cr',0):.2f} | "
                    f"Eff:{r.get('Collection_Efficiency_Pct',0):.1f}% | "
                    f"Outstanding:₹{r.get('Outstanding_Cr',0):.2f} | "
                    f"PendReg:{int(r.get('Pending_Reg',0))}"
                )
            parts.append("MONTH-ON-MONTH DATA\n" + "\n".join(mom_lines))

    return "\n\n".join(parts)


_SYSTEM = """You are a senior CRM analyst at RAGHAV Group, a Mumbai real estate developer.
Answer ONLY using the data provided. Never invent numbers.
If data is unavailable, say exactly: "This information is not available in the current report."
Always include units (₹ Cr, %, count). Be concise — 3 to 8 lines.
Collection Efficiency = Collection ÷ Demand × 100. All amounts in Indian Crores (1 Cr = ₹10 million).

DATA:
{context}"""


def _call_with_retry(model, prompt):
    for attempt in range(MAX_RETRIES):
        try:
            return model.generate_content(prompt).text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise _QuotaError()
            elif "503" in err or "unavailable" in err.lower():
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                    continue
                raise _ServiceError()
            else:
                raise e
    raise RuntimeError("Max retries exceeded")


class _QuotaError(Exception): pass
class _ServiceError(Exception): pass


# ── Public API ─────────────────────────────────────────────────────────────────

def ask_gemini(question, project_df, category_df, kpis, mom_df=None):
    """
    Main entry point called by app.py.
    Returns a markdown-formatted string answer.
    """
    if not question or not question.strip():
        return "Please type a question."

    if not GENAI_AVAILABLE:
        return ("⚠️ **google-generativeai not installed.**\n\n"
                "Add `google-generativeai` to `requirements.txt` and redeploy.")

    if not _get_api_key():
        return ("⚠️ **GEMINI_API_KEY not found in Streamlit secrets.**\n\n"
                "Go to **Settings → Secrets** and add:\n```\nGEMINI_API_KEY = \"your-key\"\n```\n"
                "Get a free key at https://aistudio.google.com/app/apikey")

    model, model_name = _get_model()
    if model is None:
        return "⚠️ Could not initialise Gemini. Check your API key."

    context = _build_context(project_df, category_df, kpis, mom_df, question)
    prompt  = _SYSTEM.format(context=context) + f"\n\nQuestion: {question.strip()}"

    try:
        return _call_with_retry(model, prompt)

    except _QuotaError:
        return (
            "🚫 **Gemini quota exceeded.**\n\n"
            "Your API key has hit its free-tier limit.\n\n"
            "**Fix options:**\n"
            "1. Enable billing at https://console.cloud.google.com/billing\n"
            "2. Wait until midnight PT for the daily free quota to reset\n"
            "3. Free tier: 15 req/min, ~1,500 req/day — a paid key removes limits\n\n"
            f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}"
        )

    except _ServiceError:
        return (
            f"⏳ **Gemini temporarily unavailable.** Try again in 1 minute.\n\n"
            f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}"
        )

    except Exception as e:
        return (
            f"⚠️ **Gemini error** (`{model_name}`): {str(e)}\n\n"
            f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}"
        )


def _rule_answer(question, project_df, kpis):
    """Deterministic fallback — answers directly from DataFrames."""
    q = question.lower()
    lines = []

    if any(k in q for k in ["total","portfolio","overall","summary","kpi"]):
        lines += [
            f"- Total Demand: ₹{kpis.get('total_demand',0):.2f} Cr",
            f"- Total Collection: ₹{kpis.get('total_collection',0):.2f} Cr",
            f"- Total Outstanding: ₹{kpis.get('total_outstanding',0):.2f} Cr",
            f"- Monthly Collection: ₹{kpis.get('monthly_coll',0):.2f} Cr",
        ]

    if any(k in q for k in ["outstanding","defaulter","overdue"]):
        if not project_df.empty and "Outstanding (Cr)" in project_df.columns:
            top = project_df.sort_values("Outstanding (Cr)", ascending=False)
            lines.append("\n**Projects by Outstanding:**")
            for _, r in top.iterrows():
                lines.append(f"- {r['Project']}: ₹{r['Outstanding (Cr)']:.2f} Cr")

    if any(k in q for k in ["efficiency"]):
        if not project_df.empty:
            lines.append("\n**Collection Efficiency:**")
            for _, r in project_df.iterrows():
                d = r.get("Actual Demand Raised (Cr)", 0)
                c = r.get("Collection Till Date (Cr)", 0)
                eff = round(c/d*100, 1) if d else 0
                lines.append(f"- {r['Project']}: {eff}%")

    if any(k in q for k in ["pending","registration"]):
        if not project_df.empty and "Pending Registrations" in project_df.columns:
            lines.append("\n**Pending Registrations:**")
            for _, r in project_df.sort_values("Pending Registrations", ascending=False).iterrows():
                lines.append(f"- {r['Project']}: {int(r['Pending Registrations'])} ({int(r.get('Pending Reg > 45 Days',0))} > 45 days)")

    return "\n".join(lines) if lines else "Please check the dashboard charts above for details."
