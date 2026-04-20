import requests
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest

from backend.tools.geo_service import _build_local_business_search_query, _enrich_business_entry, _fallback_businesses_from_osm, _finalize_local_business_results, _probe_business_website_guess, find_local_business_tool, get_country_info_tool


@patch("backend.tools.geo_service.requests.get")
def test_get_country_info_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "name": {"common": "Germany"},
            "translations": {"deu": {"common": "Deutschland"}},
            "capital": ["Berlin"],
            "population": 83200000,
            "region": "Europe",
            "currencies": {"EUR": {"name": "Euro"}},
            "languages": {"deu": "German"},
        }
    ]
    mock_get.return_value = mock_response

    result = get_country_info_tool(country="Germany").model_dump()
    assert result["status"] == "ok"
    assert result["data"]["name"] == "Deutschland"
    assert result["data"]["capital"] == "Berlin"
    assert "Euro (EUR)" in result["data"]["currencies"]
    assert result["error"] is None
    assert "execution_time_ms" in result["metadata"]


@patch("backend.tools.geo_service.requests.get")
def test_get_country_info_not_found(mock_get):
    first_response = Mock()
    first_response.status_code = 404
    second_response = Mock()
    second_response.status_code = 404
    mock_get.side_effect = [first_response, second_response]

    result = get_country_info_tool(country="Nimmerland").model_dump()
    assert result["status"] == "error"
    assert result["error"]["code"] == "NOT_FOUND"
    assert "Nimmerland" in result["error"]["message"]
    assert result["data"] == {}
    assert mock_get.call_count == 2
    assert "execution_time_ms" in result["metadata"]


def test_build_local_business_search_query_uses_compact_query_for_ollama():
    result = _build_local_business_search_query(
        query="italienische Restaurants",
        location="Berlin Prenzlauer Berg",
        provider="ollama",
    )

    assert result == "italienische Restaurants Berlin Prenzlauer Berg"


def test_build_local_business_search_query_keeps_enriched_query_for_non_ollama():
    result = _build_local_business_search_query(
        query="italienische Restaurants",
        location="Berlin Prenzlauer Berg",
        provider="gemini",
    )

    assert result == (
        "italienische Restaurants in Berlin Prenzlauer Berg Adresse Telefonnummer Öffnungszeiten "
        "offizielle Website Speisekarte Menü Reservierung booking"
    )


@patch("backend.tools.geo_service.requests.get", side_effect=requests.exceptions.RequestException("API down"))
def test_get_country_info_api_error(mock_get):
    result = get_country_info_tool(country="France").model_dump()
    assert result["status"] == "error"
    assert result["error"]["code"] == "API_ERROR"
    assert "Datenbank ist derzeit nicht erreichbar" in result["error"]["message"]
    assert result["data"] == {}
    assert "execution_time_ms" in result["metadata"]


@patch("backend.tools.geo_service.requests.get")
def test_get_country_info_contract(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"population": 100}]
    mock_get.return_value = mock_response

    result = get_country_info_tool(country="Testland").model_dump()
    assert set(result.keys()) >= {"status", "data", "error", "metadata"}
    assert result["status"] in {"ok", "error"}
    assert isinstance(result["metadata"]["execution_time_ms"], (int, float))
    if result["status"] == "ok":
        assert isinstance(result["data"], dict)
        assert result["error"] is None
    else:
        assert result["data"] == {}
        assert isinstance(result["error"], dict)


@patch("backend.tools.geo_service.requests.get")
def test_get_country_info_translation_fallback_success(mock_get):
    first_response = Mock()
    first_response.status_code = 404

    second_response = Mock()
    second_response.status_code = 200
    second_response.json.return_value = [
        {
            "name": {"common": "France"},
            "translations": {"deu": {"common": "Frankreich"}},
            "capital": ["Paris"],
            "population": 68000000,
            "region": "Europe",
            "currencies": {"EUR": {"name": "Euro"}},
            "languages": {"fra": "French"},
        }
    ]

    mock_get.side_effect = [first_response, second_response]

    result = get_country_info_tool(country="France", language="de").model_dump()
    assert result["status"] == "ok"
    assert result["data"]["name"] == "Frankreich"
    assert result["error"] is None
    assert mock_get.call_count == 2
    assert "execution_time_ms" in result["metadata"]


