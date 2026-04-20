"""Diamond-Standard Unit Tests for Deterministic Renderers.

Tests each renderer with:
- Complete / happy-path data
- Partial data (missing fields → graceful defaults)
- Minimal / empty data (edge case)

No LLM mocking needed – pure Python unit tests.
"""

import pytest

from backend.renderers.base import BaseRenderer
from backend.renderers.registry import get_renderer, get_all_renderer_skill_ids
from backend.renderers.implementations.routing_renderer import RoutingRenderer
from backend.renderers.implementations.weather_renderer import WeatherRenderer
from backend.renderers.implementations.country_info_renderer import CountryInfoRenderer
from backend.renderers.implementations.create_pdf_renderer import CreatePdfRenderer
from backend.renderers.implementations.generate_image_renderer import GenerateImageRenderer
from backend.renderers.implementations.grant_permission_renderer import GrantPermissionRenderer
from backend.renderers.implementations.local_business_renderer import LocalBusinessRenderer
from backend.renderers.implementations.revoke_permission_renderer import RevokePermissionRenderer
from backend.renderers.implementations.rss_news_renderer import RssNewsRenderer
from backend.renderers.implementations.save_mp3_renderer import SaveMp3Renderer
from backend.renderers.implementations.scrape_website_renderer import ScrapeWebsiteRenderer
from backend.renderers.implementations.websearch_renderer import WebsearchRenderer
from backend.renderers.implementations.wikipedia_summary_renderer import WikipediaSummaryRenderer


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestRegistry:
    """Verify the registry loads and returns renderers correctly."""

    def test_all_batch_one_renderers_registered(self):
        ids = get_all_renderer_skill_ids()
        assert "system.routing" in ids
        assert "system.weather" in ids
        assert "system.country_info" in ids
        assert "system.create_pdf" in ids
        assert "system.generate_image" in ids
        assert "system.grant_permission" in ids
        assert "system.local_business" in ids
        assert "system.revoke_permission" in ids
        assert "system.rss_news" in ids
        assert "system.save_mp3" in ids

    def test_get_renderer_returns_instance(self):
        r = get_renderer("system.routing")
        assert r is not None
        assert isinstance(r, BaseRenderer)

    def test_get_renderer_returns_none_for_unknown(self):
        assert get_renderer("system.nonexistent_skill") is None

    def test_get_renderer_returns_none_for_empty_string(self):
        assert get_renderer("") is None


# ---------------------------------------------------------------------------
# RoutingRenderer
# ---------------------------------------------------------------------------

_ROUTING_FULL = {
    "origin": "Berlin",
    "destination": "Hamburg",
    "distance_km": 289.0,
    "duration": "3 Std. 15 Min.",
    "maps_link": "https://www.google.com/maps/dir/?api=1&origin=Berlin&destination=Hamburg&travelmode=driving",
}

_ROUTING_PARTIAL = {
    "origin": "München",
    "destination": "Wien",
}

_ROUTING_EMPTY = {}


