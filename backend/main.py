# --- VENV PATH INJECTION (WORKAROUND) ---
import sys
import os

# Ersetze diesen Pfad mit dem, den du gerade kopiert hast!
VENV_SITE_PACKAGES = r"C:\python311\Lib\site-packages" 

if VENV_SITE_PACKAGES not in sys.path:
    print(f"!!! VENV WORKAROUND: Füge {VENV_SITE_PACKAGES} zum Systempfad hinzu.")
    sys.path.insert(0, VENV_SITE_PACKAGES)
# ----------------------------------------
import sys
import os
import io
import logging
import time

# --- STARTUP PROFILING ---
START_TIME = time.time()

def log_startup_time(step_name):
    elapsed = time.time() - START_TIME
    print(f"[STARTUP_PROFILER] {elapsed:.2f}s: {step_name}")

log_startup_time("main.py gestartet")

# Try to import version, fallback to 'dev' if not available
try:
    from backend.version import APP_VERSION
    log_startup_time("Version importiert")
except ImportError:
    APP_VERSION = "dev"  # Fallback for development without build
    log_startup_time("Version nicht gefunden, verwende 'dev'")

# Configure logging with version information
LOG_FORMAT = f'%(asctime)s - %(name)s - [%(levelname)s] - [v{APP_VERSION}] - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("janus_backend")
logger.info(f"Janus Backend starting up (v{APP_VERSION})")
log_startup_time("Logging konfiguriert")

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
    log_startup_time("Windows Console Fix angewandt")
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
    log_startup_time("Python-Pfad angepasst")
except Exception as e:
    print(f"ERROR: Failed to manipulate sys.path. Error: {e}")
# ---- ENDE: ERZWUNGENER PFAD-FIX ----

log_startup_time("Starte Standard-Imports...")
import asyncio
import logging
import os
import shutil
import threading
from contextlib import asynccontextmanager
from pathlib import Path

log_startup_time("Standard-Imports abgeschlossen")

log_startup_time("Starte Drittanbieter-Imports...")
import keyring
from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import timedelta
from sqlalchemy.orm import Session
from backend.data.database import get_db
log_startup_time("FastAPI-Imports abgeschlossen")

log_startup_time("Starte Importe eigener Module...")
from backend.utils.paths import get_app_data_dir, get_resource_path, get_images_dir
# --- FIX: Alias für Kompatibilität ---
resource_path = get_resource_path
log_startup_time("Pfad-Hilfsfunktionen importiert")
# -------------------------------------

# --- Service Imports ---
log_startup_time("Importiere memory_extractor...")
from backend.services.memory_extractor import notification_manager
log_startup_time("memory_extractor importiert")

# --- Router Imports ---
log_startup_time("Importiere Router...")
from backend.api.routers import (
    chat,
    contacts,
    context,
    media,
    memory,
    rag,
    styles,
    system,
    projects,
    images,
    users,
    local_llm,
    image_engine,
    consent,
    backlog,
)
log_startup_time("Router importiert")

log_startup_time("Importiere Datenbank und Schemas...")
from backend.data import database, schemas
from backend.services.image_engine_checker import idle_shutdown_worker
log_startup_time("Datenbank und Schemas importiert")

log_startup_time("Importiere Logging-Konfiguration...")
from backend.logger_config import setup_logging
log_startup_time("Logging-Konfiguration importiert")

log_startup_time("Importiere memory_cleanup...")
from backend.services.memory_cleanup import schedule_memory_cleanup
log_startup_time("memory_cleanup importiert")

log_startup_time("Importiere ollama_manager...")
from backend.services.ollama_manager import ollama_manager
log_startup_time("ollama_manager importiert")

log_startup_time("Importiere Konfigurations-Loader...")
from backend.utils.config_loader import load_config_data, save_config_data
log_startup_time("Konfigurations-Loader importiert")

log_startup_time("Importiere CLIP Model Loader...")
from backend.services.vision.model_loader import start_clip_model_download
log_startup_time("CLIP Model Loader importiert")

# --- Sentry Initialisierung (Fehler-Tracking für Beta-Phase) ---
log_startup_time("Importiere Sentry...")
import sentry_sdk
log_startup_time("Sentry importiert")

# Lade die App-Version, mit Fallback
app_version = "unknown"
try:
    from backend.version import APP_VERSION as VERSION
    app_version = VERSION if VERSION else "unknown"
except ImportError:
    app_version = "dev"

# Sicherstellen, dass die Version nicht leer ist
final_app_version = app_version if app_version else "unknown"

log_startup_time("Initialisiere Sentry...")
try:
    sentry_sdk.init(
        # --- NEUER, KORREKTER DSN ---
        dsn="https://5810a37c1b3c7e43faddbff6ec548cdf@o4510659131670528.ingest.de.sentry.io/4510659652943952",
        
        # Version setzen
        release=f"janus-projekt@{final_app_version}",
        
        # Environment setzen
        environment="development" if final_app_version == "dev" else "production",
        
        # Erfasst 100% der Transaktionen zur Performance-Analyse.
        traces_sample_rate=1.0,
        
        # Aktiviert detailliertes Profiling für die erfassten Transaktionen.
        profiles_sample_rate=1.0,
        
        # Sendet User-bezogene Daten (z.B. IP-Adresse), um Fehler
        # besser zuordnen zu können.
        send_default_pii=True
    )
    log_startup_time("Sentry erfolgreich initialisiert")
