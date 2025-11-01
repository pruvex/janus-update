import re
import json
import os
import keyring
import logging
import traceback
import asyncio
import shutil
import inspect
import base64

# Setup logging as early as possible
from backend.logger_config import setup_logging

setup_logging()
logger = logging.getLogger("janus_backend")

# --- START: Dynamically add bundled ffmpeg to PATH ---
# This ensures that ffmpeg is found, both in development and in the PyInstaller build.
from backend.utils.paths import resource_path
import sys

ffmpeg_path = os.path.normpath(resource_path("backend/bin"))
if os.path.isdir(ffmpeg_path):
    logger.info(f"Adding bundled ffmpeg path to system PATH: {ffmpeg_path}")
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
else:
    logger.warning(f"ffmpeg directory not found at {ffmpeg_path}. STT might fail if ffmpeg is not in system PATH.")
# --- END: Dynamically add bundled ffmpeg to PATH ---


# Load OpenAI API key from keyring and set as environment variable as early as possible
try:
    openai_key = keyring.get_password("Janus-Projekt", "openai")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        logger.info(
            "OpenAI API key loaded from keyring and set as environment variable."
        )
    else:
        logger.warning("OpenAI API key not found in keyring. Please ensure it's set.")
except Exception as e:
    logger.error(f"Error loading OpenAI API key from keyring: {e}", exc_info=True)

# Now import other modules that might depend on the environment variable
from fastapi import FastAPI, HTTPException, Depends, Response, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from backend.data import database, crud, schemas
from backend.services import chat_summarizer, filesystem_manager, image_manager, llm_gateway, memory_manager, rag_manager, vector_service, memory_extractor

from backend.llm_providers import gemini_service
from backend.llm_providers.gemini_service import _extract_image_description
from backend.data.database import get_db
from backend.services.context_manager import ContextManager
from backend.utils.paths import get_app_data_dir, resource_path
from backend.tool_registry import TOOL_REGISTRY
from backend.services.creative_writer import creative_writer, generate_style_profile_from_rag

def is_creative_writing_request(prompt: str) -> bool:
    """Prüft, ob ein Prompt eine kreative Schreibaufgabe ist."""
    prompt_lower = prompt.lower()
    creative_keywords = [
        "schreib", "erzähl", "dichte", "gedicht", "geschichte", "haiku",
        "erfinde", "reime", "songtext", "ballade", "märchen", "dialog"
    ]
    return any(keyword in prompt_lower for keyword in creative_keywords)


