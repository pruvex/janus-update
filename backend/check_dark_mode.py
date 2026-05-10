import sys
sys.path.insert(0, '.')
from data.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT dark_mode_enabled FROM users ORDER BY id LIMIT 1"))
    row = result.fetchone()
    if row:
        print(f"dark_mode_enabled: {row[0]}")
    else:
        print("No user row found")