except Exception as e:
    log_startup_time(f"FEHLER bei der Sentry-Initialisierung: {str(e)}")
# --- Ende Sentry Block ---

# 1. Setup Logging & Environment
log_startup_time("Starte Logging-Setup...")
setup_logging()
logger = logging.getLogger("janus_backend")
log_startup_time("Logging-Setup abgeschlossen")

# --- GLOBAL STATUS FLAGS ---
FFMPEG_READY = False
BOOTSTRAP_COMPLETE = False

# --- BACKGROUND TASK ---
def background_ffmpeg_install():
    global FFMPEG_READY
    from backend.utils.ffmpeg_manager import ensure_ffmpeg
    logger.info("Starting FFmpeg download in background...")
    success = ensure_ffmpeg()
    if success:
        FFMPEG_READY = True
        logger.info("FFmpeg successfully installed in background! Audio features now available.")
    else:
        logger.error("Background FFmpeg download failed. Audio features may not work.")

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
        from backend.services import memory_manager
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
        from backend.services import memory_manager
        memory_manager.prune_expired_memories(db_session)
        logger.info("Memory pruning finished.")
    except Exception as e:
        logger.error(f"Pruning task failed: {e}")


async def run_ollama_maintenance_check_delayed(delay_seconds: int = 30):
    try:
        await asyncio.sleep(max(0, int(delay_seconds)))
        if not ollama_manager.check_ollama().get("running"):
            logger.info("Ollama maintenance check skipped (service not running).")
            return

        model_snapshot = await asyncio.to_thread(ollama_manager.check_for_updates)
        binary_snapshot = await asyncio.to_thread(ollama_manager.check_ollama_binary_update)
        logger.info(
            "Ollama maintenance check completed (models_checked=%s, updates=%s, binary_update=%s)",
            model_snapshot.get("checked_models", 0),
            model_snapshot.get("updates_available", 0),
            binary_snapshot.get("update_available", False),
        )
    except Exception as exc:
        logger.warning("Ollama maintenance check failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.tools.video_tools import clear_video_search_cache

    clear_video_search_cache()

    # 1. Prepare configs & directories - Run synchronously before anything else
    logger.info("Starting application bootstrap...")
    try:
        bootstrap_app_data()
        logger.info("Bootstrap completed successfully.")
    except Exception as e:
        logger.critical(f"Critical error during bootstrap: {e}")
        # Don't exit here, let the health check handle the status
    
    # 2. Initialize Database
    try:
        database.init_db()
        
        # --- Default Chat erstellen (Verhindert Frontend-Fehler) ---
        from backend.data.database import SessionLocal
        # Wir importieren hier Models lokal, falls nötig
        from backend.data.models import Project, Chat
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # Check Project
            if not db.query(Project).first():
                logger.info("Erstelle Standard-Projekt...")
                p = Project(name="Standard", description="Default", created_at=datetime.utcnow())
                db.add(p)
                db.commit()
                db.refresh(p)
                
                # Check Chat
                logger.info("Erstelle Erstes Gespräch...")
                c = Chat(title="Erstes Gespräch", project_id=p.id, created_at=datetime.utcnow(), is_archived=False)
                db.add(c)
                db.commit()
        except Exception as e:
            logger.error(f"Konnte Default-Daten nicht anlegen: {e}")
            db.rollback()
        finally:
            db.close()
        # -----------------------------------------------------------

    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        # Don't exit here, let the health check handle the status

    # 2.5. Register all Tools (CRITICAL: Memory Tools must be registered!)
    try:
        from backend.tool_registry import register_all_tools
        register_all_tools()
        logger.info("All tools registered successfully (including memory_write, memory_read, memory_update, memory_history).")
    except Exception as e:
        logger.error(f"Failed to register tools: {e}")

    # 3. Start FFmpeg download in background (NON-BLOCKING!)
    # We use a thread so the download doesn't block the server loop
    try:
        download_thread = threading.Thread(target=background_ffmpeg_install, daemon=True)
        download_thread.start()
        logger.info("Started FFmpeg download in background.")
    except Exception as e:
        logger.error(f"Failed to start FFmpeg download: {e}")

    # 3.5. Start CLIP Model download in background (NON-BLOCKING!)
    # Lazy-Loading: Download nach App-Start im Hintergrund
    try:
        start_clip_model_download()
        logger.info("Started CLIP Model download in background (Lazy-Loading).")
    except Exception as e:
        logger.error(f"Failed to start CLIP Model download: {e}")

    # 4. Memory Maintenance Tasks (with cleanup task tracking)
    cleanup_task = None
    try:
        db_session = database.SessionLocal()
        asyncio.create_task(run_archival(db_session))
        asyncio.create_task(run_pruning(db_session))
        asyncio.create_task(run_ollama_maintenance_check_delayed(30))
        asyncio.create_task(idle_shutdown_worker())
        # STARTUP FIX: Register memory cleanup background task
        cleanup_task = asyncio.create_task(schedule_memory_cleanup(interval_seconds=900))
        logger.info("Started background maintenance tasks (including memory cleanup).")
    except Exception as e:
        logger.error(f"Failed to start maintenance tasks: {e}")

    # 5. P8: RAG V2 Background Watchdog (Optional - only if configured)
    rag_watcher = None
    try:
        from backend.services.rag.watcher import RAGWatcher
        from backend.utils.config_loader import load_config_data

        config = load_config_data()
        workspaces = config.get("filesystem_workspaces", [])

        if workspaces:
            # Start watcher for first workspace (can be extended for multiple)
            workspace_root = workspaces[0] if workspaces else None
            if workspace_root:
                rag_watcher = RAGWatcher(
                    workspace_root=workspace_root,
                    enable_path_policy=True,
                )
                rag_watcher.start()
                logger.info(f"[P8] RAG Watchdog started for workspace: {workspace_root}")
            else:
                logger.info("[P8] RAG Watchdog not started: no workspace configured")
        else:
            logger.info("[P8] RAG Watchdog not started: no workspaces in config")
    except ImportError:
        logger.info("[P8] RAG Watchdog not available (watchdog library not installed)")
    except Exception as e:
        logger.warning(f"[P8] Failed to start RAG Watchdog: {e}")

    # 7. D14: Weekly Learning Engine Background Scheduler
    learning_task = None
    try:
        async def weekly_learning_scheduler():
            """Background scheduler for weekly learning reports."""
            import asyncio
            from datetime import timedelta
            from backend.services.logging.learning_engine import LearningEngine
            
            logger.info("[LEARNING-SCHEDULER] Starting weekly learning scheduler")
            
            while True:
                try:
                    # Sleep for 7 days (604800 seconds)
                    await asyncio.sleep(604800)  # 7 days
                    
                    # Generate and persist weekly report
                    logger.info("[LEARNING-SCHEDULER] Generating weekly learning report")
                    engine = LearningEngine()
                    await engine.generate_weekly_report(days=14, persist=True)
                    logger.info("[LEARNING-SCHEDULER] Weekly learning report generated and persisted")
                    
                except Exception as e:
                    logger.error(f"[LEARNING-SCHEDULER] Error in weekly learning job: {e}", exc_info=True)
                    # Continue the loop even if there's an error (don't crash the server)
        
        # Start the background scheduler (non-blocking)
        learning_task = asyncio.create_task(weekly_learning_scheduler())
        logger.info("[LEARNING-SCHEDULER] Started background weekly learning scheduler")
    except Exception as e:
        logger.error(f"[LEARNING-SCHEDULER] Failed to start weekly learning scheduler: {e}")

    # 6. FINAL: Global Scope Discovery (Async indexing of all drives)
    def run_global_discovery():
        """Run background discovery of all local drives."""
        try:
            import os
            import pathlib
            from backend.services.rag.ingestion import IngestionRun
            from backend.services.rag.index_store import IndexStore
            from backend.utils.paths import get_app_data_dir

            gold_formats = [".pdf", ".md", ".txt", ".py", ".js", ".ts", ".docx"]

            # Check if database is empty before running global scan
            db_path = Path(get_app_data_dir()) / "knowledge_index_v2.db"
            store = IndexStore(str(db_path))
            index = store.get_all()

            if len(index) > 0:
                logger.info(f"[GLOBAL-SKIP] Database already contains {len(index)} indexed files. Skipping global discovery.")
                return

            logger.info("[GLOBAL-SCAN-START] Database is empty. Starting global discovery.")

            # Discover all local drives
            global_locations = []
            documents_path = os.path.expanduser("~/Documents")
            desktop_path = os.path.expanduser("~/Desktop")

            if os.path.exists(documents_path):
                global_locations.append(documents_path)
            if os.path.exists(desktop_path):
                global_locations.append(desktop_path)

            # Enumerate all local drives (Windows) - but exclude system directories
            if os.name == 'nt':
                import string
                system_excludes = {"Windows", "Program Files", "Program Files (x86)", "ProgramData", "System Volume Information", "$RECYCLE.BIN", "Config.Msi", "Recovery", "$Recycle.Bin"}
                # Exclude Janus installation directory to prevent self-indexing
                janus_install_dir = r"C:\KI\Janus-Projekt"
                for drive in string.ascii_uppercase:
                    drive_path = f"{drive}:\\"
                    if os.path.exists(drive_path):
                        # Scan drive root for user-accessible directories, exclude system directories
                        try:
                            for item in os.listdir(drive_path):
                                item_path = os.path.join(drive_path, item)
                                if os.path.isdir(item_path) and item not in system_excludes:
                                    # Skip Janus installation directory to prevent self-indexing
                                    if item_path.lower() == janus_install_dir.lower():
                                        logger.info(f"[GLOBAL-SCAN] Skipping Janus installation directory: {item_path}")
                                        continue
                                    global_locations.append(item_path)
                                    logger.info(f"[GLOBAL-SCAN] Added directory: {item_path}")
                        except PermissionError:
                            # Only log if not a known system directory
                            if not any(exclude in drive_path for exclude in system_excludes):
                                logger.warning(f"[GLOBAL-SCAN] Permission denied for {drive_path}")
                        except Exception as e:
                            logger.error(f"[GLOBAL-SCAN] Error scanning {drive_path}: {e}")

            if not global_locations:
                logger.info("[FINAL] No global locations found for discovery")
                return

            logger.info("[GLOBAL-SCAN-START] Global Discovery started")
            logger.info(f"[GLOBAL-SCAN-START] Scanning {len(global_locations)} locations: {global_locations}")

            # Run ingestion for each location
            total_indexed = 0
            for idx, location in enumerate(global_locations, 1):
                try:
                    logger.info(f"[GLOBAL-SCAN-PROGRESS] [{idx}/{len(global_locations)}] Scanning location: {location}")
                    ingest = IngestionRun(
                        root_dir=location,
                        chroma_path=str(Path(get_app_data_dir()) / "rag_chroma_db_v2"),
                        db_path=str(Path(get_app_data_dir()) / "knowledge_index_v2.db"),
                        enable_path_policy=True,
                    )
                    stats = ingest.run()
                    indexed_count = stats.get("indexed", 0)
                    total_indexed += indexed_count
                    logger.info(f"[GLOBAL-SCAN-PROGRESS] [{idx}/{len(global_locations)}] Completed: {location} (indexed: {indexed_count}, total: {total_indexed})")
                except Exception as e:
                    logger.error(f"[GLOBAL-SCAN-PROGRESS] [{idx}/{len(global_locations)}] Failed for {location}: {e}", exc_info=True)

            # Wait-and-Signal: Final summary
            logger.info(f"[GLOBAL-SCAN-COMPLETE] Total files indexed: {total_indexed}")

        except Exception as e:
            logger.error(f"[FINAL] Global discovery failed: {e}", exc_info=True)

    # HOTFIX: RAG_V2_AUTO_INGEST environment check to speed up boot for testing
    if os.environ.get("RAG_V2_AUTO_INGEST", "false").lower() == "true":
        try:
            from backend.services.rag.path_policy import enable_global_scan_mode
            # Enable global scan mode BEFORE starting the thread (global for all threads)
            enable_global_scan_mode()
            discovery_thread = threading.Thread(target=run_global_discovery, daemon=True)
            discovery_thread.start()
            logger.info("[FINAL] Global discovery thread started (daemon)")
        except Exception as e:
            logger.warning(f"[FINAL] Failed to start global discovery: {e}")
    else:
        logger.info("[FINAL] Global Discovery disabled via RAG_V2_AUTO_INGEST.")

    # 5. Test database connection
    try:
        db = next(database.get_db_sync())
        db.close()
        logger.info("Database connection test successful.")
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        # Don't exit here, let the health check handle the status

    # 6. Logging Pipeline: Start batch upload worker
    try:
        logger.info("Attempting to import logger_core...")
        from backend.services.logging import logger_core
        logger.info("logger_core imported successfully, starting worker...")
        await logger_core.start_worker()
        logger.info("Logging batch upload worker started successfully.")
    except Exception as e:
        logger.error(f"Failed to start logging worker: {e}", exc_info=True)
        # Don't exit here, logging is non-critical

    # Let the application start even if some non-critical components failed
    # The health check will report the actual status
    yield
    
    # GRACEFUL SHUTDOWN: Cancel memory cleanup task
    if cleanup_task:
        logger.info("Shutting down: Cancelling memory cleanup task...")
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("Memory cleanup task cancelled successfully.")
        except Exception as e:
            logger.error(f"Error cancelling memory cleanup task: {e}")
    
    # GRACEFUL SHUTDOWN: Cancel learning scheduler task
    if learning_task:
        logger.info("Shutting down: Cancelling weekly learning scheduler...")
        learning_task.cancel()
        try:
            await learning_task
        except asyncio.CancelledError:
            logger.info("Weekly learning scheduler cancelled successfully.")
        except Exception as e:
            logger.error(f"Error cancelling weekly learning scheduler: {e}")

    # P8: Stop RAG Watchdog
    if rag_watcher:
        logger.info("[P8] Shutting down: Stopping RAG Watchdog...")
        try:
            rag_watcher.stop()
            logger.info("[P8] RAG Watchdog stopped successfully.")
        except Exception as e:
            logger.warning(f"[P8] Error stopping RAG Watchdog: {e}")

    # Logging Pipeline: Flush queue and stop worker
    try:
        from backend.services.logging.logger_core import flush_log_queue, stop_worker
        logger.info("Shutting down: Flushing log queue...")
        await flush_log_queue()
        await stop_worker()
        logger.info("Logging pipeline shutdown complete.")
    except Exception as e:
        logger.error(f"Error during logging pipeline shutdown: {e}")


import secrets


def bootstrap_app_data():
    """
    Kopiert wichtige Config-Dateien nach %APPDATA%, damit wir sie bearbeiten können,
    und stellt sicher, dass ein API-Schlüssel existiert.
    """
    global BOOTSTRAP_COMPLETE
    app_data = get_app_data_dir()
    
    # 1. Statische Configs (IMMER überschreiben für Updates)
    # Diese Dateien enthalten Preise und Modelldefinitionen, die wir als Entwickler updaten.
    static_files = [
        ("backend/config/model_catalog.json", "model_catalog.json"),
        ("backend/config/style_profiles.json", "style_profiles.json")
    ]

    for src_rel, dest_name in static_files:
        dest_path = os.path.join(app_data, dest_name)
        src_path = get_resource_path(src_rel)
        if os.path.exists(src_path):
            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path) # Force Copy
                logger.info(f"Updated {dest_name} in AppData.")
            except Exception as e:
                logger.error(f"Failed to update {dest_name}: {e}")

    # 2. User Configs (NUR kopieren wenn nicht vorhanden)
    # Diese Dateien enthalten User-Einstellungen, die nicht überschrieben werden dürfen.
    user_files = [
        ("backend/config/config.json", "config.json"),
        ("backend/config/personalities.json", "personalities.json")
    ]
    
    for src_rel, dest_name in user_files:
        dest_path = os.path.join(app_data, dest_name)
        if not os.path.exists(dest_path):
            src_path = get_resource_path(src_rel)
            if os.path.exists(src_path):
                try:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    logger.info(f"Bootstrapped {dest_name} to AppData.")
                except Exception as e:
                    logger.error(f"Failed to copy {src_path} to {dest_path}: {e}")

    # API Key Sicherung (wie gehabt)
    try:
        config_path = os.path.join(app_data, "config.json")
        if os.path.exists(config_path):
            config = load_config_data()
            if "api_key" not in config or not config["api_key"]:
                new_key = secrets.token_hex(32)
                config["api_key"] = new_key
                # Defaults setzen falls fehlend
                if "last_used_provider" not in config or "last_used_model" not in config:
                    from backend.services.llm_gateway import get_first_available_text_model_with_provider
                    default_provider, default_model = get_first_available_text_model_with_provider()
                    config["last_used_provider"] = default_provider if default_provider else "openai"
                    config["last_used_model"] = default_model if default_model else ""
                save_config_data(config)
                logger.info("Generated and saved new API key.")
    except Exception as e:
        logger.error(f"Failed to ensure API key: {e}")
    
    BOOTSTRAP_COMPLETE = True
    logger.info("Bootstrap process completed successfully.")

