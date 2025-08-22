import json
import os
import keyring
import logging
import traceback
import re
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.logger_config import setup_logging
from backend import llm_gateway, database, crud, schemas, memory_extractor
from backend.context_manager import ContextManager

# --- Initialisierung ---
setup_logging()
logger = logging.getLogger('janus_backend')
app = FastAPI()

# --- Middleware & Statische Dateien ---
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Konfiguration & Startup ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
MODEL_CATALOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_catalog.json")

def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=2)

def load_model_catalog():
    with open(MODEL_CATALOG_FILE, "r") as f: return json.load(f)

model_catalog = load_model_catalog()
context_manager = ContextManager(model_catalog=model_catalog)

@app.on_event("startup")
async def startup_event():
    database.init_db()
    logger.info("Database initialized.")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Modelle ---
class ChatRequest(BaseModel):
    prompt: str; provider: str; model: str; chat_id: Optional[int] = None
class ApiKey(BaseModel):
    provider: str; api_key: str
class ModelSelection(BaseModel):
    provider: str; models: list[str]
class ChatTitleUpdate(BaseModel):
    title: str
class BudgetUpdate(BaseModel):
    budget: float

# --- API Endpunkte ---

@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        api_key = keyring.get_password("Janus-Projekt", request.provider)
        if not api_key:
            raise HTTPException(status_code=400, detail=f"API Key for {request.provider} not found.")

        # --- Verbessertes Memory Retrieval ---
        clean_prompt = re.sub(r'[^\w\s]', '', request.prompt.lower())
        search_words = [word for word in clean_prompt.split() if len(word) > 2]
        all_snippets = set()
        for word in search_words:
            snippets = crud.search_memory_by_text(db, search_term=word)
            for snippet in snippets:
                all_snippets.add(snippet.snippet)
        full_prompt_snippets = crud.search_memory_by_text(db, search_term=request.prompt)
        for snippet in full_prompt_snippets:
            all_snippets.add(snippet.snippet)
        memory_context = "\n".join([f"- {s}" for s in all_snippets])
        
        chat_history = []
        if request.chat_id:
            messages_from_db = crud.get_messages_by_chat_id(db, chat_id=request.chat_id)
            chat_history = [{"role": "user" if msg.sender == "user" else "assistant", "content": msg.content or ""} for msg in messages_from_db]
        
        chat_history.append({"role": "user", "content": request.prompt})
        
        final_prompt = context_manager.build_prompt_history(
            chat_history, 
            request.model,
            global_memory=memory_context
        )
        
        gateway_response = await llm_gateway.call_llm(request.provider, request.model, "", api_key, chat_history=final_prompt)
        
        if request.chat_id:
            crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)
            crud.create_message(
                db, chat_id=request.chat_id, sender="model",
                content=gateway_response.get("text", ""), image_path=gateway_response.get("image_url")
            )

        usage = gateway_response.get("usage")
        cost = gateway_response.get("cost", {})
        if usage:
            database.save_cost_entry(
                date=datetime.now(), model=request.model,
                input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
                image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
                total_cost=cost.get("total_cost", 0)
            )

        # Starte die Fakten-Extraktion als Hintergrundaufgabe
        try:
            full_exchange_text = f"User: {request.prompt}\nAssistant: {gateway_response.get('text', '')}"
            asyncio.create_task(
                memory_extractor.extract_and_save_fact(
                    db=db, chat_id=request.chat_id, text_block=full_exchange_text, api_key=api_key
                )
            )
        except Exception as e:
            logger.error(f"Fehler beim Starten der Hintergrund-Faktenextraktion: {e}")

        return { "sender": "model", "text": gateway_response.get("text", ""), "image_url": gateway_response.get("image_url") }
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/api/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    return crud.create_chat(db, title=chat.title)

@app.get("/api/chats", response_model=List[schemas.ChatResponse])
async def get_all_chats(db: Session = Depends(get_db), include_archived: bool = False):
    return crud.get_chats(db, include_archived=include_archived)

@app.get("/api/chats/{chat_id}", response_model=schemas.ChatResponse)
async def get_chat_details(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.get_chat_by_id(db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.get("/api/chats/{chat_id}/messages", response_model=List[schemas.MessageResponse])
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    return crud.get_messages_by_chat_id(db, chat_id)
    
@app.put("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: int, title_update: ChatTitleUpdate, db: Session = Depends(get_db)):
    chat = crud.update_chat_title(db, chat_id, title_update.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat title updated successfully"}

@app.put("/api/chats/{chat_id}/archive")
async def toggle_chat_archive(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.toggle_archive_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat archive status toggled", "is_archived": chat.is_archived}
    
@app.get("/api/chats/{chat_id}/export/txt")
async def export_chat_to_txt(chat_id: int, db: Session = Depends(get_db)):
    chat, messages = crud.get_chat_with_messages(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    export_content = f"Chat: {chat.title}\n\n"
    for msg in messages:
        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        export_content += f"{timestamp} - {msg.sender}: {msg.content}\n"
    return Response(content=export_content, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=\"{chat.title}.txt\""})

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    success = crud.delete_chat(db, chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

@app.get("/api/keys")
async def get_api_keys():
    providers = ["openai", "gemini"]
    return {"api_keys": {provider: "********" for provider in providers if keyring.get_password("Janus-Projekt", provider)}}

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    keyring.set_password("Janus-Projekt", key.provider, key.api_key)
    return {"message": "API Key saved successfully"}

@app.get("/api/models/selection/{provider}")
async def get_model_selection(provider: str):
    config = load_config()
    return {"selected_models": config.get("model_selection", {}).get(provider, [])}

@app.post("/api/models/selection")
async def save_model_selection(selection: ModelSelection):
    config = load_config()
    if "model_selection" not in config: config["model_selection"] = {}
    config["model_selection"][selection.provider] = selection.models
    save_config(config)
    return {"message": "Model selection saved successfully"}

@app.get("/api/costs/dashboard")
async def get_costs_dashboard():
    today = datetime.now()
    current_month_cost = database.get_costs_for_month(today.year, today.month)
    config = load_config()
    budget = config.get("monthly_budget", 10.00)
    return {"current_month_cost": current_month_cost, "monthly_budget": budget}

@app.post("/api/budget")
async def update_budget(budget_update: BudgetUpdate):
    config = load_config()
    config["monthly_budget"] = budget_update.budget
    save_config(config)
    return {"message": "Budget updated successfully."}

@app.get("/api/costs/summary-by-model")
async def get_costs_summary_by_model():
    return database.get_costs_summary_by_model_for_current_month()