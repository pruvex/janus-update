import logging
import json
from typing import List, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost
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

class OpenAIServiceProvider(BaseLLMProvider):

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, api_key: str, model: str, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict:
        client = openai.AsyncOpenAI(api_key=api_key)
        try:
            api_call_params = {
                "model": model,
                "messages": messages,
            }
            if tools:
                api_call_params["tools"] = tools
                api_call_params["tool_choice"] = "auto"

            response = await client.chat.completions.create(**api_call_params)
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                tool_call = tool_calls[0]
                function_args = json.loads(tool_call.function.arguments)
                logger.info(f"LLM requested tool call: {tool_call.function.name} with args {function_args}")

                usage_data = response.usage
                _, cost_data = calculate_cost(model, usage_data=usage_data)

                return {
                    "type": "tool_code",
                    "tool_name": tool_call.function.name,
                    "tool_args": function_args,
                    "usage": {"prompt_tokens": usage_data.prompt_tokens, "completion_tokens": usage_data.completion_tokens},
                    "cost": cost_data
                }

            text_response = response_message.content
            usage, cost = _calculate_and_log_cost(model, usage_data=response.usage)

            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}

        except Exception as e:
            logger.info(f"An error occurred with OpenAI API, retrying... Error: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict:
        client = openai.AsyncOpenAI(api_key=api_key)
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")
        
        try:
            logger.info(f"Attempting to generate image with prompt: {prompt}")
            response = await client.images.generate(model=model, prompt=prompt, n=1, size=size, quality=quality, response_format="url")

            cost_model_id = "dall-e-3-hd" if quality == "hd" else "dall-e-3-standard"
            image_usage, image_cost_data = _calculate_and_log_cost(model_id=cost_model_id, usage_data={"image_quality": quality, "image_size": size})

            image_url = response.data[0].url
            
            # The base provider expects a dictionary with specific keys
            return {
                "image_url": image_url,
                "usage": image_usage,
                "cost": image_cost_data
            }
        except Exception as e:
            logger.error(f"Error generating image with OpenAI (attempt failed): {e}")
            raise

# Standalone wrapper function for tool registration
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", **kwargs) -> Dict:
    """ 
    Standalone wrapper to be registered as a tool. 
    It instantiates the provider and calls the class method.
    """
    provider = OpenAIServiceProvider()
    # The tool was hardcoded to dall-e-3, so we pass it here.
    response = await provider.generate_image(api_key, "dall-e-3", prompt, size=size, quality=quality)
    
    # The tool registry expects a slightly different format (url instead of image_url)
    # We adapt it here to maintain compatibility.
    return {
        "url": response.get("image_url"),
        "usage": response.get("usage"),
        "cost": response.get("cost")
    }
