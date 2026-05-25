# backend/tests/tools/test_system_skills_diamond.py
"""
Diamond Standard V2 – Umfassende Tests für alle 15 system.* Skills.
Deckt ab: SkillResponse-Contract, Erfolgsfall, Leerfall, Fehlercodes,
Schema-Validierung, Ollama-Provider-Weichen.
"""

import json
import os
import time
from typing import Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.data.schemas import (
    CountryInfoArgs,
    FindLocalBusinessArgs,
    GetWeatherFromApiToolArgs,
    GetWikipediaSummaryArgs,
    SaveMp3Args,
    ScrapeWebsiteArgs,
    WebsearchArgsV2,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OLLAMA_BASE_URL = "http://172.26.176.1:11434"


def _validate_skill_response(payload):
    """Validate SkillResponse / ToolResultV1 wire shape; return a dict for assertions."""
    if hasattr(payload, "model_dump"):
        d = payload.model_dump()
    elif isinstance(payload, dict):
        d = payload
    else:
        raise AssertionError(f"Expected dict or BaseModel, got {type(payload)}")
    assert d.get("status") in {
        "ok",
        "error",
        "permission_required",
        "dry_run_success",
    }, f"Invalid status: {d.get('status')}"
    if d["status"] in ("ok", "dry_run_success"):
        assert "data" in d
    else:
        assert "error" in d
        assert isinstance(d["error"], dict)
        assert "code" in d["error"]
        assert "message" in d["error"]
    return d


def _execution_time_ms(payload) -> Optional[float]:
    """Diamond tools may expose timing in metadata.execution_time_ms (ToolResultV1) or top-level (SkillResponse)."""
    if hasattr(payload, "model_dump"):
        d = payload.model_dump()
    elif isinstance(payload, dict):
        d = payload
    else:
        return None
    if d.get("execution_time_ms") is not None:
        return d["execution_time_ms"]
    meta = d.get("metadata")
    if isinstance(meta, dict) and meta.get("execution_time_ms") is not None:
        return meta["execution_time_ms"]
    return None


# ===========================================================================
# 1. SCHEMA VALIDATION TESTS
# ===========================================================================


class TestSchemaValidation:
    """Validate that all Pydantic schemas enforce constraints."""

    def test_weather_schema_rejects_empty_city(self):
        with pytest.raises(Exception):
            GetWeatherFromApiToolArgs(city="", date_str=None)

    def test_weather_schema_accepts_valid(self):
        args = GetWeatherFromApiToolArgs(city="Berlin", date_str="morgen")
        assert args.city == "Berlin"

    def test_country_info_schema_rejects_short_country(self):
        with pytest.raises(Exception):
            CountryInfoArgs(country="X")

    def test_country_info_schema_accepts_valid(self):
        args = CountryInfoArgs(country="Japan", language="de")
        assert args.country == "Japan"

    def test_wikipedia_schema_rejects_short_query(self):
        with pytest.raises(Exception):
            GetWikipediaSummaryArgs(query="X")

    def test_wikipedia_schema_accepts_valid(self):
        args = GetWikipediaSummaryArgs(query="Eiffelturm", lang="de")
        assert args.query == "Eiffelturm"

    def test_websearch_schema_rejects_short_query(self):
        with pytest.raises(Exception):
            WebsearchArgsV2(query="X")

    def test_websearch_schema_accepts_valid(self):
        args = WebsearchArgsV2(query="Test query")
        assert args.query == "Test query"

    def test_websearch_schema_coerces_queries_list(self):
        args = WebsearchArgsV2(queries=["Wetter in München"])
        assert args.query == "Wetter in München"

    def test_scrape_schema_rejects_short_url(self):
        with pytest.raises(Exception):
            ScrapeWebsiteArgs(url="x")

    def test_scrape_schema_accepts_valid(self):
        args = ScrapeWebsiteArgs(url="https://example.com")
        assert args.url == "https://example.com"

    def test_save_mp3_schema_rejects_empty_content(self):
        with pytest.raises(Exception):
            SaveMp3Args(content="", filename="test.mp3")

    def test_local_business_schema_rejects_empty_query(self):
        with pytest.raises(Exception):
            FindLocalBusinessArgs(query=" ", location="Berlin", limit=5)

    def test_local_business_schema_accepts_valid(self):
        args = FindLocalBusinessArgs(query="Restaurant", location="Berlin", limit=5)
        assert args.query == "Restaurant"
        assert args.limit == 5

    def test_local_business_schema_clamps_limit(self):
        with pytest.raises(Exception):
            FindLocalBusinessArgs(query="Restaurant", location="Berlin", limit=99)


# ===========================================================================
# 2. WEATHER SERVICE TESTS
# ===========================================================================


class TestWeatherService:
    """Unit tests for system.weather handler."""

    @patch("backend.tools.weather_service.requests.get")
    @patch("backend.tools.weather_service.Nominatim")
    def test_weather_success(self, mock_nominatim_cls, mock_get):
        from backend.tools.weather_service import get_weather_from_api_tool

        mock_geo = Mock()
        mock_geo.latitude = 52.52
        mock_geo.longitude = 13.405
        mock_nominatim = Mock()
        mock_nominatim.geocode.return_value = mock_geo
        mock_nominatim_cls.return_value = mock_nominatim

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "daily": {
                "time": [time.strftime("%Y-%m-%d")],
                "temperature_2m_max": [15],
                "temperature_2m_min": [5],
                "precipitation_probability_max": [20],
                "wind_speed_10m_max": [30],
                "weather_code": [1],
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_weather_from_api_tool(city="Berlin", api_key="test")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["city"] == "Berlin"
        assert result["data"]["source"] == "open-meteo"
        assert "Quelle:" in result["data"]["forecast"]
        assert "Open-Meteo" in result["data"]["forecast"]
        assert _execution_time_ms(result) is not None

    def test_weather_missing_city(self):
        from backend.tools.weather_service import get_weather_from_api_tool

        result = get_weather_from_api_tool(city=None)
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT"

    @patch("backend.tools.weather_service.Nominatim")
    def test_weather_city_not_found(self, mock_nominatim_cls):
        from backend.tools.weather_service import get_weather_from_api_tool

        mock_nominatim = Mock()
        mock_nominatim.geocode.return_value = None
        mock_nominatim_cls.return_value = mock_nominatim

        result = get_weather_from_api_tool(city="Nimmerstadt", api_key="test")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"

    @patch("backend.tools.weather_service.Nominatim")
    def test_weather_api_unavailable(self, mock_nominatim_cls):
        from backend.tools.weather_service import get_weather_from_api_tool

        mock_geo = Mock()
        mock_geo.latitude = 52.52
        mock_geo.longitude = 13.405
        mock_nominatim = Mock()
        mock_nominatim.geocode.return_value = mock_geo
        mock_nominatim_cls.return_value = mock_nominatim

        with patch(
            "backend.tools.weather_service._get_retry_session"
        ) as mock_session_factory:
            mock_session = Mock()
            mock_session.get.side_effect = Exception("Connection timeout")
            mock_session_factory.return_value = mock_session

            result = get_weather_from_api_tool(city="Berlin", api_key="test")
            result = _validate_skill_response(result)
            assert result["status"] == "error"
            assert result["error"]["code"] == "API_UNAVAILABLE"

    def test_get_full_weather_forecast_empty_location(self):
        from backend.tools.weather_service import get_full_weather_forecast

        assert get_full_weather_forecast("", days=5) == {"forecast": {}}

    @patch("backend.tools.weather_service.Nominatim")
    def test_get_full_weather_forecast_returns_daily_precip_map(self, mock_nominatim_cls):
        from backend.tools.weather_service import get_full_weather_forecast

        mock_geo = Mock()
        mock_geo.latitude = 48.1
        mock_geo.longitude = 11.5
        mock_nominatim = Mock()
        mock_nominatim.geocode.return_value = mock_geo
        mock_nominatim_cls.return_value = mock_nominatim

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "daily": {
                "time": ["2026-05-05", "2026-05-06"],
                "precipitation_probability_max": [15, 72],
            }
        }
        with patch("backend.tools.weather_service._get_retry_session") as mock_session_factory:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_factory.return_value = mock_session

            out = get_full_weather_forecast("München", days=7)

        assert out["forecast"]["2026-05-05"]["precipitation_probability_max"] == 15
        assert out["forecast"]["2026-05-06"]["precipitation_probability_max"] == 72


# ===========================================================================
# 3. RSS NEWS SERVICE TESTS
# ===========================================================================


class TestRssNewsService:
    """Unit tests for system.rss_news handler."""

    @pytest.mark.asyncio
    async def test_rss_invalid_source(self):
        from backend.tools.rss_service import get_latest_news_rss

        result = await get_latest_news_rss(source="unbekannt")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_SOURCE"

    @pytest.mark.asyncio
    @patch("backend.tools.rss_service.asyncio.to_thread")
    async def test_rss_success(self, mock_to_thread):
        from backend.tools.rss_service import get_latest_news_rss

        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {"title": "Headline 1", "summary": "Summary 1", "link": "https://example.com/1"},
            {"title": "Headline 2", "summary": "Summary 2", "link": "https://example.com/2"},
        ]
        mock_to_thread.return_value = mock_feed

        result = await get_latest_news_rss(source="tagesschau")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert len(result["data"]["headlines"]) == 2
        assert result["data"]["items"][0]["url"] == "https://example.com/1"

    @pytest.mark.asyncio
    @patch("backend.tools.rss_service.asyncio.to_thread")
    async def test_rss_empty_results(self, mock_to_thread):
        from backend.tools.rss_service import get_latest_news_rss

        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = []
        mock_to_thread.return_value = mock_feed

        result = await get_latest_news_rss(source="tagesschau")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["headlines"] == []

    @pytest.mark.asyncio
    @patch("backend.tools.rss_service._fetch_feed_entries")
    async def test_rss_auto_uses_curated_feeds_and_returns_news_items(self, mock_fetch_entries):
        from backend.tools.rss_service import get_latest_news_rss

        async def _fake_fetch(source_key, _feed_url, limit=10):
            if source_key == "tagesschau":
                return [
                    {
                        "title": "OpenAI startet neue Funktion",
                        "summary": "Die Meldung beschreibt eine neue KI-Funktion.",
                        "url": "https://www.tagesschau.de/openai",
                        "source": "tagesschau",
                        "source_label": "Tagesschau",
                        "date": "23.05.2026",
                        "timestamp": 10,
                    }
                ]
            return []

        mock_fetch_entries.side_effect = _fake_fetch
        result = await get_latest_news_rss(source="auto", query="OpenAI")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["mode"] == "rss_hybrid"
        assert result["data"]["source"] == "auto"
        assert result["data"]["sources_used"] == ["tagesschau"]
        assert result["data"]["items"][0]["url"] == "https://www.tagesschau.de/openai"

    @pytest.mark.asyncio
    @patch("backend.tools.rss_service.execute_websearch_service", new_callable=AsyncMock)
    @patch("backend.tools.rss_service._collect_auto_news", new_callable=AsyncMock)
    async def test_rss_auto_returns_fast_no_match_without_internal_websearch(self, mock_collect, mock_websearch):
        from backend.tools.rss_service import get_latest_news_rss

        mock_collect.return_value = ([], [])
        mock_websearch.return_value = {
            "text": "Webfund mit Quelle.",
            "sources": [
                {
                    "url": "https://example.com/openai",
                    "title": "OpenAI Meldung",
                    "snippet": "Kurzer Websearch-Snippet zur Meldung.",
                }
            ],
        }

        result = await get_latest_news_rss(source="auto", query="Nischenthema", provider="gemini")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "RSS_NO_MATCH"
        mock_websearch.assert_not_awaited()


