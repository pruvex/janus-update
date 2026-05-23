"""Diamond-Standard Unit Tests for Deterministic Renderers.

Tests each renderer with:
- Complete / happy-path data
- Partial data (missing fields → graceful defaults)
- Minimal / empty data (edge case)

No LLM mocking needed – pure Python unit tests.
"""

import json

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
from backend.services.websearch.link_quality import (
    LinkIntent,
    is_low_value_source,
    score_source_for_intent,
    select_best_source_for_item,
)


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
                [
                    "Berlin → Hamburg",
                    "289.0 km",
                    "3 Std. 15 Min.",
                    "google.com/maps",
                    "Quelle:",
                    "OSRM",
                    "Nominatim",
                ],
                id="full-data",
            ),
            pytest.param(
                _ROUTING_PARTIAL,
                [
                    "München → Wien",
                    "Distanz unbekannt",
                    "Dauer unbekannt",
                    "Quelle:",
                    "OSRM",
                ],
                id="partial-data",
            ),
            pytest.param(
                _ROUTING_EMPTY,
                ["Unbekannt → Unbekannt", "Distanz unbekannt", "Quelle:", "OSRM"],
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
                [
                    "Berlin",
                    "Wettervorhersage",
                    "12°C",
                    "Quelle:",
                    "Open-Meteo",
                    "Nominatim",
                ],
                id="full-data",
            ),
            pytest.param(
                _WEATHER_WTTR_FALLBACK,
                ["Berlin", "Quelle:", "wttr.in"],
                id="wttr-fallback",
            ),
            pytest.param(
                _WEATHER_STRUCTURED_ONLY,
                [
                    "Hamburg",
                    "Regen",
                    "9°C",
                    "3°C",
                    "60%",
                    "40 km/h",
                    "Quelle:",
                    "Open-Meteo",
                ],
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
        assert "Quelle:" in result
        assert "Open-Meteo" in result


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
                [
                    "Japan",
                    "Tokio",
                    "125.1 Mio.",
                    "Asia",
                    "Japanischer Yen",
                    "Japanisch",
                    "Quelle:",
                    "REST Countries API",
                ],
                id="full-data",
            ),
            pytest.param(
                _COUNTRY_PARTIAL,
                [
                    "Atlantis",
                    "Poseidonia",
                    "Unbekannt",
                    "Quelle:",
                    "REST Countries API",
                ],
                id="partial-data",
            ),
            pytest.param(
                _COUNTRY_EMPTY,
                ["Unbekannt", "Quelle:", "REST Countries API"],
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

_RSS_NEWS_ITEMS = {
    "mode": "rss_hybrid",
    "source": "auto",
    "query": "OpenAI",
    "items": [
        {
            "title": "OpenAI startet neue Funktion",
            "summary": "Die Meldung beschreibt eine neue KI-Funktion und ordnet die wichtigsten Auswirkungen kurz ein.",
            "url": "https://www.tagesschau.de/openai",
            "source": "tagesschau",
            "source_label": "Tagesschau",
            "date": "23.05.2026",
        }
    ],
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
                _RSS_NEWS_ITEMS,
                [
                    "Kurzlage: Zu OpenAI",
                    "1. OpenAI startet neue Funktion (23.05.2026)",
                    "Quelle: Tagesschau. [Link](https://www.tagesschau.de/openai)",
                    "Einordnung:",
                ],
                id="rss-hybrid-items",
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

    def test_response_finalizer_renders_rss_news_tool_result(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "get_latest_news_rss",
                    "_skill_id": "system.rss_news",
                    "content": json.dumps({"data": _RSS_NEWS_ITEMS}),
                }
            ]
        )

        assert "Kurzlage: Zu OpenAI" in result
        assert "Quelle: Tagesschau. [Link](https://www.tagesschau.de/openai)" in result

    def test_response_finalizer_prefers_rss_news_over_parallel_websearch(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "text": "1. Freie Websearch-Synthese ohne Template",
                                "sources": [{"url": "https://example.com", "title": "Example"}],
                            }
                        }
                    ),
                },
                {
                    "role": "tool",
                    "name": "system.rss_news",
                    "_skill_id": "system.rss_news",
                    "content": json.dumps({"data": _RSS_NEWS_ITEMS}),
                },
            ]
        )

        assert "Kurzlage: Zu OpenAI" in result
        assert "Freie Websearch-Synthese" not in result

    def test_response_finalizer_renders_news_websearch_as_news_template(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. GPT-5.5 Instant: Das Modell wurde veroeffentlicht und ist neuer Standard. "
                                    "Quelle: OpenAI.\n"
                                    "2. Sora-Einstellung: Die Webanwendung wurde eingestellt. Quelle: OpenAI."
                                ),
                                "sources": [
                                    {
                                        "url": "https://openai.com/news/example",
                                        "title": "openai.com",
                                        "snippet": "GPT-5.5 Instant Quelle: OpenAI",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "Kurzlage: Zu OpenAI liegen aktuell belegte Meldungen vor." in result
        assert "1. GPT-5.5 Instant" in result
        assert "Quelle: OpenAI. [Link](https://openai.com/news/example)" in result

    def test_response_finalizer_prefers_numbered_news_text_over_single_source_item(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "items": [
                                    {
                                        "title": "openai.com",
                                        "description": "2. Nur ein strukturierter Snippet.",
                                        "source_url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example",
                                    }
                                ],
                                "text": (
                                    "1. OpenAI fuehrt im Mai 2026 die souveraene Cloud-Loesung OpenAI for Germany ein (Quelle: TechRepublic).\n"
                                    "2. Das Unternehmen betreibt in Muenchen sein erstes deutsches Buero (Quelle: OpenAI).\n"
                                    "3. In einer strategischen Allianz mit der Deutschen Telekom entwickelt OpenAI neue KI-Produkte fuer Europa (Quelle: Computerwoche).\n"
                                    "\n[Global Research]\n"
                                    "1. Dieser globale Zusatz soll nicht die Primaerliste verdoppeln (Quelle: OpenAI)."
                                ),
                                "sources": [
                                    {
                                        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/example",
                                        "title": "openai.com",
                                        "snippet": "Das Unternehmen betreibt in Muenchen sein erstes deutsches Buero (Quelle: OpenAI).",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "OpenAI fuehrt im Mai 2026 die souveraene Cloud-Loesung OpenAI for Germany ein" not in result
        assert "1. Das Unternehmen betreibt in Muenchen sein erstes deutsches Buero" in result
        assert "In einer strategischen Allianz mit der Deutschen Telekom entwickelt OpenAI" not in result
        assert "openai.com\n2. Nur ein strukturierter Snippet" not in result
        assert "globaler Zusatz" not in result

    def test_response_finalizer_uses_resolved_news_detail_link_for_item(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Sora-App: Die eigenstaendige Anwendung wurde eingestellt und in ChatGPT integriert. "
                                    "Quelle: OpenAI."
                                ),
                                "sources": [
                                    {
                                        "url": "https://reddit.com/r/example",
                                        "title": "reddit.com",
                                        "snippet": "Sora-App OpenAI Diskussion",
                                    },
                                    {
                                        "url": "https://openai.com/de-DE/news/sora-in-chatgpt",
                                        "title": "OpenAI Sora in ChatGPT",
                                        "snippet": "Sora-App wurde in ChatGPT integriert.",
                                        "news_target_index": "1",
                                        "news_target_title": "Sora-App",
                                        "news_target_label": "OpenAI",
                                    },
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "Quelle: OpenAI. [Link](https://openai.com/de-DE/news/sora-in-chatgpt)" in result
        assert "reddit.com/r/example" not in result

    def test_response_finalizer_rejects_generic_news_landing_page_link(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. GPT-5.5: Das Modell wurde als neues Standardmodell ausgerollt. "
                                    "Quelle: OpenAI."
                                ),
                                "sources": [
                                    {
                                        "url": "https://dentro.de/ai/news/",
                                        "title": "AI News",
                                        "snippet": "GPT-5.5 OpenAI Standardmodell",
                                        "news_target_index": "1",
                                        "news_target_title": "GPT-5.5",
                                        "news_target_label": "OpenAI",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "dentro.de/ai/news" not in result
        assert "1. GPT-5.5" not in result
        assert "keine sauber belegten Meldungen" in result

    def test_response_finalizer_omits_unlinked_websearch_news_but_keeps_linked_items(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Gerichtssieg gegen Elon Musk: Eine Klage gegen OpenAI wurde abgewiesen. Quelle: FAZ.\n"
                                    "2. Sora-App: Die eigenstaendige Anwendung wurde eingestellt. Quelle: OpenAI."
                                ),
                                "sources": [
                                    {
                                        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner",
                                        "title": "channelpartner.de",
                                        "snippet": "Gerichtssieg gegen Elon Musk Klage gegen OpenAI wurde abgewiesen.",
                                    },
                                    {
                                        "url": "https://openai.com/de-DE/news/sora-in-chatgpt",
                                        "title": "OpenAI Sora in ChatGPT",
                                        "snippet": "Sora-App eigenstaendige Anwendung wurde eingestellt.",
                                    },
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "Gerichtssieg gegen Elon Musk" not in result
        assert "1. Sora-App" in result
        assert "Quelle: OpenAI. [Link](https://openai.com/de-DE/news/sora-in-chatgpt)" in result

    def test_response_finalizer_drops_stale_current_news_item(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Flaggschiff-Modell GPT-5.4: Am 5. Maerz 2026 veroeffentlichte OpenAI ein aelteres Modell. Quelle: Never Code Alone.\n"
                                    "2. OpenAI fuer Deutschland: Am 18. Mai 2026 wurde eine neue KI-Infrastruktur angekuendigt. Quelle: Heise."
                                ),
                                "sources": [
                                    {
                                        "url": "https://nevercodealone.de/example",
                                        "title": "Never Code Alone",
                                        "snippet": "GPT-5.4 Maerz 2026",
                                    },
                                    {
                                        "url": "https://www.heise.de/news/openai-deutschland",
                                        "title": "Heise OpenAI fuer Deutschland",
                                        "snippet": "OpenAI fuer Deutschland 18. Mai 2026",
                                    },
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "GPT-5.4" not in result
        assert "OpenAI fuer Deutschland" in result

    def test_response_finalizer_rejects_paywall_news_link(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Boersengang im September: Im Mai 2026 soll OpenAI vertrauliche Unterlagen vorbereiten. "
                                    "Quelle: WELT."
                                ),
                                "sources": [
                                    {
                                        "url": "https://www.welt.de/wirtschaft/plus/openai-ipo",
                                        "title": "WELT OpenAI IPO",
                                        "snippet": "OpenAI IPO Mai 2026",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "welt.de" not in result
        assert "1. Boersengang im September" not in result
        assert "keine sauber belegten Meldungen" in result

    def test_response_finalizer_rejects_openai_docs_as_news_link(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Neue Realtime-Funktionen: OpenAI erweitert im Mai 2026 die Sprachfunktionen. "
                                    "Quelle: OpenAI."
                                ),
                                "sources": [
                                    {
                                        "url": "https://platform.openai.com/docs/guides/realtime",
                                        "title": "Realtime API docs",
                                        "snippet": "OpenAI Realtime API docs",
                                        "news_target_index": "1",
                                        "news_target_title": "Neue Realtime-Funktionen",
                                        "news_target_label": "OpenAI",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "platform.openai.com/docs" not in result
        assert "1. Neue Realtime-Funktionen" not in result
        assert "keine sauber belegten Meldungen" in result

    def test_response_finalizer_removes_duplicated_news_title_prefix(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Aktualisierung auf GPT-5.5 Instant: Seit Mai 2026 ist GPT-5.5 Instant das neue Standar\n"
                                    "Aktualisierung auf GPT-5.5 Instant: Seit Mai 2026 ist GPT-5.5 Instant das neue Standardmodell in ChatGPT, "
                                    "das eine gesteigerte Faktizitaet und eine praegnantere Antwortweise bietet (Quelle: OpenAI).\n"
                                ),
                                "sources": [
                                    {
                                        "url": "https://openai.com/de-DE/index/gpt-5-5",
                                        "title": "OpenAI GPT-5.5",
                                        "snippet": "GPT-5.5 Instant Standardmodell",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "1. Aktualisierung auf GPT-5.5 Instant\n" in result
        assert "Aktualisierung auf GPT-5.5 Instant: Seit Mai" not in result
        assert "Seit Mai 2026 ist GPT-5.5 Instant das neue Standardmodell" in result

    def test_response_finalizer_does_not_reuse_sparse_gemini_sources_for_wrong_news_items(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News Mai 2026 Aktuell",
                                "text": (
                                    "1. **Geplanter Boersengang im September 2026**: OpenAI bereitet laut Medienberichten "
                                    "einen vertraulichen Antrag auf Boersenzulassung vor (Quelle: Deutschlandfunk).\n"
                                    "2. **Erfolg im Rechtsstreit gegen Elon Musk**: Ein kalifornisches Gericht wies am "
                                    "19. Mai 2026 eine Klage gegen die OpenAI-Fuehrung ab (Quelle: ChannelPartner).\n"
                                    "3. **Marktfuehrerschaft bei Enterprise Coding Agents**: Gartner ernannte OpenAI im "
                                    "Mai 2026 zum Branchenfuehrer fuer Programmierassistenten (Quelle: OpenAI).\n"
                                    "4. **Wissenschaftlicher Durchbruch in der Geometrie**: Ein spezialisiertes KI-Modell "
                                    "von OpenAI konnte am 20. Mai 2026 eine zentrale Vermutung widerlegen (Quelle: OpenAI)."
                                ),
                                "sources": [
                                    {
                                        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner",
                                        "title": "channelpartner.de",
                                        "snippet": (
                                            "2. **Erfolg im Rechtsstreit gegen Elon Musk**: Ein kalifornisches Gericht "
                                            "wies am 19. Mai 2026 eine Klage gegen die OpenAI-Fuehrung ab "
                                            "(Quelle: ChannelPartner)."
                                        ),
                                    },
                                    {
                                        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/openai",
                                        "title": "openai.com",
                                        "snippet": (
                                            "4. **Wissenschaftlicher Durchbruch in der Geometrie**: Ein spezialisiertes "
                                            "KI-Modell von OpenAI konnte am 20."
                                        ),
                                    },
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "Geplanter Boersengang" not in result
        assert (
            "Quelle: ChannelPartner. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner)"
            in result
        )
        assert "Marktfuehrerschaft bei Enterprise Coding Agents" not in result
        assert (
            "Quelle: OpenAI. [Link](https://vertexaisearch.cloud.google.com/grounding-api-redirect/openai)"
            in result
        )

    def test_response_finalizer_rejects_third_party_link_when_text_claims_openai_source(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News Mai 2026 Aktuelle Entwicklungen",
                                "text": (
                                    "1. **GPT-5.5 Instant als Standard**: OpenAI hat GPT-5.5 Instant am 5. Mai 2026 "
                                    "zum neuen Standardmodell fuer ChatGPT erhoben (Quelle: OpenAI)."
                                ),
                                "sources": [
                                    {
                                        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/buildfast",
                                        "title": "buildfastwithai.com",
                                        "snippet": (
                                            "1. **GPT-5.5 Instant als Standard**: OpenAI hat GPT-5.5 Instant am 5. Mai "
                                            "2026 zum neuen Standardmodell fuer ChatGPT erhoben."
                                        ),
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "buildfastwithai.com" not in result
        assert "grounding-api-redirect/buildfast" not in result
        assert "GPT-5.5 Instant als Standard" not in result
        assert "keine sauber belegten Meldungen" in result

    def test_response_finalizer_rejects_link_when_publisher_label_mismatches_host(self):
        from backend.services.orchestrator.response_finalizer import render_websearch_sources

        result = render_websearch_sources(
            [
                {
                    "role": "tool",
                    "name": "system.websearch",
                    "_skill_id": "system.websearch",
                    "content": json.dumps(
                        {
                            "data": {
                                "query": "OpenAI News aktuell Mai 2026",
                                "text": (
                                    "1. Gerichtssieg gegen Elon Musk: Eine Klage gegen OpenAI wurde abgewiesen. "
                                    "Quelle: FAZ."
                                ),
                                "sources": [
                                    {
                                        "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner",
                                        "title": "channelpartner.de",
                                        "snippet": "Gerichtssieg gegen Elon Musk Klage gegen OpenAI wurde abgewiesen.",
                                    }
                                ],
                            }
                        }
                    ),
                }
            ]
        )

        assert "grounding-api-redirect/channelpartner" not in result
        assert "Gerichtssieg gegen Elon Musk" not in result
        assert "keine sauber belegten Meldungen" in result


class TestWebsearchLinkQuality:
    def test_openai_docs_are_bad_for_news_but_good_for_api_docs(self):
        source = {
            "url": "https://platform.openai.com/docs/guides/realtime",
            "title": "Realtime API docs",
            "snippet": "OpenAI Realtime API Dokumentation",
        }

        news_quality = score_source_for_intent(
            source,
            intent=LinkIntent.NEWS,
            title="Neue Realtime-Funktionen",
            summary="OpenAI erweitert im Mai 2026 die Sprachfunktionen.",
            label="OpenAI",
        )
        docs_quality = score_source_for_intent(
            source,
            intent=LinkIntent.API_DOCS,
            title="Realtime API",
            summary="Dokumentation fuer die Realtime API.",
            label="OpenAI",
        )

        assert not news_quality.acceptable
        assert "docs_not_news" in news_quality.reasons
        assert docs_quality.acceptable

    def test_detail_article_beats_generic_news_landing_page(self):
        sources = [
            {
                "url": "https://dentro.de/ai/news/",
                "title": "AI News",
                "snippet": "GPT-5.5 OpenAI Standardmodell",
            },
            {
                "url": "https://openai.com/de-DE/index/gpt-5-5",
                "title": "OpenAI GPT-5.5 Instant",
                "snippet": "GPT-5.5 Instant ist seit Mai 2026 das neue Standardmodell in ChatGPT.",
            },
        ]

        url, quality = select_best_source_for_item(
            sources,
            intent=LinkIntent.NEWS,
            title="GPT-5.5 Instant",
            summary="Seit Mai 2026 ist GPT-5.5 Instant das neue Standardmodell in ChatGPT.",
            label="OpenAI",
        )

        assert url == "https://openai.com/de-DE/index/gpt-5-5"
        assert quality.acceptable
        assert is_low_value_source(sources[0], LinkIntent.NEWS)

    def test_german_detail_source_wins_over_english_generic_source(self):
        sources = [
            {
                "url": "https://openai.com/news/",
                "title": "OpenAI News",
                "snippet": "Company news overview",
            },
            {
                "url": "https://www.heise.de/news/openai-deutschland-sap-microsoft",
                "title": "OpenAI fuer Deutschland",
                "snippet": "OpenAI, SAP und Microsoft starten eine KI-Initiative fuer Deutschland.",
            },
        ]

        url, quality = select_best_source_for_item(
            sources,
            intent=LinkIntent.NEWS,
            title="OpenAI fuer Deutschland",
            summary="OpenAI, SAP und Microsoft starten eine KI-Initiative fuer Deutschland.",
            label="Heise",
        )

        assert url == "https://www.heise.de/news/openai-deutschland-sap-microsoft"
        assert quality.acceptable

    def test_broad_official_label_does_not_accept_third_party_provider_redirect(self):
        source = {
            "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/buildfast",
            "title": "buildfastwithai.com",
            "snippet": "GPT-5.5 Instant OpenAI Standardmodell ChatGPT Mai 2026",
        }

        quality = score_source_for_intent(
            source,
            intent=LinkIntent.NEWS,
            title="GPT-5.5 Instant als Standard",
            summary="OpenAI hat GPT-5.5 Instant zum neuen Standardmodell fuer ChatGPT erhoben.",
            label="OpenAI",
        )

        assert not quality.acceptable
        assert "broad_label_third_party_source" in quality.reasons

    def test_publisher_label_does_not_accept_different_news_host(self):
        source = {
            "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/channelpartner",
            "title": "channelpartner.de",
            "snippet": "Gerichtssieg gegen Elon Musk Klage gegen OpenAI wurde abgewiesen.",
        }

        quality = score_source_for_intent(
            source,
            intent=LinkIntent.NEWS,
            title="Gerichtssieg gegen Elon Musk",
            summary="Eine Klage gegen OpenAI wurde abgewiesen.",
            label="FAZ",
        )

        assert not quality.acceptable
        assert "source_label_host_mismatch" in quality.reasons

    def test_ambiguous_official_provider_redirect_is_not_used_as_news_detail(self):
        source = {
            "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/openai",
            "title": "openai.com",
            "snippet": (
                "3. **Auszeichnung als Gartner-Marktfuehrer:** OpenAI wurde eingestuft. "
                "4. **Standard fuer Inhaltstransparenz:** OpenAI praesentierte neue Massnahmen."
            ),
        }

        quality = score_source_for_intent(
            source,
            intent=LinkIntent.NEWS,
            title="Auszeichnung als Gartner-Marktfuehrer",
            summary="OpenAI wurde als fuehrend fuer Coding-Agenten eingestuft.",
            label="OpenAI",
        )

        assert not quality.acceptable
        assert "ambiguous_official_provider_redirect" in quality.reasons


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
                ["Suchergebnisse mit mehreren Quellen"],
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
