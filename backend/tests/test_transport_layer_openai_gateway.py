from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.llm_providers.openai.gateway import OpenAIGateway
from backend.llm_providers.transports.openai_compat import OpenAICompatTransport
from backend.services import llm_gateway


def _set_transport_layer_flag(monkeypatch, flag_value=None):
    if flag_value is None:
        monkeypatch.delenv("TRANSPORT_LAYER_ENABLED", raising=False)
        monkeypatch.setattr(llm_gateway, "TRANSPORT_LAYER_ENABLED", False)
    else:
        monkeypatch.setenv("TRANSPORT_LAYER_ENABLED", flag_value)
        enabled = str(flag_value).strip().lower() in {"1", "true", "yes", "on"}
        monkeypatch.setattr(llm_gateway, "TRANSPORT_LAYER_ENABLED", enabled)
    return llm_gateway


class _FakeOpenAIGateway:
    def __init__(self):
        self.service = MagicMock(name="openai_service")
        self.reason_and_respond = AsyncMock(return_value={"text": "ok"})


class _FakeGeminiGateway:
    async def reason_and_respond(self, **kwargs):
        return {"text": "gemini", "kwargs": kwargs}


class _FakeOllamaGateway:
    async def reason_and_respond(self, **kwargs):
        return {"text": "ollama", "kwargs": kwargs}


def _common_reason_kwargs():
    return {
        "model": "gpt-5.4-mini",
        "api_key": "test-key",
        "chat_history": [{"role": "user", "content": "hello"}],
        "context_manager": MagicMock(),
        "db": MagicMock(),
        "user_prompt": "hello",
        "chat_id": 1,
        "tool_executor": MagicMock(),
        "disable_tools": True,
    }


@pytest.mark.parametrize("flag_value", [None, "false", "0", "off"])
@pytest.mark.asyncio
async def test_llm_gateway_flag_off_does_not_inject_provider_transport(monkeypatch, flag_value):
    gateway_module = _set_transport_layer_flag(monkeypatch, flag_value)
    captured: list[dict] = []
    fake_openai = _FakeOpenAIGateway()

    async def _capture_reason_and_respond(**kwargs):
        captured.append(kwargs)
        return {"text": "ok"}

    fake_openai.reason_and_respond = _capture_reason_and_respond

    monkeypatch.setattr(
        gateway_module,
        "_ensure_gateway_silos",
        lambda: {
            "openai": fake_openai,
            "gemini": _FakeGeminiGateway(),
            "ollama": _FakeOllamaGateway(),
        },
    )
    monkeypatch.setattr(
        gateway_module,
        "provider_access_decision",
        lambda _provider: MagicMock(disabled=False),
    )
    monkeypatch.setattr(gateway_module.tool_manager, "get_all_tools", lambda: {"noop": MagicMock()})

    await gateway_module.reason_and_respond(provider="openai", **_common_reason_kwargs())

    assert len(captured) == 1
    assert "provider_transport" not in captured[0]
    assert gateway_module.TRANSPORT_LAYER_ENABLED is False


@pytest.mark.asyncio
async def test_llm_gateway_flag_on_injects_openai_compat_transport_from_gateway_service(monkeypatch):
    gateway_module = _set_transport_layer_flag(monkeypatch, "true")
    captured: list[dict] = []
    fake_openai = _FakeOpenAIGateway()

    async def _capture_reason_and_respond(**kwargs):
        captured.append(kwargs)
        return {"text": "ok"}

    fake_openai.reason_and_respond = _capture_reason_and_respond

    monkeypatch.setattr(
        gateway_module,
        "_ensure_gateway_silos",
        lambda: {
            "openai": fake_openai,
            "gemini": _FakeGeminiGateway(),
            "ollama": _FakeOllamaGateway(),
        },
    )
    monkeypatch.setattr(
        gateway_module,
        "provider_access_decision",
        lambda _provider: MagicMock(disabled=False),
    )
    monkeypatch.setattr(gateway_module.tool_manager, "get_all_tools", lambda: {"noop": MagicMock()})

    await gateway_module.reason_and_respond(provider="openai", **_common_reason_kwargs())

    assert len(captured) == 1
    transport = captured[0].get("provider_transport")
    assert isinstance(transport, OpenAICompatTransport)
    assert transport._service is fake_openai.service


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["gemini", "ollama"])
async def test_llm_gateway_flag_on_does_not_inject_transport_for_non_openai_providers(monkeypatch, provider):
    gateway_module = _set_transport_layer_flag(monkeypatch, "true")

    monkeypatch.setattr(
        gateway_module,
        "_ensure_gateway_silos",
        lambda: {
            "openai": _FakeOpenAIGateway(),
            "gemini": _FakeGeminiGateway(),
            "ollama": _FakeOllamaGateway(),
        },
    )
    monkeypatch.setattr(
        gateway_module,
        "provider_access_decision",
        lambda _provider: MagicMock(disabled=False),
    )
    monkeypatch.setattr(gateway_module.tool_manager, "get_all_tools", lambda: {"noop": MagicMock()})

    response = await gateway_module.reason_and_respond(provider=provider, **_common_reason_kwargs())

    assert "provider_transport" not in response["kwargs"]


