import asyncio
import logging
import os
from contextlib import asynccontextmanager

import keyring
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# --- Router Imports ---
from backend.api.routers import chat, contacts, media, memory, rag, styles, system
from backend.data import database
from backend.data.database import get_db
from backend.logger_config import setup_logging
from backend.services import memory_manager
from backend.utils.paths import get_app_data_dir, resource_path

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8001)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
    input("Press Enter to exit...")
