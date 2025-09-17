
import logging
import base64
from typing import List, Dict
import google.generativeai as genai

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

class GeminiMultiModal:
    """
    Encapsulates the multi-modal (image + text) generation functionality for the Gemini provider.
    """
    async def generate_with_image(self, model: str, messages: List[Dict], image_data: str) -> Dict:
        logger.info("Image data detected for Gemini. Processing as a multi-modal request.")
        try:
            # 1. Parse the Data URI
            header, encoded = image_data.split(",", 1)
            mime_type = header.split(":")[1].split(";")[0]
            
            # 2. Decode Base64
            image_bytes = base64.b64decode(encoded)

            # 3. Extract text prompt from the last message
            prompt_text = ""
            if messages:
                last_message_content = messages[-1].get("content")
                if isinstance(last_message_content, list):
                    for part in last_message_content:
                        if part.get("type") == "text":
                            prompt_text = part.get("text", "")
                            break
                elif isinstance(last_message_content, str):
                    prompt_text = last_message_content

            # 4. Construct Gemini's content list
            gemini_content = [
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
            return {"type": "text", "text": f"Fehler bei der Bildverarbeitung mit Gemini: {e}", "image_url": None, "usage": {}, "cost": {}}
