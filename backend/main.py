import json
import os
import keyring
import logging
import traceback
import re
import asyncio
import shutil
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
from backend.utils.paths import get_app_data_dir, resource_path

setup_logging()
logger = logging.getLogger('janus_backend')
app = FastAPI()

# --- Static Files Mounting ---
# Mount the original static directory from the bundle for CSS, JS etc.
app.mount("/static", StaticFiles(directory=resource_path("backend/static")), name="static_bundle")
# Mount the user's data directory for images so they can be served
image_dir = os.path.join(get_app_data_dir(), "images")
os.makedirs(image_dir, exist_ok=True)
app.mount("/user_images", StaticFiles(directory=image_dir), name="user_images")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Path and Config Management ---
DATA_DIR = get_app_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MODEL_CATALOG_FILE = os.path.join(DATA_DIR, "model_catalog.json")

# These point to the files within the bundled app
TEMPLATE_CONFIG_FILE = resource_path("backend/config.json")
TEMPLATE_MODEL_CATALOG_FILE = resource_path("backend/model_catalog.json")

def initialize_file_from_template(template_path, destination_path):
    """Copies a file from the template location to the user's data directory if it doesn't exist."""
    if not os.path.exists(destination_path):
        try:
            # Make sure the destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy2(template_path, destination_path)
            logger.info(f"Initialized '{os.path.basename(destination_path)}' from template.")
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}. Cannot initialize config.")
            # Create a default empty file to avoid crashing the app
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
        return json.load(f)

# --- Dependency Injection ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_model_catalog_dep():
    return load_model_catalog()

def get_context_manager(model_catalog: dict = Depends(get_model_catalog_dep)):
    return ContextManager(model_catalog=model_catalog)


@app.on_event("startup")
async def startup_event():
    database.init_db()
    db = next(get_db())
    await crud.migrate_image_paths(db)
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
async def chat(request: ChatRequest, db: Session = Depends(get_db), context_manager: ContextManager = Depends(get_context_manager)):
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
            chat_history = []
            for m in messages:
                msg_data = {"role": "user" if m.sender=="user" else "assistant", "content": m.content}
                if m.image_path:
                    # Adjust path to be served by the new user_images mount
                    msg_data["image_url"] = m.image_path.replace("/static/images", "/user_images")
                chat_history.append(msg_data)

        # 4. Der EINE "Denk"-Schritt: Lasse die KI die Antwort synthetisieren
        llm_response = await llm_gateway.reason_and_respond(
            request.prompt, chat_history, memory_context, db, api_key, request.model, request.provider, context_manager
        )
        final_answer = llm_response.get("text")
        image_url = llm_response.get("image_url")
        usage = llm_response.get("usage")
        cost = llm_response.get("cost", {})

        # 5. Speichere die Konversation und Kosten
        if request.chat_id:
            crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)
            
            local_image_path = None
            if image_url: # If an image was generated
                local_image_path = crud.save_image_from_url(image_url)

            crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)
        
        # Speichere die Kosten der Haupt-LLM-Interaktion
        if usage and cost.get("total_cost", 0) > 0:
            database.save_cost_entry(
                date=datetime.now(), model=request.model,
                input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
                image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
                total_cost=cost.get("total_cost", 0)
            )

        # NEU: Fakten aus der Konversation extrahieren und speichern
        full_exchange_text = f"User: {request.prompt}\nAssistant: {final_answer}"
        asyncio.create_task(
            memory_extractor.extract_and_save_fact(
                db=db, chat_id=request.chat_id, text_block=full_exchange_text, main_api_key=api_key, provider=request.provider, model=request.model
            )
        )

        # Save last used provider and model
        config = load_config()
        config["last_used_provider"] = request.provider
        config["last_used_model"] = request.model
        save_config(config)

        # Adjust returned image path for the frontend
        if local_image_path:
            local_image_path = local_image_path.replace("/static/images", "/user_images")

        return {"sender": "model", "text": final_answer, "image_url": local_image_path}
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
    messages = crud.get_messages_by_chat_id(db, chat_id)
    for message in messages:
        if message.image_path and message.image_path.startswith("/static/images"):
            message.image_path = message.image_path.replace("/static/images", "/user_images")
    return messages
    
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

@app.get("/api/models/catalog")
async def get_model_catalog(catalog: dict = Depends(get_model_catalog_dep)):
    return catalog

if __name__ == "__main__":
    import uvicorn
    print("Attempting to start Uvicorn server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)