# 3. App Definition
app = FastAPI(title="Janus Backend", version="1.0.0", lifespan=lifespan)


# --- FIX: Exception Handler für saubere Logs beim Start ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_str = str(exc).lower()
    # Wenn Auth-Header fehlen, senden wir 401 statt 422
    if "header" in error_str or "authorization" in error_str or "api-key" in error_str:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Auth credentials missing (loading...)"},
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
# ----------------------------------------------------------

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
    "http://127.0.0.1:8080",  # Common alternative port
    "janus://app",            # Custom scheme for packaged Electron (v0.4.16-beta.5)
    "null",                   # file:// origin serialises to "null" in CORS
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
# Static assets are now handled in the final static files section below

# Bilder-Verzeichnis initialisieren
image_dir = get_images_dir()
print(f"!!! IMAGE DIRECTORY: {image_dir}")
print(f"!!! DIRECTORY EXISTS: {os.path.exists(image_dir)}")
print(f"!!! DIRECTORY LISTING: {os.listdir(os.path.dirname(image_dir))}")

# Previews - Use static assets from the program folder
assets_path = resource_path("backend/assets")
if not os.path.exists(assets_path):
    # Fallback if folder is missing (prevents crash)
    os.makedirs(assets_path, exist_ok=True)
    
# NOTE: Do NOT mount "/assets" here. Vite's production build emits hashed
# frontend bundles into `frontend/dist/assets/` (e.g. `/assets/index-*.css`).
# Since the "/" StaticFiles mount at the bottom of this file serves
# `frontend/dist`, a "/assets" mount at this point would shadow those URLs
# and cause 404s for the built CSS/JS -> UI renders completely unstyled in
# the packaged app (Electron loads from http://127.0.0.1:8001/). The old
# "/assets" route pointed to backend preview images; its duplicate
# "/backend_assets" below is the canonical path for those.
app.mount("/backend_assets", StaticFiles(directory=assets_path), name="backend_assets")

