import csv
import random
import sqlite3
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
DB = BASE / "nexus.db"
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)

random.seed(42)
regions = ["North", "South", "East", "West", "Central"]
products = [
    ("Analytics Suite", "Software"),
    ("Cloud Pro", "Software"),
    ("Security Hub", "Software"),
    ("Data Platform", "Software"),
    ("Support Plus", "Service"),
    ("Consulting", "Service"),
]
customers = [f"Customer {i:03d}" for i in range(1, 81)]
segments = ["Enterprise", "SMB", "Mid-Market"]
start = date(2025, 1, 1)
prices = {
    "Analytics Suite": 1800,
    "Cloud Pro": 2400,
    "Security Hub": 2100,
    "Data Platform": 3200,
    "Support Plus": 900,
    "Consulting": 3500,
}

transactions = []
for _ in range(900):
    order_date = start.fromordinal(start.toordinal() + random.randint(0, 364))
    region = random.choice(regions)
    product, category = random.choice(products)
    customer = random.choice(customers)
    quantity = random.randint(1, 12)
    revenue = quantity * prices[product] * random.uniform(0.75, 1.25)
    cost = revenue * random.uniform(0.52, 0.78)
    transactions.append((
        order_date.isoformat(), region, product, customer, category,
        quantity, round(revenue, 2), round(cost, 2), round(revenue - cost, 2)
    ))

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("DELETE FROM transactions")
cur.executemany("""
    INSERT INTO transactions
    (date, region, product, customer, category, quantity, revenue, cost, profit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", transactions)

cur.execute("DELETE FROM customers")
for customer_id, customer in enumerate(customers, 1):
    segment = random.choice(segments)
    region = random.choice(regions)
    orders = random.randint(2, 30)
    revenue = round(random.uniform(8000, 150000), 2)
    satisfaction = round(random.uniform(2.8, 5.0), 1)
    churn_risk = min(99, max(3, round(
        70 - (satisfaction - 3) * 18 + random.uniform(-18, 18), 1
    )))
    cur.execute("""
        INSERT INTO customers
        (id, customer, segment, region, orders, revenue, satisfaction, churn_risk)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_id, customer, segment, region, orders,
        revenue, satisfaction, churn_risk
    ))

conn.commit()
conn.close()

with (DATA_DIR / "transactions.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow([
        "date", "region", "product", "customer", "category",
        "quantity", "revenue", "cost", "profit"
    ])
    writer.writerows(transactions)

(BASE / ".seeded").write_text("ok", encoding="utf-8")
print("NEXUS database and CSV data seeded.")
