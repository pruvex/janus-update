import base64
import logging
import httpx
import json
from typing import Dict, List, Optional

# Korrigierte Import-Pfade
from backend.services import image_manager
from backend.services.cost_calculator import calculate_cost
from backend.llm_providers.utils import _extract_image_description

logger = logging.getLogger("janus_backend")


def _calculate_and_log_cost(model_id, usage_data=None):
    """Helper to calculate and log cost for Gemini."""
    usage, cost = calculate_cost(model_id, usage_data)
    logger.info(
        f"\n--- USAGE TRACKING (Gemini) ---\n"
        f"Model: {model_id}\n"
        f"Specs: {usage.get('image_size', 'N/A')}\n"
        f"Cost: {cost.get('total_cost', 0):.6f} €\n"
        f"-------------------------------"
    )
    return usage, cost


class GeminiImageGeneration:
    """
    Handler for Gemini Image Generation via direct REST API.
    """

    async def generate_image(self, api_key: str, model: str, prompt: str, image_bytes_list: list = None, **kwargs) -> Dict:
        # Endpunkt-URL bauen
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # --- 1. Konfiguration ---
        generation_config = {"responseModalities": ["IMAGE"]}
        image_config = {}
        aspect_ratio = kwargs.get("aspect_ratio")
        image_size = kwargs.get("image_size")
        
        if aspect_ratio: image_config["aspectRatio"] = aspect_ratio
        if image_size: image_config["imageSize"] = image_size
        if image_config: generation_config["imageConfig"] = image_config
            
        logger.info(f"Gemini Image Config: {generation_config}")

        # --- 2. Tools (Google Search) ---
        tools_list = []
        if "gemini-3-pro-image" in model:
            tools_list.append({"google_search": {}})
            logger.info("Gemini Grounding: Offering Google Search tool.")
        
        # --- 3. Content (Prompt + Bilder) ---
        if image_bytes_list:
            if len(image_bytes_list) > 1:
                # MULTI-IMAGE (Combine) PROMPT
                logger.info(f"PROVIDER CHECK: Processing {len(image_bytes_list)} images for COMBINE.")
                final_prompt = (
                    f"INSTRUCTION: Combine the attached images based on the user's request. "
                    f"Identify the main subjects in each image (e.g., person, object, background) and merge them into a new, coherent scene.\n\n"
                    f"USER REQUEST: \"{prompt}\""
                )
            else:
                # SINGLE-IMAGE (Edit/Refine) PROMPT - GOLDSTANDARD
                logger.info("PROVIDER CHECK: Processing 1 image for EDIT/REFINE.")
                final_prompt = (
                    f"INSTRUCTION: Perform a precise edit on the attached image. "
                    f"Your primary goal is to preserve the main subject (e.g., the person, the animal, the object) with high fidelity, keeping their appearance completely unchanged. "
                    f"Then, apply ONLY the following modification:\n\n"
                    f"USER REQUEST: \"{prompt}\""
                )
            
            parts = [{"text": final_prompt}]
            for img_bytes in image_bytes_list:
                mime_type = "image/jpeg" if img_bytes.startswith(b'\xff\xd8') else "image/png"
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(img_bytes).decode('utf-8')
                    }
                })
        else:
            parts = [{"text": prompt}]
        
        contents = [{"parts": parts}]

        # --- 4. Payload für REST-API ---
        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }
        if tools_list:
            payload["tools"] = tools_list

        try:
            async with httpx.AsyncClient(timeout=180.0) as client: # Längeres Timeout für Bilder
                response = await client.post(url, json=payload)
                response.raise_for_status()
            
            response_json = response.json()
            
            # --- 5. Response-Verarbeitung ---
            first_part = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0]
            
            if "inlineData" in first_part:
                image_data = first_part["inlineData"]["data"]
                image_bytes_result = base64.b64decode(image_data)
                
                # Speichern
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(
                    image_bytes_result, description=cleaned_description, file_extension="png"
                )
                
                usage_data_for_cost = {"aspect_ratio": aspect_ratio, "image_size": image_size}
                usage, cost = _calculate_and_log_cost(model, usage_data=usage_data_for_cost)
                
                return {
                    "image_url": image_url,
                    "usage": usage,
                    "cost": cost,
                    "previous_response_id": response_json.get("candidates", [{}])[0].get("content", {}).get("response_id"),
                    "previous_image_id": response_json.get("candidates", [{}])[0].get("content", {}).get("image_id")
                }
            else:
                text_content = first_part.get("text", "Unbekannte Antwort von Gemini.")
                logger.warning(f"Gemini lieferte Text: {text_content}")
                return { 
                    "type": "text", 
                    "text": f"Gemini Hinweis: {text_content}", 
                    "image_url": None 
                }

        except httpx.HTTPStatusError as e:
            error_body = e.response.json()
            error_message = error_body.get("error", {}).get("message", "API-Fehler")
            logger.error(f"HTTP Error Gemini Image: {error_body}")
            raise ValueError(f"Fehler bei Gemini: {error_message}")
        except Exception as e:
            logger.error(f"Error Gemini Image Generation: {e}", exc_info=True)
            raise
