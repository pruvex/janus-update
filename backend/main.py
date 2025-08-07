import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from . import llm_gateway

app = FastAPI()

CONFIG_FILE = "backend/config.json"

class ChatRequest(BaseModel):
    prompt: str
    provider: str

class ApiKey(BaseModel):
    provider: str
    api_key: str

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

@app.get("/api/health")
async def read_health():
    return {"status": "ok", "message": "Hello from Janus Backend"}

@app.get("/api/keys")
async def get_api_keys():
    config = load_config()
    return {"api_keys": config.get("api_keys", {})}

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    config = load_config()
    if "api_keys" not in config:
        config["api_keys"] = {}
    config["api_keys"][key.provider] = key.api_key
    save_config(config)
    return {"message": "API Key saved successfully"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    config = load_config()
    api_keys = config.get("api_keys", {})
    api_key = api_keys.get(request.provider)

    if not api_key:
        raise HTTPException(status_code=400, detail=f"API Key for provider {request.provider} not found.")
    
    return llm_gateway.call_llm(request.provider, request.prompt, api_key)
