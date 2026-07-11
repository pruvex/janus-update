import json

from backend.services.orchestrator.response_finalizer import _build_calendar_weather_combo_response


def test_build_calendar_weather_combo_response_keeps_calendar_and_weather():
    text = _build_calendar_weather_combo_response(
        [
            {
                "role": "tool",
                "name": "calendar_list_events",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {"events": [], "listing_text": "", "event_count": 0},
                        "message": "Keine Termine im angegebenen Zeitraum gefunden.",
                        "output": "Keine Termine im angegebenen Zeitraum gefunden.",
                    },
                    ensure_ascii=False,
                ),
            },
            {
                "role": "tool",
                "name": "system_weather",
                "_skill_id": "system.weather",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "forecast": "Das Wetter fuer Koeln (heute, 08.07.2026) im Ueberblick:\n* Zustand: Bedeckt\n\nQuelle: Open-Meteo",
                            "city": "Koeln",
                            "source": "open-meteo",
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ]
    )

    assert "Keine Termine im angegebenen Zeitraum gefunden." in text
    assert "Das Wetter fuer Koeln" in text
