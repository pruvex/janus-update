# backend/services/websearch/gemini_provider.py
import logging
import json
import asyncio
import urllib.request
import urllib.error
from urllib.parse import urlparse
from typing import Dict, Any

from .base_provider import BaseWebSearchProvider
from backend.services.cost_calculator import calculate_cost

logger = logging.getLogger("janus_backend")

class GeminiWebSearchProvider(BaseWebSearchProvider):
    async def search(self, api_key: str, query: str, model: str) -> Dict[str, Any]:
        """
        Führt eine Google-Suche via Gemini API durch (Direct REST).
        Nutzt 'groundingSupports' für Inline-Links.
        FALLBACK: Wenn keine Inline-Links möglich sind, werden sie unten angehängt.
        """
        logger.info(f"Using Gemini's native web search (Smart-Linking + Fallback) for query: {query} with model: {model}")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": query}]
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
            final_text = ""
            urls = set()
            search_queries_count = 0
            links_injected_count = 0
            
            if "candidates" in result and result["candidates"]:
                candidate = result["candidates"][0]
                
                # 1. Rohtext extrahieren
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            text_output += part["text"]
                
                # 2. Metadaten verarbeiten
                grounding_chunks = []
                grounding_supports = []
                
                if "groundingMetadata" in candidate:
                    meta = candidate["groundingMetadata"]
                    if "groundingChunks" in meta:
                        grounding_chunks = meta["groundingChunks"]
                        for chunk in grounding_chunks:
                            if "web" in chunk and "uri" in chunk["web"]:
                                urls.add(chunk["web"]["uri"])
                    if "groundingSupports" in meta:
                        grounding_supports = meta["groundingSupports"]
                    if "webSearchQueries" in meta:
                        search_queries_count = len(meta["webSearchQueries"])

                # 3. Intelligente Link-Injektion (Smart Linking)
                current_text = text_output
                
                if text_output and grounding_supports and grounding_chunks:
                    # Rückwärts sortieren, damit Indizes stabil bleiben
                    sorted_supports = sorted(
                        grounding_supports, 
                        key=lambda x: x.get('segment', {}).get('endIndex', 0), 
                        reverse=True
                    )
                    
                    for support in sorted_supports:
                        try:
                            end_idx = support.get('segment', {}).get('endIndex')
                            chunk_indices = support.get('groundingChunkIndices', [])
                            
                            if end_idx is not None and chunk_indices:
                                links_str = ""
                                for idx in chunk_indices:
                                    if idx < len(grounding_chunks):
                                        chunk = grounding_chunks[idx]
                                        if "web" in chunk and "uri" in chunk["web"]:
                                            uri = chunk["web"]["uri"]
                                            try:
                                                domain = urlparse(uri).netloc.replace("www.", "")
                                                display = domain if domain else "Quelle"
                                            except:
                                                display = "Quelle"
                                            links_str += f" ([{display}]({uri}))"
                                
                                if links_str and end_idx <= len(current_text):
                                    current_text = current_text[:end_idx] + links_str + current_text[end_idx:]
                                    links_injected_count += 1
                        except Exception as e:
                            logger.warning(f"Injection failed for a segment: {e}")
                            continue
                
                final_text = current_text

                # 4. FALLBACK: Wenn KEINE Links in den Text gewoben wurden, hängen wir sie unten an.
                # Das passiert oft bei kurzen Antworten, wo Google keine Supports liefert.
                if links_injected_count == 0 and urls:
                    final_text += "\n\n**Gefundene Quellen:**\n"
                    for url in sorted(list(urls)):
                        try:
                            domain = urlparse(url).netloc.replace("www.", "")
                        except:
                            domain = url
                        final_text += f"- [{domain}]({url})\n"

            # Kosten berechnen
            if search_queries_count > 0:
                logger.info(f"Gemini executed {search_queries_count} queries. Injected {links_injected_count} inline citations.")
                usage, cost = calculate_cost("websearch_gemini", usage_data={"query_count": search_queries_count})
            else:
                usage, cost = {}, {}

            return {"text": final_text, "urls": list(urls), "usage": usage, "cost": cost}

        except Exception as e:
            logger.error(f"Error during Gemini Direct web search: {e}", exc_info=True)
            return {"text": f"Verbindungsfehler bei der Websuche: {e}", "urls": [], "usage": {}, "cost": {}}