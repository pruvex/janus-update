"""Kurze Quellenzeilen für deterministische Renderer (nur Text, keine URLs)."""

import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Vorschlagsblöcke („💡 Vorschlag“ / „Passende nächste Schritte“); optional * fürs Markdown-Bold
_SUGGESTION_BLOCK_START = re.compile(r"(?im)^[\*\s]*💡\s")


_SUGGESTION_BLOCK_START = re.compile(
    r"(?im)^[\*\s]*(?:ðŸ’¡\s|💡\s|Passende\s+n(?:ä|ae|Ã¤)chste\s+Schritte\s*:?)"
)


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


def insert_quelle_block_before_suggestion_block(body: str, block: str) -> str:
    """Fuegt einen mehrzeiligen Quellenblock direkt unter den Inhalt, aber vor Vorschlaege."""
    value = (block or "").strip()
    if not value:
        return body
    m = _SUGGESTION_BLOCK_START.search(body)
    if m:
        head = body[: m.start()].rstrip()
        tail = body[m.start() :].lstrip()
        sep_h = "\n\n" if head else ""
        return f"{head}{sep_h}{value}\n\n{tail}"
    trimmed = body.rstrip()
    sep = "\n\n" if trimmed else ""
    return f"{trimmed}{sep}{value}"


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


def _domain_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse

        return urlparse(str(url or "").strip()).netloc.replace("www.", "")
    except Exception:
        return ""


def _is_google_redirect_url(url: str) -> bool:
    domain = _domain_from_url(url)
    return domain.endswith("vertexaisearch.cloud.google.com") or domain.endswith("google.com")


def _extract_markdown_source_links(text: str) -> List[tuple[str, str]]:
    source_tail = str(text or "")
    marker = re.search(r"(?im)^\s*(?:#{1,6}\s*)?(?:\d+\.?\s*)?Quellen?\b.*$", source_tail)
    if marker:
        source_tail = source_tail[marker.start() :]
    links: List[tuple[str, str]] = []
    for label, url in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", source_tail):
        clean_url = str(url or "").strip()
        if clean_url:
            links.append((str(label or "").strip(), clean_url))
    return links


def _has_inline_markdown_source_links(text: str) -> bool:
    """True when the answer already cites sources in the content body.

    Source-list-only links still need deterministic cleanup, but inline links
    should not get an extra duplicate "Quelle:" footer.
    """
    value = str(text or "")
    marker = re.search(r"(?im)^\s*(?:#{1,6}\s*)?(?:\d+\.?\s*)?Quellen?\b.*$", value)
    body = value[: marker.start()] if marker else value
    return bool(re.search(r"\[[^\]]+\]\(https?://[^)]+\)", body))


def _strip_websearch_source_sections(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return value
    patterns = (
        r"(?ims)\n?\s*#{1,6}\s*\d+\.?\s*Quellen\s*$[\s\S]*$",
        r"(?ims)\n?\s*\d+\.?\s*Quellen\s*$[\s\S]*$",
        r"(?ims)\n?\s*\*\*Quellen\*\*\s*:?[\s\S]*$",
        r"(?ims)\n?\s*Quellen\s*:?[\s\S]*$",
        r"(?im)^\s*\*\*Quelle:\*\*\s*\[.+?\]\(https?://[^)]+\)(?:\s*\([^)]+\))?\s*$",
        r"(?im)^\s*(?:\*\*)?Quelle(?:\*\*)?:\s*\[.+?\]\(https?://[^)]+\)(?:\s*\([^)]+\))?\s*$",
    )
    for pattern in patterns:
        value = re.sub(pattern, "", value).rstrip()
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _extract_first_source_from_payload(payload: Dict[str, Any]) -> tuple[str, str]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return "", ""

    candidates: List[Dict[str, Any]] = []
    sources = data.get("sources")
    if isinstance(sources, list):
        candidates.extend([source for source in sources if isinstance(source, dict)])
    items = data.get("items")
    if isinstance(items, list):
        candidates.extend([item for item in items if isinstance(item, dict)])

    for source in candidates:
        url = str(source.get("url") or source.get("source_url") or "").strip()
        if not url:
            continue
        title = str(source.get("title") or source.get("name") or "").strip()
        if not title:
            try:
                from urllib.parse import urlparse

                title = urlparse(url).netloc.replace("www.", "") or url
            except Exception:
                title = url
        return title, url
    return "", ""


def _source_label_for_clickable_link(title: str, url: str) -> str:
    raw_title = str(title or "").strip()
    raw_url = str(url or "").strip()
    domain = _domain_from_url(raw_url)

    title_domain_match = re.search(
        r"\b([a-z0-9-]+\.(?:de|com|org|net|eu|info|tv|co\.uk))\b",
        raw_title,
        re.IGNORECASE,
    )
    if title_domain_match:
        return title_domain_match.group(1).lower()

    redirect_domains = ("vertexaisearch.cloud.google.com", "google.com")
    if domain and not any(domain.endswith(redirect) for redirect in redirect_domains):
        return domain

    if raw_title and raw_title.lower() not in {"quelle", "gefundene quelle"}:
        compact = re.sub(r"\s+", " ", raw_title).strip()
        return compact[:80]
    return domain or "Quelle"


def _build_hidden_source_link_block(domain_label: str, url: str) -> str:
    safe_domain = str(domain_label or "Quelle").strip()
    safe_url = str(url or "").strip()
    return f"Quelle: [Link]({safe_url}) ({safe_domain})"


def append_websearch_attribution_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Ergaenzt fuer erfolgreiche system.websearch-Ergebnisse immer einen klickbaren Quellenlink."""
    text = str(final_text or "").strip()
    if not text or not tool_results:
        return str(final_text or "")

    existing_links = _extract_markdown_source_links(text)
    if _has_inline_markdown_source_links(text) and not any(_is_google_redirect_url(url) for _, url in existing_links):
        return str(final_text or "")

    source_links_from_text = [
        (label, url)
        for label, url in _extract_markdown_source_links(text)
        if not _is_google_redirect_url(url)
    ]
    text_without_sources = _strip_websearch_source_sections(text)

    for tr in reversed(tool_results):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        skill_id = str(tr.get("_skill_id") or tr.get("skill_id") or "").strip().lower()
        if name not in ("system.websearch", "system_websearch") and skill_id != "system.websearch":
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
        if source_links_from_text:
            title, url = source_links_from_text[0]
        else:
            title, url = _extract_first_source_from_payload(parsed)
        if not url:
            continue
        if _is_google_redirect_url(url):
            continue
        label = _source_label_for_clickable_link(title, url)
        return insert_quelle_block_before_suggestion_block(
            text_without_sources or text,
            _build_hidden_source_link_block(label, url),
        )

    if text_without_sources != text and any(_is_google_redirect_url(url) for _, url in existing_links):
        return text_without_sources

    return str(final_text or "")


def append_tool_attributions_from_tools(final_text: str, tool_results: List[Dict[str, Any]]) -> str:
    """Websearch-, Wetter-, Wikipedia-, Routing- und Laenderinfo-Quelle vor Vorschlaegen bzw. Textende."""
    t = append_websearch_attribution_from_tools(final_text, tool_results)
    t = append_weather_attribution_from_tools(t, tool_results)
    t = append_wikipedia_attribution_from_tools(t, tool_results)
    t = append_routing_attribution_from_tools(t, tool_results)
    return append_country_info_attribution_from_tools(t, tool_results)
