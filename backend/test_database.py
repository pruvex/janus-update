import unittest
import os
import sqlite3
from datetime import datetime
from database import init_db, save_cost_entry, get_costs_for_month, get_all_cost_entries, DATABASE_FILE

class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Ensure a clean database for each test
        if os.path.exists(DATABASE_FILE):
            os.remove(DATABASE_FILE)
        init_db()

    def tearDown(self):
        # Clean up the database after each test
        if os.path.exists(DATABASE_FILE):
            os.remove(DATABASE_FILE)

    def test_init_db(self):
        # Test if the database file is created and table exists
        self.assertTrue(os.path.exists(DATABASE_FILE))
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='costs';")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_save_cost_entry(self):
        # Test saving a cost entry
        save_cost_entry(
            date=datetime.now().isoformat(),
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            image_quality=None,
            image_cost=None,
            total_cost=0.01
        )
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM costs;")
        self.assertEqual(len(cursor.fetchall()), 1)
        conn.close()

    def test_get_costs_for_month(self):
        # Test retrieving costs for a specific month
        today = datetime.now()
        save_cost_entry(today.isoformat(), "model1", 100, 50, None, None, 0.01)
        save_cost_entry(today.isoformat(), "model2", 200, 100, None, None, 0.02)
        
        # Add an entry for a different month
        last_month = today.replace(month=today.month - 1 if today.month > 1 else 12, 
                                   year=today.year if today.month > 1 else today.year - 1)
        save_cost_entry(last_month.isoformat(), "model3", 50, 20, None, None, 0.05)

        cost = get_costs_for_month(today.year, today.month)
        self.assertAlmostEqual(cost, 0.03)

    def test_get_all_cost_entries(self):
        # Test retrieving all cost entries
        save_cost_entry(datetime(2025, 1, 1).isoformat(), "modelA", 10, 5, None, None, 0.1)
        save_cost_entry(datetime(2025, 1, 2).isoformat(), "modelB", 20, 10, "hd", 0.5, 0.5)
        
        entries = get_all_cost_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["model"], "modelB") # Ordered by date DESC
        self.assertEqual(entries[1]["model"], "modelA")

if __name__ == '__main__':
    unittest.main()