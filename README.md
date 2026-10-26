# NEXUS — Enterprise Decision Intelligence Platform

NEXUS is a portfolio MVP that combines business analytics, a web dashboard, and baseline machine-learning demonstrations. **The entire app can run as one Render web service**: Flask serves both the dashboard and its API.

## Features
- Revenue, profit, transaction count, and profit margin KPIs
- Monthly revenue/profit charts
- Regional and product analytics
- Random Forest revenue forecast demonstration
- Isolation Forest anomaly detection
- Business Q&A endpoint using deterministic response templates
- Synthetic SQLite data generation and CSV export for Power BI/Tableau

## Tech stack
Python, Flask, SQLite, pandas, scikit-learn, Gunicorn, HTML, CSS, JavaScript, Chart.js, Render.

## Deploy on Render

### One-click Blueprint
Use the Render Blueprint link and authorize Render to access this GitHub repository:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FPremRaj2420%2FNEXUS-Enterprise-Decision-Intelligence)

Review the service configuration and choose **Apply**. Render reads `render.yaml`, installs dependencies, and starts the Flask app. When deployment succeeds, open the `onrender.com` URL shown by Render.

### If creating the service manually
Connect this repo in Render → **New + → Web Service** and use:

| Setting | Value |
|---|---|
| Runtime | Python |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn --bind 0.0.0.0:$PORT app:app` |
| Health check path | `/api/summary` |

The Flask app serves both the page and API on the same domain, so you do not need Netlify or a second backend host.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The first run seeds the SQLite database and creates `data/transactions.csv`.

## Power BI and Tableau
After running locally, import `data/transactions.csv` into Power BI or Tableau. Suggested views: executive KPI overview, monthly revenue/profit trend, regional performance, and product profitability.

## Jira / Agile
Suggested epics: Data & SQL, Business Analytics, Power BI, Tableau, AI/ML Analytics, Business Q&A Assistant, and Web Application.

## Limitations
This demo uses synthetic data. The forecast is a baseline model. The Q&A assistant uses deterministic response templates and **is not connected to a large language model**. Render's free service may spin down after inactivity, and its local filesystem is not persistent across all service events; this app regenerates demo data on startup. For a production system, use managed persistent storage/database and restrict CORS to known origins.
