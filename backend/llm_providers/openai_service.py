import logging
import json
from typing import List, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.utils import _extract_image_description

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
    async def generate_response(self, api_key: str, model: str, messages: List[Dict], tools: Optional[List[Dict]] = None, image_data: Optional[str] = None, **kwargs) -> Dict:
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
                if model == "gpt-5": # Assuming "gpt-5" is the actual model ID
                    api_call_params["tool_choice"] = "required"
                else:
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
    async def generate_image(self, api_key: str, model: str, prompt: str, previous_response_id: Optional[str] = None, **kwargs) -> Dict:
        client = openai.AsyncOpenAI(api_key=api_key)
        
        try:
            # This API uses a chat model to generate images via a tool.
            # We use a powerful vision-capable model like gpt-4o as a reliable choice.
            chat_model_for_image_gen = "gpt-4o"
            logger.info(f"Calling Responses API (using model {chat_model_for_image_gen}) with prompt: '{prompt}' and previous_response_id: '{previous_response_id}'")

            api_params = {
                "model": chat_model_for_image_gen,
                "input": prompt,
                "tools": [{"type": "image_generation"}]
            }
            if previous_response_id:
                api_params["previous_response_id"] = previous_response_id

            response = await client.responses.create(**api_params)

            image_base64 = None
            if response.output:
                for output in response.output:
                    if output.type == "image_generation_call":
                        image_base64 = output.result
                        break
            
            if not image_base64:
                text_response = ""
                if response.output:
                    for output in response.output:
                        if output.type == "text":
                            text_response = output.result
                            break
                logger.warning(f"No image data found in the Responses API output. Text response: {text_response}")
                return {"type": "text", "text": text_response, "image_url": None, "usage": {}, "cost": {}, "response_id": response.id}


            from backend import image_manager
            import base64

            image_bytes = base64.b64decode(image_base64)
            cleaned_description = _extract_image_description(prompt)
            image_url = image_manager.save_image_from_bytes(image_bytes, description=cleaned_description, file_extension="png")

            usage_data = response.usage
            usage, cost = _calculate_and_log_cost(chat_model_for_image_gen, usage_data=usage_data)

            return {
                "image_url": image_url,
                "usage": usage,
                "cost": cost,
                "response_id": response.id
            }

        except Exception as e:
            logger.error(f"Error generating image with OpenAI Responses API: {e}", exc_info=True)
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
