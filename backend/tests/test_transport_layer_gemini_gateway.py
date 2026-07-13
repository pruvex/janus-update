from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.llm_providers.gemini.gateway import GeminiGateway
from backend.llm_providers.transports.gemini_native import GeminiNativeTransport
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


class _FakeGeminiGateway:
    def __init__(self):
        self.service = MagicMock(name="gemini_service")
        self.reason_and_respond = AsyncMock(return_value={"text": "ok"})


class _FakeOpenAIGateway:
    async def reason_and_respond(self, **kwargs):
        return {"text": "openai", "kwargs": kwargs}


class _FakeOllamaGateway:
    async def reason_and_respond(self, **kwargs):
        return {"text": "ollama", "kwargs": kwargs}


def _common_reason_kwargs():
    return {
        "model": "gemini-3-flash-preview",
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
async def test_llm_gateway_flag_off_does_not_inject_gemini_transport(monkeypatch, flag_value):
    gateway_module = _set_transport_layer_flag(monkeypatch, flag_value)
    captured: list[dict] = []
    fake_gemini = _FakeGeminiGateway()

    async def _capture_reason_and_respond(**kwargs):
        captured.append(kwargs)
        return {"text": "ok"}

    fake_gemini.reason_and_respond = _capture_reason_and_respond

    monkeypatch.setattr(
        gateway_module,
        "_ensure_gateway_silos",
        lambda: {
            "openai": _FakeOpenAIGateway(),
            "gemini": fake_gemini,
            "ollama": _FakeOllamaGateway(),
        },
    )
    monkeypatch.setattr(
        gateway_module,
        "provider_access_decision",
        lambda _provider: MagicMock(disabled=False),
    )
    monkeypatch.setattr(gateway_module.tool_manager, "get_all_tools", lambda: {"noop": MagicMock()})

    await gateway_module.reason_and_respond(provider="gemini", **_common_reason_kwargs())

    assert len(captured) == 1
    assert "provider_transport" not in captured[0]
    assert gateway_module.TRANSPORT_LAYER_ENABLED is False


@pytest.mark.asyncio
async def test_llm_gateway_flag_on_injects_gemini_native_transport_from_gateway_service(monkeypatch):
    gateway_module = _set_transport_layer_flag(monkeypatch, "true")
    captured: list[dict] = []
    fake_gemini = _FakeGeminiGateway()

    async def _capture_reason_and_respond(**kwargs):
        captured.append(kwargs)
        return {"text": "ok"}

    fake_gemini.reason_and_respond = _capture_reason_and_respond

    monkeypatch.setattr(
        gateway_module,
        "_ensure_gateway_silos",
        lambda: {
            "openai": _FakeOpenAIGateway(),
            "gemini": fake_gemini,
            "ollama": _FakeOllamaGateway(),
        },
    )
    monkeypatch.setattr(
        gateway_module,
        "provider_access_decision",
        lambda _provider: MagicMock(disabled=False),
    )
    monkeypatch.setattr(gateway_module.tool_manager, "get_all_tools", lambda: {"noop": MagicMock()})

    await gateway_module.reason_and_respond(provider="gemini", **_common_reason_kwargs())

    assert len(captured) == 1
    transport = captured[0].get("provider_transport")
    assert isinstance(transport, GeminiNativeTransport)
    assert transport._service is fake_gemini.service


@pytest.mark.asyncio
async def test_llm_gateway_flag_on_does_not_inject_gemini_transport_for_ollama(monkeypatch):
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

    response = await gateway_module.reason_and_respond(provider="ollama", **_common_reason_kwargs())

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
async def test_gemini_gateway_legacy_tool_loop_uses_injected_transport_request_and_history_seams(monkeypatch):
    gateway = GeminiGateway()
    transport = _RecordingTransport()

    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.shared.tool_loop_runner.TRANSPORT_TOOL_LOOP_RUNNER_ENABLED",
        False,
        raising=False,
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
        "backend.llm_providers.gemini.gateway._filter_tools_by_skill_ids",
        lambda allowed_skill_ids: [{"name": "system.weather", "description": "", "parameters": {}}],
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway._build_tool_definitions_for_llm",
        lambda tools: [{"type": "function", "function": {"name": "system_weather", "parameters": {}}}],
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway._prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls},
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway.resolve_moa_model",
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

    response = await gateway._run_legacy_simple_tool_loop(
        provider="gemini",
        model="gemini-3-flash-preview",
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


@pytest.mark.asyncio
async def test_gemini_gateway_runner_uses_injected_transport_service_seam(monkeypatch):
    gateway = GeminiGateway()
    transport = _RecordingTransport()

    monkeypatch.setenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "true")
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)

    async def _send(**kwargs):
        transport.send_calls.append(kwargs)
        return {
            "type": "text",
            "text": "runner-done",
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "cost": {"total_cost": 0.01},
        }

    transport.send = _send

    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway._filter_tools_by_skill_ids",
        lambda allowed_skill_ids: [],
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway._build_tool_definitions_for_llm",
        lambda tools: [],
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway._prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls},
        raising=False,
    )
    monkeypatch.setattr(
        "backend.llm_providers.gemini.gateway.resolve_moa_model",
        lambda **kwargs: (kwargs["user_base_model"], False),
        raising=False,
    )

    from backend.llm_providers.shared import utils as shared_utils

    monkeypatch.setattr(shared_utils, "_filter_tools_by_skill_ids", lambda allowed_skill_ids: [])
    monkeypatch.setattr(shared_utils, "_build_tool_definitions_for_llm", lambda tools: [])
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls},
    )

    from backend.llm_providers.shared import moa as moa_module

    monkeypatch.setattr(moa_module, "resolve_moa_model", lambda **kwargs: (kwargs["user_base_model"], False))

    response = await gateway._run_simple_tool_loop_with_runner(
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="test-key",
        chat_history=[],
        user_prompt="hello",
        tool_executor=MagicMock(),
        allowed_skill_ids=[],
        max_tool_rounds=1,
        provider_transport=transport,
    )

    assert response["text"] == "runner-done"
    assert len(transport.send_calls) == 1


