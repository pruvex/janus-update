import sys
import os

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
from contextlib import asynccontextmanager

import keyring
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# --- Router Imports ---
from backend.api.routers import chat, contacts, media, memory, rag, styles, system, projects, images
from backend.data import database, schemas
from backend.data.database import get_db
from backend.logger_config import setup_logging
from backend.services import memory_manager
from backend.utils.paths import get_app_data_dir, resource_path
from backend.utils.config_loader import load_config_data, save_config_data

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
    # Database Init
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

    yield


# 3. App Definition
app = FastAPI(title="Janus Backend", version="1.0.0", lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "electron://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Static Files
app.mount("/static", StaticFiles(directory=resource_path("backend/static")), name="static_bundle")
image_dir = os.path.join(get_app_data_dir(), "images")
os.makedirs(image_dir, exist_ok=True)
app.mount("/user_images", StaticFiles(directory=image_dir), name="user_images")

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

# NEU: Route zum Setzen des zuletzt verwendeten Modells und Providers
@app.put("/api/last-used-model")
async def set_last_used_model(request: schemas.SetLastUsedModelRequest):
    config = load_config_data()
    config["last_used_provider"] = request.provider
    config["last_used_model"] = request.model
    save_config_data(config)
    return {"message": "Last used model and provider updated successfully."}

if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8001)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
    input("Press Enter to exit...")