@pytest.mark.asyncio
async def test_find_local_business_tool_returns_skill_response_success():
    search_payload = {
        "text": "- Luigi's Pizza\n- Trattoria Roma\n- Osteria Centro",
        "urls": ["https://example.com/luigi", "https://example.com/roma"],
    }
    llm_payload = {
        "text": (
            "Name: Luigi's Pizza\n"
            "Beschreibung: Bekannt für neapolitanische Pizza und lockere Atmosphäre.\n"
            "Kategorie: Geheimtipp\n"
            "Adresse: Große Bergstraße 1, Hamburg\n"
            "Öffnungszeiten: Mo-So 12:00-22:30\n"
            "Telefon: +49 40 123456\n"
            "E-Mail: ciao@luigi.de\n"
            "Website: https://luigi.de\n"
            "Speisekarte: https://luigi.de/menu\n"
            "Reservierung: https://luigi.de/reservieren\n\n"
            "Name: Trattoria Roma\n"
            "Beschreibung: Rustikale Pasta und große Portionen.\n"
            "Kategorie: Budget\n"
            "Adresse: Altonaer Straße 5, Hamburg\n"
            "Öffnungszeiten: Di-So 17:00-23:00\n"
            "Telefon: Nicht gefunden\n"
            "E-Mail: Nicht gefunden\n"
            "Website: https://trattoriaroma.de\n"
            "Speisekarte: Nicht gefunden\n"
            "Reservierung: Nicht gefunden"
        )
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value=llm_payload),
    ) as call_llm_mock, patch("backend.tools.geo_service.asyncio.create_task") as create_task_mock:
        result = (await find_local_business_tool(
            query="italienisches Restaurant",
            location="Hamburg Altona",
            limit=2,
            provider="gemini",
            model="gemini-2.0-flash",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert result["error"] is None
    assert result["metadata"]["suggestion"]["relevance_tags"] == ["local_business", "poi"]
    assert result["data"]["query"] == "italienisches Restaurant"
    assert result["data"]["location"] == "Hamburg Altona"
    assert result["data"]["result_count"] == 2
    assert len(result["data"]["businesses"]) == 2
    assert result["data"]["provider"] == "gemini"
    first_business = result["data"]["businesses"][0]
    assert first_business["name"] == "Luigi's Pizza"
    assert first_business["description"] == "Bekannt für neapolitanische Pizza und lockere Atmosphäre."
    assert first_business["category"] == "Geheimtipp"
    assert first_business["opening_hours"] == "Mo-So 12:00-22:30"
    assert first_business["phone"] == "+49 40 123456"
    assert first_business["email"] == "ciao@luigi.de"
    assert first_business["menu_url"] == "https://luigi.de/menu"
    assert first_business["reservation_url"] == "https://luigi.de/reservieren"
    assert first_business["website"] == "https://luigi.de"
    create_task_mock.assert_not_called()
    assert call_llm_mock.await_count == 1
    assert isinstance(result["metadata"]["execution_time_ms"], (int, float))


@pytest.mark.asyncio
async def test_find_local_business_tool_returns_ok_with_empty_results():
    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value={"text": "", "urls": []}),
    ):
        result = (await find_local_business_tool(
            query="Baumarkt",
            location="Leipzig",
            limit=3,
            provider="openai",
            model="gpt-5.4-nano",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert result["data"]["businesses"] == []
    assert result["data"]["result_count"] == 0
    assert result["metadata"]["suggestion"]["relevance_tags"] == ["local_business", "search"]


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_uses_osm_fallback_when_duckduckgo_soft_fails_with_empty_result():
    search_payload = {
        "text": "",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "Trattoria Roma",
            "description": "Italienisches Restaurant in Prenzlauer Berg.",
            "category": "italian",
            "address": "Schönhauser Allee 10, 10119 Berlin",
            "opening_hours": "Mo-So 12:00-22:00",
            "phone": "+49 30 123456",
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        }
    ]

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ) as osm_mock, patch(
        "backend.tools.geo_service._enrich_business_entry",
        AsyncMock(side_effect=lambda business, **kwargs: business),
    ), patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=5,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert result["data"]["result_count"] == 1
    assert result["data"]["businesses"][0]["name"] == "Trattoria Roma"
    osm_mock.assert_called_once()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_does_not_create_placeholder_businesses_from_no_result_text():
    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(
            return_value={
                "text": "Suchergebnisse ohne belastbare Treffer.",
                "urls": ["https://duckduckgo.com/?q=italienische+Restaurants+Berlin"],
            }
        ),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "Keine passenden Suchergebnisse gefunden.\nAdresse: Adresse nicht gefunden"}),
    ), patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=4,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert result["data"]["businesses"] == []
    assert result["data"]["result_count"] == 0


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_ignores_directory_hosts_in_url_fallback():
    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(
            return_value={
                "text": "Unklare Ergebnisse",
                "urls": [
                    "https://duckduckgo.com/?q=pizzeria+berlin",
                    "https://www.google.com/search?q=pizzeria+berlin",
                ],
            }
        ),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "- Nicht gefunden"}),
    ), patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="Pizzeria",
            location="Berlin",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert result["data"]["businesses"] == []
    assert result["data"]["result_count"] == 0


