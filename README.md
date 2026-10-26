# NEXUS — Enterprise Decision Intelligence Platform

A lightweight business intelligence MVP combining operational analytics, machine-learning demonstrations, and a natural-language business Q&A interface.

## Features
- Executive KPIs: revenue, profit, transaction count, and profit margin
- Monthly revenue and profit trends
- Regional and product performance tables
- Random Forest revenue forecasting demonstration
- Isolation Forest anomaly detection
- Natural-language business Q&A endpoint using rule-based insights
- SQLite-backed synthetic demo data
- CSV export generated for Power BI and Tableau

## Tech stack
Python, Flask, SQLite, pandas, scikit-learn, HTML, CSS, JavaScript, and Chart.js.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. On first run, the app creates the SQLite database, generates synthetic transactions and customers, and writes `data/transactions.csv`.

## Power BI and Tableau
Import `data/transactions.csv` after the first run. Suggested views:
- Executive KPI overview
- Monthly revenue and profit trends
- Regional performance comparison
- Product profitability

## Jira / Agile
Suggested epics for a Jira project:
1. Data & SQL
2. Business Analytics
3. Power BI Dashboard
4. Tableau Dashboard
5. AI/ML Analytics
6. Business Q&A Assistant
7. Web Application

## Scope and limitations
This is a demo MVP using synthetic data. The forecast is a baseline machine-learning demonstration. The Q&A endpoint uses deterministic response templates and is **not connected to an LLM**, despite the UI's GenAI-style label. Validate model quality and metrics before using this design for real business decisions.
