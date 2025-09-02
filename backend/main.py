import re
import json
import os
import keyring
import logging
import traceback
import asyncio
import shutil
import inspect
from fastapi import FastAPI, HTTPException, Depends, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from backend.logger_config import setup_logging
from backend import llm_gateway, database, crud, schemas, memory_extractor, vector_service, chat_summarizer, image_manager, memory_manager
from backend.database import get_db
from backend.context_manager import ContextManager
from backend.utils.paths import get_app_data_dir, resource_path
from backend.tool_registry import TOOL_REGISTRY

setup_logging()
logger = logging.getLogger('janus_backend')
app = FastAPI()

# --- Static Files Mounting ---
app.mount("/static", StaticFiles(directory=resource_path("backend/static")), name="static_bundle")
image_dir = os.path.join(get_app_data_dir(), "images")
os.makedirs(image_dir, exist_ok=True)
app.mount("/user_images", StaticFiles(directory=image_dir), name="user_images")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Path and Config Management ---
DATA_DIR = get_app_data_dir()
logger.info(f"Application Data Directory: {DATA_DIR}")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MODEL_CATALOG_FILE = os.path.join(DATA_DIR, "model_catalog.json")

TEMPLATE_CONFIG_FILE = resource_path("backend/config.json")
TEMPLATE_MODEL_CATALOG_FILE = resource_path("backend/model_catalog.json")

def initialize_file_from_template(template_path, destination_path):
    if not os.path.exists(destination_path):
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy2(template_path, destination_path)
            logger.info(f"Initialized '{os.path.basename(destination_path)}' from template.")
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}. Cannot initialize config.")
            with open(destination_path, 'w') as f:
                json.dump({}, f)

def load_config():
    initialize_file_from_template(TEMPLATE_CONFIG_FILE, CONFIG_FILE)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.warning(f"Could not load or parse config file at {CONFIG_FILE}. Returning empty config.")
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def load_model_catalog():
    initialize_file_from_template(TEMPLATE_MODEL_CATALOG_FILE, MODEL_CATALOG_FILE)
    with open(MODEL_CATALOG_FILE, "r") as f:
        models_list = json.load(f)
    return {model["id"]: model for model in models_list}

def get_model_catalog_dep():
    return load_model_catalog()

def get_context_manager(model_catalog: dict = Depends(get_model_catalog_dep)):
    return ContextManager(model_catalog=model_catalog.values())

@app.on_event("startup")
async def startup_event():
    database.init_db()
    db = next(get_db())
    db.close()

# --- Pydantic Models for API ---
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

# --- Business Logic ---
def check_budget_and_raise_if_exceeded(db: Session):
    today = datetime.now()
    current_month_cost = database.get_costs_for_month(today.year, today.month)
    config = load_config()
    monthly_budget = config.get("monthly_budget", 10.00)

    if current_month_cost >= monthly_budget:
        raise HTTPException(status_code=402, detail=f"Monthly budget of {monthly_budget:.2f} € exceeded. Current cost: {current_month_cost:.2f} €.")

