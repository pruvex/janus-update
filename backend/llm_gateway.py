from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import json

router = APIRouter()

class ChatRequest(BaseModel):
    model: str
    messages: list
    use_google_ai: bool = False

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if request.use_google_ai:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Google API Key not configured.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": request.messages}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API Key not configured.")
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": request.model,
            "messages": request.messages
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

@router.get("/config")
async def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Config file not found.")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config