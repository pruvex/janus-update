import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.data.models import SkillTelemetry
from backend.services.tool_executor import ToolExecutor


@pytest.mark.asyncio
async def test_executor_executes_local_business_with_skill_response_contract(monkeypatch):
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    monkeypatch.setattr(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value={"text": "- Apotheke Mitte\n- Apotheke Nord", "urls": ["https://example.com/apotheke"]}),
    )
    monkeypatch.setattr(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "- Apotheke Mitte\n- Apotheke Nord"}),
    )
    monkeypatch.setattr("backend.tools.geo_service.asyncio.create_task", lambda *_args, **_kwargs: None)

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-local-business",
                "function": {
                    "name": "system.local_business",
                    "arguments": '{"query":"Apotheke","location":"Berlin Mitte","limit":2}',
                },
            }
        ],
        bypass_policy=False,
    )

    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "ok"
    assert payload["data"]["location"] == "Berlin Mitte"
    assert payload["data"]["result_count"] == 2
    assert payload["error"] is None


@pytest.mark.asyncio
async def test_executor_uses_canonical_local_business_skill_id_for_telemetry(db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    monkeypatch.setattr(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value={"text": "- Pizzeria Centro", "urls": ["https://example.com/pizza"]}),
    )
    monkeypatch.setattr(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "- Pizzeria Centro"}),
    )
    monkeypatch.setattr("backend.tools.geo_service.asyncio.create_task", lambda *_args, **_kwargs: None)

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="gemini",
        model="gemini-2.0-flash",
    )

    await executor.execute_tool_calls(
        [
            {
                "id": "tc-local-business-telemetry",
                "function": {
                    "name": "find_local_business_tool",
                    "arguments": '{"query":"Pizzeria","location":"Köln","limit":1}',
                },
            }
        ],
        bypass_policy=False,
    )

    latest = db_session.query(SkillTelemetry).order_by(SkillTelemetry.id.desc()).first()
    assert latest is not None
    assert latest.skill_id == "system.local_business"
    assert latest.success is True


@pytest.mark.asyncio
async def test_executor_blocks_third_local_business_call_with_rate_limit(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="ollama",
        model="gemma3:12b",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    executor.execute_tool_call = AsyncMock(
        return_value={
            "role": "tool",
            "name": "system.local_business",
            "content": json.dumps({"status": "ok", "data": {"businesses": [], "result_count": 0}, "error": None}),
        }
    )

    results = await executor.execute_tool_calls(
        [
            {"id": "lb-1", "function": {"name": "system.local_business", "arguments": '{"query":"Apotheke","location":"Berlin","limit":1}'}},
            {"id": "lb-2", "function": {"name": "system.local_business", "arguments": '{"query":"Kino","location":"Berlin","limit":1}'}},
            {"id": "lb-3", "function": {"name": "system.local_business", "arguments": '{"query":"Museum","location":"Berlin","limit":1}'}},
        ],
        bypass_policy=False,
    )

    payload = json.loads(results[-1]["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_executor_sanitizes_ollama_local_business_query_from_original_user_text(monkeypatch):
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    captured_queries = []

    async def _fake_find_local_business_tool(**kwargs):
        captured_queries.append({
            "query": kwargs.get("query"),
            "location": kwargs.get("location"),
            "limit": kwargs.get("limit"),
        })
        return {
            "status": "ok",
            "data": {
                "businesses": [],
                "query": kwargs.get("query"),
                "location": kwargs.get("location"),
                "result_count": 0,
            },
            "error": None,
        }

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda _name: MagicMock(name="find_local_business_tool", func=_fake_find_local_business_tool, args_schema=None),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.tool_manager.get_skill_id",
        lambda _name: "system.local_business",
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="ollama",
        model="gemma2:27b@test",
        additional_context={
            "original_user_text": "Finde mir exakt 4 gute italienische Restaurants in Berlin Prenzlauer Berg.",
        },
    )

    result = await executor.execute_tool_call(
        "system.local_business",
        {
            "query": "highly rated italian restaurants",
            "location": "Berlin Prenzlauer Berg",
            "limit": 4,
        },
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    assert captured_queries[0]["query"] == "italienische Restaurants"
    assert captured_queries[0]["location"] == "Berlin Prenzlauer Berg"
    assert payload["data"]["query"] == "italienische Restaurants"
    assert payload["data"]["location"] == "Berlin Prenzlauer Berg"
