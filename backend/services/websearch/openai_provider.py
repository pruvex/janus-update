# backend/services/websearch/openai_provider.py
import logging
import re
import json
import sentry_sdk
from typing import Any, Optional
from urllib.parse import urlparse
from openai import AsyncOpenAI, BadRequestError
from .base_provider import BaseWebSearchProvider, WebSearchResult, WebSearchSource, WebSearchMetadata
from backend.services.cost_calculator import calculate_cost
from backend.services.websearch.query_bias import (
    augment_query_with_local_bias,
    enforce_german_market_bias,
)

logger = logging.getLogger("janus_backend")

_MAX_RETURNED_SOURCES = 1
_MAX_APPENDED_SOURCE_LINKS = 4
_MAX_TEXT_CHARS = 3200


def _build_compact_sources(sources: list[dict[str, Any]]) -> list[dict[str, str]]:
    compact_sources: list[dict[str, str]] = []
    for src in sources or []:
        if not isinstance(src, dict):
            continue
        url = str(src.get("url") or "").strip()
        if not url:
            continue
        title = str(src.get("title") or src.get("name") or "").strip()
        snippet = str(src.get("text") or src.get("snippet") or "").strip()
        compact_source = {"url": url}
        if title:
            compact_source["title"] = title
        if snippet:
            compact_source["snippet"] = snippet[:220].strip()
        compact_sources.append(compact_source)
    return compact_sources


_PRICE_INTEGRITY_RULE = (
    "PREIS-INTEGRITÄT (ABSOLUTES GEBOT): "
    "Nenne einen Preis NUR dann, wenn du ihn WORTWÖRTLICH in einem Such-Snippet findest. "
    "Schätze, runde oder interpoliere KEINE Preise. "
    "Wenn kein Preis im Snippet steht, schreibe exakt: 'Preis nur via Link verfügbar'."
)

_GROUNDING_DIRECTIVE = (
    "GROUNDING-PFLICHT: Wenn Suchergebnisse vorliegen, darfst du NIEMALS schreiben "
    "'Keine spezifische Quelle gefunden' oder aehnliches. "
    "Halluziniere NIEMALS Preise, Produktgenerationen (z.B. M5, M4, Pro Max) oder "
    "Spezifikationen, die nicht WOERTLICH in den Suchergebnissen stehen. "
    "Markiere jede Preisangabe mit dem Hinweis '(laut Suchergebnis)'."
)

_DIAMOND_SEARCH_SYSTEM_PROMPT = (
    "💎 DIAMOND-STANDARD SUCH-DIREKTIVE: Du bist ein Präzisions-Recherche-Agent. "
    "Deine Aufgabe ist es, eine Websuche durchzuführen und die Ergebnisse VOLLSTÄNDIG und LÜCKENLOS zusammenzufassen. "
    "Übersehe niemals ein Datum, einen Preis oder einen Namen, der in den Suchergebnissen vorkommt. "
    "Besonders bei Listen (z. B. Release-Termine) ist Vollständigkeit wichtiger als Kürze. "
    "Antworte direkt mit den Fakten, sei extrem präzise und nenne Quellen. "
    + _PRICE_INTEGRITY_RULE + " " + _GROUNDING_DIRECTIVE
)


def _build_diamond_search_system_prompt(model_id: str) -> str:
    return (
        "Du bist ein Präzisions-Recherche-Agent für Janus. Deine Aufgabe ist die faktenbasierte Suche.\n\n"
        "DIREKTIVE: Nenne Namen, Teams und Punkte vollständig. "
        "VERBOT: Keine URLs oder Markdown-Links im Text. "
        "PROAKTIVITÄT: Nutze das web_search Tool sofort.\n"
        + _PRICE_INTEGRITY_RULE + "\n" + _GROUNDING_DIRECTIVE
    )

