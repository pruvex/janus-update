import logging
import json
from typing import List, Dict, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost, MODEL_PRICES

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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_openai_api(api_key: str, model_id: str, chat_history: List[Dict], model_info: Dict, tools: List[Dict]):
    client = openai.AsyncOpenAI(api_key=api_key)
    
    try:
        api_call_params = {
            "model": model_id,
            "messages": chat_history,
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
            _, cost_data = calculate_cost(model_id, usage_data=usage_data)

            return {
                "type": "tool_code",
                "tool_name": tool_call.function.name,
                "tool_args": function_args,
                "usage": {"prompt_tokens": usage_data.prompt_tokens, "completion_tokens": usage_data.completion_tokens},
                "cost": cost_data
            }

        text_response = response_message.content
        usage, cost = _calculate_and_log_cost(model_id, usage_data=response.usage)
        
        return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}

    except Exception as e:
        logger.warning(f"An error occurred with OpenAI API, retrying... Error: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    client = openai.AsyncOpenAI(api_key=api_key)
    try:
        logger.info(f"Attempting to generate image with prompt: {prompt}")
        response = await client.images.generate(model="dall-e-3", prompt=prompt, n=1, size=size, quality=quality, response_format=response_format)
        
        cost_model_id = "dall-e-3-hd" if quality == "hd" else "dall-e-3-standard"
        image_usage, image_cost_data = _calculate_and_log_cost(model_id=cost_model_id, usage_data={"image_quality": quality, "image_size": size})

        result = {"created": response.created}
        if response_format == "url":
            result["url"] = response.data[0].url
        
        image_usage['model'] = cost_model_id # Add model to usage info
        result["usage"] = image_usage
        result["cost"] = image_cost_data
        return result
    except Exception as e:
        logger.error(f"Error generating image with tool (attempt failed): {e}")
        raise
