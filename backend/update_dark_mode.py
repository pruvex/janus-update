import sys
sys.path.insert(0, '.')
from data.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("UPDATE users SET dark_mode_enabled = 0 WHERE id = 1"))
    conn.commit()
    print("Updated dark_mode_enabled to 0")
    
    # Verify
    result = conn.execute(text("SELECT dark_mode_enabled FROM users WHERE id = 1"))
    row = result.fetchone()
    if row:
        print(f"Verified dark_mode_enabled: {row[0]}")