@pytest.mark.asyncio
async def test_gemini_gateway_runner_uses_transport_for_moa_synthesis(monkeypatch):
    gateway = GeminiGateway()
    transport = _RecordingTransport()

    monkeypatch.setenv("TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "true")
    import importlib

    import backend.llm_providers.shared.tool_loop_runner as runner_module

    importlib.reload(runner_module)

    responses = [
        {
            "type": "text",
            "text": "tool-loop-result",
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "cost": {"total_cost": 0.01},
        },
        {
            "type": "text",
            "text": "synthesis-result",
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "cost": {"total_cost": 0.01},
        },
    ]

    async def _send(**kwargs):
        transport.send_calls.append(kwargs)
        return responses[len(transport.send_calls) - 1]

    transport.send = _send

    from backend.llm_providers.shared import moa as moa_module
    from backend.llm_providers.shared import utils as shared_utils

    monkeypatch.setattr(shared_utils, "_filter_tools_by_skill_ids", lambda allowed_skill_ids: [])
    monkeypatch.setattr(shared_utils, "_build_tool_definitions_for_llm", lambda tools: [])
    monkeypatch.setattr(
        shared_utils,
        "_prevalidate_tool_calls",
        lambda tool_calls, user_prompt="": {"valid_calls": tool_calls},
    )
    monkeypatch.setattr(
        moa_module,
        "resolve_moa_model",
        lambda **kwargs: ("gemini-3-pro-preview", True),
    )

    response = await gateway._run_simple_tool_loop_with_runner(
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="test-key",
        chat_history=[],
        user_prompt="hello",
        tool_executor=MagicMock(),
        allowed_skill_ids=[],
        max_tool_rounds=1,
        provider_transport=transport,
    )

    assert response["text"] == "synthesis-result"
    assert len(transport.send_calls) == 2


@pytest.mark.asyncio
async def test_gemini_gateway_engine_owned_path_does_not_receive_transport(monkeypatch):
    gateway = GeminiGateway()
    captured_engine: list[dict] = []
    captured_simple: list[dict] = []

    async def _capture_engine_owned(**kwargs):
        captured_engine.append(kwargs)
        return {"text": "engine-owned"}

    async def _capture_simple(**kwargs):
        captured_simple.append(kwargs)
        return {"text": "simple"}

    monkeypatch.setattr(gateway, "_run_engine_owned_gemini_turn", _capture_engine_owned)
    monkeypatch.setattr(gateway, "_run_simple_tool_loop", _capture_simple)

    await gateway.reason_and_respond(
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="test-key",
        chat_history=[],
        context_manager=MagicMock(),
        db=MagicMock(),
        user_prompt="hello",
        chat_id=1,
        tool_executor=MagicMock(),
        _gemini_engine_owned_tool_loop=True,
        provider_transport=_RecordingTransport(),
    )

    assert len(captured_engine) == 1
    assert "provider_transport" not in captured_engine[0]
    assert len(captured_simple) == 0


@pytest.mark.asyncio
async def test_gemini_gateway_drill_down_path_does_not_receive_transport(monkeypatch):
    gateway = GeminiGateway()
    captured_drill: list[dict] = []

    async def _capture_drill_down(**kwargs):
        captured_drill.append(kwargs)
        return {"text": "drill-down"}

    monkeypatch.setattr(gateway, "_run_drill_down_list_research", _capture_drill_down)
    monkeypatch.setattr(gateway, "_is_list_query", lambda _prompt: True)

    await gateway.reason_and_respond(
        provider="gemini",
        model="gemini-3-flash-preview",
        api_key="test-key",
        chat_history=[],
        context_manager=MagicMock(),
        db=MagicMock(),
        user_prompt="top 5 games list",
        chat_id=1,
        tool_executor=MagicMock(),
        allowed_skill_ids=["system.websearch"],
        provider_transport=_RecordingTransport(),
    )

    assert len(captured_drill) == 1
    assert "provider_transport" not in captured_drill[0]
