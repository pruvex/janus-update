"""Kurze Quellenzeilen für deterministische Renderer (nur Text, keine URLs)."""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Vorschlagsblöcke („💡 Vorschlag“ / „Passende nächste Schritte“); optional * fürs Markdown-Bold
_SUGGESTION_BLOCK_START = re.compile(r"(?im)^[\*\s]*💡\s")


def append_quelle_line(body: str, label: str) -> str:
    """Hängt unter dem Markdown-Body eine Absatzzeile „Quelle: …“ an."""
    text = (label or "").strip()
    if not text:
        return body
    trimmed = body.rstrip()
    sep = "\n\n" if trimmed else ""
    return f"{trimmed}{sep}Quelle: {text}"


def insert_quelle_line_before_suggestion_block(body: str, label: str) -> str:
    """„Quelle: …“ direkt unter den Inhalt, aber vor einen Block ab Zeilenanfang „💡 …“."""
    lbl = (label or "").strip()
    if not lbl:
        return body
    qline = f"Quelle: {lbl}"
    m = _SUGGESTION_BLOCK_START.search(body)
    if m:
        head = body[: m.start()].rstrip()
        tail = body[m.start() :].lstrip()
        sep_h = "\n\n" if head else ""
        return f"{head}{sep_h}{qline}\n\n{tail}"
    return append_quelle_line(body, lbl)


def weather_source_label(api_source: str | None) -> str:
    """Übersetzt Tool-`source`-Slug in eine verständliche Kurzquelle ohne Link."""
    key = (api_source or "").strip().lower()
    if key == "open-meteo":
        return "Open-Meteo"
    if key in ("wttr.in", "wttr"):
        return "wttr.in (Kurzvorhersage)"
    if (api_source or "").strip():
        return (api_source or "").strip()
    return ""


# Kurz wie „Open-Meteo“; Geocoding bleibt technisch unsichtbar in der Nutzerzeile.
ROUTING_SOURCE_LABEL = "OSRM"

COUNTRY_INFO_SOURCE_LABEL = "REST Countries API (restcountries.com)"

WIKIPEDIA_SOURCE_LABEL = "Wikipedia"


def append_weather_attribution_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Hängt „Quelle: …“ aus dem letzten erfolgreichen system.weather-Tool an.

    Wird im Tool-Loop-Endtext (inkl. SSE ``stream_complete``) genutzt, damit die UI die Quelle
    sieht, selbst wenn das LLM sie beim Umformulieren weglässt (Finalize allein reicht nicht).
    """
    text = str(final_text or "").strip()
    if not text or not tool_results:
        return str(final_text or "")

    for tr in reversed(tool_results):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        skill_id = str(tr.get("_skill_id") or "").strip().lower()
        if name != "system.weather" and skill_id != "system.weather":
            continue
        raw = tr.get("_raw_content") or tr.get("content") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(parsed, dict):
            continue
        if str(parsed.get("status") or "").strip().lower() != "ok":
            continue
        data = parsed.get("data")
        if not isinstance(data, dict):
            continue
        label = weather_source_label(str(data.get("source") or "") or "")
        if not label:
            continue
        needle = f"Quelle: {label}"
        # Bestehende Zeile mit gleichem Präfix (z. B. ältere Langform) nicht verdoppeln
        if needle in text:
            return str(final_text or "")
        out = insert_quelle_line_before_suggestion_block(text, label)
        return out

    return str(final_text or "")


def append_routing_attribution_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Ergänzt „Quelle: OSRM“, wenn erfolgreiches ``system.routing`` (Distanz/Route) verwendet wurde."""
    text = str(final_text or "").strip()
    if not text or not tool_results:
        return str(final_text or "")

    logger.info(f"ATTRIBUTION-CHECK: tool_results count={len(tool_results)}, results={tool_results}")

    for tr in reversed(tool_results):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        skill_id = str(tr.get("_skill_id") or "").strip().lower()
        logger.debug(f"[ATTRIBUTION-DEBUG] Checking tool result: name='{name}', skill_id='{skill_id}'")
        # Check both canonical name (system.routing) and provider-safe variant (system_routing)
        if name not in ("system.routing", "system_routing") and skill_id not in ("system.routing", "system_routing"):
            logger.debug(f"[ATTRIBUTION-DEBUG] Skipping tool result: name='{name}', skill_id='{skill_id}' (not system.routing)")
            continue
        raw = tr.get("_raw_content") or tr.get("content") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(parsed, dict):
            continue
        if str(parsed.get("status") or "").strip().lower() != "ok":
            continue
        data = parsed.get("data")
        if not isinstance(data, dict):
            continue
        if data.get("distance_km") is None and not data.get("maps_link"):
            continue
        label = ROUTING_SOURCE_LABEL
        needle = f"Quelle: {label}"
        if needle in text:
            return str(final_text or "")
        out = insert_quelle_line_before_suggestion_block(text, label)
        logger.info(f"ATTRIBUTION-SUCCESS: Added 'Quelle: {label}' to text")
        return out

    logger.info(f"ATTRIBUTION-FAIL: No matching routing tool result found")
    return str(final_text or "")