from backend.dependencies import api_key_auth

# --- NEUER HEALTH CHECK ENDPUNKT (ungeschützt) ---
@app.get("/api/health", status_code=200, tags=["System"])
async def health_check():
    """
    Health check endpoint that doesn't require authentication.
    Returns 503 if the service is still initializing (bootstrap not complete).
    """
    if not BOOTSTRAP_COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable: Initializing..."
        )
    
    return {
        "status": "ready",
        "audio_ready": FFMPEG_READY
    }


@app.get("/debug/images")
async def list_images():
    """
    Debug endpoint to list contents of the images directory.
    No authentication required for debugging purposes.
    """
    path = get_images_dir()
    if not os.path.exists(path):
        return {"error": f"Path does not exist: {path}", "abs_path": os.path.abspath(path)}
    try:
        files = os.listdir(path)
        return {
            "path": path,
            "files_count": len(files),
            "files": files[:10],  # First 10 files
            "abs_path": os.path.abspath(path),
            "is_dir": os.path.isdir(path),
            "access_ok": os.access(path, os.R_OK | os.W_OK | os.X_OK)
        }
    except Exception as e:
        return {
            "error": str(e),
            "path": path,
            "abs_path": os.path.abspath(path) if 'path' in locals() else None,
            "type": str(type(e).__name__)
        }


