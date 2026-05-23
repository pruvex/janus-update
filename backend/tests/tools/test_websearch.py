from unittest.mock import AsyncMock, Mock, patch
import json

import pytest
import requests

from backend.data import schemas
from backend.renderers.attribution import append_tool_attributions_from_tools
from backend.renderers.implementations.unified_websearch_renderer import UnifiedWebSearchRenderer
from backend.renderers.websearch_templates import WebSearchTemplateEngine
from backend.services.websearch.gemini_provider import (
    GeminiWebSearchProvider,
    _build_gemini_native_websearch_prompt,
    _extract_clean_sources_from_metadata,
)
from backend.services.websearch.duckduckgo_provider import DuckDuckGoWebSearchProvider
from backend.services.websearch.openai_provider import coerce_openai_websearch_model, _build_diamond_search_system_prompt
from backend.services.websearch.query_bias import augment_query_with_local_bias, normalize_source_url, prioritize_german_sources
from backend.tool_registry import (
    _coerce_websearch_model_for_provider,
    _normalize_websearch_query,
    _resolve_news_detail_sources,
    websearch_wrapper,
)
from backend.services.skill_router import (
    get_blocked_skills_for_query,
    is_realtime_search_query,
    prioritize_skills_for_query,
)


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
async def test_websearch_wrapper_persists_gemini_token_usage_costs():
    fake_db = Mock()

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.services.websearch.websearch.GEMINI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "Release-Liste",
                "sources": [{"url": "https://example.com/switch2", "title": "GamePro"}],
                "metadata": {"provider": "gemini"},
                "usage": {"input_tokens": 1200, "output_tokens": 340, "total_tokens": 1540, "query_count": 2},
                "cost": {"total_cost": 0.0025},
            }
        ),
    ), patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ) as create_cost_entry_mock:
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="welche spiele erscheinen nächsten monat für die nintendo switch 2",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    create_cost_entry_mock.assert_called_once()
    kwargs = create_cost_entry_mock.call_args.kwargs
    assert kwargs["amount"] == 0.0025
    assert kwargs["provider"] == "gemini"
    assert kwargs["model"] == "gemini-3-flash-preview"
    assert kwargs["source_type"] == "websearch"
    assert kwargs["input_tokens"] == 1200
    assert kwargs["output_tokens"] == 340
    assert kwargs["total_tokens"] == 1540
    assert kwargs["context_details"] == "query_count=2"
    fake_db.close.assert_called_once()


