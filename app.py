from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import sys
import subprocess
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "nexus.db")
app = Flask(__name__)


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY,
      date TEXT,
      region TEXT,
      product TEXT,
      customer TEXT,
      category TEXT,
      quantity INTEGER,
      revenue REAL,
      cost REAL,
      profit REAL
    );

    CREATE TABLE IF NOT EXISTS customers (
      id INTEGER PRIMARY KEY,
      customer TEXT,
      segment TEXT,
      region TEXT,
      orders INTEGER,
      revenue REAL,
      satisfaction REAL,
      churn_risk REAL
    );
    """)
    conn.commit()
    conn.close()


def query(sql, args=()):
    conn = db()
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def scalar(sql):
    conn = db()
    value = conn.execute(sql).fetchone()[0]
    conn.close()
    return value or 0


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/summary")
def summary():
    revenue = scalar("SELECT SUM(revenue) FROM transactions")
    profit = scalar("SELECT SUM(profit) FROM transactions")
    orders = scalar("SELECT COUNT(*) FROM transactions")
    customers_count = scalar("SELECT COUNT(*) FROM customers")
    return jsonify({
        "revenue": round(revenue, 2),
        "profit": round(profit, 2),
        "orders": orders,
        "customers": customers_count,
        "margin": round((profit / revenue * 100) if revenue else 0, 2)
    })


@app.route("/api/monthly")
def monthly():
    return jsonify(query("""
        SELECT substr(date, 1, 7) AS month,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit
        FROM transactions
        GROUP BY month
        ORDER BY month
    """))


@app.route("/api/regions")
def regions():
    return jsonify(query("""
        SELECT region,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit,
               COUNT(*) AS orders
        FROM transactions
        GROUP BY region
        ORDER BY revenue DESC
    """))


@app.route("/api/products")
def products():
    return jsonify(query("""
        SELECT product, category,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit,
               SUM(quantity) AS quantity
        FROM transactions
        GROUP BY product, category
        ORDER BY revenue DESC
    """))


@app.route("/api/customers")
def customer_analytics():
    return jsonify(query("""
        SELECT customer, segment, region, orders,
               ROUND(revenue, 2) AS revenue,
               ROUND(satisfaction, 1) AS satisfaction,
               ROUND(churn_risk, 1) AS churn_risk
        FROM customers
        ORDER BY churn_risk DESC
        LIMIT 20
    """))


@app.route("/api/forecast")
def forecast():
    rows = query("""
        SELECT substr(date, 1, 7) AS month, SUM(revenue) AS revenue
        FROM transactions
        GROUP BY month
        ORDER BY month
    """)
    df = pd.DataFrame(rows)
    if len(df) < 4:
        return jsonify({"months": [], "values": []})

    df["x"] = range(len(df))
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(df[["x"]], df["revenue"])
    future = [len(df) + i for i in range(1, 4)]
    predictions = model.predict(pd.DataFrame({"x": future}))
    return jsonify({
        "months": [f"Forecast +{i}" for i in range(1, 4)],
        "values": [round(float(value), 2) for value in predictions]
    })


@app.route("/api/anomalies")
def anomalies():
    rows = query("""
        SELECT id, date, region, product, revenue, profit
        FROM transactions
    """)
    df = pd.DataFrame(rows)
    if len(df) < 10:
        return jsonify([])

    model = IsolationForest(contamination=0.05, random_state=42)
    df["flag"] = model.fit_predict(df[["revenue", "profit"]])
    outliers = df[df["flag"] == -1].sort_values(
        "revenue", ascending=False
    ).head(10)
    return jsonify(outliers.drop(columns=["flag"]).to_dict("records"))


@app.route("/api/ask", methods=["POST"])
def ask():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip().lower()
    if not question:
        return jsonify({"answer": "Enter a question about revenue, profit, customers, churn, or regions."})

    total_revenue = scalar("SELECT SUM(revenue) FROM transactions")
    total_profit = scalar("SELECT SUM(profit) FROM transactions")
    top_region = query("""
        SELECT region, SUM(revenue) AS revenue
        FROM transactions
        GROUP BY region
        ORDER BY revenue DESC
        LIMIT 1
    """)
    top_product = query("""
        SELECT product, SUM(profit) AS profit
        FROM transactions
        GROUP BY product
        ORDER BY profit DESC
        LIMIT 1
    """)
    risky_customers = scalar(
        "SELECT COUNT(*) FROM customers WHERE churn_risk >= 70"
    )

    if "revenue" in question and ("why" in question or "performance" in question):
        answer = (
            f"Total revenue is ₹{total_revenue:,.0f}. The strongest region is "
            f"{top_region[0]['region']} with ₹{top_region[0]['revenue']:,.0f}. "
            "Review monthly, regional, and product trends to investigate the drivers."
        )
    elif "profit" in question:
        answer = (
            f"Total profit is ₹{total_profit:,.0f}. "
            f"{top_product[0]['product']} is currently the highest-profit product. "
            "Compare product margins and investigate low-margin offerings."
        )
    elif "churn" in question or "customer" in question:
        answer = (
            f"{risky_customers} customers have a churn-risk score of at least 70. "
            "Prioritize high-value customers for retention outreach and review satisfaction "
            "and order activity."
        )
    elif "region" in question:
        answer = (
            f"The leading region by revenue is {top_region[0]['region']}. "
            "Use Regional Analytics to compare revenue, profit, and order volume."
        )
    else:
        answer = (
            f"NEXUS reports revenue of ₹{total_revenue:,.0f}, profit of "
            f"₹{total_profit:,.0f}, and {risky_customers} high-risk customers. "
            "Ask about revenue, profit, customers, churn, or regions."
        )
    return jsonify({"answer": answer})


if __name__ == "__main__":
    init_db()
    marker = os.path.join(BASE, ".seeded")
    if not os.path.exists(marker):
        subprocess.run([sys.executable, os.path.join(BASE, "seed.py")], check=True)
    app.run(debug=True, port=5000)
