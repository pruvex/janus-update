import logging
from typing import List, Dict, Optional
import openai
import google.generativeai as genai
from backend.cost_calculator import calculate_cost

logger = logging.getLogger('janus_backend')

async def call_llm(provider: str, model: str, prompt: str, api_key: str, chat_history: Optional[List[Dict]] = None):
    """
    Haupt-Gateway-Funktion, die Anfragen an den entsprechenden API-Provider weiterleitet.
    Der 'prompt' Parameter wird ignoriert, da der eigentliche Inhalt in 'chat_history' liegt.
    """
    if not chat_history:
        chat_history = [{"role": "user", "content": prompt}]

    if provider == "openai":
        return await _call_openai_api(api_key, model, chat_history)
    elif provider == "gemini":
        return await _call_gemini_api(api_key, model, chat_history)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def _call_openai_api(api_key: str, model_id: str, chat_history: List[Dict]):
    client = openai.AsyncOpenAI(api_key=api_key)
    is_image_model = "dall-e" in model_id.lower()

    

    if is_image_model:
        final_prompt = chat_history[-1]['content']
        response = await client.images.generate(
            model=model_id,
            prompt=final_prompt,
            n=1,
            size="1024x1024",
            quality="standard"
        )
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        usage, cost = calculate_cost(model_id, custom_prompt=revised_prompt)
        return {"text": revised_prompt, "image_url": image_url, "usage": usage, "cost": cost}
    else:
        # Hier war der Fehler: `messages` MUSS chat_history sein.
        response = await client.chat.completions.create(
            model=model_id,
            messages=chat_history
        )
        text_response = response.choices[0].message.content
        usage, cost = calculate_cost(model_id, usage_data=response.usage)
        return {"text": text_response, "image_url": None, "usage": usage, "cost": cost}

async def _call_gemini_api(api_key: str, model_id: str, chat_history: List[Dict]):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    
    # Konvertiere die OpenAI-Format Historie korrekt in das Gemini-Format
    gemini_history = []
    for msg in chat_history:
        role = 'user' if msg['role'] == 'user' else 'model'
        gemini_history.append({'role': role, 'parts': [msg['content']]})
    
    
    
    response = await model.generate_content_async(gemini_history)
    
    text_response = response.text
    usage, cost = {}, {} # Platzhalter
    return {"text": text_response, "image_url": None, "usage": usage, "cost": cost}