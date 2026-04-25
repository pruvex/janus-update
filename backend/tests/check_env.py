#!/usr/bin/env python3
"""
Isolated Environment Check for Supabase Credentials
Tests if SUPABASE_URL and SUPABASE_KEY are loaded correctly
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("=" * 60)
print("ISOLATED ENVIRONMENT CHECK")
print("=" * 60)

# Check .env file location
env_path = Path(__file__).parent.parent.parent / "backend" / ".env"
print(f"[1/4] .env path: {env_path}")
print(f"       Exists: {env_path.exists()}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path)
print(f"[2/4] Environment loaded from .env")

# Check SUPABASE_URL
supabase_url = os.getenv("SUPABASE_URL")
print(f"[3/4] SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
if supabase_url:
    print(f"       Value: {supabase_url[:50]}..." if len(supabase_url) > 50 else f"       Value: {supabase_url}")
else:
    print(f"       WARNING: SUPABASE_URL is not set!")

# Check SUPABASE_KEY
supabase_key = os.getenv("SUPABASE_KEY")
print(f"[4/4] SUPABASE_KEY: {'SET' if supabase_key else 'NOT SET'}")
if supabase_key:
    print(f"       Length: {len(supabase_key)} chars")
    print(f"       Prefix: {supabase_key[:10]}...")
else:
    print(f"       WARNING: SUPABASE_KEY is not set!")

print("=" * 60)

# Try to initialize Supabase client
print("\nAttempting to initialize Supabase client...")
try:
    from backend.services.logging.supabase_client import get_supabase_client
    client = get_supabase_client()
    print("✅ Supabase client initialized successfully")
except Exception as e:
    print(f"❌ Supabase client failed: {e}")
    print(f"   Error type: {type(e).__name__}")

print("=" * 60)
