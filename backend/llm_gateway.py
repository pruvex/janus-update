from fastapi import APIRouter, HTTPException
import httpx
import os
import json
from openai import OpenAI

router = APIRouter()

async def _call_dalle_api(api_key: str, prompt: str, quality: str):
    client = OpenAI(api_key=api_key)
    
    response = client.images.generate(
        model="dall-e-3", # DALL-E 3 is the model for image generation
        prompt=prompt,
        size="1024x1024",
        quality=quality, # Use the passed quality
        n=1,
    )
    image_url = response.data[0].url
    return image_url # Return just the URL

# New function for OpenAI Chat Completion API calls
async def _call_chat_completion_api(api_key: str, prompt: str, model: str):
    client = OpenAI(api_key=api_key)
    
    messages = [{"role": "user", "content": prompt}]
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    chat_response_text = response.choices[0].message.content
    return {"text": chat_response_text} # Return as JSON object

async def call_llm(provider: str, model: str, prompt: str, api_key: str):
    if provider == "gemini":
        api_model_name = model.replace('-latest', '') # Added this line
        url = f"https://generativelanguage.googleapis.com/v1/models/{api_model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    elif provider == "openai":
        if "dall-e" in model:
            # Extract quality from model name if available (e.g., "dall-e-3-hd")
            quality = "standard"
            if "hd" in model:
                quality = "hd"
            return await _call_dalle_api(api_key, prompt, quality)
        else:
            return await _call_chat_completion_api(api_key, prompt, model)
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider.")

@router.get("/config")
async def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Config file not found.")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config