@pytest.mark.asyncio
async def test_websearch_wrapper_resolves_missing_ranking_list_source_with_targeted_search():
    fake_db = Mock()

    primary_result = {
        "text": (
            "Die 5 erfolgreichsten Basketballer aller Zeiten sind:\n\n"
            "Quelle der Liste: IMAGO.\n\n"
            "1. Michael Jordan\n"
            "Sechsfacher NBA-Champion."
        ),
        "sources": [],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    resolver_result = {
        "text": "IMAGO Ranking",
        "sources": [
            {
                "title": "Die besten Basketballspieler aller Zeiten - IMAGO",
                "url": "https://blog.imago-images.com/de/beste-basketballspieler-aller-zeiten",
                "snippet": "Ranking Liste der besten Basketballspieler aller Zeiten.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ) as create_cost_entry_mock:
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="wer sind die top 5 berühmtesten basketballspieler",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    assert rd["data"]["sources"][0]["url"] == "https://blog.imago-images.com/de/beste-basketballspieler-aller-zeiten"
    assert execute_mock.await_count == 2
    resolver_query = execute_mock.await_args_list[1].kwargs["query"]
    assert "IMAGO" in resolver_query
    assert "Ranking" in resolver_query
    assert "site:de" in resolver_query
    assert create_cost_entry_mock.call_count == 2
    assert fake_db.close.call_count == 2


@pytest.mark.asyncio
async def test_websearch_wrapper_does_not_attach_non_ranking_source_as_list_source():
    primary_result = {
        "text": (
            "Die 5 relevantesten Einträge aus der Suche sind:\n\n"
            "Quelle der Liste: Der Spiegel.\n\n"
            "1. Roger Federer\n"
            "Tennislegende."
        ),
        "sources": [],
        "metadata": {"provider": "openai"},
        "usage": {"query_count": 1},
        "cost": {"total_cost": 0.01},
    }
    resolver_result = {
        "text": "Spiegel Tennis Artikel",
        "sources": [
            {
                "title": "Roger Federer im Interview - DER SPIEGEL",
                "url": "https://www.spiegel.de/sport/roger-federer-interview",
                "snippet": "Ein Porträt über Roger Federer ohne Rangliste.",
            }
        ],
        "metadata": {"provider": "openai"},
        "usage": {"query_count": 1},
        "cost": {"total_cost": 0.01},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ), patch("backend.tool_registry.SessionLocal", return_value=Mock()), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="wer sind die top 5 berühmtesten Tennisspieler",
                provider="openai",
                model="gpt-5.4-nano",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    assert rd["data"]["sources"] == []


@pytest.mark.asyncio
async def test_websearch_wrapper_rejects_publisher_article_as_ranking_list_source():
    primary_result = {
        "text": (
            "Die 5 relevantesten EintrÃ¤ge aus der Suche sind:\n\n"
            "Quelle der Liste: Eurosport.\n\n"
            "1. Roger Federer\n"
            "Tennislegende."
        ),
        "sources": [],
        "metadata": {"provider": "openai"},
        "usage": {"query_count": 1},
        "cost": {"total_cost": 0.01},
    }
    resolver_result = {
        "text": "Eurosport Tennis Artikel",
        "sources": [
            {
                "title": "Historischer Dreikampf: Novak Djokovic Ã¼berholt Rafael Nadal und jagt Roger Federer",
                "url": "https://www.eurosport.de/tennis/historischer-dreikampf-novak-djokovic-uberholt-rafael-nadal-und-jagt-roger-federer_sto6973488/story.shtml",
                "snippet": "Ein Artikel Ã¼ber Djokovic, Nadal und Federer, aber keine Bestenliste.",
                "source": "Eurosport",
            }
        ],
        "metadata": {"provider": "openai"},
        "usage": {"query_count": 1},
        "cost": {"total_cost": 0.01},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ), patch("backend.tool_registry.SessionLocal", return_value=Mock()), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="wer sind die top 5 berÃ¼hmtesten Tennisspieler",
                provider="openai",
                model="gpt-5.4-nano",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    assert rd["data"]["sources"] == []


@pytest.mark.asyncio
async def test_websearch_wrapper_resolves_missing_release_entry_sources_in_one_batch():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. Death Cab For Cutie – I Built You A Tower: Die US-amerikanische Indie-Rock-Institution veröffentlicht ein neues Studioalbum am 5. Juni 2026.\n"
            "Quelle: Musikexpress.\n"
            "2. The Pretty Reckless – Dear God: Das vierte Studioalbum erscheint Ende Juni 2026.\n"
            "Quelle: Visions.\n"
            "3. Hard-Fi – Sweating Someone Else’s Fever: Die britische Indie-Rock-Band kehrt am 19. Juni 2026 mit einem neuen Werk zurück.\n"
            "Quelle: Musikexpress.\n"
            "4. Temples – BLISS: Die britische Band führt ihren Psychedelic-Rock auf diesem neuen Longplayer fort.\n"
            "Quelle: FluxFM."
        ),
        "sources": [
            {
                "title": "Death Cab For Cutie – I Built You A Tower - Musikexpress",
                "url": "https://www.musikexpress.de/death-cab-for-cutie-i-built-you-a-tower",
                "snippet": "Death Cab For Cutie veröffentlichen I Built You A Tower.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    resolver_result = {
        "text": "Release Quellen",
        "sources": [
            {
                "title": "The Pretty Reckless – Dear God - Visions",
                "url": "https://www.visions.de/news/the-pretty-reckless-dear-god",
                "snippet": "Visions meldet das neue Album Dear God von The Pretty Reckless.",
            },
            {
                "title": "Hard-Fi – Sweating Someone Else’s Fever - Musikexpress",
                "url": "https://www.musikexpress.de/hard-fi-sweating-someone-elses-fever",
                "snippet": "Musikexpress zum neuen Hard-Fi-Album Sweating Someone Else’s Fever.",
            },
            {
                "title": "Temples – BLISS - FluxFM",
                "url": "https://www.fluxfm.de/temples-bliss",
                "snippet": "FluxFM berichtet über BLISS von Temples.",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ) as create_cost_entry_mock:
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="welche neuen rockalben erscheinen nächsten monat",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    urls = [source["url"] for source in rd["data"]["sources"]]
    assert "https://www.visions.de/news/the-pretty-reckless-dear-god" in urls
    assert "https://www.musikexpress.de/hard-fi-sweating-someone-elses-fever" in urls
    assert "https://www.fluxfm.de/temples-bliss" in urls
    assert execute_mock.await_count == 2
    resolver_query = execute_mock.await_args_list[1].kwargs["query"]
    assert "The Pretty Reckless" in resolver_query
    assert "Hard-Fi" in resolver_query
    assert "Temples" in resolver_query
    assert create_cost_entry_mock.call_count == 2
    assert fake_db.close.call_count == 2


@pytest.mark.asyncio
async def test_websearch_wrapper_resolves_openai_news_with_official_site_query():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. GPT-5.5 Instant: OpenAI veroeffentlichte das Modell als neuen ChatGPT-Standard. Quelle: OpenAI.\n"
            "2. Einstellung von Sora: Die eigenstaendige Sora-App wurde eingestellt. Quelle: OpenAI."
        ),
        "sources": [
            {
                "title": "medium.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/medium",
                "snippet": "GPT-5.5 Instant OpenAI ChatGPT Standard Quelle: OpenAI.",
            },
            {
                "title": "digen.ai",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/digen",
                "snippet": "Sora wurde eingestellt.",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    resolver_result = {
        "text": "OpenAI detail sources",
        "sources": [
            {
                "title": "OpenAI GPT-5.5 Instant",
                "url": "https://openai.com/de-DE/index/gpt-5-5",
                "snippet": "GPT-5.5 Instant ist neuer ChatGPT-Standard.",
            },
            {
                "title": "OpenAI Sora update",
                "url": "https://openai.com/de-DE/index/sora-update",
                "snippet": "Die eigenstaendige Sora-App wurde eingestellt.",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="OpenAI News Mai 2026 Aktuell",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    urls = [source["url"] for source in rd["data"]["sources"]]
    assert "https://openai.com/de-DE/index/gpt-5-5" in urls
    assert "https://openai.com/de-DE/index/sora-update" in urls
    assert all("medium" not in url and "digen" not in url for url in urls[:2])
    assert execute_mock.await_count == 2
    resolver_query = execute_mock.await_args_list[1].kwargs["query"]
    assert '"GPT-5.5 Instant" site:openai.com' in resolver_query
    assert '"Einstellung von Sora" site:openai.com' in resolver_query


@pytest.mark.asyncio
async def test_websearch_wrapper_resolves_only_weak_news_targets():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. Elon Musk scheitert mit Klage: Das Gericht wies die Klage ab. Quelle: ChannelPartner.\n"
            "2. Spitzenposition im Bereich Coding-Agenten: Gartner stufte OpenAI als Marktführer ein. Quelle: OpenAI.\n"
            "3. Neue Sicherheitsinitiative Daybreak: OpenAI startet ein Cybersecurity-Programm. Quelle: ComputerBase."
        ),
        "sources": [
            {
                "title": "channelpartner.de",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner",
                "snippet": "1. Elon Musk scheitert mit Klage: Das Gericht wies die Klage ab. Quelle: ChannelPartner.",
            },
            {
                "title": "openai.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/openai-generic",
                "snippet": "Mai 2026 als Marktführer für KI-gestützte Entwicklerwerkzeuge in Unternehmen ein.",
            },
            {
                "title": "computerbase.de",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/computerbase-generic",
                "snippet": "(Quelle: OpenAI) (Quelle: OpenAI)",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    resolver_result = {
        "text": "detail repair",
        "sources": [
            {
                "title": "OpenAI Gartner Coding Agents",
                "url": "https://openai.com/de-DE/index/gartner-coding-agents",
                "snippet": "Spitzenposition im Bereich Coding-Agenten: Gartner stufte OpenAI als Marktführer ein.",
            },
            {
                "title": "ComputerBase Daybreak",
                "url": "https://www.computerbase.de/news/ki/openai-daybreak-cybersecurity/",
                "snippet": "Neue Sicherheitsinitiative Daybreak: OpenAI startet ein Cybersecurity-Programm.",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }
    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="OpenAI News Mai 2026 Aktuell",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    urls = [source["url"] for source in rd["data"]["sources"]]
    assert "https://openai.com/de-DE/index/gartner-coding-agents" in urls
    assert "https://www.computerbase.de/news/ki/openai-daybreak-cybersecurity/" in urls
    assert "https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner" in urls
    assert execute_mock.await_count == 2
    resolver_query = execute_mock.await_args_list[1].kwargs["query"]
    assert "Elon Musk scheitert" not in resolver_query
    assert '"Spitzenposition im Bereich Coding-Agenten" site:openai.com' in resolver_query
    assert '"Neue Sicherheitsinitiative Daybreak" "ComputerBase" site:de' in resolver_query


@pytest.mark.asyncio
async def test_websearch_wrapper_skips_global_fallback_for_news_queries():
    fake_db = Mock()
    primary_result = {
        "text": "1. Einstellung des Together-Mode in Teams: Microsoft stellt eine Teams-Ansicht um. Quelle: BornCity.",
        "sources": [
            {
                "title": "borncity.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/borncity",
                "snippet": "Einstellung des Together-Mode in Teams: Microsoft stellt eine Teams-Ansicht um. Quelle: BornCity.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(return_value=primary_result),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="Microsoft News aktuell Mai 2026",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    assert execute_mock.await_count == 1
    assert "latest news" not in execute_mock.await_args.kwargs["query"]


@pytest.mark.asyncio
async def test_news_source_repair_skips_when_elapsed_budget_is_exhausted():
    with patch("backend.tool_registry.execute_websearch_service", AsyncMock()) as execute_mock:
        sources = await _resolve_news_detail_sources(
            query="Microsoft News aktuell Mai 2026",
            text=(
                "1. Sicherheits-Patchday Mai 2026: Microsoft schliesst kritische Luecken. Quelle: Security-Insider.\n"
                "2. Entwicklerkonferenz Build 2026: Microsoft kuendigt neue Azure-Funktionen an. Quelle: Microsoft."
            ),
            sources=[],
            provider="gemini",
            model="gemini-3-flash-preview",
            api_key="gemini-key",
            persist_cost=lambda *_args, **_kwargs: None,
            elapsed_ms_fn=lambda: 25001,
        )

    assert sources == []
    execute_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_websearch_wrapper_does_not_reuse_one_provider_redirect_for_multiple_news_items():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. Kritische Sicherheits-Patches: Microsoft veroeffentlichte Notfall-Updates fuer Defender. Quelle: BornCity.\n"
            "2. Anpassung der Copilot-Integration: Nutzer koennen den Copilot-Button in Office verschieben. Quelle: BornCity.\n"
            "3. Fuehrungswechsel und Wachstumsziele: Yusuf Mehdi kuendigte seinen Abschied an. Quelle: BornCity."
        ),
        "sources": [
            {
                "title": "borncity.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/borncity",
                "snippet": (
                    "1. Kritische Sicherheits-Patches: Microsoft veroeffentlichte Notfall-Updates "
                    "fuer Defender. Quelle: BornCity."
                ),
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    resolver_result = {
        "text": "detail repair",
        "sources": [
            {
                "title": "BornCity Copilot Integration",
                "url": "https://www.borncity.com/blog/2026/05/22/microsoft-copilot-button-office/",
                "snippet": "Anpassung der Copilot-Integration: Nutzer koennen den Copilot-Button in Office verschieben.",
            },
            {
                "title": "BornCity Yusuf Mehdi Microsoft",
                "url": "https://www.borncity.com/blog/2026/05/22/microsoft-yusuf-mehdi-wachstumsziele/",
                "snippet": "Fuehrungswechsel und Wachstumsziele: Yusuf Mehdi kuendigte seinen Abschied an.",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }
    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, resolver_result]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="Microsoft News Mai 2026 Aktuell",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    urls = [source["url"] for source in rd["data"]["sources"]]
    assert "https://www.borncity.com/blog/2026/05/22/microsoft-copilot-button-office/" in urls
    assert "https://www.borncity.com/blog/2026/05/22/microsoft-yusuf-mehdi-wachstumsziele/" in urls
    assert execute_mock.await_count == 2
    resolver_query = execute_mock.await_args_list[1].kwargs["query"]
    assert "Kritische Sicherheits-Patches" not in resolver_query
    assert '"Anpassung der Copilot-Integration" "BornCity" site:de' in resolver_query
    assert '"Fuehrungswechsel und Wachstumsziele" "BornCity" site:de' in resolver_query


@pytest.mark.asyncio
async def test_websearch_wrapper_runs_limited_focused_news_repair_when_batch_recall_is_low():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. Windows 11 Recall und Datenschutz: Die Funktion erstellt lokale Snapshots. Quelle: hp.com.\n"
            "2. Microsoft Patchday Mai 2026: Der Konzern schliesst kritische Sicherheitsluecken. Quelle: Security-Insider.\n"
            "3. Fox Tempest: Microsoft geht gegen einen Cybercrime-Dienst vor. Quelle: Microsoft."
        ),
        "sources": [
            {
                "title": "hp.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/hp",
                "snippet": "Windows 11 Recall und Datenschutz: Die Funktion erstellt lokale Snapshots. Quelle: hp.com.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    batch_result = {
        "text": "batch found one",
        "sources": [
            {
                "title": "Security Insider Patchday Mai 2026",
                "url": "https://www.security-insider.de/microsoft-patchday-mai-2026/",
                "snippet": "Microsoft Patchday Mai 2026: Der Konzern schliesst kritische Sicherheitsluecken.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }
    focused_hp = {
        "text": "hp detail",
        "sources": [
            {
                "title": "HP Windows 11 Recall Datenschutz",
                "url": "https://www.hp.com/de-de/windows-11-recall-datenschutz",
                "snippet": "Windows 11 Recall und Datenschutz: Die Funktion erstellt lokale Snapshots.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40, "query_count": 1},
        "cost": {"total_cost": 0.0002},
    }
    focused_microsoft = {
        "text": "microsoft detail",
        "sources": [
            {
                "title": "Microsoft Fox Tempest",
                "url": "https://www.microsoft.com/de-de/security/blog/2026/05/fox-tempest/",
                "snippet": "Fox Tempest: Microsoft geht gegen einen Cybercrime-Dienst vor.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40, "query_count": 1},
        "cost": {"total_cost": 0.0002},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, batch_result, focused_hp, focused_microsoft]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="Microsoft News Mai 2026 Aktuell",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    urls = [source["url"] for source in rd["data"]["sources"]]
    assert "https://www.security-insider.de/microsoft-patchday-mai-2026/" in urls
    assert "https://www.hp.com/de-de/windows-11-recall-datenschutz" in urls
    assert "https://www.microsoft.com/de-de/security/blog/2026/05/fox-tempest/" in urls
    assert execute_mock.await_count == 4
    assert '"Windows 11 Recall und Datenschutz" site:hp.com' in execute_mock.await_args_list[2].kwargs["query"]
    assert '"Fox Tempest" site:microsoft.com' in execute_mock.await_args_list[3].kwargs["query"]


@pytest.mark.asyncio
async def test_websearch_wrapper_skips_focused_news_repair_when_batch_has_three_links():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. Windows 11 Recall und Datenschutz: Die Funktion erstellt lokale Snapshots. Quelle: hp.com.\n"
            "2. Microsoft Patchday Mai 2026: Der Konzern schliesst kritische Sicherheitsluecken. Quelle: Security-Insider.\n"
            "3. Fox Tempest: Microsoft geht gegen einen Cybercrime-Dienst vor. Quelle: Microsoft."
        ),
        "sources": [
            {
                "title": "hp.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/hp",
                "snippet": "Windows 11 Recall und Datenschutz: Die Funktion erstellt lokale Snapshots. Quelle: hp.com.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    batch_result = {
        "text": "batch found three",
        "sources": [
            {
                "title": "HP Windows 11 Recall Datenschutz",
                "url": "https://www.hp.com/de-de/windows-11-recall-datenschutz",
                "snippet": "Windows 11 Recall und Datenschutz: Die Funktion erstellt lokale Snapshots.",
            },
            {
                "title": "Security Insider Patchday Mai 2026",
                "url": "https://www.security-insider.de/microsoft-patchday-mai-2026/",
                "snippet": "Microsoft Patchday Mai 2026: Der Konzern schliesst kritische Sicherheitsluecken.",
            },
            {
                "title": "Microsoft Fox Tempest",
                "url": "https://www.microsoft.com/de-de/security/blog/2026/05/fox-tempest/",
                "snippet": "Fox Tempest: Microsoft geht gegen einen Cybercrime-Dienst vor.",
            },
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 80, "output_tokens": 20, "total_tokens": 100, "query_count": 1},
        "cost": {"total_cost": 0.0008},
    }
    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(side_effect=[primary_result, batch_result]),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="Microsoft News Mai 2026 Aktuell",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    assert execute_mock.await_count == 2


@pytest.mark.asyncio
async def test_websearch_wrapper_runs_focused_news_repair_when_batch_repair_fails():
    fake_db = Mock()
    primary_result = {
        "text": (
            "1. Office-Update fuer KI-Assistenten: Microsoft erlaubt flexiblere Copilot-Steuerung. Quelle: BornCity.\n"
            "2. Lokale Datenverarbeitung in Deutschland: Microsoft 365 Copilot verarbeitet Daten national. Quelle: Computerwoche.\n"
            "3. Neues News-Erlebnis in Microsoft Teams: SharePoint-News werden in Teams integriert. Quelle: Microsoft.\n"
            "4. Firmware-Aktualisierung fuer Surface-Geraete: Updates korrigieren Touch- und Pen-Probleme. Quelle: Dr. Windows."
        ),
        "sources": [
            {
                "title": "borncity.com",
                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/borncity",
                "snippet": "Office-Update fuer KI-Assistenten: Microsoft erlaubt flexiblere Copilot-Steuerung. Quelle: BornCity.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 100, "output_tokens": 40, "total_tokens": 140, "query_count": 1},
        "cost": {"total_cost": 0.001},
    }
    computerwoche_detail = {
        "text": "computerwoche detail",
        "sources": [
            {
                "title": "Computerwoche Microsoft 365 Copilot Deutschland",
                "url": "https://www.computerwoche.de/article/microsoft-365-copilot-deutschland.html",
                "snippet": "Lokale Datenverarbeitung in Deutschland: Microsoft 365 Copilot verarbeitet Daten national.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40, "query_count": 1},
        "cost": {"total_cost": 0.0002},
    }
    microsoft_detail = {
        "text": "microsoft detail",
        "sources": [
            {
                "title": "Microsoft Teams SharePoint News",
                "url": "https://www.microsoft.com/de-de/microsoft-365/blog/2026/05/teams-sharepoint-news/",
                "snippet": "Neues News-Erlebnis in Microsoft Teams: SharePoint-News werden in Teams integriert.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40, "query_count": 1},
        "cost": {"total_cost": 0.0002},
    }
    drwindows_detail = {
        "text": "dr windows detail",
        "sources": [
            {
                "title": "Dr. Windows Surface Firmware Update",
                "url": "https://www.drwindows.de/news/surface-firmware-update-mai-2026",
                "snippet": "Firmware-Aktualisierung fuer Surface-Geraete: Updates korrigieren Touch- und Pen-Probleme.",
            }
        ],
        "metadata": {"provider": "gemini"},
        "usage": {"input_tokens": 30, "output_tokens": 10, "total_tokens": 40, "query_count": 1},
        "cost": {"total_cost": 0.0002},
    }

    with patch("backend.tool_registry.keyring.get_password", return_value="gemini-key"), patch(
        "backend.tool_registry.execute_websearch_service",
        AsyncMock(
            side_effect=[
                primary_result,
                RuntimeError("Native Grounding failed"),
                computerwoche_detail,
                microsoft_detail,
                drwindows_detail,
            ]
        ),
    ) as execute_mock, patch("backend.tool_registry.SessionLocal", return_value=fake_db), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="Microsoft News Aktuelles Mai 2026",
                provider="gemini",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    urls = [source["url"] for source in rd["data"]["sources"]]
    assert "https://www.computerwoche.de/article/microsoft-365-copilot-deutschland.html" in urls
    assert "https://www.microsoft.com/de-de/microsoft-365/blog/2026/05/teams-sharepoint-news/" in urls
    assert "https://www.drwindows.de/news/surface-firmware-update-mai-2026" in urls
    assert execute_mock.await_count == 5
    assert (
        '"Lokale Datenverarbeitung in Deutschland" "Computerwoche" site:de'
        in execute_mock.await_args_list[2].kwargs["query"]
    )
    assert '"Neues News-Erlebnis in Microsoft Teams" site:microsoft.com' in execute_mock.await_args_list[3].kwargs["query"]
    assert (
        '"Firmware-Aktualisierung fuer Surface-Geraete" "Dr. Windows" site:de'
        in execute_mock.await_args_list[4].kwargs["query"]
    )


@pytest.mark.asyncio
async def test_gemini_provider_costs_native_search_by_tokens_when_usage_metadata_exists():
    provider = GeminiWebSearchProvider()
    fake_response = {
        "usageMetadata": {
            "promptTokenCount": 111,
            "candidatesTokenCount": 22,
            "totalTokenCount": 133,
        },
        "candidates": [
            {
                "content": {"parts": [{"text": "1. Test Game (3. Juni 2026): Ein Actionspiel. (Quelle: IGN)."}]},
                "groundingMetadata": {
                    "webSearchQueries": ["Test Game Switch 2"],
                    "groundingChunks": [
                        {"web": {"uri": "https://www.ign.com/test-game", "title": "IGN Test Game"}}
                    ],
                    "groundingSupports": [
                        {"segment": {"text": "Test Game release date"}, "groundingChunkIndices": [0]}
                    ],
                },
            }
        ],
    }

    with patch("backend.services.websearch.gemini_provider.asyncio.to_thread", AsyncMock(return_value=fake_response)), patch(
        "backend.services.websearch.gemini_provider.calculate_cost",
        return_value=(
            {"input_tokens": 111, "output_tokens": 22, "total_tokens": 133},
            {"total_cost": 0.00042},
        ),
    ) as calculate_cost_mock:
        result = await provider.search("gemini-key", "Test Game Switch 2 release", "gemini-3-flash-preview")

    calculate_cost_mock.assert_called_once_with(
        "gemini-3-flash-preview",
        usage_data={"input_tokens": 111, "output_tokens": 22, "total_tokens": 133, "query_count": 1},
    )
    assert result["usage"]["input_tokens"] == 111
    assert result["usage"]["output_tokens"] == 22
    assert result["usage"]["total_tokens"] == 133
    assert result["usage"]["query_count"] == 1
    assert result["cost"]["total_cost"] == 0.00042


@pytest.mark.asyncio
async def test_gemini_provider_preserves_token_usage_when_model_price_is_missing():
    provider = GeminiWebSearchProvider()
    fake_response = {
        "usageMetadata": {
            "promptTokenCount": 222,
            "candidatesTokenCount": 44,
            "totalTokenCount": 266,
        },
        "candidates": [
            {
                "content": {"parts": [{"text": "1. Test Game (3. Juni 2026): Ein Actionspiel. Quelle: IGN."}]},
                "groundingMetadata": {
                    "webSearchQueries": ["Test Game Switch 2"],
                    "groundingChunks": [
                        {"web": {"uri": "https://www.ign.com/test-game", "title": "IGN Test Game"}}
                    ],
                },
            }
        ],
    }

    with patch("backend.services.websearch.gemini_provider.asyncio.to_thread", AsyncMock(return_value=fake_response)), patch(
        "backend.services.websearch.gemini_provider.calculate_cost",
        side_effect=[
            ({}, {}),
            ({"query_count": 1}, {"total_cost": 0.0}),
        ],
    ) as calculate_cost_mock:
        result = await provider.search("gemini-key", "Test Game Switch 2 release", "gemini-3-flash-preview")

    assert calculate_cost_mock.call_args_list[0].args[0] == "gemini-3-flash-preview"
    assert calculate_cost_mock.call_args_list[1].args[0] == "websearch_gemini"
    assert result["usage"]["input_tokens"] == 222
    assert result["usage"]["output_tokens"] == 44
    assert result["usage"]["total_tokens"] == 266
    assert result["usage"]["query_count"] == 1


@pytest.mark.asyncio
async def test_websearch_wrapper_normalizes_current_price_query_for_openai_search():
    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "ok",
                "sources": [{"url": "https://example.com/gold", "title": "Goldpreis"}],
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
    assert forwarded_query == "aktueller Preis einer Feinunze Gold 2026 in Euro Goldpreis Spotpreis"


def test_websearch_query_normalizes_platinum_price_to_eur_spotprice():
    forwarded_query = _normalize_websearch_query("weiviel kostet eine feinunze platin")

    assert "in Euro" in forwarded_query
    assert "Platinpreis" in forwarded_query
    assert "Spotpreis" in forwarded_query


def test_release_lookup_query_requires_realtime_websearch_route():
    assert is_realtime_search_query("welche spiele erscheinen nächsten monat für die nintendo switch 2")
    assert is_realtime_search_query("Nintendo Switch 2 upcoming games next month")


def test_ranking_query_requires_realtime_websearch_route():
    assert is_realtime_search_query("wer sind die top 5 berühmtesten basketballspieler")
    assert is_realtime_search_query("was sind im moment die besten bücher")
    assert is_realtime_search_query("top 5 ki tools für produktivität")
    assert not is_realtime_search_query("gib mir top 5 ideen für ein gedicht")


def test_news_update_query_prioritizes_rss_before_websearch():
    skills = ["system.websearch", "system.price_comparison", "system.rss_news"]

    assert is_realtime_search_query("was gibt es neues zu OpenAI")
    assert is_realtime_search_query("aktuelle Lage zu Ukraine")
    assert "system.rss_news" not in get_blocked_skills_for_query("was gibt es neues zu OpenAI")
    assert prioritize_skills_for_query("was gibt es neues zu OpenAI", skills)[:2] == [
        "system.rss_news",
        "system.websearch",
    ]


def test_gemini_ranking_prompt_preserves_requested_count_and_descriptions():
    prompt = _build_gemini_native_websearch_prompt("wer sind die top 5 berühmtesten basketballspieler")

    assert "Top 3 Titel, keine Beschreibungen" not in prompt
    assert "Halte dich an die angefragte Anzahl" in prompt
    assert "1-2 informative Saetze" in prompt
    assert "Ranking-/Toplisten-Seite als Hauptquelle" in prompt
    assert "Keine separate Quellenliste" in prompt
    assert "Bevorzuge deutschsprachige Quellen" in prompt


def test_openai_ranking_prompt_matches_diamond_list_contract():
    prompt = _build_diamond_search_system_prompt("gpt-5.4-nano")

    assert "Halte dich an die angefragte Anzahl" in prompt
    assert "zuerst den Namen/Titel" in prompt
    assert "1-2 informative Saetze" in prompt
    assert "Ranking-/Toplisten-Seite als Hauptquelle" in prompt
    assert "Keine separate Quellenliste" in prompt
    assert "Bevorzuge deutschsprachige Quellen" in prompt


def test_ranking_queries_get_german_source_bias_without_price_cost_bias():
    biased = augment_query_with_local_bias("wer sind die top 5 berühmtesten basketballspieler")

    assert "deutschsprachige Quellen Deutschland" in biased
    assert '"in Euro"' not in biased
    assert "site:de" in biased
    purchase_bias = augment_query_with_local_bias("ich möchte gute kopfhörer bestellen")
    assert "deutschsprachige Quellen Deutschland" in purchase_bias
    assert "site:de" in purchase_bias
    assert '"in Euro"' not in purchase_bias


def test_german_sources_are_prioritized_without_dropping_fallback_links():
    sources = [
        {"title": "ESPN", "url": "https://www.espn.com/nba/story"},
        {"title": "SVT Sport", "url": "https://www.svt.se/sport/basket"},
        {"title": "Sport1", "url": "https://www.sport1.de/news/us-sport/nba/michael-jordan"},
        {"title": "Kicker", "url": "https://www.kicker.de/lebron-james-nba"},
        {"title": "NBA", "url": "https://www.nba.com/news/lebron-james"},
    ]

    prioritized = prioritize_german_sources(sources, max_items=5)

    assert [source["title"] for source in prioritized] == ["Sport1", "Kicker", "ESPN", "SVT Sport", "NBA"]


def test_source_url_hygiene_unwraps_redirects_and_drops_google_search_pages():
    assert normalize_source_url("https://www.google.com/search?q=Michael+Jordan+site%3Ade") == ""
    assert normalize_source_url("http://www.w3.org/2000/svg") == ""
    assert normalize_source_url("https://example.com/assets/logo.svg") == ""
    assert normalize_source_url("https://vertexaisearch.cloud.google.com/grounding-api-redirect/example") == (
        "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example"
    )
    assert normalize_source_url("https://www.google.com/url?q=https%3A%2F%2Fwww.spiegel.de%2Fsport%2Fmichael-jordan") == (
        "https://www.spiegel.de/sport/michael-jordan"
    )


def test_renderer_drops_svg_namespace_urls_from_ranking_list_sources():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "sources": [{"title": "IMAGO", "url": "http://www.w3.org/2000/svg"}],
        },
        (
            "Die 5 erfolgreichsten Basketballer aller Zeiten sind:\n\n"
            "Quelle der Liste: IMAGO.\n\n"
            "1. Michael Jordan\n"
            "Der sechsfache NBA-Champion gilt als der GOAT."
        ),
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "w3.org/2000/svg" not in rendered
    assert "Quelle der Liste: IMAGO. [Link]" not in rendered


def test_source_prioritization_moves_image_stock_sources_to_the_end():
    sources = [
        {"title": "IMAGO", "url": "https://www.imago-images.de/st/009123"},
        {"title": "SPIEGEL", "url": "https://www.spiegel.de/sport/michael-jordan"},
        {"title": "Wikipedia", "url": "https://de.wikipedia.org/wiki/LeBron_James"},
    ]

    prioritized = prioritize_german_sources(sources, max_items=3)

    assert [source["title"] for source in prioritized] == ["SPIEGEL", "Wikipedia", "IMAGO"]


def test_gemini_source_extraction_does_not_create_google_search_source_urls():
    extracted = _extract_clean_sources_from_metadata(
        {
            "webSearchQueries": ["Michael Jordan beste Basketballspieler site:de"],
            "groundingChunks": [],
            "searchEntryPoint": {"renderedContent": ""},
        }
    )

    assert extracted == []


def test_websearch_template_engine_routes_release_lookup_only():
    assert WebSearchTemplateEngine.is_release_lookup("welche spiele erscheinen nächsten monat für die nintendo switch 2")
    assert not WebSearchTemplateEngine.is_release_lookup("wie ist das wetter morgen in berlin")


def test_websearch_template_engine_routes_ranking_lookup_without_release_collision():
    assert WebSearchTemplateEngine.is_ranking_lookup("wer sind die top 5 berühmtesten basketballspieler")
    assert WebSearchTemplateEngine.is_ranking_lookup("was sind im moment die besten bücher")
    assert not WebSearchTemplateEngine.is_ranking_lookup("welche spiele erscheinen nächsten monat für die nintendo switch 2")
    assert not WebSearchTemplateEngine.is_ranking_lookup("wie ist das wetter morgen in berlin")


def test_websearch_template_engine_release_list_contract():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "Nintendo Switch 2 Spiele Releases Juni 2026",
            "sources": [{"title": "IGN", "url": "https://www.ign.com/games/final-fantasy-vii-rebirth"}],
        },
        (
            "1. **Final Fantasy VII Rebirth erscheint am 3. Juni 2026 als Fortsetzung der RPG-Saga um Cloud Strife für die Switch 2 (Quelle**\n"
            "IGN)."
        ),
        "Nintendo Switch 2 Spiele Releases Juni 2026",
    )

    assert rendered == (
        "1. **Final Fantasy VII Rebirth (3. Juni 2026)**\n"
        "Eine Fortsetzung der RPG-Saga um Cloud Strife für die Switch 2.\n"
        "Preis: online leider nicht verfügbar.\n"
        "Quelle: IGN. [Link](https://www.ign.com/games/final-fantasy-vii-rebirth)"
    )


def test_websearch_template_engine_ranking_list_contract():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "sources": [{"title": "NBA", "url": "https://www.nba.com/news/history-nba-legend-michael-jordan"}],
        },
        (
            "1. **Michael Jordan:** Sechsfacher NBA-Champion und globale Basketball-Ikone, "
            "dessen Karriere die moderne NBA-Popkultur geprägt hat. (Quelle: NBA)."
        ),
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert rendered == (
        "Die 1 erfolgreichsten Basketballer aller Zeiten sind:\n\n"
        "Quelle der Liste: NBA.\n\n"
        "1. **Michael Jordan**\n"
        "Sechsfacher NBA-Champion und globale Basketball-Ikone, dessen Karriere die moderne NBA-Popkultur geprägt hat.\n"
        "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)"
    )
    assert "Preis:" not in rendered


def test_ranking_template_uses_list_source_and_entry_detail_link_when_both_exist():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "sources": [
                {
                    "title": "SPORT1",
                    "url": "https://www.sport1.de/galerie/nowitzki-jordan-lebron-co-die-besten-nba-spieler-aller-zeiten__40029D8B-0424-11E7-B3CE-F80F41FC6A62",
                    "snippet": "Ranking der besten Basketballspieler aller Zeiten mit Michael Jordan.",
                },
                {
                    "title": "Michael Jordan - Wikipedia",
                    "url": "https://de.wikipedia.org/wiki/Michael_Jordan",
                    "snippet": "Michael Jordan ist ein ehemaliger US-amerikanischer Basketballspieler.",
                },
            ],
        },
        "1. Michael Jordan: Sechsfacher NBA-Champion und globale Basketball-Ikone. Quelle: SPORT1.",
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "Quelle der Liste: SPORT1. [Link](https://www.sport1.de/galerie/nowitzki-jordan-lebron-co-die-besten-nba-spieler-aller-zeiten__40029D8B-0424-11E7-B3CE-F80F41FC6A62)" in rendered
    assert "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)" in rendered


def test_ranking_template_uses_german_wikipedia_detail_fallback_for_person_lists():
    rendered = WebSearchTemplateEngine.render(
        {"query": "wer sind die top 5 berühmtesten basketballspieler", "sources": []},
        "1. Magic Johnson: Revolutionärer Point Guard der Showtime-Lakers. Quelle: Tipico.",
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "Quelle der Liste: Tipico." in rendered
    assert "Details: [Link](https://de.wikipedia.org/wiki/Magic_Johnson)" in rendered


def test_ranking_template_generates_intro_when_model_omits_it():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "sources": [{"title": "SPOX", "url": "https://www.spox.com/de/sport/ussport/nba/ranking-beste-spieler"}],
        },
        "1. Michael Jordan: Sechsfacher NBA-Champion. Quelle: SPOX.",
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert rendered.startswith("Die 1 erfolgreichsten Basketballer aller Zeiten sind:\n\n")
    assert "Quelle der Liste: SPOX. [Link](https://www.spox.com/de/sport/ussport/nba/ranking-beste-spieler)" in rendered


def test_ranking_template_splits_person_name_from_sentence_without_colon():
    rendered = WebSearchTemplateEngine.render(
        {"query": "wer sind die top 5 berühmtesten basketballspieler", "sources": []},
        (
            "1. Michael Jordan gilt dank seiner sechs NBA-Titel mit den Chicago Bulls global als der größte Basketballer der Geschichte\n"
            "Quelle: Sport1.\n"
            "2. LeBron James hat als All-Time-Scoring-Leader der NBA neue Maßstäbe gesetzt\n"
            "Quelle: Sport1."
        ),
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "1. **Michael Jordan**\nGilt dank seiner sechs NBA-Titel" in rendered
    assert "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)" in rendered
    assert "2. **LeBron James**\nHat als All-Time-Scoring-Leader" in rendered
    assert "Details: [Link](https://de.wikipedia.org/wiki/LeBron_James)" in rendered
    assert "online leider nicht eindeutig" not in rendered


def test_ranking_template_repairs_existing_broken_detail_lines_and_relinks_list_source():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "sources": [{"title": "Sport1", "url": "https://www.sport1.de/galerie/nowitzki-jordan-lebron-co-die-besten-nba-spieler-aller-zeiten__40029D8B-0424-11E7-B3CE-F80F41FC6A62"}],
        },
        (
            "Die 5 erfolgreichsten Basketballer aller Zeiten sind:\n\n"
            "Quelle der Liste: Sport1.\n\n"
            "1. Michael Jordan gilt dank seiner sechs NBA-Titel global als der größte Basketballer der Geschichte\n"
            "Details: online leider nicht eindeutig verfügbar.\n\n"
            "2. LeBron James hat als All-Time-Scoring-Leader neue Maßstäbe gesetzt\n"
            "Details: online leider nicht eindeutig verfügbar."
        ),
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert rendered.startswith("Die 5 erfolgreichsten Basketballer aller Zeiten sind:\n\n")
    assert "Quelle der Liste: Sport1. [Link](https://www.sport1.de/galerie/nowitzki-jordan-lebron-co-die-besten-nba-spieler-aller-zeiten__40029D8B-0424-11E7-B3CE-F80F41FC6A62)" in rendered
    assert "1. **Michael Jordan**\nGilt dank seiner sechs NBA-Titel" in rendered
    assert "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)" in rendered
    assert "2. **LeBron James**\nHat als All-Time-Scoring-Leader" in rendered
    assert "Details: online leider nicht eindeutig" not in rendered


def test_ranking_template_does_not_fake_list_link_when_source_url_missing():
    rendered = WebSearchTemplateEngine.render(
        {"query": "wer sind die top 5 berühmtesten basketballspieler", "sources": []},
        (
            "Die 5 erfolgreichsten Basketballer aller Zeiten sind:\n\n"
            "Quelle der Liste: IMAGO.\n\n"
            "1. Michael Jordan\n"
            "Der sechsfache Champion der Chicago Bulls gilt als der Inbegriff des Basketballs.\n"
            "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)"
        ),
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "Quelle der Liste: IMAGO." in rendered
    assert "Quelle der Liste: IMAGO. [Link]" not in rendered


def test_ranking_template_does_not_hardcode_spiegel_list_link_when_source_url_missing():
    rendered = WebSearchTemplateEngine.render(
        {"query": "wer sind die top 5 berühmtesten basketballspieler", "sources": []},
        (
            "Die 5 erfolgreichsten Basketballer aller Zeiten sind:\n\n"
            "Quelle der Liste: Spiegel.\n\n"
            "1. Michael Jordan\n"
            "Der sechsfache NBA-Champion gilt als der GOAT.\n"
            "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)"
        ),
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "Quelle der Liste: Spiegel." in rendered
    assert "Quelle der Liste: Spiegel. [Link]" not in rendered


def test_ranking_template_does_not_link_plain_publisher_article_as_list_source():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berÃ¼hmtesten tennisspieler",
            "sources": [
                {
                    "title": "Historischer Dreikampf: Novak Djokovic Ã¼berholt Rafael Nadal und jagt Roger Federer",
                    "url": "https://www.eurosport.de/tennis/historischer-dreikampf-novak-djokovic-uberholt-rafael-nadal-und-jagt-roger-federer_sto6973488/story.shtml",
                    "snippet": "Ein Artikel Ã¼ber Djokovic, Nadal und Federer, aber keine Bestenliste.",
                    "source": "Eurosport",
                }
            ],
        },
        (
            "Die 5 relevantesten EintrÃ¤ge aus der Suche sind:\n\n"
            "Quelle der Liste: Eurosport.\n\n"
            "1. Roger Federer\n"
            "Der Schweizer gilt als eine der grÃ¶ÃŸten Figuren der Tennisgeschichte."
        ),
        "wer sind die top 5 berÃ¼hmtesten tennisspieler",
    )

    assert "Quelle der Liste: Eurosport." in rendered
    assert "Quelle der Liste: Eurosport. [Link]" not in rendered
    assert "eurosport.de/tennis/historischer-dreikampf" not in rendered


def test_ranking_template_does_not_fake_unknown_list_source_link():
    rendered = WebSearchTemplateEngine.render(
        {"query": "wer sind die top 5 berühmtesten basketballspieler", "sources": []},
        "1. Michael Jordan: Sechsfacher NBA-Champion. Quelle: unbekannte Quelle.",
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "Quelle der Liste: unbekannte Quelle." in rendered
    assert "Quelle der Liste: unbekannte Quelle. [Link]" not in rendered


def test_ranking_template_prefers_overview_source_for_list_link_over_wikipedia_detail():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "sources": [
                {"title": "Michael Jordan - Wikipedia", "url": "https://de.wikipedia.org/wiki/Michael_Jordan"},
                {
                    "title": "SPOX Ranking beste NBA-Spieler",
                    "url": "https://www.spox.com/de/sport/ussport/nba/ranking-beste-spieler",
                    "snippet": "Ranking Liste der besten Basketballspieler aller Zeiten.",
                },
            ],
        },
        "1. Michael Jordan: Sechsfacher NBA-Champion. Quelle: SPOX.",
        "wer sind die top 5 berühmtesten basketballspieler",
    )

    assert "Quelle der Liste: SPOX. [Link](https://www.spox.com/de/sport/ussport/nba/ranking-beste-spieler)" in rendered
    assert "Quelle der Liste: SPOX. [Link](https://de.wikipedia.org/wiki/Michael_Jordan)" not in rendered


def test_ranking_lookup_renderer_formats_entries_without_price_line_or_footer_noise():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "wer sind die top 5 berühmtesten basketballspieler",
            "text": (
                "1) Michael Jordan — Sechsfacher NBA-Champion und globale Basketball-Ikone.\n"
                "Quelle: NBA. (nba.com)\n\n"
                "2) LeBron James — All-Time-Scoring-Leader und eine prägende Figur der modernen NBA.\n"
                "Quelle: Britannica. (britannica.com)\n\n"
                "### Quellen\n"
                "* [NBA](https://www.nba.com/news/history-nba-legend-michael-jordan)"
            ),
            "sources": [
                {"title": "NBA", "url": "https://www.nba.com/news/history-nba-legend-michael-jordan"},
                {"title": "Britannica", "url": "https://www.britannica.com/biography/LeBron-James"},
            ],
        }
    )

    assert "1. **Michael Jordan**\nSechsfacher NBA-Champion" in rendered
    assert "2. **LeBron James**\nAll-Time-Scoring-Leader" in rendered
    assert "Preis:" not in rendered
    assert "1)" not in rendered
    assert "### Quellen" not in rendered
    assert "(nba.com)" not in rendered
    assert "Quelle der Liste: NBA." in rendered
    assert "Quelle der Liste: NBA. [Link]" not in rendered
    assert "Details: [Link](https://de.wikipedia.org/wiki/Michael_Jordan)" in rendered


def test_release_lookup_renderer_does_not_append_price_comparison_block():
    renderer = UnifiedWebSearchRenderer()
    renderer.product_map = {
        "switch2": {
            "name": "Nintendo Switch 2",
            "aliases": ["Nintendo Switch 2"],
            "links": {"idealo.de": "https://www.idealo.de/preisvergleich/OffersOfProduct/206193300_-switch-2-nintendo.html"},
        }
    }

    rendered = renderer.render(
        {
            "text": "1. **Mario Kart World**: Rennspiel fuer Nintendo Switch 2. Quelle: Nintendo.",
            "sources": [{"url": "https://www.nintendo.com/us/gaming-systems/switch-2/games/", "title": "Nintendo"}],
        },
        llm_text="Welche Spiele erscheinen naechsten Monat fuer Nintendo Switch 2?\n\n1. **Mario Kart World**: Rennspiel fuer Nintendo Switch 2. Quelle: Nintendo.",
    )

    assert "Preisvergleich" not in rendered
    assert "Idealo" not in rendered


def test_websearch_renderer_strips_global_research_raw_block():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "text": "1. **Mario Kart World**: Rennspiel fuer Switch 2. Quelle: Nintendo.\n\n[Global Research]\nRohmaterial nicht anzeigen.",
            "sources": [{"url": "https://www.nintendo.com/us/gaming-systems/switch-2/games/", "title": "Nintendo"}],
        }
    )

    assert "Mario Kart World" in rendered
    assert "Global Research" not in rendered
    assert "Rohmaterial" not in rendered


def test_release_lookup_renderer_formats_list_with_price_and_source_lines_without_vertex_footer():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 upcoming games release Juni 2026",
            "text": (
                "1. **Final Fantasy VII Rebirth (03.06.2026):** Das JRPG-Epos setzt die Geschichte um Cloud fort "
                "und kostet laut Suchergebnis 49,99 US-Dollar (Quelle: GameStop).\n"
                "2. **eFootball Kick-Off! (03.06.2026)**: Konamis Fussball-Simulation erscheint als dedizierte Version (Quelle: VGC)."
            ),
            "sources": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example", "title": "GameStop"}],
        }
    )

    assert "1. **Final Fantasy VII Rebirth (03.06.2026)**\nDas JRPG-Epos" in rendered
    assert "\n\n2. **eFootball Kick-Off! (03.06.2026)**\nKonamis" in rendered
    assert "Preis: voraussichtlich 49,99 US-Dollar laut Suchergebnis." in rendered
    assert "Preis: online leider nicht verfügbar." in rendered
    assert "Quelle: GameStop." in rendered
    assert "Quelle: VGC." in rendered
    assert "Quelle: GameStop. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/example)" in rendered
    assert "[vertexaisearch.cloud.google.com]" not in rendered


def test_release_lookup_renderer_formats_plain_gemini_numbered_entries():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 upcoming games release Juni 2026",
            "text": (
                "1. Final Fantasy VII Rebirth (3. Juni 2026): Das zweite Kapitel der RPG-Neuauflage erscheint als grafisch optimierte Version\n"
                "Quelle: IGN.\n"
                "2. Police Simulator: Patrol Officers (4. Juni 2026): Diese Simulation des Streifendienstes bietet verbesserte Shader\n"
                "Quelle: YouTube."
            ),
            "sources": [{"url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example", "title": "IGN"}],
        }
    )

    assert "1. **Final Fantasy VII Rebirth (3. Juni 2026)**\nDas zweite Kapitel" in rendered
    assert "Preis: online leider nicht verfügbar." in rendered
    assert "Quelle: IGN." in rendered
    assert "\n\n2. **Police Simulator: Patrol Officers (4. Juni 2026)**\nDiese Simulation" in rendered
    assert "Quelle: YouTube." in rendered
    assert "1. Final Fantasy VII Rebirth" not in rendered
    assert "Quelle: IGN. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/example)" in rendered
    assert "[vertexaisearch.cloud.google.com]" not in rendered


def test_release_lookup_renderer_uses_clickable_fallback_links_when_source_labels_do_not_match():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 upcoming games release Juni 2026",
            "text": (
                "1. Final Fantasy VII Rebirth (3. Juni 2026): Das RPG-Epos erscheint fuer Switch 2\n"
                "Quelle: GamesRadar.\n"
                "2. Police Simulator: Patrol Officers (4. Juni 2026): Realistische Polizeisimulation in Brighton\n"
                "Quelle: YouTube."
            ),
            "sources": [
                {
                    "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/first",
                    "title": "nintendolife.com",
                },
                {
                    "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/second",
                    "title": "example result",
                },
            ],
        }
    )

    assert "Quelle: GamesRadar. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/first)" in rendered
    assert "Quelle: YouTube. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/second)" in rendered
    assert "[vertexaisearch.cloud.google.com]" not in rendered


def test_release_lookup_renderer_prefers_item_detail_link_over_release_overview():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 Spiele Releases Juni 2026",
            "text": (
                "1. Final Fantasy VII Rebirth (3. Juni 2026): Das RPG-Epos erscheint fuer Switch 2\n"
                "Quelle: IGN."
            ),
            "sources": [
                {
                    "url": "https://www.ign.com/articles/nintendo-switch-2-games-release-dates-june-2026",
                    "title": "Nintendo Switch 2 games release dates for June 2026",
                    "snippet": "A list of all upcoming Switch 2 releases in June.",
                },
                {
                    "url": "https://www.ign.com/games/final-fantasy-vii-rebirth",
                    "title": "Final Fantasy VII Rebirth - IGN",
                    "snippet": "Final Fantasy VII Rebirth details, release date and platform information.",
                },
            ],
        }
    )

    assert "Quelle: IGN. [Link](https://www.ign.com/games/final-fantasy-vii-rebirth)" in rendered
    assert "games-release-dates-june-2026" not in rendered


def test_release_lookup_renderer_normalizes_openai_note_style_release_entries():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 Spiele Releases Juni 2026",
            "text": (
                "1. eFootball Kick-Off!: — Fußball-Game-Release für Nintendo Switch 2 am 3. Juni 2026. (Quelle\n"
                "GamePro) (gamepro.de).\n"
                "2. Final Fantasy VII Rebirth: — JRPG/Action-RPG-Release für Nintendo Switch 2 am 3. Juni 2026. (Quelle\n"
                "GamePro) (gamepro.de)."
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **eFootball Kick-Off! (3. Juni 2026)**\nFußball-Game-Release für Nintendo Switch 2." in rendered
    assert "2. **Final Fantasy VII Rebirth (3. Juni 2026)**\nJRPG/Action-RPG-Release für Nintendo Switch 2." in rendered
    assert "Quelle: GamePro. [Link](https://www.gamepro.de/artikel/switch-2-juni-releases)" in rendered
    assert "nicht eindeutig verfügbar" not in rendered
    assert "(gamepro.de)" not in rendered
    assert "—" not in rendered


def test_release_lookup_renderer_normalizes_openai_parenthesis_numbering_and_source_lines():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1) Star Fox (Switch 2, Remake) — Release am 25. Juni 2026, Action-Spiel/Schienen-Shooter; "
                "Nintendo Switch 2-exklusive Neuauflage des N64-Titels.\n"
                "Quelle: GamePro. (gamepro.de)\n\n"
                "2) Destroy All Humans! — Release am 23. Juni 2026, Action-/Schießspiel mit Humor "
                "(Alien-Invasion), für Nintendo Switch und Nintendo Switch 2.\n"
                "Quelle: GamesWirtschaft.de. (gameswirtschaft.de)"
            ),
            "sources": [
                {"title": "GamePro", "url": "https://www.gamepro.de/artikel/star-fox-switch-2"},
                {"title": "GamesWirtschaft.de", "url": "https://www.gameswirtschaft.de/release-liste/destroy-all-humans-switch-2"},
            ],
        }
    )

    assert "1. **Star Fox (Switch 2, Remake) (25. Juni 2026)**" in rendered
    assert "Action-Spiel/Schienen-Shooter; Nintendo Switch 2-exklusive Neuauflage" in rendered
    assert "Preis: online leider nicht verfügbar." in rendered
    assert "Quelle: GamePro. [Link](https://www.gamepro.de/artikel/star-fox-switch-2)" in rendered
    assert "2. **Destroy All Humans! (23. Juni 2026)**" in rendered
    assert "Quelle: GamesWirtschaft.de. [Link](https://www.gameswirtschaft.de/release-liste/destroy-all-humans-switch-2)" in rendered
    assert "1)" not in rendered
    assert "(gamepro.de)" not in rendered


def test_release_lookup_renderer_splits_openai_inline_dash_after_dated_title():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. eFootball Kick-Off! (03. Juni 2026) – Fußball-Simulation; Release-Termin für Nintendo Switch 2 im Juni 2026.\n"
                "Quelle: GamePro. (gamepro.de)\n\n"
                "2. Final Fantasy 7 Rebirth (03. Juni 2026) – JRPG-Blockbuster; kommt laut Juni-2026-Übersicht für Nintendo Switch 2.\n"
                "Quelle: GamePro. (gamepro.de)\n\n"
                "3. Monopoly (11. Juni 2026)\n"
                "Star Wars Heroes vs. Villains (11. Juni 2026) – Brettspiel-Umsetzung im Star-Wars-Setting; Nintendo Switch 2 Release.\n"
                "Quelle: GamePro. (gamepro.de)"
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **eFootball Kick-Off! (03. Juni 2026)**\nFußball-Simulation; Release-Termin" in rendered
    assert "1. **eFootball Kick-Off! (03. Juni 2026) –" not in rendered
    assert "2. **Final Fantasy 7 Rebirth (03. Juni 2026)**\nJRPG-Blockbuster" in rendered
    assert "3. **Monopoly: Star Wars Heroes vs. Villains (11. Juni 2026)**" in rendered
    assert "\nStar Wars Heroes vs. Villains (11. Juni 2026) –" not in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 3
    assert rendered.count("Quelle: GamePro. [Link](https://www.gamepro.de/artikel/switch-2-juni-releases)") == 3


def test_release_lookup_renderer_repairs_gemini_sentence_fragments_without_layout_regression():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. Final Fantasy VII Rebirth (3. Juni 2026): die Nintendo Switch 2 und bringt das Rollenspiel-Epos auf die Plattform.\n"
                "Quelle: IGN.\n\n"
                "2. Police Simulator: Patrol Officers (4. Juni 2026): veröffentlicht und bietet eine realitätsnahe Simulation des Polizeialltags.\n"
                "Quelle: GamePro."
            ),
            "sources": [
                {"title": "IGN", "url": "https://www.ign.com/games/final-fantasy-vii-rebirth"},
                {"title": "GamePro", "url": "https://www.gamepro.de/artikel/police-simulator-switch-2"},
            ],
        }
    )

    assert "1. **Final Fantasy VII Rebirth (3. Juni 2026)**\nErscheint für die Nintendo Switch 2 und bringt" in rendered
    assert "2. **Police Simulator: Patrol Officers (4. Juni 2026)**\nWird veröffentlicht und bietet" in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 2
    assert "Quelle: IGN. [Link](https://www.ign.com/games/final-fantasy-vii-rebirth)" in rendered
    assert "Quelle: GamePro. [Link](https://www.gamepro.de/artikel/police-simulator-switch-2)" in rendered


def test_release_lookup_renderer_moves_openai_hidden_release_dates_from_descriptions():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. eFootball Kick-Off!\n"
                "Fußballspiel für Nintendo Switch 2, geplant am 3. Juni 2026.\n"
                "Quelle: GamePro.\n\n"
                "2. Final Fantasy 7 Rebirth\n"
                "Action-/RPG (Square Enix), für den 3. Juni 2026 in der Switch-2-Release-Liste geführt.\n"
                "Quelle: GamePro."
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **eFootball Kick-Off! (3. Juni 2026)**\nFußballspiel für Nintendo Switch 2." in rendered
    assert "2. **Final Fantasy 7 Rebirth (3. Juni 2026)**\nAction-/RPG (Square Enix)." in rendered
    assert "geplant am" not in rendered
    assert "Release-Liste geführt" not in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 2
    assert rendered.count("Quelle: GamePro. [Link](https://www.gamepro.de/artikel/switch-2-juni-releases)") == 2


def test_release_lookup_renderer_normalizes_openai_dash_date_colon_context_style():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. eFootball Kick-Off! — 03. Juni 2026: Fußballspiel-Reihe (Kontext\n"
                "offizielles eFootball-Release).\n"
                "Quelle: GamePro.\n\n"
                "2. Final Fantasy 7 Rebirth — 03. Juni 2026: Rollenspiel-Blockbuster (Kontext\n"
                "Fortsetzung/Remake-Projekt der Final-Fantasy-7-Reihe).\n"
                "Quelle: GamePro."
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **eFootball Kick-Off! (03. Juni 2026)**\nFußballspiel-Reihe (offizielles eFootball-Release)." in rendered
    assert "2. **Final Fantasy 7 Rebirth (03. Juni 2026)**\nRollenspiel-Blockbuster (Fortsetzung/Remake-Projekt" in rendered
    assert "Kontext" not in rendered
    assert "— 03. Juni 2026:" not in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 2
    assert rendered.count("Quelle: GamePro. [Link](https://www.gamepro.de/artikel/switch-2-juni-releases)") == 2


def test_release_lookup_renderer_merges_body_subtitle_dates_and_removes_calendar_noise():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. eFootball Kick-Off! (03. Juni 2026)\n"
                "Fußball-Spiel für die Nintendo Switch 2; als Terminspiel im Juni-Kalender von GamePro gelistet.\n"
                "Quelle: GamePro.\n\n"
                "2. Monopoly\n"
                "Star Wars Heroes vs. Villains (11. Juni 2026) – Monopoly-Edition mit Star-Wars-Thema für die Switch 2; "
                "GamePro nennt den Release konkret für den 11. Juni.\n"
                "Quelle: GamePro.\n\n"
                "3. Denshattack! (17. Juni 2026)\n"
                "Action-/Arcade-lastiger Titel für die Switch 2; GamePro führt ihn als Juni-Release mit Datum 17. Juni.\n"
                "Quelle: GamePro.\n\n"
                "4. The Adventures of Elliot\n"
                "The Millennium Tales (18. Juni 2026) – Abenteuer-/Story-Game für die Switch 2; "
                "steht bei GamePro ebenfalls für den 18. Juni im Juni-Kalender.\n"
                "Quelle: GamePro."
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **eFootball Kick-Off! (03. Juni 2026)**\nFußball-Spiel für die Nintendo Switch 2." in rendered
    assert "2. **Monopoly: Star Wars Heroes vs. Villains (11. Juni 2026)**\nMonopoly-Edition mit Star-Wars-Thema für die Switch 2." in rendered
    assert "3. **Denshattack! (17. Juni 2026)**\nAction-/Arcade-lastiger Titel für die Switch 2." in rendered
    assert "4. **The Adventures of Elliot: The Millennium Tales (18. Juni 2026)**\nAbenteuer-/Story-Game für die Switch 2." in rendered
    assert "Terminspiel" not in rendered
    assert "Release konkret" not in rendered
    assert "mit Datum 17. Juni" not in rendered
    assert "18. Juni im Juni-Kalender" not in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 4


def test_release_lookup_renderer_splits_dated_title_dash_and_drops_additional_context():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. Denshattack! (17. Juni 2026) – Spielankündigung für die Switch 2 mit Release im Juni 2026; "
                "genaue Genre- und Entwicklerangaben stehen im Suchsnippet nicht.\n"
                "Zusätzlich (nicht im Juni-Block, aber im Kontext “kurz davor”): Star Fox (Release: 25. Juni 2026).\n"
                "Quelle: GamePro."
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **Denshattack! (17. Juni 2026)**\nSpielankündigung für die Switch 2" in rendered
    assert "Denshattack! (17. Juni 2026) –" not in rendered
    assert "Zusätzlich" not in rendered
    assert "Star Fox" not in rendered
    assert "Preis: online leider nicht verfügbar." in rendered
    assert "Quelle: GamePro. [Link](https://www.gamepro.de/artikel/switch-2-juni-releases)" in rendered


def test_release_lookup_renderer_removes_repeated_release_dates_from_description():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            "text": (
                "1. eFootball Kick-Off! (03. Juni 2026)\n"
                "Fußballspiel mit Live-Service-Charakter für die Nintendo Switch 2; erscheint am 3. Juni.\n"
                "Quelle: GamePro.\n\n"
                "2. Final Fantasy 7 Rebirth (03. Juni 2026)\n"
                "Action-RPG-Highlight, das laut GamePro ebenfalls am 3. Juni für die Nintendo Switch 2 ankommt.\n"
                "Quelle: GamePro."
            ),
            "sources": [{"title": "GamePro", "url": "https://www.gamepro.de/artikel/switch-2-juni-releases"}],
        }
    )

    assert "1. **eFootball Kick-Off! (03. Juni 2026)**\nFußballspiel mit Live-Service-Charakter für die Nintendo Switch 2." in rendered
    assert "2. **Final Fantasy 7 Rebirth (03. Juni 2026)**\nAction-RPG-Highlight." in rendered
    assert "erscheint am 3. Juni" not in rendered
    assert "ebenfalls am 3. Juni" not in rendered
    assert "laut GamePro" not in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 2


@pytest.mark.parametrize(
    ("query", "raw_text", "sources", "expected_lines"),
    [
        (
            "welche spiele erscheinen nächsten monat für die nintendo switch 2",
            (
                "1. Final Fantasy VII Rebirth (3. Juni 2026): Das Rollenspiel-Epos erscheint technisch optimiert für die Switch 2.\n"
                "Quelle: IGN.\n"
                "2. Monopoly\n"
                "Star Wars Heroes vs. Villains: Eine Brettspiel-Umsetzung im Star-Wars-Universum erscheint am 11. Juni 2026.\n"
                "Quelle: IGN."
            ),
            [{"title": "IGN", "url": "https://www.ign.com/example"}],
            [
                "1. **Final Fantasy VII Rebirth (3. Juni 2026)**\nDas Rollenspiel-Epos",
                "2. **Monopoly: Star Wars Heroes vs. Villains (11. Juni 2026)**\nEine Brettspiel-Umsetzung",
            ],
        ),
        (
            "welche filme erscheinen nächsten monat im kino",
            (
                "1) Echo Valley — Release am 12. Juni 2026, Thriller-Drama über eine Familie und ein verschwundenes Kind.\n"
                "Quelle: Filmstarts. (filmstarts.de)\n"
                "2) The Last Frontier — Release am 19. Juni 2026, Actionfilm mit Survival-Elementen und großem Ensemble.\n"
                "Quelle: Kino.de. (kino.de)"
            ),
            [
                {"title": "Filmstarts", "url": "https://www.filmstarts.de/kritiken/echo-valley"},
                {"title": "Kino.de", "url": "https://www.kino.de/film/the-last-frontier"},
            ],
            [
                "1. **Echo Valley (12. Juni 2026)**\nThriller-Drama",
                "2. **The Last Frontier (19. Juni 2026)**\nActionfilm",
            ],
        ),
        (
            "welche bücher erscheinen nächsten monat",
            (
                "1. **The Glass Library**\n"
                "(5. Juni 2026): Fantasy-Roman über eine verborgene Bibliothek und politische Intrigen.\n"
                "Quelle: Goodreads.\n"
                "2. **Mars Papers (18. Juni 2026):** Sachbuch über Raumfahrtpolitik und private Missionen (Quelle: Publishers Weekly)."
            ),
            [
                {"title": "Goodreads", "url": "https://www.goodreads.com/book/show/glass-library"},
                {"title": "Publishers Weekly", "url": "https://www.publishersweekly.com/mars-papers"},
            ],
            [
                "1. **The Glass Library (5. Juni 2026)**\nFantasy-Roman",
                "2. **Mars Papers (18. Juni 2026)**\nSachbuch",
            ],
        ),
        (
            "welche serien starten nächsten monat",
            (
                "1. Neon Harbor (8. Juni 2026): Sci-Fi-Serie über Ermittlungen in einer schwimmenden Metropole.\n"
                "Quelle: Variety.\n"
                "2. The Orchard (21. Juni 2026): Familiendrama mit Mystery-Elementen und internationalem Cast.\n"
                "Quelle: Deadline."
            ),
            [
                {"title": "Variety", "url": "https://variety.com/neon-harbor"},
                {"title": "Deadline", "url": "https://deadline.com/the-orchard"},
            ],
            [
                "1. **Neon Harbor (8. Juni 2026)**\nSci-Fi-Serie",
                "2. **The Orchard (21. Juni 2026)**\nFamiliendrama",
            ],
        ),
        (
            "welche steam games erscheinen nächsten monat",
            (
                "1. Iron Bloom (4. Juni 2026) – Taktikspiel mit Roguelite-Struktur und Koop-Modus.\n"
                "Quelle: Steam. (steampowered.com)\n"
                "2. **Deep Signal erscheint am 27. Juni 2026 als atmosphärisches Horror-Adventure in einer Unterwasserstation (Quelle**\n"
                "PC Gamer)."
            ),
            [
                {"title": "Steam", "url": "https://store.steampowered.com/app/iron-bloom"},
                {"title": "PC Gamer", "url": "https://www.pcgamer.com/deep-signal"},
            ],
            [
                "1. **Iron Bloom (4. Juni 2026)**\nTaktikspiel",
                "2. **Deep Signal (27. Juni 2026)**\nEin atmosphärisches Horror-Adventure",
            ],
        ),
        (
            "welche neuen rockalben erscheinen nÃ¤chsten monat",
            (
                "1. Evergrey â€“ Architects Of A New Weave: Die schwedische Progressive-Metal-Band verÃ¶ffentlicht ihr neues Album am 5. Juni 2026 Ã¼ber das Label Napalm Records\n"
                "Quelle: Rock Report.\n"
                "2. Death Cab For Cutie â€“ I Built You A Tower: Die US-amerikanische Indie-Rock-Band bringt ihr neues Werk am 5. Juni 2026 heraus, wobei der Sound EinflÃ¼sse aus Electro und Emorock vereint\n"
                "Quelle: Musikexpress."
            ),
            [
                {"title": "Rock Report", "url": "https://www.rock-report.de/evergrey-architects-of-a-new-weave"},
                {"title": "Musikexpress", "url": "https://www.musikexpress.de/death-cab-for-cutie-i-built-you-a-tower"},
            ],
            [
                "1. **Evergrey â€“ Architects Of A New Weave (5. Juni 2026)**\nDie schwedische Progressive-Metal-Band",
                "2. **Death Cab For Cutie â€“ I Built You A Tower (5. Juni 2026)**\nDie US-amerikanische Indie-Rock-Band bringt ein neues Werk heraus",
            ],
        ),
    ],
)
def test_release_list_template_contract_across_common_list_queries(query, raw_text, sources, expected_lines):
    rendered = WebSearchTemplateEngine.render(
        {"query": query, "text": raw_text, "sources": sources},
        raw_text,
        query,
    )

    assert rendered is not None
    for expected in expected_lines:
        assert expected in rendered
    assert rendered.count("Preis: online leider nicht verfügbar.") == 2
    assert rendered.count("[Link](") == 2
    assert "1)" not in rendered
    assert "Quelle\n" not in rendered
    assert "(gamepro.de)" not in rendered
    assert "(filmstarts.de)" not in rendered
    assert "(steampowered.com)" not in rendered
    assert "Quelle**" not in rendered
    assert "[vertexaisearch.cloud.google.com]" not in rendered


@pytest.mark.parametrize(
    ("query", "raw_text", "sources", "expected_lines"),
    [
        (
            "wer sind die top 5 berühmtesten basketballspieler",
            (
                "1) Michael Jordan — Sechsfacher NBA-Champion und globale Basketball-Ikone mit enormem kulturellem Einfluss.\n"
                "Quelle: NBA. (nba.com)\n"
                "2) LeBron James — Vierfacher Champion, All-Time-Scoring-Leader und prägende Figur der modernen NBA.\n"
                "Quelle: Britannica. (britannica.com)"
            ),
            [
                {"title": "NBA", "url": "https://www.nba.com/news/history-nba-legend-michael-jordan"},
                {"title": "Britannica", "url": "https://www.britannica.com/biography/LeBron-James"},
            ],
            [
                "1. **Michael Jordan**\nSechsfacher NBA-Champion",
                "2. **LeBron James**\nVierfacher Champion",
            ],
        ),
        (
            "was sind im moment die top 5 bücher",
            (
                "1. **Atomic Habits:** Ein praxisnaher Ratgeber über kleine Gewohnheiten und langfristige Verhaltensänderung (Quelle**\n"
                "Goodreads).\n"
                "2. The Women: Historischer Roman über US-Krankenschwestern im Vietnamkrieg und die Rückkehr in eine gespaltene Gesellschaft.\n"
                "Quelle: Publishers Weekly."
            ),
            [
                {"title": "Goodreads", "url": "https://www.goodreads.com/book/show/atomic-habits"},
                {"title": "Publishers Weekly", "url": "https://www.publishersweekly.com/the-women"},
            ],
            [
                "1. **Atomic Habits**\nEin praxisnaher Ratgeber",
                "2. **The Women**\nHistorischer Roman",
            ],
        ),
        (
            "top 5 ki tools für produktivität",
            (
                "1. Notion AI: KI-Assistent für Notizen, Wissensdatenbanken und Team-Dokumentation. Quelle: Notion.\n"
                "2. Perplexity AI: Recherche-Tool mit Antwortsynthese und Quellenverweisen für schnelle Wissensarbeit. Quelle: Perplexity."
            ),
            [
                {"title": "Notion", "url": "https://www.notion.com/product/ai"},
                {"title": "Perplexity", "url": "https://www.perplexity.ai/"},
            ],
            [
                "1. **Notion AI**\nKI-Assistent",
                "2. **Perplexity AI**\nRecherche-Tool",
            ],
        ),
        (
            "beste serien aktuell top 5",
            (
                "1. **Severance**\nMystery-Drama über getrennte Arbeits- und Privatidentitäten mit satirischem Blick auf Bürokratie.\n"
                "Quelle: Variety.\n"
                "2. **The Bear**\nDramedy über ein Restaurantteam, Stress, Familie und kreative Arbeit in der Küche.\n"
                "Quelle: Rotten Tomatoes."
            ),
            [
                {"title": "Variety", "url": "https://variety.com/t/severance/"},
                {"title": "Rotten Tomatoes", "url": "https://www.rottentomatoes.com/tv/the_bear"},
            ],
            [
                "1. **Severance**\nMystery-Drama",
                "2. **The Bear**\nDramedy",
            ],
        ),
        (
            "beste kopfhörer 2026 top 5",
            (
                "1. Sony WH-1000XM6 — Over-Ear-Kopfhörer mit starker Geräuschunterdrückung und langer Akkulaufzeit.\n"
                "Quelle: The Verge. (theverge.com)\n"
                "2. Bose QuietComfort Ultra — Komfortabler ANC-Kopfhörer mit räumlichem Klang und guter App-Steuerung.\n"
                "Quelle: CNET. (cnet.com)"
            ),
            [
                {"title": "The Verge", "url": "https://www.theverge.com/sony-wh-1000xm6-review"},
                {"title": "CNET", "url": "https://www.cnet.com/tech/mobile/bose-quietcomfort-ultra-review/"},
            ],
            [
                "1. **Sony WH-1000XM6**\nOver-Ear-Kopfhörer",
                "2. **Bose QuietComfort Ultra**\nKomfortabler ANC-Kopfhörer",
            ],
        ),
    ],
)
def test_ranking_list_template_contract_across_common_list_queries(query, raw_text, sources, expected_lines):
    rendered = WebSearchTemplateEngine.render(
        {"query": query, "text": raw_text, "sources": sources},
        raw_text,
        query,
    )

    assert rendered is not None
    for expected in expected_lines:
        assert expected in rendered
    assert rendered.count("[Link](") >= 2
    assert "Quelle der Liste:" in rendered
    assert rendered.count("Details: [Link](") == 2
    assert "Preis:" not in rendered
    assert "1)" not in rendered
    assert "Quelle\n" not in rendered
    assert "(nba.com)" not in rendered
    assert "(theverge.com)" not in rendered
    assert "Quelle**" not in rendered
    assert "[vertexaisearch.cloud.google.com]" not in rendered


def test_release_lookup_renderer_moves_leading_date_into_title_line():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 Spiele Releases Juni 2026",
            "text": (
                "1. **Final Fantasy VII Rebirth**\n"
                "(03.06.2026): Der zweite Teil des Remake-Projekts erscheint als technisch optimierte Version.\n"
                "Preis: online leider nicht verfügbar.\n"
                "Quelle: IGN."
            ),
            "sources": [],
        }
    )

    assert "1. **Final Fantasy VII Rebirth (03.06.2026)**" in rendered
    assert "\n(03.06.2026):" not in rendered
    assert "\nDer zweite Teil des Remake-Projekts" in rendered


def test_release_lookup_renderer_repairs_sentence_bold_and_split_source_markup():
    renderer = UnifiedWebSearchRenderer()

    rendered = renderer.render(
        {
            "query": "Nintendo Switch 2 Spiele Releases Juni 2026",
            "text": (
                "1. **Final Fantasy VII Rebirth erscheint am 3. Juni 2026 als Fortsetzung der RPG-Saga um Cloud Strife für die Switch 2 (Quelle**\n"
                "IGN).\n"
                "2. **eFootball Kick-Off! wird am 3. Juni 2026 als Fußball-Simulation mit neuen Online-Modi und Club-Management veröffentlicht (Quelle**\n"
                "GamesRadar).\n"
                "3. **Police Simulator**\n"
                "Patrol Officers startet am 4. Juni 2026 und bietet eine realistische Polizeisimulation in der fiktiven Stadt Brighton.\n"
                "Quelle: YouTube."
            ),
            "sources": [],
        }
    )

    assert "1. **Final Fantasy VII Rebirth (3. Juni 2026)**" in rendered
    assert "Eine Fortsetzung der RPG-Saga um Cloud Strife für die Switch 2." in rendered
    assert "Quelle: IGN." in rendered
    assert "2. **eFootball Kick-Off! (3. Juni 2026)**" in rendered
    assert "Eine Fußball-Simulation mit neuen Online-Modi und Club-Management veröffentlicht." in rendered
    assert "Quelle: GamesRadar." in rendered
    assert "3. **Police Simulator: Patrol Officers (4. Juni 2026)**" in rendered
    assert "realistische Polizeisimulation" in rendered
    assert "Quelle: YouTube." in rendered
    assert "Quelle**" not in rendered
    assert "Quelle: nicht eindeutig verfügbar" not in rendered


def test_release_lookup_template_moves_dates_and_subtitles_from_descriptions():
    rendered = WebSearchTemplateEngine.render(
        {
            "query": "Nintendo Switch 2 Spiele Releases Juni 2026",
            "sources": [
                {"title": "IGN", "url": "https://www.ign.com/example"},
                {"title": "YouTube", "url": "https://www.youtube.com/watch?v=abc"},
                {"title": "Reddit", "url": "https://www.reddit.com/r/example"},
            ],
        },
        (
            "1. **Final Fantasy VII Rebirth**\n"
            "Die technisch angepasste Portierung des JRPG-Epos erscheint am 3. Juni 2026 für die Switch 2.\n"
            "Preis: online leider nicht verfügbar.\n"
            "Quelle: IGN.\n\n"
            "2. **Police Simulator**\n"
            "Patrol Officers: Diese realistische Simulation des Polizeialltags in der Stadt Brighton wird am 4. Juni 2026 veröffentlicht.\n"
            "Preis: online leider nicht verfügbar.\n"
            "Quelle: YouTube.\n\n"
            "3. **Monopoly**\n"
            "Star Wars Heroes vs. Villains: Die digitale Brettspiel-Adaption im Star-Wars-Universum erscheint am 11. Juni 2026.\n"
            "Preis: online leider nicht verfügbar.\n"
            "Quelle: IGN.\n\n"
            "4. **Denshattack!**\n"
            "Dieser Titel wird laut aktuellen Release-Planungen für den 17. Juni 2026 auf der neuen Konsole gelistet.\n"
            "Preis: online leider nicht verfügbar.\n"
            "Quelle: Reddit.\n\n"
            "5. **The Adventures of Elliot**\n"
            "The Millennium Tales: Das am 18. Juni 2026 erscheinende Spiel bietet eine neue Abenteuererfahrung für die Plattform.\n"
            "Preis: online leider nicht verfügbar.\n"
            "Quelle: IGN."
        ),
        "Nintendo Switch 2 Spiele Releases Juni 2026",
    )

    assert "1. **Final Fantasy VII Rebirth (3. Juni 2026)**" in rendered
    assert "Die technisch angepasste Portierung des JRPG-Epos erscheint für die Switch 2." in rendered
    assert "2. **Police Simulator: Patrol Officers (4. Juni 2026)**" in rendered
    assert "Diese realistische Simulation des Polizeialltags in der Stadt Brighton wird veröffentlicht." in rendered
    assert "3. **Monopoly: Star Wars Heroes vs. Villains (11. Juni 2026)**" in rendered
    assert "4. **Denshattack! (17. Juni 2026)**" in rendered
    assert "5. **The Adventures of Elliot: The Millennium Tales (18. Juni 2026)**" in rendered
    assert "Preis: online leider nicht verfügbar." in rendered
    assert "Quelle: IGN. [Link](https://www.ign.com/example)" in rendered
    assert "https://www.ign.com/example" in rendered


def test_websearch_model_guard_rejects_cross_provider_models():
    assert _coerce_websearch_model_for_provider("openai", "gemini-3-flash-preview") == "gpt-5.4-nano"
    assert _coerce_websearch_model_for_provider("gemini", "gpt-5.4-mini") == "gemini-3-flash-preview"
    assert coerce_openai_websearch_model("gemini-3-flash-preview") == "gpt-5.4-nano"


def test_websearch_attribution_adds_clickable_source_before_suggestions():
    tool_results = [
        {
            "role": "tool",
            "name": "system_websearch",
            "_skill_id": "system.websearch",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "text": "Koeln gewann 2:0.",
                        "sources": [
                            {
                                "url": "https://www.kicker.de/fc-augsburg-gegen-1-fc-koeln",
                                "title": "Kicker Spielbericht",
                            }
                        ],
                    },
                }
            ),
        }
    ]
    text = "Der FC Koeln gewann 2:0.\n\n💡 Passende nächste Schritte:\n• Torschuetzen?"

    rendered = append_tool_attributions_from_tools(text, tool_results)

    assert "Quelle: [Link](https://www.kicker.de/fc-augsburg-gegen-1-fc-koeln) (kicker.de)" in rendered
    assert "[janus-source-1]:" not in rendered
    assert rendered.index("Quelle:") < rendered.index("Passende")


def test_websearch_attribution_keeps_inline_sources_without_duplicate_footer():
    tool_results = [
        {
            "role": "tool",
            "name": "system_websearch",
            "_skill_id": "system.websearch",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "sources": [
                            {
                                "url": "https://www.ign.com/games/example",
                                "title": "IGN",
                            }
                        ],
                    },
                }
            ),
        }
    ]
    text = (
        "1. **Example Game** - Ein Action-Adventure mit Fokus auf Erkundung. "
        "Quelle: [IGN](https://www.ign.com/games/example)"
    )

    rendered = append_tool_attributions_from_tools(text, tool_results)

    assert rendered == text
    assert rendered.count("Quelle:") == 1


