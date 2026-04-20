import asyncio
import json
import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger("janus_backend")


async def _resolve_redirect(client: httpx.AsyncClient, url: str) -> str:
    """Folgt einem Redirect und gibt die finale URL zurück."""
    try:
        response = await client.head(url, follow_redirects=True, timeout=10)
        return str(response.url)
    except Exception as e:
        logger.warning(f"Konnte Redirect für {url} nicht auflösen: {e}")
        return url


async def _extract_clean_sources(response_json: Dict) -> List[Dict[str, str]]:
    """Extrahiert und bereinigt die Quell-URLs aus den Metadaten."""
    try:
        metadata = response_json["candidates"][0].get("groundingMetadata", {})
        chunks = metadata.get("groundingChunks", [])

        redirect_uris = {
            chunk["web"]["uri"]
            for chunk in chunks
            if chunk.get("web") and chunk["web"].get("uri", "").startswith("https://vertexaisearch.cloud.google.com/")
        }

        resolved_urls = {}
        if redirect_uris:
            async with httpx.AsyncClient() as client:
                tasks = [_resolve_redirect(client, uri) for uri in redirect_uris]
                results = await asyncio.gather(*tasks)
                resolved_urls = dict(zip(redirect_uris, results))

        clean_sources = []
        for chunk in chunks:
            if not chunk.get("web"):
                continue
            original_uri = chunk["web"].get("uri")
            final_uri = resolved_urls.get(original_uri, original_uri)
            if final_uri:
                clean_sources.append({
                    "uri": final_uri,
                    "title": chunk["web"].get("title", ""),
                })
        return clean_sources
    except (KeyError, IndexError):
        return []


class GeminiWebSearch:
    async def search_and_generate(
        self, api_key: str, model: str, history: List[Dict], system_instruction: str
    ) -> Dict:
        logger.info("Web search angefordert für Gemini. Nutze direkten REST API Call.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        last_user_message_content = ""
        for msg in reversed(history):
            if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                last_user_message_content = msg["content"]
                break

        if not last_user_message_content:
            return {"type": "error", "text": "Keine Benutzeranfrage gefunden."}

        enhanced_query = f"{last_user_message_content} (Seiten auf Deutsch, Fokus Deutschland/Österreich/Schweiz)"

        final_system_instruction = str(system_instruction or "").strip()

        # --- START DIAMOND DEEP-RESEARCH FIX ---
        lang_rule = (
            "CRITICAL RESEARCH DIRECTIVE:\n"
            "1. You are an expert researcher for users in Germany. Prioritize German sources (.de, .at).\n"
            "2. If the user asks for a LIST of items (like games, movies, products, or newspapers), DO NOT be lazy! DO NOT just return the link of a generic overview listicle.\n"
            "3. You MUST perform a MULTI-STEP SEARCH:\n"
            "   - Step 1: Find the list of items.\n"
            "   - Step 2: For EVERY SINGLE ITEM you found, you MUST execute a NEW, specific search query (e.g. 'The Rogue Prince of Persia offizielle website deutsch').\n"
            "4. You MUST gather the specific deep-link URL for every single entity before returning your final search result."
        )
        # --- ENDE DIAMOND DEEP-RESEARCH FIX ---

        if "CRITICAL RESEARCH DIRECTIVE" not in final_system_instruction:
            final_system_instruction = f"{lang_rule}\n\n{final_system_instruction}".strip()

        payload = {
            "contents": [{"role": "user", "parts": [{"text": enhanced_query}]}],
            "tools": [{"google_search": {}}],
            "systemInstruction": {"parts": [{"text": final_system_instruction}]}
            if final_system_instruction
            else None,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            response_json = response.json()

            text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
            clean_sources = await _extract_clean_sources(response_json)

            final_content: Dict[str, Any] = {
                "status": "ok",
                "data": {
                    "text": text_response,
                    "sources": clean_sources,
                },
            }

            return {
                "type": "tool_code",
                "content": json.dumps(final_content, ensure_ascii=False),
            }

        except Exception as e:
            logger.error(f"Fehler bei direktem Gemini API Call: {e}", exc_info=True)
            return {"type": "error", "text": f"Fehler bei der Gemini-Websuche: {str(e)}"}