# --- FIX: Manueller Image-Server ---
# Dieser Endpunkt liefert die Bilder manuell aus, was Probleme mit 
# Windows-Ordner-Berechtigungen oder OneDrive-Symlinks umgeht.
@app.get("/user_images/{filename}")
async def serve_user_image(filename: str):
    """Serve user images with security checks and forced CORS."""
    # Security check
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join(image_dir, filename)
    
    # Hilfsfunktion zum Erstellen der Response mit Header
    def make_response(path):
        response = FileResponse(path)
        # HIER IST DER FIX: Wir zwingen den Header manuell rein
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    if os.path.exists(file_path):
        return make_response(file_path)
    
    # Check uploads subfolder if not found in root
    uploads_path = os.path.join(image_dir, "uploads", filename)
    if os.path.exists(uploads_path):
        return make_response(uploads_path)

    raise HTTPException(status_code=404, detail="Image not found")

# --- FIX: Spezifischer Endpunkt für Uploads ---
@app.get("/user_images/uploads/{filename}")
async def serve_upload_image(filename: str):
    """Serve uploaded images with forced CORS."""
    # Security check
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Construct path to the uploads folder
    file_path = os.path.join(image_dir, "uploads", filename)
    
    if os.path.exists(file_path):
        response = FileResponse(file_path)
        # HIER IST DER FIX: Wir zwingen den Header manuell rein
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    
    raise HTTPException(status_code=404, detail="Upload not found")


