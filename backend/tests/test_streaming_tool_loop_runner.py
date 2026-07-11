from pathlib import Path

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.services.orchestrator import execution_engine as ee_module
from backend.services.orchestrator.schemas import OrchestratorContext
from backend.services.orchestrator.stream_protocol import StreamEvent


def test_should_route_stream_tool_round_via_gateway_flag_off(monkeypatch):
    monkeypatch.setattr(ee_module, "TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", False)
    assert (
        ee_module._should_route_stream_tool_round_via_gateway(
            had_tool_round=True,
            provider="openai",
        )
        is False
    )


def test_should_route_stream_tool_round_via_gateway_flag_on(monkeypatch):
    monkeypatch.setattr(ee_module, "TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", True)
    assert (
        ee_module._should_route_stream_tool_round_via_gateway(
            had_tool_round=True,
            provider="openai",
        )
        is True
    )
    assert (
        ee_module._should_route_stream_tool_round_via_gateway(
            had_tool_round=False,
            provider="openai",
        )
        is False
    )
    assert (
        ee_module._should_route_stream_tool_round_via_gateway(
            had_tool_round=True,
            provider="ollama",
        )
        is False
    )


def test_build_stream_gateway_handoff_kwargs_strips_stream_only_fields():
    kwargs = ee_module._build_stream_gateway_handoff_kwargs(
        {
            "provider": "openai",
            "model": "gpt-5.4",
            "forced_tool": True,
            "forced_tool_args": {"query": "x"},
            "force_tool_name": "system.websearch",
            "_prompt_cache_decision": object(),
            "chat_history": [],
        },
        current_call_provider="openai",
        current_call_model="gpt-5.4-nano",
        user_selected_model="gpt-5.4",
        remaining_tool_rounds=3,
    )

    assert kwargs["provider"] == "openai"
    assert kwargs["model"] == "gpt-5.4-nano"
    assert kwargs["max_tool_rounds"] == 3
    assert "forced_tool" not in kwargs
    assert "forced_tool_args" not in kwargs
    assert "force_tool_name" not in kwargs
    assert "_prompt_cache_decision" not in kwargs


def test_execution_engine_stream_handoff_dispatch_present():
    source = Path("backend/services/orchestrator/execution_engine.py").read_text(encoding="utf-8")

    assert "TRANSPORT_TOOL_LOOP_RUNNER_ENABLED" in source
    assert "_should_route_stream_tool_round_via_gateway" in source
    assert "_build_stream_gateway_handoff_kwargs" in source
    assert "STREAM-GATEWAY-HANDOFF" in source
    assert "llm_gateway.reason_and_respond" in source
    assert "_async_iter_llm_stream" in source


@pytest.mark.asyncio
async def test_stream_post_tool_round_uses_gateway_handoff_when_flag_on(monkeypatch):
    monkeypatch.setattr(ee_module, "TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", True)

    gateway_handoff_mock = AsyncMock(
        return_value={
            "text": "final from gateway",
            "tool_calls": [],
            "usage": {"input_tokens": 3, "output_tokens": 4},
            "cost": {"total_cost": 0.02},
        }
    )
    stream_mock = AsyncMock()

    async def _fake_stream(*args, **kwargs):
        stream_mock()
        if False:
            yield StreamEvent(type="text_delta", content="should-not-run", metadata={})

    monkeypatch.setattr(ee_module.llm_gateway, "reason_and_respond", gateway_handoff_mock)
    monkeypatch.setattr(ee_module, "_async_iter_llm_stream", _fake_stream)

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "name": "system.websearch",
                "content": json.dumps({"status": "ok", "data": {"summary": "done"}}),
            }
        ]
    )

    engine = ee_module.OrchestratorExecutionEngine(
        db=None,
        context_manager=MagicMock(),
        model_hierarchy={},
        agent_planner=MagicMock(),
        agent_runtime=MagicMock(),
        skill_selector=MagicMock(),
    )

    events = []
    async for ev in engine.run_tool_loop_stream(
        orchestrator_context=OrchestratorContext(history=[{"role": "user", "content": "search news"}]),
        tool_executor=tool_executor,
        gateway_kwargs={
            "provider": "openai",
            "model": "gpt-5.4",
            "api_key": "test-key",
            "chat_history": [{"role": "user", "content": "search news"}],
            "user_prompt": "search news",
            "chat_id": 1,
            "allowed_skill_ids": ["system.websearch"],
            "force_tool_name": "system.websearch",
            "forced_tool_args": {"query": "news"},
        },
        fallback_summary="fallback",
        current_limit=3,
        bypass_policy_this_turn=False,
        set_policy_pending=MagicMock(),
        chat_id=1,
        user_text="search news",
    ):
        events.append(ev)

    gateway_handoff_mock.assert_awaited_once()
    assert gateway_handoff_mock.await_args.kwargs["max_tool_rounds"] == 2
    stream_mock.assert_not_called()
    assert any(ev.type == "text_delta" and ev.content == "final from gateway" for ev in events)


@pytest.mark.asyncio
async def test_stream_post_tool_round_keeps_direct_stream_when_flag_off(monkeypatch):
    monkeypatch.setattr(ee_module, "TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", False)

    gateway_handoff_mock = AsyncMock()
    stream_calls = {"count": 0}

    async def _fake_stream(*args, **kwargs):
        stream_calls["count"] += 1
        yield StreamEvent(type="text_delta", content="streamed synthesis", metadata={})

    monkeypatch.setattr(ee_module.llm_gateway, "reason_and_respond", gateway_handoff_mock)
    monkeypatch.setattr(ee_module, "_async_iter_llm_stream", _fake_stream)

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(
        return_value=[
            {
                "role": "tool",
                "name": "system.websearch",
                "content": json.dumps({"status": "ok", "data": {"summary": "done"}}),
            }
        ]
    )

    engine = ee_module.OrchestratorExecutionEngine(
        db=None,
        context_manager=MagicMock(),
        model_hierarchy={},
        agent_planner=MagicMock(),
        agent_runtime=MagicMock(),
        skill_selector=MagicMock(),
    )

    events = []
    async for ev in engine.run_tool_loop_stream(
        orchestrator_context=OrchestratorContext(history=[{"role": "user", "content": "search news"}]),
        tool_executor=tool_executor,
        gateway_kwargs={
            "provider": "openai",
            "model": "gpt-5.4",
            "api_key": "test-key",
            "chat_history": [{"role": "user", "content": "search news"}],
            "user_prompt": "search news",
            "chat_id": 1,
            "allowed_skill_ids": ["system.websearch"],
            "force_tool_name": "system.websearch",
            "forced_tool_args": {"query": "news"},
        },
        fallback_summary="fallback",
        current_limit=3,
        bypass_policy_this_turn=False,
        set_policy_pending=MagicMock(),
        chat_id=1,
        user_text="search news",
    ):
        events.append(ev)

    gateway_handoff_mock.assert_not_called()
    assert stream_calls["count"] == 1
    assert any(ev.type == "text_delta" and ev.content == "streamed synthesis" for ev in events)