class TestRoutingRenderer:
    renderer = RoutingRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _ROUTING_FULL,
                ["Berlin → Hamburg", "289.0 km", "3 Std. 15 Min.", "google.com/maps"],
                id="full-data",
            ),
            pytest.param(
                _ROUTING_PARTIAL,
                ["München → Wien", "Distanz unbekannt", "Dauer unbekannt"],
                id="partial-data",
            ),
            pytest.param(
                _ROUTING_EMPTY,
                ["Unbekannt → Unbekannt", "Distanz unbekannt"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.routing"

    def test_no_maps_link_when_missing(self):
        result = self.renderer.render({"origin": "A", "destination": "B"})
        assert "google.com/maps" not in result.lower()
        assert "Route anzeigen" not in result


# ---------------------------------------------------------------------------
# WeatherRenderer
# ---------------------------------------------------------------------------

_WEATHER_FULL = {
    "forecast": "Wettervorhersage für Berlin am 18.03.2026 (morgen): Es wird leicht bewölkt erwartet. Höchsttemperatur: 12°C, Tiefsttemperatur: 4°C. Niederschlagswahrscheinlichkeit: 15%. Windböen bis zu 25 km/h.",
    "city": "Berlin",
    "date": "18.03.2026",
    "temp_max": 12,
    "temp_min": 4,
    "precipitation_probability": 15,
    "wind_speed_max": 25,
    "weather_description": "Leicht bewölkt",
    "source": "open-meteo",
}

_WEATHER_WTTR_FALLBACK = {
    "forecast": "Berlin: +8°C",
    "source": "wttr.in",
    "city": "Berlin",
}

_WEATHER_STRUCTURED_ONLY = {
    "city": "Hamburg",
    "date": "20.03.2026",
    "temp_max": 9,
    "temp_min": 3,
    "precipitation_probability": 60,
    "wind_speed_max": 40,
    "weather_description": "Regen",
    "source": "open-meteo",
}

_WEATHER_EMPTY = {}


class TestWeatherRenderer:
    renderer = WeatherRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _WEATHER_FULL,
                ["Berlin", "Wettervorhersage", "12°C", "open-meteo"],
                id="full-data",
            ),
            pytest.param(
                _WEATHER_WTTR_FALLBACK,
                ["Berlin", "wttr.in"],
                id="wttr-fallback",
            ),
            pytest.param(
                _WEATHER_STRUCTURED_ONLY,
                ["Hamburg", "Regen", "9°C", "3°C", "60%", "40 km/h"],
                id="structured-no-forecast",
            ),
            pytest.param(
                _WEATHER_EMPTY,
                ["Unbekannt"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.weather"

    def test_source_attribution_present(self):
        result = self.renderer.render(_WEATHER_FULL)
        assert "open-meteo" in result


# ---------------------------------------------------------------------------
# CountryInfoRenderer
# ---------------------------------------------------------------------------

_COUNTRY_FULL = {
    "name": "Japan",
    "capital": "Tokio",
    "population": 125100000,
    "region": "Asia",
    "currencies": ["Japanischer Yen (JPY)"],
    "languages": ["Japanisch"],
}

_COUNTRY_PARTIAL = {
    "name": "Atlantis",
    "capital": "Poseidonia",
}

_COUNTRY_EMPTY = {}


class TestCountryInfoRenderer:
    renderer = CountryInfoRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _COUNTRY_FULL,
                ["Japan", "Tokio", "125.1 Mio.", "Asia", "Japanischer Yen", "Japanisch"],
                id="full-data",
            ),
            pytest.param(
                _COUNTRY_PARTIAL,
                ["Atlantis", "Poseidonia", "Unbekannt"],
                id="partial-data",
            ),
            pytest.param(
                _COUNTRY_EMPTY,
                ["Unbekannt"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.country_info"

    def test_population_formatting_billions(self):
        result = self.renderer.render({"name": "World", "population": 8_000_000_000})
        assert "8.00 Mrd." in result

    def test_population_formatting_thousands(self):
        result = self.renderer.render({"name": "Liechtenstein", "population": 39000})
        assert "39.000" in result

    def test_multiple_currencies(self):
        data = {
            "name": "Schweiz",
            "capital": "Bern",
            "currencies": ["Schweizer Franken (CHF)", "Euro (EUR)"],
            "languages": ["Deutsch", "Französisch", "Italienisch", "Rätoromanisch"],
        }
        result = self.renderer.render(data)
        assert "Schweizer Franken" in result
        assert "Euro" in result
        assert "Deutsch" in result
        assert "Rätoromanisch" in result


_CREATE_PDF_FULL = {
    "file_path": "workspace/reports/projektbericht.pdf",
}

_CREATE_PDF_DRY_RUN = {
    "preview_url": "data:application/pdf;base64,JVBERi0x...",
}

_CREATE_PDF_EMPTY = {}


class TestCreatePdfRenderer:
    renderer = CreatePdfRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _CREATE_PDF_FULL,
                ["PDF erfolgreich erstellt", "workspace/reports/projektbericht.pdf"],
                id="full-data",
            ),
            pytest.param(
                _CREATE_PDF_DRY_RUN,
                ["PDF-Vorschau erzeugt", "Dry-Run-Modus", "data:application/pdf;base64"],
                id="dry-run",
            ),
            pytest.param(
                _CREATE_PDF_EMPTY,
                ["PDF-Daten konnten nicht aufbereitet werden."],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.create_pdf"


_GENERATE_IMAGE_FULL = {
    "message": "Bild erfolgreich generiert und im Image Studio gespeichert.",
    "local_image_path": "/user_images/red_cat.png",
    "image_url": "/user_images/red_cat.png",
    "prompt_used": "A cozy watercolor illustration of a red cat sleeping on a windowsill",
    "cost": 0.04,
}

_GENERATE_IMAGE_PARTIAL = {
    "image_url": "/user_images/lake_house.png",
    "prompt_used": "Draw a bright wooden house by a lake at sunrise",
}

_GENERATE_IMAGE_EMPTY = {}


class TestGenerateImageRenderer:
    renderer = GenerateImageRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _GENERATE_IMAGE_FULL,
                ["Bild erfolgreich generiert", "/user_images/red_cat.png", "watercolor", "0.04"],
                id="full-data",
            ),
            pytest.param(
                _GENERATE_IMAGE_PARTIAL,
                ["Bild erfolgreich generiert", "/user_images/lake_house.png", "wooden house"],
                id="partial-data",
            ),
            pytest.param(
                _GENERATE_IMAGE_EMPTY,
                ["Bild erfolgreich generiert"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.generate_image"


_GRANT_PERMISSION_FULL = {
    "skill_id": "communication.read_email",
    "action": "granted",
    "permission_state": "always_allow",
    "already_present": False,
}

_GRANT_PERMISSION_ALREADY_PRESENT = {
    "skill_id": "communication.read_email",
    "action": "granted",
    "permission_state": "always_allow",
    "already_present": True,
}

_GRANT_PERMISSION_EMPTY = {}


class TestGrantPermissionRenderer:
    renderer = GrantPermissionRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _GRANT_PERMISSION_FULL,
                ["Freigabe aktualisiert", "communication.read_email", "granted", "always_allow"],
                id="full-data",
            ),
            pytest.param(
                _GRANT_PERMISSION_ALREADY_PRESENT,
                ["war bereits freigegeben", "communication.read_email"],
                id="already-present",
            ),
            pytest.param(
                _GRANT_PERMISSION_EMPTY,
                ["Freigabe aktualisiert", "Unbekannter Skill", "always_allow"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.grant_permission"


_LOCAL_BUSINESS_FULL = [
    {
        "name": "Trattoria da Luigi",
        "address": "Ottenser Hauptstr. 12, 22765 Hamburg",
        "phone": "+49 40 123456",
        "website": "https://trattoria-luigi.de",
    }
]

_LOCAL_BUSINESS_EMPTY = []


class TestLocalBusinessRenderer:
    renderer = LocalBusinessRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _LOCAL_BUSINESS_FULL,
                ["Gefundene lokale Ergebnisse", "Trattoria da Luigi", "Ottenser Hauptstr.", "trattoria-luigi.de"],
                id="full-data",
            ),
            pytest.param(
                _LOCAL_BUSINESS_EMPTY,
                ["keine passenden Ergebnisse"],
                id="empty-list",
            ),
            pytest.param(
                {},
                ["keine passenden Ergebnisse"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        lowered = result.lower()
        for fragment in expected_fragments:
            if fragment == "keine passenden Ergebnisse":
                assert "keine passenden ergebnisse" in lowered or "keine passenden" in lowered
            else:
                assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.local_business"


_REVOKE_PERMISSION_FULL = {
    "skill_id": "filesystem.delete_file",
    "action": "revoked",
    "permission_state": "requires_consent",
    "removed": True,
}

_REVOKE_PERMISSION_NOT_PRESENT = {
    "skill_id": "filesystem.delete_file",
    "action": "revoked",
    "permission_state": "requires_consent",
    "removed": False,
}


class TestRevokePermissionRenderer:
    renderer = RevokePermissionRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _REVOKE_PERMISSION_FULL,
                ["Freigabe widerrufen", "filesystem.delete_file", "revoked", "requires_consent"],
                id="full-data",
            ),
            pytest.param(
                _REVOKE_PERMISSION_NOT_PRESENT,
                ["war nicht dauerhaft gesetzt", "filesystem.delete_file"],
                id="not-present",
            ),
            pytest.param(
                {},
                ["Freigabe widerrufen", "Unbekannter Skill", "requires_consent"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.revoke_permission"


_RSS_NEWS_FULL = {
    "headlines": ["Bundestag beschließt neues Klimagesetz", "DAX erreicht Rekordhoch"],
    "source": "tagesschau",
    "count": 2,
}

_RSS_NEWS_EMPTY = {
    "headlines": [],
    "source": "tagesschau",
}


class TestRssNewsRenderer:
    renderer = RssNewsRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _RSS_NEWS_FULL,
                ["Aktuelle Schlagzeilen von tagesschau", "1. Bundestag", "2. DAX", "Anzahl"],
                id="full-data",
            ),
            pytest.param(
                _RSS_NEWS_EMPTY,
                ["keine Schlagzeilen"],
                id="empty-headlines",
            ),
            pytest.param(
                {},
                ["keine Schlagzeilen"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        lowered = result.lower()
        for fragment in expected_fragments:
            if fragment == "keine Schlagzeilen":
                assert "keine schlagzeilen" in lowered
            else:
                assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.rss_news"


_SAVE_MP3_FULL = {
    "file_path": "C:/Users/User/Desktop/test_audio.mp3",
    "filename": "test_audio.mp3",
}

_SAVE_MP3_PARTIAL = {
    "filename": "leer.mp3",
}


class TestSaveMp3Renderer:
    renderer = SaveMp3Renderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _SAVE_MP3_FULL,
                ["MP3 erfolgreich gespeichert", "test_audio.mp3", "C:/Users/User/Desktop/test_audio.mp3"],
                id="full-data",
            ),
            pytest.param(
                _SAVE_MP3_PARTIAL,
                ["MP3 erfolgreich gespeichert", "leer.mp3"],
                id="partial-data",
            ),
            pytest.param(
                {},
                ["MP3 erfolgreich gespeichert", "audio.mp3"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.save_mp3"


_SCRAPE_WEBSITE_FULL = {
    "content": "Titel: Example Domain\nURL: https://example.com\n\n--- INHALT ---\nThis domain is for use in illustrative examples.",
    "url": "https://example.com",
    "char_count": 95,
}

_SCRAPE_WEBSITE_PARTIAL = {
    "url": "https://example.com/docs",
}

class TestScrapeWebsiteRenderer:
    renderer = ScrapeWebsiteRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _SCRAPE_WEBSITE_FULL,
                ["Executive Summary: Website-Inhalt bereit", "https://example.com", "Example Domain", "95 Zeichen"],
                id="full-data",
            ),
            pytest.param(
                _SCRAPE_WEBSITE_PARTIAL,
                ["Executive Summary: Website-Inhalt bereit", "https://example.com/docs", "Unbekannter Titel", "0 Zeichen"],
                id="partial-data",
            ),
            pytest.param(
                {},
                ["Executive Summary: Website-Inhalt bereit", "Unbekannte URL", "Unbekannter Titel"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.scrape_website"


_WEBSEARCH_FULL = {
    "text": "Suchergebnisse mit mehreren Quellen und kurzen Snippets.",
    "urls": ["https://example.com", "https://example.org"],
    "source": "duckduckgo",
}

_WEBSEARCH_PARTIAL = {
    "urls": ["https://example.net"],
}

class TestWebsearchRenderer:
    renderer = WebsearchRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _WEBSEARCH_FULL,
                ["Executive Summary: Websuche bereit", "duckduckgo", "2", "https://example.com"],
                id="full-data",
            ),
            pytest.param(
                _WEBSEARCH_PARTIAL,
                ["Executive Summary: Websuche bereit", "unbekannt", "1", "https://example.net"],
                id="partial-data",
            ),
            pytest.param(
                {},
                ["Executive Summary: Websuche bereit", "unbekannt", "0"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.websearch"


_WIKIPEDIA_SUMMARY_FULL = {
    "title": "Eiffelturm",
    "summary": "Der Eiffelturm ist ein 330 Meter hoher Eisenfachwerkturm in Paris.",
    "url": "https://de.wikipedia.org/wiki/Eiffelturm",
}

_WIKIPEDIA_SUMMARY_PARTIAL = {
    "title": "Artikel ohne URL",
}

class TestWikipediaSummaryRenderer:
    renderer = WikipediaSummaryRenderer()

    @pytest.mark.parametrize(
        "data, expected_fragments",
        [
            pytest.param(
                _WIKIPEDIA_SUMMARY_FULL,
                ["Executive Summary: Wikipedia-Daten bereit", "Eiffelturm", "https://de.wikipedia.org/wiki/Eiffelturm"],
                id="full-data",
            ),
            pytest.param(
                _WIKIPEDIA_SUMMARY_PARTIAL,
                ["Executive Summary: Wikipedia-Daten bereit", "Artikel ohne URL", "0 Zeichen"],
                id="partial-data",
            ),
            pytest.param(
                {},
                ["Executive Summary: Wikipedia-Daten bereit", "Unbekannter Artikel", "0 Zeichen"],
                id="empty-data",
            ),
        ],
    )
    def test_render(self, data, expected_fragments):
        result = self.renderer.render(data)
        assert isinstance(result, str)
        assert len(result) > 0
        for fragment in expected_fragments:
            assert fragment in result, f"Expected '{fragment}' in:\n{result}"

    def test_skill_id(self):
        assert self.renderer.skill_id == "system.wikipedia_summary"


# ---------------------------------------------------------------------------
# Contract: All renderers must be subclass of BaseRenderer
# ---------------------------------------------------------------------------

class TestBaseRendererContract:
    """Ensure all registered renderers comply with the ABC contract."""

    def test_all_renderers_are_base_renderer_subclass(self):
        for skill_id in get_all_renderer_skill_ids():
            renderer = get_renderer(skill_id)
            assert isinstance(renderer, BaseRenderer), (
                f"Renderer for '{skill_id}' is not a BaseRenderer subclass"
            )

    def test_all_renderers_have_skill_id(self):
        for skill_id in get_all_renderer_skill_ids():
            renderer = get_renderer(skill_id)
            assert renderer.skill_id, f"Renderer {type(renderer).__name__} has no skill_id"

    def test_render_always_returns_string(self):
        for skill_id in get_all_renderer_skill_ids():
            renderer = get_renderer(skill_id)
            result = renderer.render({})
            assert isinstance(result, str), (
                f"Renderer for '{skill_id}' returned {type(result)} instead of str"
            )