@pytest.mark.asyncio
async def test_find_local_business_tool_selectively_enriches_incomplete_top_results():
    initial_search_payload = {
        "text": "- Luigi's Pizza\n- Trattoria Roma\n- Osteria Centro",
        "urls": [
            "https://luigi.de",
            "https://trattoriaroma.de",
            "https://osteriacentro.de",
        ],
    }
    enrichment_search_payload = {
        "text": "Öffnungszeiten Mo-So 12:00-22:30. Speisekarte unter /menu. Reservierung unter /reservieren.",
        "urls": [
            "https://luigi.de/menu",
            "https://luigi.de/reservieren",
        ],
    }

    execute_websearch_mock = AsyncMock(side_effect=[initial_search_payload, enrichment_search_payload])
    call_llm_mock = AsyncMock(
        side_effect=[
            {
                "text": (
                    "Name: Luigi's Pizza\n"
                    "Beschreibung: Bekannt für neapolitanische Pizza und lockere Atmosphäre.\n"
                    "Kategorie: Geheimtipp\n"
                    "Adresse: Große Bergstraße 1, Hamburg\n"
                    "Öffnungszeiten: Nicht gefunden\n"
                    "Telefon: +49 40 123456\n"
                    "E-Mail: ciao@luigi.de\n"
                    "Website: https://luigi.de\n"
                    "Speisekarte: Nicht gefunden\n"
                    "Reservierung: Nicht gefunden\n\n"
                    "Name: Trattoria Roma\n"
                    "Beschreibung: Rustikale Pasta und große Portionen.\n"
                    "Kategorie: Budget\n"
                    "Adresse: Altonaer Straße 5, Hamburg\n"
                    "Öffnungszeiten: Di-So 17:00-23:00\n"
                    "Telefon: +49 40 55555\n"
                    "E-Mail: Nicht gefunden\n"
                    "Website: https://trattoriaroma.de\n"
                    "Speisekarte: https://trattoriaroma.de/menu\n"
                    "Reservierung: https://trattoriaroma.de/reservieren"
                )
            },
            {
                "text": (
                    "Öffnungszeiten: Mo-So 12:00-22:30\n"
                    "Speisekarte: https://luigi.de/menu\n"
                    "Reservierung: https://luigi.de/reservieren"
                )
            },
        ]
    )

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        execute_websearch_mock,
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        call_llm_mock,
    ):
        result = (await find_local_business_tool(
            query="italienisches Restaurant",
            location="Hamburg Altona",
            limit=2,
            provider="gemini",
            model="gemini-2.0-flash",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert execute_websearch_mock.await_count == 2
    assert call_llm_mock.await_count == 2
    businesses = result["data"]["businesses"]
    assert businesses[0]["opening_hours"] == "Mo-So 12:00-22:30"
    assert businesses[0]["menu_url"] == "https://luigi.de/menu"
    assert businesses[0]["reservation_url"] == "https://luigi.de/reservieren"
    assert businesses[1]["opening_hours"] == "Di-So 17:00-23:00"


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_timeout_uses_candidate_url_fallback():
    search_payload = {
        "text": "Treffer: Trattoria Roma, Luigi, Osteria Centro",
        "urls": [
            "https://trattoriaroma.de",
            "https://luigi-berlin.de/menu",
            "https://quandoo.de/luigi-berlin/reservierung",
        ],
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ) as execute_websearch_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(side_effect=TimeoutError("ollama timeout")),
    ) as call_llm_mock:
        result = (await find_local_business_tool(
            query="Italienisches Restaurant",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert result["error"] is None
    assert result["data"]["result_count"] == 2
    assert len(result["data"]["businesses"]) == 2
    assert result["data"]["summary"] == ""
    assert execute_websearch_mock.await_count >= 1
    assert call_llm_mock.await_count >= 1
    first_business = result["data"]["businesses"][0]
    assert first_business["source"] == "websearch_url_fallback"
    assert first_business["website"] == "https://trattoriaroma.de"
    assert first_business["name"] == "Trattoriaroma"
    second_business = result["data"]["businesses"][1]
    assert second_business["menu_url"] == "https://luigi-berlin.de/menu"


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_enriches_multiple_website_ready_osm_items():
    initial_search_payload = {
        "text": "Keine prägnanten Ergebnisse.",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "Trattoria Roma",
            "description": None,
            "category": "italian",
            "address": "Prenzlauer Allee 10, 10405 Berlin",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": "https://trattoriaroma.de",
            "contact": "https://trattoriaroma.de",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "Italienisches Restaurant",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Luigi",
            "description": None,
            "category": "italian",
            "address": "Berlin Prenzlauer Berg",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": "https://luigi-berlin.de",
            "contact": "https://luigi-berlin.de",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "Italienisches Restaurant",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Osteria Centro",
            "description": None,
            "category": "italian",
            "address": "Berlin Prenzlauer Berg",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "Italienisches Restaurant",
            "location": "Berlin Prenzlauer Berg",
        },
    ]
    execute_websearch_mock = AsyncMock(return_value=initial_search_payload)
    enrich_mock = AsyncMock(
        side_effect=[
            {
                **osm_businesses[0],
                "opening_hours": "Mo-So 12:00-22:00",
                "menu_url": "https://trattoriaroma.de/menu",
                "reservation_url": "https://trattoriaroma.de/book",
            },
            {
                **osm_businesses[1],
                "opening_hours": "Di-So 17:00-23:00",
                "menu_url": "https://luigi-berlin.de/speisekarte",
                "reservation_url": "https://luigi-berlin.de/reservierung",
            },
        ]
    )

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        execute_websearch_mock,
    ), patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch(
        "backend.tools.geo_service._enrich_business_entry",
        enrich_mock,
    ), patch(
        "backend.tools.geo_service.asyncio.create_task",
    ):
        result = (await find_local_business_tool(
            query="Italienisches Restaurant",
            location="Berlin Prenzlauer Berg",
            limit=3,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    assert result["status"] == "ok"
    assert execute_websearch_mock.await_count >= 1
    assert enrich_mock.await_count >= 1
    businesses = result["data"]["businesses"]
    by_name = {b["name"]: b for b in businesses}
    assert by_name["Trattoria Roma"]["opening_hours"] == "Mo-So 12:00-22:00"
    assert by_name["Trattoria Roma"]["menu_url"] == "https://trattoriaroma.de/menu"
    assert by_name["Trattoria Roma"]["reservation_url"] == "https://trattoriaroma.de/book"
    if enrich_mock.await_count >= 2:
        assert by_name["Luigi"]["opening_hours"] == "Di-So 17:00-23:00"
        assert by_name["Luigi"]["menu_url"] == "https://luigi-berlin.de/speisekarte"
        assert by_name["Luigi"]["reservation_url"] == "https://luigi-berlin.de/reservierung"
    if "Osteria Centro" in by_name:
        assert by_name["Osteria Centro"]["opening_hours"] is None


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_uses_url_fallback_when_extraction_returns_no_results_prose():
    search_payload = {
        "text": "Treffer: Trattoria Roma, Luigi, Osteria Centro",
        "urls": [
            "https://trattoriaroma.de",
            "https://luigi-berlin.de/menu",
        ],
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "Es wurden keine prägnanten Suchergebnisse gefunden, um passende Einträge zu generieren."}),
    ):
        result = (await find_local_business_tool(
            query="Italienisches Restaurant",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    assert businesses[0]["source"] == "websearch_url_fallback"
    assert businesses[0]["name"] == "Trattoriaroma"
    assert businesses[1]["menu_url"] == "https://luigi-berlin.de/menu"


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_uses_snippet_fallback_when_directory_urls_are_not_usable():
    search_payload = {
        "text": "Treffer: Trattoria Roma, Luigi, Osteria Centro",
        "urls": [
            "https://duckduckgo.com/?q=trattoria+roma+berlin",
            "https://www.google.com/search?q=luigi+berlin",
        ],
        "source": "duckduckgo",
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="Italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=3,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 3
    by_name = {b["name"]: b for b in businesses}
    tr = by_name["Trattoria Roma"]
    assert tr["source"] == "websearch_snippet_fallback"
    assert tr["address"] == "Berlin Prenzlauer Berg"
    assert by_name["Luigi"]["name"] == "Luigi"
    assert by_name["Osteria Centro"]["name"] == "Osteria Centro"
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_duckduckgo_url_fallback_skips_free_extraction_and_enrichment():
    search_payload = {
        "text": "Treffer: Trattoria Roma, Luigi, Osteria Centro",
        "urls": [
            "https://trattoriaroma.de",
            "https://luigi-berlin.de/menu",
            "https://quandoo.de/luigi-berlin/reservierung",
        ],
        "source": "duckduckgo",
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ), patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="Italienisches Restaurant",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    tr = next(b for b in businesses if "trattoria" in b["name"].lower())
    luigi = next(b for b in businesses if "luigi" in b["name"].lower())
    assert tr["source"] == "websearch_url_fallback"
    assert tr["website"] == "https://trattoriaroma.de"
    assert luigi["menu_url"] == "https://luigi-berlin.de/menu"


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_extracts_names_from_duckduckgo_bullet_snippets_with_extra_text():
    search_payload = {
        "text": (
            "- Trattoria Roma in Berlin Prenzlauer Berg - Italienisches Restaurant mit Pasta und Pizza\n\n"
            "- Luigi Berlin | Öffnungszeiten, Telefonnummer und Adresse\n\n"
            "- Osteria Centro, Berlin Prenzlauer Berg – Speisekarte und Reservierung"
        ),
        "urls": [
            "https://duckduckgo.com/?q=trattoria+roma+berlin+prenzlauer+berg",
            "https://www.google.com/search?q=luigi+berlin+prenzlauer+berg",
            "https://duckduckgo.com/?q=osteria+centro+berlin+prenzlauer+berg",
        ],
        "source": "duckduckgo",
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=3,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 3
    by_name = {b["name"]: b for b in businesses}
    assert set(by_name.keys()) >= {"Trattoria Roma", "Luigi Berlin", "Osteria Centro"}
    assert by_name["Trattoria Roma"]["source"] == "websearch_snippet_fallback"
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_snippet_fallback_ignores_no_result_text():
    search_payload = {
        "text": "Keine passenden Restaurants gefunden. Bitte versuche eine andere Suche.",
        "urls": [
            "https://duckduckgo.com/?q=italienische+restaurants+berlin",
        ],
        "source": "duckduckgo",
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="Italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=3,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    assert result["data"]["businesses"] == []
    assert result["data"]["result_count"] == 0
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_uses_osm_fallback_when_duckduckgo_returns_no_renderable_results():
    search_payload = {
        "text": "Keine prägnanten Ergebnisse.",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10435 Berlin",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Trattoria Roma",
            "description": None,
            "category": "italian",
            "address": "Prenzlauer Allee 10, 10405 Berlin",
            "opening_hours": "Mo-Sa 12:00-22:00",
            "phone": "+49 30 123456",
            "email": None,
            "website": "https://trattoriaroma.de",
            "contact": "https://trattoriaroma.de",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Osteria Centro",
            "description": None,
            "category": "italian;pizza",
            "address": "Berlin Prenzlauer Berg",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
    ]

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ) as osm_fallback_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    assert businesses[0]["source"] == "osm_overpass_fallback"
    assert businesses[0]["name"] == "Trattoria Roma"
    assert businesses[0]["website"] == "https://trattoriaroma.de"
    assert businesses[1]["name"] == "Osteria Centro"
    osm_fallback_mock.assert_called_once_with(
        "italienische Restaurants",
        "Berlin Prenzlauer Berg",
        2,
        osm_phase_deadline=ANY,
    )
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_enrich_business_entry_uses_direct_website_for_osm_fallback_without_llm():
    business = {
        "name": "Trattoria Roma",
        "description": None,
        "category": "italian",
        "address": "Prenzlauer Allee 10, 10405 Berlin",
        "opening_hours": None,
        "phone": None,
        "email": None,
        "website": "https://trattoriaroma.de",
        "contact": "https://trattoriaroma.de",
        "menu_url": None,
        "reservation_url": None,
        "source": "osm_overpass_fallback",
        "query": "italienische Restaurants",
        "location": "Berlin Prenzlauer Berg",
    }
    website_html = """
    <html>
      <body>
        <a href="/speisekarte">Speisekarte</a>
        <a href="/reservierung">Tisch reservieren</a>
        <p>Telefon: +49 30 123456</p>
        <p>E-Mail: ciao@trattoriaroma.de</p>
        <p>Mo-So 12:00-23:00</p>
      </body>
    </html>
    """
    website_response = Mock()
    website_response.text = website_html
    website_response.raise_for_status = Mock()

    with patch(
        "backend.tools.geo_service.requests.get",
        return_value=website_response,
    ) as requests_get_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock:
        enriched = await _enrich_business_entry(
            business,
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )

    assert enriched["menu_url"] == "https://trattoriaroma.de/speisekarte"
    assert enriched["reservation_url"] == "https://trattoriaroma.de/reservierung"
    assert enriched["phone"] == "+49 30 123456"
    assert enriched["email"] == "ciao@trattoriaroma.de"
    assert enriched["opening_hours"] == "Mo-So 12:00-23:00"
    requests_get_mock.assert_called_once()
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_enrich_business_entry_discards_bot_protection_pages():
    business = {
        "name": "Trattoria Shield",
        "description": None,
        "category": "italian",
        "address": "Berlin Prenzlauer Berg",
        "opening_hours": None,
        "phone": None,
        "email": None,
        "website": "https://trattoria-shield.de",
        "contact": "https://trattoria-shield.de",
        "menu_url": None,
        "reservation_url": None,
        "source": "osm_overpass_fallback",
        "query": "italienische Restaurants",
        "location": "Berlin Prenzlauer Berg",
    }
    website_response = Mock()
    website_response.url = "https://trattoria-shield.de/cdn-cgi/challenge-platform/h/g/check"
    website_response.text = "<html><body><h1>DDoS protection by Cloudflare</h1><p>Please enable JavaScript and cookies</p></body></html>"
    website_response.raise_for_status = Mock()

    with patch(
        "backend.tools.geo_service.requests.get",
        return_value=website_response,
    ) as requests_get_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock:
        enriched = await _enrich_business_entry(
            business,
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )

    assert enriched["website"] is None
    assert enriched["menu_url"] is None
    assert enriched["reservation_url"] is None
    assert enriched["contact"] is None
    requests_get_mock.assert_called_once()
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_prioritizes_more_complete_osm_results_before_limit():
    search_payload = {
        "text": "Keine prägnanten Ergebnisse.",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "Weak One",
            "description": None,
            "category": "italian",
            "address": "Berlin Prenzlauer Berg",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Strong One",
            "description": None,
            "category": "italian",
            "address": "Berlin Prenzlauer Berg",
            "opening_hours": "Mo-So 12:00-22:00",
            "phone": "+49 30 123456",
            "email": None,
            "website": "https://strong-one.de",
            "contact": "https://strong-one.de",
            "menu_url": "https://strong-one.de/menu",
            "reservation_url": "https://strong-one.de/book",
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Medium One",
            "description": None,
            "category": "italian",
            "address": "Berlin Prenzlauer Berg",
            "opening_hours": "Di-So 17:00-23:00",
            "phone": None,
            "email": None,
            "website": "https://medium-one.de",
            "contact": "https://medium-one.de",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
    ]

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    assert businesses[0]["name"] == "Strong One"
    assert businesses[1]["name"] == "Medium One"
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_discovers_missing_website_for_osm_entry():
    search_payload = {
        "text": "Keine prägnanten Ergebnisse.",
        "urls": [],
        "source": "duckduckgo",
    }
    discovery_payload = {
        "text": "I Due Forni Berlin offizielle Website",
        "urls": [
            "https://www.idueforni.de/",
            "https://www.idueforni.de/speisekarte",
            "https://www.idueforni.de/reservierung",
        ],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10119 Berlin",
            "opening_hours": "Mo-Su 12:00-24:00",
            "phone": "+49 30 44017333",
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        }
    ]
    enriched_business = {
        **osm_businesses[0],
        "website": "https://www.idueforni.de/",
        "menu_url": "https://www.idueforni.de/speisekarte",
        "reservation_url": "https://www.idueforni.de/reservierung",
        "contact": "+49 30 44017333 | https://www.idueforni.de/",
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(side_effect=[search_payload, discovery_payload]),
    ) as execute_websearch_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch(
        "backend.tools.geo_service._enrich_business_entry",
        AsyncMock(return_value=enriched_business),
    ) as enrich_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=4,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 1
    assert businesses[0]["name"] == "I Due Forni"
    assert businesses[0]["website"] == "https://www.idueforni.de/"
    assert businesses[0]["menu_url"] == "https://www.idueforni.de/speisekarte"
    assert businesses[0]["reservation_url"] == "https://www.idueforni.de/reservierung"
    assert execute_websearch_mock.await_count == 2
    assert enrich_mock.await_count == 0
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_guesses_valid_direct_domain_when_discovery_urls_are_empty():
    search_payload = {
        "text": "Fehler bei der DuckDuckGo-Suche: Connection aborted.",
        "urls": [],
        "source": "duckduckgo",
    }
    discovery_payload = {
        "text": "I Due Forni Berlin offizielle Website",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10119 Berlin",
            "opening_hours": "Mo-Su 12:00-24:00",
            "phone": "+49 30 44017333",
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        }
    ]

    guessed_response = Mock()
    guessed_response.raise_for_status = Mock()
    guessed_response.url = "https://www.idueforni.de/"
    guessed_response.text = "<html><body><h1>I Due Forni Berlin</h1><p>Schönhauser Allee 12, 10119 Berlin Prenzlauer Berg</p><a href='/speisekarte'>Speisekarte</a><a href='/reservierung'>Reservierung</a></body></html>"

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(side_effect=[search_payload, discovery_payload]),
    ) as execute_websearch_mock, patch(
        "backend.tools.geo_service.requests.get",
        Mock(return_value=guessed_response),
    ) as requests_get_mock, patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch(
        "backend.tools.geo_service._enrich_business_entry",
        AsyncMock(side_effect=lambda business, **kwargs: business),
    ) as enrich_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=4,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 1
    assert businesses[0]["website"] == "https://www.idueforni.de/"
    assert businesses[0]["menu_url"] == "https://www.idueforni.de/speisekarte"
    assert businesses[0]["reservation_url"] == "https://www.idueforni.de/reservierung"
    assert execute_websearch_mock.await_count == 2
    assert requests_get_mock.call_count >= 1
    enrich_mock.assert_not_awaited()
    call_llm_mock.assert_not_awaited()


def test_probe_business_website_guess_rejects_unrelated_domain_content():
    unrelated_response = Mock()
    unrelated_response.raise_for_status = Mock()
    unrelated_response.url = "https://www.random-example.de/"
    unrelated_response.text = "<html><body><h1>Random Example</h1><p>Completely unrelated business page.</p></body></html>"

    with patch("backend.tools.geo_service.requests.get", Mock(return_value=unrelated_response)):
        result = _probe_business_website_guess("https://www.random-example.de/", "I Due Forni")

    assert result is None


def test_probe_business_website_guess_rejects_similar_domain_without_berlin_location_evidence():
    similar_response = Mock()
    similar_response.raise_for_status = Mock()
    similar_response.url = "https://i-due-forni.de/"
    similar_response.text = "<html><body><h1>I Due Forni</h1><p>Willkommen in München.</p><a href='/menu'>Menu</a></body></html>"

    with patch("backend.tools.geo_service.requests.get", Mock(return_value=similar_response)):
        result = _probe_business_website_guess(
            "https://i-due-forni.de/",
            "I Due Forni",
            address="Schönhauser Allee 12, 10119 Berlin",
            location="Berlin Prenzlauer Berg",
        )

    assert result is None


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_prefers_more_canonical_guessed_domain():
    search_payload = {
        "text": "Fehler bei der DuckDuckGo-Suche: Connection aborted.",
        "urls": [],
        "source": "duckduckgo",
    }
    discovery_payload = {
        "text": "I Due Forni Berlin offizielle Website",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10119 Berlin",
            "opening_hours": "Mo-Su 12:00-24:00",
            "phone": "+49 30 44017333",
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        }
    ]

    dueforni_response = Mock()
    dueforni_response.raise_for_status = Mock()
    dueforni_response.url = "http://www.dueforni.com/"
    dueforni_response.text = "<html><body><h1>I Due Forni</h1><p>Roma Centro</p><a href='/menu'>Menu</a><a href='/book'>Book</a></body></html>"

    similar_response = Mock()
    similar_response.raise_for_status = Mock()
    similar_response.url = "https://i-due-forni.de/"
    similar_response.text = "<html><body><h1>I Due Forni</h1><p>Willkommen in München.</p><a href='/menu'>Menu</a><a href='/book'>Book</a></body></html>"

    idueforni_response = Mock()
    idueforni_response.raise_for_status = Mock()
    idueforni_response.url = "https://www.idueforni.de/"
    idueforni_response.text = "<html><body><h1>I Due Forni Berlin</h1><p>Schönhauser Allee 12, 10119 Berlin Prenzlauer Berg</p><a href='/speisekarte'>Speisekarte</a><a href='/reservierung'>Reservierung</a></body></html>"

    def _mock_requests_get(url, *args, **kwargs):
        if "i-due-forni.de" in url:
            return similar_response
        if "dueforni.com" in url:
            return dueforni_response
        if "idueforni.de" in url:
            return idueforni_response
        raise requests.exceptions.ConnectionError("unexpected url")

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(side_effect=[search_payload, discovery_payload]),
    ), patch(
        "backend.tools.geo_service.requests.get",
        Mock(side_effect=_mock_requests_get),
    ), patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=4,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 1
    assert businesses[0]["website"] == "https://www.idueforni.de/"
    assert businesses[0]["menu_url"] == "https://www.idueforni.de/speisekarte"
    assert businesses[0]["reservation_url"] == "https://www.idueforni.de/reservierung"
    call_llm_mock.assert_not_awaited()


