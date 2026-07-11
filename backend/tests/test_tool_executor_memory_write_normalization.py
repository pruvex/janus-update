import json
from unittest.mock import MagicMock

import pytest

from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import tool_manager


@pytest.mark.asyncio
async def test_memory_write_normalizes_query_legacy_field_before_validation(
    monkeypatch, assert_skill_response_contract
):
    captured = {}

    async def _fake_memory_write(**kwargs):
        captured.update(kwargs)
        return {
            "status": "ok",
            "data": {
                "operation": "saved",
                "memory_id": 123,
            },
        }

    tool_def = tool_manager.get_tool("memory.write")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_memory_write)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="gemini",
        model="gemini-3-flash-preview",
    )

    result = await executor.execute_tool_call(
        "memory.write",
        {
            "query": "Nathans Freundin heißt Elena.",
            "tags": ["Nathan", "Elena", "Beziehung"],
            "priority": 0.6,
        },
    )
    payload = json.loads(result["content"])

    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert captured["fact"] == "Nathans Freundin heißt Elena."
    assert captured["category"] == "Allgemein"
    assert captured["priority_override"] == 0.6
    assert captured["tags"] == ["Nathan", "Elena", "Beziehung"]


@pytest.mark.asyncio
async def test_memory_write_derives_subject_and_category_from_key_value_legacy_shape(
    monkeypatch, assert_skill_response_contract
):
    captured = {}

    async def _fake_memory_write(**kwargs):
        captured.update(kwargs)
        return {
            "status": "ok",
            "data": {
                "operation": "saved",
                "memory_id": 124,
            },
        }

    tool_def = tool_manager.get_tool("memory.write")
    assert tool_def is not None
    monkeypatch.setattr(tool_def, "func", _fake_memory_write)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="gemini",
        model="gemini-3-flash-preview",
    )

    result = await executor.execute_tool_call(
        "memory.write",
        {
            "key": "Beziehungen_Milan",
            "value": "Milans Freundin heißt Sina.",
        },
    )
    payload = json.loads(result["content"])

    assert_skill_response_contract(payload)
    assert payload["status"] == "ok"
    assert captured["fact"] == "Milans Freundin heißt Sina."
    assert captured["category"] == "Beziehungen"
    assert captured["subject_name"] == "Milan"
