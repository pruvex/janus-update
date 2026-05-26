"""
Extract skill test logs from Supabase for forensic analysis.
"""
import os
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import subprocess

# Load .env file
load_dotenv("backend/.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def check_backend_logs():
    """Check backend terminal logs for D18 batch test output."""
    try:
        # Get backend logs from the running process
        result = subprocess.run(
            ["powershell", "-Command", "Get-Content \"$env:USERPROFILE\\AppData\\Roaming\\Janus Projekt\\logs\\janus_backend.log\" -Tail 200"],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        print("\n=== Backend Logs (last 200 lines) ===\n")
        
        # Filter for D18 batch test and filesystem.list_directory
        relevant_lines = []
        for line in logs.split('\n'):
            if 'D18' in line or 'filesystem.list_directory' in line or 'key_exists' in line:
                relevant_lines.append(line)
        
        if relevant_lines:
            print("\n=== D18 Relevant Logs ===\n")
            for line in relevant_lines[-50:]:  # Last 50 relevant lines
                print(line)
        else:
            print("No D18 or filesystem.list_directory logs found")
        
        return relevant_lines
    except Exception as e:
        print(f"ERROR: Failed to read backend logs: {e}")
        return []

def query_skill_logs(skill_id="filesystem.list_directory", limit=5):
    """Query logs_raw for specific skill test events."""
    
    # Query specifically for the skill
    url = f"{SUPABASE_URL}/rest/v1/logs_raw"
    params = {
        "skill": f"eq.{skill_id}",
        "order": "timestamp.desc",
        "limit": str(limit)
    }
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: Query failed with status {response.status_code}")
        print(response.text)
        return None
    
    logs = response.json()
    print(f"\n=== Found {len(logs)} logs for {skill_id} ===\n")
    
    if logs:
        for i, log in enumerate(logs):
            print(f"\n--- Log #{i+1} ---")
            print(f"ID: {log.get('id')}")
            print(f"Timestamp: {log.get('timestamp')}")
            print(f"Trace ID: {log.get('trace_id')}")
            print(f"Status: {log.get('status')}")
            print(f"Event Type: {log.get('event_type')}")
            print(f"Test Type: {log.get('payload', {}).get('test_type')}")
            
            # Extract and pretty-print full payload
            payload = log.get('payload')
            if payload:
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except:
                        pass
                print(f"\n=== FULL PAYLOAD ===")
                print(json.dumps(payload, indent=2, default=str))
            else:
                print("No payload found")
                
            # Show all fields in the log
            print(f"\n=== ALL FIELDS ===")
            for key, value in log.items():
                if key != 'payload':
                    print(f"{key}: {value}")
    else:
        print("No logs found for this skill")
    
    return logs

if __name__ == "__main__":
    # Check backend logs first (more likely to have recent test output)
    check_backend_logs()
    
    # Also try Supabase query
    logs = query_skill_logs("filesystem.list_directory", limit=5)
