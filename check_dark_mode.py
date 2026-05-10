import sys
sys.path.insert(0, 'backend')
from data.database import get_db
from data.models import User

db = next(get_db())
row = db.query(User).first()

if row:
    print(f"User found: {row.username}")
    print(f"dark_mode_enabled: {row.dark_mode_enabled}")
    print(f"Type: {type(row.dark_mode_enabled)}")
else:
    print("No user row found")
