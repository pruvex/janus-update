import logging
import re
import copy
import json
import httpx
import asyncio
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost
from backend import image_manager
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.utils import _extract_image_description

logger = logging.getLogger('janus_backend')

def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    logger.info(f"\n--- USAGE TRACKING ---\n" 
                f"Model: {model_id}\n" 
                f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n" 
                f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n" 
                f"Image Quality: {usage.get('image_quality', 'N/A')}\n" 
                f"Image Size: {usage.get('image_size', 'N/A')}\n" 
                f"Total Cost: {cost.get('total_cost', 0):.8f} €\n" 
                f"----------------------")
    return usage, cost



async def _resolve_redirect(client: httpx.AsyncClient, url: str) -> str:
    """Folgt einer Redirect-URL und gibt die finale, saubere URL zurück."""
    try:
        response = await client.head(url, follow_redirects=True, timeout=10)
        return str(response.url)
    except Exception as e:
        logger.warning(f"Could not resolve redirect for {url}: {e}")
        return url

async def _format_response_with_citations(response_json: Dict) -> str:
    """
    Verarbeitet die JSON-Antwort, um den Text mit sauberen, gruppierten Inline-Nummern zu versehen
    und eine separate, geordnete Quellenliste am Ende anzufügen.
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

class GeminiServiceProvider(BaseLLMProvider):

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, api_key: str, model: str, messages: List[Dict], tools: Optional[List[Dict]] = None, image_data: Optional[str] = None, **kwargs) -> Dict:
        genai.configure(api_key=api_key)

        # --- START: Handle Image Data ---
        if image_data:
            logger.info("Image data detected for Gemini. Processing as a multi-modal request.")
            try:
                # 1. Parse the Data URI
                header, encoded = image_data.split(",", 1)
                mime_type = header.split(":")[1].split(";")[0]
                
                # 2. Decode Base64
                import base64
                image_bytes = base64.b64decode(encoded)

                # 3. Extract text prompt from the last message
                prompt_text = ""
                if messages:
                    # The last message content might be a list if it was prepared for another provider (like OpenAI)
                    last_message_content = messages[-1].get("content")
                    if isinstance(last_message_content, list):
                        for part in last_message_content:
                            if part.get("type") == "text":
                                prompt_text = part.get("text", "")
                                break
                    elif isinstance(last_message_content, str):
                        prompt_text = last_message_content

                # 4. Construct Gemini's content list
                # As per docs: for single image, put text after the image
                gemini_content = [
                    # The SDK can handle a dict with mime_type and data directly
                    {'mime_type': mime_type, 'data': image_bytes},
                    {'text': prompt_text}
                ]

                # 5. Call the API
                genai_model = genai.GenerativeModel(model_name=model)
                input_tokens = (await genai_model.count_tokens_async(gemini_content)).total_tokens
                response = await genai_model.generate_content_async(gemini_content)
                text_response = response.text
                output_tokens = (await genai_model.count_tokens_async(text_response)).total_tokens
                
                usage, cost = _calculate_and_log_cost(model, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})
                return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}

            except Exception as e:
                logger.error(f"An unexpected error occurred with Gemini image processing: {e}", exc_info=True)
                # Return a user-friendly error message
                return {"type": "text", "text": f"Fehler bei der Bildverarbeitung mit Gemini: {e}", "image_url": None, "usage": {}, "cost": {}}
        # --- END: Handle Image Data ---

        # Existing logic for text-only messages
        is_websearch_active = False
        if tools:
            for tool in tools:
                if tool.get('function', {}).get('name') == 'perform_websearch':
                    is_websearch_active = True
                    break
        
        system_instruction = None
        gemini_history_for_api = []
        for msg in messages:
            if msg.get("role") == "system":
                system_instruction = msg.get("content")
                continue
            role = "user" if msg["role"] == "user" else "model"
            gemini_history_for_api.append({'role': role, 'parts': [{'text': msg.get('content', '')}]})
        
        if is_websearch_active:
            logger.info("Web search requested for Gemini. Using direct REST API call.")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": gemini_history_for_api,
                "tools": [{"google_search": {}}],
                "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None
            }
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                response_json = response.json()
                text_response = await _format_response_with_citations(response_json)
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
        
        logger.info("Standard Gemini request. Using Python SDK.")
        genai_model = genai.GenerativeModel(model_name=model, system_instruction=system_instruction)
        try:
            input_tokens = (await genai_model.count_tokens_async(gemini_history_for_api)).total_tokens
            response = await genai_model.generate_content_async(gemini_history_for_api)
            text_response = response.text
            output_tokens = (await genai_model.count_tokens_async(text_response)).total_tokens
            usage, cost = _calculate_and_log_cost(model, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})
            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}
        except Exception as e:
            logger.error(f"An unexpected error occurred with Gemini SDK: {e}", exc_info=True)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict:
        genai.configure(api_key=api_key)
        genai_model = genai.GenerativeModel(model)
        try:
            logger.info(f"Calling Gemini image model '{model}' with prompt: '{prompt}'")
            response = await genai_model.generate_content_async(prompt)
            image_data = None
            text_response = None
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_data = part.inline_data.data
                        break
                    if part.text:
                        text_response = part.text
            image_url = None
            if image_data:
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(image_data, description=cleaned_description, file_extension="png")
                text_response = None
            usage, cost = _calculate_and_log_cost(model)
            return {"text": text_response, "image_url": image_url, "usage": usage, "cost": cost}
        except Exception as e:
            logger.error(f"Error generating image with Gemini (attempt failed): {e}")
            raise