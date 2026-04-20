import os
import sys

import pytest

# Pfad-Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tool_registry import get_all_tools, register_all_tools


@pytest.fixture(autouse=True)
def setup_tools():
    if hasattr(get_all_tools, "cache_clear"):
        get_all_tools.cache_clear()
    register_all_tools()


def test_memory_write_tool_registration():
    """Testet, ob memory_write (V2.1 Gold Standard) korrekt registriert ist."""
    tools = get_all_tools()
    tool_name = "memory_write"

    assert tool_name in tools, f"Fehlt: {tool_name}"
    tool = tools[tool_name]

    assert tool.args_schema.__name__ == "MemoryWriteArgs"


def test_memory_write_tool_description():
    """Testet die Beschreibung des memory_write Tools."""
    tools = get_all_tools()
    tool_name = "memory_write"
    tool = tools[tool_name]
    description = tool.description

    assert "Speichert einen Fakt" in description
    assert "Langzeitgedächtnis" in description


def test_memory_read_tool_registration():
    """Testet, ob memory_read (V2.1 Gold Standard) korrekt registriert ist."""
    tools = get_all_tools()
    tool_name = "memory_read"

    assert tool_name in tools, f"Fehlt: {tool_name}"
    tool = tools[tool_name]

    assert tool.args_schema.__name__ == "MemoryReadArgs"


def test_legacy_tools_not_registered():
    """Sicherstellen, dass alte Memory-Tools NICHT mehr registriert sind."""
    tools = get_all_tools()
    assert "save_core_memory_fact" not in tools, "Legacy save_core_memory_fact darf nicht registriert sein!"
    assert "search_past_conversation_summaries_tool" not in tools, "Legacy search tool darf nicht registriert sein!"
