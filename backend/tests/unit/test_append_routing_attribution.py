"""append_routing_attribution_from_tools / append_tool_attributions_from_tools (Quelle vor 💡)."""

import json

from backend.renderers.attribution import (
    append_routing_attribution_from_tools,
    append_tool_attributions_from_tools,
)


def _routing_tool(distance_km: float = 100.0, name: str = "system.routing"):
    return {
        "role": "tool",
        "name": name,
        "content": json.dumps(
            {
                "status": "ok",
                "data": {
                    "origin": "Köln",
                    "destination": "München",
                    "distance_km": distance_km,
                    "duration": "1 Std.",
                    "maps_link": "https://www.google.com/maps/dir/",
                },
            },
            ensure_ascii=False,
        ),
    }


def test_routing_inserts_before_suggestion_block():
    prose = (
        "Von Köln nach München sind es ca. 576 km.\n\n"
        "💡 Passende nächste Schritte:\n"
        "• Zugroute?"
    )
    out = append_routing_attribution_from_tools(prose, [_routing_tool()])
    assert "576 km" in out
    assert "💡 Passende nächste Schritte:" in out
    q_pos = out.index("Quelle: OSRM")
    sug_pos = out.index("💡")
    assert q_pos < sug_pos


def test_routing_idempotent_short_quelle():
    prose = "500 km.\n\nQuelle: OSRM"
    out = append_routing_attribution_from_tools(prose, [_routing_tool()])
    assert out.strip() == prose.strip()


def test_routing_idempotent_legacy_long_quelle_line():
    legacy = (
        "Quelle: OSRM (Routenberechnung); Ortszuordnung OpenStreetMap (Nominatim)"
    )
    prose = f"500 km.\n\n{legacy}"
    out = append_routing_attribution_from_tools(prose, [_routing_tool()])
    assert out.strip() == prose.strip()


def test_routing_matches_skill_id_alias():
    tr = _routing_tool(name="get_distance_and_route_tool")
    tr["_skill_id"] = "system.routing"
    out = append_routing_attribution_from_tools("Nur Prosa.\n\n💡 Vorschlag:\n• x", [tr])
    assert "Quelle: OSRM" in out


def test_tool_attributions_weather_then_routing_before_suggestions():
    tools = [
        {
            "role": "tool",
            "name": "system.weather",
            "content": json.dumps(
                {"status": "ok", "data": {"source": "open-meteo"}},
                ensure_ascii=False,
            ),
        },
        _routing_tool(),
    ]
    prose = "Wetter und Strecke.\n\n💡 Ideen:\n• ok"
    out = append_tool_attributions_from_tools(prose, tools)
    w = out.index("Quelle: Open-Meteo")
    r = out.index("Quelle: OSRM")
    s = out.index("💡")
    assert w < r < s