class OpenAIWebSearchProvider(BaseWebSearchProvider):
    
    def _clean_raw_text(self, text: str) -> str:
        """Entfernt JSON-Artefakte aus dem Text, falls OpenAI diese leakt."""
        if not text:
            return ""
        # Versuche, reine JSON-Strings zu parsen und nur den Inhalt zu nehmen
        try:
            if text.strip().startswith("{") and text.strip().endswith("}"):
                data = json.loads(text)
                # Wenn es ein Dict ist, suchen wir nach 'text' oder 'snippet' Feldern
                if isinstance(data, dict):
                    return data.get("text") or data.get("snippet") or str(data)
        except:
            pass
        return text

    def _strip_citation_tags(self, text: str) -> str:
        """Entfernt OpenAI-Zitattags 【id†title】 und Markdown-Links aus dem Text.
        
        Der UnifiedWebSearchRenderer ist die einzige Autorität für Links.
        """
        text = self._clean_raw_text(text)
        if not text:
            return "Zusammenfassung der Suchergebnisse:"
        # Entferne OpenAI citation tags: 【...】
        text = re.sub(r"【.*?】", "", text)
        # Entferne inline Markdown-Links: [title](url) → title
        text = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", text)
        # Entferne nackte URLs
        text = re.sub(r"https?://\S+", "", text)
        # Bereinige doppelte Leerzeichen
        text = re.sub(r"  +", " ", text).strip()
        return text

    async def search(self, api_key: str, query: str, model: Optional[str] = None) -> WebSearchResult:
        normalized_query = str(query or "").strip()
        biased_query = enforce_german_market_bias(
            augment_query_with_local_bias(normalized_query)
        )
        if biased_query != normalized_query:
            logger.info(
                "OPENAI-WEBSEARCH: Applied localization bias to query -> %s",
                biased_query,
            )
        else:
            logger.info("Using OpenAI's native web search capability for query: %s", biased_query)

        query = biased_query
        openai_client = AsyncOpenAI(api_key=api_key)

        raw_model = getattr(model, "id", None)
        if not raw_model:
            raw_model = str(model or "").strip()
        model_name = raw_model or "gpt-5.4-nano"
        if model_name.lower() == "none":
            model_name = "gpt-5.4-nano"

        fallback_model = "gpt-5.4-nano"

        async def _execute_with_model(model_to_use: str):
            logger.info(
                "OPENAI-WEBSEARCH: calling model '%s' for query '%s' with Diamond Standard",
                model_to_use,
                query,
            )
            system_prompt = _build_diamond_search_system_prompt(model_to_use)
            # Wir übergeben den Diamond-Standard als System-Instruktion im input-Array
            diamond_input = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            return await openai_client.responses.create(
                model=model_to_use,
                tools=[{"type": "web_search"}],
                input=diamond_input,
                include=["web_search_call.action.sources"],
            )

        try:
            response = await _execute_with_model(model_name)
        except BadRequestError as exc:
            error_message = str(exc).lower()
            if exc.status_code == 400 and "web_search" in error_message and model_name.lower() != fallback_model:
                logger.warning(
                    "OPENAI-WEBSEARCH: Modell %s unterstützt web_search nicht, weiche auf %s aus.",
                    model_name,
                    fallback_model,
                )
                response = await _execute_with_model(fallback_model)
                model_name = fallback_model
            else:
                logger.error("Error during OpenAI web search: %s", exc, exc_info=True)
                sentry_sdk.capture_exception(exc)
                raise RuntimeError("OpenAI native web search failed") from exc
        except Exception as exc:
            logger.error("Error during OpenAI web search: %s", exc, exc_info=True)
            sentry_sdk.capture_exception(exc)
            raise RuntimeError("OpenAI native web search failed") from exc

        # --- Daten aus response.output extrahieren ---
        # Die Responses-API liefert output als Liste von Items:
        #   - type="web_search_call" → action.sources (URL-Liste der konsultierten Quellen)
        #   - type="message" → content[].annotations (url_citation mit url+title)
        sources_dicts: list[dict] = []
        annotations: list[dict] = []
        try:
            for item in (response.output or []):
                # 1. web_search_call → action.sources
                if getattr(item, "type", "") == "web_search_call":
                    action = getattr(item, "action", None)
                    if action and hasattr(action, "sources") and action.sources:
                        for src in action.sources:
                            if hasattr(src, "model_dump"):
                                sources_dicts.append(src.model_dump())
                            elif isinstance(src, dict):
                                sources_dicts.append(src)
                # 2. message → content[].annotations (url_citation)
                if getattr(item, "type", "") == "message":
                    for content_block in (getattr(item, "content", None) or []):
                        for ann in (getattr(content_block, "annotations", None) or []):
                            ann_type = getattr(ann, "type", "")
                            if ann_type == "url_citation":
                                url = getattr(ann, "url", "") or ""
                                title = getattr(ann, "title", "") or ""
                                if url:
                                    annotations.append({"url": url, "title": title})
        except Exception as extraction_error:
            logger.warning("Could not extract sources/annotations: %s", extraction_error)

        # URL-Liste: annotations haben die relevantesten Links mit Titel
        all_source_urls = []
        seen_urls = set()
        for ann in annotations:
            url = ann.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_source_urls.append(ann)
        for src in sources_dicts:
            url = src.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_source_urls.append(src)

        all_source_urls = all_source_urls[:_MAX_RETURNED_SOURCES]
        urls = [s["url"] for s in all_source_urls if s.get("url")]

        raw_text = response.output_text if response.output_text else ""

        if (not raw_text or len(raw_text) < 50) and all_source_urls:
            logger.info("OpenAI text empty/short. Building from snippets.")
            raw_text = f"Hier sind Informationen zu '{query}':\n\n"
            for src in all_source_urls[:4]:
                title = src.get("title", "Info")
                snippet = src.get("text", "")
                if snippet:
                    raw_text += f"- **{title}**: {snippet}\n"

        if not raw_text:
            raw_text = "Keine relevanten Text-Ergebnisse."

        # 💎 DIAMOND: No-Citation-Mode — strip all links/citations from text
        # UnifiedWebSearchRenderer is the sole authority for link display
        text_output = self._strip_citation_tags(raw_text)

        logger.info(
            "OPENAI-WEBSEARCH: result text_len=%s sources=%s annotations=%s",
            len(text_output), len(all_source_urls), len(annotations),
        )

        usage, cost = calculate_cost("websearch", usage_data={"query_count": 1})

        # 💎 DIAMOND: Normalize to WebSearchResult contract
        sources: list[WebSearchSource] = []
        for src in all_source_urls:
            src_url = str(src.get("url") or "").strip()
            src_title = str(src.get("title") or src.get("name") or "").strip()
            # Fallback: Domain-Name statt generisches "Quelle"
            if not src_title or src_title == "Quelle":
                try:
                    src_title = urlparse(src_url).netloc.replace("www.", "") or "Quelle"
                except Exception:
                    src_title = "Quelle"
            source: WebSearchSource = {
                "url": src_url,
                "title": src_title,
            }
            snippet = str(src.get("text") or src.get("snippet") or "").strip()
            if snippet:
                source["snippet"] = snippet[:220]
            sources.append(source)

        metadata: WebSearchMetadata = {
            "provider": "openai",
            "model": model_name,
            "usage": usage,
            "cost": cost,
        }

        result: WebSearchResult = {
            "text": text_output,
            "sources": sources,
            "metadata": metadata,
        }

        return result
