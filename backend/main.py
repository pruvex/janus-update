import sys
import os
import io

# ---- FIX FÜR WINDOWS CONSOLE CRASH (Unicode/Emojis) ----
# Das hier rettet dich vor dem cp1252 Fehler in der Konsole!
try:
    if sys.platform.startswith('win'):
        # Methode 1: Für Python 3.7+
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        # Methode 2: Fallback (Brute Force)
        else:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception as e:
    print(f"Warnung: Konnte Console-Encoding nicht setzen: {e}")
# --------------------------------------------------------

# ---- START: ERZWUNGENER PFAD-FIX ----
# Dieser Block stellt sicher, dass der site-packages Ordner der venv immer im Suchpfad ist.
try:
    # Finde den Pfad zum venv-Ordner relativ zu dieser Datei
    current_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(current_dir, 'venv')
    site_packages = os.path.join(venv_path, 'Lib', 'site-packages')

    # Füge den Pfad an den Anfang der Suchliste hinzu, falls er nicht schon da ist
    if site_packages not in sys.path:
        sys.path.insert(0, site_packages)
        print(f"INFO: Manually added site-packages path to sys.path: {site_packages}")
except Exception as e:
    print(f"ERROR: Failed to manipulate sys.path. Error: {e}")
# ---- ENDE: ERZWUNGENER PFAD-FIX ----

import asyncio
import logging
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import keyring
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from datetime import timedelta

from backend.utils.paths import get_app_data_dir, resource_path

# --- Service Imports ---
from backend.services.memory_extractor import notification_manager

# --- Router Imports ---
from backend.api.routers import chat, contacts, media, memory, rag, styles, system, projects, images, users
from backend.data import database, schemas
from backend.data.database import get_db
from backend.logger_config import setup_logging
from backend.services import memory_manager
from backend.utils.paths import get_app_data_dir, resource_path
from backend.utils.config_loader import load_config_data, save_config_data

# --- Sentry Initialisierung (Fehler-Tracking für Beta-Phase) ---
import sentry_sdk

sentry_sdk.init(
    # --- NEUER, KORREKTER DSN ---
    dsn="https://5810a37c1b3c7e43faddbff6ec548cdf@o4510659131670528.ingest.de.sentry.io/4510659652943952",
    
    # Erfasst 100% der Transaktionen zur Performance-Analyse.
    traces_sample_rate=1.0,
    
    # Aktiviert detailliertes Profiling für die erfassten Transaktionen.
    profiles_sample_rate=1.0,
    
    # Sendet User-bezogene Daten (z.B. IP-Adresse), um Fehler
    # besser zuordnen zu können.
    send_default_pii=True
)
# --- Ende Sentry Block ---

# 1. Setup Logging & Environment
setup_logging()
logger = logging.getLogger("janus_backend")

# FFMPEG Path Setup
ffmpeg_path = os.path.normpath(resource_path("backend/bin"))
if os.path.isdir(ffmpeg_path):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    logger.info(f"FFMPEG path added: {ffmpeg_path}")
else:
    logger.warning("FFMPEG binary not found.")

# Load OpenAI Key explicitly for os.environ (Legacy support)
try:
    openai_key = keyring.get_password("Janus-Projekt", "openai")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
except Exception as e:
    logger.error(f"Error loading OpenAI key: {e}")


# 2. Lifespan Logic (Background Tasks on Startup)
async def run_archival(db_session):
    try:
        memory_manager.archive_old_memories(db_session)
        logger.info("Memory archival finished.")
    except Exception as e:
        logger.error(f"Archival task failed: {e}")
    finally:
        # Wir prüfen vorsichtig, ob close möglich ist
        try:
            if db_session.is_active:
                db_session.close()
        except:
            pass


async def run_pruning(db_session):
    try:
        memory_manager.prune_expired_memories(db_session)
        logger.info("Memory pruning finished.")
    except Exception as e:
        logger.error(f"Pruning task failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Configs & Ordner vorbereiten
    bootstrap_app_data()
    
    # 2. Database Init
    database.init_db()

    # Memory Maintenance Tasks
    db_session = database.SessionLocal()
    asyncio.create_task(run_archival(db_session))
    asyncio.create_task(run_pruning(db_session))

    # Ensure DB connection works
    try:
        db = next(get_db())
        db.close()
    except Exception as e:
        logger.critical(f"Database connection failed: {e}")
        import sys
        sys.exit(1) # Hinzugefügt: Harter Abbruch

    yield


def bootstrap_app_data():
    """
    Kopiert wichtige Config-Dateien nach %APPDATA%, damit wir sie bearbeiten können.
    """
    app_data = get_app_data_dir()
    
    # Mapping: Wo liegt es im Install-Ordner -> Wie soll es im AppData heißen
    files_to_copy = [
        ("backend/config/model_catalog.json", "model_catalog.json"),
        ("backend/config/config.json", "config.json"),
        ("backend/config/personalities.json", "personalities.json"),
        ("backend/config/style_profiles.json", "style_profiles.json")
    ]
    
    for src_rel, dest_name in files_to_copy:
        dest_path = os.path.join(app_data, dest_name)
        
        # Nur kopieren, wenn noch nicht im AppData vorhanden
        if not os.path.exists(dest_path):
            src_path = resource_path(src_rel)
            
            # Sicherheitscheck: Existiert die Quelle überhaupt?
            if os.path.exists(src_path):
                try:
                    # Stelle sicher, dass das Zielverzeichnis existiert
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    logger.info(f"Bootstrapped {dest_name} to AppData.")
                except Exception as e:
                    logger.error(f"Failed to copy {src_path} to {dest_path}: {e}")
            else:
                logger.warning(f"Source config missing: {src_path}. Using defaults/empty.")

# 3. App Definition
app = FastAPI(title="Janus Backend", version="1.0.0", lifespan=lifespan)

# CORS Configuration
# Define allowed origins for CORS
origins = [
    "http://localhost",
    "http://localhost:5173",  # Vite Development Server
    "http://localhost:5174",  # Vite Preview
    "http://localhost:5175",  # Additional Vite port
    "http://localhost:8000",  # Common development port
    "http://127.0.0.1:5173",  # Alternative localhost with Vite
    "http://127.0.0.1:8000",  # Alternative localhost with port 8000
    "http://127.0.0.1",       # General 127.0.0.1
    "electron://localhost",   # Electron app
    "http://127.0.0.1:8001",  # Common alternative port
    "http://localhost:3000",  # Common React port
    "http://127.0.0.1:3000",  # Common React port alternative
    "http://localhost:8080",  # Common alternative port
    "http://127.0.0.1:8080"   # Common alternative port
]

# Add CORS middleware with comprehensive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=600,  # Cache preflight request for 10 minutes
)