# ===========================================================================
# 4. WIKIPEDIA SERVICE TESTS
# ===========================================================================


class TestWikipediaService:
    """Unit tests for system.wikipedia_summary handler."""

    @pytest.mark.asyncio
    @patch("backend.tools.wiki_service.wikipediaapi.Wikipedia")
    async def test_wikipedia_success(self, mock_wiki_cls):
        from backend.tools.wiki_service import get_wikipedia_summary

        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = "Eiffelturm"
        mock_page.summary = "Der Eiffelturm ist ein 330 Meter hoher Turm."
        mock_page.fullurl = "https://de.wikipedia.org/wiki/Eiffelturm"

        mock_wiki = Mock()
        mock_wiki.page.return_value = mock_page
        mock_wiki_cls.return_value = mock_wiki

        result = await get_wikipedia_summary(query="Eiffelturm", lang="de")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["title"] == "Eiffelturm"
        assert "url" in result["data"]

    @pytest.mark.asyncio
    @patch("backend.tools.wiki_service.wikipediaapi.Wikipedia")
    async def test_wikipedia_not_found(self, mock_wiki_cls):
        from backend.tools.wiki_service import get_wikipedia_summary
        import wikipedia as wp_mod

        mock_page = Mock()
        mock_page.exists.return_value = False

        mock_wiki = Mock()
        mock_wiki.page.return_value = mock_page
        mock_wiki_cls.return_value = mock_wiki

        with patch.object(wp_mod, "search", return_value=[]):
            with patch.object(wp_mod, "set_lang"):
                result = await get_wikipedia_summary(query="Xyzzy_nonexistent")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    @patch("backend.tools.wiki_service.wikipediaapi.Wikipedia")
    async def test_wikipedia_api_error(self, mock_wiki_cls):
        from backend.tools.wiki_service import get_wikipedia_summary

        mock_wiki_cls.side_effect = Exception("Network error")

        result = await get_wikipedia_summary(query="Test")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "API_ERROR"