def test_finalize_local_business_results_ollama_drops_weak_third_result_when_two_strong_exist():
    businesses = [
        {
            "name": "Trattoria Zoe",
            "website": "https://www.zoeberlin.de/",
            "menu_url": "https://www.zoeberlin.de/menu",
            "reservation_url": "https://www.zoeberlin.de/book",
            "opening_hours": "12:00-24:00",
            "phone": "+49 30 43720175",
        },
        {
            "name": "I Due Forni",
            "website": "https://www.idueforni.de/",
            "menu_url": "https://www.idueforni.de/speisekarte",
            "reservation_url": "https://www.idueforni.de/reservierung",
            "opening_hours": "Mo-Su 12:00-24:00",
            "phone": "+49 30 44017333",
        },
        {
            "name": "Trattoria Da Pia",
            "website": None,
            "menu_url": None,
            "reservation_url": None,
            "opening_hours": None,
            "phone": None,
        },
    ]

    finalized = _finalize_local_business_results(
        businesses,
        limit=3,
        provider="ollama",
        uses_duckduckgo_fallback=True,
    )

    assert [item["name"] for item in finalized] == ["Trattoria Zoe", "I Due Forni"]


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_does_not_burn_only_slot_on_blocked_website_target():
    search_payload = {
        "text": "Fehler bei der DuckDuckGo-Suche: Connection aborted.",
        "urls": [],
        "source": "duckduckgo",
    }
    osm_businesses = [
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10119 Berlin",
            "opening_hours": "Mo-Su 12:00-24:00",
            "phone": "+49 30 44017333",
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Trattoria Da Pia",
            "description": None,
            "category": "italian",
            "address": "Naugarder Straße 45 II, 10409 Berlin",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": "https://www.trattoria-da-pia.de",
            "contact": "https://www.trattoria-da-pia.de",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
    ]

    def _fake_enrich(entry, **kwargs):
        if entry["name"] == "Trattoria Da Pia":
            return {
                **entry,
                "website": None,
                "contact": None,
                "menu_url": None,
                "reservation_url": None,
            }
        if entry["name"] == "I Due Forni":
            return {
                **entry,
                "menu_url": "https://www.idueforni.de/speisekarte",
                "reservation_url": "https://www.idueforni.de/reservierung",
                "contact": "+49 30 44017333",
            }
        return entry

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_payload),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock, patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch(
        "backend.tools.geo_service._discover_missing_business_websites",
        AsyncMock(return_value=osm_businesses),
    ), patch(
        "backend.tools.geo_service._enrich_business_entry",
        AsyncMock(side_effect=_fake_enrich),
    ) as enrich_mock, patch("backend.tools.geo_service.asyncio.create_task"):
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    assert enrich_mock.await_count >= 1
    call_llm_mock.assert_not_awaited()


