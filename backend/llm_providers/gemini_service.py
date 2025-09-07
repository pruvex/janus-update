import logging
import re
from typing import List, Dict, Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost
from backend import image_manager
from backend.llm_providers.base_provider import BaseLLMProvider

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

def _extract_image_description(prompt: str) -> str:
    # Simplified and robust normalization
    cleaned_prompt = prompt.lower()
    prefixes = [
        "gemini:", "gpt:", "mache ein bild von", "erstelle ein bild von",
        "generiere ein bild von", "make an image of", "generate an image of",
        "create an image of", "zeig mir bild von", "zeig mir ein bild von",
        "zeige mir bild von", "zeige mir ein bild von", "zeichne", "mache", "erstelle"
    ]
    for prefix in prefixes:
        if cleaned_prompt.startswith(prefix):
            cleaned_prompt = cleaned_prompt[len(prefix):].strip()

    # Replace spaces and special characters with hyphens
    cleaned_prompt = cleaned_prompt.replace(' ', '-')
    cleaned_prompt = re.sub(r'[^a-z0-9-]', '', cleaned_prompt)

    # Clean up multiple and leading/trailing hyphens
    cleaned_prompt = re.sub(r'-+', '-', cleaned_prompt).strip('-')
    return cleaned_prompt

class GeminiServiceProvider(BaseLLMProvider):

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, api_key: str, model: str, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict:
        genai.configure(api_key=api_key)
        genai_model = genai.GenerativeModel(model)

        gemini_history = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({'role': role, 'parts': [msg['content']]})

        try:
            response = await genai_model.generate_content_async(gemini_history)
            text_response = response.text

            input_tokens = (await genai_model.count_tokens(gemini_history)).total_tokens
            output_tokens = (await genai_model.count_tokens(text_response)).total_tokens

            usage, cost = _calculate_and_log_cost(model, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})

            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}

        except ResourceExhausted as e:
            logger.warning(f"Gemini API quota exceeded: {e.message}")
            return {"type": "text", "text": f"Fehler: Das Anfragelimit für die Gemini API wurde überschritten. (Fehler: 429)", "image_url": None, "usage": {}, "cost": {}}
        except Exception as e:
            logger.warning(f"An error occurred with Gemini API, retrying... Error: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict:
        genai.configure(api_key=api_key)
        genai_model = genai.GenerativeModel(model)
        try:
            logger.info(f"Calling Gemini image model '{model}' with prompt: '{prompt}'")
            response = await genai_model.generate_content_async(prompt)

            image_data = None
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_data = part.inline_data.data
                        break

            image_url = None
            if image_data:
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(image_data, description=cleaned_description, file_extension="png")
                logger.info(f"Image saved via image_manager. URL: {image_url}")

            usage, cost = _calculate_and_log_cost(model)
            return {"text": "", "image_url": image_url, "usage": usage, "cost": cost}
        except Exception as e:
            logger.error(f"Error generating image with Gemini (attempt failed): {e}")
            raise
