import json

from backend.services.tool_result_renderer import (
    append_missing_pdf_facts,
    append_missing_pdf_paths,
    render_local_business_from_tool_results,
    render_local_business_no_results_text,
    render_routing_segments_text,
)


def test_render_local_business_from_tool_results_formats_business_entries():
    tool_results = [
        {
            "_skill_id": "system.local_business",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "query": "italienische Restaurants",
                        "location": "Berlin Prenzlauer Berg",
                        "businesses": [
                            {
                                "name": "Ristorante Roma",
                                "description": "Hausgemachte Pasta und Pizza.",
                                "category": "Italienisch",
                                "address": "Teststraße 1",
                                "opening_hours": "Mo-So 12-22 Uhr",
                                "phone": "+49 30 123456",
                                "website": "https://roma.example",
                                "menu_url": "https://roma.example/menu",
                                "reservation_url": "https://roma.example/book",
                            }
                        ],
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    text = render_local_business_from_tool_results(tool_results)

    assert text is not None
    assert "Hier sind passende italienische Restaurants in Berlin Prenzlauer Berg" in text
    assert "**Ristorante Roma**" in text
    assert "Speisekarte: [Link](https://roma.example/menu)" in text
    assert "Reservierung: [Link](https://roma.example/book)" in text


def test_render_local_business_from_tool_results_ignores_placeholder_entries():
    tool_results = [
        {
            "_skill_id": "system.local_business",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "query": "italienische Restaurants",
                        "location": "Berlin Prenzlauer Berg",
                        "businesses": [
                            {
                                "name": "Keine passenden Suchergebnisse gefunden.",
                                "address": "Adresse nicht gefunden",
                                "website": "",
                            }
                        ],
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    text = render_local_business_from_tool_results(tool_results)

    assert text is None


def test_render_local_business_no_results_text_returns_deterministic_fallback():
    tool_results = [
        {
            "_skill_id": "system.local_business",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "query": "italienische Restaurants",
                        "location": "Berlin Prenzlauer Berg",
                        "businesses": [],
                        "result_count": 0,
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    text = render_local_business_no_results_text(tool_results)

    assert text is not None
    assert "italienische Restaurants" in text
    assert "Berlin Prenzlauer Berg" in text


def test_render_routing_segments_text_includes_links():
    text = render_routing_segments_text(
        [
            {
                "origin": "Berlin",
                "destination": "Hamburg",
                "distance_km": "289",
                "duration": "2 Std. 54 Min.",
                "maps_link": "https://www.google.com/maps/dir/?api=1&origin=Berlin&destination=Hamburg",
            }
        ]
    )

    assert "1. Berlin -> Hamburg: 289 km, 2 Std. 54 Min." in text
    assert "Google Maps Links:" in text
    assert "https://www.google.com/maps/dir/?api=1&origin=Berlin&destination=Hamburg" in text


def test_append_missing_pdf_paths_appends_new_paths_only():
    text = append_missing_pdf_paths("Fertig.", ["C:\\Docs\\bericht.pdf"])

    assert "Gespeicherte PDF-Datei(en):" in text
    assert "C:\\Docs\\bericht.pdf" in text


def test_append_missing_pdf_facts_appends_missing_facts_only():
    text = append_missing_pdf_facts("Zusammenfassung vorhanden.", ["Hauptstadt: Stockholm", "Einwohner: 10 Mio."])

    assert "Hier sind die recherchierten Fakten:" in text
    assert "Hauptstadt: Stockholm" in text
    assert "Einwohner: 10 Mio." in text
