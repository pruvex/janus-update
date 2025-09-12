import re
import json
import os
import keyring
import logging
import traceback
import asyncio
import shutil
import inspect

# Setup logging as early as possible
from backend.logger_config import setup_logging
setup_logging()
logger = logging.getLogger('janus_backend')

# Load OpenAI API key from keyring and set as environment variable as early as possible
try:
    openai_key = keyring.get_password("Janus-Projekt", "openai")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        logger.info("OpenAI API key loaded from keyring and set as environment variable.")
    else:
        logger.warning("OpenAI API key not found in keyring. Please ensure it's set.")
except Exception as e:
    logger.error(f"Error loading OpenAI API key from keyring: {e}", exc_info=True)

# Now import other modules that might depend on the environment variable
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from backend import llm_gateway, database, crud, schemas, memory_extractor, vector_service, chat_summarizer, image_manager, memory_manager, filesystem_manager
from backend.llm_providers import gemini_service
from backend.llm_providers.gemini_service import _extract_image_description
from backend.database import get_db
from backend.context_manager import ContextManager
from backend.utils.paths import get_app_data_dir, resource_path
from backend.tool_registry import TOOL_REGISTRY

def is_confirmation(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine positive Bestätigung ist."""
    # Liste von Phrasen, die eine exakte Übereinstimmung für eine Bestätigung erfordern.
    # Dies verhindert, dass Sätze, die nur "ja" enthalten, fälschlicherweise als Bestätigung gewertet werden.
    confirm_phrases = [
        "das ist richtig", "das stimmt", "ja genau", "ja das stimmt", "ist korrekt",
        "genau", "richtig", "korrekt", "stimmt", "ja"
    ]
    prompt_lower = prompt.lower().strip().replace('.', '').replace('!', '')
    
    # Prüfe auf exakte Übereinstimmung mit einer der Phrasen in der Liste.
    return prompt_lower in confirm_phrases

app = FastAPI()

FILE_OPERATION_HISTORY = []

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

class WorkspaceAdd(BaseModel):
    path: str

class WorkspaceRemove(BaseModel):
    path: str

class WorkspaceUpdate(BaseModel):
    workspaces: list[str]

# --- Business Logic ---
def check_budget_and_raise_if_exceeded(db: Session):
    today = datetime.now()
    current_month_cost = database.get_costs_for_month(today.year, today.month)
    config = load_config()
    monthly_budget = config.get("monthly_budget", 10.00)
    if current_month_cost >= monthly_budget:
        raise HTTPException(status_code=402, detail=f"Monthly budget of {monthly_budget:.2f} € exceeded. Current cost: {current_month_cost:.2f} €.")

# --- GOLD STANDARD SWITCH IMPLEMENTATION ---
async def handle_chat_request(request: ChatRequest, db: Session, context_manager: ContextManager, model_catalog: dict):
    api_key = keyring.get_password("Janus-Projekt", request.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key not found.")

    check_budget_and_raise_if_exceeded(db)

    if request.chat_id is None:
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")

    crud.create_message(db, chat_id=request.chat_id, sender="user", content=request.prompt)

    prompt_lower = request.prompt.lower()
    image_keywords = [
        "bild", "image", "picture", "foto", "photo",
        "zeichne", "draw"
    ]
    if any(keyword in prompt_lower for keyword in image_keywords):
            logger.info("Image generation intent detected by keyword. Bypassing reason_and_respond.")

            selected_text_model = model_catalog.get(request.model, {})
            image_model_id = selected_text_model.get("image_generation_model")

            if not image_model_id:
                default_image_models = {
                    "openai": "dall-e-3",
                    "gemini": "gemini-2.5-flash-image-preview"
                }
                image_model_id = default_image_models.get(request.provider, "")
                logger.warning(f"Model {request.model} has no image_generation_model. Falling back to {image_model_id}.")

            if not image_model_id:
                raise HTTPException(status_code=500, detail=f"No suitable image generation model found for provider {request.provider}")

            llm_response = await llm_gateway.generate_image(request.provider, image_model_id, api_key, request.prompt)

            remote_image_url = llm_response.get("image_url")
            local_image_path = None

            if remote_image_url and (remote_image_url.startswith("http://") or remote_image_url.startswith("https://")):
                try:
                    title = _extract_image_description(request.prompt)
                    local_image_path = image_manager.save_image_from_url(remote_image_url, title=title)
                    logger.info(f"[DEBUG] Image saved locally to: {local_image_path}")
                except Exception as e:
                    logger.error(f"Fehler beim lokalen Speichern des Bildes: {e}")
                    local_image_path = remote_image_url
            elif remote_image_url:
                local_image_path = remote_image_url
            else:
                local_image_path = None

            usage = llm_response.get("usage", {})
            cost = llm_response.get("cost", {})
            final_answer = f"Bild wurde erfolgreich mit {request.provider.capitalize()} generiert." if local_image_path else llm_response.get("text", f"Fehler bei der {request.provider.capitalize()}-Bildgenerierung.")

            crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)
            if usage and cost.get("total_cost", 0) > 0:
                database.save_cost_entry(
                    date=datetime.now(), model=image_model_id,
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    image_quality=usage.get("image_quality"),
                    image_cost=cost.get("image_cost", 0),
                    total_cost=cost.get("total_cost", 0)
                )
            return {"sender": "model", "text": final_answer, "image_url": local_image_path}

    chat_history = []
    messages = crud.get_messages_by_chat_id(db, request.chat_id)
    for m in messages:
        if len(chat_history) < 20:
             chat_history.append({"role": "user" if m.sender == "user" else "assistant", "content": m.content})
    
    # --- START NEUER CODEBLOCK: FEEDBACK-LOOP FÜR BESTÄTIGUNGEN ---
    if is_confirmation(request.prompt) and len(chat_history) >= 2:
        # Die letzte Nachricht ist die Bestätigung des Users.
        # Die vorletzte Nachricht ist die Aussage des Assistenten, die bestätigt wurde.
        confirmed_statement = chat_history[-2]['content']
        
        logger.info(f"User confirmed assistant's statement: '{confirmed_statement}'. Triggering direct fact saving.")

        # GOLD STANDARD FIX:
        # Anstatt zu versuchen, den Fakt aus einem komplexen Satz zu extrahieren,
        # nehmen wir die bestätigte Aussage, bereinigen sie von spekulativen Formulierungen
        # und speichern sie direkt als neue, verifizierte Tatsache.
        
        new_fact = confirmed_statement
        
        # Bereinige den Fakt von Formulierungen der Unsicherheit
        speculative_phrases = [
            "ist es sehr wahrscheinlich, dass ",
            "Es ist sehr wahrscheinlich, dass ",
            "vermutlich ",
            "wahrscheinlich "
        ]
        for phrase in speculative_phrases:
            if phrase in new_fact:
                new_fact = new_fact.split(phrase)[-1]

        # Entferne einleitende Nebensätze, die oft bei Schlussfolgerungen entstehen
        if new_fact.startswith("Da ") and "," in new_fact:
            new_fact = new_fact.split(",", 1)[1].strip()

        # Finale Bereinigung
        new_fact = new_fact.replace("ebenfalls ", "").strip().rstrip('.')
        
        # Erstelle eine Hintergrund-Aufgabe, um diesen neuen Fakt zu verarbeiten und zu speichern.
        # Dies stellt sicher, dass die UI nicht warten muss.
        async def process_confirmed_fact(fact_to_process, chat_id_to_save, provider_to_use, model_to_use, api_key_to_use):
            db_session = database.SessionLocal()
            try:
                logger.info(f"Processing confirmed fact in background: '{fact_to_process}'")
                
                # 1. Klassifizieren (Core / Non-Core)
                is_core = False
                try:
                    # Wir importieren hier, um Zirkel-Importe auf Modulebene zu vermeiden
                    from backend import memory_extractor 
                    classification_history = [{"role": "user", "content": memory_extractor.IS_CORE_FACT_PROMPT.format(fact=fact_to_process)}]
                    classification_response = await llm_gateway.call_llm(
                        provider=provider_to_use, model_id=model_to_use, api_key=api_key_to_use, messages=classification_history
                    )
                    if "ja" in classification_response.get("text", "").lower():
                        is_core = True
                        logger.info(f"Confirmed fact classified as CORE: '{fact_to_process}'")
                    else:
                        logger.info(f"Confirmed fact classified as NON-CORE: '{fact_to_process}'")
                except Exception as e:
                    logger.error(f"Could not classify confirmed fact '{fact_to_process}': {e}. Defaulting to NON-CORE.")

                # 2. Mit bestehendem Wissen konsolidieren oder neu speichern
                logger.info(f"Saving new, confirmed fact: '{fact_to_process}'")
                memory_manager.save_memory_snippet(db_session, chat_id=chat_id_to_save, snippet_text=fact_to_process, is_core=is_core)
            
            except Exception as e:
                logger.error(f"Error in background fact processing: {e}", exc_info=True)
            finally:
                db_session.close()

        # Starte die Verarbeitung des neuen Fakts im Hintergrund
        asyncio.create_task(process_confirmed_fact(
            new_fact, request.chat_id, request.provider, request.model, api_key
        ))
        
        # Gib dem User eine sofortige, positive Rückmeldung
        final_answer = "Verstanden. Ich habe mir das als neuen Fakt gemerkt."
        crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer)
        return {"sender": "model", "text": final_answer, "image_url": None}

    # --- ENDE NEUER CODEBLOCK ---
    
    # --- START ERSETZUNG: LÖSCHE DEN ALTEN GEDÄCHTNIS-BLOCK UND ERSETZE IHN HIERMIT ---

    user_name = crud.get_user_name(db)
    memory_context = ""

    # === GOLD STANDARD HYBRID CONTEXT BUILDER ===

    # 1. Konversations-Gedächtnis (Fakten aus dem aktuellen Chat)
    # Hole ALLE Fakten, die in DIESEM Chat gelernt wurden. Diese sind IMMER relevant.
    current_chat_memories = crud.get_memory_by_chat_id(db, request.chat_id)

    # 2. Assoziatives Langzeitgedächtnis: Finde die relevantesten "Ankerpunkte" in alten Chats (STM + LTM).
    all_searchable_past_memories = [
        mem for mem in memory_manager.get_all_searchable_memories(db)
        if mem.chat_id != request.chat_id
    ]
    similar_anchor_snippets = vector_service.find_similar_snippets(
        request.prompt, all_searchable_past_memories, top_k=3
    )

    # LTM-Promotion: Wenn Anker aus dem LTM stammen, befördere sie zurück ins STM.
    promoted_snippets = []
    for anchor in similar_anchor_snippets:
        if hasattr(anchor, 'source') and anchor.source == 'ltm':
            logger.info(f"Relevanter Fakt im LTM gefunden: '{anchor.snippet}'. Befördere zu STM.")
            promoted_memory = memory_manager.promote_ltm_to_stm(db, anchor)
            if promoted_memory:
                promoted_snippets.append(promoted_memory)
        else:
            # Es ist bereits im STM, füge es einfach zur Liste hinzu
            promoted_snippets.append(anchor)
    similar_anchor_snippets = promoted_snippets # Überschreibe die Liste mit den jetzt im STM befindlichen Objekten

    # 3. Kontext-Cluster-Retrieval: Lade den VOLLSTÄNDIGEN Kontext der relevanten alten Chats.
    contextual_cluster_facts = []
    processed_chat_ids = set()

    for anchor in similar_anchor_snippets:
        # Stellen sicher, dass wir mit einem STM-Objekt arbeiten (nach der Promotion)
        if anchor.chat_id not in processed_chat_ids:
            logger.info(f"Relevanter alter Chat gefunden (ID: {anchor.chat_id}). Lade vollständigen Kontext dieses Chats.")
            full_chat_context = crud.get_memory_by_chat_id(db, anchor.chat_id)
            contextual_cluster_facts.extend(full_chat_context)
            processed_chat_ids.add(anchor.chat_id)

    # 4. Kombiniere alle Gedächtnisarten und entferne Duplikate
    final_snippets = []
    processed_ids = set()

    # Priorität 1: Alle Erinnerungen aus dem aktuellen Chat.
    for mem in current_chat_memories:
        if mem.id not in processed_ids:
            final_snippets.append(mem)
            processed_ids.add(mem.id)
    
    # Priorität 2: Der vollständige Kontext relevanter alter Chats.
    for mem in contextual_cluster_facts:
        if mem.id not in processed_ids:
            final_snippets.append(mem)
            processed_ids.add(mem.id)

    memory_context = "\n".join([f"- {mem.snippet}" for mem in final_snippets])
    logger.info(f"[DEBUG] FINAL HYBRID Memory Context Generated (length: {len(memory_context)}): {memory_context[:1500]}")

    # 5. "Touch" all used STM memories to update their last_accessed_at timestamp
    for mem in final_snippets:
        # Wir berühren nur Einträge, die aus dem STM stammen (LTM-Einträge haben keine ID im STM)
        if hasattr(mem, 'id') and isinstance(mem, database.Memory):
             memory_manager.touch_memory_snippet(db, mem.id)
    logger.info(f"Touched {len(final_snippets)} memory snippets to update their relevance.")

    allowed_workspaces = filesystem_manager._get_allowed_workspaces()
    if allowed_workspaces:
        memory_context += "\n\n--- VERFÜGBARE ARBEITSBEREICHE ---\n"
        for ws in allowed_workspaces:
            memory_context += f"- {ws.name}: {ws}\n"

    if FILE_OPERATION_HISTORY:
        memory_context += "\n\n--- LETZTE DATEIOPERATIONEN ---\n"
        for op in FILE_OPERATION_HISTORY:
            memory_context += f"- {op}\n"

    # Übergebe den Kontext und den Benutzernamen an die Logik-Funktion
    llm_response = await llm_gateway.reason_and_respond(
        user_prompt=request.prompt,
        chat_history=chat_history,
        memory_context=memory_context,
        db=db,
        api_key=api_key,
        model=request.model,
        provider=request.provider,
        context_manager=context_manager,
        user_name=user_name
    )

    final_answer = ""
    local_image_path = None
    usage = llm_response.get("usage", {})
    cost = llm_response.get("cost", {})
    response_type = llm_response.get("type")

    if response_type == "tool_code":
        tool_name = llm_response.get("tool_name")
        tool_args = llm_response.get("tool_args", {})
        
        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
        
        tool = TOOL_REGISTRY.get(tool_name)
        if tool:
            all_possible_args = {"api_key": api_key, "db": db, **tool_args}
            tool_func_params = inspect.signature(tool.func).parameters
            final_tool_args = {name: all_possible_args[name] for name in tool_func_params if name in all_possible_args}
            
            if inspect.iscoroutinefunction(tool.func):
                tool_output = await tool.func(**final_tool_args)
            else:
                tool_output = tool.func(**final_tool_args)

            if "file" in tool_name or "directory" in tool_name:
                op_string = f"{tool_name} with args {tool_args}"
                FILE_OPERATION_HISTORY.append(op_string)
                if len(FILE_OPERATION_HISTORY) > 5:
                    FILE_OPERATION_HISTORY.pop(0)

            if tool_name == "websearch_tool":
                logger.info("Web search tool executed. Sending results back to LLM for summarization.")
                
                summarization_prompt = (
                    f"Basierend auf den folgenden Suchergebnissen, beantworte bitte die ursprüngliche Frage des Benutzers.\n"
                    f"Ursprüngliche Frage: '{request.prompt}'\n\n"
                    f"--- Suchergebnisse ---\n{tool_output}\n--- Ende der Suchergebnisse ---"
                )
                
                summarization_messages = chat_history[-2:]
                summarization_messages.append({"role": "user", "content": summarization_prompt})

                summarized_response = await llm_gateway.call_llm(
                    request.provider, request.model, api_key, messages=summarization_messages
                )
                
                final_answer = summarized_response.get("text", "Ich konnte die Suchergebnisse nicht zusammenfassen.")
                usage = summarized_response.get("usage", {})
                cost = summarized_response.get("cost", {})
            else:
                if isinstance(tool_output, dict):
                    image_url = tool_output.get("url")
                    usage = llm_response.get("usage", {})
                    cost = llm_response.get("cost", {})
                    if image_url:
                        local_image_path = image_manager.save_image_from_url(image_url, title=_extract_image_description(request.prompt))
                        final_answer = f"Tool '{tool_name}' erfolgreich ausgeführt. Bild wurde generiert."
                    else:
                        output = tool_output.get("output", str(tool_output))
                        final_answer = f"Ergebnis von Tool '{tool_name}': {output}"
                elif isinstance(tool_output, str):
                    usage = llm_response.get("usage", {})
                    cost = llm_response.get("cost", {})
                    image_url = None
                    local_image_path = None
                    final_answer = f"Ergebnis von Tool '{tool_name}': {tool_output}"
                else:
                    usage = llm_response.get("usage", {})
                    cost = llm_response.get("cost", {})
                    image_url = None
                    local_image_path = None
                    final_answer = f"Ergebnis von Tool '{tool_name}': {str(tool_output)}"
        else:
            final_answer = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."
            logger.error(final_answer)

    elif response_type == "text":
        final_answer = llm_response.get("text") or ""
        
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

    if not final_answer and not local_image_path:
        final_answer = "Es tut mir leid, ich konnte keine passende Antwort finden. Kannst du die Frage anders formulieren?"

    crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)
    
    if usage and cost.get("total_cost", 0) > 0:
        model_for_cost = usage.get("model", request.model)
        database.save_cost_entry(
            date=datetime.now(), model=model_for_cost,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            image_quality=usage.get("image_quality"),
            image_cost=cost.get("image_cost", 0),
            total_cost=cost.get("total_cost", 0)
        )

    config = load_config()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config(config)

    return {"sender": "model", "text": final_answer, "image_url": local_image_path}


# --- API Endpoints ---
@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db), context_manager: ContextManager = Depends(get_context_manager), model_catalog: dict = Depends(get_model_catalog_dep)):
    try:
        return await handle_chat_request(request, db, context_manager, model_catalog)
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
        # Dieser Block für die Zusammenfassung bleibt exakt so, wie er war.
        if messages:
            config = load_config()
            provider = config.get("last_used_provider", "openai")
            model = config.get("last_used_model", "gpt-4o-mini")
            api_key = keyring.get_password("Janus-Projekt", provider)
            if api_key:
                asyncio.create_task(chat_summarizer.summarize_and_store_chat(db, last_chat.id, api_key, provider, model))
            else:
                logger.warning(f"API key for {provider} not found. Skipping chat summarization.")
    
    # Die neue Archivierungslogik kommt hierhin, nach der Zusammenfassung und vor dem Erstellen des neuen Chats.
    try:
        # Wir rufen die neue Helferfunktion ohne Argumente auf.
        asyncio.create_task(run_archival())
    except Exception as e:
        logger.error(f"Failed to schedule memory archival task: {e}")

    return crud.create_chat(db, title=chat.title)


# Füge diese neue Helferfunktion irgendwo in main.py auf der obersten Ebene hinzu
# (z.B. nach der create_chat Funktion).

async def run_archival():
    """
    Wrapper, um die synchrone DB-Operation in einer asyncio-Task auszuführen.
    Diese Funktion erstellt ihre eigene DB-Session, um für Hintergrund-Tasks sicher zu sein.
    """
    logger.info("Background memory archival task starting.")
    db_session = database.SessionLocal()
    try:
        memory_manager.archive_old_memories(db_session)
        logger.info("Background memory archival task finished successfully.")
    except Exception as e:
        logger.error(f"An error occurred in the background archival task: {e}", exc_info=True)
    finally:
        db_session.close()

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
    messages = crud.get_messages_by_chat_id(db, chat_id)
    # NEU: Gehe durch die Nachrichten und stelle sicher, dass 'content' nie None ist.
    for message in messages:
        if message.content is None:
            message.content = ""  # Ersetze None durch einen leeren String
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
    logger.info("Attempting to retrieve API keys.")
    providers = ["openai", "gemini", "anthropic", "cohere"]
    retrieved_keys = {}
    for p in providers:
        try:
            key = keyring.get_password("Janus-Projekt", p)
            if key:
                retrieved_keys[p] = "********"
                logger.info(f"Successfully retrieved API key for provider: {p}")
            else:
                logger.info(f"No API key found for provider: {p}")
        except Exception as e:
            logger.error(f"Failed to retrieve API key for {p}: {e}", exc_info=True)
    return {"api_keys": retrieved_keys}

@app.post("/api/keys")
async def add_api_key(key: ApiKey):
    logger.info(f"Attempting to save API key for provider: {key.provider}")
    try:
        keyring.set_password("Janus-Projekt", key.provider.lower(), key.api_key)
        logger.info(f"Successfully saved API key for provider: {key.provider}")
        return {"message": "API Key saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save API key for {key.provider}: {e}", exc_info=True) # Add exc_info=True for full traceback
        raise HTTPException(status_code=500, detail="Failed to save API key.")

@app.post("/api/workspaces/add")
async def add_workspace(addition: WorkspaceAdd):
    config = load_config()
    if "filesystem_workspaces" not in config:
        config["filesystem_workspaces"] = []
    
    # Avoid duplicates
    if addition.path not in config["filesystem_workspaces"]:
        config["filesystem_workspaces"].append(addition.path)
        save_config(config)
        return {"message": "Workspace added successfully"}
    else:
        return {"message": "Workspace already exists"}

@app.post("/api/workspaces/remove")
async def remove_workspace(removal: WorkspaceRemove):
    config = load_config()
    if "filesystem_workspaces" in config and removal.path in config["filesystem_workspaces"]:
        config["filesystem_workspaces"].remove(removal.path)
        save_config(config)
        return {"message": "Workspace removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Workspace not found")

@app.get("/api/workspaces")
async def get_workspaces():
    config = load_config()
    return {"workspaces": config.get("filesystem_workspaces", [])}

@app.post("/api/workspaces")
async def save_workspaces(update: WorkspaceUpdate):
    config = load_config()
    config["filesystem_workspaces"] = update.workspaces
    save_config(config)
    return {"message": "Workspaces saved successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)