def test_fallback_businesses_from_osm_filters_suspicious_website_domains():
    overpass_response = Mock()
    overpass_response.raise_for_status = Mock()
    overpass_response.json.return_value = {
        "elements": [
            {
                "tags": {
                    "name": "Due Forni",
                    "website": "https://duckduckgo.com/y.js?ad_domain=example.com",
                    "phone": "+49 30 44017333",
                    "opening_hours": "Mo-Su 12:00-24:00",
                    "addr:street": "Schönhauser Allee",
                    "addr:housenumber": "12",
                    "addr:postcode": "10119",
                    "addr:city": "Berlin",
                }
            }
        ]
    }
    geo_result = Mock(latitude=52.54, longitude=13.42)

    with patch("backend.tools.geo_service.Nominatim") as nominatim_mock, patch(
        "backend.tools.geo_service.requests.get",
        return_value=overpass_response,
    ):
        nominatim_mock.return_value.geocode.return_value = geo_result
        businesses = _fallback_businesses_from_osm("italienische Restaurants", "Berlin Prenzlauer Berg", 4)

    assert len(businesses) == 1
    assert businesses[0]["website"] is None
    assert businesses[0]["contact"] == "+49 30 44017333"


def test_fallback_businesses_from_osm_retries_after_overpass_timeout():
    failing_response = Mock()
    failing_response.raise_for_status.side_effect = requests.HTTPError("504 Server Error: Gateway Timeout")

    success_response = Mock()
    success_response.raise_for_status = Mock()
    success_response.json.return_value = {
        "elements": [
            {
                "tags": {
                    "name": "Trattoria Roma",
                    "website": "https://trattoriaroma.de",
                    "phone": "+49 30 123456",
                    "opening_hours": "Mo-Sa 12:00-22:00",
                    "addr:street": "Prenzlauer Allee",
                    "addr:housenumber": "10",
                    "addr:postcode": "10405",
                    "addr:city": "Berlin",
                    "cuisine": "italian",
                }
            }
        ]
    }
    geo_result = Mock(latitude=52.54, longitude=13.42)

    with patch("backend.tools.geo_service.Nominatim") as nominatim_mock, patch(
        "backend.tools.geo_service.requests.get",
        side_effect=[failing_response, success_response],
    ) as requests_get_mock:
        nominatim_mock.return_value.geocode.return_value = geo_result
        businesses = _fallback_businesses_from_osm("italienische Restaurants", "Berlin Prenzlauer Berg", 4)

    assert len(businesses) == 1
    assert businesses[0]["name"] == "Trattoria Roma"
    assert businesses[0]["website"] == "https://trattoriaroma.de"
    assert requests_get_mock.call_count >= 2


