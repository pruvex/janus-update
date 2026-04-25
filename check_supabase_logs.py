"""
Check Supabase logs for provider and model fields.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, "c:\\KI\\Janus-Projekt")

from supabase import create_client

# Supabase credentials from .env
SUPABASE_URL = "https://loyezwlrucjgmemjrrwx.supabase.co"
SUPABASE_KEY = "sb_publishable_vXa0UAx1erE9Gqni7uNiDA_pMq4q5aQ"

# Create Supabase client
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Query logs_raw table for recent logs with session_id = 999999
response = client.table("logs_raw").select("*").eq("session_id", "999999").limit(10).execute()

print(f"Found {len(response.data)} logs for session_id = 999999")
print("\n=== RECENT LOGS ===")
for log in response.data:
    print(f"\n--- Log ID: {log.get('id')} ---")
    print(f"session_id: {log.get('session_id')}")
    print(f"provider: {log.get('provider')}")
    print(f"model: {log.get('model')}")
    print(f"skill: {log.get('skill')}")
    print(f"event_type: {log.get('event_type')}")
    print(f"status: {log.get('status')}")
    print(f"created_at: {log.get('created_at')}")
    print(f"payload: {log.get('payload')}")

# Check if provider and model are NOT 'unknown'
print("\n=== VERIFICATION ===")
if response.data:
    for log in response.data:
        provider = log.get('provider')
        model = log.get('model')
        if provider and provider != 'unknown':
            print(f"✓ provider is correctly set: {provider}")
        else:
            print(f"✗ provider is 'unknown' or missing")
        
        if model and model != 'unknown':
            print(f"✓ model is correctly set: {model}")
        else:
            print(f"✗ model is 'unknown' or missing")
else:
    print("No logs found for session_id = 999999")