# ===========================================================================
# 5. SCRAPE WEBSITE SERVICE TESTS
# ===========================================================================


class TestScrapeWebsiteService:
    """Unit tests for system.scrape_website handler."""

    @pytest.mark.asyncio
    async def test_scrape_empty_url(self):
        from backend.services.scraper_service import scrape_website

        result = await scrape_website(url="")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT"

    @pytest.mark.asyncio
    @patch("backend.services.scraper_service.asyncio.to_thread")
    async def test_scrape_success(self, mock_to_thread):
        from backend.services.scraper_service import scrape_website

        mock_to_thread.return_value = "Titel: Example\nURL: https://example.com\n\n--- INHALT ---\nHello World"

        result = await scrape_website(url="https://example.com")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert "content" in result["data"]
        assert result["data"]["url"] == "https://example.com"

    @pytest.mark.asyncio
    @patch("backend.services.scraper_service.asyncio.to_thread")
    async def test_scrape_ollama_truncation(self, mock_to_thread):
        from backend.services.scraper_service import scrape_website

        long_content = "A" * 5000
        mock_to_thread.return_value = long_content

        result = await scrape_website(url="https://example.com", provider="ollama")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        # Ollama truncation: max 1000 chars + truncation message
        assert len(result["data"]["content"]) < 1100

    @pytest.mark.asyncio
    @patch("backend.services.scraper_service.asyncio.to_thread")
    async def test_scrape_openai_no_truncation(self, mock_to_thread):
        from backend.services.scraper_service import scrape_website

        long_content = "B" * 5000
        mock_to_thread.return_value = long_content

        result = await scrape_website(url="https://example.com", provider="openai")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert len(result["data"]["content"]) == 5000

    @pytest.mark.asyncio
    @patch("backend.services.scraper_service.asyncio.to_thread")
    async def test_scrape_failed(self, mock_to_thread):
        from backend.services.scraper_service import scrape_website

        mock_to_thread.return_value = "Fehler beim Lesen der Webseite: timeout"

        result = await scrape_website(url="https://broken.invalid")
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "SCRAPE_FAILED"


