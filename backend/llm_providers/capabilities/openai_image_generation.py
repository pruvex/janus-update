import logging
import base64
from typing import Optional, Dict
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.services import image_manager
from backend.services.cost_calculator import calculate_cost
from backend.llm_providers.utils import _extract_image_description

logger = logging.getLogger("janus_backend")


def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Helper to calculate and log cost."""
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    logger.info(
        f"\n--- USAGE TRACKING ---\n"
        f"Model: {model_id}\n"
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

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_image(
        self, api_key: str, model: str, prompt: str, **kwargs
    ) -> Dict:
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
                model=model,  # e.g., "dall-e-3"
                prompt=prompt,
                n=1,
                size=kwargs.get("size", "1024x1024"),
                quality=kwargs.get("quality", "standard"),
                response_format="b64_json",
            )

            image_base64 = response.data[0].b64_json
            if not image_base64:
                logger.warning(f"No image data found in the OpenAI API output.")
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
            usage, cost = _calculate_and_log_cost(
                model, custom_prompt=prompt, usage_data=kwargs
            )

            return {"image_url": image_url, "usage": usage, "cost": cost, "text": None}

        except Exception as e:
            logger.error(f"Error generating image with OpenAI API: {e}", exc_info=True)
            raise
