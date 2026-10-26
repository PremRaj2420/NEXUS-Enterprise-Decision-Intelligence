import unittest
from app import app


class NexusApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)
        cls.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_home_page_contains_navigation_views(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        for feature in ["Sales analytics", "Customer 360", "AI insights", "Business analyst", "Reports & exports"]:
            self.assertIn(feature, page)

    def test_summary_has_seeded_data(self):
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(data["revenue"], 0)
        self.assertGreater(data["orders"], 0)
        self.assertGreater(data["customers"], 0)
        self.assertIn("high_risk_customers", data)

    def test_sales_filters(self):
        response = self.client.get("/api/sales?region=North&start=2025-01-01&end=2025-12-31")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(data["totals"]["orders"], 0)
        self.assertTrue(all(row["region"] == "North" for row in data["regions"]))

    def test_customer_risk_filter(self):
        response = self.client.get("/api/customers?risk=high")
        self.assertEqual(response.status_code, 200)
        rows = response.get_json()
        self.assertTrue(rows)
        self.assertTrue(all(float(row["churn_risk"]) >= 70 for row in rows))

    def test_segments_endpoint(self):
        response = self.client.get("/api/segments")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.get_json()), 2)

    def test_forecast_endpoint(self):
        response = self.client.get("/api/forecast")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["months"]), 3)
        self.assertEqual(len(data["values"]), 3)
        self.assertTrue(all(float(value) >= 0 for value in data["values"]))

    def test_insights_endpoint(self):
        response = self.client.get("/api/insights")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreaterEqual(len(data["insights"]), 4)
        self.assertIn("anomalies", data)

    def test_business_analyst(self):
        response = self.client.post("/api/ask", json={"question": "Which customers are at risk?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("customers", response.get_json()["answer"].lower())

    def test_empty_business_question_is_validated(self):
        response = self.client.post("/api/ask", json={"question": " "})
        self.assertEqual(response.status_code, 400)

    def test_csv_exports(self):
        for path in [
            "/api/reports/summary.csv",
            "/api/reports/transactions.csv",
            "/api/reports/customers.csv"
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/csv", response.content_type)
                self.assertGreater(len(response.get_data()), 30)


if __name__ == "__main__":
    unittest.main()