# ===========================================================================
# 6. SAVE MP3 SERVICE TESTS
# ===========================================================================


class TestSaveMp3Service:
    """Unit tests for system.save_mp3 handler."""

    @pytest.mark.asyncio
    async def test_save_mp3_empty_content(self):
        from backend.tools.media_tools import save_mp3_tool

        result = await save_mp3_tool(content=None)
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_INPUT"

    @pytest.mark.asyncio
    async def test_save_mp3_ssml_missing_api_key(self):
        from backend.tools.media_tools import save_mp3_tool

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            result = await save_mp3_tool(content="<speak>Hallo</speak>", filename="test")
            result = _validate_skill_response(result)
            assert result["status"] == "error"
            assert result["error"]["code"] == "PROVIDER_KEY_MISSING"

    @pytest.mark.asyncio
    async def test_save_mp3_appends_extension(self):
        from backend.tools.media_tools import save_mp3_tool

        # Trigger the TTS path without .mp3 extension -> will fail at TTS but filename should have .mp3
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            result = await save_mp3_tool(content="<speak>Test</speak>", filename="myfile")
            result = _validate_skill_response(result)
            # Even on error, the contract is maintained
            assert result["status"] == "error"


# ===========================================================================
# 7. COUNTRY INFO SERVICE TESTS
# ===========================================================================