def test_fallback_businesses_from_osm_broadens_when_strict_query_returns_too_few_matches():
    strict_response = Mock()
    strict_response.raise_for_status = Mock()
    strict_response.json.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "tags": {
                    "name": "Trattoria Roma",
                    "website": "https://trattoriaroma.de",
                    "phone": "+49 30 123456",
                    "opening_hours": "Mo-Sa 12:00-22:00",
                    "addr:street": "Prenzlauer Allee",
                    "addr:housenumber": "10",
                    "addr:postcode": "10405",
                    "addr:city": "Berlin",
                    "cuisine": "italian",
                },
            }
        ]
    }
    broad_response = Mock()
    broad_response.raise_for_status = Mock()
    broad_response.json.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "tags": {
                    "name": "Trattoria Roma",
                    "website": "https://trattoriaroma.de",
                    "phone": "+49 30 123456",
                    "opening_hours": "Mo-Sa 12:00-22:00",
                    "addr:street": "Prenzlauer Allee",
                    "addr:housenumber": "10",
                    "addr:postcode": "10405",
                    "addr:city": "Berlin",
                    "cuisine": "italian",
                },
            },
            {
                "type": "node",
                "id": 2,
                "tags": {
                    "name": "I Due Forni",
                    "phone": "+49 30 44017333",
                    "opening_hours": "Mo-Su 12:00-24:00",
                    "addr:street": "Schönhauser Allee",
                    "addr:housenumber": "12",
                    "addr:postcode": "10119",
                    "addr:city": "Berlin",
                },
            },
            {
                "type": "node",
                "id": 3,
                "tags": {
                    "name": "Random Burger",
                    "phone": "+49 30 999999",
                    "addr:street": "Teststraße",
                    "addr:housenumber": "1",
                    "addr:postcode": "10119",
                    "addr:city": "Berlin",
                },
            },
        ]
    }
    geo_result = Mock(latitude=52.54, longitude=13.42)

    with patch("backend.tools.geo_service.Nominatim") as nominatim_mock, patch(
        "backend.tools.geo_service.requests.get",
        side_effect=[strict_response, broad_response],
    ) as requests_get_mock:
        nominatim_mock.return_value.geocode.return_value = geo_result
        businesses = _fallback_businesses_from_osm("italienische Restaurants", "Berlin Prenzlauer Berg", 4)

    assert len(businesses) == 2
    assert businesses[0]["name"] == "Trattoria Roma"
    assert businesses[1]["name"] == "I Due Forni"
    assert all(business["name"] != "Random Burger" for business in businesses)
    assert requests_get_mock.call_count == 2


