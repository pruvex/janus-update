from unittest.mock import AsyncMock, Mock, patch
import json

import pytest
import requests

from backend.data import schemas
from backend.services.websearch.gemini_provider import GeminiWebSearchProvider
from backend.services.websearch.duckduckgo_provider import DuckDuckGoWebSearchProvider
from backend.tool_registry import websearch_wrapper


@pytest.mark.asyncio
async def test_websearch_wrapper_gemini_failure_returns_error_without_ddg_fallback():
    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.services.websearch.websearch.GEMINI_PROVIDER.search",
        AsyncMock(side_effect=RuntimeError("Native Grounding failed")),
    ) as gemini_search_mock, patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "must not be called",
                "sources": [],
                "metadata": {"provider": "openai"},
            }
        ),
    ) as openai_search_mock:
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(query="Neuigkeiten zur EU", provider="gemini", model="gemini-2.0-flash")
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "error"
    assert rd["error"]["code"] == "WEBSEARCH_FAILED"
    gemini_search_mock.assert_awaited_once()
    openai_search_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_websearch_wrapper_persists_cost_entry_for_successful_openai_websearch():
    fake_db = Mock()

    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "Goldpreis heute",
                "sources": [{"url": "https://example.com/gold", "title": "Gold"}],
                "metadata": {"provider": "openai"},
                "usage": {"query_count": 1},
                "cost": {"total_cost": 0.01, "query_cost": 0.01},
            }
        ),
    ), patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ) as create_cost_entry_mock:
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(query="Goldpreis heute", provider="openai", model="gpt-5.4-nano")
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    create_cost_entry_mock.assert_called_once()
    kwargs = create_cost_entry_mock.call_args.kwargs
    assert kwargs["amount"] == 0.01
    assert kwargs["provider"] == "openai"
    assert kwargs["model"] == "gpt-5.4-nano"
    assert kwargs["source_type"] == "websearch"
    assert kwargs["context_details"] == "query_count=1"
    fake_db.close.assert_called_once()


@pytest.mark.asyncio
async def test_websearch_wrapper_normalizes_current_price_query_for_openai_search():
    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "ok",
                "sources": [],
                "metadata": {"provider": "openai"},
                "usage": {},
                "cost": {},
            }
        ),
    ) as openai_search_mock, patch("backend.tool_registry.SessionLocal", return_value=Mock()), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(query="aktueller Preis einer Feinunze Gold 2025", provider="openai", model="gpt-5.4-nano")
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    forwarded_query = openai_search_mock.await_args.kwargs["query"]
    assert forwarded_query == "aktueller Preis einer Feinunze Gold 2026 in Euro"


@pytest.mark.asyncio
async def test_websearch_wrapper_does_not_append_euro_when_query_already_mentions_usd():
    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "ok",
                "sources": [],
                "metadata": {"provider": "openai"},
                "usage": {},
                "cost": {},
            }
        ),
    ) as openai_search_mock, patch("backend.tool_registry.SessionLocal", return_value=Mock()), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(query="current price of gold per troy ounce 2025 USD", provider="openai", model="gpt-5.4-nano")
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    forwarded_query = openai_search_mock.await_args.kwargs["query"]
    assert forwarded_query == "current price of gold per troy ounce 2026 USD"


