from unittest.mock import patch

import pytest

from backend.llm_providers.shared.tool_call_adapter import ToolCallAdapter, get_tool_call_adapter
from backend.services.tool_manager import ToolManager


async def _adapter_test_tool():
    return {"status": "ok"}


def test_openai_outbound_replaces_dots_with_underscores():
    adapter = get_tool_call_adapter("openai")
    assert adapter.outbound_name("system.websearch") == "system_websearch"
    assert adapter.outbound_name("filesystem.list_directory") == "filesystem_list_directory"


def test_tool_manager_keeps_canonical_dotted_names():
    manager = ToolManager()
    manager.register_tool(_adapter_test_tool, name="system.websearch")

    definitions = manager.get_tool_definitions(["system.websearch"])

    assert definitions[0]["function"]["name"] == "system.websearch"


def test_gemini_outbound_sanitizes_provider_unsafe_names():
    adapter = get_tool_call_adapter("gemini")
    assert adapter.outbound_name("system.websearch") == "system_websearch"
    assert adapter.outbound_name("calendar.create-event") == "calendar_create_event"


def test_gemini_inbound_restores_manual_provider_safe_names():
    adapter = get_tool_call_adapter("gemini")
    assert adapter.inbound_name("system_websearch") == "system.websearch"
    assert adapter.inbound_name("system_routing") == "system.routing"


def test_openai_inbound_restores_underscore_names_to_canonical_skill_ids():
    adapter = get_tool_call_adapter("openai")
    with patch(
        "backend.services.tool_manager.tool_manager.get_skill_mapping",
        return_value={"list_directory": "filesystem.list_directory"},
    ):
        assert adapter.inbound_name("filesystem_list_directory") == "filesystem.list_directory"


def test_gemini_inbound_preserves_canonical_dotted_name():
    adapter = get_tool_call_adapter("gemini")
    assert adapter.inbound_name("calendar.create_event") == "calendar.create_event"


def test_gemini_history_outbound_uses_provider_safe_name():
    adapter = get_tool_call_adapter("gemini")
    assert adapter.outbound_name_for_history("calendar.create_event") == "calendar_create_event"


def test_openai_schema_sanitization_resolves_defs_refs():
    adapter = get_tool_call_adapter("openrouter")
    sanitized = adapter.sanitize_tool_schema(
        {
            "type": "object",
            "properties": {
                "category": {"$ref": "#/$defs/MemoryCategory"},
                "text": {"type": "string"},
            },
            "required": ["text"],
            "$defs": {
                "MemoryCategory": {
                    "type": "string",
                    "enum": ["ALLGEMEIN", "VORLIEBE"],
                }
            },
        }
    )
    assert "$defs" not in sanitized
    assert "$ref" not in str(sanitized)
    assert sanitized["properties"]["category"]["type"] == "string"
    assert sanitized["properties"]["category"]["enum"] == ["ALLGEMEIN", "VORLIEBE"]


def test_openai_schema_sanitization_clamps_to_object_shape():
    adapter = get_tool_call_adapter("openai")
    sanitized = adapter.sanitize_tool_schema(
        {
            "title": "ignored",
            "type": "object",
            "properties": {"query": {"type": "string", "title": "ignored"}},
            "required": ["query"],
        }
    )
    assert sanitized["type"] == "object"
    assert "title" not in sanitized
    assert "query" in sanitized["properties"]


def test_gemini_schema_sanitization_removes_forbidden_fields():
    adapter = get_tool_call_adapter("gemini")
    sanitized = adapter.sanitize_tool_schema(
        {
            "type": "object",
            "properties": {"query": {"type": "string", "format": "email"}},
            "required": ["query"],
            "title": "ignored",
        }
    )
    assert sanitized["type"] == "object"
    assert "title" not in sanitized
    assert "format" not in sanitized["properties"]["query"]


def test_convert_tools_to_openai_format_uses_provider_safe_names():
    adapter = get_tool_call_adapter("openai")
    converted = adapter.convert_tools_to_openai_format(
        [
            {
                "name": "system.websearch",
                "description": "Search the web",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
            }
        ]
    )
    assert converted[0]["function"]["name"] == "system_websearch"


def test_convert_tools_to_openai_format_unwraps_already_openai_shaped_tools():
    adapter = get_tool_call_adapter("openrouter")
    converted = adapter.convert_tools_to_openai_format(
        [
            {
                "type": "function",
                "function": {
                    "name": "system.weather",
                    "description": "Get weather",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                    },
                },
            }
        ]
    )
    assert converted[0]["function"]["name"] == "system_weather"
    assert converted[0]["function"]["description"] == "Get weather"


def test_convert_tools_to_gemini_format_uses_provider_safe_names():
    adapter = get_tool_call_adapter("gemini")
    converted = adapter.convert_tools_to_gemini_format(
        [
            {
                "type": "function",
                "function": {
                    "name": "system.websearch",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                },
            }
        ]
    )
    assert converted[0]["function_declarations"][0]["name"] == "system_websearch"


def test_adapt_openai_stream_params_normalizes_forced_tool_choice():
    adapter = get_tool_call_adapter("openai")
    params = {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "system.websearch",
                    "description": "Search",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
        "tool_choice": {"type": "function", "function": {"name": "system.websearch"}},
    }
    adapter.adapt_openai_stream_params(params)
    assert params["tools"][0]["function"]["name"] == "system_websearch"
    assert params["tool_choice"]["function"]["name"] == "system_websearch"
