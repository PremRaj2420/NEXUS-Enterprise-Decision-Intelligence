from flask import Flask, render_template, jsonify, request, Response
import csv
import io
import os
import sqlite3
import subprocess
import sys
from datetime import date
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("NEXUS_DB_PATH", os.path.join(BASE, "nexus.db"))
app = Flask(__name__)


def db():
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY,
      date TEXT NOT NULL,
      region TEXT NOT NULL,
      product TEXT NOT NULL,
      customer TEXT NOT NULL,
      category TEXT NOT NULL,
      quantity INTEGER NOT NULL,
      revenue REAL NOT NULL,
      cost REAL NOT NULL,
      profit REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS customers (
      id INTEGER PRIMARY KEY,
      customer TEXT NOT NULL,
      segment TEXT NOT NULL,
      region TEXT NOT NULL,
      orders INTEGER NOT NULL,
      revenue REAL NOT NULL,
      satisfaction REAL NOT NULL,
      churn_risk REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
    CREATE INDEX IF NOT EXISTS idx_transactions_region ON transactions(region);
    CREATE INDEX IF NOT EXISTS idx_transactions_product ON transactions(product);
    CREATE INDEX IF NOT EXISTS idx_customers_risk ON customers(churn_risk);
    """)
    conn.commit()
    conn.close()


def query(sql, args=()):
    conn = db()
    try:
        rows = conn.execute(sql, args).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def scalar(sql, args=()):
    conn = db()
    try:
        value = conn.execute(sql, args).fetchone()[0]
        return value if value is not None else 0
    finally:
        conn.close()


def transactions_where(args_map=None):
    args_map = args_map or {}
    clauses = []
    params = []
    start = args_map.get("start", "")
    end = args_map.get("end", "")
    region = args_map.get("region", "")
    product = args_map.get("product", "")
    if start:
        clauses.append("date >= ?")
        params.append(start)
    if end:
        clauses.append("date <= ?")
        params.append(end)
    if region and region != "All":
        clauses.append("region = ?")
        params.append(region)
    if product and product != "All":
        clauses.append("product = ?")
        params.append(product)
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


def safe_csv(filename, headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=" + filename}
    )


def forecast_data():
    rows = query("""
        SELECT substr(date, 1, 7) AS month, ROUND(SUM(revenue), 2) AS revenue
        FROM transactions GROUP BY month ORDER BY month
    """)
    if len(rows) < 4:
        return {"months": [], "values": [], "method": "Insufficient history"}
    df = pd.DataFrame(rows)
    df["x"] = range(len(df))
    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(df[["x"]], df["revenue"])
    future = [len(df) + i for i in range(1, 4)]
    predictions = model.predict(pd.DataFrame({"x": future}))
    return {
        "months": ["Next period", "Period +2", "Period +3"],
        "values": [round(float(value), 2) for value in predictions],
        "method": "Random Forest baseline"
    }


def anomaly_data():
    rows = query("SELECT id, date, region, product, revenue, profit FROM transactions")
    if len(rows) < 10:
        return []
    df = pd.DataFrame(rows)
    model = IsolationForest(contamination=0.05, random_state=42)
    df["flag"] = model.fit_predict(df[["revenue", "profit"]])
    outliers = df[df["flag"] == -1].sort_values("revenue", ascending=False).head(15)
    return outliers.drop(columns=["flag"]).to_dict("records")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "app": "NEXUS", "database": "connected"})


@app.route("/api/summary")
def summary():
    revenue = scalar("SELECT SUM(revenue) FROM transactions")
    profit = scalar("SELECT SUM(profit) FROM transactions")
    orders = scalar("SELECT COUNT(*) FROM transactions")
    customer_count = scalar("SELECT COUNT(*) FROM customers")
    return jsonify({
        "revenue": round(float(revenue), 2),
        "profit": round(float(profit), 2),
        "orders": int(orders),
        "customers": int(customer_count),
        "margin": round((profit / revenue * 100) if revenue else 0, 2),
        "avg_order_value": round((revenue / orders) if orders else 0, 2),
        "high_risk_customers": int(scalar("SELECT COUNT(*) FROM customers WHERE churn_risk >= 70"))
    })


@app.route("/api/monthly")
def monthly():
    return jsonify(query("""
        SELECT substr(date, 1, 7) AS month,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit,
               COUNT(*) AS orders
        FROM transactions
        GROUP BY month ORDER BY month
    """))


@app.route("/api/regions")
def regions():
    return jsonify(query("""
        SELECT region, ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit, COUNT(*) AS orders
        FROM transactions GROUP BY region ORDER BY revenue DESC
    """))


@app.route("/api/products")
def products():
    return jsonify(query("""
        SELECT product, category, ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit, SUM(quantity) AS quantity,
               ROUND(SUM(profit) * 100.0 / NULLIF(SUM(revenue), 0), 2) AS margin
        FROM transactions GROUP BY product, category ORDER BY revenue DESC
    """))


@app.route("/api/sales")
def sales():
    where, params = transactions_where(request.args)
    trend = query("""
        SELECT substr(date, 1, 7) AS month,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit, COUNT(*) AS orders
        FROM transactions""" + where + """
        GROUP BY month ORDER BY month
    """, params)
    by_region = query("""
        SELECT region, ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit, COUNT(*) AS orders
        FROM transactions""" + where + """
        GROUP BY region ORDER BY revenue DESC
    """, params)
    by_product = query("""
        SELECT product, category, ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit, SUM(quantity) AS quantity,
               ROUND(SUM(profit) * 100.0 / NULLIF(SUM(revenue), 0), 2) AS margin
        FROM transactions""" + where + """
        GROUP BY product, category ORDER BY revenue DESC
    """, params)
    totals = query("""
        SELECT ROUND(SUM(revenue), 2) AS revenue, ROUND(SUM(profit), 2) AS profit,
               COUNT(*) AS orders, SUM(quantity) AS units
        FROM transactions""" + where, params)[0]
    return jsonify({"trend": trend, "regions": by_region, "products": by_product, "totals": totals})


@app.route("/api/customers")
def customers():
    clauses = []
    params = []
    risk = request.args.get("risk", "all")
    segment = request.args.get("segment", "All")
    search = request.args.get("search", "").strip()
    if risk == "high":
        clauses.append("churn_risk >= 70")
    elif risk == "medium":
        clauses.append("churn_risk >= 40 AND churn_risk < 70")
    elif risk == "low":
        clauses.append("churn_risk < 40")
    if segment and segment != "All":
        clauses.append("segment = ?")
        params.append(segment)
    if search:
        clauses.append("(customer LIKE ? OR region LIKE ?)")
        params.extend(["%" + search + "%", "%" + search + "%"])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = query("""
        SELECT customer, segment, region, orders,
               ROUND(revenue, 2) AS revenue,
               ROUND(satisfaction, 1) AS satisfaction,
               ROUND(churn_risk, 1) AS churn_risk
        FROM customers""" + where + """
        ORDER BY churn_risk DESC, revenue DESC LIMIT 100
    """, params)
    return jsonify(rows)


@app.route("/api/segments")
def segments():
    return jsonify(query("""
        SELECT segment, COUNT(*) AS customers, ROUND(SUM(revenue), 2) AS revenue,
               ROUND(AVG(satisfaction), 2) AS avg_satisfaction,
               ROUND(AVG(churn_risk), 2) AS avg_churn_risk
        FROM customers GROUP BY segment ORDER BY revenue DESC
    """))


@app.route("/api/forecast")
def forecast():
    return jsonify(forecast_data())


@app.route("/api/anomalies")
def anomalies():
    return jsonify(anomaly_data())


@app.route("/api/insights")
def insights():
    summary_data = summary().get_json()
    top_region = query("""
        SELECT region, ROUND(SUM(revenue), 2) AS revenue
        FROM transactions GROUP BY region ORDER BY revenue DESC LIMIT 1
    """)
    low_region = query("""
        SELECT region, ROUND(SUM(revenue), 2) AS revenue
        FROM transactions GROUP BY region ORDER BY revenue ASC LIMIT 1
    """)
    top_product = query("""
        SELECT product, ROUND(SUM(profit), 2) AS profit
        FROM transactions GROUP BY product ORDER BY profit DESC LIMIT 1
    """)
    forecast_result = forecast_data()
    high_risk = summary_data["high_risk_customers"]
    items = [
        {"type": "positive", "title": "Revenue leader", "detail": "{} leads with {} in revenue.".format(top_region[0]["region"], round(top_region[0]["revenue"]))},
        {"type": "attention", "title": "Improvement opportunity", "detail": "{} has the lowest regional revenue in this demo dataset.".format(low_region[0]["region"])},
        {"type": "positive", "title": "Profit contributor", "detail": "{} has the highest total profit.".format(top_product[0]["product"])},
        {"type": "attention" if high_risk else "positive", "title": "Customer retention", "detail": "{} customers currently have a churn-risk score of 70 or above.".format(high_risk)},
        {"type": "neutral", "title": "Forecast note", "detail": "A Random Forest baseline estimates the next three periods. Treat it as a prototype, not a validated business forecast."}
    ]
    return jsonify({"insights": items, "forecast": forecast_result, "anomalies": anomaly_data()[:10]})


@app.route("/api/ask", methods=["POST"])
def ask():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip().lower()
    if not question:
        return jsonify({"answer": "Enter a question about revenue, profit, sales, regions, products, or customer churn."}), 400

    total_revenue = scalar("SELECT SUM(revenue) FROM transactions")
    total_profit = scalar("SELECT SUM(profit) FROM transactions")
    total_orders = scalar("SELECT COUNT(*) FROM transactions")
    top_region = query("SELECT region, SUM(revenue) AS revenue FROM transactions GROUP BY region ORDER BY revenue DESC LIMIT 1")
    low_region = query("SELECT region, SUM(revenue) AS revenue FROM transactions GROUP BY region ORDER BY revenue ASC LIMIT 1")
    top_product = query("SELECT product, SUM(profit) AS profit FROM transactions GROUP BY product ORDER BY profit DESC LIMIT 1")
    top_revenue_product = query("SELECT product, SUM(revenue) AS revenue FROM transactions GROUP BY product ORDER BY revenue DESC LIMIT 1")
    high_risk = scalar("SELECT COUNT(*) FROM customers WHERE churn_risk >= 70")
    average_satisfaction = scalar("SELECT AVG(satisfaction) FROM customers")
    anomalies = anomaly_data()

    if "churn" in question or "customer" in question or "retention" in question:
        customers_at_risk = query("""
            SELECT customer, segment, region, ROUND(revenue, 0) AS revenue,
                   ROUND(satisfaction, 1) AS satisfaction, ROUND(churn_risk, 1) AS churn_risk
            FROM customers WHERE churn_risk >= 70 ORDER BY revenue DESC LIMIT 5
        """)
        names = ", ".join("{} (risk {}%)".format(x["customer"], x["churn_risk"]) for x in customers_at_risk)
        answer = "{} customers are high-risk (score >= 70). Average satisfaction is {:.1f}/5. Start with high-value at-risk accounts: {}. Suggested action: contact the customers, review open support issues, and propose a retention plan.".format(high_risk, average_satisfaction, names or "review the customer-risk table")
    elif "profit" in question or "margin" in question:
        answer = "Total profit is ₹{:,.0f} from {:,} transactions. {} is the highest-profit product (₹{:,.0f}). Compare product margins and investigate cost drivers before changing pricing.".format(total_profit, total_orders, top_product[0]["product"], top_product[0]["profit"])
    elif "region" in question or "geograph" in question:
        answer = "{} is the highest-revenue region (₹{:,.0f}); {} is the lowest (₹{:,.0f}). Compare product mix, sales volume and account coverage before attributing the difference to a cause.".format(top_region[0]["region"], top_region[0]["revenue"], low_region[0]["region"], low_region[0]["revenue"])
    elif "product" in question:
        answer = "{} generates the most revenue (₹{:,.0f}); {} has the highest profit (₹{:,.0f}). Revenue and profitability are different measures, so use both when making product decisions.".format(top_revenue_product[0]["product"], top_revenue_product[0]["revenue"], top_product[0]["product"], top_product[0]["profit"])
    elif "anomal" in question or "unusual" in question or "outlier" in question:
        answer = "The Isolation Forest scan flagged {} transactions for review. These are statistical outliers, not necessarily errors or fraud. Validate each against source transactions and business context.".format(len(anomalies))
    elif "forecast" in question or "predict" in question or "future" in question:
        fc = forecast_data()
        answer = "The Random Forest baseline forecasts {} for the next three periods. Values: {}. This demo has limited features and no backtesting, so treat these values as a prototype signal rather than a reliable forecast.".format(", ".join(fc["months"]), ", ".join("₹{:,.0f}".format(v) for v in fc["values"]))
    elif "why" in question or "revenue" in question or "sales" in question:
        answer = "Recorded revenue is ₹{:,.0f} across {:,} transactions. {} leads regional revenue at ₹{:,.0f}; {} leads product revenue at ₹{:,.0f}. These are associations in synthetic demo data, not proven causes. Drill into monthly trends and mix to validate drivers.".format(total_revenue, total_orders, top_region[0]["region"], top_region[0]["revenue"], top_revenue_product[0]["product"], top_revenue_product[0]["revenue"])
    else:
        answer = "NEXUS reports ₹{:,.0f} revenue, ₹{:,.0f} profit, a {:.1f}% margin, and {} high-risk customers. Ask about sales, regional performance, product profitability, churn, anomalies or forecast.".format(total_revenue, total_profit, (total_profit / total_revenue * 100) if total_revenue else 0, high_risk)
    return jsonify({"answer": answer, "mode": "rule-based demo analyst"})


@app.route("/api/reports/transactions.csv")
def transactions_csv():
    rows = query("""
        SELECT id, date, region, product, customer, category, quantity, revenue, cost, profit
        FROM transactions ORDER BY date, id
    """)
    headers = ["id", "date", "region", "product", "customer", "category", "quantity", "revenue", "cost", "profit"]
    return safe_csv("nexus_transactions.csv", headers, [[row[h] for h in headers] for row in rows])


@app.route("/api/reports/customers.csv")
def customers_csv():
    rows = query("""
        SELECT id, customer, segment, region, orders, revenue, satisfaction, churn_risk
        FROM customers ORDER BY churn_risk DESC
    """)
    headers = ["id", "customer", "segment", "region", "orders", "revenue", "satisfaction", "churn_risk"]
    return safe_csv("nexus_customers.csv", headers, [[row[h] for h in headers] for row in rows])


@app.route("/api/reports/summary.csv")
def summary_csv():
    data = summary().get_json()
    headers = ["metric", "value"]
    rows = [
        ["revenue", data["revenue"]],
        ["profit", data["profit"]],
        ["orders", data["orders"]],
        ["customers", data["customers"]],
        ["profit_margin_percent", data["margin"]],
        ["average_order_value", data["avg_order_value"]],
        ["high_risk_customers", data["high_risk_customers"]]
    ]
    return safe_csv("nexus_executive_summary.csv", headers, rows)


# Render's filesystem can be recreated at deployment/startup. Seed when the tables are empty,
# instead of relying only on a marker file that may not match the database state.
init_db()
if scalar("SELECT COUNT(*) FROM transactions") == 0 or scalar("SELECT COUNT(*) FROM customers") == 0:
    subprocess.run([sys.executable, os.path.join(BASE, "seed.py")], check=True)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )
