
import logging
import httpx
import json
import copy
import asyncio
from typing import Dict, List

from backend.cost_calculator import calculate_cost

logger = logging.getLogger('janus_backend')

def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Helper to calculate and log cost."""
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    logger.info(f"\n--- USAGE TRACKING ---\n" 
                f"Model: {model_id}\n" 
                f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n" 
                f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n" 
                f"Total Cost: {cost.get('total_cost', 0):.8f} €\n" 
                f"----------------------")
    return usage, cost

async def _resolve_redirect(client: httpx.AsyncClient, url: str) -> str:
    """Follows a redirect URL and returns the final, clean URL."""
    try:
        response = await client.head(url, follow_redirects=True, timeout=10)
        return str(response.url)
    except Exception as e:
        logger.warning(f"Could not resolve redirect for {url}: {e}")
        return url

async def _format_response_with_citations(response_json: Dict) -> str:
    """
    Processes the JSON response to add clean, grouped inline numbers to the text
    and append a separate, ordered list of sources at the end.
    """
    try:
        candidate = response_json['candidates'][0]
        text = candidate['content']['parts'][0]['text']
        
        metadata = candidate.get('groundingMetadata')
        if not metadata or not metadata.get('groundingSupports'):
            return text

        supports = metadata['groundingSupports']
        chunks = metadata.get('groundingChunks', [])
        
        redirect_uris_to_resolve = {
            chunk['web']['uri']
            for chunk in chunks
            if chunk.get('web') and chunk['web'].get('uri', '').startswith("https://vertexaisearch.cloud.google.com/")
        }

        resolved_urls_map = {}
        if redirect_uris_to_resolve:
            async with httpx.AsyncClient() as client:
                tasks = [_resolve_redirect(client, uri) for uri in redirect_uris_to_resolve]
                resolved_results = await asyncio.gather(*tasks)
                resolved_urls_map = dict(zip(redirect_uris_to_resolve, resolved_results))

        used_chunks = {}
        for support in supports:
            for index in support.get('groundingChunkIndices', []):
                if index not in used_chunks and index < len(chunks):
                    original_uri = chunks[index].get('web', {}).get('uri')
                    clean_uri = resolved_urls_map.get(original_uri, original_uri)
                    
                    chunk_copy = copy.deepcopy(chunks[index])
                    if 'web' in chunk_copy and 'uri' in chunk_copy['web']:
                        chunk_copy['web']['uri'] = clean_uri
                    used_chunks[index] = chunk_copy

        source_map = {old_index: new_index + 1 for new_index, old_index in enumerate(sorted(used_chunks.keys()))}
        citations_by_position = {}

        for support in supports:
            segment = support.get('segment', {})
            end_index = segment.get('endIndex')
            if end_index is None: continue
            
            insert_pos = end_index
            while insert_pos < len(text) and text[insert_pos].isalnum():
                insert_pos += 1

            if insert_pos not in citations_by_position:
                citations_by_position[insert_pos] = set()
            
            for index in support.get('groundingChunkIndices', []):
                if index in source_map:
                    citations_by_position[insert_pos].add(source_map[index])

        sorted_positions = sorted(citations_by_position.keys(), reverse=True)
        for position in sorted_positions:
            sorted_indices = sorted(list(citations_by_position[position]))
            citation_string = "".join([f"[{i}]" for i in sorted_indices])
            if position > 0 and text[position-1].isalnum():
                 citation_string = " " + citation_string
            text = text[:position] + citation_string + text[position:]

        if used_chunks:
            source_list_markdown = "\n\n---\n**Quellen:**\n"
            for old_index, new_index in sorted(source_map.items(), key=lambda item: item[1]):
                chunk = used_chunks[old_index]
                if chunk.get('web'):
                    uri = chunk['web'].get('uri', '#')
                    title = chunk['web'].get('title', uri)
                    source_list_markdown += f"{new_index}. [{title}]({uri})\n"
            text += source_list_markdown
        
        return text

    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Could not parse grounding metadata: {e}. Returning raw text.", exc_info=True)
        try:
            return response_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Fehler bei der Verarbeitung der Antwort."

class GeminiWebSearch:
    """
    Encapsulates the web search functionality for the Gemini provider.
    """
    async def search_and_generate(self, api_key: str, model: str, history: List[Dict], system_instruction: str) -> Dict:
        logger.info("Web search requested for Gemini. Using direct REST API call.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": history,
            "tools": [{"google_search": {}}],
            "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            response_json = response.json()
            text_response = await _format_response_with_citations(response_json)
            # Token calculation for web search is an approximation
            input_tokens = len(json.dumps(payload)) // 4 
            output_tokens = len(text_response) // 4
            usage, cost = _calculate_and_log_cost(model, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})
            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}
        except httpx.HTTPStatusError as e:
            error_body = e.response.json()
            logger.error(f"HTTP Error during direct Gemini API call: {error_body}", exc_info=True)
            error_message = error_body.get("error", {}).get("message", "Unbekannter API-Fehler")
            return {"type": "text", "text": f"Fehler bei der Gemini-Websuche: {error_message}", "image_url": None, "usage": {}, "cost": {}}
        except Exception as e:
            logger.error(f"An unexpected error occurred with direct Gemini API call: {e}", exc_info=True)
            raise