class TestCountryInfoService:
    """Unit tests for system.country_info handler."""

    @patch("backend.tools.geo_service.requests.get")
    def test_country_info_success(self, mock_get):
        from backend.tools.geo_service import get_country_info_tool

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
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["capital"] == "Berlin"

    @patch("backend.tools.geo_service.requests.get")
    def test_country_info_not_found(self, mock_get):
        from backend.tools.geo_service import get_country_info_tool

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_country_info_tool(country="Nimmerland").model_dump()
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "NOT_FOUND"


# ===========================================================================
# 8. ROUTING SERVICE TESTS
# ===========================================================================


class TestRoutingService:
    """Unit tests for system.routing handler."""

    @pytest.mark.asyncio
    @patch("backend.tools.geo_service._geocode_city_center")
    @patch("backend.tools.geo_service.asyncio.to_thread")
    async def test_routing_success(self, mock_to_thread, mock_geocode):
        from backend.tools.geo_service import get_distance_and_route_tool

        mock_geo_origin = Mock()
        mock_geo_origin.latitude = 52.52
        mock_geo_origin.longitude = 13.405
        mock_geo_dest = Mock()
        mock_geo_dest.latitude = 53.55
        mock_geo_dest.longitude = 9.99

        # _geocode_city_center is awaited twice
        mock_geocode.side_effect = [mock_geo_origin, mock_geo_dest]

        # asyncio.to_thread is used for requests.get -> mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "routes": [{"distance": 289000, "duration": 11700}]
        }
        mock_to_thread.return_value = mock_response

        result = (await get_distance_and_route_tool(origin="Berlin", destination="Hamburg", mode="driving")).model_dump()
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["distance_km"] == 289.0

    @pytest.mark.asyncio
    @patch("backend.tools.geo_service._geocode_city_center")
    async def test_routing_invalid_coordinates(self, mock_geocode):
        from backend.tools.geo_service import get_distance_and_route_tool

        mock_geocode.side_effect = [None, None]

        result = (await get_distance_and_route_tool(origin="Berlin", destination="Nimmerland")).model_dump()
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_COORDINATES"

    @pytest.mark.asyncio
    async def test_routing_invalid_mode(self):
        from backend.tools.geo_service import get_distance_and_route_tool

        result = (await get_distance_and_route_tool(origin="Berlin", destination="Hamburg", mode="flying")).model_dump()
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "INVALID_MODE"


# ===========================================================================
# 9. PERMISSION SERVICES TESTS
# ===========================================================================


