import unittest
import os
import sqlite3
from datetime import datetime
from fastapi.testclient import TestClient
from main import app # Assuming 'app' is the FastAPI instance
from database import init_db, save_cost_entry, DATABASE_FILE

class TestCostAPI(unittest.TestCase):

    def setUp(self):
        # Ensure a clean database for each test
        if os.path.exists(DATABASE_FILE):
            os.remove(DATABASE_FILE)
        init_db()
        self.client = TestClient(app)

    def tearDown(self):
        # Clean up the database after each test
        if os.path.exists(DATABASE_FILE):
            os.remove(DATABASE_FILE)

    def test_get_costs_dashboard(self):
        # Add some dummy cost data
        today = datetime.now()
        save_cost_entry(today.isoformat(), "model1", 100, 50, None, None, 0.01)
        save_cost_entry(today.isoformat(), "model2", 200, 100, None, None, 0.02)

        response = self.client.get("/api/costs/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("current_month_cost", data)
        self.assertIn("monthly_budget", data)
        self.assertAlmostEqual(data["current_month_cost"], 0.03)
        self.assertEqual(data["monthly_budget"], 10.00) # Hardcoded in main.py

    def test_get_costs_details(self):
        # Add some dummy cost data
        save_cost_entry(datetime(2025, 1, 1).isoformat(), "modelA", 10, 5, None, None, 0.1)
        save_cost_entry(datetime(2025, 1, 2).isoformat(), "modelB", 20, 10, "hd", 0.5, 0.5)

        response = self.client.get("/api/costs/details")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["model"], "modelB") # Ordered by date DESC
        self.assertAlmostEqual(data[0]["total_cost"], 0.5)
        self.assertEqual(data[1]["model"], "modelA")
        self.assertAlmostEqual(data[1]["total_cost"], 0.1)

    def test_get_costs_dashboard_no_data(self):
        # Test dashboard when no data is present
        response = self.client.get("/api/costs/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertAlmostEqual(data["current_month_cost"], 0.0)

    def test_get_costs_details_no_data(self):
        # Test details when no data is present
        response = self.client.get("/api/costs/details")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 0)

if __name__ == '__main__':
    unittest.main()