@pytest.mark.asyncio
async def test_execute_websearch_service_openai_raises_on_native_failure_without_ddg_fallback():
    from backend.services.websearch.websearch import execute_websearch_service

    with patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(side_effect=RuntimeError("boom")),
    ) as openai_mock, patch(
        "backend.services.websearch.websearch.DUCKDUCKGO_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "must not be called",
                "sources": [],
                "metadata": {"provider": "openai"},
            }
        ),
    ) as ddg_mock:
        with pytest.raises(RuntimeError, match="boom"):
            await execute_websearch_service(
            query="Goldpreis heute",
            api_key="sk-123",
            provider="openai",
            model="gpt-5.4-nano",
        )

    openai_mock.assert_awaited_once()
    ddg_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_websearch_service_gemini_raises_on_native_failure_without_ddg_fallback():
    from backend.services.websearch.websearch import execute_websearch_service

    with patch(
        "backend.services.websearch.websearch.GEMINI_PROVIDER.search",
        AsyncMock(side_effect=RuntimeError("Native Grounding failed")),
    ) as gemini_mock, patch(
        "backend.services.websearch.websearch.DUCKDUCKGO_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "must not be called",
                "sources": [],
                "metadata": {"provider": "openai"},
            }
        ),
    ) as ddg_mock:
        with pytest.raises(RuntimeError, match="Native Grounding failed"):
            await execute_websearch_service(
            query="Goldpreis heute",
            api_key="gem-key",
            provider="gemini",
            model="gemini-2.0-flash",
        )

    gemini_mock.assert_awaited_once()
    ddg_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_websearch_service_ollama_uses_ddg_immediately():
    from backend.services.websearch.websearch import execute_websearch_service

    ddg_result = {
        "text": "ddg",
        "sources": [{"url": "https://duckduckgo.com", "title": "DuckDuckGo"}],
        "metadata": {"provider": "duckduckgo"},
        "usage": {},
        "cost": {},
    }
    with patch(
        "backend.services.websearch.websearch.DUCKDUCKGO_PROVIDER.search",
        AsyncMock(return_value=ddg_result),
    ) as ddg_mock, patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "must not be called",
                "sources": [],
                "metadata": {"provider": "openai"},
            }
        ),
    ) as openai_mock, patch(
        "backend.services.websearch.websearch.GEMINI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "must not be called",
                "sources": [],
                "metadata": {"provider": "openai"},
            }
        ),
    ) as gemini_mock:
        result = await execute_websearch_service(
            query="Goldpreis heute",
            api_key="ollama",
            provider="ollama",
            model="qwen2.5:14b",
        )

    assert result == ddg_result
    ddg_mock.assert_awaited_once()
    openai_mock.assert_not_awaited()
    gemini_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_gemini_provider_search_sends_native_google_search_tool_block():
    provider = GeminiWebSearchProvider()
    captured = {}

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b""

    def _fake_urlopen(request):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _Response()

    with patch("backend.services.websearch.gemini_provider.urllib.request.urlopen", side_effect=_fake_urlopen), patch(
        "backend.services.websearch.gemini_provider.json.load",
        return_value={
            "candidates": [
                {
                    "content": {"parts": [{"text": "Antwort mit Quelle"}]},
                    "groundingMetadata": {
                        "webSearchQueries": ["Neuigkeiten zur EU"],
                        "groundingChunks": [{"web": {"uri": "https://example.com"}}],
                        "groundingSupports": [],
                    },
                }
            ]
        },
    ):
        result = await provider.search(api_key="gem-key", query="Neuigkeiten zur EU", model="gemini-2.0-flash")

    assert result["sources"][0]["url"] == "https://example.com"
    assert result["text"] == "Antwort mit Quelle"
    assert captured["body"]["tools"] == [{"google_search": {}}]
    assert "Nutzerfrage: Neuigkeiten zur EU" in captured["body"]["contents"][0]["parts"][0]["text"]
    assert "gründliche Google-Recherche" in captured["body"]["contents"][0]["parts"][0]["text"]
    assert "KEINE Markdown-Links" in captured["body"]["contents"][0]["parts"][0]["text"]


@pytest.mark.asyncio
async def test_gemini_provider_search_returns_clean_sources_and_raw_text_without_source_appendix():
    provider = GeminiWebSearchProvider()

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b""

    with patch("backend.services.websearch.gemini_provider.urllib.request.urlopen", return_value=_Response()), patch(
        "backend.services.websearch.gemini_provider.json.load",
        return_value={
            "candidates": [
                {
                    "content": {"parts": [{"text": "Antwort mit Quelle\n\n**Gefundene Quellen:**\n- [example.com](https://example.com/a)"}]},
                    "groundingMetadata": {
                        "webSearchQueries": ["Switch 2 Deutschland"],
                        "groundingChunks": [
                            {"web": {"uri": "https://example.com/a", "title": "Quelle A"}},
                            {"web": {"uri": "https://example.com/b", "title": "Quelle B"}},
                        ],
                        "groundingSupports": [
                            {"segment": {"text": "Mario Kart World erscheint im April 2026 für Switch 2."}, "groundingChunkIndices": [0]},
                            {"segment": {"text": "Die UVP liegt bei 79,99 Euro."}, "groundingChunkIndices": [1]},
                        ],
                    },
                }
            ]
        },
    ):
        result = await provider.search(api_key="gem-key", query="Switch 2 Deutschland", model="gemini-3-pro-preview")

    assert len(result["sources"]) == 2
    assert result["text"] == "Antwort mit Quelle"
    assert [s["url"] for s in result["sources"]] == ["https://example.com/a", "https://example.com/b"]
    assert result["sources"][0]["title"] == "Quelle A"
    assert result["sources"][0]["url"] == "https://example.com/a"
    assert "Mario Kart World" in result["sources"][0]["snippet"]
    assert result["sources"][1]["title"] == "Quelle B"
    assert result["sources"][1]["url"] == "https://example.com/b"
    assert "79,99 Euro" in result["sources"][1]["snippet"]


