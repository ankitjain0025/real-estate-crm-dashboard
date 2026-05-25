"""
utils/qa_engine.py
Gemini AI Q&A — fixed model list for 404 / 429 errors.

Root cause of 404: gemini-1.5-flash requires API version v1, not v1beta.
google-generativeai SDK < 0.8 defaults to v1beta for some models.
Fix: use model names that work on v1beta AND v1, with fallback chain.
"""

import time
import streamlit as st
import pandas as pd

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Model priority — ordered by availability across free & paid keys
# gemini-1.5-flash-latest  → resolves to latest stable, avoids version issues
# gemini-1.5-pro-latest    → fallback
# gemini-pro               → oldest, widest compatibility
MODEL_PRIORITY = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-pro",
]

MAX_RETRIES  = 3
RETRY_DELAYS = [5, 15, 30]


def _get_api_key():
    try:
        k = st.secrets.get("GEMINI_API_KEY", "")
        return k if k and str(k).strip() and k != "your-gemini-api-key-here" else None
    except Exception:
        return None


def _get_model():
    if not GENAI_AVAILABLE:
        return None, None
    key = _get_api_key()
    if not key:
        return None, None

    genai.configure(api_key=key)
    cfg = genai.types.GenerationConfig(
        temperature=0.05,
        max_output_tokens=800,
        top_p=0.9,
    )
    for name in MODEL_PRIORITY:
        try:
            model = genai.GenerativeModel(name, generation_config=cfg)
            return model, name
        except Exception:
            continue
    return None, None


def _build_context(project_df, category_df, kpis, mom_df=None, question=""):
    q = question.lower()
    parts = []

    # Always include portfolio KPIs
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

    # Project table — always included
    if not project_df.empty:
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
                f"Ach:₹{r.get('Collection Achievement (Cr)',0):.2f} | "
                f"AchPct:{r.get('Achievement %',0)*100:.1f}% | "
                f"PendReg:{int(r.get('Pending Registrations',0))} | "
                f"Pend>45:{int(r.get('Pending Reg > 45 Days',0))}"
            )
        parts.append("PROJECTS\n" + "\n".join(rows))

    # Category — only when relevant
    if any(k in q for k in ["category","ocr","slab","spill","segment","type","booking"]):
        if not category_df.empty:
            rows = [
                f"{r.get('Category','')} | Target:₹{r.get('Target (Cr)',0):.2f} | "
                f"Ach:₹{r.get('Achievement (Cr)',0):.2f} | "
                f"AchPct:{r.get('Achievement %',0)*100:.1f}%"
                for _, r in category_df.iterrows()
            ]
            parts.append("CATEGORIES\n" + "\n".join(rows))

    # MoM — only when trend question
    if mom_df is not None and not mom_df.empty:
        if any(k in q for k in ["month","trend","mom","march","april","may","jan","feb",
                                  "history","compare","over time","improve","worsen",
                                  "efficiency","outstanding","forecast"]):
            keep = [c for c in ["Month","Project","Monthly_Achievement_Cr",
                                 "Achievement_Pct","Forecast_Cr",
                                 "Collection_Efficiency_Pct","Outstanding_Cr",
                                 "Pending_Reg"] if c in mom_df.columns]
            lines = [
                " | ".join(f"{k}:{round(v,2) if isinstance(v,float) else v}"
                           for k, v in zip(keep, row))
                for row in mom_df[keep].values
            ]
            parts.append("MONTH-ON-MONTH\n" + "\n".join(lines))

    return "\n\n".join(parts)


_SYSTEM = """You are a senior CRM analyst at RAGHAV Group, a Mumbai real estate developer.
Answer ONLY from the data provided. Never invent figures.
If data unavailable say: "This information is not available in the current report."
Units: ₹ Cr, %, count. Be concise — 3 to 8 lines max.
Collection Efficiency = Collection ÷ Demand × 100. All amounts in Indian Crores.

DATA:
{context}"""


def _call_with_retry(model, prompt, model_name):
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
            elif "404" in err or "not found" in err.lower():
                raise _ModelNotFoundError(model_name)
            else:
                raise e
    raise RuntimeError("Max retries exceeded")


class _QuotaError(Exception): pass
class _ServiceError(Exception): pass
class _ModelNotFoundError(Exception): pass


