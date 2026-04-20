# backend/services/websearch/gemini_provider.py
import logging
import json
import asyncio
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


from .base_provider import BaseWebSearchProvider, WebSearchResult, WebSearchSource, WebSearchMetadata
from backend.services.cost_calculator import calculate_cost

logger = logging.getLogger("janus_backend")


def _dedupe_gemini_sources(raw_sources: list[dict[str, str]], max_items: int = 10) -> list[dict[str, str]]:
    """Deduplicate and limit sources."""
    deduped: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for source in raw_sources or []:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or source.get("uri") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        item: dict[str, str] = {"url": url, "uri": url}
        title = str(source.get("title") or "").strip()
        snippet = str(source.get("snippet") or source.get("text") or "").strip()
        if title:
            item["title"] = title[:160]
        if snippet:
            item["snippet"] = snippet[:320]
        deduped.append(item)
        if len(deduped) >= max_items:
            break
    return deduped


def _extract_clean_sources_from_metadata(grounding_metadata: Dict[str, Any]) -> list[dict[str, str]]:
    """
    💎 Diamond + BRUTE-FORCE FALLBACK: Extract sources from groundingMetadata.
    
    1. Versuche strukturierte Chunks zu extrahieren
    2. FALLBACK: Wenn Chunks leer, extrahiere aus rohen Such-Snippets
    """
    if not isinstance(grounding_metadata, dict):
        return []
    
    chunks = grounding_metadata.get("groundingChunks", []) if isinstance(grounding_metadata.get("groundingChunks"), list) else []
    supports = grounding_metadata.get("groundingSupports", []) if isinstance(grounding_metadata.get("groundingSupports"), list) else []
    
    # Build support text index by chunk
    support_texts_by_chunk_index: dict[int, list[str]] = {}
    for support in supports:
        if not isinstance(support, dict):
            continue
        segment = support.get("segment") if isinstance(support.get("segment"), dict) else {}
        segment_text = str(segment.get("text") or "").strip()
        if not segment_text:
            continue
        for idx in support.get("groundingChunkIndices", []) or []:
            if not isinstance(idx, int):
                continue
            support_texts_by_chunk_index.setdefault(idx, []).append(segment_text)
    
    clean_sources: list[dict[str, str]] = []
    for idx, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            continue
        web = chunk.get("web") if isinstance(chunk.get("web"), dict) else {}
        uri = str(web.get("uri") or "").strip()
        if not uri:
            continue
            
        item: dict[str, str] = {"url": uri, "uri": uri}
        title = str(web.get("title") or "").strip()
        if title:
            item["title"] = title
        snippet = " ".join(support_texts_by_chunk_index.get(idx, [])[:3]).strip()
        if snippet:
            item["snippet"] = snippet[:320]
        clean_sources.append(item)
    
    # --- BRUTE-FORCE FALLBACK: Wenn keine strukturierten Chunks, nutze rohe Snippets ---
    if not clean_sources:
        logger.warning("BRUTE-FORCE FALLBACK: Keine strukturierten Chunks, extrahiere aus Such-Snippets")
        
        # Versuche aus searchEntryPoint oder renderedContent zu extrahieren
        search_entry = grounding_metadata.get("searchEntryPoint", {}) if isinstance(grounding_metadata.get("searchEntryPoint"), dict) else {}
        rendered_content = str(search_entry.get("renderedContent") or "").strip()
        
        # Extrahiere URLs aus dem Text
        url_pattern = r'https?://[^\s<>"\')\]]+[^\s<>"\')\].,;!?]'
        fallback_urls: set[str] = set()
        
        # Suche im gerenderten Content
        if rendered_content:
            for match in re.finditer(url_pattern, rendered_content):
                url = match.group().strip()
                if url.startswith(("http://", "https://")):
                    fallback_urls.add(url)
        
        # Suche auch in den Web-Suchanfragen (manchmal enthalten Snippets dort)
        web_queries = grounding_metadata.get("webSearchQueries", []) if isinstance(grounding_metadata.get("webSearchQueries"), list) else []
        
        if not fallback_urls and web_queries:
            # Letzter Fallback: Generische Google-Such-URLs für die Queries
            for query in web_queries[:3]:  # Max 3 Queries
                if isinstance(query, str) and query.strip():
                    search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query.strip())}"
                    fallback_urls.add(search_url)
        
        # Erstelle Sources aus gefundenen URLs
        for url in list(fallback_urls)[:10]:  # Max 10
            clean_sources.append({
                "url": url,
                "uri": url,
                "title": "Gefundene Quelle",
                "snippet": "Aus Such-Snippet extrahiert"
            })
            logger.info("BRUTE-FORCE FALLBACK: URL extrahiert: %s", url[:80])
    
    return _dedupe_gemini_sources(clean_sources, max_items=30)


