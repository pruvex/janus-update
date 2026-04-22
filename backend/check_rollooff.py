import sqlite3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.paths import get_app_data_dir

db_path = os.path.join(get_app_data_dir(), "knowledge_index_v2.db")
print(f"Checking database at: {db_path}")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check what tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables in database: {[t[0] for t in tables]}")

# Check for rollooff.pdf in each table
for table in tables:
    table_name = table[0]
    try:
        cursor.execute(f"SELECT * FROM {table_name} WHERE path LIKE '%rollooff%'")
        results = cursor.fetchall()
        if results:
            print(f"\nFound {len(results)} entries for 'rollooff' in table '{table_name}':")
            for row in results:
                print(row)
    except Exception as e:
        print(f"Error querying table '{table_name}': {e}")

# Also check all files to see what's indexed (if indexed_files table exists)
if any(t[0] == 'indexed_files' for t in tables):
    cursor.execute("SELECT COUNT(*) FROM indexed_files")
    total_files = cursor.fetchone()[0]
    print(f"\nTotal files in index: {total_files}")

    # List first 10 files
    cursor.execute("SELECT path FROM indexed_files LIMIT 10")
    first_10 = cursor.fetchall()
    print("\nFirst 10 indexed files:")
    for row in first_10:
        print(row[0])

conn.close()
