# RAGHAV Group — CRM Collection MIS Dashboard

Enterprise-grade CRM dashboard for Mumbai real estate developers.  
Built with **Streamlit · Pandas · Plotly · Gemini AI**.

---

## Setup

### 1. Clone your repo and place Excel files in `data/`

```
data/
  Overall Collection Summary - Mar 2026.xlsx
  Overall Collection Summary - Apr 2026.xlsx
  Overall Collection Summary - May 2026.xlsx
```

### 2. Add your Gemini API key

In `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
```
Get a key free at https://aistudio.google.com/app/apikey  
Enable billing to avoid 429 quota errors.

### 3. Install dependencies and run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 4. Deploy to Streamlit Cloud

1. Push repo to GitHub (do **not** commit `secrets.toml`)
2. Go to https://share.streamlit.io → New app → Select repo → `app.py`
3. Under **Settings → Secrets**, paste:
   ```
   GEMINI_API_KEY = "your-key-here"
   ```
4. Click **Deploy**

---

## File Structure

```
real-estate-crm-dashboard/
├── app.py                          ← Main Streamlit app (3 tabs)
├── requirements.txt
├── data/
│   └── Overall Collection Summary*.xlsx
├── utils/
│   ├── __init__.py
│   ├── data_loader.py              ← Parses current month Excel
│   ├── multi_month_loader.py       ← Loads all monthly files for MoM
│   ├── dashboard.py                ← All current-month chart functions
│   ├── mom_charts.py               ← All MoM trend chart functions
│   ├── qa_engine.py                ← Gemini AI Q&A engine
│   ├── crm_metrics.py              ← CRM metric calculations
│   └── helpers.py                  ← Formatting utilities
└── .streamlit/
    └── secrets.toml                ← API key (DO NOT commit to GitHub)
```

## Dashboard Tabs

| Tab | Contents |
|-----|----------|
| 📊 Current Month | KPIs · Project analysis · Target vs Achievement · Outstanding · Category breakdown · Top defaulters · Export CSV |
| 📈 MoM Trends | Efficiency trend · Target vs Achievement history · Outstanding trend · Forecast accuracy · Heatmap |
| 🤖 AI Assistant | Gemini-powered Q&A answering from live Excel data |