def test_websearch_attribution_does_not_append_vertex_redirect_footer():
    tool_results = [
        {
            "role": "tool",
            "name": "system_websearch",
            "_skill_id": "system.websearch",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "sources": [
                            {
                                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example",
                                "title": "transfermarkt.de - 1. FC Koeln Spielplan",
                            }
                        ],
                    },
                }
            ),
        }
    ]

    rendered = append_tool_attributions_from_tools("Naechstes Spiel: offen.", tool_results)

    assert rendered == "Naechstes Spiel: offen."
    assert "[janus-source-1]:" not in rendered
    assert "vertexaisearch.cloud.google.com" not in rendered


def test_websearch_attribution_strips_existing_vertex_redirect_footer():
    tool_results = [
        {
            "role": "tool",
            "name": "system_websearch",
            "_skill_id": "system.websearch",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "sources": [
                            {
                                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example",
                                "title": "ign.com",
                            }
                        ],
                    },
                }
            ),
        }
    ]
    text = "Antwort.\n\n**Quelle:** [vertexaisearch.cloud.google.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/example)"

    rendered = append_tool_attributions_from_tools(text, tool_results)

    assert rendered == "Antwort."
    assert "vertexaisearch" not in rendered


def test_websearch_attribution_prefers_direct_source_link_from_gemini_source_block():
    tool_results = [
        {
            "role": "tool",
            "name": "system_websearch",
            "_skill_id": "system.websearch",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "sources": [
                            {
                                "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example",
                                "title": "dfb.de - Spielplan",
                            }
                        ],
                    },
                }
            ),
        }
    ]
    text = (
        "Naechstes Spiel: offen.\n\n"
        "### 3. Quellen\n"
        "* [fussballdaten.de](https://www.fussballdaten.de)\n"
        "* [dfb.de](https://www.dfb.de)\n"
    )

    rendered = append_tool_attributions_from_tools(text, tool_results)

    assert "### 3. Quellen" not in rendered
    assert "Quelle: [Link](https://www.fussballdaten.de) (fussballdaten.de)" in rendered
    assert "[janus-source-1]:" not in rendered
    assert "vertexaisearch" not in rendered


