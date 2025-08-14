import sqlite3
import os
from datetime import datetime

DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "costs.db")

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            image_quality TEXT,
            image_cost REAL,
            total_cost REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")

def save_cost_entry(date: str, model: str, input_tokens: int, output_tokens: int, image_quality: str, image_cost: float, total_cost: float):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO costs (date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost))
    conn.commit()
    conn.close()
    

def get_costs_for_month(year: int, month: int) -> float:
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # Query to sum total_cost for the given month and year
    cursor.execute("""
        SELECT SUM(total_cost) FROM costs
        WHERE STRFTIME('%Y', date) = ? AND STRFTIME('%m', date) = ?
    """, (str(year), f"{month:02d}"))
    total_cost = cursor.fetchone()[0]
    conn.close()
    return total_cost if total_cost is not None else 0.0

def get_all_cost_entries():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, model, input_tokens, output_tokens, image_quality, image_cost, total_cost
        FROM costs
        ORDER BY date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    
    # Convert rows to a list of dictionaries for easier processing
    results = []
    for row in rows:
        results.append({
            "date": row[0],
            "model": row[1],
            "input_tokens": row[2],
            "output_tokens": row[3],
            "image_quality": row[4],
            "image_cost": row[5],
            "total_cost": row[6]
        })
    return results
