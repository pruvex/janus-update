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
from backend import llm_gateway, database, crud, schemas, memory_extractor, vector_service, chat_summarizer
from backend.context_manager import ContextManager

setup_logging()
logger = logging.getLogger('janus_backend')
app = FastAPI()

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

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

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        api_key = keyring.get_password("Janus-Projekt", request.provider)
        if not api_key: raise HTTPException(status_code=400, detail="API Key not found.")
        
        # 1. Speichere die rohe Benutzernachricht im Gedächtnis (wenn sie lang genug ist)
        logger.info(f"Chat Request: chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")
        if request.chat_id is None:
            new_chat = crud.create_chat(db, title="New Chat") # Standardtitel
            request.chat_id = new_chat.id
            logger.info(f"New chat created with ID: {request.chat_id}")

        if len(request.prompt.split()) > 3: # Ignoriere kurze Sätze wie "hi"
             crud.save_raw_memory(db, chat_id=request.chat_id, user_input=request.prompt)

        # 2. Finde relevante Erinnerungen mit Vektor-Suche
        all_memories = crud.get_all_memories(db)
        logger.info(f"Loaded {len(all_memories)} memories from DB.")
        similar_snippets = vector_service.find_similar_snippets(request.prompt, all_memories, top_k=20, threshold=0.2)
        memory_context = "\n".join([f"- {mem.snippet}" for mem in similar_snippets])
        logger.info(f"Memory context for reasoning: {memory_context}")

        # 3. Lade den aktuellen Chat-Verlauf
        chat_history = []
        if request.chat_id:
            messages = crud.get_messages_by_chat_id(db, chat_id=request.chat_id)
            chat_history = [{"role": "user" if m.sender=="user" else "assistant", "content": m.content} for m in messages]

        # 4. Der EINE "Denk"-Schritt: Lasse die KI die Antwort synthetisieren
        final_answer = await llm_gateway.reason_and_respond(
            request.prompt, chat_history, memory_context, db, api_key, request.model, request.provider
        )

        # 5. Speichere die Konversation und Kosten
        if request.chat_id:
            crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)
            crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer)
        
        # NEU: Fakten aus der Konversation extrahieren und speichern
        full_exchange_text = f"User: {request.prompt}\nAssistant: {final_answer}"
        asyncio.create_task(
            memory_extractor.extract_and_save_fact(
                db=db, chat_id=request.chat_id, text_block=full_exchange_text, main_api_key=api_key, provider=request.provider, model=request.model
            )
        )

        # ... Kosten-Logik ...
        # This part is missing from the user's instruction, so I will comment it out for now.
        # usage = gateway_response.get("usage")
        # cost = gateway_response.get("cost", {})
        # if usage:
        #     database.save_cost_entry(
        #         date=datetime.now(), model=request.model,
        #         input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
        #         image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
        #         total_cost=cost.get("total_cost", 0)
        #     )

        # Save last used provider and model
        config = load_config()
        config["last_used_provider"] = request.provider
        config["last_used_model"] = request.model
        save_config(config)

        return {"sender": "model", "text": final_answer}
    except Exception as e:
        # ... Error Handling ...
        tb_str = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/api/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    # Summarize previous chat if it exists
    existing_chats = crud.get_chats(db)
    if existing_chats:
        last_chat = existing_chats[-1] # Assuming the last chat is the most recent
        messages = crud.get_messages_by_chat_id(db, chat_id=last_chat.id)
        if messages: # Only summarize if there are messages
            config = load_config()
            provider = config.get("last_used_provider", "openai")
            model = config.get("last_used_model", "gpt-4o-mini")
            api_key = keyring.get_password("Janus-Projekt", provider)
            if api_key:
                asyncio.create_task(chat_summarizer.summarize_and_store_chat(db, last_chat.id, api_key, provider, model))
            else:
                logger.warning(f"API key for {provider} not found. Skipping chat summarization.")

    return crud.create_chat(db, title=chat.title)


@app.get("/api/chats", response_model=List[schemas.ChatResponse])
async def get_all_chats(db: Session = Depends(get_db), include_archived: bool = False):
    return crud.get_chats(db, include_archived=include_archived)

@app.get("/api/chats/{chat_id}", response_model=schemas.ChatResponse)
async def get_chat_details(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.get_chat_by_id(db, chat_id=chat_id)
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.get("/api/chats/{chat_id}/messages", response_model=List[schemas.MessageResponse])
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    return crud.get_messages_by_chat_id(db, chat_id)
    
@app.put("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: int, title_update: schemas.ChatTitleUpdate, db: Session = Depends(get_db)):
    chat = crud.update_chat_title(db, chat_id, title_update.title)
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat title updated successfully"}

@app.put("/api/chats/{chat_id}/archive")
async def toggle_chat_archive(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.toggle_archive_chat(db, chat_id)
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat archive status toggled", "is_archived": chat.is_archived}
    
@app.get("/api/chats/{chat_id}/export/txt")
async def export_chat_to_txt(chat_id: int, db: Session = Depends(get_db)):
    chat, messages = crud.get_chat_with_messages(db, chat_id)
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")
    export_content = f"Chat: {chat.title}\n\n"
    for msg in messages:
        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        export_content += f"{timestamp} - {msg.sender}: {msg.content}\n"
    return Response(content=export_content, media_type="text/plain", headers={"Content-Disposition": f'attachment; filename="{chat.title}.txt"'})

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    if not crud.delete_chat(db, chat_id): raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

@app.get("/api/keys")
async def get_api_keys():
    providers = ["openai", "gemini"]
    return {"api_keys": {p: "********" for p in providers if keyring.get_password("Janus-Projekt", p)}}

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
    cost = database.get_costs_for_month(today.year, today.month)
    config = load_config()
    budget = config.get("monthly_budget", 10.00)
    return {"current_month_cost": cost, "monthly_budget": budget}

@app.post("/api/budget")
async def update_budget(budget_update: BudgetUpdate):
    config = load_config()
    config["monthly_budget"] = budget_update.budget
    save_config(config)
    return {"message": "Budget updated successfully."}

@app.get("/api/costs/summary-by-model")
async def get_costs_summary_by_model():
    return database.get_costs_summary_by_model_for_current_month()

@app.get("/api/last-used-model")
async def get_last_used_model():
    config = load_config()
    return {
        "provider": config.get("last_used_provider", "openai"),
        "model": config.get("last_used_model", "gpt-4o-mini")
    }