import base64
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
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
    Handler for Gemini Image Generation Models (2.5 Flash, 3 Pro).
    Phase 1: Basic Text-to-Image.
    """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        image_bytes_list: list = None, # <--- KORREKT
        **kwargs,
    ) -> dict:
        genai.configure(api_key=api_key)
        
        # --- 1. Konfiguration ---
        generation_config = {
            "response_modalities": ["IMAGE"]
        }
        
        image_config = {}
        # Parameter aus Frontend
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")
        image_size = kwargs.get("image_size") # "1K", "2K", "4K"
        
        if aspect_ratio:
            image_config["aspectRatio"] = aspect_ratio
            
        if image_size:
            image_config["imageSize"] = image_size
            
        if image_config:
            generation_config["imageConfig"] = image_config
            
        logger.info(f"Gemini Image Config: {generation_config}")

        # --- 2. Content Aufbau (Text + Bilder) ---
        try:
            # FIX: Prompt-Engineering für Gemini Edit-Mode
            if image_bytes_list:
                # Wir sagen dem Modell explizit, dass es das Bild als Basis nehmen soll.
                # (Diese Technik nennt sich "Instruction Following")
                final_prompt = (
                    f"Use the attached image as the base. "
                    f"Preserve the main subject(s) with high fidelity. "
                    f"Apply the following change: {prompt}"
                )
                parts = [{"text": final_prompt}]
            else:
                # Normaler Text-zu-Bild Prompt
                parts = [{"text": prompt}]
            
            # Bilder anhängen
            if image_bytes_list:
                logger.info(f"Adding {len(image_bytes_list)} reference images to Gemini request.")
                for img_bytes in image_bytes_list:
                    # MIME-Type Erkennung
                    mime_type = "image/png"
                    if img_bytes.startswith(b'\xff\xd8'): mime_type = "image/jpeg"
                    elif img_bytes.startswith(b'RIFF'): mime_type = "image/webp"
                    
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(img_bytes).decode('utf-8')
                        }
                    })
            
            # Finalen 'contents' Array bauen
            contents = [{"role": "user", "parts": parts}]
            # --- END: Image Processing ---

            gen_model = genai.GenerativeModel(model)
            
            response = await gen_model.generate_content_async(
                contents=contents,
                generation_config=generation_config
            )
            
            # --- 3. Response Handling ---
            if not response.candidates or not response.parts:
                raise ValueError("Keine Bild-Daten von Gemini erhalten.")
                
            first_part = response.parts[0]
            
            # Bild erhalten?
            if hasattr(first_part, "inline_data") and first_part.inline_data:
                image_data = first_part.inline_data.data
                image_bytes_result = base64.b64decode(image_data)
                
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(
                    image_bytes_result, description=cleaned_description, file_extension="png"
                )
                
                # Kosten berechnen (mit den neuen Parametern)
                usage_data_for_cost = {
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size
                }
                # WICHTIG: usage_data als dictionary übergeben!
                usage, cost = _calculate_and_log_cost(model, usage_data=usage_data_for_cost)
                
                return {
                    "image_url": image_url,
                    "previous_response_id": None, 
                    "previous_image_id": None,
                    "usage": usage,
                    "cost": cost
                }
            else:
                text_content = first_part.text if hasattr(first_part, "text") else "Unbekannt"
                logger.warning(f"Gemini lieferte Text: {text_content}")
                return {
                    "type": "text",
                    "text": f"Gemini Hinweis: {text_content}",
                    "image_url": None
                }

        except Exception as e:
            logger.error(f"Error Gemini Generation: {e}", exc_info=True)
            raise e