def ask_gemini(question, project_df, category_df, kpis, mom_df=None):
    if not question or not question.strip():
        return "Please type a question."

    if not GENAI_AVAILABLE:
        return ("⚠️ **google-generativeai not installed.**\n\n"
                "Add `google-generativeai` to `requirements.txt` and redeploy.")

    if not _get_api_key():
        return ("⚠️ **GEMINI_API_KEY not configured.**\n\n"
                "Go to Streamlit Cloud → **Settings → Secrets** and add:\n"
                "```\nGEMINI_API_KEY = \"your-key-here\"\n```\n"
                "Get a free key at https://aistudio.google.com/app/apikey")

    model, model_name = _get_model()
    if model is None:
        return "⚠️ Could not initialise any Gemini model. Check your API key."

    context = _build_context(project_df, category_df, kpis, mom_df, question)
    prompt  = _SYSTEM.format(context=context) + f"\n\nQuestion: {question.strip()}"

    try:
        return _call_with_retry(model, prompt, model_name)

    except _ModelNotFoundError as e:
        # Try next model in list manually
        genai.configure(api_key=_get_api_key())
        cfg = genai.types.GenerationConfig(temperature=0.05, max_output_tokens=800)
        for fallback_name in MODEL_PRIORITY:
            if fallback_name == str(e):
                continue
            try:
                fb_model = genai.GenerativeModel(fallback_name, generation_config=cfg)
                return fb_model.generate_content(prompt).text.strip()
            except Exception:
                continue
        return (
            f"⚠️ **No Gemini model available** on your API key.\n\n"
            f"Tried: {', '.join(MODEL_PRIORITY)}\n\n"
            f"**Fix:** Enable billing at https://console.cloud.google.com/billing "
            f"or generate a new key at https://aistudio.google.com/app/apikey\n\n"
            f"**Data answer:**\n{_rule_answer(question, project_df, kpis)}"
        )

    except _QuotaError:
        return (
            "🚫 **Quota exceeded** — free tier limit hit.\n\n"
            "Enable billing at https://console.cloud.google.com/billing "
            "or wait until midnight PT for reset.\n\n"
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
    q = question.lower()
    lines = []

    if any(k in q for k in ["total","portfolio","overall","summary"]):
        lines += [
            f"- Total Demand: ₹{kpis.get('total_demand',0):.2f} Cr",
            f"- Total Collection: ₹{kpis.get('total_collection',0):.2f} Cr",
            f"- Outstanding: ₹{kpis.get('total_outstanding',0):.2f} Cr",
            f"- Efficiency: {kpis.get('collection_eff',0):.1f}%",
            f"- Monthly Target: ₹{kpis.get('crm_monthly_tgt',0):.2f} Cr",
            f"- Monthly Achievement: ₹{kpis.get('crm_monthly_ach',0):.2f} Cr",
        ]

    if any(k in q for k in ["outstanding","defaulter","overdue"]):
        if not project_df.empty and "Outstanding (Cr)" in project_df.columns:
            lines.append("\n**Projects by Outstanding:**")
            for _, r in project_df.sort_values("Outstanding (Cr)", ascending=False).iterrows():
                lines.append(f"- {r['Project']}: ₹{r['Outstanding (Cr)']:.2f} Cr")

    if any(k in q for k in ["efficiency"]):
        if not project_df.empty:
            lines.append("\n**Collection Efficiency:**")
            for _, r in project_df.iterrows():
                d = r.get("Actual Demand Raised (Cr)", 0)
                c = r.get("Collection Till Date (Cr)", 0)
                lines.append(f"- {r['Project']}: {round(c/d*100,1) if d else 0}%")

    if any(k in q for k in ["pending","registration"]):
        if not project_df.empty and "Pending Registrations" in project_df.columns:
            lines.append("\n**Pending Registrations:**")
            for _, r in project_df.sort_values("Pending Registrations", ascending=False).iterrows():
                lines.append(
                    f"- {r['Project']}: {int(r['Pending Registrations'])} "
                    f"({int(r.get('Pending Reg > 45 Days',0))} > 45 days)"
                )

    if any(k in q for k in ["target","achieve","forecast"]):
        if not project_df.empty and "Collection Target (Cr)" in project_df.columns:
            lines.append("\n**Target vs Achievement:**")
            for _, r in project_df.iterrows():
                lines.append(
                    f"- {r['Project']}: Target ₹{r.get('Collection Target (Cr)',0):.2f} | "
                    f"Achieved ₹{r.get('Collection Achievement (Cr)',0):.2f} | "
                    f"{r.get('Achievement %',0)*100:.1f}%"
                )

    return "\n".join(lines) if lines else "Please refer to the dashboard charts above."