def append_country_info_attribution_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Ergänzt „Quelle: REST Countries API …“, wenn erfolgreiches ``system.country_info`` verwendet wurde."""
    text = str(final_text or "").strip()
    if not text or not tool_results:
        return str(final_text or "")

    for tr in reversed(tool_results):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        skill_id = str(tr.get("_skill_id") or "").strip().lower()
        if name != "system.country_info" and skill_id != "system.country_info":
            continue
        raw = tr.get("_raw_content") or tr.get("content") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(parsed, dict):
            continue
        if str(parsed.get("status") or "").strip().lower() != "ok":
            continue
        data = parsed.get("data")
        if not isinstance(data, dict):
            continue
        if not any(k in data for k in ("name", "capital", "population", "region")):
            continue
        label = COUNTRY_INFO_SOURCE_LABEL
        needle = f"Quelle: {label}"
        if needle in text:
            return str(final_text or "")
        # Ältere Kurzform „REST Countries API“ ohne Domain
        if "Quelle: REST Countries API" in text:
            return str(final_text or "")
        out = insert_quelle_line_before_suggestion_block(text, label)
        return out

    return str(final_text or "")


def append_tool_attributions_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Wetter-, Routing- und Länderinfo-Quelle (jeweils vor 💡 bzw. Textende)."""
    t = append_weather_attribution_from_tools(final_text, tool_results)
    t = append_routing_attribution_from_tools(t, tool_results)
    return append_country_info_attribution_from_tools(t, tool_results)


def append_wikipedia_attribution_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Ergaenzt "Quelle: Wikipedia", wenn erfolgreiches system.wikipedia_summary genutzt wurde."""
    text = str(final_text or "").strip()
    if not text or not tool_results:
        return str(final_text or "")

    for tr in reversed(tool_results):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        skill_id = str(tr.get("_skill_id") or "").strip().lower()
        if name not in ("system.wikipedia_summary", "system_wikipedia_summary") and skill_id not in (
            "system.wikipedia_summary",
            "system_wikipedia_summary",
        ):
            continue
        raw = tr.get("_raw_content") or tr.get("content") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(parsed, dict):
            continue
        if str(parsed.get("status") or "").strip().lower() != "ok":
            continue
        data = parsed.get("data")
        if not isinstance(data, dict):
            continue
        if not (data.get("title") or data.get("summary") or data.get("url")):
            continue
        if "Quelle: Wikipedia" in text:
            return str(final_text or "")
        return insert_quelle_line_before_suggestion_block(text, WIKIPEDIA_SOURCE_LABEL)

    return str(final_text or "")


def append_tool_attributions_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Wetter-, Wikipedia-, Routing- und Laenderinfo-Quelle vor Vorschlaegen bzw. Textende."""
    t = append_weather_attribution_from_tools(final_text, tool_results)
    t = append_wikipedia_attribution_from_tools(t, tool_results)
    t = append_routing_attribution_from_tools(t, tool_results)
    return append_country_info_attribution_from_tools(t, tool_results)
