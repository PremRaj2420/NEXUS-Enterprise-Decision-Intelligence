# NEXUS — Enterprise Decision Intelligence Platform

A portfolio MVP combining business analytics, machine-learning demonstrations, and a dashboard interface.

## Features
- Revenue, profit, transaction count, and profit margin KPIs
- Monthly revenue/profit trends
- Regional and product analytics
- Random Forest revenue forecasting demonstration
- Isolation Forest anomaly detection
- Business Q&A endpoint using deterministic response templates
- Synthetic SQLite demo data and CSV export for BI tools
- Static Netlify frontend + Flask API hosted separately

## Tech stack
Python, Flask, SQLite, pandas, scikit-learn, Gunicorn, HTML, CSS, JavaScript, Chart.js, Netlify, Render.

## Deploy online

### 1. Deploy the Python API on Render
1. Open https://dashboard.render.com and choose **New + → Web Service**.
2. Connect the repository `PremRaj2420/NEXUS-Enterprise-Decision-Intelligence`.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Set **Start Command** to `gunicorn --bind 0.0.0.0:$PORT app:app`.
5. Create the service and wait for it to become live.
6. Copy its URL, for example `https://your-service.onrender.com`.

A `render.yaml` Blueprint file is also included as a configuration reference.

### 2. Connect the Netlify frontend to the API
Edit `netlify-site/config.js` and replace the empty value with your actual Render URL:

```js
window.NEXUS_API_BASE = "https://your-service.onrender.com";
```

Do not add a trailing slash. Commit the change to GitHub.

### 3. Deploy the frontend on Netlify
1. Open https://app.netlify.com and choose **Add new project → Import an existing project**.
2. Select the GitHub repository.
3. The included `netlify.toml` sets the publish directory to `netlify-site`; no frontend build step is needed.
4. Deploy the site. Netlify will redeploy when you push future frontend changes.

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. The first run seeds the SQLite database and creates `data/transactions.csv`.

## Power BI and Tableau
Import `data/transactions.csv` after running the app once. Suggested dashboards: executive KPIs, monthly revenue/profit trends, regional performance, and product profitability.

## Limitations
This is a demonstration with synthetic data. The forecast is a baseline model; the Q&A assistant uses deterministic response templates and is not connected to a large language model. Render's local filesystem may reset on service restarts, so the demo database is reseeded as needed. For production, use a managed database and restrict CORS to your Netlify domain.