def test_duckduckgo_provider_parse_html_results_extracts_titles_snippets_and_urls():
    html = """
    <html>
      <body>
        <div class="result">
          <a class="result__a" href="https://trattoriaroma.de">Trattoria Roma</a>
          <a class="result__snippet">Italienisches Restaurant in Berlin Prenzlauer Berg mit Pasta und Pizza.</a>
        </div>
        <div class="result">
          <a class="result__a" href="https://luigi-berlin.de/menu">Luigi Berlin</a>
          <div class="result__snippet">Speisekarte, Öffnungszeiten und Reservierung.</div>
        </div>
      </body>
    </html>
    """

    result = DuckDuckGoWebSearchProvider._parse_html_results(html)

    assert "- Trattoria Roma - Italienisches Restaurant in Berlin Prenzlauer Berg mit Pasta und Pizza." in result["text"]
    assert "- Luigi Berlin - Speisekarte, Öffnungszeiten und Reservierung." in result["text"]
    assert result["urls"] == ["https://trattoriaroma.de", "https://luigi-berlin.de/menu"]


def test_duckduckgo_provider_parse_html_results_normalizes_redirect_urls_and_alt_markup():
    html = """
    <html>
      <body>
        <div class="web-result">
          <h2>
            <a href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fosteria-centro.de%2Freservierung">Osteria Centro</a>
          </h2>
          <div class="excerpt">Reservierung und italienische Küche in Berlin Prenzlauer Berg.</div>
        </div>
      </body>
    </html>
    """

    result = DuckDuckGoWebSearchProvider._parse_html_results(html)

    assert "- Osteria Centro - Reservierung und italienische Küche in Berlin Prenzlauer Berg." in result["text"]
    assert result["urls"] == ["https://osteria-centro.de/reservierung"]


def test_duckduckgo_provider_parse_html_results_falls_back_to_generic_external_links():
    html = """
    <html>
      <head><title>DuckDuckGo</title></head>
      <body>
        <div>
          <a href="https://trattoria-roma.de">Trattoria Roma</a>
          <span>Italienisches Restaurant in Berlin Prenzlauer Berg mit Speisekarte.</span>
        </div>
      </body>
    </html>
    """

    result = DuckDuckGoWebSearchProvider._parse_html_results(html)

    assert "- Trattoria Roma - Italienisches Restaurant in Berlin Prenzlauer Berg mit Speisekarte." in result["text"]
    assert result["urls"] == ["https://trattoria-roma.de"]


@pytest.mark.asyncio
async def test_duckduckgo_provider_search_appends_html_results_when_instant_answer_is_weak():
    provider = DuckDuckGoWebSearchProvider()
    instant_payload = {
        "AbstractText": "Keine prägnanten Ergebnisse.",
        "RelatedTopics": [],
        "Results": [],
    }
    html_result = {
        "text": "- Trattoria Roma - Italienisches Restaurant in Berlin Prenzlauer Berg",
        "urls": ["https://trattoriaroma.de"],
        "usage": {},
        "cost": {},
    }

    response_mock = Mock()
    response_mock.raise_for_status.return_value = None
    response_mock.json.return_value = instant_payload

    with patch("backend.services.websearch.duckduckgo_provider.requests.get", return_value=response_mock), patch(
        "backend.services.websearch.duckduckgo_provider.DuckDuckGoWebSearchProvider._search_html_results",
        AsyncMock(return_value=html_result),
    ), patch(
        "backend.services.websearch.duckduckgo_provider.DuckDuckGoWebSearchProvider._search_via_library",
        AsyncMock(return_value=None),
    ):
        result = await provider.search(api_key="", query="italienische Restaurants Berlin Prenzlauer Berg", model=None)

    assert result["text"] == html_result["text"]
    assert [s["url"] for s in result["sources"]] == html_result["urls"]


@pytest.mark.asyncio
async def test_duckduckgo_provider_search_soft_fails_to_empty_result_on_connection_error():
    provider = DuckDuckGoWebSearchProvider()

    with patch(
        "backend.services.websearch.duckduckgo_provider.requests.get",
        side_effect=requests.exceptions.ConnectionError("captcha block"),
    ), patch(
        "backend.services.websearch.duckduckgo_provider.DuckDuckGoWebSearchProvider._search_via_library",
        AsyncMock(return_value=None),
    ):
        result = await provider.search(api_key="", query="italienische Restaurants Berlin", model=None)

    assert result == {"text": "", "sources": [], "metadata": {"provider": "duckduckgo"}}
