"""append_weather_attribution_from_tools: Quelle-Zeile am Assistenztext trotz LLM-Umformulierung."""

import json

from backend.renderers.attribution import append_weather_attribution_from_tools, render_weather_forecast_from_tools


def test_appends_when_model_omitted_source():
    tool_results = [
        {
            "role": "tool",
            "name": "system.weather",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {"source": "open-meteo", "city": "München"},
                },
                ensure_ascii=False,
            ),
        }
    ]
    prose = (
        "In München werden heute leichte Regenschauer erwartet. "
        "Die Temperaturen liegen zwischen 12 °C und 23,5 °C."
    )
    out = append_weather_attribution_from_tools(prose, tool_results)
    assert prose in out or prose.split(".")[0] in out  # Haupttext bleibt
    assert "Quelle:" in out
    assert "Open-Meteo" in out


def test_idempotent_when_exact_quelle_already_present():
    label = "Open-Meteo"
    prose = f"Warm und sonnig.\n\nQuelle: {label}"
    tool_results = [
        {
            "role": "tool",
            "name": "system.weather",
            "content": json.dumps(
                {"status": "ok", "data": {"source": "open-meteo", "forecast": prose}},
                ensure_ascii=False,
            ),
        }
    ]
    out = append_weather_attribution_from_tools(prose, tool_results)
    assert out.strip() == prose.strip()


def test_idempotent_when_legacy_long_quelle_prefix_present():
    """Ältere Antworten: Zeile beginnt mit „Quelle: Open-Meteo …“ — nicht erneut einfügen."""
    label = (
        "Open-Meteo (Wettervorhersage); "
        "Ortszuordnung OpenStreetMap (Nominatim)"
    )
    prose = f"Warm und sonnig.\n\nQuelle: {label}"
    tool_results = [
        {
            "role": "tool",
            "name": "system.weather",
            "content": json.dumps(
                {"status": "ok", "data": {"source": "open-meteo", "forecast": prose}},
                ensure_ascii=False,
            ),
        }
    ]
    out = append_weather_attribution_from_tools(prose, tool_results)
    assert out.strip() == prose.strip()


def test_inserts_quelle_before_suggestion_block():
    tool_results = [
        {
            "role": "tool",
            "name": "system.weather",
            "content": json.dumps(
                {"status": "ok", "data": {"source": "open-meteo"}},
                ensure_ascii=False,
            ),
        }
    ]
    prose = (
        "In München kühler.\n"
        "Max. 19 °C\n\n"
        "💡 Passende nächste Schritte:\n"
        "• Frage morgen?"
    )
    out = append_weather_attribution_from_tools(prose, tool_results)
    assert "Max. 19 °C" in out
    assert "💡 Passende nächste Schritte:" in out
    q_pos = out.index("Quelle: Open-Meteo")
    sug_pos = out.index("💡")
    assert q_pos < sug_pos
    assert out.index("Max. 19 °C") < q_pos


def test_matches_skill_id_when_name_differs():
    """Executor kann API-Namen liefern; Zuordnung über _skill_id."""
    tool_results = [
        {
            "role": "tool",
            "name": "get_weather_from_api_tool",
            "_skill_id": "system.weather",
            "content": json.dumps(
                {"status": "ok", "data": {"source": "open-meteo"}},
                ensure_ascii=False,
            ),
        }
    ]
    out = append_weather_attribution_from_tools("Sonst nur Prosa.", tool_results)
    assert "Quelle:" in out
    assert "Open-Meteo" in out


def test_skips_when_no_weather_tool():
    out = append_weather_attribution_from_tools(
        "Nur Smalltalk ohne Tool.",
        [{"role": "tool", "name": "memory.read", "content": "{}"}],
    )
    assert "Quelle:" not in out


def test_render_weather_forecast_from_tools_prefers_tool_forecast_text():
    forecast = (
        "Das Wetter fuer Koeln (heute, 26.05.2026) im Ueberblick:\n"
        "* Zustand: Bedeckt\n"
        "* Temperaturen: Hoechstwerte bis zu 32.1 C, Tiefstwerte bei 18.5 C\n"
        "* Regen: Die Niederschlagswahrscheinlichkeit liegt bei 0 %\n"
        "* Wind: Leichte Brisen mit Boeen bis zu 7.9 km/h\n\n"
        "Quelle: Open-Meteo"
    )
    tool_results = [
        {
            "role": "tool",
            "name": "system.weather",
            "_skill_id": "system.weather",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {
                        "forecast": forecast,
                        "source": "open-meteo",
                        "city": "Koeln",
                    },
                },
                ensure_ascii=False,
            ),
        }
    ]

    assert render_weather_forecast_from_tools(tool_results) == forecast
