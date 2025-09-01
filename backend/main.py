import json
import os
import keyring
import logging
import traceback
import asyncio
import shutil
from fastapi import FastAPI, HTTPException, Depends, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()
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
from backend.tool_registry import TOOL_REGISTRY # NEUER IMPORT

setup_logging()
logger = logging.getLogger('janus_backend')
app = FastAPI()

app.include_router(router)

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
    # await image_manager.migrate_image_paths(db, database.Message) # Kann auskommentiert werden, wenn nicht mehr benötigt
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
        # Nur die letzten 20 Nachrichten berücksichtigen, um den Kontext nicht zu überladen
        if len(chat_history) < 20:
             chat_history.append({"role": "user" if m.sender == "user" else "assistant", "content": m.content})
    
    all_memories = memory_manager.get_all_memories(db)
    similar_snippets = vector_service.find_similar_snippets(request.prompt, all_memories)
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
            # Führe die Tool-Funktion aus
            tool_result = await tool.func(api_key=api_key, **tool_args)
            
            # Verarbeite das Ergebnis (speziell für Bildgenerierung)
            image_url = tool_result.get("url")
            if image_url:
                local_image_path = await image_manager.save_image_from_url(image_url)
                final_answer = "Bild wurde erfolgreich generiert." # Standardantwort
            else:
                final_answer = tool_result.get("text", f"Tool {tool_name} ausgeführt.")
            
            # Kosten und Nutzung vom Tool-Ergebnis übernehmen
            usage = tool_result.get("usage", {})
            cost = tool_result.get("cost", {})
        else:
            final_answer = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."
            logger.error(final_answer)

    elif response_type == "text":
        final_answer = llm_response.get("text", "")
        # Ggf. Faktenextraktion für normale Chat-Antworten
        if final_answer: # Nur ausführen, wenn eine Antwort vorhanden ist
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/api/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    existing_chats = crud.get_chats(db)
    if existing_chats:
        last_chat = existing_chats[-1]
        messages = crud.get_messages_by_chat_id(db, chat_id=last_chat.id)
        if messages:
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

@app.get("/api/chats/{chat_id}/messages", response_model=List[schemas.MessageResponse])
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = crud.get_messages_by_chat_id(db, chat_id)
    for message in messages:
        if message.image_path and not message.image_path.startswith('/user_images'):
            # Path normalization logic if needed
            pass
    return messages

@router.put("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: int, title_update: schemas.ChatTitleUpdate, db: Session = Depends(get_db)):
    chat = crud.update_chat_title(db, chat_id, title_update.title)
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat title updated successfully"}

# ... (Restliche Endpunkte bleiben unverändert, hier der Übersichtlichkeit halber gekürzt) ...
# Fügen Sie hier die restlichen Endpunkte von `get_chat_details` bis `get_model_catalog` aus der Originaldatei ein.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)