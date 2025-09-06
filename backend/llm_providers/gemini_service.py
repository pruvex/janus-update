import logging
import uuid
import re
from typing import List, Dict, Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost, MODEL_PRICES
from backend import image_manager

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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_gemini_api(api_key: str, model_id: str, chat_history: List[Dict], model_info: Dict):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    
    gemini_history = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({'role': role, 'parts': [msg['content']]})
        
    try:
        response = await model.generate_content_async(gemini_history)
        text_response = response.text
        
        input_tokens = (await model.count_tokens(gemini_history)).total_tokens
        output_tokens = (await model.count_tokens(text_response)).total_tokens
        
        usage, cost = _calculate_and_log_cost(model_id, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})
        
        return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}
            
    except ResourceExhausted as e:
        logger.warning(f"Gemini API quota exceeded: {e.message}")
        # Don't retry on quota exceeded, just return the error
        return {"type": "text", "text": f"Fehler: Das Anfragelimit für die Gemini API wurde überschritten. Bitte versuchen Sie es in einer Minute erneut. (Fehler: 429)", "image_url": None, "usage": {}, "cost": {}}
    except Exception as e:
        logger.warning(f"An error occurred with Gemini API, retrying... Error: {e}")
        raise

def _extract_image_description(prompt: str) -> str:
    # Normalize prompt to lowercase and replace spaces with hyphens for consistent matching
    normalized_prompt = prompt.lower().replace(' ', '-')

    # Remove common image generation prefixes and model prefixes
    prefixes = [
        "gemini:",
        "gpt:",
        "mache-ein-bild-von",
        "erstelle-ein-bild-von",
        "generiere-ein-bild-von",
        "make-an-image-of",
        "generate-an-image-of",
        "create-an-image-of",
        "zeig-mir-bild-von",
        "zeig-mir-ein-bild-von",
        "zeige-mir-bild-von",
        "zeige-mir-ein-bild-von"
    ]
    
    cleaned_prompt = normalized_prompt
    for prefix in prefixes:
        if cleaned_prompt.startswith(prefix):
            cleaned_prompt = cleaned_prompt[len(prefix):].strip('-') # Strip leading hyphens after removing prefix

    # Further clean up by removing common redundant phrases that might remain
    redundant_phrases = [
        "eines", 
        "einer",
        "ein",
        "eine",
        "einem",
        "bild",
        "foto",
        "image",
        "picture",
        "zeig-mir",
        "zeige-mir",
        "erstelle",
        "generiere",
        "mache",
        "mach",
        "draw",
        "create",
        "generate",
        "a",
        "an",
        "the",
        "of"
    ]
    for phrase in redundant_phrases:
        # Use regex to replace whole words only, to avoid partial matches
        cleaned_prompt = re.sub(r'\b' + re.escape(phrase) + r'\b', '', cleaned_prompt).strip('-')

    # German grammatical normalization (heuristic) - more targeted replacements
    cleaned_prompt = re.sub(r'\b(roten|blauen|gelben|grünen|weissen)-hauses\b', r'\1-haus', cleaned_prompt)
    cleaned_prompt = re.sub(r'\b(roten|blauen|gelben|grünen)-autos\b', r'\1-auto', cleaned_prompt)
    cleaned_prompt = re.sub(r'\b(roten|blauen|gelben|grünen)-hunde\b', r'\1-hund', cleaned_prompt)
    cleaned_prompt = re.sub(r'\b(roten|blauen|gelben|grünen)-katzen\b', r'\1-katze', cleaned_prompt)
    
    # Specific adjective ending corrections (e.g., "roten" -> "rotes")
    cleaned_prompt = cleaned_prompt.replace("roten-", "rotes-")
    cleaned_prompt = cleaned_prompt.replace("blauen-", "blaues-")
    cleaned_prompt = cleaned_prompt.replace("gelben-", "gelbes-")
    cleaned_prompt = cleaned_prompt.replace("grünen-", "grünes-")
    cleaned_prompt = cleaned_prompt.replace("weissen-", "weisses-")

    # Remove any remaining non-alphanumeric or non-hyphen characters
    cleaned_prompt = re.sub(r'[^a-zA-Z0-9-]', '', cleaned_prompt)

    # Replace multiple hyphens with a single hyphen and strip leading/trailing hyphens
    cleaned_prompt = re.sub(r'-+', '-', cleaned_prompt).strip('-')

    return cleaned_prompt

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_gemini_image_generation_api(api_key: str, model_id: str, prompt: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    try:
        logger.info(f"_call_gemini_image_generation_api: Calling model '{model_id}' with prompt: '{prompt}'")
        response = await model.generate_content_async(prompt)
        
        image_data = None
        # Safely access nested attributes
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_data = part.inline_data.data
                    break

        image_url = None
        if image_data:
            cleaned_description = _extract_image_description(prompt)
            image_url = image_manager.save_image_from_bytes(image_data, description=cleaned_description, file_extension="png") 
            logger.info(f"_call_gemini_image_generation_api: Image saved via image_manager. URL: {image_url}")

        usage, cost = _calculate_and_log_cost(model_id)
        return {"text": "", "image_url": image_url, "usage": usage, "cost": cost}
    except Exception as e:
        logger.error(f"Error generating image with Gemini (attempt failed): {e}")
        raise
