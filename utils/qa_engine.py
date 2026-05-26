"""
utils/qa_engine.py — Gemini Q&A engine
Fix: st.secrets["key"] in try/except instead of st.secrets.get()
     which silently returns "" on Streamlit Cloud even when key exists.
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
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
]
MAX_RETRIES  = 3
RETRY_DELAYS = [5, 15, 30]


def _get_api_key():
    """Read API key — uses [] not .get() to work on Streamlit Cloud."""
    try:
        k = st.secrets["GEMINI_API_KEY"]
        return str(k).strip() if k and str(k).strip() != "your-gemini-api-key-here" else None
    except (KeyError, FileNotFoundError, Exception):
        return None


def _build_context(project_df, category_df, kpis, mom_df=None, question=""):
    q = question.lower()
    parts = []

    parts.append(
        f"PORTFOLIO | Date:{kpis.get('report_date','—')} | Month:{kpis.get('month_label','—')}\n"
        f"Demand:₹{kpis.get('total_demand',0):.2f}Cr | "
        f"Collection:₹{kpis.get('total_collection',0):.2f}Cr | "
        f"Outstanding:₹{kpis.get('total_outstanding',0):.2f}Cr | "
        f"Efficiency:{kpis.get('collection_eff',0):.1f}% | "
        f"MonthlyTarget:₹{kpis.get('crm_monthly_tgt',0):.2f}Cr | "
        f"MonthlyAch:₹{kpis.get('crm_monthly_ach',0):.2f}Cr | "
        f"PendingReg:{int(kpis.get('pending_reg',0))} | "
        f"PendingReg>45d:{int(kpis.get('pending_reg_45',0))}"
    )

    if not project_df.empty:
        rows = []
        for _, r in project_df.iterrows():
            demand = r.get("Actual Demand Raised (Cr)", 0)
            coll   = r.get("Collection Till Date (Cr)", 0)
            tgt    = r.get("Collection Target (Cr)", 0)
            fore   = r.get("CRM Forecast (Cr)", 0)
            eff    = round(coll/demand*100, 1) if demand else 0
            rows.append(
                f"{r.get('Project','')} | RM:{r.get('RM','—')} | "
                f"Demand:₹{demand:.2f} | Collected:₹{coll:.2f} | "
                f"Outstanding:₹{r.get('Outstanding (Cr)',0):.2f} | Eff:{eff}% | "
                f"Target:₹{tgt:.2f} | Forecast:₹{fore:.2f} | "
                f"Ach:₹{r.get('Collection Achievement (Cr)',0):.2f} | "
                f"AchPct:{r.get('Achievement %',0)*100:.1f}% | "
                f"PendReg:{int(r.get('Pending Registrations',0))} | "
                f"Pend>45:{int(r.get('Pending Reg > 45 Days',0))}"
            )
        parts.append("PROJECTS\n" + "\n".join(rows))

    if any(k in q for k in ["category","ocr","slab","spill","booking"]):
        if not category_df.empty:
            rows = [
                f"{r.get('Category','')} | Target:₹{r.get('Target (Cr)',0):.2f} | "
                f"Ach:₹{r.get('Achievement (Cr)',0):.2f} | {r.get('Achievement %',0)*100:.1f}%"
                for _, r in category_df.iterrows()
            ]
            parts.append("CATEGORIES\n" + "\n".join(rows))

    if mom_df is not None and not mom_df.empty:
        if any(k in q for k in ["month","trend","mom","march","april","may","feb","history",
                                  "compare","improve","worsen","efficiency","outstanding",
                                  "forecast","rm","relationship"]):
            keep = [c for c in ["Month","Project","RM","Monthly_Achievement_Cr",
                                 "Achievement_Pct","Forecast_Cr","Collection_Efficiency_Pct",
                                 "Outstanding_Cr","Pending_Reg"] if c in mom_df.columns]
            lines = [
                " | ".join(f"{k}:{round(v,2) if isinstance(v,float) else v}"
                           for k,v in zip(keep, row))
                for row in mom_df[keep].values
            ]
            parts.append("MONTH-ON-MONTH\n" + "\n".join(lines))

    return "\n\n".join(parts)


_SYSTEM = """You are a senior CRM analyst at RAGHAV Group, a Mumbai real estate developer.
Answer ONLY from the data provided. Never invent figures.
If unavailable say: "This information is not available in the current report."
Units: ₹ Cr, %, count. Be concise — 3 to 8 lines.
Collection Efficiency = Collection ÷ Demand × 100. All amounts in Indian Crores.
RM (Relationship Manager) is responsible for demand dispatch, customer follow-up, collection.
OCR and New Booking collection is Sales team responsibility.