# 4. Static Files
# --- Static Files with Directory Validation ---
# Statische Assets (CSS/JS) bleiben im Programmordner (read-only ist ok)
static_path = resource_path("backend/static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static_bundle")

# User Images & Previews kommen in APPDATA (damit wir schreiben dürfen!)
app_data = get_app_data_dir()

# User Images
image_dir = os.path.join(app_data, "images")
os.makedirs(image_dir, exist_ok=True)
app.mount("/user_images", StaticFiles(directory=image_dir), name="user_images")

# Previews - Use static assets from the program folder
assets_path = resource_path("backend/assets")
if not os.path.exists(assets_path):
    # Fallback if folder is missing (prevents crash)
    os.makedirs(assets_path, exist_ok=True)
    
app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# 5. Include Routers
# Hier wird die modulare Struktur eingebunden
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(contacts.router, prefix="/api", tags=["Contacts"])
app.include_router(memory.router, prefix="/api", tags=["Memory"])
app.include_router(media.router, prefix="/api", tags=["Media"])
app.include_router(rag.router, prefix="/api", tags=["RAG"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(styles.router, prefix="/api", tags=["Styles"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(images.router, prefix="/api", tags=["Images"])
app.include_router(users.router, prefix="/api", tags=["Users"])


from backend.dependencies import (
    get_current_user,
    create_access_token,
    check_api_keys_in_keyring,
    security,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Route zum Abrufen des zuletzt verwendeten Modells
@app.get("/api/last-used-model", response_model=schemas.GetLastUsedModelResponse)
async def get_last_used_model():
    config = load_config_data()
    return {
        "provider": config.get("last_used_provider"),
        "model": config.get("last_used_model")
    }

@app.put("/api/last-used-model")
async def set_last_used_model(
    request: schemas.SetLastUsedModelRequest,
    # --- HIER: DIE KORREKTE PRÜFUNG ---
    # Wir prüfen, ob der Token das Recht 'settings:write' hat
    current_user: str = Security(get_current_user, scopes=["settings:write"]) 
):
    config = load_config_data()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config_data(config)
    return {"message": "Last used model and provider updated successfully."}

# --- SSE ENDPOINT (REALTIME UPDATES) ---
@app.get("/api/events")
async def sse_endpoint():
    """Streams events (like 'refresh') to the client."""
    async def event_generator():
        queue = await notification_manager.connect()
        try:
            while True:
                # Wait for message (infinite)
                data = await queue.get()
                # SSE Format: "data: <message>\n\n"
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            notification_manager.disconnect(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
# ----------------------------------------

@app.post("/api/auth/token")
def create_session_token():
    # 1. Keys prüfen
    keys_are_valid = check_api_keys_in_keyring()
    if not keys_are_valid:
        raise HTTPException(status_code=401, detail="API keys not configured.")

    user_identifier = "local_user"
    
    # --- HIER: DIE ENTSCHEIDENDE ZEILE ---
    # Wir geben dem Token BEIDE Rechte: 'me' (lesen) und 'settings:write' (schreiben)
    my_scopes = ["me", "settings:write"] 
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": user_identifier, "scopes": my_scopes}, # <--- Scopes in den Token packen
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- FIX FÜR PYINSTALLER PFADE ---
import sys  # Sicherstellen, dass sys importiert ist

# Definiere den Pfad zu deinem gebauten Frontend
if getattr(sys, 'frozen', False):
    # WENN WIR ALS EXE LAUFEN (Produktion):
    # PyInstaller entpackt Daten in einen temporären Ordner (_MEIPASS)
    base_path = Path(sys._MEIPASS)
    frontend_build_dir = base_path / "frontend" / "dist"
else:
    # WENN WIR IN DER ENTWICKLUNG LAUFEN:
    base_path = Path(__file__).resolve().parent.parent
    frontend_build_dir = base_path / "frontend" / "dist"

print(f"DEBUG: Frontend path resolved to: {frontend_build_dir}")

# Sicherheits-Check: Wenn der Ordner fehlt, erstellen wir ihn leer, 
# damit die App nicht komplett abstürzt (verhindert den Sentry-Fehler)
if not os.path.exists(frontend_build_dir):
    print(f"CRITICAL WARNING: Frontend build dir missing at {frontend_build_dir}")
    os.makedirs(frontend_build_dir, exist_ok=True)
# ---------------------------------

# "Einhängen" des gesamten Verzeichnisses am Wurzelpfad "/"
app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8001)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
    input("Press Enter to exit...")
