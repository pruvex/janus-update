import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import llm_gateway

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Erlaube alle Ursprünge für die lokale Entwicklung
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_FILE = "backend/config.json"

class ChatRequest(BaseModel):
    prompt: str
    provider: str

class ApiKey(BaseModel):
    provider: str
    api_key: str

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"api_keys": {}} # Leere Konfiguration, wenn Datei nicht existiert
    except json.JSONDecodeError:
        return {"api_keys": {}} # Leere Konfiguration, wenn JSON ungültig ist

def save_config(config):
    try:
        # Sicherstellen, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        # Hier könnte man ein Logging hinzufügen
        print(f"Error saving config: {e}")
        raise

@app.get("/api/health")
async def read_health():
    return {"status": "ok", "message": "Hello from Janus Backend"}

@app.get("/api/keys")
async def get_api_keys():
    try:
        config = load_config()
        return {"api_keys": config.get("api_keys", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading API keys: {str(e)}")

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    try:
        config = load_config()
        if "api_keys" not in config:
            config["api_keys"] = {}
        config["api_keys"][key.provider] = key.api_key
        save_config(config)
        return {"message": "API Key saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving API key: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        config = load_config()
        api_keys = config.get("api_keys", {})
        api_key = api_keys.get(request.provider)

        if not api_key:
            raise HTTPException(status_code=400, detail=f"API Key for provider {request.provider} not found.")
        
        return llm_gateway.call_llm(request.provider, request.prompt, api_key)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during chat processing: {str(e)}")
