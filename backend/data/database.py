# backend/data/database.py
import logging
import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("janus_backend")

# --- 1. Pfad-Logik (Lokal definiert für maximale Sicherheit) ---
def get_db_url():
    """Ermittelt den Pfad zur Datenbank im AppData Ordner."""
    test_db_url = os.getenv("JANUS_TEST_DB_URL")
    if test_db_url:
        logger.info("Nutze Test-Datenbank aus JANUS_TEST_DB_URL: %s", test_db_url)
        return test_db_url

    try:
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser("~")
        
        # Ordner erstellen: %APPDATA%/Janus Projekt
        janus_dir = os.path.join(app_data, "Janus Projekt")
        os.makedirs(janus_dir, exist_ok=True)
        
        db_path = os.path.join(janus_dir, "janus.db")
        return f"sqlite:///{db_path}"
    except Exception as e:
        # Fallback falls irgendwas mit den Pfaden schief läuft
        logger.critical(f"Konnte DB-Pfad nicht ermitteln: {e}")
        return "sqlite:///./janus_fallback.db"

# --- 2. SQLAlchemy Setup ---
SQLALCHEMY_DATABASE_URL = get_db_url()


# Wir erhöhen den Timeout auf 30 Sekunden (verhindert 'database is locked')
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_reset_on_return="rollback",
)

# WICHTIG: WAL Mode aktivieren (Write-Ahead Logging)
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _ensure_sqlite_schema_migrations() -> None:
    """Apply lightweight ALTERs for existing SQLite DBs (Drift vs. Alembic / create_all)."""
    try:
        url = str(engine.url)
        if not url.startswith("sqlite"):
            return
        insp = inspect(engine)

        if insp.has_table("users"):
            user_cols = {c["name"] for c in insp.get_columns("users")}
            if "suggestion_mode" not in user_cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN suggestion_mode INTEGER NOT NULL DEFAULT 1"
                        )
                    )
                logger.info("Migration: users.suggestion_mode added (default=1).")

        if insp.has_table("chats"):
            chat_cols = {c["name"] for c in insp.get_columns("chats")}
            if "category" not in chat_cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE chats ADD COLUMN category VARCHAR NOT NULL DEFAULT 'general'"
                        )
                    )
                logger.info("Migration: chats.category added (default='general').")
            if "auto_generated" not in chat_cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE chats ADD COLUMN auto_generated BOOLEAN NOT NULL DEFAULT 1"
                        )
                    )
                logger.info("Migration: chats.auto_generated added (default=1).")

        if insp.has_table("memories"):
            memory_cols = {c["name"] for c in insp.get_columns("memories")}
            if "user_editable" not in memory_cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE memories ADD COLUMN user_editable BOOLEAN NOT NULL DEFAULT 1"
                        )
                    )
                logger.info("Migration: memories.user_editable added (default=1).")
            if "source_type" not in memory_cols:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE memories ADD COLUMN source_type VARCHAR DEFAULT 'text'"
                        )
                    )
                logger.info("Migration: memories.source_type added (default='text').")
    except Exception:
        logger.warning(
            "SQLite schema migration skipped or failed (non-fatal).",
            exc_info=True,
        )


def __getattr__(name: str):
    """Backward-compatible lazy exports for legacy imports."""
    if name in {"Memory", "Chat", "Message"}:
        from backend.data import models

        return getattr(models, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# --- 3. Dependency für FastAPI Routen ---
def get_db_sync() -> Generator:
    """Synchroner Generator für Datenbank-Sessions (Legacy-Aufrufer)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Fehler beim Schließen der DB-Session: {e}")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator:
    """Asynchroner Session-Context, der DB-Sessions immer sauber schließt."""
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Fehler beim Schließen der DB-Session (async): {e}")


async def get_db() -> AsyncGenerator:
    """FastAPI-Dependency: liefert Session via async Context-Management."""
    async with get_db_session() as db:
        yield db


@contextmanager
def get_db_context():
    """Context-Manager für kurze, explizit geschlossene DB-Sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. Init-Funktion (Der Fix für die fehlenden Tabellen) ---
def init_db():
    """
    Initialisiert die Tabellen. 
    Importiert Modelle erst HIER, um Circular Import Errors zu verhindern.
    """
    logger.info(f"Initialisiere Datenbank: {SQLALCHEMY_DATABASE_URL}")
    try:
        # Modelle registrieren (Side-Effect auf Base.metadata), bevor create_all läuft.
        import backend.data.models  # noqa: F401

        # Tabellen erstellen (macht nichts, wenn sie schon da sind)
        Base.metadata.create_all(bind=engine)
        _ensure_sqlite_schema_migrations()
        logger.info("Datenbank-Initialisierung erfolgreich.")
        
    except Exception as e:
        logger.error(
            "Error in database.init_db: SQLAlchemy initialization failed",
            exc_info=True,
        )
        raise RuntimeError(
            f"Kritischer Datenbankfehler bei Initialisierung ({SQLALCHEMY_DATABASE_URL})."
        ) from e