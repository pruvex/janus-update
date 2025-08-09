from fastapi import APIRouter, HTTPException
import httpx
import os
import json

router = APIRouter()

async def call_llm(provider: str, model: str, prompt: str, api_key: str):
    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    elif provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-3.5-turbo", # Oder ein anderer Standard-OpenAI-Modell
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
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