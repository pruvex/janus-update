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
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from backend.logger_config import setup_logging
from backend import llm_gateway, database, crud, schemas, memory_extractor, vector_service, chat_summarizer, image_manager, memory_manager
from backend.database import get_db
from backend.context_manager import ContextManager
from backend.utils.paths import get_app_data_dir, resource_path

# Wrapper for Gemini image generation to match tool signature
async def gemini_image_tool_wrapper(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    # _call_gemini_image_generation_api expects model_id as well, but it's determined internally
    # For now, we'll just pass the prompt and api_key
    # The model_id for Gemini image generation is typically hardcoded or derived from the model_catalog
    # This wrapper simplifies the interface for the TOOL_REGISTRY
    return await llm_gateway._call_gemini_image_generation_api(api_key, "gemini-2.5-flash-image-preview", prompt) # Hardcode model_id for now

# --- Tool Registry (Placeholder) ---
TOOL_REGISTRY = {
    "generate_image_tool": llm_gateway.generate_image_tool,
    # "gemini_image_generation": gemini_image_tool_wrapper # Removed as it's handled directly
}

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
logger.info(f"Application Data Directory: {DATA_DIR}")
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
    await image_manager.migrate_image_paths(db, database.Message)
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

async def _classify_intent_with_llm_fallback(prompt: str, api_key: str, provider: str, model: str) -> str:
    """Classifies the user's intent using an LLM."""
    # Use a dedicated, capable model for intent classification
    classification_model_id = "gpt-4o-mini" # Or gemini-2.5-pro
    classification_provider = "openai" # Or gemini

    # Ensure API key for the classification provider is available
    classification_api_key = keyring.get_password("Janus-Projekt", classification_provider)
    if not classification_api_key:
        logger.warning(f"API Key for {classification_provider} not found. Cannot use LLM for intent classification. Falling back to 'chat'.")
        return "chat"

    classification_prompt = (
        "You are an intent classification AI. Your task is to classify the user's prompt into one of the following categories: "
        "'chat', 'image_generation', 'tool_call', 'memory_query'. "
        "Respond with ONLY the category name, nothing else. Do NOT add any other text, explanations, or punctuation.\n\n"
        "Examples:\n"
        "Prompt: Hello, how are you?\nCategory: chat\n\n"
        "Prompt: Create an image of a red car.\nCategory: image_generation\n\n"
        "Prompt: Use the calculator tool to add 5 and 3.\nCategory: tool_call\n\n"
        "Prompt: What did we talk about yesterday?\nCategory: memory_query\n\n"
        f"Prompt: {prompt}\nCategory:"
    )
    try:
        response = await llm_gateway.call_llm(
            provider=classification_provider,
            model_id=classification_model_id,
            prompt=classification_prompt,
            api_key=classification_api_key,
            chat_history=[{"role": "user", "content": classification_prompt}]
        )
        intent = response.get("text", "").strip().lower()
        if intent in ["chat", "image_generation", "tool_call", "memory_query"]:
            logger.info(f"LLM classified intent as: {intent}")
            return intent
        else:
            logger.warning(f"LLM returned unrecognised intent '{intent}'. Falling back to 'chat'.")
            return "chat"
    except Exception as e:
        logger.error(f"Error classifying intent with LLM: {e}. Falling back to 'chat'.")
        return "chat"


def detect_intent(prompt: str) -> str:
    """Detects the user's intent based on keywords in the prompt (fast, local check)."""
    prompt_lower = prompt.lower()

    # Image generation keywords
    image_keywords = ["bild", "image", "picture", "foto", "photo", "draw", "create", "generate", "zeichne", "erstelle", "generiere"]
    if any(keyword in prompt_lower for keyword in image_keywords):
        return "image_generation"

    # Tool call keywords (example - expand as needed)
    tool_keywords = ["tool", "werkzeug", "führe aus", "execute"]
    if any(keyword in prompt_lower for keyword in tool_keywords):
        return "tool_call"

    # Memory query keywords (example - expand as needed)
    memory_keywords = ["erinnerst du dich", "was weisst du", "gedächtnis", "speicher"]
    if any(keyword in prompt_lower for keyword in memory_keywords):
        return "memory_query"

    return "chat" # Default to chat if no specific intent is detected by keywords


def check_budget_and_raise_if_exceeded(db: Session):
    today = datetime.now()
    current_month_cost = database.get_costs_for_month(today.year, today.month)
    config = load_config()
    monthly_budget = config.get("monthly_budget", 10.00) # Default budget of 10.00

    if current_month_cost >= monthly_budget:
        raise HTTPException(status_code=402, detail=f"Monthly budget of {monthly_budget:.2f} € exceeded. Current cost: {current_month_cost:.2f} €.")

def _check_model_capability(model_id: str, model_catalog: dict, required_capability: str):
    logger.info(f"_check_model_capability: Checking model '{model_id}' for capability '{required_capability}'.")
    logger.info(f"_check_model_capability: Full model_catalog received: {model_catalog}")
    model_info = model_catalog.get(model_id)
    if not model_info:
        raise HTTPException(status_code=400, detail=f"Model {model_id} not found in catalog.")
    
    capabilities = model_info.get("capabilities", [])
    logger.info(f"_check_model_capability: Model '{model_id}' capabilities: {capabilities}")
    if required_capability not in capabilities:
        raise HTTPException(status_code=400, detail=f"Model {model_id} does not support {required_capability}.")

async def _execute_tool_from_llm_response(llm_response: Dict, api_key: str) -> Dict:
    tool_name = llm_response.get("tool_name")
    tool_args = llm_response.get("tool_args")

    if tool_name in TOOL_REGISTRY:
        tool_function = TOOL_REGISTRY[tool_name]
        tool_output = await tool_function(api_key=api_key, **tool_args)
        
        final_answer = f"Tool '{tool_name}' executed. Output: {tool_output.get('url', tool_output.get('text', 'No direct output'))}"
        image_url = tool_output.get('url') # Assuming image tools return 'url'
        usage = tool_output.get('usage', {})
        cost = tool_output.get('cost', {})

        return {"text": final_answer, "image_url": image_url, "usage": usage, "cost": cost}
    else:
        return {"text": f"Unknown tool: {tool_name}", "image_url": None, "usage": {}, "cost": {}}

# --- OPTIMIERTER BEREICH START ---
async def handle_chat_request(request: ChatRequest, db: Session, context_manager: ContextManager, model_catalog: dict):
    api_key = keyring.get_password("Janus-Projekt", request.provider)
    logger.info(f"handle_chat_request: Provider from request: {request.provider}")
    logger.info(f"handle_chat_request: API Key retrieved (masked): {api_key[:4] + '********' + api_key[-4:] if api_key else 'None'}")
    if not api_key: raise HTTPException(status_code=400, detail="API Key not found.")

    intent = await _classify_intent_with_llm_fallback(request.prompt, api_key, request.provider, request.model)

    if request.chat_id is None:
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")

    # Speichere die Benutzernachricht immer zuerst
    crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)
    
    final_answer = ""
    local_image_path = None
    usage = {}
    cost = {}
    
    match intent:
        case "image_generation":
            try:
                model_info = model_catalog.get(request.model)
                image_url = None
                llm_response = {}

                if "image_generation" in model_info.get("capabilities", []):
                    _check_model_capability(request.model, model_catalog, "image_generation")
                    check_budget_and_raise_if_exceeded(db)
                    logger.info(f"Image Generation Request (Direct): chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")
                    
                    if request.provider == "gemini":
                        llm_response = await llm_gateway._call_gemini_image_generation_api(api_key, request.model, request.prompt)
                    else: # OpenAI DALL-E models
                        llm_response = await llm_gateway.reason_and_respond(
                            request.prompt, [], "", db, api_key, request.model, request.provider, context_manager
                        )
                
                elif "tool_calling" in model_info.get("capabilities", []):
                    _check_model_capability(request.model, model_catalog, "tool_calling")
                    check_budget_and_raise_if_exceeded(db)
                    logger.info(f"Image Generation Request (via Tool): chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")

                    if request.provider == "openai":
                        llm_response = await llm_gateway.generate_image_tool(api_key=api_key, prompt=request.prompt)
                    elif request.provider == "gemini":
                        image_model_id = model_info.get("image_generation_model")
                        if not image_model_id:
                            raise HTTPException(status_code=400, detail=f"Gemini text model {request.model} does not specify an image generation model.")
                        llm_response = await llm_gateway._call_gemini_image_generation_api(api_key, image_model_id, request.prompt)
                    else:
                        raise HTTPException(status_code=400, detail=f"Unsupported provider {request.provider} for image generation via tool.")
                
                else:
                    raise HTTPException(status_code=400, detail=f"Model {request.model} does not support image generation directly or via tool calls.")

                # Einheitliche Verarbeitung der Antwort
                final_answer = llm_response.get("text", "")
                # OPTIMIZED LINE: Checks for 'url' first (from tool) and then 'image_url' (from direct generation)
                image_url = llm_response.get("url") or llm_response.get("image_url") 
                usage = llm_response.get("usage", {})
                cost = llm_response.get("cost", {})
                
                # The image_manager now always returns the correct relative path for saving in the DB
                # So we can use the returned URL directly if it's already a local path, or save it if it's a web URL
                if image_url and image_url.startswith("http"):
                    local_image_path = image_manager.save_image_from_url(image_url)
                else:
                    local_image_path = image_url


            except Exception as e:
                logger.error(f"Error in image_generation case: {e}\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"Internal Server Error during image generation: {e}")

        case "tool_call" | "memory_query" | "chat":
            capability = intent
            if intent == "memory_query": capability = "memory_query"
            elif intent == "chat": capability = "chat"
            else: capability = "tool_calling"
            
            _check_model_capability(request.model, model_catalog, capability)
            check_budget_and_raise_if_exceeded(db)

            logger.info(f"{intent.capitalize()} Request: chat_id={request.chat_id}, prompt='{request.prompt}', provider={request.provider}, model={request.model}")

            memory_context = ""
            if capability in ["chat", "memory_query"]:
                 if len(request.prompt.split()) > 3:
                    memory_manager.save_raw_memory(db, chat_id=request.chat_id, user_input=request.prompt)
                 all_memories = memory_manager.get_all_memories(db)
                 logger.info(f"Loaded {len(all_memories)} memories from DB.")
                 similar_snippets = vector_service.find_similar_snippets(request.prompt, all_memories, top_k=50, threshold=0.1)
                 memory_context = "\n".join([f"- {mem.snippet}" for mem in similar_snippets])
                 logger.info(f"Memory context for reasoning: {memory_context}")

            chat_history = []
            if request.chat_id:
                messages = crud.get_messages_by_chat_id(db, chat_id=request.chat_id)
                for m in messages:
                    msg_data = {"role": "user" if m.sender=="user" else "assistant", "content": m.content}
                    if m.image_path:
                        msg_data["image_url"] = m.image_path
                    chat_history.append(msg_data)

            llm_response = await llm_gateway.reason_and_respond(
                request.prompt, chat_history, memory_context, db, api_key, request.model, request.provider, context_manager
            )
            
            final_answer = llm_response.get("text", "")
            # OPTIMIZED LINE: Also check for 'url' here for images generated during a chat (e.g., by GPT-4o)
            image_url = llm_response.get("url") or llm_response.get("image_url") 

            if image_url and image_url.startswith("http"): # DALL-E via Chat (e.g. GPT-4o) gives a full URL
                local_image_path = image_manager.save_image_from_url(image_url)
            else:
                local_image_path = image_url

            usage = llm_response.get("usage", {})
            cost = llm_response.get("cost", {})

            if intent == "chat":
                 full_exchange_text = f"User: {request.prompt}\nAssistant: {final_answer}"
                 asyncio.create_task(
                     memory_extractor.extract_and_save_fact(
                         db=db, chat_id=request.chat_id, text_block=full_exchange_text, original_prompt=request.prompt, main_api_key=api_key, provider=request.provider, model=request.model
                     )
                 )
        case _:
            raise HTTPException(status_code=400, detail="Unknown intent")
            
    # Speichere die Antwort des Models und die Kosten
    crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)

    if usage and cost.get("total_cost", 0) > 0:
        database.save_cost_entry(
            date=datetime.now(), model=request.model,
            input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
            image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
            total_cost=cost.get("total_cost", 0)
        )

    config = load_config()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config(config)

    return {"sender": "model", "text": final_answer, "image_url": local_image_path}