@pytest.mark.asyncio
async def test_enrich_business_entry_prefers_resolved_final_website_url():
    business = {
        "name": "Ristorante Example",
        "description": None,
        "category": "italian",
        "address": "Teststraße 1, 10405 Berlin",
        "opening_hours": None,
        "phone": None,
        "email": None,
        "website": "https://redirect.example/path",
        "contact": "https://redirect.example/path",
        "menu_url": None,
        "reservation_url": None,
        "source": "osm_overpass_fallback",
        "query": "italienische Restaurants",
        "location": "Berlin Prenzlauer Berg",
    }
    website_response = Mock()
    website_response.url = "https://ristorante-example.de"
    website_response.text = """
    <html>
      <body>
        <a href="/menu">Menu</a>
        <p>Telefon: +49 30 111222</p>
      </body>
    </html>
    """
    website_response.raise_for_status = Mock()

    with patch(
        "backend.tools.geo_service.requests.get",
        return_value=website_response,
    ) as requests_get_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock:
        enriched = await _enrich_business_entry(
            business,
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )

    assert enriched["website"] == "https://ristorante-example.de"
    assert enriched["contact"] == "+49 30 111222 | https://ristorante-example.de"
    assert enriched["menu_url"] == "https://ristorante-example.de/menu"
    requests_get_mock.assert_called_once()
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_enrich_business_entry_blocks_expired_domain_redirect_targets():
    business = {
        "name": "Trattoria Da Pia",
        "description": None,
        "category": "italian",
        "address": "Naugarder Straße 45 II, 10409 Berlin",
        "opening_hours": None,
        "phone": None,
        "email": None,
        "website": "https://www.trattoria-da-pia.de",
        "contact": "https://www.trattoria-da-pia.de",
        "menu_url": None,
        "reservation_url": None,
        "source": "osm_overpass_fallback",
        "query": "italienische Restaurants",
        "location": "Berlin Prenzlauer Berg",
    }
    website_response = Mock()
    website_response.url = "https://expireddomains.com/domain/trattoria-da-pia.de"
    website_response.text = """
    <html>
      <body>
        <a href="/menu">Menu</a>
        <a href="/booking">Reservierung</a>
        <p>Telefon: 01/03/2025</p>
      </body>
    </html>
    """
    website_response.raise_for_status = Mock()

    with patch(
        "backend.tools.geo_service.requests.get",
        return_value=website_response,
    ) as requests_get_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock:
        enriched = await _enrich_business_entry(
            business,
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )

    assert enriched["website"] is None
    assert enriched["menu_url"] is None
    assert enriched["reservation_url"] is None
    assert enriched["phone"] is None
    assert enriched["contact"] is None
    requests_get_mock.assert_called_once()
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_osm_fallback_still_runs_selective_enrichment():
    search_results = {
        "provider": "ollama",
        "source": "duckduckgo",
        "fallback_reason": "ollama_duckduckgo_fallback",
        "text": "Keine prägnanten Ergebnisse.",
        "urls": [],
    }
    osm_businesses = [
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10435 Berlin",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Trattoria Roma",
            "description": None,
            "category": "italian",
            "address": "Prenzlauer Allee 10, 10405 Berlin",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": "https://trattoriaroma.de",
            "contact": "https://trattoriaroma.de",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        }
    ]
    enriched_business = {
        **osm_businesses[1],
        "menu_url": "https://trattoriaroma.de/speisekarte",
        "reservation_url": "https://trattoriaroma.de/reservierung",
        "phone": "+49 30 123456",
        "opening_hours": "Mo-So 12:00-23:00",
        "contact": "+49 30 123456 | https://trattoriaroma.de",
    }

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_results),
    ), patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=osm_businesses,
    ), patch(
        "backend.tools.geo_service._enrich_business_entry",
        AsyncMock(return_value=enriched_business),
    ) as enrich_business_mock, patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock:
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=4,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    assert businesses[0]["name"] == "Trattoria Roma"
    assert businesses[0]["menu_url"] == "https://trattoriaroma.de/speisekarte"
    assert businesses[0]["reservation_url"] == "https://trattoriaroma.de/reservierung"
    assert businesses[0]["phone"] == "+49 30 123456"
    assert businesses[1]["name"] == "I Due Forni"
    enriched_input = enrich_business_mock.await_args_list[0].args[0]
    assert enriched_input["name"] == "Trattoria Roma"
    enrich_business_mock.assert_awaited_once()
    call_llm_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_local_business_tool_ollama_demotes_weak_osm_leftovers_in_final_results():
    search_results = {
        "provider": "ollama",
        "source": "duckduckgo",
        "fallback_reason": "ollama_duckduckgo_fallback",
        "text": "Keine prägnanten Ergebnisse.",
        "urls": [],
    }
    businesses_after_enrichment = [
        {
            "name": "Ristorante a Mano",
            "description": None,
            "category": "italian",
            "address": "Strausberger Platz 2, 10243 Berlin",
            "opening_hours": "Mo-Su 12:00-23:00",
            "phone": "+49 30 95598243",
            "email": None,
            "website": "https://www.amano-ristorante.de/",
            "contact": "+49 30 95598243 | https://www.amano-ristorante.de/",
            "menu_url": "https://www.amano-ristorante.de/menu",
            "reservation_url": "https://www.amano-ristorante.de/reservierung",
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "I Due Forni",
            "description": None,
            "category": "italian",
            "address": "Schönhauser Allee 12, 10119 Berlin",
            "opening_hours": "Mo-Su 12:00-24:00",
            "phone": "+49 30 44017333",
            "email": None,
            "website": None,
            "contact": "+49 30 44017333",
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
        {
            "name": "Trattoria Da Pia",
            "description": None,
            "category": "italian",
            "address": "Naugarder Straße 45 II, 10409 Berlin",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": None,
            "contact": None,
            "menu_url": None,
            "reservation_url": None,
            "source": "osm_overpass_fallback",
            "query": "italienische Restaurants",
            "location": "Berlin Prenzlauer Berg",
        },
    ]

    with patch(
        "backend.tools.geo_service.execute_websearch_service",
        AsyncMock(return_value=search_results),
    ), patch(
        "backend.tools.geo_service._fallback_businesses_from_osm",
        return_value=businesses_after_enrichment,
    ), patch(
        "backend.tools.geo_service._discover_missing_business_websites",
        AsyncMock(return_value=businesses_after_enrichment),
    ), patch(
        "backend.tools.geo_service._selectively_enrich_businesses",
        AsyncMock(return_value=businesses_after_enrichment),
    ), patch(
        "backend.tools.geo_service.llm_gateway.call_llm",
        AsyncMock(return_value={"text": "must not be called"}),
    ) as call_llm_mock:
        result = (await find_local_business_tool(
            query="italienische Restaurants",
            location="Berlin Prenzlauer Berg",
            limit=2,
            provider="ollama",
            model="gemma2:27b@test",
            api_key="dummy",
        )).model_dump()

    businesses = result["data"]["businesses"]
    assert len(businesses) == 2
    assert businesses[0]["name"] == "Ristorante a Mano"
    assert businesses[1]["name"] == "I Due Forni"
    assert all(item["name"] != "Trattoria Da Pia" for item in businesses)
    call_llm_mock.assert_not_awaited()