# --- GOLD STANDARD SWITCH IMPLEMENTATION ---
async def handle_chat_request(request: ChatRequest, db: Session, context_manager: ContextManager):
    api_key = keyring.get_password("Janus-Projekt", request.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key not found.")

    check_budget_and_raise_if_exceeded(db)

    # 1. Chat erstellen, falls nicht vorhanden
    if request.chat_id is None:
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")

    # 2. Benutzernachricht immer speichern
    crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)

    # 3. Chat-Historie und Gedächtnis-Kontext laden
    chat_history = []
    messages = crud.get_messages_by_chat_id(db, request.chat_id)
    for m in messages:
        if len(chat_history) < 20:
             chat_history.append({"role": "user" if m.sender == "user" else "assistant", "content": m.content})
    
    all_facts = memory_manager.get_all_facts(db)
    # Wir holen jetzt mehr Ergebnisse, um die Chance zu erhöhen, alle relevanten Fakten zu erwischen
    similar_snippets = vector_service.find_similar_snippets(request.prompt, all_facts, top_k=10)
    memory_context = "\n".join([f"- {mem.snippet}" for mem in similar_snippets])

    # 4. Zentraler Aufruf an den "Denk"-Prozess im Gateway
    llm_response = await llm_gateway.reason_and_respond(
        request.prompt, chat_history, memory_context, db, api_key, request.model, request.provider, context_manager
    )

    final_answer = ""
    local_image_path = None
    usage = llm_response.get("usage", {})
    cost = llm_response.get("cost", {})

    # 5. DER "SWITCH": Verarbeite die Antwort des Gateways
    response_type = llm_response.get("type")

    if response_type == "tool_code":
        tool_name = llm_response.get("tool_name")
        tool_args = llm_response.get("tool_args", {})

        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")

        tool = TOOL_REGISTRY.get(tool_name)
        if tool:
            # --- HIER IST DIE KORREKTUR ---
            # 1. Sammle alle Argumente, die wir potenziell übergeben könnten
            all_possible_args = {
                "api_key": api_key,
                "db": db,
                **tool_args  # Die vom LLM vorgeschlagenen Argumente
            }
            # 2. Finde heraus, welche Argumente die Tool-Funktion tatsächlich erwartet
            tool_func_params = inspect.signature(tool.func).parameters
            # 3. Baue ein Dictionary nur mit den Argumenten, die auch wirklich akzeptiert werden
            final_tool_args = {
                name: all_possible_args[name]
                for name in tool_func_params
                if name in all_possible_args
            }
            # 4. Rufe das Tool nur mit den passenden Argumenten auf
            # Prüfen, ob die Funktion asynchron ist oder nicht
            if inspect.iscoroutinefunction(tool.func):
                tool_result = await tool.func(**final_tool_args)
            else:
                tool_result = tool.func(**final_tool_args)
            # --- ENDE DER KORREKTUR ---

            # Generische Ergebnisverarbeitung
            # Wir nehmen an, dass Tools ein Dictionary zurückgeben
            usage = tool_result.get("usage", {})
            cost = tool_result.get("cost", {})

            # Spezifische Verarbeitung nur für den Bild-Fall
            image_url = tool_result.get("url")
            if image_url:
                local_image_path = image_manager.save_image_from_url(image_url)
                final_answer = f"Tool '{tool_name}' erfolgreich ausgeführt. Bild wurde generiert."
            else:
                # Generische Antwort für alle anderen Tools
                output = tool_result.get("output", f"Tool '{tool_name}' erfolgreich ausgeführt.")
                final_answer = f"Ergebnis von Tool '{tool_name}': {output}"
        else:
            final_answer = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."
            logger.error(final_answer)

    elif response_type == "text":
        # HIER DIE ÄNDERUNG: Sicherstellen, dass final_answer nie None ist
        final_answer = llm_response.get("text") or ""
        
        # --- NEUER GEMINI FALLBACK ---
        image_url_match = re.search(r"!\[.*?\]\((https?://[^\s]+)\)", final_answer) # Funktioniert jetzt immer
        if request.provider == "gemini" and image_url_match:
            logger.info("Gemini returned a text URL. Intercepting and calling image generation logic directly.")
            
            image_model_id = "gemini-2.5-flash-image-preview"
            image_response = await llm_gateway._call_gemini_image_generation_api(api_key, image_model_id, request.prompt)

            local_image_path = image_response.get("image_url")
            usage = image_response.get("usage", usage)
            cost = image_response.get("cost", cost)
            
            if local_image_path:
                final_answer = "Bild wurde erfolgreich mit Gemini generiert."
            else:
                final_answer = image_response.get("text", "Ein unbekannter Fehler bei der Gemini-Bildgenerierung ist aufgetreten.")
        # --- ENDE NEUER GEMINI FALLBACK ---
        
        if not local_image_path and final_answer:
            full_exchange_text = f"User: {request.prompt}\nAssistant: {final_answer}"
            asyncio.create_task(
                 memory_extractor.extract_and_save_fact(
                     db=db, chat_id=request.chat_id, text_block=full_exchange_text, 
                     original_prompt=request.prompt, main_api_key=api_key, 
                     provider=request.provider, model=request.model
                 )
             )
    else:
        final_answer = "Ein unerwarteter Fehler ist aufgetreten."
        logger.error(f"Unknown response type from LLM gateway: {response_type}")

    # 6. Speichere die finale Antwort des Models und die Kosten
    crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)
    
    if usage and cost.get("total_cost", 0) > 0:
        database.save_cost_entry(
            date=datetime.now(), model=request.model,
            input_tokens=usage.get("prompt_tokens", 0), 
            output_tokens=usage.get("completion_tokens", 0),
            image_quality=usage.get("image_quality"), 
            image_cost=cost.get("image_cost", 0),
            total_cost=cost.get("total_cost", 0)
        )

    # 7. Konfiguration speichern und Antwort an Frontend senden
    config = load_config()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config(config)

    return {"sender": "model", "text": final_answer, "image_url": local_image_path}

# --- API Endpoints ---
@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db), context_manager: ContextManager = Depends(get_context_manager)):
    try:
        return await handle_chat_request(request, db, context_manager)
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    existing_chats = crud.get_chats(db)
    if existing_chats:
        last_chat = existing_chats[-1]
        messages = crud.get_messages_by_chat_id(db, chat_id=last_chat.id)
        if messages:
            config = load_config()
            # HIER DIE ÄNDERUNG: Lade die zuletzt verwendeten Daten
            provider = config.get("last_used_provider", "openai")
            model = config.get("last_used_model", "gpt-4o-mini") # Fallback, falls nichts gespeichert ist
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
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
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
    
@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    if not crud.delete_chat(db, chat_id): raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}

@app.get("/api/costs/summary-by-model")
async def get_costs_summary_by_model():
    return database.get_costs_summary_by_model_for_current_month()

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

@app.get("/api/last-used-model")
async def get_last_used_model():
    config = load_config()
    return {
        "provider": config.get("last_used_provider", "openai"),
        "model": config.get("last_used_model", "gpt-4o-mini")
    }

@app.get("/api/models/catalog")
async def get_model_catalog(catalog: dict = Depends(get_model_catalog_dep)):
    return list(catalog.values())

@app.get("/api/keys")
async def get_api_keys():
    providers = ["openai", "gemini"]
    return {"api_keys": {p: "********" for p in providers if keyring.get_password("Janus-Projekt", p)}}

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    try:
        keyring.set_password("Janus-Projekt", key.provider, key.api_key)
        return {"message": "API Key saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save API key for {key.provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save API key.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)