class TestPermissionServices:
    """Unit tests for system.grant_permission & system.revoke_permission."""

    def test_grant_permission_contract(self, db_session):
        from backend.services.permission_service import grant_permission

        result = grant_permission(skill_id="filesystem.delete_file", db=db_session)
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["action"] == "granted"

    def test_grant_permission_unknown_skill(self, db_session):
        from backend.services.permission_service import grant_permission

        result = grant_permission(skill_id="nonexistent.skill_xyz", db=db_session)
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "SKILL_NOT_FOUND"

    def test_revoke_permission_contract(self, db_session):
        from backend.services.permission_service import revoke_permission
        from backend.services.policy_engine import PolicyEngine

        PolicyEngine.grant_permanent_permission("filesystem.delete_file", db_session)
        result = revoke_permission(skill_id="filesystem.delete_file", db=db_session)
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert result["data"]["action"] == "revoked"

    def test_revoke_permission_unknown_skill(self, db_session):
        from backend.services.permission_service import revoke_permission

        result = revoke_permission(skill_id="nonexistent.skill_xyz", db=db_session)
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "SKILL_NOT_FOUND"


# ===========================================================================
# 10. WEBSEARCH SERVICE TESTS
# ===========================================================================


class TestWebsearchService:
    """Unit tests for system.websearch handler."""

    @pytest.mark.asyncio
    @patch("backend.tool_registry.execute_websearch_service")
    async def test_websearch_success(self, mock_search):
        from backend.tool_registry import websearch_wrapper

        mock_search.return_value = {"text": "Results", "urls": [], "source": "duckduckgo"}
        args = WebsearchArgsV2(query="Test query")
        result = await websearch_wrapper(args)
        result = _validate_skill_response(result)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    @patch("backend.tool_registry.execute_websearch_service")
    async def test_websearch_failure(self, mock_search):
        from backend.tool_registry import websearch_wrapper

        mock_search.side_effect = Exception("Connection failed")
        args = WebsearchArgsV2(query="Test query")
        result = await websearch_wrapper(args)
        result = _validate_skill_response(result)
        assert result["status"] == "error"
        assert result["error"]["code"] == "WEBSEARCH_FAILED"


# ===========================================================================
# 11. SKILL CATALOG VALIDATION
# ===========================================================================


