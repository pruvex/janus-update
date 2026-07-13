"""Provider-family response finishing at the central gateway-router seam."""

import logging
import re
from typing import Any, Callable, Dict, List, Mapping, Optional

from backend.llm_providers.shared.utils import (
    _extract_release_line_title,
    _extract_websearch_sources_for_link_repair,
    _find_best_source_for_release_title,
)

logger = logging.getLogger("janus_backend")


def _is_game_release_websearch_prompt(user_prompt: str) -> bool:
    lowered = str(user_prompt or "").strip().lower()
    if not lowered:
        return False
    months = (
        "januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember",
        "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
    )
    is_game_query = any(token in lowered for token in ("spiele", "games", "nintendo", "switch", "playstation", "xbox", "pc"))
    is_release_query = any(token in lowered for token in ("erscheinen", "release", "veröffentlich", "nächsten monat", "kommenden monat", "termin")) or any(month in lowered for month in months)
    return is_game_query and is_release_query


def ensure_openai_release_list_links(
    response: Dict[str, Any], *, user_prompt: str, tool_results: Optional[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Preserve legacy OpenAI release-list link repair outside gateway ownership."""
    if not isinstance(response, dict) or not _is_game_release_websearch_prompt(user_prompt):
        return response
    text = str(response.get("text") or "")
    if not text.strip():
        return response
    sources = _extract_websearch_sources_for_link_repair(tool_results or [])
    if not sources:
        return response
    updated_lines: List[str] = []
    changed = False
    for line in text.splitlines():
        stripped = line.strip()
        if not re.match(r"^[-*+]\s+", stripped):
            updated_lines.append(line)
            continue
        title = _extract_release_line_title(stripped)
        if not title:
            updated_lines.append(line)
            continue
        matched_url = _find_best_source_for_release_title(title, sources)
        line_without_link = re.sub(r"\s*[—–-]\s*\[Mehr erfahren\]\([^)]+\)", "", line).rstrip()
        if matched_url:
            updated_lines.append(f"{line_without_link} — [Mehr erfahren]({matched_url})")
        else:
            updated_lines.append(f"{line_without_link} — (Keine spezifische Quelle gefunden)")
        changed = True
    if not changed:
        return response
    updated_response = dict(response)
    updated_response["text"] = "\n".join(updated_lines)
    logger.info("OPENAI LINK-REPAIR: Links in der Release-Liste wurden semantisch korrigiert.")
    return updated_response


def ensure_gemini_grounding_links(response: Dict[str, Any], **_: Any) -> Dict[str, Any]:
    """Render preserved Gemini grounding metadata at the central post-response seam."""
    if not isinstance(response, dict):
        return response
    metadata = response.get("_preserved_metadata")
    if not isinstance(metadata, Mapping):
        return response
    from backend.llm_providers.gemini.link_renderer import get_link_renderer

    return get_link_renderer().render_final_response(response, metadata=dict(metadata))


ResponsePostprocessor = Callable[..., Dict[str, Any]]
_POSTPROCESSORS: Dict[str, ResponsePostprocessor] = {
    "openai_compat": ensure_openai_release_list_links,
    "gemini_native": ensure_gemini_grounding_links,
}
_PROVIDER_FAMILIES = {"openai": "openai_compat", "gemini": "gemini_native", "google": "gemini_native"}


def postprocess_provider_response(provider: str, response: Dict[str, Any], **context: Any) -> Dict[str, Any]:
    """Apply the registered provider-family finisher or return the response unchanged."""
    family = _PROVIDER_FAMILIES.get(str(provider or "").strip().lower())
    processor = _POSTPROCESSORS.get(family or "")
    return processor(response, **context) if processor else response