def is_confirmation(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine positive Bestätigung ist. Toleriert Tippfehler."""
    # Liste von Schlüsselwörtern, die eine Bestätigung signalisieren
    keywords = ["richtig", "stimmt", "korrekt", "bestätigt", "ja"]

    prompt_lower = (
        prompt.lower().strip().replace(".", "").replace("!", "").replace(",", "")
    )

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
        "erzähl mir von dir",
    ]
    # Prüft, ob der Prompt eine der Phrasen enthält
    return any(keyword in prompt_lower for keyword in keywords)


def is_feature_suggestion_query(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt ein Vorschlag für ein neues Feature ist."""
    prompt_lower = prompt.lower()
    keywords = [
        "tts", "text-to-speech", "sprachausgabe", "vorlesen",
        "neues modul", "feature", "funktion", "könnten wir einbauen",
        "was hältst du davon", "wie wäre es mit", "spendieren"
    ]
    return any(keyword in prompt_lower for keyword in keywords)


def is_greeting(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine einfache Begrüßung ist."""
    greetings = ["hallo", "hi", "hey", "guten morgen", "guten tag", "guten abend"]
    prompt_lower = (
        prompt.lower().strip().replace(".", "").replace("!", "").replace(",", "")
    )
    return prompt_lower in greetings


def _extract_creative_style(prompt: str) -> str:
    """Extrahiert den gewünschten kreativen Stil aus dem Prompt."""
    prompt_lower = prompt.lower()
    if "haiku" in prompt_lower:
        return "haiku"
    if "gedicht" in prompt_lower or "poesie" in prompt_lower:
        return "gedicht"
    if "geschichte" in prompt_lower or "erzählung" in prompt_lower:
        return "geschichte"
    if "ballade" in prompt_lower:
        return "ballade"
    if "songtext" in prompt_lower:
        return "songtext"
    # Weitere Stile können hier hinzugefügt werden
    return "poetisch"  # Standard-Stil, wenn nichts Spezifisches gefunden wird


def _is_image_unrelated_task(prompt: str) -> bool:
    """
    Prüft mit Schlüsselwörtern, ob ein Prompt eine aufgabenorientierte, nicht-visuelle Aufgabe ist
    (wie Dateioperationen oder Websuche), bei der der visuelle Kontext stören würde.
    """
    prompt_lower = prompt.lower()

    # Schlüsselwörter für Aufgaben, die KEINEN Bildkontext wollen
    task_keywords = [
        # Dateioperationen
        "datei",
        "file",
        "ordner",
        "folder",
        "verzeichnis",
        "directory",
        "speicher",
        "save",
        "schreibe",
        "write",
        "lese",
        "read",
        "kopiere",
        "copy",
        "verschiebe",
        "move",
        "lösche",
        "delete",
        "benenne",
        "rename",
        "führe aus",
        "execute",
        # Websuche
        "suche",
        "search",
        "finde",
        "find",
        "preis",
        "price",
        "kostet",
        "costs",
        "gewonnen",
        "won",
        "ergebnis",
        "result",
        "nachrichten",
        "news",
        "wetter",
        "weather",
    ]

    if any(keyword in prompt_lower for keyword in task_keywords):
        return True

    return False


def _is_explicitly_image_related_task(prompt: str) -> bool:
    """
    Prüft, ob ein Prompt eine explizite Frage zum visuellen Inhalt eines Bildes ist.
    Diese Funktion hat Vorrang vor _is_image_unrelated_task.
    """
    prompt_lower = prompt.lower()

    # Schlüsselwörter für Aufgaben, die den Bildkontext ZWINGEND benötigen
    image_keywords = [
        "beschreibe",
        "erkennst",
        "was siehst du",
        "was ist das",
        "was ist auf dem bild",
        "analysiere das bild",
        "erkläre das bild",
        "identifiziere",
        "was für ein",
    ]

    if any(keyword in prompt_lower for keyword in image_keywords):
        return True

    return False


def _get_most_recent_image_path_from_history(
    messages: List[schemas.MessageResponse],
) -> Optional[str]:
    """Durchsucht die Nachrichtenverlauf von neu nach alt und gibt den Pfad des letzten Bildes zurück."""
    for message in reversed(messages):
        if message.image_path:
            # Wir geben den relativen Pfad zurück, wie er in der DB steht
            return message.image_path
    return None


app = FastAPI()

FILE_OPERATION_HISTORY = []
LAST_RESPONSE_ID_PER_CHAT = {}
LAST_SSML_RESPONSE_PER_CHAT = {}

# --- Static Files Mounting ---
app.mount(
    "/static",
    StaticFiles(directory=resource_path("backend/static")),
    name="static_bundle",
)
image_dir = os.path.join(get_app_data_dir(), "images")
os.makedirs(image_dir, exist_ok=True)
app.mount("/user_images", StaticFiles(directory=image_dir), name="user_images")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Path and Config Management ---
DATA_DIR = get_app_data_dir()
logger.info(f"Application Data Directory: {DATA_DIR}")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
MODEL_CATALOG_FILE = os.path.join(DATA_DIR, "model_catalog.json")
PERSONALITIES_FILE = os.path.join(DATA_DIR, "personalities.json")  # NEU

TEMPLATE_CONFIG_FILE = resource_path("backend/config/config.json")
TEMPLATE_MODEL_CATALOG_FILE = resource_path("backend/config/model_catalog.json")
TEMPLATE_PERSONALITIES_FILE = resource_path("backend/config/personalities.json")  # NEU


def initialize_file_from_template(template_path, destination_path):
    if not os.path.exists(destination_path):
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy2(template_path, destination_path)
            logger.info(
                f"Initialized '{os.path.basename(destination_path)}' from template."
            )
        except FileNotFoundError:
            logger.error(
                f"Template file not found: {template_path}. Cannot initialize config."
            )
            with open(destination_path, "w") as f:
                json.dump({}, f)


# Lade verfügbare Persönlichkeiten aus der JSON-Datei
def load_personalities():
    initialize_file_from_template(TEMPLATE_PERSONALITIES_FILE, PERSONALITIES_FILE)
    try:
        # Verwende utf-8-sig für bessere Kompatibilität mit BOM-markierten Dateien
        with open(PERSONALITIES_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(
            f"Could not load or parse personalities file at {PERSONALITIES_FILE}. Error: {e}. Returning empty list.",
            exc_info=True,
        )
        return []


def load_config():
    initialize_file_from_template(TEMPLATE_CONFIG_FILE, CONFIG_FILE)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.warning(
            f"Could not load or parse config file at {CONFIG_FILE}. Returning empty config."
        )
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


# Nahe am Anfang der Datei, bei den anderen Imports
from backend.services import rag_manager
from typing import Dict, Any

# Fügen Sie diese globale Variable nach den Imports hinzu
RAG_INDEXING_STATUS: Dict[str, Any] = {
    "in_progress": False,
    "total_files": 0,
    "processed_files": 0,
    "current_file": "",
    "message": "Keine Indexierung aktiv.",
}


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
    provider: str
    api_key: str


class ModelSelection(BaseModel):
    provider: str
    models: list[str]


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


class RagFolderRequest(BaseModel):
    path: str
    collection_name: str


class RagUrlRequest(BaseModel):
    url: str
    collection_name: str


# In backend/main.py, bei den anderen Pydantic-Modellen
class StyleProfile(BaseModel):
    genre: str
    author_style: str
    key_elements: List[str]
    complexity: str


class StyleProfileSaveRequest(BaseModel):
    profile_key: str
    profile_data: StyleProfile


# --- Business Logic ---
def check_budget_and_raise_if_exceeded(db: Session):
    today = datetime.now()
    current_month_cost = database.get_costs_for_month(today.year, today.month)
    config = load_config()
    monthly_budget = config.get("monthly_budget", 10.00)
    if current_month_cost >= monthly_budget:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget of {monthly_budget:.2f} € exceeded. Current cost: {current_month_cost:.2f} €.",
        )


@app.get("/api/rag/collections")
async def get_rag_collections():
    return {"collections": rag_manager.list_collections()}


@app.get("/api/rag/indexing-status")
async def get_indexing_status():
    return RAG_INDEXING_STATUS


@app.post("/api/rag/index-folder")
async def index_folder(request: RagFolderRequest):
    if RAG_INDEXING_STATUS["in_progress"]:
        raise HTTPException(status_code=409, detail="Eine Indexierung läuft bereits.")

    try:
        RAG_INDEXING_STATUS.update(
            {
                "in_progress": True,
                "total_files": 0,
                "processed_files": 0,
                "message": "Indexierung wird gestartet...",
            }
        )
        asyncio.create_task(
            asyncio.to_thread(
                rag_manager.process_and_index_folder,
                request.path,
                RAG_INDEXING_STATUS,
                request.collection_name,
            )
        )
        return {"message": "Indexierung gestartet."}
    except Exception as e:
        RAG_INDEXING_STATUS["in_progress"] = False
        logger.error(f"Fehler beim Start der Ordner-Indexierung: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Fehler beim Start der Indexierung."
        )


def is_creative_writing_request(prompt: str) -> bool:
    """
    Prüft, ob ein Prompt eine kreative Schreibaufgabe ist.
    Ein Befehl zum Speichern ist KEINE kreative Aufgabe.
    """
    prompt_lower = prompt.lower().strip()
    creative_keywords = [
        "schreib", "erzähl", "dichte", "gedicht", "geschichte", "haiku",
        "erfinde", "reime", "songtext", "ballade", "märchen", "dialog"
    ]
    # Die Anfrage ist nur kreativ, wenn sie mit einem dieser Wörter BEGINNT.
    return any(prompt_lower.startswith(keyword) for keyword in creative_keywords)

# --- GOLD STANDARD SWITCH IMPLEMENTATION ---
async def handle_chat_request(
    request: ChatRequest,
    db: Session,
    context_manager: ContextManager,
    model_catalog: dict,
):
    # --- START: Adapt for new content structure ---
    user_prompt_text = ""
    image_data = None
    llm_response = {}

    if request.content:
        for part in request.content:
            if part.type == "text":
                user_prompt_text = part.text
            elif part.type == "image_url" and part.image_url:
                image_data = part.image_url
        if not user_prompt_text:
            user_prompt_text = "Analyze the image."
    elif request.prompt:
        user_prompt_text = request.prompt

    if not user_prompt_text:
        raise HTTPException(status_code=400, detail="No prompt provided.")

    user_prompt_text = user_prompt_text.encode("utf-8").decode("utf-8")

    api_key = keyring.get_password("Janus-Projekt", request.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key not found.")

    check_budget_and_raise_if_exceeded(db)

    is_new_chat = False
    if request.chat_id is None:
        is_new_chat = True
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")

    messages_in_chat_from_db = crud.get_messages_by_chat_id(db, request.chat_id)

    if not image_data:
        logger.info("No new image uploaded. Checking history for existing image context.")
        load_image_from_history = False
        is_explicitly_related = _is_explicitly_image_related_task(user_prompt_text)
        is_explicitly_unrelated = _is_image_unrelated_task(user_prompt_text)

        if is_explicitly_related:
            load_image_from_history = True
            logger.info("Explicit image-related prompt detected. Forcing visual context.")
        elif not is_explicitly_unrelated:
            load_image_from_history = True
        else:
            logger.info("Task-oriented prompt detected (file ops/web search). Suppressing visual context.")

        if load_image_from_history:
            most_recent_image_path_relative = _get_most_recent_image_path_from_history(messages_in_chat_from_db)
            if most_recent_image_path_relative:
                try:
                    base_image_dir = os.path.join(get_app_data_dir(), "images")
                    image_filename = most_recent_image_path_relative.replace("/user_images/", "")
                    full_image_path = os.path.join(base_image_dir, image_filename)
                    if os.path.exists(full_image_path):
                        logger.info(f"Reloading previous image: {full_image_path}")
                        with open(full_image_path, "rb") as f:
                            encoded_string = base64.b64encode(f.read()).decode("utf-8")
                            image_data = f"data:image/png;base64,{encoded_string}"
                    else:
                        logger.warning(f"Image path in history, but file not found: {full_image_path}")
                except Exception as e:
                    logger.error(f"Error reloading image from history: {e}", exc_info=True)
                    image_data = None

    local_user_image_path = None
    if request.content and any(part.type == "image_url" for part in request.content):
        try:
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            local_user_image_path = image_manager.save_image_from_bytes(
                image_bytes, description="user-upload", subdirectory="uploads"
            )
            logger.info(f"User-uploaded image saved to: {local_user_image_path}")
        except Exception as e:
            logger.error(f"Could not save user-uploaded image: {e}", exc_info=True)
            local_user_image_path = None

    crud.create_message(
        db, chat_id=request.chat_id, sender="user", content=user_prompt_text, image_path=local_user_image_path
    )

    config = load_config()
    personalities = load_personalities()
    active_personality_id = config.get("active_personality", "ai_assistant")
    system_message = None
    for p in personalities:
        if p.get("id") == active_personality_id:
            persona_prompt = p.get("prompt")
            if persona_prompt:
                # ... [Persona-Prompt Erstellung bleibt gleich] ...
                system_message = {"role": "system", "content": persona_prompt}
                logger.info(f"Using persona prompt for '{active_personality_id}'")
            break

    messages_in_chat = crud.get_messages_by_chat_id(db, request.chat_id)
    image_data = None
    llm_response = {}  # Initialize llm_response to prevent UnboundLocalError
    
    # Get active personality
    config = load_config()
    active_personality_id = config.get("active_personality", "ai_assistant")

    if request.content:
        # New format with content list
        for part in request.content:
            if part.type == "text":
                user_prompt_text = part.text
            elif part.type == "image_url" and part.image_url:
                image_data = part.image_url  # This is the data URI

        # Fallback if no text part is found
        if not user_prompt_text:
            user_prompt_text = "Analyze the image."

    elif request.prompt:
        # Old format with just a prompt string
        user_prompt_text = request.prompt

    if not user_prompt_text:
        raise HTTPException(status_code=400, detail="No prompt provided.")

    # Defensive fix for encoding issues.
    user_prompt_text = user_prompt_text.encode("utf-8").decode("utf-8")
    # --- END: Adapt for new content structure ---

    async def _extract_entities(text: str) -> List[str]:
        # Simple, aber effektive Entitäten-Extraktion: Alle Wörter, die mit einem Großbuchstaben beginnen.
        # Dies fängt Namen und wichtige Substantive ab.
        entities = re.findall(r"\b[A-Z][a-z]*\b", text)
        return list(set(entities))  # 'set' entfernt Duplikate

    api_key = keyring.get_password("Janus-Projekt", request.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key not found.")

    check_budget_and_raise_if_exceeded(db)

    # --- NEUE LOGIK START ---
    is_new_chat = False
    if request.chat_id is None:
        is_new_chat = True
        new_chat = crud.create_chat(db, title="New Chat")
        request.chat_id = new_chat.id
        logger.info(f"New chat created with ID: {request.chat_id}")
    # --- NEUE LOGIK ENDE ---

    # Lade den Verlauf einmal, um ihn mehrfach zu verwenden
    messages_in_chat_from_db = crud.get_messages_by_chat_id(db, request.chat_id)

    # --- START: VISUELLES GEDÄCHTNIS (v2) ---
    # Wenn kein NEUES Bild hochgeladen wird, prüfen wir, ob ein ALTES im Verlauf existiert.
    if not image_data:
        logger.info(
            "No new image uploaded. Checking history for existing image context."
        )

        # Logik: Lade das letzte Bild, es sei denn, die Aufgabe verbietet es explizit.
        # Eine explizite Bild-Frage hat dabei immer Vorrang.

        load_image_from_history = False
        is_explicitly_related = _is_explicitly_image_related_task(user_prompt_text)
        is_explicitly_unrelated = _is_image_unrelated_task(user_prompt_text)

        if is_explicitly_related:
            # Wenn der User explizit nach dem Bild fragt, laden wir es auf jeden Fall.
            load_image_from_history = True
            logger.info(
                "Explicit image-related prompt detected. Forcing visual context."
            )
        elif not is_explicitly_unrelated:
            # Wenn es keine explizit bild-fremde Aufgabe ist, laden wir es als Standardkontext.
            load_image_from_history = True
        else:
            # Nur wenn es eine explizit bild-fremde Aufgabe ist, unterdrücken wir das Laden.
            logger.info(
                "Task-oriented prompt detected (file ops/web search). Suppressing visual context to ensure tool usage."
            )

        if load_image_from_history:
            most_recent_image_path_relative = _get_most_recent_image_path_from_history(
                messages_in_chat_from_db
            )
            if most_recent_image_path_relative:
                try:
                    # Baue den vollständigen, absoluten Pfad zum Bild
                    base_image_dir = os.path.join(get_app_data_dir(), "images")
                    image_filename = most_recent_image_path_relative.replace(
                        "/user_images/", ""
                    )
                    full_image_path = os.path.join(base_image_dir, image_filename)

                    if os.path.exists(full_image_path):
                        logger.info(
                            f"Image context is relevant. Reloading previous image: {full_image_path}"
                        )
                        with open(full_image_path, "rb") as f:
                            encoded_string = base64.b64encode(f.read()).decode("utf-8")
                            image_data = f"data:image/png;base64,{encoded_string}"
                    else:
                        logger.warning(
                            f"Image path found in history, but file does not exist: {full_image_path}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error reloading image from history: {e}", exc_info=True
                    )
                    image_data = None
    # --- ENDE: VISUELLES GEDÄCHTNIS (v2) ---

    # --- START: Save user-uploaded image and persist its path ---
    local_user_image_path = None
    if request.content and any(part.type == "image_url" for part in request.content):
        # Wir speichern nur, wenn in der ursprünglichen Anfrage ein Bild war
        try:
            # The image_manager can save the image and return a local path
            # We need to extract the raw base64 data from the data URI
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            # Use a generic description for user-uploaded images
            local_user_image_path = image_manager.save_image_from_bytes(
                image_bytes, description="user-upload", subdirectory="uploads"
            )
            logger.info(f"User-uploaded image saved to: {local_user_image_path}")
        except Exception as e:
            logger.error(f"Could not save user-uploaded image: {e}", exc_info=True)
            local_user_image_path = (
                None  # Continue without the image path if saving fails
            )

    crud.create_message(
        db,
        chat_id=request.chat_id,
        sender="user",
        content=user_prompt_text,
        image_path=local_user_image_path,
    )
    # --- END: Save user-uploaded image ---

    config = load_config()
    personalities = load_personalities()  # Lade aus der neuen Datei
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
                    "**WERKZEUGNUTZUNGS-DIREKTIVE:** Deine primäre Informationsquelle ist die **FAKTENGRUNDLAGE**. "
                    "Wenn eine Frage nach aktuellen Informationen (nach 2023), Preisen, Personen oder spezifischen Fakten gestellt wird, "
                    "prüfe **ZUERST**, ob die Antwort bereits in der FAKTENGRUNDLAGE enthalten ist. "
                    "**WENN DIE FAKTENGRUNDLAGE KEINE ANTWORT LIEFERT ODER DIE INFORMATIONEN VERALTET SIND**, "
                    "MUSST du das 'perform_websearch'-Werkzeug benutzen, um die Information zu finden. "
                    "Antworte NIEMALS aus deinem internen Wissen, wenn eine Websuche eine aktuellere oder präzisere Antwort liefern kann."
                )
                
                # --- START: NEUE, ENTSCHEIDENDE REGEL ---
                fact_directive = (
                    "**FAKTEN-DIREKTIVE:** Wenn dir unter 'FAKTENGRUNDLAGE' Informationen bereitgestellt werden, "
                    "basiere deine Antwort **primär** auf diesen Fakten. Fasse sie nicht ungefragt zusammen, "
                    "sondern nutze sie, um die Anfrage des Benutzers intelligent zu beantworten. "
                    "Wenn die Anfrage nur einen Teil der Fakten betrifft (z.B. eine Filterung einer Liste), "
                    "antworte nur mit den relevanten Informationen und nicht mit der gesamten Liste."
                )
                # --- ENDE: NEUE, ENTSCHEIDENDE REGEL ---

                import re

                # Füge BEIDE Direktiven zum Prompt hinzu
                if "**Werkzeugnutzung:**" in persona_prompt:
                    # Ersetze die alte, allgemeine Anweisung
                    persona_prompt = re.sub(
                        r"\*\*Werkzeugnutzung:\*\*.*",
                        f"{tool_directive}\n{fact_directive}",
                        persona_prompt,
                        flags=re.DOTALL,
                    )
                else:
                    # Füge die Anweisungen hinzu, falls sie fehlen
                    persona_prompt += f"\n\n{tool_directive}\n\n{fact_directive}"

                logger.info(
                    "Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet."
                )
                system_message = {"role": "system", "content": persona_prompt}
                logger.info(f"Using persona prompt for '{active_personality_id}'")
            break

    # Load chat history once to be used by multiple parts of the logic
    messages_in_chat = crud.get_messages_by_chat_id(db, request.chat_id)

    # --- START: Final, Robust Image Generation Intent Logic (v5 - mit Tool-Priorisierung) ---
    is_image_generation_request = False
    prompt_lower = user_prompt_text.lower()

    # NEU: Prüfe ZUERST auf explizite Befehle zur Werkzeugnutzung, die NICHT Bildgenerierung sind.
    # Dies verhindert, dass "mach eine PDF mit einem bild" fälschlicherweise als Bildgenerierung erkannt wird.
    explicit_tool_keywords = ["pdf", "datei", "file", "ordner", "folder", "suche", "search"]
    is_explicit_tool_request = any(keyword in prompt_lower for keyword in explicit_tool_keywords)

    if not is_explicit_tool_request:
        # Nur wenn es KEIN expliziter Befehl für ein anderes Werkzeug ist, prüfen wir auf Bildgenerierung.

        # Keywords that explicitly mean "create a new image" (from scratch)
        explicit_creation_keywords = [
            "zeichne", "draw", "male", "paint", "erzeuge", "generate",
        ]

        # Keywords that explicitly mean "edit an existing image" (requires image_data or reference_image_path)
        explicit_editing_keywords = [
            "ändere", "änder", "change", "ersetze", "replace", "mach", "make",
            "füge", "add", "soll", "tragen", "mit", "statt", "verwandle",
            "gib ihr", "gib ihm", "lass", "setze",
        ]
        
        # Scenario 1: User wants to create a brand new image (no image_data, explicit creation keyword)
        if image_data is None and any(
            keyword in prompt_lower for keyword in explicit_creation_keywords
        ):
            is_image_generation_request = True
        # Scenario 2: User wants to edit an existing image (image_data present, explicit editing keyword)
        elif image_data is not None and any(
            keyword in prompt_lower for keyword in explicit_editing_keywords
        ):
            is_image_generation_request = True
        # Scenario 3: User wants to create a new image with ambiguous keywords (no image_data, no image in history)
        elif (
            image_data is None
        ): 
            ambiguous_creation_keywords = [
                "erstelle", "erstell", "create", "bild", "image", "picture", "foto", "photo",
            ]
            conversation_has_image = any(
                msg.image_path is not None for msg in messages_in_chat
            )
            if not conversation_has_image and any(
                keyword in prompt_lower for keyword in ambiguous_creation_keywords
            ):
                is_image_generation_request = True

    # Der Rest der Logik (is_image_analysis_request) bleibt gleich.
    is_image_analysis_request = (
        image_data is not None and not is_image_generation_request
    )
    # --- ENDE: Final, Robust Image Generation Intent Logic (v5) ---
    if is_image_generation_request:
        logger.info("Image generation intent detected by keyword.")

        # --- START: Multi-turn logic ---
        previous_response_id = LAST_RESPONSE_ID_PER_CHAT.get(request.chat_id)

        # For iterative generation, we must use the OpenAI provider.
        provider_for_gen = request.provider

        # The model used for the new Responses API is a chat model, not a dall-e model.
        selected_text_model = model_catalog.get(request.model, {})
        image_model_id = selected_text_model.get(
            "image_generation_model", "gpt-4o"
        )  # Fallback to gpt-4o

        # --- START: Image-to-Image Context Logic ---
        reference_image_path = None
        # The check for conversation_has_image is already done when detecting intent.
        # We can find the latest image path from the messages we already fetched.
        # Iterate in reverse to find the most recent image.
        for msg in reversed(messages_in_chat):
            if msg.image_path:
                reference_image_path = msg.image_path
                logger.info(
                    f"Found reference image for image-to-image task: {reference_image_path}"
                )
                break

        llm_response = await llm_gateway.generate_image(
            provider=provider_for_gen,
            model_id=image_model_id,
            api_key=api_key,
            prompt=user_prompt_text,
            previous_response_id=previous_response_id,
            reference_image_path=reference_image_path,  # Pass the new parameter
        )
        # --- END: Image-to-Image Context Logic ---

        # Store the new response ID for the next turn, or clear if no image was returned
        if (
            request.chat_id
            and llm_response.get("response_id")
            and llm_response.get("image_url")
        ):
            LAST_RESPONSE_ID_PER_CHAT[request.chat_id] = llm_response["response_id"]
        elif request.chat_id in LAST_RESPONSE_ID_PER_CHAT:
            # If the model returned text or an error, the chain is broken. Clear the ID.
            del LAST_RESPONSE_ID_PER_CHAT[request.chat_id]
        # --- END: Multi-turn logic ---

        # Handle the response, which could be an image or text
        final_answer = ""
        local_image_path = None

        if llm_response.get("type") == "text":
            final_answer = llm_response.get(
                "text", "Die Anfrage zur Bild-Generierung ergab eine Text-Antwort."
            )
        elif llm_response.get("image_url"):
            # The image is already saved by the provider service, and a local path is returned.
            local_image_path = llm_response.get("image_url")
            final_answer = f"Bild wurde erfolgreich mit {provider_for_gen.capitalize()} modifiziert/generiert."
        else:
            final_answer = (
                f"Fehler bei der {provider_for_gen.capitalize()}-Bildgenerierung."
            )

        usage = llm_response.get("usage", {})
        cost = llm_response.get("cost", {})

        crud.create_message(
            db,
            chat_id=request.chat_id,
            sender="model",
            content=final_answer,
            image_path=local_image_path,
        )
        if usage and cost.get("total_cost", 0) > 0:
            cost_model = llm_response.get("usage", {}).get("model", image_model_id)
            database.save_cost_entry(
                date=datetime.now(),
                model=cost_model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                image_quality=usage.get("image_quality"),
                image_cost=cost.get("image_cost", 0),
                total_cost=cost.get("total_cost", 0),
            )
        return {"sender": "model", "text": final_answer, "image_url": local_image_path}

    else:
        # It's not an image generation request, so clear the stored ID for this chat
        if request.chat_id in LAST_RESPONSE_ID_PER_CHAT:
            del LAST_RESPONSE_ID_PER_CHAT[request.chat_id]

    # Lade den Chat-Verlauf, ABER wende eine spezielle Logik für Identitätsfragen an
    chat_history = []

    # Lade den Verlauf nur, wenn es KEINE Identitätsfrage ist UND es KEINE reine Bildanalyse ist
    if not is_identity_query(user_prompt_text) and not is_image_analysis_request:
        # Wir verwenden die bereits geladenen Nachrichten aus messages_in_chat_from_db
        for m in messages_in_chat_from_db:
            if len(chat_history) < 20:
                chat_history.append(
                    {
                        "role": "user" if m.sender == "user" else "assistant",
                        "content": m.content,
                    }
                )
    else:
        # Für Identitätsfragen oder reine Bildanalyse: Lasse den Verlauf leer, um die Persona zu erzwingen.
        # Oder um das Modell auf die Bildanalyse zu fokussieren.
        if is_identity_query(user_prompt_text):
            logger.info(
                "Identity query detected. Using a clean context to reinforce persona."
            )
        elif is_image_analysis_request:
            logger.info(
                "Pure image analysis request detected. Suppressing chat history for focused analysis."
            )
        # WICHTIG: Füge hier nur die aktuelle User-Frage hinzu (wird später hinzugefügt).
        # chat_history bleibt hier leer, wenn es eine Identitätsfrage oder Bildanalyse ist.

    user_name = None
    memory_context = ""
    system_context = ""  # <-- DIESE ZEILE HINZUFÜGEN
    if not is_greeting(user_prompt_text) and not is_identity_query(user_prompt_text):
        # === GOLD STANDARD HYBRID CONTEXT BUILDER V4 (CLUSTER-LOGIK) ===
        user_name = crud.get_user_name(db)

        # 1. Lade immer alle Fakten aus dem aktuellen Chat.
        final_snippets_map = {
            mem.id: mem for mem in crud.get_memory_by_chat_id(db, request.chat_id)
        }
        
        # --- NEUER BLOCK START: Proaktives Laden für neue Chats ---
        if is_new_chat:
            logger.info("New chat detected. Proactively searching for relevant context from past chats.")
            all_past_memories_for_new_chat = memory_manager.get_all_searchable_memories(db)
            if all_past_memories_for_new_chat:
                relevant_past_snippets = vector_service.find_similar_snippets(
                    user_prompt_text, all_past_memories_for_new_chat, top_k=5
                )
                for mem in relevant_past_snippets:
                    if mem.id not in final_snippets_map:
                         final_snippets_map[mem.id] = mem
                         logger.info(f"Proactively loaded fact for new chat: '{mem.snippet}'")
        # --- NEUER BLOCK ENDE ---

        # 2. Finde relevante Fakten in alten Chats über eine mehrstufige Cluster-Suche.
        all_past_memories = [
            mem
            for mem in memory_manager.get_all_searchable_memories(db)
            if mem.chat_id != request.chat_id
        ]

        if all_past_memories:
            # STUFE A: Finde die "Anker"-Fakten, die am relevantesten zur Frage sind.
            semantic_anchors = vector_service.find_similar_snippets(
                user_prompt_text, all_past_memories, top_k=5
            )

            # STUFE B: Extrahiere alle Namen (Entitäten) aus den Anker-Fakten UND dem aktuellen User-Prompt.
            import re

            relevant_entities = set()
            if user_name:
                relevant_entities.add(user_name)

            # NEU: Entitäten auch aus der aktuellen Benutzeranfrage extrahieren.
            # Das macht die Relevanzerkennung deutlich robuster.
            entities_in_prompt = re.findall(r"\b[A-Z][a-z]+\b", user_prompt_text)
            for entity in entities_in_prompt:
                relevant_entities.add(entity)

            for anchor in semantic_anchors:
                if hasattr(anchor, "snippet"):
                    entities_in_snippet = re.findall(r"\b[A-Z][a-z]+\b", anchor.snippet)
                    for entity in entities_in_snippet:
                        relevant_entities.add(entity)

            logger.info(
                f"Identifizierte relevante Entitäten für Kontext-Cluster: {relevant_entities}"
            )

            # STUFE C: Lade ALLE Fakten, die eine dieser relevanten Entitäten enthalten.
            if relevant_entities:
                for mem in all_past_memories:
                    if hasattr(mem, "snippet"):
                        if any(entity in mem.snippet for entity in relevant_entities):
                            key = (
                                mem.id
                                if hasattr(mem, "id") and mem.source == "stm"
                                else f"ltm_{mem.original_memory_id}"
                            )
                            if key not in final_snippets_map:
                                final_snippets_map[key] = mem

        final_snippets = list(final_snippets_map.values())

        promoted_snippets = []
        for mem in final_snippets:
            if hasattr(mem, "source") and mem.source == "ltm":
                logger.info(
                    f"Relevanter Fakt im LTM gefunden: '{mem.snippet}'. Befördere zu STM."
                )
                promoted_memory = memory_manager.promote_ltm_to_stm(db, mem)
                if promoted_memory:
                    promoted_snippets.append(promoted_memory)
            else:
                promoted_snippets.append(mem)
        final_snippets = promoted_snippets

        memory_context = "\n".join([f"- {mem.snippet}" for mem in final_snippets])
        logger.info(
            f"[DEBUG] FINAL HYBRID Memory Context Generated (length: {len(memory_context)}): {memory_context[:1500]}"
        )

        for mem in final_snippets:
            if hasattr(mem, "id") and isinstance(mem, database.Memory):
                memory_manager.touch_memory_snippet(db, mem.id)
        logger.info(
            f"Touched {len(final_snippets)} memory snippets to update their relevance."
        )

        # --- ÄNDERUNG START: System-Kontext von Fakten trennen ---
        if not is_identity_query(user_prompt_text):
            allowed_workspaces = filesystem_manager._get_allowed_workspaces()
            if allowed_workspaces:
                system_context += "\n\n--- SYSTEM-KONTEXT (Verfügbare Arbeitsbereiche) ---\n"
                for ws in allowed_workspaces:
                    system_context += f"- {ws.name}: {ws}\n"

            if FILE_OPERATION_HISTORY:
                if not system_context:
                    system_context += "\n\n--- SYSTEM-KONTEXT ---\n"
                system_context += "\n--- Letzte Dateioperationen ---\n"
                for op in FILE_OPERATION_HISTORY:
                    system_context += f"- {op}\n"
        # --- ÄNDERUNG ENDE ---

    # --- NEUE PROMPT-ASSEMBLIERUNG (Struktureller Fix) ---
    messages_for_llm = []
    
    # 1. Starte mit dem Basis-System-Prompt (Persona)
    if system_message and not is_image_analysis_request:
        
        # --- START DER KORREKTUR V3 (Kontext für Folgefragen) ---
        # Prüfe, ob die AKTUELLE oder die LETZTE User-Nachricht eine Identitäts- oder Feature-Frage war.
        # Dies hält die KI für mindestens eine Runde im "konzeptionellen Modus".
        is_conceptual_conversation = is_identity_query(user_prompt_text) or is_feature_suggestion_query(user_prompt_text)
        if not is_conceptual_conversation and chat_history:
            # Holen der letzten User-Nachricht aus dem Verlauf
            last_user_message = next((msg['content'] for msg in reversed(chat_history) if msg['role'] == 'user'), None)
            if last_user_message:
                is_conceptual_conversation = is_identity_query(last_user_message) or is_feature_suggestion_query(last_user_message)

        if is_conceptual_conversation:
            if is_identity_query(user_prompt_text):
                logger.info("Identity query detected. Stripping tool directives from system prompt.")
            else:
                logger.info("Conceptual conversation context (identity or feature) detected. Stripping tool directives.")

            prompt_content = system_message['content']
            prompt_content = re.sub(r'\*\*WERKZEUGNUTZUNGS-DIREKTIVE:\*\*.*', '', prompt_content, flags=re.DOTALL)
            prompt_content = re.sub(r'\*\*FAKTEN-DIREKTIVE:\*\*.*', '', prompt_content, flags=re.DOTALL)
            system_message['content'] = prompt_content.strip()
        # --- ENDE DER KORREKTUR V3 ---

        # Baue den erweiterten System-Kontext
        system_context_parts = [system_message['content']]
        
        if memory_context:
            system_context_parts.append(f"**WICHTIG: Nutze die folgenden Fakten als Grundlage für deine Antwort.**\n--- FAKTENGRUNDLAGE ---\n{memory_context}")
        
        if system_context:
            system_context_parts.append(system_context)
            
        # Kombiniere alles zu einem einzigen, reichen System-Prompt
        system_message['content'] = "\n\n".join(system_context_parts)
        messages_for_llm.append(system_message)

    # 2. Füge den Chat-Verlauf hinzu
    messages_for_llm.extend(chat_history)

    # 3. Füge die saubere, unveränderte User-Nachricht hinzu
    if image_data:
        # Mehrteilige Nachricht für Bild und Text
        user_content = [
            {"type": "text", "text": user_prompt_text},
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data
                },
            }
        ]
        messages_for_llm.append({"role": "user", "content": user_content})
    else:
        # Reine Text-Nachricht
        messages_for_llm.append({"role": "user", "content": user_prompt_text})

    # Übergebe den Kontext und den Benutzernamen an die Logik-Funktion
    final_answer = ""
    local_image_path = None
    usage = {}
    cost = {}
    response_type = "text"  # Default to text for creative writer

    final_answer = ""
    local_image_path = None
    usage = {}
    cost = {}
    response_type = "text"

    is_creative_request = is_creative_writing_request(user_prompt_text)

    # Die intelligente Weiche
    if active_personality_id == "creative_writer" and is_creative_request:
        logger.info("Creative Writer persona active for creative task. Calling creative_writer pipeline.")
        creative_style = _extract_creative_style(user_prompt_text)
        logger.info(f"Creative Writer - Extracted style: {creative_style}")
        try:
            ssml_answer = await creative_writer(
                user_prompt_text,
                provider=request.provider,
                model=request.model,
                api_key=api_key,
                style=creative_style,
            )
            # Store the original SSML response
            LAST_SSML_RESPONSE_PER_CHAT[request.chat_id] = ssml_answer
            # Clean the SSML for display
            final_answer = re.sub(r'<[^>]+>', '', ssml_answer)

        except Exception as e:
            logger.error(f"Error in creative writing pipeline: {e}", exc_info=True)
            final_answer = "Entschuldigung, beim Verarbeiten deiner kreativen Anfrage ist ein Fehler aufgetreten. Bitte versuche es später erneut."
        
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "model": request.model}
        cost = {"total_cost": 0}
    else:
        if active_personality_id == "creative_writer" and not is_creative_request:
            logger.info("Creative Writer persona performing a tool-based or follow-up action.")

        # KORREKTUR: Hier wird die korrekte Funktion `reason_and_respond` aufgerufen.
        llm_response = await llm_gateway.reason_and_respond(
            user_prompt=user_prompt_text,
            chat_history=messages_for_llm, # Stellen Sie sicher, dass `messages_for_llm` hier korrekt befüllt ist
            memory_context=memory_context, # Stellen Sie sicher, dass `memory_context` hier korrekt befüllt ist
            db=db,
            api_key=api_key,
            model=request.model,
            provider=request.provider,
            context_manager=context_manager,
            user_name=user_name,
            chat_id=request.chat_id,
            image_data=image_data,
            is_image_analysis_request=is_image_analysis_request,
            disable_tools=is_conceptual_conversation,
        )
        # Der Rest des Codes zur Verarbeitung der `llm_response` bleibt exakt so wie er war.
        usage = llm_response.get("usage", {})
        cost = llm_response.get("cost", {})
        response_type = llm_response.get("type")
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
            image_data=image_data,
            is_image_analysis_request=is_image_analysis_request,
            disable_tools=is_conceptual_conversation,  # NEU
        )
        usage = llm_response.get("usage", {})
        cost = llm_response.get("cost", {})
        response_type = llm_response.get("type")
        
        # Handle both single tool call and list of tool calls
        if response_type in ("tool_code", "tool_code_list"):
            # Normalize to single tool call for backward compatibility
            if response_type == "tool_code_list":
                tool_calls = llm_response.get("tool_calls", [])
                if not tool_calls:
                    logger.error("tool_code_list received but no tool_calls found")
                    final_answer = "Ein unerwarteter Fehler ist aufgetreten."
                    response_type = "error"
                else:
                    # For now, handle only the first tool call (multi-tool not yet supported)
                    first_call = tool_calls[0]
                    llm_response["tool_name"] = first_call.get("tool_name")
                    llm_response["tool_args"] = first_call.get("tool_args", {})
                    response_type = "tool_code"  # Normalize
                    logger.info(f"Normalized tool_code_list to tool_code: {llm_response['tool_name']}")
            
        if response_type == "tool_code":
            tool_name = llm_response.get("tool_name")
            tool_args = llm_response.get("tool_args", {})
            logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")

            # ================================================================
            # START: KORREKTURLOGIK FÜR save_mp3_tool (Ticket TTS-001)
            # ================================================================
            if tool_name == "save_mp3_tool":
                # Lade die letzte SSML-Antwort aus der temporären Variable
                last_ssml_content = LAST_SSML_RESPONSE_PER_CHAT.get(request.chat_id)
                
                if last_ssml_content:
                    logger.info("Korrektur für 'save_mp3_tool': Überschreibe 'content' mit dem zwischengespeicherten SSML-Text.")
                    # Überschreibe den (falschen) Inhalt vom LLM mit dem korrekten, vollständigen SSML-Text
                    tool_args['content'] = last_ssml_content
                else:
                    logger.warning("Konnte keine zwischengespeicherte SSML-Antwort finden, um den Inhalt für TTS zu extrahieren.")
            # ================================================================
            # ENDE: KORREKTURLOGIK FÜR save_mp3_tool
            # ================================================================

            # --- ROBUSTE LOGIK FÜR PDF-WERKZEUG (v2) ---
            if tool_name == "create_pdf_from_markdown":
                # Wir prüfen auf ZWEI Bedingungen:
                # 1. Hat das LLM den Flag korrekt gesetzt?
                # 2. ODER hat der Benutzer explizit Wörter wie "bild" oder "foto" im Prompt verwendet?
                # This makes the system robust against LLM errors.
                user_prompt_lower = user_prompt_text.lower()
                image_keywords_in_prompt = any(keyword in user_prompt_lower for keyword in ["bild", "foto", "photo", "image", "screenshot"])

                if tool_args.get("include_image") or image_keywords_in_prompt:
                    logger.info("PDF tool: Anforderung zum Einfügen eines Bildes erkannt (durch Flag oder Keyword).")
                    
                    # Finde den Pfad des letzten Bildes im aktuellen Chat
                    messages_in_chat = crud.get_messages_by_chat_id(db, request.chat_id)
                    last_image_path = None
                    for message in reversed(messages_in_chat):
                        if message.image_path:
                            # Baue den vollständigen, absoluten Pfad zum Bild
                            base_image_dir = os.path.join(get_app_data_dir(), "images")
                            image_filename = os.path.basename(message.image_path)
                            last_image_path = os.path.join(base_image_dir, image_filename)
                            break

                    if last_image_path and os.path.exists(last_image_path):
                        logger.info(f"Letztes Bild gefunden: {last_image_path}")
                        # Füge den echten Bildpfad zu den Argumenten hinzu
                        tool_args["image_path"] = last_image_path
                    else:
                        logger.warning(
                            "Kein Bild im Chatverlauf gefunden, um es zur PDF hinzuzufügen."
                        )

                # Entferne das 'include_image'-Argument, da die Python-Funktion es nicht kennt
                if "include_image" in tool_args:
                    del tool_args["include_image"]
            # --- ENDE DER ROBUSTEn LOGIK ---

            tool = TOOL_REGISTRY.get(tool_name)
            tool_output_raw = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."
            if tool:
                all_possible_args = {"api_key": api_key, "db": db, **tool_args}
                tool_func_params = inspect.signature(tool.func).parameters
                final_tool_args = {
                    name: all_possible_args[name]
                    for name in tool_func_params
                    if name in all_possible_args
                }
                if inspect.iscoroutinefunction(tool.func):
                    tool_output_raw = await tool.func(**final_tool_args)
                else:
                    tool_output_raw = tool.func(**final_tool_args)
                if "file" in tool_name or "directory" in tool_name:
                    op_string = f"{tool_name} with args {tool_args}"
                    FILE_OPERATION_HISTORY.append(op_string)
                    if len(FILE_OPERATION_HISTORY) > 5:
                        FILE_OPERATION_HISTORY.pop(0)
                if tool_name == "perform_websearch" and isinstance(
                    tool_output_raw, dict
                ):
                    logger.info(
                        "Web search completed. Sending results back to the original LLM for final response."
                    )
                    web_search_text = tool_output_raw.get(
                        "text", "Keine Ergebnisse gefunden."
                    )
                    web_search_urls = tool_output_raw.get("urls", [])

                    # NEU: Websuchkosten speichern
                    websearch_usage = tool_output_raw.get("usage", {})
                    websearch_cost = tool_output_raw.get("cost", {})
                    if websearch_cost.get("total_cost", 0) > 0:
                        database.save_cost_entry(
                            date=datetime.now(),
                            model="websearch", # Fester model_id für Websuche
                            input_tokens=websearch_usage.get("query_count", 0), # query_count als input_tokens
                            output_tokens=0, # NEU: Standardwert für Websuche
                            image_quality=None, # NEU: Standardwert für Websuche
                            image_cost=0, # NEU: Standardwert für Websuche
                            total_cost=websearch_cost.get("total_cost", 0),
                        )
                    summarization_prompt = (
                        "Hier sind die Ergebnisse einer Websuche. Formuliere basierend auf diesen Informationen eine klare und hilfreiche Antwort auf die ursprüngliche Frage des Benutzers. "
                        "Gib am Ende deiner Antwort einen Abschnitt 'Quellen:' an und liste dort die gefundenen URLs auf.\n\n"
                        f"Ursprüngliche Frage: '{user_prompt_text}'\n\n"
                        f"--- Suchergebnisse ---\n{web_search_text}\n\n"
                        f"--- Gefundene URLs ---\n"
                        + "\n".join([f"- {url}" for url in web_search_urls])
                    )
                    messages_for_llm = list(chat_history)
                    messages_for_llm.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": json.dumps(tool_args),
                                    },
                                }
                            ],
                        }
                    )
                    messages_for_llm.append(
                        {
                            "role": "tool",
                            "tool_call_id": "call_123",
                            "name": tool_name,
                            "content": summarization_prompt,
                        }
                    )
                    final_response_from_llm = await llm_gateway.call_llm(
                        request.provider,
                        request.model,
                        api_key,
                        messages=messages_for_llm,
                        tools=None,
                    )
                    final_answer = final_response_from_llm.get(
                        "text", "Ich konnte die Suchergebnisse nicht zusammenfassen."
                    )
                    usage = final_response_from_llm.get("usage", {})
                    cost = final_response_from_llm.get("cost", {})
                else:
                    if isinstance(tool_output_raw, dict):
                        if tool_output_raw.get("url"):
                            # Das "url"-Feld vom generate_image_tool enthält bereits den LOKALEN Pfad
                            local_image_path = tool_output_raw.get("url")
                            final_answer = f"Tool '{tool_name}' erfolgreich ausgeführt. Bild wurde generiert."
                            # Das `tool_output_raw` enthält die korrekten Kosten vom Bildgenerator
                            if tool_output_raw.get("usage") and tool_output_raw.get("cost"):
                                database.save_cost_entry(
                                    date=datetime.now(),
                                    model=tool_output_raw["usage"].get("model", request.model),
                                    input_tokens=tool_output_raw["usage"].get("prompt_tokens", 0),
                                    output_tokens=tool_output_raw["usage"].get("completion_tokens", 0),
                                    image_quality=tool_output_raw["usage"].get("image_quality"), # NEU
                                    image_cost=tool_output_raw["cost"].get("image_cost", 0), # NEU
                                    total_cost=tool_output_raw["cost"].get("total_cost", 0),
                                )
                            return {
                                "sender": "model",
                                "text": final_answer,
                                "image_url": local_image_path,
                            }
                        else:
                            final_answer = f"Ergebnis von Tool '{tool_name}': {json.dumps(tool_output_raw, indent=2)}"
                    else:
                        final_answer = (
                            f"Ergebnis von Tool '{tool_name}': {str(tool_output_raw)}"
                        )
                    usage = llm_response.get("usage", {})
                    cost = llm_response.get("cost", {})
            else:
                final_answer = f"Fehler: Unbekanntes Tool '{tool_name}' angefordert."
                logger.error(final_answer)
                usage = {}
                cost = {}
            # --- ENDE KOPIEREN/VERSCHIEBEN ---
        elif response_type == "text":
            final_answer = llm_response.get("text") or ""
    # =========================================================================
    # --- START: HIER DEN AUSGESCHNITTENEN BLOCK EINFÜGEN ---
    # Diese Logik wird jetzt für JEDE finale Antwort ausgeführt.
    # =========================================================================
    # Prüfen, ob der User-Input eine Bestätigung war.
    if is_confirmation(user_prompt_text):
        logger.info(
            "Confirmation detected. Attempting to promote the last AI deduction into a fact."
        )
        messages_before_this_turn = crud.get_messages_by_chat_id(
            db, request.chat_id
        )
        if messages_before_this_turn:
            last_assistant_message = messages_before_this_turn[-1]
            if last_assistant_message.sender == "model":
                logger.info(
                    f"Promoting content from last AI message: '{last_assistant_message.content}'"
                )
                asyncio.create_task(
                    memory_extractor.extract_and_save_fact(
                        db=db,
                        chat_id=request.chat_id,
                        text_block=last_assistant_message.content,
                        main_api_key=api_key,
                        provider=request.provider,
                        model=request.model,
                    )
                )

    # Standard-Faktenextraktion für den normalen Dialog
    if (
        not local_image_path
        and final_answer
        and not is_greeting(user_prompt_text)
    ):
        full_exchange_text = (
            f"User: {user_prompt_text}\nAssistant: {final_answer}"
        )
        asyncio.create_task(
            memory_extractor.extract_and_save_fact(
                db=db,
                chat_id=request.chat_id,
                text_block=full_exchange_text,
                main_api_key=api_key,
                provider=request.provider,
                model=request.model,
            )
        )
    # =========================================================================
    # --- ENDE DES EINGEFÜGTEN BLOCKS ---
    # =========================================================================

    logger.info(f"Final answer before check: '{final_answer}'")
    if not final_answer and not local_image_path:
        final_answer = "Es tut mir leid, ich konnte keine passende Antwort finden. Kannst du die Frage anders formulieren?"

    crud.create_message(
        db,
        chat_id=request.chat_id,
        sender="model",
        content=final_answer,
        image_path=local_image_path,
    )

    if usage and cost.get("total_cost", 0) > 0:
        model_for_cost = usage.get("model", request.model)
        database.save_cost_entry(
            date=datetime.now(),
            model=model_for_cost,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            image_quality=usage.get("image_quality"),
            image_cost=cost.get("image_cost", 0),
            total_cost=cost.get("total_cost", 0),
        )

    config = load_config()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config(config)

    return {"sender": "model", "text": final_answer, "image_url": local_image_path}


# --- API Endpoints ---
@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    context_manager: ContextManager = Depends(get_context_manager),
    model_catalog: dict = Depends(get_model_catalog_dep),
):
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
                asyncio.create_task(
                    chat_summarizer.summarize_and_store_chat(
                        db, last_chat.id, api_key, provider, model
                    )
                )
            else:
                logger.warning(
                    f"API key for {provider} not found. Skipping chat summarization."
                )

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
        logger.error(
            f"An error occurred in the background archival task: {e}", exc_info=True
        )
    finally:
        # Diese Session wird nur einmal geschlossen, von dem Task, der als letztes fertig wird.
        # Da run_pruning meist schneller ist, wird diese hier die Session schließen.
        # Eine robustere Lösung wäre ein Counter, aber für diesen Fall ist es ausreichend.
        try:
            if db_session.is_active:
                db_session.close()
        except Exception:
            pass  # Session könnte bereits geschlossen sein


async def run_pruning(db_session: Session):
    """
    Wrapper, um die synchrone DB-Operation zum Aufräumen in einer asyncio-Task auszuführen.
    """
    logger.info("Background memory pruning task starting.")
    try:
        memory_manager.prune_expired_memories(db_session)
        logger.info("Background memory pruning task finished successfully.")
    except Exception as e:
        logger.error(
            f"An error occurred in the background pruning task: {e}", exc_info=True
        )
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
async def update_chat_title(
    chat_id: int, title_update: schemas.ChatTitleUpdate, db: Session = Depends(get_db)
):
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


@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    if not crud.delete_chat(db, chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
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
    if "model_selection" not in config:
        config["model_selection"] = {}
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
        "model": config.get("last_used_model", "gpt-4o-mini"),
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
        logger.error(
            f"Failed to save API key for {key.provider}: {e}", exc_info=True
        )  # Add exc_info=True for full traceback
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
    if (
        "filesystem_workspaces" in config
        and removal.path in config["filesystem_workspaces"]
    ):
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
        raise HTTPException(
            status_code=404,
            detail=f"Personality with id '{update.personality_id}' not found.",
        )

    config["active_personality"] = update.personality_id
    save_config(config)
    logger.info(f"Active personality set to '{update.personality_id}'")
    return {"message": f"Active personality set to {update.personality_id}"}


# --- NEUER API ENDPUNKT FÜR DIE GALERIE ---
@app.get("/api/images")
async def get_all_images():
    """
    Listet alle Bilder auf, die im 'images' Verzeichnis gespeichert sind.
    """
    image_dir = os.path.join(get_app_data_dir(), "images")
    supported_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    try:
        # Liste alle Dateien auf und filtere nach Bild-Endungen
        all_files = os.listdir(image_dir)
        image_files = [f for f in all_files if f.lower().endswith(supported_extensions)]

        # Sortiere die Bilder, die neuesten zuerst
        image_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(image_dir, x)), reverse=True
        )

        # Erstelle die vollständigen URLs, die das Frontend verwenden kann
        image_urls = [f"/user_images/{f}" for f in image_files]

        return {"images": image_urls}
    except FileNotFoundError:
        logger.warning(f"Image directory not found at: {image_dir}")
        return {"images": []}
    except Exception as e:
        logger.error(f"Error reading image directory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve images.")


import tempfile
from backend.services.speech_to_text_service import get_stt_service

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file, transcribes it using the local Whisper model,
    and returns the transcribed text.
    """
    stt_service = get_stt_service()
    if not stt_service:
        raise HTTPException(status_code=500, detail="Speech-to-text service is not available.")

    # Create a temporary file to store the uploaded audio
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        logger.error(f"Failed to create temporary audio file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not process uploaded file.")
    finally:
        file.file.close()

    try:
        # Transcribe the audio file
        transcribed_text = stt_service.transcribe_audio(tmp_path)
        if transcribed_text is None:
            raise HTTPException(status_code=500, detail="Transcription failed.")
        
        return {"transcription": transcribed_text}
    except Exception as e:
        logger.error(f"Error during transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during transcription: {e}")
    finally:
        # Clean up the temporary file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


# --- TTS API ENDPOINTS ---
from backend.services.tts_service import get_tts_service
from fastapi import Query


def is_creative_writing_request(prompt: str) -> bool:
    """Prüft, ob ein Prompt eine kreative Schreibaufgabe ist."""
    prompt_lower = prompt.lower()
    creative_keywords = [
        "schreib", "erzähl", "dichte", "gedicht", "geschichte", "haiku",
        "erfinde", "reime", "songtext", "ballade", "märchen", "dialog"
    ]
    return any(keyword in prompt_lower for keyword in creative_keywords)

@app.get("/api/tts/voices")
async def get_tts_voices(lang: Optional[str] = None):
    """Get available TTS voices, optionally filtered by language."""
    try:
        config = load_config()
        tts_service = get_tts_service(config=config)
        voices = tts_service.get_voices(lang=lang)
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error getting TTS voices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {e}")







@app.post("/api/tts/synthesize")
async def synthesize_speech(
    text: str,
    lang: str = Query("de"),
    # Die folgenden Parameter sind jetzt optional, da wir sie aus der Persönlichkeit holen
    voice_id: Optional[str] = None,
    speed: Optional[float] = None,
    fmt: str = Query("mp3"),
    provider: Optional[str] = None,
    stream: bool = False
):
    """
    Synthesize speech from text using TTS. The voice and speed are now
    primarily determined by the active personality's settings.
    """
    try:
        config = load_config()
        personalities = load_personalities()
        openai_api_key = keyring.get_password("Janus-Projekt", "openai")
        if not openai_api_key:
            logger.warning("OpenAI API key not found in keyring. OpenAI TTS might not work.")
        
        tts_service = get_tts_service(config, openai_api_key)

        # --- NEUE LOGIK: Lade TTS-Einstellungen aus der aktiven Persönlichkeit ---
        active_personality_id = config.get("active_personality", "ai_assistant")
        active_personality = next((p for p in personalities if p.get("id") == active_personality_id), None)

        # Standard-Fallback-Werte, falls in der JSON etwas fehlt
        default_settings = {"voice": "openai_alloy", "speed": 1.0}
        
        # Lade die Einstellungen aus der Persönlichkeit oder nutze den Fallback
        personality_tts_settings = active_personality.get("tts_settings", default_settings)
        
        # Überschreibe nur, wenn explizit Parameter übergeben wurden (z.B. für Tests),
        # ansonsten nutze die Einstellungen der Persönlichkeit.
        final_voice_id = voice_id or personality_tts_settings.get("voice")
        final_speed = speed or personality_tts_settings.get("speed")
        
        logger.info(f"Synthesizing with personality '{active_personality_id}': voice='{final_voice_id}', speed={final_speed}")

        audio_bytes = tts_service.synthesize(
            text=text,
            lang=lang,
            voice=final_voice_id,
            speed=final_speed,
            fmt=fmt,
            provider=provider,
            stream=stream,
        )
        
        mime_types = { "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg" }
        mime_type = mime_types.get(fmt.lower(), "application/octet-stream")
        
        return Response(content=audio_bytes, media_type=mime_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")



@app.post("/api/rag/collections/{collection_name}/analyze-style", response_model=StyleProfile)
async def analyze_collection_style(collection_name: str):
    """
    Stößt die Stilanalyse für eine gegebene RAG-Collection an.
    Dies ist der Endpunkt für den "Meta-Agenten".
    """
    logger.info(f"Anfrage zur Stilanalyse für Collection '{collection_name}' erhalten.")
    try:
        # Hier rufen wir die neue Logik aus creative_writer.py auf
        style_profile_json = await generate_style_profile_from_rag(
            collection_name=collection_name,
            api_key=keyring.get_password("Janus-Projekt", "openai"), # Annahme: Wir nutzen OpenAI für die Analyse
            model="gpt-4o-mini", # Ein günstiges, aber fähiges Modell für diese Aufgabe
            provider="openai"
        )
        return style_profile_json
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' nicht gefunden oder leer.")
    except Exception as e:
        logger.error(f"Fehler bei der Stilanalyse für '{collection_name}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stilanalyse fehlgeschlagen: {e}")


@app.post("/api/styles/profiles")
async def save_style_profile(request: StyleProfileSaveRequest):
    """
    Speichert ein neues oder aktualisiertes Stil-Profil in der style_profiles.json.
    """
    profiles_path = resource_path("backend/config/style_profiles.json")
    try:
        # Lade existierende Profile
        profiles = {}
        if os.path.exists(profiles_path):
            with open(profiles_path, "r", encoding="utf-8-sig") as f:
                profiles = json.load(f)

        # Füge hinzu oder überschreibe
        profiles[request.profile_key] = request.profile_data.dict()

        # Speichere die aktualisierte Datei
        with open(profiles_path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Stil-Profil für '{request.profile_key}' erfolgreich gespeichert.")
        return {"message": f"Stil-Profil für '{request.profile_key}' gespeichert."}
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Stil-Profils: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Speichern des Profils fehlgeschlagen: {e}")


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8001)
    except Exception as e:
        logger.error(f"Uvicorn startup failed: {e}", exc_info=True)
    input("Press Enter to exit...")
