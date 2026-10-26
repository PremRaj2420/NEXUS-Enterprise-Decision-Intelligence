# NEXUS — Enterprise Decision Intelligence Platform

NEXUS is an interview-ready portfolio demo for exploring business analytics, customer risk, machine-learning prototypes and executive reporting. The Flask app serves the complete frontend and API from **one Render service**.

## Working modules
- **Overview:** revenue, profit, transaction count, margin, AOV, customer risk, monthly trends, regional and product summaries.
- **Sales analytics:** date, region and product filters; filtered KPIs and visual breakdowns.
- **Customer 360:** searchable customer list with risk/segment filters, satisfaction, revenue and segment comparison.
- **AI insights:** Random Forest forecast baseline, Isolation Forest anomaly detection and management signals.
- **Business analyst:** interactive question-and-answer experience for sales, products, regions, customer retention, anomalies and forecast.
- **Reports & exports:** downloadable executive summary, transaction dataset and customer dataset CSVs.
- **Health endpoint:** `/api/health`.

## Stack
Python, Flask, SQLite, pandas, scikit-learn, Gunicorn, HTML, CSS, JavaScript and Chart.js.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. On first start the app creates SQLite tables, seeds synthetic demo records and generates `data/transactions.csv`.

Run the integration tests:

```bash
python -m unittest discover -s tests -v
```

GitHub Actions also runs these checks on pushes and pull requests to `main`.

## API endpoints
- `GET /api/health`
- `GET /api/summary`
- `GET /api/monthly`
- `GET /api/regions`
- `GET /api/products`
- `GET /api/sales?start=2025-01-01&end=2025-12-31&region=North&product=Cloud%20Pro`
- `GET /api/customers?risk=high&segment=Enterprise&search=Customer`
- `GET /api/segments`
- `GET /api/forecast`
- `GET /api/anomalies`
- `GET /api/insights`
- `POST /api/ask` with JSON such as `{"question":"Which customers are at risk?"}`
- `GET /api/reports/summary.csv`
- `GET /api/reports/transactions.csv`
- `GET /api/reports/customers.csv`

## Deploy on Render
The repository includes `render.yaml`. Open the [Render Blueprint deployment](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FPremRaj2420%2FNEXUS-Enterprise-Decision-Intelligence), authorize repository access, review the service and apply. Or create a Web Service with:

- Build: `pip install -r requirements.txt`
- Start: `gunicorn --bind 0.0.0.0:$PORT app:app`
- Health check: `/api/health`

If your Render service is already connected to this GitHub repository, check its Events/Deploys page for the latest commit and wait for the deployment to finish before presenting. A failed deploy must be fixed in the Render logs before the live URL can work.

## Power BI / Tableau
Run the app locally once and import `data/transactions.csv` into Power BI or Tableau. Suggested charts: revenue/profit trend, regional performance, product profitability, and customer segments.

## Important limitations
This is a demonstration using **synthetic data**. The forecast is a baseline model without backtesting. The assistant uses transparent rule-based response templates and SQL summaries; it is **not connected to an external LLM** and it does not prove causal explanations. Anomaly results need manual validation. Render's free services may spin down and local filesystem data is not guaranteed to persist, so this demo reseeds records when database tables are empty. Do not use it for real business decisions without proper data validation, model evaluation and persistent storage.
