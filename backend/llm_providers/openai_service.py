import logging
import json
from typing import List, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.services.cost_calculator import calculate_cost
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.utils import _extract_image_description
from backend.llm_providers.capabilities.openai_image_generation import (
    OpenAIImageGeneration,
)

logger = logging.getLogger("janus_backend")


def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
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


class OpenAIServiceProvider(BaseLLMProvider):
    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        client = openai.AsyncOpenAI(api_key=api_key)
        try:
            # The logic to handle image_data is now in main.py,
            # where the 'messages' list is constructed correctly from the start.
            # This function now just passes the prepared messages list to the API.

            api_call_params = {
                "model": model,
                "messages": messages,
            }
            if tools:
                api_call_params["tools"] = tools
                if model == "gpt-5":  # Assuming "gpt-5" is the actual model ID
                    api_call_params["tool_choice"] = "auto"
                else:
                    api_call_params["tool_choice"] = "auto"

            response = await client.chat.completions.create(**api_call_params)
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                logger.info(f"LLM requested {len(tool_calls)} tool calls.")
                
                processed_tool_calls = []
                for tool_call in tool_calls:
                    function_args = json.loads(tool_call.function.arguments)
                    processed_tool_calls.append({
                        "tool_call_id": tool_call.id,
                        "tool_name": tool_call.function.name,
                        "tool_args": function_args,
                    })
                    logger.info(
                        f"  - Parsed tool call: {tool_call.function.name} with args {function_args}"
                    )

                usage_data = response.usage
                _, cost_data = calculate_cost(model, usage_data=usage_data)

                return {
                    "type": "tool_code_list",
                    "tool_calls": processed_tool_calls,
                    "usage": {
                        "prompt_tokens": usage_data.prompt_tokens,
                        "completion_tokens": usage_data.completion_tokens,
                    },
                    "cost": cost_data,
                    "raw_assistant_response": response_message.model_dump(),
                }

            text_response = response_message.content
            usage, cost = _calculate_and_log_cost(model, usage_data=response.usage)

            return {
                "type": "text",
                "text": text_response,
                "image_url": None,
                "usage": usage,
                "cost": cost,
            }

        except Exception as e:
            logger.info(f"An error occurred with OpenAI API, retrying... Error: {e}")
            raise

    def __init__(self):
        self.image_generator = OpenAIImageGeneration()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_image(
        self, api_key: str, model: str, prompt: str, **kwargs
    ) -> Dict:
        return await self.image_generator.generate_image(
            api_key, model, prompt, **kwargs
        )