# Backward-compatible alias
async def _extract_clean_sources(candidate: Dict[str, Any]) -> list[dict[str, str]]:
    """Async wrapper for backward compatibility."""
    metadata = candidate.get("groundingMetadata") if isinstance(candidate, dict) else {}
    return _extract_clean_sources_from_metadata(metadata if isinstance(metadata, dict) else {})


def _strip_source_appendix(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    patterns = (
        r"\n{2,}\*\*Gefundene Quellen:\*\*[\s\S]*$",
        r"\n{2,}\*\*Quellen:\*\*[\s\S]*$",
        r"\n{2,}Quellen:\s*[\s\S]*$",
        r"\n{2,}Sources:\s*[\s\S]*$",
    )
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).rstrip()
    return cleaned


def _build_gemini_native_websearch_prompt(query: str) -> str:
    cleaned_query = str(query or "").strip()
    lowered = cleaned_query.lower()
    is_game_release_query = any(token in lowered for token in ("switch", "nintendo", "spiele", "games", "release", "erscheinen", "launch"))
    asks_price = any(token in lowered for token in ("preis", "preise", "uvp", "straßenpreis", "strassenpreis", "street price", "in euro"))
    asks_ranking = any(token in lowered for token in ("top 3", "top3", "ranking", "beliebteste", "beliebtesten", "highlights", "popular"))
    asks_launch = any(token in lowered for token in ("launch", "veröffentlicht", "veroeffentlicht", "release date", "wann wurde"))
    prompt_parts = [
        "Führe eine gründliche Google-Recherche durch.",
        "Antworte maximal prägnant in 1-2 Sätzen. Keine Einleitung ('Laut meiner Suche...'), sondern direkt die Fakten. Beispiel: 'Die Feinunze Gold kostet aktuell 3.890 Euro (Stand: 25.03.2026).'",
        "Nutze bevorzugt offizielle Seiten, große Fachmedien und verlässliche Handels-/Preisquellen.",
        "Antworte auf Deutsch und liefere ausschließlich Recherchematerial, keine finale Nutzerantwort.",
        "Schreibe KEINE Markdown-Links, KEINE Inline-Zitate und KEIN separates Quellenverzeichnis in den Text.",
        "Der Text dient nur als Rohmaterial für eine nachgelagerte Synthetisierung im Backend.",
        f"Nutzerfrage: {cleaned_query}",
    ]
    if is_game_release_query:
        prompt_parts.extend(
            [
                "Prüfe strikt die Zielplattform und das Zielgebiet; mische keine anderen Konsolen oder falschen Regionen/Jahre hinein.",
                "Ermittle möglichst vollständig alle relevanten Titel, Release-Termine/Fenster, Plattformangaben und zugehörigen Quellen.",
                "Strukturiere das Recherchematerial mit klaren Abschnitten für Launch, Preise/UVP, Highlights/Top 3 und verifizierte Release-Liste, sofern diese Aspekte angefragt sind.",
            ]
        )
    if asks_price or asks_ranking or asks_launch:
        prompt_parts.append("Behandle kombinierte Teilfragen separat und recherchiere jede Facette explizit.")
    if asks_price:
        prompt_parts.append(
            "PREIS-INTEGRITÄT (ABSOLUTES GEBOT): "
            "Nenne einen Preis NUR dann, wenn du ihn WORTWÖRTLICH in einem Such-Snippet findest. "
            "Schätze, runde oder interpoliere KEINE Preise. "
            "Wenn kein Preis im Snippet steht, schreibe exakt: 'Preis nur via Link verfügbar'."
        )
    if asks_ranking:
        prompt_parts.append("Nenne nur die Top 3 Titel, keine Beschreibungen.")
    if asks_launch:
        prompt_parts.append("Gib nur das deutsche/europäische Release-Datum an.")
    prompt_parts.append("Wenn Informationen fehlen oder widersprüchlich sind, mache die Unsicherheit sichtbar statt zu raten.")
    prompt_parts.append(
        "GROUNDING-PFLICHT: Wenn Suchergebnisse vorliegen, darfst du NIEMALS schreiben "
        "'Keine spezifische Quelle gefunden' oder aehnliches. "
        "Halluziniere NIEMALS Preise, Produktgenerationen (z.B. M5, M4, Pro Max) oder "
        "Spezifikationen, die nicht WOERTLICH in den Suchergebnissen stehen. "
        "Markiere jede Preisangabe mit dem Hinweis '(laut Suchergebnis)'."
    )
    return "\n".join(prompt_parts).strip()

