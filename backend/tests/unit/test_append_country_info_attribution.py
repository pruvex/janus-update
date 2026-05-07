"""append_country_info_attribution_from_tools / append_tool_attributions mit Country."""

import json

from backend.renderers.attribution import (
    append_country_info_attribution_from_tools,
    append_tool_attributions_from_tools,
)


def _country_tool(name_field: str = "system.country_info"):
    return {
        "role": "tool",
        "name": name_field,
        "content": json.dumps(
            {
                "status": "ok",
                "data": {
                    "name": "Frankreich",
                    "capital": "Paris",
                    "population": 66351959,
                    "region": "Europe",
                    "currencies": ["Euro (EUR)"],
                    "languages": ["French"],
                },
            },
            ensure_ascii=False,
        ),
    }


def test_country_inserts_before_suggestion_block():
    prose = (
        "Paris ist die Hauptstadt von Frankreich.\n\n"
        "💡 Passende nächste Schritte:\n"
        "• Mehr?"
    )
    out = append_country_info_attribution_from_tools(prose, [_country_tool()])
    assert "Paris" in out or "Frankreich" in out
    q_pos = out.index("Quelle: REST Countries API")
    sug_pos = out.index("💡")
    assert q_pos < sug_pos
    assert "(restcountries.com)" in out


def test_country_idempotent_with_legacy_short_label():
    prose = "Fakten.\n\nQuelle: REST Countries API"
    out = append_country_info_attribution_from_tools(prose, [_country_tool()])
    assert out.strip() == prose.strip()


def test_country_idempotent_full_domain_label():
    label = "REST Countries API (restcountries.com)"
    prose = f"Fakten.\n\nQuelle: {label}"
    out = append_country_info_attribution_from_tools(prose, [_country_tool()])
    assert out.strip() == prose.strip()


def test_country_skill_id_alias():
    tr = _country_tool(name_field="get_country_info_tool")
    tr["_skill_id"] = "system.country_info"
    out = append_country_info_attribution_from_tools(
        "Text.\n\n💡 x:\n• y", [tr]
    )
    assert "Quelle: REST Countries API" in out


def test_tool_attributions_three_layers_before_suggestions():
    tools = [
        {
            "role": "tool",
            "name": "system.weather",
            "content": json.dumps(
                {"status": "ok", "data": {"source": "open-meteo"}},
                ensure_ascii=False,
            ),
        },
        {
            "role": "tool",
            "name": "system.routing",
            "content": json.dumps(
                {
                    "status": "ok",
                    "data": {"distance_km": 100.0, "maps_link": "https://x"},
                },
                ensure_ascii=False,
            ),
        },
        _country_tool(),
    ]
    prose = "Gemischt.\n\n💡 Ideen:\n• ok"
    out = append_tool_attributions_from_tools(prose, tools)
    ow = out.index("Quelle: Open-Meteo")
    oru = out.index("Quelle: OSRM")
    oc = out.index("Quelle: REST Countries API")
    s = out.index("💡")
    assert ow < oru < oc < s
