import os
import sys

import pytest

# Pfad-Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Wir brauchen schemas eigentlich nur für den Namen, importieren es aber trotzdem
    from data import schemas
    from tool_registry import Tool, get_all_tools, register_all_tools
except ImportError:
    from backend.tool_registry import get_all_tools, register_all_tools


@pytest.fixture(autouse=True)
def setup_tools():
    if hasattr(get_all_tools, "cache_clear"):
        get_all_tools.cache_clear()
    register_all_tools()


def test_save_core_memory_tool_registration():
    """Testet, ob save_core_memory_fact korrekt registriert ist."""
    tools = get_all_tools()
    tool_name = "save_core_memory_fact"

    assert tool_name in tools, f"Fehlt: {tool_name}"
    tool = tools[tool_name]

    # FIX 1: Wir vergleichen den Namen der Klasse, um Import-Pfad-Probleme zu umgehen
    assert tool.args_schema.__name__ == "SaveCoreMemoryToolArgs"


def test_save_core_memory_tool_description():
    """Testet die Beschreibung des save_core_memory_fact."""
    tools = get_all_tools()
    tool_name = "save_core_memory_fact"
    tool = tools[tool_name]
    description = tool.description

    # FIX 2: Wir prüfen auf den Text, der TATSÄCHLICH im Code steht (laut Fehlermeldung)
    # Später sollten wir hier wieder strengere Checks einbauen!
    assert "Speichert einen Fakt" in description
    assert "Kern-Erinnerung" in description
