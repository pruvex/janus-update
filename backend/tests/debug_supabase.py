#!/usr/bin/env python3
"""
Isolated Supabase Client Test
Tests direct upload to Supabase without Queue/Worker
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.services.logging.supabase_client import (
    get_supabase_client,
    SupabaseClientSingleton,
)
from backend.data.schemas_logging import LogEventCreate
from datetime import datetime
import uuid


def test_direct_supabase_upload():
    """Test direct Supabase upload without Queue"""
    print("=" * 60)
    print("ISOLATED SUPABASE CLIENT TEST")
    print("=" * 60)

    # Reset client to ensure fresh connection
    SupabaseClientSingleton.reset()

    # Get Supabase client
    try:
        client = get_supabase_client()
        print("[1/4] Supabase client initialized: ✅")
    except Exception as e:
        print(f"[1/4] Supabase client failed: ❌")
        print(f"   Error: {e}")
        return

    # Create test event
    test_event = LogEventCreate(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        session_id="debug_test_123",
        provider="test",
        model="debug",
        skill="debug_supabase",
        event_type="direct_test",
        status="success",
        payload={"message": "Isolated Supabase test"},
        latency_ms=0,
        trace_id=str(uuid.uuid4()),
    )
    print("[2/4] Test event created: ✅")

    # Direct upload attempt
    try:
        response = client.table("logs_raw").insert(test_event.model_dump(mode='json')).execute()
        print("[3/4] Direct upload attempt: ✅")
        print(f"   Response data: {response.data}")
    except Exception as e:
        print("[3/4] Direct upload attempt: ❌")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return

    # Verify upload by querying
    try:
        query = (
            client.table("logs_raw")
            .select("*")
            .eq("session_id", "debug_test_123")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        print("[4/4] Upload verification: ✅")
        print(f"   Found {len(query.data)} records")
        if query.data:
            print(f"   Latest record: {query.data[0]['id']}")
    except Exception as e:
        print("[4/4] Upload verification: ❌")
        print(f"   Error: {e}")

    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_direct_supabase_upload()
