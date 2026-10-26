# NEXUS — Enterprise Decision Intelligence Platform

A lightweight business intelligence MVP combining operational analytics, machine-learning demonstrations, and a natural-language business Q&A interface.

## Features
- Executive KPIs: revenue, profit, transaction count, and profit margin
- Monthly revenue and profit trends
- Regional and product performance tables
- Random Forest revenue forecast demonstration
- Isolation Forest anomaly detection
- Natural-language business Q&A endpoint (rule-based insight templates, not a connected LLM)
- SQLite-backed demo dataset and CSV export for Power BI/Tableau

## Stack
Python, Flask, SQLite, pandas, scikit-learn, HTML, CSS, JavaScript, Chart.js.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The app seeds a local demo database on the first run.

## Data and BI
`data/transactions.csv` contains synthetic transaction data for practice and dashboard building. Import it into Power BI or Tableau and create executive KPI, monthly trend, regional performance, and product profitability views.

## Jira / Agile suggestion
Track the project in Jira with epics for Data & SQL, Analytics, Power BI, Tableau, AI/ML, GenAI Assistant, and Web Application.

## Important scope note
This is a demo MVP using synthetic data. The forecasting model is a baseline demonstration, and the business Q&A endpoint uses deterministic templates rather than a connected large language model. Validate metrics and model quality before using for real business decisions.
