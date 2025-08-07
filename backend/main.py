from fastapi import FastAPI
from pydantic import BaseModel
from . import llm_gateway

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str
    provider: str

@app.get("/api/health")
async def read_health():
    return {"status": "ok", "message": "Hello from Janus Backend"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # TODO: API-Key sicher aus der Konfiguration laden
    api_key = "dummy_key_for_now"
    return llm_gateway.call_llm(request.provider, request.prompt, api_key)
