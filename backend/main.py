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
from backend.creative_writer import creative_writer

def is_confirmation(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine positive Bestätigung ist. Toleriert Tippfehler."""
    # Liste von Schlüsselwörtern, die eine Bestätigung signalisieren
    keywords = ["richtig", "stimmt", "korrekt", "bestätigt", "ja"]
    
    prompt_lower = prompt.lower().strip().replace('.', '').replace('!', '').replace(',', '')
    
    # Prüfe, ob eines der Schlüsselwörter im Prompt enthalten ist.
    # Dies funktioniert auch bei Tippfehlern in anderen Wörtern (z.B. "ja das timmt")
    if any(keyword in prompt_lower for keyword in keywords):
        return True
    
    return False


def is_identity_query(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine Frage zur Identität oder den Fähigkeiten der KI ist."""
    prompt_lower = prompt.lower().strip()
    keywords = [
        "wer bist du", 
        "was bist du", 
        "deine rolle", 
        "deine aufgabe",
        "was ist deine funktion", 
        "stell dich vor",
        # --- ERWEITERUNG ---
        "deine stärken",
        "was kannst du",
        "wie arbeitest du",
        "was sind deine fähigkeiten",
        "erzähl mir von dir"
    ]
    # Prüft, ob der Prompt eine der Phrasen enthält
    return any(keyword in prompt_lower for keyword in keywords)

def is_greeting(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine einfache Begrüßung ist."""
    greetings = ["hallo", "hi", "hey", "guten morgen", "guten tag", "guten abend"]
    prompt_lower = prompt.lower().strip().replace('.', '').replace('!', '').replace(',', '')
    return prompt_lower in greetings

app = FastAPI()

FILE_OPERATION_HISTORY = []
LAST_RESPONSE_ID_PER_CHAT = {}

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
PERSONALITIES_FILE = os.path.join(DATA_DIR, "personalities.json") # NEU

TEMPLATE_CONFIG_FILE = resource_path("backend/config.json")
TEMPLATE_MODEL_CATALOG_FILE = resource_path("backend/model_catalog.json")
TEMPLATE_PERSONALITIES_FILE = resource_path("backend/personalities.json") # NEU

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

# Lade verfügbare Persönlichkeiten aus der JSON-Datei
def load_personalities():
    initialize_file_from_template(TEMPLATE_PERSONALITIES_FILE, PERSONALITIES_FILE)
    try:
        # Verwende utf-8-sig für bessere Kompatibilität mit BOM-markierten Dateien
        with open(PERSONALITIES_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Could not load or parse personalities file at {PERSONALITIES_FILE}. Error: {e}. Returning empty list.", exc_info=True)
        return []

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
    # --- HINZUFÜGEN START ---
    logger.info("Scheduling initial memory maintenance tasks on startup.")
    # Wir erstellen eine dedizierte DB-Session für die Hintergrund-Tasks, die in den Tasks selbst geschlossen wird.
    db_session_for_tasks = database.SessionLocal()
    try:
        # Führe die Wartung in Hintergrund-Tasks aus, damit der Start nicht blockiert wird.
        # Wichtig: Wir übergeben die erstellte Session an die Funktionen.
        asyncio.create_task(run_archival(db_session_for_tasks))
        asyncio.create_task(run_pruning(db_session_for_tasks))
    except Exception as e:
        logger.error(f"Failed to schedule memory maintenance tasks on startup: {e}")
        # Nur bei einem Fehler beim Erstellen der Tasks die Session hier schließen.
        db_session_for_tasks.close()
    # --- HINZUFÜGEN ENDE ---
    db = next(get_db())
    db.close()

# --- Pydantic Models for API ---
class ContentPart(BaseModel):
    type: str
    text: Optional[str] = None
    image_url: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: Optional[str] = None
    content: Optional[List[ContentPart]] = None
    provider: str
    model: str
    chat_id: Optional[int] = None
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
    # --- START: Adapt for new content structure ---
    user_prompt_text = ""
    image_data = None

    if request.content:
        # New format with content list
        for part in request.content:
            if part.type == 'text':
                user_prompt_text = part.text
            elif part.type == 'image_url' and part.image_url:
                image_data = part.image_url # This is the data URI
        
        # Fallback if no text part is found
        if not user_prompt_text:
            user_prompt_text = "Analyze the image."

    elif request.prompt:
        # Old format with just a prompt string
        user_prompt_text = request.prompt

    if not user_prompt_text:
        raise HTTPException(status_code=400, detail="No prompt provided.")
    # --- END: Adapt for new content structure ---


    async def _extract_entities(text: str) -> List[str]:
        # Simple, aber effektive Entitäten-Extraktion: Alle Wörter, die mit einem Großbuchstaben beginnen.
        # Dies fängt Namen und wichtige Substantive ab.
        entities = re.findall(r'\b[A-Z][a-z]*\b', text)
        return list(set(entities)) # 'set' entfernt Duplikate

    api_key = keyring.get_password("Janus-Projekt", request.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key not found.")

    check_budget_and_raise_if_exceeded(db)

    if request.chat_id is None:
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")

    crud.create_message(db, chat_id=request.chat_id, sender="user", content=user_prompt_text)

    config = load_config()
    personalities = load_personalities() # Lade aus der neuen Datei
    active_personality_id = config.get("active_personality", "ai_assistant")
    
    system_message = None
    for p in personalities:
        if p.get("id") == active_personality_id:
            persona_prompt = p.get("prompt")
            if persona_prompt:
                # --- START: FINALE ANPASSUNG FÜR ZEITLICHEN KONTEXT ---
                # Wir teilen der KI explizit mit, welches Datum wir simulieren.
                # Das hilft ihr, die Suchergebnisse korrekt einzuordnen.
                current_date_prompt = f"WICHTIGER HINWEIS: Das aktuelle Datum ist der {datetime.now().strftime('%d. %B %Y')}. Bitte beantworte alle Fragen aus der Perspektive dieses Datums. Wenn Websuchergebnisse widersprüchliche (ältere) Informationen enthalten, weise den Benutzer darauf hin und nutze die Informationen, die am besten zum aktuellen Datum passen."
                
                # Wir stellen den Datumshinweis an den Anfang des gesamten Prompts.
                persona_prompt = f"{current_date_prompt}\n\n{persona_prompt}"
                # --- ENDE: FINALE ANPASSUNG ---

                # WIR GEBEN JETZT ALLEN MODELLEN EINE EXPLIZITE ANWEISUNG, UM INKONSISTENZEN ZU VERMEIDEN
                tool_directive = (
                    "**WERKZEUGNUTZUNGS-DIREKTIVE:** Du MUSST deine Werkzeuge benutzen, um Fragen zu beantworten. "
                    "Wenn eine Frage aktuelle Informationen (nach 2023), Preise, Personen oder spezifische Fakten betrifft, "
                    "ist die Nutzung des 'perform_websearch'-Werkzeugs ZWINGEND VORGESCHRIEBEN. "
                    "Antworte NICHT aus deinem Gedächtnis, wenn ein Werkzeug die Frage besser beantworten kann."
                )
                
                import re
                if "**Werkzeugnutzung:**" in persona_prompt:
                    # Ersetze die alte, allgemeine Anweisung
                    persona_prompt = re.sub(
                        r'\*\*Werkzeugnutzung:\*\*.*', 
                        tool_directive, 
                        persona_prompt, 
                        flags=re.DOTALL
                    )
                else:
                    # Füge die Anweisung hinzu, falls sie fehlt
                    persona_prompt += f"\n\n{tool_directive}"

                logger.info("Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.")
                system_message = {"role": "system", "content": persona_prompt}
                logger.info(f"Using persona prompt for '{active_personality_id}'")
            break

    prompt_lower = user_prompt_text.lower()
    image_keywords = [
        "bild", "image", "picture", "foto", "photo",
        "zeichne", "draw"
    ]
    is_image_generation_request = image_data is None and any(keyword in prompt_lower for keyword in image_keywords)

    if is_image_generation_request:
        logger.info("Image generation intent detected by keyword.")
        
        # --- START: Multi-turn logic ---
        previous_response_id = LAST_RESPONSE_ID_PER_CHAT.get(request.chat_id)
        
        # For iterative generation, we must use the OpenAI provider.
        provider_for_gen = request.provider
        if previous_response_id and provider_for_gen != "openai":
            logger.warning(f"Iterative image generation is only supported for OpenAI. Forcing provider to OpenAI.")
            provider_for_gen = "openai"

        # The model used for the new Responses API is a chat model, not a dall-e model.
        selected_text_model = model_catalog.get(request.model, {})
        image_model_id = selected_text_model.get("image_generation_model", "gpt-4o") # Fallback to gpt-4o

        llm_response = await llm_gateway.generate_image(
            provider=provider_for_gen, 
            model_id=image_model_id, 
            api_key=api_key, 
            prompt=user_prompt_text,
            previous_response_id=previous_response_id
        )

        # Store the new response ID for the next turn, or clear if no image was returned
        if request.chat_id and llm_response.get("response_id") and llm_response.get("image_url"):
            LAST_RESPONSE_ID_PER_CHAT[request.chat_id] = llm_response["response_id"]
        elif request.chat_id in LAST_RESPONSE_ID_PER_CHAT:
            # If the model returned text or an error, the chain is broken. Clear the ID.
            del LAST_RESPONSE_ID_PER_CHAT[request.chat_id]
        # --- END: Multi-turn logic ---

        # Handle the response, which could be an image or text
        final_answer = ""
        local_image_path = None

        if llm_response.get("type") == "text":
             final_answer = llm_response.get("text", "Die Anfrage zur Bild-Generierung ergab eine Text-Antwort.")
        elif llm_response.get("image_url"):
            # The image is already saved by the provider service, and a local path is returned.
            local_image_path = llm_response.get("image_url")
            final_answer = f"Bild wurde erfolgreich mit {provider_for_gen.capitalize()} modifiziert/generiert."
        else:
            final_answer = f"Fehler bei der {provider_for_gen.capitalize()}-Bildgenerierung."

        usage = llm_response.get("usage", {})
        cost = llm_response.get("cost", {})

        crud.create_message(db, chat_id=request.chat_id, sender="model", content=final_answer, image_path=local_image_path)
        if usage and cost.get("total_cost", 0) > 0:
            cost_model = llm_response.get("usage", {}).get("model", image_model_id)
            database.save_cost_entry(
                date=datetime.now(), model=cost_model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                image_quality=usage.get("image_quality"),
                image_cost=cost.get("image_cost", 0),
                total_cost=cost.get("total_cost", 0)
            )
        return {"sender": "model", "text": final_answer, "image_url": local_image_path}

    else:
        # It's not an image generation request, so clear the stored ID for this chat
        if request.chat_id in LAST_RESPONSE_ID_PER_CHAT:
            del LAST_RESPONSE_ID_PER_CHAT[request.chat_id]

    # Lade den Chat-Verlauf, ABER wende eine spezielle Logik für Identitätsfragen an
    chat_history = []
    
    # Lade den Verlauf nur, wenn es KEINE Identitätsfrage ist
    if not is_identity_query(user_prompt_text):
        messages = crud.get_messages_by_chat_id(db, request.chat_id)
        for m in messages:
            if len(chat_history) < 20:
                chat_history.append({"role": "user" if m.sender == "user" else "assistant", "content": m.content})
    else:
        # Für Identitätsfragen: Lasse den Verlauf leer, um die Persona zu erzwingen.
        logger.info("Identity query detected. Using a clean context to reinforce persona.")
        # WICHTIG: Füge hier nur die aktuelle User-Frage hinzu.
        chat_history.append({"role": "user", "content": user_prompt_text})

    user_name = None
    memory_context = ""
    if not is_greeting(user_prompt_text):
        # === GOLD STANDARD HYBRID CONTEXT BUILDER V4 (CLUSTER-LOGIK) ===
        user_name = crud.get_user_name(db)

        # 1. Lade immer alle Fakten aus dem aktuellen Chat.
        final_snippets_map = {mem.id: mem for mem in crud.get_memory_by_chat_id(db, request.chat_id)}

        # 2. Finde relevante Fakten in alten Chats über eine mehrstufige Cluster-Suche.
        all_past_memories = [mem for mem in memory_manager.get_all_searchable_memories(db) if mem.chat_id != request.chat_id]

        if all_past_memories:
            # STUFE A: Finde die "Anker"-Fakten, die am relevantesten zur Frage sind.
            semantic_anchors = vector_service.find_similar_snippets(
                user_prompt_text, all_past_memories, top_k=5
            )

            # STUFE B: Extrahiere alle Namen (Entitäten) aus diesen Anker-Fakten.
            import re
            relevant_entities = set()
            if user_name:
                relevant_entities.add(user_name)

            for anchor in semantic_anchors:
                if hasattr(anchor, 'snippet'):
                    entities_in_snippet = re.findall(r'\b[A-Z][a-z]+\b', anchor.snippet)
                    for entity in entities_in_snippet:
                        relevant_entities.add(entity)
            
            logger.info(f"Identifizierte relevante Entitäten für Kontext-Cluster: {relevant_entities}")

            # STUFE C: Lade ALLE Fakten, die eine dieser relevanten Entitäten enthalten.
            if relevant_entities:
                for mem in all_past_memories:
                    if hasattr(mem, 'snippet'):
                        if any(entity in mem.snippet for entity in relevant_entities):
                            key = mem.id if hasattr(mem, 'id') and mem.source == 'stm' else f"ltm_{mem.original_memory_id}"
                            if key not in final_snippets_map:
                                final_snippets_map[key] = mem

        final_snippets = list(final_snippets_map.values())
        
        promoted_snippets = []
        for mem in final_snippets:
            if hasattr(mem, 'source') and mem.source == 'ltm':
                logger.info(f"Relevanter Fakt im LTM gefunden: '{mem.snippet}'. Befördere zu STM.")
                promoted_memory = memory_manager.promote_ltm_to_stm(db, mem)
                if promoted_memory:
                    promoted_snippets.append(promoted_memory)
            else:
                promoted_snippets.append(mem)
        final_snippets = promoted_snippets

        memory_context = "\n".join([f"- {mem.snippet}" for mem in final_snippets])
        logger.info(f"[DEBUG] FINAL HYBRID Memory Context Generated (length: {len(memory_context)}): {memory_context[:1500]}")

        for mem in final_snippets:
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

    # --- Kombiniere System-Prompt mit dem (jetzt korrekten) Chat-Verlauf ---
    messages_for_llm = []
    if system_message:
        messages_for_llm.append(system_message)
    
    # Füge den (potenziell leeren) Chat-Verlauf hinzu
    messages_for_llm.extend(chat_history)

    # Baue den User-Prompt mit dem Memory-Kontext zusammen
    prompt_with_context = user_prompt_text
    if memory_context and not is_greeting(user_prompt_text):
        prompt_with_context = f"**WICHTIG: Nutze die folgenden Fakten als Grundlage für deine Antwort.**\n--- FAKTENGRUNDLAGE ---\n{memory_context}\n\n--- AKTUELLE ANFRAGE DES BENUTZERS ---\n{user_prompt_text}"
    
    # Füge die finale User-Nachricht hinzu
    if image_data:
        # Wenn ein Bild vorhanden ist, erstelle eine mehrteilige Nachricht
        user_content = [
            {"type": "text", "text": prompt_with_context}
        ]
        # Füge das Bild als separaten Teil hinzu
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": image_data  # image_data ist die Data-URI
            }
        })
        messages_for_llm.append({"role": "user", "content": user_content})
    else:
        # Nur Text
        messages_for_llm.append({"role": "user", "content": prompt_with_context})
    
    
    
    # Übergebe den Kontext und den Benutzernamen an die Logik-Funktion
    final_answer = ""
    local_image_path = None
    usage = {}
    cost = {}
    response_type = "text" # Default to text for creative writer

    if active_personality_id == "creative_writer":
        logger.info("Creative Writer persona active. Calling creative_writer pipeline.")
        # Annahme: style und selection werden vorerst nicht aus dem Prompt extrahiert
        # und verwenden Standardwerte. Dies kann später erweitert werden.
        final_answer = await creative_writer(
            user_prompt_text,
            provider=request.provider,
            model=request.model,
            api_key=api_key,
            style="poetisch",
            selection="first"
        )
        # Für die creative_writer Pipeline setzen wir usage und cost auf 0
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "model": request.model}
        cost = {"total_cost": 0}
        response_type = "text"
    else:
        llm_response = await llm_gateway.reason_and_respond(
            user_prompt=user_prompt_text,
            chat_history=messages_for_llm,
            memory_context=memory_context,
            db=db,
            api_key=api_key,
            model=request.model,
            provider=request.provider,
            context_manager=context_manager,
            user_name=user_name,
            chat_id=request.chat_id,
            image_data=image_data
        )
        usage = llm_response.get("usage", {})
        cost = llm_response.get("cost", {})
        response_type = llm_response.get("type")

    if response_type == "tool_code":
        tool_name = llm_response.get("tool_name")
        tool_args = llm_response.get("tool_args", {})
        
        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
        
        tool = TOOL_REGISTRY.get(tool_name)
        tool_output_raw = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."

        if tool:
            # Wir rufen das Tool auf. Wichtig: Der API-Key ist hier der Key des *originalen Providers*
            all_possible_args = {"api_key": api_key, "db": db, **tool_args}
            tool_func_params = inspect.signature(tool.func).parameters
            final_tool_args = {name: all_possible_args[name] for name in tool_func_params if name in all_possible_args}
            
            if inspect.iscoroutinefunction(tool.func):
                tool_output_raw = await tool.func(**final_tool_args)
            else:
                tool_output_raw = tool.func(**final_tool_args)

            if "file" in tool_name or "directory" in tool_name:
                op_string = f"{tool_name} with args {tool_args}"
                FILE_OPERATION_HISTORY.append(op_string)
                if len(FILE_OPERATION_HISTORY) > 5:
                    FILE_OPERATION_HISTORY.pop(0)
            
            # --- WIEDERHERGESTELLTE LOGIK: SPEZIALBEHANDLUNG FÜR WEBSUCHE ---
            if tool_name == "perform_websearch" and isinstance(tool_output_raw, dict):
                logger.info("Web search completed. Sending results back to the original LLM for final response.")
                
                web_search_text = tool_output_raw.get("text", "Keine Ergebnisse gefunden.")
                web_search_urls = tool_output_raw.get("urls", [])

                # Wir bauen den Anweisungstext, genau wie im alten Code
                summarization_prompt = (
                    "Hier sind die Ergebnisse einer Websuche. Formuliere basierend auf diesen Informationen eine klare und hilfreiche Antwort auf die ursprüngliche Frage des Benutzers. "
                    "Gib am Ende deiner Antwort einen Abschnitt 'Quellen:' an und liste dort die gefundenen URLs auf.\n\n"
                    f"Ursprüngliche Frage: '{user_prompt_text}'\n\n"
                    f"--- Suchergebnisse ---\n{web_search_text}\n\n"
                    f"--- Gefundene URLs ---\n" + "\n".join([f"- {url}" for url in web_search_urls])
                )

                # Wir bauen die Nachrichten für den finalen Aufruf
                # Wichtig: Wir nehmen den bestehenden Verlauf und fügen die Tool-Antwort hinzu.
                messages_for_llm = list(chat_history)
                messages_for_llm.append({"role": "assistant", "content": None, "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": tool_name, "arguments": json.dumps(tool_args)}}]})
                messages_for_llm.append({"role": "tool", "tool_call_id": "call_123", "name": tool_name, "content": summarization_prompt})

                # Wir rufen das *originale Modell* (z.B. Gemini) erneut auf, um die Zusammenfassung zu erstellen
                final_response_from_llm = await llm_gateway.call_llm(
                    request.provider, request.model, api_key, messages=messages_for_llm, tools=None
                )

                final_answer = final_response_from_llm.get("text", "Ich konnte die Suchergebnisse nicht zusammenfassen.")
                usage = final_response_from_llm.get("usage", {})
                cost = final_response_from_llm.get("cost", {})
            
            # --- Fallback für alle anderen Tools ---
            else:
                # Dieser Teil behandelt z.B. die Bildgenerierung oder Dateizugriffe
                if isinstance(tool_output_raw, dict):
                    if tool_output_raw.get("url"): # Bildgenerierung
                        image_url = tool_output_raw.get("url")
                        local_image_path = image_manager.save_image_from_url(image_url, title=_extract_image_description(user_prompt_text))
                        final_answer = f"Tool '{tool_name}' erfolgreich ausgeführt. Bild wurde generiert."
                        
                        # Speichere die Kosten für den Tool-Aufruf
                        if llm_response.get("usage") and llm_response.get("cost"):
                            database.save_cost_entry(
                                date=datetime.now(), 
                                model=request.model, 
                                input_tokens=llm_response["usage"].get("prompt_tokens", 0),
                                output_tokens=llm_response["usage"].get("completion_tokens", 0),
                                total_cost=llm_response["cost"].get("total_cost", 0)
                            )
                        return {"sender": "model", "text": final_answer, "image_url": local_image_path}
                    else: # Andere Dictionary-Antworten
                        final_answer = f"Ergebnis von Tool '{tool_name}': {json.dumps(tool_output_raw, indent=2)}"
                else: # String-Antworten
                    final_answer = f"Ergebnis von Tool '{tool_name}': {str(tool_output_raw)}"
                
                # Für nicht-Websuche-Tools speichern wir die ursprüngliche Antwort
                usage = llm_response.get("usage", {})
                cost = llm_response.get("cost", {})
        else: # Fallback, falls das Tool nicht gefunden wird
            final_answer = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."
            logger.error(final_answer)
            usage = {}
            cost = {}
    elif response_type == "text":
        final_answer = llm_response.get("text") or ""
        
        if not local_image_path and final_answer and not is_greeting(user_prompt_text):
            full_exchange_text = f"User: {user_prompt_text}\nAssistant: {final_answer}"
            asyncio.create_task(
                 memory_extractor.extract_and_save_fact(
                     db=db, chat_id=request.chat_id, text_block=full_exchange_text,
                     original_prompt=user_prompt_text, main_api_key=api_key,
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
    
    

    return crud.create_chat(db, title=chat.title)


# Füge diese neue Helferfunktion irgendwo in main.py auf der obersten Ebene hinzu
# (z.B. nach der create_chat Funktion).

async def run_archival(db_session: Session):
    """
    Wrapper, um die synchrone DB-Operation in einer asyncio-Task auszuführen.
    Diese Funktion nutzt die übergebene DB-Session.
    """
    logger.info("Background memory archival task starting.")
    try:
        memory_manager.archive_old_memories(db_session)
        logger.info("Background memory archival task finished successfully.")
    except Exception as e:
        logger.error(f"An error occurred in the background archival task: {e}", exc_info=True)
    finally:
        # Diese Session wird nur einmal geschlossen, von dem Task, der als letztes fertig wird.
        # Da run_pruning meist schneller ist, wird diese hier die Session schließen.
        # Eine robustere Lösung wäre ein Counter, aber für diesen Fall ist es ausreichend.
        try:
            if db_session.is_active:
                db_session.close()
        except Exception:
            pass # Session könnte bereits geschlossen sein

async def run_pruning(db_session: Session):
    """
    Wrapper, um die synchrone DB-Operation zum Aufräumen in einer asyncio-Task auszuführen.
    """
    logger.info("Background memory pruning task starting.")
    try:
        memory_manager.prune_expired_memories(db_session)
        logger.info("Background memory pruning task finished successfully.")
    except Exception as e:
        logger.error(f"An error occurred in the background pruning task: {e}", exc_info=True)
    # Die Session wird von run_archival geschlossen, um doppeltes Schließen zu vermeiden.

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

# --- Füge dies am Ende von main.py hinzu ---

# Pydantic-Model für die Anfrage
class PersonalityUpdate(BaseModel):
    personality_id: str

@app.get("/api/personalities")
async def get_personalities():
    return load_personalities()

@app.get("/api/personalities/active")
async def get_active_personality():
    config = load_config()
    return {"active_personality_id": config.get("active_personality", "ai_assistant")}

@app.post("/api/personalities/active")
async def set_active_personality(update: PersonalityUpdate):
    config = load_config()
    personalities = load_personalities()
    
    personality_ids = [p.get("id") for p in personalities]
    if update.personality_id not in personality_ids:
        raise HTTPException(status_code=404, detail=f"Personality with id '{update.personality_id}' not found.")
        
    config["active_personality"] = update.personality_id
    save_config(config)
    logger.info(f"Active personality set to '{update.personality_id}'")
    return {"message": f"Active personality set to {update.personality_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)