# --- MEMORY SYSTEM DEBUG ENDPOINT ---
@app.get("/api/debug/memory")
async def debug_memory_system():
    """
    Debug endpoint for Memory V2 system observability.
    Returns cache stats, metrics, embedding cache stats, circuit breaker state,
    and Memory V2 budget system status.
    """
    result = {}
    try:
        from backend.services.memory_cache import memory_cache
        result["cache"] = memory_cache.get_stats()
    except Exception as e:
        result["cache"] = {"error": str(e)}
    try:
        from backend.services.memory_observability import memory_metrics
        result["metrics"] = memory_metrics.snapshot()
    except Exception as e:
        result["metrics"] = {"error": str(e)}
    try:
        from backend.services.embedding_cache import embedding_cache_stats
        result["embedding_cache"] = embedding_cache_stats()
    except Exception as e:
        result["embedding_cache"] = {"error": str(e)}
    try:
        from backend.services.memory_extractor import _extraction_breaker
        result["circuit_breaker"] = _extraction_breaker.get_state()
    except Exception as e:
        result["circuit_breaker"] = {"error": str(e)}
    try:
        from backend.services.memory_budget import MEMORY_V2_ENABLED, _get_tiktoken_encoder
        result["budget_system"] = {
            "v2_enabled": MEMORY_V2_ENABLED,
            "tiktoken_available": _get_tiktoken_encoder() is not None,
        }
    except Exception as e:
        result["budget_system"] = {"error": str(e)}
    return result


# 5. Include Routers
# Hier wird die modulare Struktur eingebunden
from backend.api.routers import chat, contacts, context, memory, media, rag, system, local_llm, styles, image_engine, projects, images, users, tasks, calendar, backlog

app.include_router(chat.router, prefix="/api", tags=["Chat"], dependencies=[Depends(api_key_auth)])
app.include_router(contacts.router, prefix="/api", tags=["Contacts"], dependencies=[Depends(api_key_auth)])
app.include_router(context.router, prefix="/api", tags=["Context"], dependencies=[Depends(api_key_auth)])
app.include_router(memory.router, prefix="/api", tags=["Memory"], dependencies=[Depends(api_key_auth)])
app.include_router(media.router, prefix="/api", tags=["Media"], dependencies=[Depends(api_key_auth)])
# FIX: router already defines /rag so mount just under /api
app.include_router(rag.router, prefix="/api", tags=["RAG"], dependencies=[Depends(api_key_auth)])
# Auth entfernt für Config-Loading beim Start:
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(local_llm.router, prefix="/api", tags=["Local LLM"])
app.include_router(styles.router, prefix="/api", tags=["Styles"])
app.include_router(image_engine.router, prefix="/api/local-image-gen", tags=["Local Image Engine"])
# Andere Router bleiben geschützt
app.include_router(projects.router, prefix="/api", tags=["Projects"], dependencies=[Depends(api_key_auth)])
app.include_router(images.router, prefix="/api", tags=["Images"], dependencies=[Depends(api_key_auth)])
app.include_router(users.router, prefix="/api", tags=["Users"], dependencies=[Depends(api_key_auth)])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"], dependencies=[Depends(api_key_auth)])
app.include_router(calendar.router, prefix="/api", tags=["Calendar"], dependencies=[Depends(api_key_auth)])
app.include_router(backlog.router, prefix="/api", tags=["Backlog"], dependencies=[Depends(api_key_auth)])
app.include_router(consent.router, prefix="/api/consent", tags=["Consent"])


