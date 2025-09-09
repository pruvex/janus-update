import logging
import re
from typing import List, Dict, Optional, Any
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.cost_calculator import calculate_cost
from backend import image_manager
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

def _extract_image_description(prompt: str) -> str:
    cleaned_prompt = prompt.lower()
    prefixes = [
        "gemini:", "gpt:", "mache ein bild von", "erstelle ein bild von",
        "generiere ein bild von", "make an image of", "generate an image of",
        "create an image of", "zeig mir bild von", "zeig mir ein bild von",
        "zeige mir bild von", "zeige mir ein bild von", "zeichne", "mache", "erstelle"
    ]
    for prefix in prefixes:
        if cleaned_prompt.startswith(prefix):
            cleaned_prompt = cleaned_prompt[len(prefix):].strip()
    cleaned_prompt = cleaned_prompt.replace(' ', '-')
    cleaned_prompt = re.sub(r'[^a-z0-9-]', '', cleaned_prompt)
    cleaned_prompt = re.sub(r'-+', '-', cleaned_prompt).strip('-')
    return cleaned_prompt

def _sanitize_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return schema
    new_schema = {}
    if 'type' in schema and isinstance(schema['type'], str):
        new_schema['type'] = schema['type'].upper()
    if 'description' in schema:
        new_schema['description'] = schema['description']
    if 'required' in schema:
        new_schema['required'] = schema['required']
    if 'enum' in schema:
        new_schema['enum'] = schema['enum']
    if 'properties' in schema and isinstance(schema['properties'], dict):
        new_schema['properties'] = {
            prop_name: _sanitize_schema_for_gemini(prop_schema)
            for prop_name, prop_schema in schema['properties'].items()
        }
    if 'items' in schema and isinstance(schema['items'], dict):
        new_schema['items'] = _sanitize_schema_for_gemini(schema['items'])
    return new_schema

class GeminiServiceProvider(BaseLLMProvider):

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, api_key: str, model: str, messages: List[Dict], tools: Optional[List[Dict]] = None, **kwargs) -> Dict:
        genai.configure(api_key=api_key)

        gemini_tools = []
        if tools:
            for tool in tools:
                if tool.get('type') == 'function' and 'function' in tool:
                    func_def = tool['function']
                    if 'parameters' in func_def:
                        func_def['parameters'] = _sanitize_schema_for_gemini(func_def['parameters'])
                    gemini_tools.append(func_def)
                else:
                    gemini_tools.append(tool)
        
        final_tools = gemini_tools if gemini_tools else None
        
        genai_model = genai.GenerativeModel(model, tools=final_tools)

        gemini_history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({'role': role, 'parts': [msg['content']]})

        last_user_prompt = messages[-1]['content']

        try:
            chat_session = genai_model.start_chat(history=gemini_history)
            response = await chat_session.send_message_async(last_user_prompt)

            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                tool_name = function_call.name
                tool_args = {key: value for key, value in function_call.args.items()}
                logger.info(f"Gemini LLM requested tool call: {tool_name} with args {tool_args}")
                usage, cost = _calculate_and_log_cost(model)
                return {"type": "tool_code", "tool_name": tool_name, "tool_args": tool_args, "usage": usage, "cost": cost}

            text_response = response.text
            input_tokens = (await genai_model.count_tokens_async(gemini_history)).total_tokens
            output_tokens = (await genai_model.count_tokens_async(text_response)).total_tokens
            usage, cost = _calculate_and_log_cost(model, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})
            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}

        except ResourceExhausted as e:
            logger.warning(f"Gemini API quota exceeded: {e.message}")
            return {"type": "text", "text": f"Fehler: Das Anfragelimit für die Gemini API wurde überschritten. (Fehler: 429)", "image_url": None, "usage": {}, "cost": {}}
        except Exception as e:
            logger.error(f"An unexpected error occurred with Gemini API: {e}", exc_info=True)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key: str, model: str, prompt: str, **kwargs) -> Dict:
        genai.configure(api_key=api_key)
        genai_model = genai.GenerativeModel(model)
        try:
            logger.info(f"Calling Gemini image model '{model}' with prompt: '{prompt}'")
            response = await genai_model.generate_content_async(prompt)
            image_data = None
            text_response = None
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_data = part.inline_data.data
                        break
                    if part.text:
                        text_response = part.text
            image_url = None
            if image_data:
                cleaned_description = _extract_image_description(prompt)
                image_url = image_manager.save_image_from_bytes(image_data, description=cleaned_description, file_extension="png")
                text_response = None
            usage, cost = _calculate_and_log_cost(model)
            return {"text": text_response, "image_url": image_url, "usage": usage, "cost": cost}
        except Exception as e:
            logger.error(f"Error generating image with Gemini (attempt failed): {e}")
            raise