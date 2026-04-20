import base64
import logging
import httpx
import sentry_sdk
import uuid
from typing import Dict

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

    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        narrative_prompt: str,
        preset_context: Dict,
        image_bytes_list: list = None,
        **kwargs
    ) -> Dict:
        # Endpunkt-URL bauen
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # --- 1. Konfiguration ---
        # WICHTIG: Wir erlauben TEXT und IMAGE. 
        # Wenn Gemini Tools (Google Search) nutzt, sendet es oft erst Text/Suchergebnisse und dann das Bild.
        generation_config = {"responseModalities": ["TEXT", "IMAGE"]}
        
        image_config = {}
        aspect_ratio = kwargs.get("aspect_ratio")
        image_size = kwargs.get("image_size")
        
        if aspect_ratio: image_config["aspectRatio"] = aspect_ratio
        if image_size: image_config["imageSize"] = image_size
        if image_config: generation_config["imageConfig"] = image_config
            
        logger.info(f"Gemini Image Config: {generation_config}")

        # --- 2. Tools (Google Search) ---
        tools_list = []
        # Grounding nur bei Modellen aktivieren, die es unterstützen (Preview/Pro)
        if "gemini-3" in model or "preview" in model:
            tools_list.append({"google_search": {}})
            logger.info("Gemini Grounding: Offering Google Search tool.")
        
        # 1. Start with Director's narrative as the base prompt
        final_image_prompt = narrative_prompt
        
        # 2. Force-append technical keywords for Gemini (The "Hammer" approach)
        # Gemini often ignores style in prose. We must append it explicitly.
        if preset_context:
            try:
                # Try to get the keywords directly
                tech_keywords = preset_context.get("gemini_style_keywords", "")
                
                # If not found, try to get them from the 'rules' dictionary (fallback)
                if not tech_keywords and "rules" in preset_context:
                    # Sometimes they're hidden elsewhere
                    pass 

                if tech_keywords and len(tech_keywords) > 5:
                    # Only append if they're not already at the end of the prompt (avoid duplication)
                    if tech_keywords not in final_image_prompt:
                        final_image_prompt = f"{final_image_prompt} \n\nSTYLE REFERENCE: {tech_keywords}"
                        logger.info("Gemini Provider: Force-appended technical keywords.")
                    else:
                        logger.info("Gemini Provider: Keywords already present in prompt.")
                else:
                    logger.warning("Gemini Provider: No technical keywords found in preset_context.")
            except Exception as e:
                logger.error(f"Gemini Prompt Assembly Error: {e}")
                # Fallback to pure narrative
                final_image_prompt = narrative_prompt
        else:
            logger.info("Gemini Provider: No preset context available.")
        
        logger.info(f"Gemini Final Prompt Length: {len(final_image_prompt)}")
        logger.info(f"Gemini Provider: Using enhanced prompt. Model: {model}")

        # --- 3. Content (Multi-Turn Simulation) ---
        contents = []

        if image_bytes_list and len(image_bytes_list) == 1:
            logger.info("Gemini: Using Multi-Turn Simulation for precise EDIT/REFINE.")
            
            # Turn 1: Wir simulieren, dass das Modell das Bild bereits erstellt hat
            # (Das funktioniert auch bei Cross-Provider Bildern!)
            img_bytes = image_bytes_list[0]
            mime_type = "image/jpeg" if img_bytes.startswith(b'\xff\xd8') else "image/png"
            
            contents.append({
                "role": "user",
                "parts": [{"text": "Generate an image based on the previous context."}]
            })
            contents.append({
                "role": "model",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(img_bytes).decode('utf-8')
                        }
                    }
                ]
            })
            
            # Turn 2: Deep Cohesion & Identity Protection
            instruction = (
                f"TASK: Deep Image Transformation.\n"
                f"MODIFICATION: {final_image_prompt}.\n"
                f"1. IDENTITY PROTECTION: Analyze the facial features of the person. You MUST maintain their specific likeness, age, and ethnicity. Do not change the person into someone else.\n"
                f"2. ANATOMICAL INTEGRITY: Ensure the head, neck, and shoulders are anatomically connected to the new clothing. No 'cut-and-paste' look.\n"
                f"3. GLOBAL RE-LIGHTING: You MUST repaint the lighting on the subject's skin and hair to match the new background perfectly. Use shadows and highlights to 'glue' the person into the scene.\n"
                f"4. TEXTURE HARMONY: The subject and the environment must share the same photographic grain, sharpness, and depth of field."
            )
            
            contents.append({"role": "user", "parts": [{"text": instruction}]})

        elif image_bytes_list and len(image_bytes_list) > 1:
            logger.info(f"Gemini: Native REST Combine Mode with {len(image_bytes_list)} images.")
            
            # WICHTIG: Keine Labels wie "Reference Image 1". 
            # Einfach Prompt + Bild + Bild. Das versteht Gemini 3 am besten.
            
            # 1. Der Prompt
            parts = [{"text": final_image_prompt}]
            
            # 2. Die Bilder (einfach anhängen)
            for img_bytes in image_bytes_list:
                m_type = "image/jpeg" if img_bytes.startswith(b'\xff\xd8') else "image/png"
                parts.append({
                    "inline_data": {
                        "mime_type": m_type,
                        "data": base64.b64encode(img_bytes).decode('utf-8')
                    }
                })
            
            contents.append({"role": "user", "parts": parts})
            
        else:
            # Normales Text-to-Image
            contents.append({"role": "user", "parts": [{"text": prompt}]})
        # --- 4. Payload ---
        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }

        if tools_list:
            payload["tools"] = tools_list

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            
            response_json = response.json()
            
            # --- 5. Response-Verarbeitung (Smart Search) ---
            candidates = response_json.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini API lieferte keine Kandidaten zurück.")

            first_candidate = candidates[0]
            finish_reason = first_candidate.get("finishReason")
            
            # Safety Check
            if finish_reason and finish_reason not in ["STOP", "MAX_TOKENS"]:
                safety_ratings = first_candidate.get("safetyRatings", [])
                msg = f"Generierung abgebrochen. Grund: {finish_reason}"
                if safety_ratings:
                    msg += " (Sicherheitsfilter)"
                logger.warning(msg)
                raise ValueError(msg)

            parts = first_candidate.get("content", {}).get("parts", [])
            
            image_data = None
            text_accumulator = []

            # Wir iterieren durch ALLE Teile, da das Bild nicht zwingend an Position 0 steht
            # (besonders nicht bei Grounding, wo erst Text kommt).
            for part in parts:
                if "inlineData" in part:
                    image_data = part["inlineData"]["data"]
                elif "text" in part:
                    text_accumulator.append(part["text"])

            if image_data:
                # ERFOLG: Bild gefunden
                image_bytes_result = base64.b64decode(image_data)
                
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(
                    image_bytes_result, description=cleaned_description, file_extension="png"
                )
                
                usage_data_for_cost = {"aspect_ratio": aspect_ratio, "image_size": image_size}
                usage, cost = _calculate_and_log_cost(model, usage_data=usage_data_for_cost)
                
                # Wenn Text dabei war (z.B. Wetterbericht), loggen wir ihn
                if text_accumulator:
                    logger.info(f"Gemini begleitender Text: {' '.join(text_accumulator)[:200]}...")

                return {
                    "image_url": image_url,
                    # FIX: Wir generieren eine UUID, damit das Frontend dies als KI-Bild erkennt
                    "previous_response_id": str(uuid.uuid4()), 
                    "previous_image_id": None,
                    "usage": usage,
                    "cost": cost
                }
            else:
                # KEIN BILD GEFUNDEN
                full_text = " ".join(text_accumulator)
                logger.warning(f"Gemini lieferte nur Text: {full_text}")
                
                if not full_text:
                    full_text = f"Unbekannter Fehler (FinishReason: {finish_reason})"
                    
                raise ValueError(f"Gemini hat kein Bild generiert. Antwort: {full_text[:300]}")

        except httpx.HTTPStatusError as e:
            error_body = e.response.json()
            error_msg = error_body.get("error", {}).get("message", "API Error")
            logger.error(f"HTTP Error Gemini Image: {error_body}")
            sentry_sdk.capture_exception(e)
            raise ValueError(f"API Fehler: {error_msg}")
        except Exception as e:
            logger.error(f"Error Gemini Image Generation: {e}", exc_info=True)
            sentry_sdk.capture_exception(e)
            raise ValueError(f"Generierungsfehler: {str(e)}")