class _RecordingTransport:
    def __init__(self):
        self.send_calls = []
        self.prepare_history_calls = []

    async def send(self, **kwargs):
        self.send_calls.append(kwargs)
        return {"type": "text", "text": "via-transport", "usage": {}, "cost": {}}

    def prepare_history_for_second_call(self, **kwargs):
        self.prepare_history_calls.append(kwargs)
        return list(kwargs.get("chat_history") or [])


@pytest.mark.asyncio
async def test_openai_gateway_uses_injected_transport_for_synthesis_request_seam(monkeypatch):
    gateway = OpenAIGateway()
    transport = _RecordingTransport()
    helpers = MagicMock()
    helpers._should_skip_fact_extraction_for_tool_results.return_value = False
    helpers._apply_routing_quality_guards.side_effect = lambda response, *_args, **_kwargs: response
    monkeypatch.setattr(gateway, "_gateway_helpers", lambda: helpers)

    response = await gateway.reason_and_respond(
        provider="openai",
        model="gpt-5.4-mini",
        api_key="test-key",
        chat_history=[{"role": "user", "content": "hello"}],
        context_manager=MagicMock(),
        db=MagicMock(),
        user_prompt="hello",
        chat_id=1,
        tool_executor=MagicMock(),
        tool_results=[{"skill_id": "system.websearch", "status": "ok", "data": {}}],
        provider_transport=transport,
    )

    assert response["text"] == "via-transport"
    assert len(transport.send_calls) == 1
    assert transport.send_calls[0]["api_key"] == "test-key"
    assert transport.send_calls[0]["model"] == "gpt-5.4-mini"


@pytest.mark.asyncio
async def test_openai_gateway_legacy_tool_loop_uses_injected_transport_request_and_history_seams(monkeypatch):
    gateway = OpenAIGateway()
    transport = _RecordingTransport()

    monkeypatch.setattr(
        "backend.llm_providers.openai.gateway.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.shared.tool_loop_runner.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        gateway,
        "_run_full_tool_loop",
        gateway._run_legacy_tool_loop,
    )

    async def _fake_execute_tool_calls(_calls):
        return [{"skill_id": "system.weather", "status": "ok", "content": "{}"}]

    tool_executor = MagicMock()
    tool_executor.execute_tool_calls = AsyncMock(side_effect=_fake_execute_tool_calls)

    send_responses = [
        {
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "system_weather", "arguments": "{}"},
                }
            ],
            "raw_assistant_response": {"role": "assistant"},
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "cost": {"total_cost": 0.01},
        },
        {"type": "text", "text": "done", "usage": {}, "cost": {}},
    ]

    async def _send(**kwargs):
        transport.send_calls.append(kwargs)
        return send_responses[min(len(transport.send_calls) - 1, len(send_responses) - 1)]

    transport.send = _send

    monkeypatch.setattr(
        "backend.llm_providers.openai.gateway._filter_tools_by_skill_ids",
        lambda allowed_skill_ids: [{"name": "system.weather", "description": "", "parameters": {}}],
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.openai.gateway._build_tool_definitions_for_llm",
        lambda tools: [{"type": "function", "function": {"name": "system_weather", "parameters": {}}}],
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.openai.gateway._prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls},
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.openai.gateway.resolve_moa_model",
        lambda **kwargs: (kwargs["user_base_model"], False),
        raising=False,
    )

    from backend.llm_providers.shared import utils as shared_utils

    monkeypatch.setattr(shared_utils, "_filter_tools_by_skill_ids", lambda allowed_skill_ids: [{"name": "system.weather"}])
    monkeypatch.setattr(
        shared_utils,
        "_build_tool_definitions_for_llm",
        lambda tools: [{"type": "function", "function": {"name": "system_weather", "parameters": {}}}],
    )
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls},
    )

    from backend.llm_providers.shared import moa as moa_module

    monkeypatch.setattr(moa_module, "resolve_moa_model", lambda **kwargs: (kwargs["user_base_model"], False))

    response = await gateway._run_legacy_tool_loop(
        provider="openai",
        model="gpt-5.4-mini",
        api_key="test-key",
        chat_history=[],
        user_prompt="weather?",
        tool_executor=tool_executor,
        allowed_skill_ids=["system.weather"],
        max_tool_rounds=3,
        provider_transport=transport,
    )

    assert response["text"] == "done"
    assert len(transport.send_calls) >= 2
    assert len(transport.prepare_history_calls) == 1
