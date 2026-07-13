from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.llm_providers.ollama.gateway import OllamaGateway
from backend.llm_providers.transports.ollama_local import OllamaLocalTransport
from backend.services import llm_gateway


@pytest.mark.asyncio
async def test_flag_on_injects_ollama_transport(monkeypatch):
    class Gateway:
        def __init__(self):
            self.service = MagicMock()
            self.reason_and_respond = AsyncMock(return_value={"text": "ok"})

    gateway = Gateway()
    monkeypatch.setattr(llm_gateway, "TRANSPORT_LAYER_ENABLED", True)
    monkeypatch.setattr(llm_gateway, "_ensure_gateway_silos", lambda: {"ollama": gateway})
    monkeypatch.setattr(llm_gateway, "provider_access_decision", lambda _: MagicMock(disabled=False))
    monkeypatch.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: {})
    await llm_gateway.reason_and_respond(provider="ollama", model="qwen", api_key="ollama", chat_history=[], context_manager=MagicMock(), db=MagicMock(), user_prompt="hi", chat_id=1, tool_executor=MagicMock())
    assert isinstance(gateway.reason_and_respond.await_args.kwargs["provider_transport"], OllamaLocalTransport)


@pytest.mark.asyncio
async def test_gateway_uses_transport_for_initial_and_synthesis(monkeypatch):
    gateway = OllamaGateway()
    transport = MagicMock()
    transport.send = AsyncMock(return_value={"type": "text", "text": "ok"})
    await gateway.reason_and_respond(provider="ollama", model="qwen", api_key="ollama", chat_history=[{"role": "user", "content": "hi"}], context_manager=MagicMock(), db=MagicMock(), user_prompt="hi", chat_id=1, tool_executor=MagicMock(), provider_transport=transport)
    await gateway.reason_and_respond(provider="ollama", model="qwen", api_key="ollama", chat_history=[{"role": "tool", "content": "x"}], context_manager=MagicMock(), db=MagicMock(), user_prompt="hi", chat_id=1, tool_executor=MagicMock(), tool_results=[{}], provider_transport=transport)
    assert transport.send.await_count == 2
