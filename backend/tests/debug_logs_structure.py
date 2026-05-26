"""
Forensic Table Scan for Debugging Insight Engine.

Scans all tables that sound like 'log' to check:
1. Which tables exist
2. Column names in logs_raw
3. Timestamp column name (created_at vs timestamp)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.logging.supabase_client import get_supabase_client


def main():
    print("=" * 80)
    print("FORENSIC TABLE SCAN — LOG STRUCTURE DEBUG")
    print("=" * 80)
    
    supabase = get_supabase_client()
    
    # List of potential log-related tables
    potential_tables = [
        "logs_raw",
        "logs",
        "logs_insights",
        "events",
        "telemetry",
        "log_events",
        "system_logs"
    ]
    
    print("\nScanning tables...")
    
    for table_name in potential_tables:
        try:
            print(f"\n--- Table: {table_name} ---")
            
            # Try to fetch last 5 records
            response = (
                supabase
                .table(table_name)
                .select("*")
                .limit(5)
                .execute()
            )
            
            if response.data:
                print(f"✅ Table exists: {len(response.data)} records found")
                
                # Show column names
                columns = list(response.data[0].keys())
                print(f"Columns: {columns}")
                
                # Check for timestamp-related columns
                timestamp_columns = [col for col in columns if 'time' in col.lower() or 'date' in col.lower()]
                if timestamp_columns:
                    print(f"Timestamp-related columns: {timestamp_columns}")
                
                # Show first record as example
                print(f"First record: {response.data[0]}")
                
                # Special handling for logs_raw
                if table_name == "logs_raw":
                    print("\n🔍 LOGS_RAW ANALYSIS:")
                    print(f"Column names: {columns}")
                    
                    # Check which timestamp column exists
                    if "timestamp" in columns:
                        print("✅ 'timestamp' column EXISTS")
                    else:
                        print("❌ 'timestamp' column MISSING")
                    
                    if "created_at" in columns:
                        print("✅ 'created_at' column EXISTS")
                    else:
                        print("❌ 'created_at' column MISSING")
                    
                    # Check if there's any timestamp column
                    if timestamp_columns:
                        print(f"⚠️  Found timestamp columns: {timestamp_columns}")
                        print(f"⚠️  InsightEngine currently searches for 'timestamp' column")
                        print(f"⚠️  If logs use '{timestamp_columns[0]}', the query will fail!")
            else:
                print(f"⚠️  Table exists but is empty")
                
        except Exception as e:
            print(f"❌ Table does not exist or error: {e}")
    
    print("\n" + "=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