class GeminiWebSearchProvider(BaseWebSearchProvider):
    async def search(self, api_key: str, query: str, model: Optional[str] = None) -> WebSearchResult:
        """
        Führt eine native Google-Suche via Gemini API durch (Direct REST).
        Nutzt ausschließlich das native `google_search`-Tool für Grounding.
        """
        logger.info(f"Using Gemini's native web search for query: {query} with model: {model}")

        raw_model = getattr(model, "id", None) or str(model or "").strip()
        model_name = raw_model or "gemini-2.5-flash"

        # --- NEU: Narrensicherer Fallback ---
        if not model_name.lower().startswith("gemini"):
            logger.warning(f"Falsches Modell für Gemini Provider übergeben ({model_name}). Fallback auf gemini-3-flash-preview.")
            model_name = "gemini-3-flash-preview"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        search_prompt = _build_gemini_native_websearch_prompt(query)
        
        payload = {
            "contents": [{
                "parts": [{"text": search_prompt}]
            }],
            "tools": [{
                "google_search": {} 
            }]
        }

        def _make_request():
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={'Content-Type': 'application/json'}, 
                method='POST'
            )
            try:
                with urllib.request.urlopen(req) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP Status {response.status}")
                    return json.load(response)
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else str(e)
                raise Exception(f"HTTP {e.code}: {error_body}")

        try:
            result = await asyncio.to_thread(_make_request)

            text_output = ""
            search_queries_count = 0
            
            if "candidates" in result and result["candidates"]:
                candidate = result["candidates"][0]
                
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            text_output += part["text"]

                if "groundingMetadata" in candidate:
                    meta = candidate["groundingMetadata"]
                    if "webSearchQueries" in meta:
                        search_queries_count = len(meta["webSearchQueries"])

                clean_sources = await _extract_clean_sources(candidate)
                urls = [str(source.get("url") or "").strip() for source in clean_sources if str(source.get("url") or "").strip()]
                final_text = _strip_source_appendix(text_output)
            else:
                clean_sources = []
                urls = []
                final_text = ""

            if search_queries_count > 0:
                logger.info("Gemini executed %s queries. Extracted %s clean sources.", search_queries_count, len(urls))
                usage, cost = calculate_cost("websearch_gemini", usage_data={"query_count": search_queries_count})
            else:
                usage, cost = {}, {}

            if search_queries_count <= 0:
                raise RuntimeError("Native Grounding failed")

            logger.info(
                "GEMINI-WEBSEARCH: result text_len=%s sources=%s queries=%s",
                len(final_text), len(clean_sources), search_queries_count,
            )

            # 💎 DIAMOND: Normalize to WebSearchResult contract
            sources: list[WebSearchSource] = []
            for src in clean_sources:
                source: WebSearchSource = {
                    "url": str(src.get("url") or "").strip(),
                    "title": str(src.get("title") or "Quelle").strip(),
                }
                if src.get("snippet"):
                    source["snippet"] = str(src["snippet"])[:320]
                sources.append(source)
            
            metadata: WebSearchMetadata = {
                "provider": "gemini",
                "model": model_name,
                "query_count": search_queries_count,
                "usage": usage,
                "cost": cost,
            }
            
            result: WebSearchResult = {
                "text": final_text,
                "sources": sources,
                "metadata": metadata,
            }
            
            return result

        except Exception as e:
            logger.error(f"Error during Gemini Direct web search: {e}", exc_info=True)
            raise RuntimeError("Native Grounding failed") from e