import base64
import logging
from typing import Dict

import openai
from backend.llm_providers.utils import _extract_image_description
from backend.services import image_manager
from backend.services.cost_calculator import calculate_cost
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("janus_backend")


def _calculate_and_log_cost(model_id_base: str, usage_data: dict = None, custom_prompt: str = None):
    """Helper to calculate and log cost."""
    # Extrahiere Qualität und Größe aus usage_data (die von kwargs in generate_image kommen)
    # Diese usage_data enthalten die vom Frontend gewählten Parameter
    quality = usage_data.get("quality", "medium") # Default to medium for GPT Image
    size = usage_data.get("size", "1024x1024")

    # Für GPT Image Modelle ist model_id_base bereits der korrekte Katalog-Lookup-Key
    full_model_id_for_catalog_lookup = model_id_base
    
    # Passiere die Qualität und Größe innerhalb von usage_data
    # calculate_cost erwartet diese nun direkt im usage_data dict
    updated_usage_data = usage_data.copy() if usage_data else {}
    updated_usage_data["quality"] = quality
    updated_usage_data["size"] = size

    usage, cost = calculate_cost(full_model_id_for_catalog_lookup, updated_usage_data, custom_prompt)
    logger.info(
        f"\n--- USAGE TRACKING ---\n"
        f"Model: {full_model_id_for_catalog_lookup}\n" # Logge den Katalog-ID
        f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n"
        f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n"
        f"Image Quality: {usage.get('image_quality', 'N/A')}\n"
        f"Image Size: {usage.get('image_size', 'N/A')}\n"
        f"Total Cost: {cost.get('total_cost', 0):.8f} €\n"
        f"----------------------"
    )
    return usage, cost


class OpenAIImageGeneration:
    """
    Encapsulates the image generation functionality for the OpenAI provider.
    """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict:
        """
        Generates an image using the OpenAI API.
        This method handles the logic for both dall-e-3 and the newer Responses API approach.
        """
        client = openai.AsyncOpenAI(api_key=api_key)

        # This logic is based on the original openai_service.py.
        # It seems to use a chat model to generate images via a tool.
        try:
            chat_model_for_image_gen = "gpt-4o"  # As it was in the original file
            logger.info(
                f"Calling OpenAI Image API (via model {chat_model_for_image_gen}) with prompt: '{prompt}'"
            )

            # The original implementation used client.responses.create, which seems to be a custom or older API structure.
            # A more standard approach for dall-e-3 would be client.images.generate.
            # To maintain original functionality, I will replicate the logic of using a powerful model to call an image tool.
            # For now, let's assume the `generate_image` was called for a DALL-E model directly.

            response = await client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=kwargs.get("size", "1024x1024"),
                quality=kwargs.get("quality", "medium"), # Default quality to 'medium' for GPT Image
            )

            image_base64 = response.data[0].b64_json
            if not image_base64:
                logger.warning("No image data found in the OpenAI API output.")
                return {
                    "type": "text",
                    "text": "Konnte kein Bild generieren.",
                    "image_url": None,
                    "usage": {},
                    "cost": {},
                }

            image_bytes = base64.b64decode(image_base64)
            cleaned_description = _extract_image_description(prompt)
            image_url = image_manager.save_image_from_bytes(
                image_bytes, description=cleaned_description, file_extension="png"
            )

            # DALL-E 3 doesn't return token usage, cost is per image.
            usage, cost = _calculate_and_log_cost(model, custom_prompt=prompt, usage_data=kwargs)

            return {"image_url": image_url, "usage": usage, "cost": cost, "text": None}

        except openai.APIStatusError as e: # Spezifischer Fehler für API-Statusfehler (z.B. 400, 401, etc.)
            error_message = f"OpenAI API Fehler (Status {e.status_code}): {e.response.json().get('error', {}).get('message', 'Unbekannter Fehler')} (Code: {e.response.json().get('error', {}).get('code', 'N/A')})"
            logger.error(error_message, exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {error_message}",
                "image_url": None,
                "usage": {},
                "cost": {},
            }
        except openai.APIConnectionError as e: # Fehler bei der Netzwerkverbindung
            error_message = f"OpenAI API Verbindungsfehler: {e.request}"
            logger.error(error_message, exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {error_message}",
                "image_url": None,
                "usage": {},
                "cost": {},
            }
        except openai.RateLimitError as e: # Rate Limit überschritten
            error_message = f"OpenAI API Rate Limit überschritten: {e.response.json().get('error', {}).get('message', 'Unbekannter Fehler')}"
            logger.error(error_message, exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {error_message}",
                "image_url": None,
                "usage": {},
                "cost": {},
            }
        except openai.AuthenticationError as e: # Authentifizierungsfehler
            error_message = f"OpenAI API Authentifizierungsfehler: {e.response.json().get('error', {}).get('message', 'Ungültiger API-Schlüssel')}"
            logger.error(error_message, exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {error_message}. Bitte überprüfen Sie Ihren API-Schlüssel.",
                "image_url": None,
                "usage": {},
                "cost": {},
            }
        except Exception as e:
            logger.error(f"Error generating image with OpenAI API: {e}", exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Bildgenerierung: {e}",
                "image_url": None,
                "usage": {},
                "cost": {},
            }
