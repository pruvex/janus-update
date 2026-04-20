import logging
from typing import Dict, List

import google.generativeai as genai
from backend.services.cost_calculator import calculate_cost

logger = logging.getLogger("janus_backend")


def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Helper to calculate and log cost."""
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    logger.info(
        f"\n--- USAGE TRACKING ---\n"
        f"Model: {model_id}\n"
        f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n"
        f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n"
        f"Total Cost: {cost.get('total_cost', 0):.8f} €\n"
        f"----------------------"
    )
    return usage, cost


class GeminiTextGeneration:
    """
    Encapsulates the standard text generation functionality for the Gemini provider.
    """

    async def generate_text(self, model: str, history: List[Dict], system_instruction: str) -> Dict:
        logger.info("Standard Gemini request. Using Python SDK.")
        genai_model = genai.GenerativeModel(model_name=model, system_instruction=system_instruction)
        try:
            input_tokens = (await genai_model.count_tokens_async(history)).total_tokens
            response = await genai_model.generate_content_async(history)
            text_response = response.text
            output_tokens = (await genai_model.count_tokens_async(text_response)).total_tokens
            usage, cost = _calculate_and_log_cost(
                model,
                usage_data={
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                },
            )
            return {
                "type": "text",
                "text": text_response,
                "image_url": None,
                "usage": usage,
                "cost": cost,
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred with Gemini SDK: {e}", exc_info=True)
            raise
