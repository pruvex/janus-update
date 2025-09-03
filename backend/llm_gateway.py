import logging
from backend.tool_registry import get_all_tool_definitions
from typing import List, Dict, Optional
import openai
import google.generativeai as genai
import json
import os
import uuid
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from backend.cost_calculator import calculate_cost, MODEL_PRICES
from sqlalchemy.orm import Session
from backend import crud, vector_service, image_manager
from backend.context_manager import ContextManager
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')
IMAGE_DIR = os.path.join(get_app_data_dir(), "images")

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

async def call_llm(provider: str, model_id: str, prompt: str, api_key: str, chat_history: Optional[List[Dict]] = None):
    if not chat_history:
        chat_history = [{"role": "user", "content": prompt}]

    model_info = MODEL_PRICES.get(model_id)
    if not model_info:
        raise ValueError(f"Model {model_id} not found in model catalog.")

    try:
        if provider == "openai":
            return await _call_openai_api(api_key, model_id, chat_history, model_info)
        elif provider == "gemini":
            return await _call_gemini_api(api_key, model_id, chat_history, model_info)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except RetryError as e:
        logger.error(f"API call failed after multiple retries: {e}")
        return {"type": "text", "text": "Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.", "image_url": None, "usage": {}, "cost": {}}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_openai_api(api_key: str, model_id: str, chat_history: List[Dict], model_info: Dict):
    client = openai.AsyncOpenAI(api_key=api_key)
    tools = get_all_tool_definitions()
    
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=chat_history,
            tools=tools,
            tool_choice="auto"
        )

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
async def _call_gemini_api(api_key: str, model_id: str, chat_history: List[Dict], model_info: Dict):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    
    gemini_history = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({'role': role, 'parts': [msg['content']]})
        
    try:
        response = await model.generate_content_async(gemini_history)
        text_response = response.text
        
        input_tokens = model.count_tokens(gemini_history).total_tokens
        output_tokens = model.count_tokens(text_response).total_tokens
        
        usage, cost = _calculate_and_log_cost(model_id, usage_data={"prompt_tokens": input_tokens, "completion_tokens": output_tokens})
        
        return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}
            
    except ResourceExhausted as e:
        logger.warning(f"Gemini API quota exceeded: {e.message}")
        # Don't retry on quota exceeded, just return the error
        return {"type": "text", "text": f"Fehler: Das Anfragelimit für die Gemini API wurde überschritten. Bitte versuchen Sie es in einer Minute erneut. (Fehler: 429)", "image_url": None, "usage": {}, "cost": {}}
    except Exception as e:
        logger.warning(f"An error occurred with Gemini API, retrying... Error: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_gemini_image_generation_api(api_key: str, model_id: str, prompt: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    try:
        logger.info(f"_call_gemini_image_generation_api: Calling model '{model_id}' with prompt: '{prompt}'")
        response = await model.generate_content_async(prompt)
        
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_data = part.inline_data.data
                break

        image_url = None
        if image_data:
            file_name = f"{uuid.uuid4()}.png"
            file_path = os.path.join(IMAGE_DIR, file_name)
            with open(file_path, 'wb') as f:
                f.write(image_data)
            image_url = f"/user_images/{file_name}"
            logger.info(f"_call_gemini_image_generation_api: Image saved to {file_path}")

        usage, cost = _calculate_and_log_cost(model_id)
        return {"text": "", "image_url": image_url, "usage": usage, "cost": cost}
    except Exception as e:
        logger.error(f"Error generating image with Gemini (attempt failed): {e}")
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
        
        result["usage"] = image_usage
        result["cost"] = image_cost_data
        return result
    except Exception as e:
        logger.error(f"Error generating image with tool (attempt failed): {e}")
        raise

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")
    
    # --- DIES IST DER KORREKTE PROMPT, DER ZUM TEST PASST ---
    system_rules = (
        "Du bist Janus, ein hilfreicher KI-Assistent, der logisch schlussfolgert. Deine Aufgabe ist es, die Frage des Benutzers zu beantworten.\n"
        "**DEINE GOLDENE REGEL: Deine Antwort MUSS sich auf die unten stehenden BEWEISE stützen. Erfinde keine Fakten.**\n\n"
        "1.  **FAKTEN AUS DEM LANGZEITGEDÄCHTNIS:** Dies ist die absolute Wahrheit über den Benutzer.\n"
        "2.  **AKTUELLER GESPRÄCHSVERLAUF:** Dieser liefert den unmittelbaren Kontext.\n\n"
        "**DEIN VORGEHEN:**\n"
        "- **KOMBINIERE FAKTEN:** Deine wichtigste Fähigkeit ist es, Fakten zu kombinieren, um eine logische Schlussfolgerung zu ziehen. (Beispiel: Wenn FAKT A 'Kalle mag Blau' ist und FAKT B 'Das Auto des Benutzers ist blau' ist, lautet die Schlussfolgerung 'Kalle würde eine Fahrt in dem Auto gefallen').\n"
        "- **ANTWORTE HILFREICH:** Formuliere eine direkte und nützliche Antwort auf die Frage des Benutzers, basierend auf den Fakten und deinen Schlussfolgerungen.\n"
        "- **GIB WISSENSLÜCKEN ZU:** Wenn die Beweise nicht ausreichen, um eine Frage vollständig zu beantworten, sage das klar und deutlich."
    )

    final_prompt_for_llm = f"{system_rules}\n\n"
    if memory_context:
        final_prompt_for_llm += f"--- FAKTEN AUS DEM LANGZEITGEDÄCHTNIS ---\n{memory_context}\n\n"
        
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    final_prompt_for_llm += f"--- AKTUELLER GESPRÄCHSVERLAUF ---\n{history_str}\n\n"
    final_prompt_for_llm += f"--- FRAGE DES BENUTZERS ---\n{user_prompt}\n\n--- ANTWORT ---"

    response = await call_llm(provider, model, final_prompt_for_llm, api_key, chat_history=[])
    
    if response.get("type") == "tool_code":
        return response
    
    return {
        "type": "text", 
        "text": response.get("text"), 
        "image_url": response.get("image_url"), 
        "usage": response.get("usage"), 
        "cost": response.get("cost")
    }