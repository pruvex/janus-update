import logging
import uuid
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
            file_name = f"{uuid.uuid4()}.png"
            image_url = image_manager.save_image_from_bytes(image_data, file_name) 
            logger.info(f"_call_gemini_image_generation_api: Image saved via image_manager. URL: {image_url}")

        usage, cost = _calculate_and_log_cost(model_id)
        return {"text": "", "image_url": image_url, "usage": usage, "cost": cost}
    except Exception as e:
        logger.error(f"Error generating image with Gemini (attempt failed): {e}")
        raise
