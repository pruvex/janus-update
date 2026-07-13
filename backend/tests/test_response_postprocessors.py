import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.llm_providers.shared import response_postprocessors
from backend.services import llm_gateway


def _release_tool_results():
    return [{
        "content": json.dumps({
            "status": "ok",
            "data": {
                "sources": [{
                    "title": "Nintendo Switch 2 release date",
                    "snippet": "Nintendo Switch 2 release details",
                    "url": "https://example.de/switch-2",
                }]
            },
        })
    }]


def test_openai_compat_registry_preserves_release_list_link_repair():
    response = response_postprocessors.postprocess_provider_response(
        "openai",
        {"text": "- Nintendo Switch 2"},
        user_prompt="Welche Nintendo Spiele erscheinen im nächsten Monat?",
        tool_results=_release_tool_results(),
    )

    assert response["text"] == "- Nintendo Switch 2 — [Mehr erfahren](https://example.de/switch-2)"


def test_gemini_native_registry_renders_preserved_metadata(monkeypatch):
    renderer = MagicMock()
    renderer.render_final_response.return_value = {"text": "rendered"}
    monkeypatch.setattr(
        "backend.llm_providers.gemini.link_renderer.get_link_renderer",
        lambda: renderer,
    )
    metadata = {"groundingChunks": [{"web": {"uri": "https://example.test"}}]}

    response = response_postprocessors.postprocess_provider_response(
        "gemini", {"text": "source-backed", "_preserved_metadata": metadata}
    )

    assert response == {"text": "rendered"}
    renderer.render_final_response.assert_called_once_with(
        {"text": "source-backed", "_preserved_metadata": metadata}, metadata=metadata
    )


def test_missing_metadata_and_unregistered_provider_leave_response_unchanged():
    gemini_response = {"text": "plain Gemini"}
    unknown_response = {"text": "plain Ollama"}

    assert response_postprocessors.postprocess_provider_response("gemini", gemini_response) is gemini_response
    assert response_postprocessors.postprocess_provider_response("ollama", unknown_response) is unknown_response


@pytest.mark.asyncio
async def test_central_router_owns_postprocessor_invocation(monkeypatch):
    response = {"text": "silo response"}
    fake_silo = MagicMock(service=MagicMock())
    fake_silo.reason_and_respond = AsyncMock(return_value=response)
    seen = {}

    def _postprocess(provider, returned_response, **context):
        seen.update(provider=provider, response=returned_response, context=context)
        return {"text": "finished"}

    monkeypatch.setattr(response_postprocessors, "postprocess_provider_response", _postprocess)
    monkeypatch.setattr(llm_gateway, "_ensure_gateway_silos", lambda: {"openai": fake_silo})
    monkeypatch.setattr(llm_gateway, "provider_access_decision", lambda _provider: MagicMock(disabled=False))
    monkeypatch.setattr(llm_gateway.tool_manager, "get_all_tools", lambda: {"noop": MagicMock()})

    result = await llm_gateway.reason_and_respond(
        provider="openai", model="test", api_key="test", chat_history=[], context_manager=MagicMock(),
        db=MagicMock(), user_prompt="hello", chat_id=1, tool_executor=MagicMock(), disable_tools=True,
    )

    assert result == {"text": "finished"}
    assert seen["provider"] == "openai"
    assert seen["response"] is response