@pytest.mark.asyncio
async def test_websearch_wrapper_coerces_openai_cross_provider_model_before_search():
    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "ok",
                "sources": [{"url": "https://example.com/platin", "title": "Platinpreis"}],
                "metadata": {"provider": "openai"},
                "usage": {},
                "cost": {},
            }
        ),
    ) as openai_search_mock, patch("backend.tool_registry.SessionLocal", return_value=Mock()), patch(
        "backend.services.cost_service.create_cost_entry"
    ):
        result = await websearch_wrapper(
            schemas.WebsearchArgsV2(
                query="weiviel kostet eine feinunze platin",
                provider="openai",
                model="gemini-3-flash-preview",
            )
        )

    rd = result.model_dump() if hasattr(result, "model_dump") else result
    assert rd["status"] == "ok"
    assert openai_search_mock.await_args.kwargs["model"] == "gpt-5.4-nano"


@pytest.mark.asyncio
async def test_websearch_wrapper_does_not_append_euro_when_query_already_mentions_usd():
    with patch("backend.tool_registry.keyring.get_password", return_value="openai-key"), patch(
        "backend.services.websearch.websearch.OPENAI_PROVIDER.search",
        AsyncMock(
            return_value={
                "text": "ok",
                "sources": [{"url": "https://example.com/gold-usd", "title": "Gold spot price"}],
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
    prompt_text = captured["body"]["contents"][0]["parts"][0]["text"]
    assert "Nutzerfrage: Neuigkeiten zur EU Deutschland aktuell site:de deutschsprachige Quellen Deutschland" in prompt_text
    assert "site:de" in prompt_text
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
