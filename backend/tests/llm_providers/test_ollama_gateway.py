from unittest.mock import MagicMock

import pytest

from backend.llm_providers.ollama.gateway import OllamaGateway
from backend.services import llm_gateway


class _Tool:
    def __init__(self, name: str, description: str = "tool"):
        self.name = name
        self.description = description
        self.args_schema = None


def _weather_tool_definition() -> dict:
    return {
        "name": "system.weather",
        "description": "Weather lookup",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
        },
    }


def _install_weather_tool_registry(monkeypatch):
    fake_tools = {"system.weather": _Tool("system.weather", "Weather lookup")}

    def _get_all_tools():
        return fake_tools

    def _get_skill_id(name):
        return "system.weather" if str(name) == "system.weather" else str(name)

    for target in (
        "backend.llm_providers.ollama.gateway.tool_manager",
        "backend.llm_providers.shared.utils.tool_manager",
        "backend.services.llm_gateway.tool_manager",
    ):
        monkeypatch.setattr(f"{target}.get_all_tools", _get_all_tools)
        monkeypatch.setattr(f"{target}.get_skill_id", _get_skill_id)


@pytest.mark.asyncio
async def test_ollama_gateway_forwards_bound_weather_tools_and_force_to_service(monkeypatch):
    _install_weather_tool_registry(monkeypatch)
    captured: dict = {}

    gateway = OllamaGateway()

    async def _fake_generate_response(**kwargs):
        captured.update(kwargs)
        return {
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "call_weather",
                    "type": "function",
                    "function": {
                        "name": "system.weather",
                        "arguments": '{"city":"Berlin"}',
                    },
                }
            ],
        }

    gateway.service.generate_response = _fake_generate_response

    response = await gateway.reason_and_respond(
        provider="ollama",
        model="qwen2.5-coder:14b",
        api_key="ollama",
        chat_history=[{"role": "user", "content": "Wie ist das Wetter in Berlin?"}],
        context_manager=MagicMock(),
        db=MagicMock(),
        user_prompt="Wie ist das Wetter in Berlin?",
        chat_id=1,
        tool_executor=MagicMock(),
        allowed_skill_ids=["system.weather"],
        validated_tool_definitions=[_weather_tool_definition()],
        forced_tool={
            "skill_id": "system.weather",
            "provider_tool_name": "system.weather",
        },
        force_tool_name="system.weather",
    )

    assert captured.get("tools")
    assert any(item.get("name") == "system.weather" for item in captured["tools"])
    assert captured.get("force_tool_name") == "system.weather"
    assert captured.get("tool_choice") is None
    assert response.get("type") == "tool_code"
    assert response.get("tool_calls")


@pytest.mark.asyncio
async def test_ollama_gateway_builds_tools_from_allowed_skill_ids_when_unbound(monkeypatch):
    _install_weather_tool_registry(monkeypatch)
    captured: dict = {}

    gateway = OllamaGateway()

    async def _fake_generate_response(**kwargs):
        captured.update(kwargs)
        return {"type": "text", "text": "fallback"}

    gateway.service.generate_response = _fake_generate_response

    await gateway.reason_and_respond(
        provider="ollama",
        model="qwen2.5-coder:14b",
        api_key="ollama",
        chat_history=[{"role": "user", "content": "Wie ist das Wetter in Berlin?"}],
        context_manager=MagicMock(),
        db=MagicMock(),
        user_prompt="Wie ist das Wetter in Berlin?",
        chat_id=1,
        tool_executor=MagicMock(),
        allowed_skill_ids=["system.weather"],
        forced_tool={
            "skill_id": "system.weather",
            "provider_tool_name": "system.weather",
        },
    )

    assert captured.get("tools")
    assert any(item.get("name") == "system.weather" for item in captured["tools"])
    assert captured.get("force_tool_name") == "system.weather"


@pytest.mark.asyncio
async def test_llm_gateway_forwards_force_tool_name_to_ollama_silo(monkeypatch):
    captured: list[dict] = []

    class _FakeOllamaGateway:
        async def reason_and_respond(self, **kwargs):
            captured.append(kwargs)
            return {"type": "tool_code", "tool_calls": [{"id": "1"}]}

    monkeypatch.setattr(
        llm_gateway,
        "_ensure_gateway_silos",
        lambda: {"ollama": _FakeOllamaGateway()},
    )
    monkeypatch.setattr(llm_gateway, "provider_access_decision", lambda _provider: MagicMock(disabled=False))

    await llm_gateway.reason_and_respond(
        provider="ollama",
        model="qwen2.5-coder:14b",
        api_key="ollama",
        chat_history=[{"role": "user", "content": "Wie ist das Wetter in Berlin?"}],
        context_manager=MagicMock(),
        db=MagicMock(),
        user_prompt="Wie ist das Wetter in Berlin?",
        chat_id=1,
        tool_executor=MagicMock(),
        allowed_skill_ids=["system.weather"],
        validated_tool_definitions=[_weather_tool_definition()],
        forced_tool={
            "skill_id": "system.weather",
            "provider_tool_name": "system.weather",
        },
        force_tool_name="system.weather",
    )

    assert len(captured) == 1
    assert captured[0].get("force_tool_name") == "system.weather"
    assert captured[0].get("validated_tool_definitions")
    assert captured[0].get("forced_tool", {}).get("skill_id") == "system.weather"