from backend.dependencies import (
    get_current_user,
    create_access_token,
    check_api_keys_in_keyring,
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

@app.post("/api/video/analyze")
async def analyze_video(request: dict, db: Session = Depends(get_db)):
    """Direct video analysis endpoint without chat orchestrator.

    Takes video_id and returns VideoUnderstandingOutput directly.
    This is used by the transcript-modal UI.
    """
    from backend.tools.video_understanding import video_understanding_tool
    from backend.data.schemas import VideoUnderstandingInput

    video_id = request.get("video_id")
    if not video_id or len(video_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid video_id. Must be exactly 11 characters.")

    # Create input with source="ui_button" to bypass guardrail
    args = VideoUnderstandingInput(
        video_id=video_id,
        task="summarize",
        language="de",
        detail_level="medium",
        source="ui_button"
    )

    try:
        # Call the tool directly with await (it's already async)
        result = await video_understanding_tool(args, db=db)
        return result.data if result.status == "ok" else {"error": result.error}
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Image migration from AppData to Pictures folder
def migrate_images_to_public_folder():
    """Moves images from AppData to the public Pictures folder."""
    try:
        old_images_dir = os.path.join(get_app_data_dir(), "images")
        new_images_dir = get_images_dir()
        
        if os.path.exists(old_images_dir):
            logger.info(f"Checking for old images in: {old_images_dir}")
            
            # Process all files in the old directory
            for item in os.listdir(old_images_dir):
                old_path = os.path.join(old_images_dir, item)
                new_path = os.path.join(new_images_dir, item)
                
                # If it's a file and doesn't exist in the new location -> Move it
                if os.path.isfile(old_path):
                    if not os.path.exists(new_path):
                        shutil.move(old_path, new_path)
                        logger.info(f"Image migrated: {item}")
                    else:
                        # If file exists (unlikely with GUIDs), keep the old one
                        pass
                
                # If it's a directory (e.g., 'uploads') -> Move its contents
                elif os.path.isdir(old_path):
                    new_uploads_dir = os.path.join(new_images_dir, "uploads")
                    os.makedirs(new_uploads_dir, exist_ok=True)
                    # Move files from old uploads to new uploads
                    for subitem in os.listdir(old_path):
                        sub_old = os.path.join(old_path, subitem)
                        sub_new = os.path.join(new_uploads_dir, subitem)
                        if os.path.isfile(sub_old) and not os.path.exists(sub_new):
                            shutil.move(sub_old, sub_new)
                            logger.info(f"Upload migrated: {item}/{subitem}")

            logger.info("Image migration completed successfully.")
            
    except Exception as e:
        logger.error(f"Error during image migration: {e}")

# Run migration on startup
migrate_images_to_public_folder()

# ==============================================================================
# DER FINALE SOUND-RETTER (Manuelle Route)
# ==============================================================================

# 1. Pfade bestimmen
if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
    frontend_build_dir = base_path / "frontend" / "dist"
else:
    # Passe das hier an deine Struktur an, falls nötig
    base_path = Path(__file__).resolve().parent.parent 
    frontend_build_dir = base_path / "frontend" / "dist"

# 2. Die Manuelle Sound-Route (Zwingt den Browser zur Kooperation)
@app.get("/sounds/{filename}")
async def get_sound(filename: str):
    # Wir bauen den Pfad zur Datei im dist/sounds Ordner
    sound_file = frontend_build_dir / "sounds" / filename
    
    if not sound_file.exists():
        # Debugging-Hilfe, falls es doch schief geht
        logger.error(f"SOUND FEHLER: Datei nicht gefunden unter: {sound_file}")
        raise HTTPException(status_code=404, detail="Sound not found")

    try:
        logger.info(f"Sound wird ausgeliefert (/sounds): {sound_file} ({sound_file.stat().st_size} bytes)")
    except Exception:
        logger.info(f"Sound wird ausgeliefert (/sounds): {sound_file}")
        
    # HIER IST DER TRICK: media_type="audio/mpeg"
    # Das zwingt den Browser, es als Audio zu erkennen.
    return FileResponse(path=sound_file, media_type="audio/mpeg")

# ==============================================================================
# SOUND-API (Der sichere Weg)
# ==============================================================================
@app.get("/api/system/camera_sound")
async def get_camera_sound():
    sound_candidates = [
        get_resource_path("backend/assets/camera-shutter-199580.mp3"),
        get_resource_path("frontend/dist/sounds/camera-shutter-199580.mp3"),
        get_resource_path("backend/static/camera-shutter-199580.mp3"),
    ]

    for sound_path in sound_candidates:
        if os.path.exists(sound_path):
            try:
                logger.info(f"Camera-Sound wird ausgeliefert (/api/system/camera_sound): {sound_path} ({os.path.getsize(sound_path)} bytes)")
            except Exception:
                logger.info(f"Camera-Sound wird ausgeliefert (/api/system/camera_sound): {sound_path}")
            return FileResponse(sound_path, media_type="audio/mpeg")

    logger.error(f"Sound-Datei fehlt. Geprüfte Pfade: {sound_candidates}")
    raise HTTPException(status_code=404, detail="Sound file missing")


# ==============================================================================
# D11: Debug Compression Engine Endpoint (Workaround für Router-Loading Issue)
# ==============================================================================
@app.get("/api/system/debug-summary")
async def get_debug_summary():
    """
    D11: Debug Compression Engine — Returns compressed debug diagnosis as Markdown.
    
    Analyzes recent logs using the LogAnalyzer (heuristics + LLM summary)
    and returns a clean Markdown summary for AI Studio debugging.
    """
    try:
        import asyncio
        from backend.services.logging.debug_engine import DebugEngine, get_speed_tier_model
        from backend.data.schemas_logging import LogEventCreate
        from datetime import datetime
        
        # Get provider and model for LLM
        provider, model = get_speed_tier_model()
        logger.info(f"[DEBUG-SUMMARY] Using {provider}/{model} for LLM summary")
        
        # Initialize Debug Engine
        engine = DebugEngine(provider=provider, model=model)
        
        # Timeout-Guard: Fetch logs mit 5 Sekunden Timeout
        try:
            logs = await asyncio.wait_for(
                engine.fetcher.fetch_logs(limit=100),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("[DEBUG-SUMMARY] Timeout bei Log-Fetch")
            return "# Debug Summary\n\nTimeout bei Log-Analyse (5s exceeded)."
        
        if not logs:
            return "# Debug Summary\n\nKeine relevanten Logs für eine Analyse vorhanden (RAM-Buffer leer oder keine Logs in den letzten 10 Minuten)."
        
        # Convert LogEntry to LogEvent for _run_heuristics
        events = []
        for log in logs:
            event = LogEventCreate(
                timestamp=log.timestamp,
                level=log.level,
                message=log.message,
                event_type="log"
            )
            events.append(event)
        
        # Timeout-Guard: Heuristik mit 5 Sekunden Timeout (non-blocking via run_in_executor)
        try:
            findings = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    engine.analyzer._run_heuristics,
                    events
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("[DEBUG-SUMMARY] Timeout bei Heuristik-Analyse")
            return "# Debug Summary\n\nTimeout bei Heuristik-Analyse (5s exceeded)."
        
        # Generate heuristic summary
        heuristic_summary = engine.analyzer.generate_heuristic_summary(findings)
        
        # Build Markdown response
        markdown_parts = []
        markdown_parts.append("# 🐛 Debug Summary")
        markdown_parts.append(f"\n**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        markdown_parts.append(f"**Logs Analyzed:** {len(logs)}")
        markdown_parts.append(f"**Confidence Score:** {findings['confidence_score']:.2f}")
        markdown_parts.append("")
        
        # Heuristic Findings
        markdown_parts.append("## 🔍 Heuristic Findings")
        markdown_parts.append("")
        markdown_parts.append("```")
        markdown_parts.append(heuristic_summary)
        markdown_parts.append("```")
        markdown_parts.append("")
        
        # Quick Summary
        markdown_parts.append("## 📋 Quick Summary")
        markdown_parts.append("")
        if findings['hard_errors']:
            markdown_parts.append(f"- **Hard Errors:** {len(findings['hard_errors'])}")
        if findings['model_drift']:
            markdown_parts.append(f"- **Model Drift:** {len(findings['model_drift'])}")
        if findings['latency_spikes']:
            markdown_parts.append(f"- **Latency Spikes:** {len(findings['latency_spikes'])}")
        if not any([findings['hard_errors'], findings['model_drift'], findings['latency_spikes']]):
            markdown_parts.append("- No critical issues detected")
        
        markdown_parts.append("")
        markdown_parts.append("---")
        markdown_parts.append("")
        markdown_parts.append("*Generated by D11 Debug Compression Engine*")
        
        return "\n".join(markdown_parts)
        
    except Exception as e:
        logger.error("[DEBUG-SUMMARY] Failed to generate debug summary: %s", e, exc_info=True)
        return f"# Debug Summary\n\nFehler bei der Log-Analyse: {str(e)}"


# 3. Frontend Mount (Muss ganz unten stehen)
if os.path.exists(frontend_build_dir):
    logger.info(f"Frontend wird gemountet von: {frontend_build_dir}")
    app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True), name="frontend")
else:
    logger.critical(f"FATAL: Frontend-Verzeichnis für Mount nicht gefunden: {frontend_build_dir}")

# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    import sys

    # Ghost-Process detection log
    print("💎 DIAMOND-OS BACKEND STARTING ON PORT 8001...")

    try:
        # Server starten (Produktionsversion ohne Reload)
        uvicorn.run(app, host="127.0.0.1", port=8001)
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        sys.exit(1)
