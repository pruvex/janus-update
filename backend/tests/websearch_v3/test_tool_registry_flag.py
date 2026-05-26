from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.data import schemas


@pytest.mark.asyncio
async def test_websearch_wrapper_routes_simple_news_to_v3_when_flag_is_enabled(monkeypatch):
    monkeypatch.setenv("JANUS_WEBSEARCH_V3_PHASE1", "1")

    raw_v3 = {
        "text": "Kurzlage: Es liegt aktuell eine belegte Meldung vor.",
        "sources": [
            {
                "url": "https://www.computerwoche.de/a/microsoft-ki,123",
                "title": "Microsoft und EY bauen KI-Kooperation aus",
                "snippet": "Microsoft und EY erweitern ihre KI-Kooperation.",
            }
        ],
        "metadata": {
            "provider": "openai",
            "status": "ok",
            "pipeline": "websearch_v3",
            "verified_source_mode": "multi",
            "max_sources": 2,
        },
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.tool_registry.execute_single_verified_news",
        AsyncMock(return_value=raw_v3),
    ) as v3_mock, patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(return_value={"text": "v2", "sources": [], "metadata": {"provider": "openai"}}),
    ) as v2_mock:
        from backend.tool_registry import websearch_wrapper

        result = await websearch_wrapper(schemas.WebsearchArgsV2(query="was gibt es neues zu Microsoft?", provider="openai"))

    payload = result.model_dump() if hasattr(result, "model_dump") else result
    assert payload["status"] == "ok"
    assert payload["data"]["pipeline"] == "websearch_v3"
    assert payload["data"]["verified_source_mode"] == "multi"
    assert payload["data"]["max_sources"] == 2
    assert payload["data"]["sources"][0]["url"] == "https://www.computerwoche.de/a/microsoft-ki,123"
    v3_mock.assert_awaited_once()
    assert v3_mock.await_args.kwargs["provider"] == "openai"
    v2_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_websearch_v3_tool_result_survives_response_finalizer_without_rerender(monkeypatch):
    monkeypatch.setenv("JANUS_WEBSEARCH_V3_PHASE1", "1")
    v3_text = (
        "Kurzlage: Es liegt aktuell eine belegte Meldung vor.\n\n"
        "1. Microsoft und EY bauen KI-Kooperation aus\n"
        "Microsoft und EY erweitern ihre Zusammenarbeit.\n"
        "Quelle: computerwoche.de. [Link](https://www.computerwoche.de/a/microsoft-ki,123)\n\n"
        "Einordnung:\nDiese Kurzlage basiert auf einer verifizierten Webquelle."
    )
    raw_v3 = {
        "text": v3_text,
        "sources": [
            {
                "url": "https://www.computerwoche.de/a/microsoft-ki,123",
                "title": "Microsoft und EY bauen KI-Kooperation aus",
                "snippet": "Microsoft und EY erweitern ihre KI-Kooperation.",
                "verified": True,
            }
        ],
        "metadata": {"provider": "openai", "status": "ok", "pipeline": "websearch_v3"},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.tool_registry.execute_single_verified_news",
        AsyncMock(return_value=raw_v3),
    ):
        from backend.tool_registry import websearch_wrapper

        result = await websearch_wrapper(schemas.WebsearchArgsV2(query="was gibt es neues zu Microsoft?", provider="openai"))

    from backend.services.orchestrator.response_finalizer import render_websearch_sources

    rendered = render_websearch_sources(
        [
            {
                "role": "tool",
                "name": "system.websearch",
                "_skill_id": "system.websearch",
                "content": json.dumps(result.model_dump(), ensure_ascii=False),
            }
        ]
    )

    assert rendered == v3_text


def test_websearch_v3_no_source_results_are_rendered_once():
    from backend.services.orchestrator.response_finalizer import render_websearch_sources

    payload = {
        "status": "ok",
        "data": {
            "query": "was gibt es neues zu Microsoft?",
            "pipeline": "websearch_v3",
            "verified_source_mode": "single",
            "verification_status": "no_source",
            "verification_reason": "no_verified_source",
            "text": "Ich habe aktuell keine ausreichend belastbare Quelle gefunden.",
            "sources": [],
        },
    }

    rendered = render_websearch_sources(
        [
            {
                "role": "tool",
                "name": "system.websearch",
                "_skill_id": "system.websearch",
                "content": json.dumps(payload, ensure_ascii=False),
            },
            {
                "role": "tool",
                "name": "system.websearch",
                "_skill_id": "system.websearch",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ]
    )

    assert rendered == "Ich habe aktuell keine ausreichend belastbare Quelle gefunden."


@pytest.mark.asyncio
async def test_websearch_wrapper_requires_native_provider_when_v3_flag_is_enabled(monkeypatch):
    monkeypatch.setenv("JANUS_WEBSEARCH_V3_PHASE1", "1")

    with patch("backend.tool_registry.keyring.get_password", return_value=""), patch(
        "backend.tool_registry.execute_single_verified_news",
        AsyncMock(return_value={}),
    ) as v3_mock, patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(return_value={"text": "", "sources": [], "metadata": {"provider": "openai"}}),
    ) as v2_mock, patch("backend.tool_registry.SessionLocal"):
        from backend.tool_registry import websearch_wrapper

        result = await websearch_wrapper(schemas.WebsearchArgsV2(query="was gibt es neues zu Microsoft?"))

    payload = result.model_dump() if hasattr(result, "model_dump") else result
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "WEBSEARCH_V3_PROVIDER_REQUIRED"
    v3_mock.assert_not_awaited()
    v2_mock.assert_not_awaited()
