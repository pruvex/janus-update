"""
Test script to verify that provider and model are correctly logged
when a tool throws an error.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, "c:\\KI\\Janus-Projekt")

from backend.tools.weather_service import get_weather_from_api_tool
from backend.services.tool_executor import ToolExecutor
from backend.data.database import SessionLocal
import asyncio

async def test_weather_error_logging():
    """Test weather tool with invalid city to trigger error and check logging."""
    
    # Create a ToolExecutor with provider and model in additional_context
    db = SessionLocal()
    executor = ToolExecutor(
        db=db,
        api_key="test-key",
        provider="openai",
        model="gpt-4o-mini",
        additional_context={
            "chat_id": 999999,
            "provider": "openai",
            "model": "gpt-4o-mini",
        }
    )
    
    # Call weather tool with invalid city to trigger error
    # Use execute_tool_calls (plural) to trigger logging in _execute_with_logging
    tool_calls = [
        {
            "id": "test-call-1",
            "type": "function",
            "function": {
                "name": "system.weather",
                "arguments": '{"city": "nichtexistenteStadt123456"}'
            }
        }
    ]
    
    results = await executor.execute_tool_calls(tool_calls)
    
    print("Results:", results)
    print("\n=== CHECK SUPABASE LOGS ===")
    print("Check the logs_raw table in Supabase for:")
    print("- session_id: 999999")
    print("- provider: should be 'openai' (not 'unknown')")
    print("- model: should be 'gpt-4o-mini' (not 'unknown')")
    print("- skill: 'system.weather'")
    print("- event_type: 'tool_start' and 'tool_end'")
    print("- status: 'error' (because city doesn't exist)")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_weather_error_logging())