# --- OPTIMIERTER BEREICH ENDE ---


@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db), context_manager: ContextManager = Depends(get_context_manager), model_catalog: dict = Depends(get_model_catalog_dep)):
    try:
        return await handle_chat_request(request, db, context_manager, model_catalog)
    except Exception as e:
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
    
@app.post("/api/chats/{chat_id}/messages", response_model=schemas.MessageResponse)
async def add_message_to_chat(chat_id: int, msg: schemas.MessageCreate, db: Session = Depends(get_db)):
    chat = crud.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    created = crud.create_message(db, chat_id=chat_id, sender=msg.sender, content=msg.content, image_path=msg.image_path)
    # Normalize image path for serving if needed
    if created.image_path and created.image_path.startswith("/static/images"):
        created.image_path = created.image_path.replace("/static/images", "/user_images")
    return created
    
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

@app.get("/api/debug/keyring/{provider_name}")
async def debug_keyring(provider_name: str):
    try:
        key = keyring.get_password("Janus-Projekt", provider_name)
        if key:
            return {"provider": provider_name, "status": "Key found", "key_masked": key[:4] + "********" + key[-4:]}
        else:
            return {"provider": provider_name, "status": "Key not found"}
    except Exception as e:
        return {"provider": provider_name, "status": "Error", "message": str(e)}

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
    return list(catalog.values())

if __name__ == "__main__":
    import uvicorn
    print("Attempting to start Uvicorn server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)