DATA:
{context}"""


class _QuotaError(Exception): pass
class _ServiceError(Exception): pass
class _ModelNotFoundError(Exception): pass


def _call_with_retry(model, prompt, model_name):
    for attempt in range(MAX_RETRIES):
        try:
            return model.generate_content(prompt).text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt]); continue
                raise _QuotaError()
            elif "503" in err or "unavailable" in err.lower():
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAYS[attempt]); continue
                raise _ServiceError()
            elif "404" in err or "not found" in err.lower():
                raise _ModelNotFoundError(model_name)
            else:
                raise e
    raise RuntimeError("Max retries exceeded")


def ask_gemini(question, project_df, category_df, kpis, mom_df=None):
    if not question or not question.strip():
        return "Please type a question."
    if not GENAI_AVAILABLE:
        return "⚠️ **google-generativeai not installed.** Add to `requirements.txt`."

    key = _get_api_key()
    if not key:
        return ("⚠️ **GEMINI_API_KEY not found in Streamlit Secrets.**\n\n"
                "Go to Streamlit Cloud → your app → **Settings → Secrets** and add:\n"
                "```\nGEMINI_API_KEY = \"your-key-here\"\n```\n"
                "Then **Reboot** the app. Get a key at https://aistudio.google.com/app/apikey")

    genai.configure(api_key=key)
    cfg = genai.types.GenerationConfig(temperature=0.05, max_output_tokens=800)
    context = _build_context(project_df, category_df, kpis, mom_df, question)
    prompt  = _SYSTEM.format(context=context) + f"\n\nQuestion: {question.strip()}"

    last_err = ""
    for model_name in MODEL_PRIORITY:
        try:
            model = genai.GenerativeModel(model_name, generation_config=cfg)
            return _call_with_retry(model, prompt, model_name)
        except _QuotaError:
            return (
                "🚫 **Quota exceeded.** Enable billing at "
                "https://console.cloud.google.com/billing\n\n"
                f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}"
            )
        except _ServiceError:
            return (f"⏳ **Gemini temporarily unavailable.** Try again.\n\n"
                    f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}")
        except _ModelNotFoundError:
            last_err = f"{model_name} not available on your key"
            continue
        except Exception as e:
            last_err = str(e)
            continue

    return (f"⚠️ **Gemini unavailable** ({last_err})\n\n"
            f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}")


def _rule_answer(question, project_df, kpis):
    q = question.lower(); lines = []
    if any(k in q for k in ["total","portfolio","overall","summary"]):
        lines += [f"- Total Demand: ₹{kpis.get('total_demand',0):.2f} Cr",
                  f"- Total Collection: ₹{kpis.get('total_collection',0):.2f} Cr",
                  f"- Outstanding: ₹{kpis.get('total_outstanding',0):.2f} Cr",
                  f"- Efficiency: {kpis.get('collection_eff',0):.1f}%",
                  f"- Monthly Target: ₹{kpis.get('crm_monthly_tgt',0):.2f} Cr",
                  f"- Monthly Achievement: ₹{kpis.get('crm_monthly_ach',0):.2f} Cr"]
    if any(k in q for k in ["outstanding","defaulter","overdue"]):
        if not project_df.empty and "Outstanding (Cr)" in project_df.columns:
            lines.append("\n**Projects by Outstanding:**")
            for _, r in project_df.sort_values("Outstanding (Cr)", ascending=False).iterrows():
                d = r.get("Actual Demand Raised (Cr)", 0)
                pct = round(r["Outstanding (Cr)"]/d*100, 1) if d else 0
                lines.append(f"- {r['Project']}: ₹{r['Outstanding (Cr)']:.2f} Cr ({pct}% of demand)")
    if any(k in q for k in ["efficiency"]):
        if not project_df.empty:
            lines.append("\n**Collection Efficiency:**")
            for _, r in project_df.iterrows():
                d=r.get("Actual Demand Raised (Cr)",0); c=r.get("Collection Till Date (Cr)",0)
                lines.append(f"- {r['Project']}: {round(c/d*100,1) if d else 0}%")
    if any(k in q for k in ["pending","registration"]):
        if not project_df.empty and "Pending Registrations" in project_df.columns:
            lines.append("\n**Pending Registrations:**")
            for _, r in project_df.sort_values("Pending Registrations",ascending=False).iterrows():
                lines.append(f"- {r['Project']}: {int(r['Pending Registrations'])} ({int(r.get('Pending Reg > 45 Days',0))} > 45d)")
    if any(k in q for k in ["rm","relationship"]):
        if not project_df.empty and "RM" in project_df.columns:
            lines.append("\n**RM-wise Outstanding:**")
            for rm, val in project_df.groupby("RM")["Outstanding (Cr)"].sum().sort_values(ascending=False).items():
                lines.append(f"- {rm}: ₹{val:.2f} Cr")
    return "\n".join(lines) if lines else "Please refer to the dashboard charts above."