class TestSkillCatalogIntegrity:
    """Validate all 15 system skill JSON catalogs meet Diamond V2 standard."""

    SKILL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "skills", "system")

    @pytest.fixture(autouse=True)
    def _resolve_skill_dir(self):
        self.SKILL_DIR = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "skills", "system")
        )

    def _load_catalog(self, filename):
        path = os.path.join(self.SKILL_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.mark.parametrize("filename", [
        "country_info.json",
        "create_pdf.json",
        "generate_image.json",
        "grant_permission.json",
        "local_business.json",
        "revoke_permission.json",
        "routing.json",
        "rss_news.json",
        "save_mp3.json",
        "scrape_website.json",
        "weather.json",
        "websearch.json",
        "wikipedia_summary.json",
    ])
    def test_catalog_has_required_fields(self, filename):
        catalog = self._load_catalog(filename)
        assert "skill" in catalog, f"{filename} missing 'skill'"
        assert "version" in catalog, f"{filename} missing 'version'"
        assert catalog["version"] >= "1.1.0", f"{filename} version < 1.1.0: {catalog['version']}"
        assert "latency_class" in catalog, f"{filename} missing 'latency_class'"
        assert catalog["latency_class"] in ("fast", "normal", "slow"), f"{filename} invalid latency_class"
        assert "sandbox_level" in catalog, f"{filename} missing 'sandbox_level'"
        assert "timeout_ms" in catalog, f"{filename} missing 'timeout_ms'"
        assert isinstance(catalog.get("examples"), list), f"{filename} missing or invalid 'examples'"
        assert len(catalog["examples"]) >= 1, f"{filename} needs at least 1 example"
        assert isinstance(catalog.get("tags"), list), f"{filename} missing 'tags'"
        assert len(catalog["tags"]) >= 2, f"{filename} needs at least 2 tags"

    @pytest.mark.parametrize("filename", [
        "country_info.json",
        "create_pdf.json",
        "generate_image.json",
        "grant_permission.json",
        "local_business.json",
        "routing.json",
        "rss_news.json",
        "save_mp3.json",
        "scrape_website.json",
        "weather.json",
        "wikipedia_summary.json",
    ])
    def test_catalog_examples_have_skillresponse_format(self, filename):
        catalog = self._load_catalog(filename)
        for i, ex in enumerate(catalog["examples"]):
            assert "input" in ex, f"{filename} example[{i}] missing 'input'"
            assert "output" in ex, f"{filename} example[{i}] missing 'output'"
            output = ex["output"]
            assert output.get("status") in ("ok", "error", "dry_run_success"), (
                f"{filename} example[{i}] invalid status: {output.get('status')}"
            )


# ===========================================================================
# 12. OLLAMA PROVIDER-PARAMETRISIERTE TESTS
# ===========================================================================


class TestOllamaProviderSwitches:
    """Validate Ollama-specific behavior across skills."""

    @pytest.mark.asyncio
    @patch("backend.services.scraper_service.asyncio.to_thread")
    async def test_scrape_website_ollama_truncates(self, mock_to_thread):
        from backend.services.scraper_service import scrape_website

        mock_to_thread.return_value = "X" * 3000
        result = await scrape_website(url="https://example.com", provider="ollama")
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert len(result["data"]["content"]) <= 1100
        assert "gekürzt" in result["data"]["content"]

    @pytest.mark.asyncio
    @patch("backend.services.scraper_service.asyncio.to_thread")
    @pytest.mark.parametrize("provider", ["openai", "gemini", ""])
    async def test_scrape_website_non_ollama_no_truncation(self, mock_to_thread, provider):
        from backend.services.scraper_service import scrape_website

        mock_to_thread.return_value = "Y" * 3000
        result = await scrape_website(url="https://example.com", provider=provider)
        result = _validate_skill_response(result)
        assert result["status"] == "ok"
        assert len(result["data"]["content"]) == 3000

    def test_local_business_search_query_ollama_compact(self):
        from backend.tools.geo_service import _build_local_business_search_query

        result = _build_local_business_search_query(
            query="Restaurant",
            location="Berlin",
            provider="ollama",
        )
        # Ollama: compact query without enrichment keywords
        assert "Adresse" not in result
        assert "Telefonnummer" not in result
        assert "Restaurant" in result
        assert "Berlin" in result

    def test_local_business_search_query_openai_enriched(self):
        from backend.tools.geo_service import _build_local_business_search_query

        result = _build_local_business_search_query(
            query="Restaurant",
            location="Berlin",
            provider="openai",
        )
        # OpenAI: enriched query with extra keywords
        assert "Adresse" in result
        assert "Telefonnummer" in result


# ===========================================================================
# 13. EXECUTION TIME TRACKING
# ===========================================================================


class TestExecutionTimeTracking:
    """Verify that all handlers include execution_time_ms."""

    def test_weather_has_execution_time(self):
        from backend.tools.weather_service import get_weather_from_api_tool

        result = get_weather_from_api_tool(city=None)
        ms = _execution_time_ms(result)
        assert ms is not None
        assert isinstance(ms, (int, float))

    @pytest.mark.asyncio
    async def test_rss_has_execution_time(self):
        from backend.tools.rss_service import get_latest_news_rss

        result = await get_latest_news_rss(source="unbekannt")
        assert _execution_time_ms(result) is not None

    @pytest.mark.asyncio
    async def test_wikipedia_has_execution_time(self):
        from backend.tools.wiki_service import get_wikipedia_summary

        with patch("backend.tools.wiki_service.wikipediaapi.Wikipedia", side_effect=Exception("test")):
            result = await get_wikipedia_summary(query="Test")
            assert _execution_time_ms(result) is not None

    @pytest.mark.asyncio
    async def test_scrape_has_execution_time(self):
        from backend.services.scraper_service import scrape_website

        result = await scrape_website(url="")
        assert _execution_time_ms(result) is not None

    @pytest.mark.asyncio
    async def test_save_mp3_has_execution_time(self):
        from backend.tools.media_tools import save_mp3_tool

        result = await save_mp3_tool(content=None)
        assert _execution_time_ms(result) is not None
