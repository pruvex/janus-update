import json
import os
import keyring
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import llm_gateway
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Erlaube alle Ursprünge für die lokale Entwicklung
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

class ChatRequest(BaseModel):
    prompt: str
    provider: str
    model: str

class ApiKey(BaseModel):
    provider: str
    api_key: str

class ModelSelection(BaseModel):
    provider: str
    models: list[str]

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {} # Leere Konfiguration, wenn Datei nicht existiert
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {} # Leere Konfiguration, wenn JSON ungültig ist
    except Exception:
        raise # Re-raise other exceptions

def save_config(config):
    try:
        # Sicherstellen, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise

@app.get("/api/health")
async def read_health():
    return {"status": "ok", "message": "Hello from Janus Backend"}

@app.get("/api/keys")
async def get_api_keys():
    try:
        available_providers = ["openai", "gemini"] # Annahme: Diese Liste kommt von llm_gateway
        stored_api_keys = {}
        for provider in available_providers:
            if keyring.get_password("Janus-Projekt", provider) is not None:
                stored_api_keys[provider] = "********" # Maskiere den Key für die UI
        return {"api_keys": stored_api_keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading API keys: {str(e)}")

@app.get("/api/models/selection/{provider}")
async def get_model_selection(provider: str):
    try:
        config = load_config()
        return {"selected_models": config.get("model_selection", {}).get(provider, [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model selection: {str(e)}")

@app.post("/api/models/selection")
async def save_model_selection(selection: ModelSelection):
    try:
        config = load_config()
        if "model_selection" not in config:
            config["model_selection"] = {}
        config["model_selection"][selection.provider] = selection.models
        save_config(config)
        return {"message": "Model selection saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving model selection: {str(e)}")

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    try:
        keyring.set_password("Janus-Projekt", key.provider, key.api_key)
        return {"message": "API Key saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving API key: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        api_key = keyring.get_password("Janus-Projekt", request.provider)

        if not api_key:
            raise HTTPException(status_code=400, detail=f"API Key for provider {request.provider} not found.")
        
        return await llm_gateway.call_llm(request.provider, request.model, request.prompt, api_key)
    except HTTPException as e:
        raise e
    except Exception as e:
        tb_str = traceback.format_exc()
        print(f"Ein Fehler ist aufgetreten: {e}\nTraceback:\n{tb_str}")
        raise HTTPException(
            status_code=500,
            detail=f"Ein interner Serverfehler ist aufgetreten.\n\nTraceback:\n{tb_str}"
        )