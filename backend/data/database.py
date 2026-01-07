import datetime
import logging
import os
import re # NEU: Für RegEx zum Parsen der Bildgröße

import datetime
import logging
import os
import re # NEU: Für RegEx zum Parsen der Bildgröße

from backend.utils.encryption import EncryptedString
from backend.utils.paths import get_app_data_dir
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    func,
    text,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

logger = logging.getLogger("janus_backend")

# --- Haupt-Datenbank für Chats und Memory ---
DB_PATH = os.path.join(get_app_data_dir(), "chat_history.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# FastAPI Dependency: DB-Session bereitstellen
def get_db():
    """Yieldet eine DB-Session für Requests und schließt sie danach."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Modelle ---
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True) # Bleibt unverschlüsselt für die Anzeige
    created_at = Column(DateTime, default=datetime.datetime.now)
    summary = Column(EncryptedString, nullable=True) # Verschlüsselt
    summary_embedding_json = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    memories = relationship("Memory", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="chats")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender = Column(String) # Bleibt unverschlüsselt ('user' oder 'assistant')
    content = Column(EncryptedString) # Verschlüsselt
    image_path = Column(EncryptedString, nullable=True) # Verschlüsselt
    timestamp = Column(DateTime, default=datetime.datetime.now)
    chat = relationship("Chat", back_populates="messages")


class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True)
    
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    snippet = Column(EncryptedString, nullable=False)
    embedding_json = Column(String, nullable=False)
    
    # --- NEUE FELDER HINZUFÜGEN ---
    normalized_text = Column(String, nullable=False, server_default='')
    text_hash = Column(String, nullable=False, server_default='')
    # --- ENDE NEUE FELDER ---
    
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_accessed_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )
    
    expires_at = Column(DateTime, nullable=True)
    retain_until = Column(DateTime, nullable=True)
    
    category = Column(String, default="Allgemein", nullable=False)  # Default auf Deutsch ändern
    is_core_fact = Column(Boolean, default=False, nullable=False)
    core_priority = Column(Integer, default=0, nullable=False)

    chat = relationship("Chat", back_populates="memories")

    __table_args__ = (
        Index('ix_memories_chat_expiry', 'chat_id', 'expires_at'),
        Index('ix_memories_chat_retain', 'chat_id', 'retain_until'),
        Index('ix_memories_chat_core', 'chat_id', 'is_core_fact', 'core_priority'),
        Index('ix_memories_access', 'last_accessed_at'),
        # Diese Zeile erzwingt, dass pro Chat jeder Fakt nur einmal vorkommen kann
        Index('ix_memories_chat_hash', 'chat_id', 'text_hash', unique=True, sqlite_where=text("text_hash != ''")),
    )


class LongTermMemory(Base):
    __tablename__ = "long_term_memory"
    id = Column(Integer, primary_key=True, index=True)
    original_memory_id = Column(Integer)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    snippet = Column(EncryptedString, nullable=False) # Verschlüsselt
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime)
    archived_at = Column(DateTime, default=datetime.datetime.now)


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(EncryptedString, nullable=False, index=True) # Verschlüsselt
    category = Column(String, default="Unkategorisiert", nullable=False)
    email = Column(EncryptedString, nullable=True, unique=True, index=True) # Verschlüsselt
    phone = Column(EncryptedString, nullable=True) # Verschlüsselt
    address = Column(EncryptedString, nullable=True) # Verschlüsselt
    website = Column(EncryptedString, nullable=True) # Verschlüsselt
    notes = Column(EncryptedString, nullable=True) # Verschlüsselt
    created_at = Column(DateTime, default=datetime.datetime.now)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(EncryptedString, index=True, nullable=False) # Verschlüsselt
    description = Column(EncryptedString, nullable=True) # Verschlüsselt
    created_at = Column(DateTime, default=datetime.datetime.now)

    chats = relationship("Chat", back_populates="project")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")


class ProjectFile(Base):
    __tablename__ = "project_files"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(EncryptedString, nullable=False) # Verschlüsselt
    local_path = Column(EncryptedString, nullable=False) # Verschlüsselt
    file_type = Column(String)
    
    openai_file_id = Column(String, nullable=True) 
    gemini_file_uri = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.now)

    project = relationship("Project", back_populates="files")


class GeneratedImage(Base):
    __tablename__ = "generated_images"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(EncryptedString, nullable=True) # Verschlüsselt
    style_preset = Column(String, nullable=True)
    variation_preset = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    image_url = Column(String, nullable=False)
    is_uploaded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    previous_response_id = Column(String, nullable=True)
    previous_image_id = Column(String, nullable=True)
    quality_gate_stats = Column(JSON, nullable=True)
    provider_response_id = Column(String, nullable=True)



# --- Kosten-Datenbank ---
COSTS_DB_PATH = os.path.join(get_app_data_dir(), "costs.db")
COSTS_DATABASE_URL = f"sqlite:///{COSTS_DB_PATH}"
costs_engine = create_engine(COSTS_DATABASE_URL, connect_args={"check_same_thread": False})
CostsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=costs_engine)
CostsBase = declarative_base()

# Alias für Tests (Kompatibilität zu bestehenden Testfällen)
DATABASE_FILE = COSTS_DB_PATH


class Cost(CostsBase):
    __tablename__ = "costs"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.now)
    model = Column(String, index=True)  # Index hinzugefügt für schnellere Abfragen
    provider = Column(String, index=True, nullable=True)  # NEUE SPALTE
    source_type = Column(String, index=True, nullable=True)  # NEUE SPALTE
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    image_quality = Column(String, nullable=True)
    image_size = Column(String, nullable=True) # NEUE SPALTE
    image_cost = Column(Float, nullable=True)
    total_cost = Column(Float)


# --- Initialisierungs-Funktion ---
def init_db():
    try:
        # 1. Tabellen erstellen (existierende werden ignoriert)
        Base.metadata.create_all(bind=engine)
        CostsBase.metadata.create_all(bind=costs_engine)
        
        # 2. Migrationen und Index-Checks
        with engine.connect() as conn:
            # A) Check 'project_id' in 'chats'
            columns_info = conn.execute(text("PRAGMA table_info(chats)")).fetchall()
            column_names = [col[1] for col in columns_info]
            
            if "project_id" not in column_names:
                logger.info("Migration: Füge 'project_id' Spalte zur Tabelle 'chats' hinzu.")
                conn.execute(text("ALTER TABLE chats ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
            
            # B) Manuelle Index-Prüfung (Falls create_all sie verpasst hat oder bei Migrationen)
            # Wichtig: Wir nutzen text() für den SQL String!
            existing_indices_result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name IN (
                    'ix_memories_chat_expiry',
                    'ix_memories_chat_retain',
                    'ix_memories_chat_core',
                    'ix_memories_access'
                )
            """)).fetchall()
            
            existing_names = [row[0] for row in existing_indices_result]

            # Indizes explizit erstellen, falls sie fehlen
            if 'ix_memories_chat_expiry' not in existing_names:
                 conn.execute(text("CREATE INDEX IF NOT EXISTS ix_memories_chat_expiry ON memories (chat_id, expires_at)"))
            
            if 'ix_memories_chat_retain' not in existing_names:
                 conn.execute(text("CREATE INDEX IF NOT EXISTS ix_memories_chat_retain ON memories (chat_id, retain_until)"))

            if 'ix_memories_chat_core' not in existing_names:
                 conn.execute(text("CREATE INDEX IF NOT EXISTS ix_memories_chat_core ON memories (chat_id, is_core_fact, core_priority)"))

            if 'ix_memories_access' not in existing_names:
                 conn.execute(text("CREATE INDEX IF NOT EXISTS ix_memories_access ON memories (last_accessed_at)"))

            conn.commit()
        
    except OperationalError as e:
        logger.warning(f"Database schema warning (safe to ignore if app works): {e}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        # Wir raisen hier nicht, damit der Server bei kleinen DB-Warnungen trotzdem startet


# --- Kosten-spezifische DB-Funktionen ---
def get_costs_for_month(year, month):
    db = CostsSessionLocal()
    try:
        total_cost = (
            db.query(func.sum(Cost.total_cost))
            .filter(
                func.strftime("%Y", Cost.date) == str(year),
                func.strftime("%m", Cost.date) == str(month).zfill(2),
            )
            .scalar()
        )
        return total_cost if total_cost is not None else 0.0
    finally:
        db.close()


def get_costs_summary_by_model_for_current_month():
    db = CostsSessionLocal()
    try:
        today = datetime.datetime.now()
        current_month_costs = (
            db.query(Cost)
            .filter(
                func.strftime("%Y", Cost.date) == str(today.year),
                func.strftime("%m", Cost.date) == str(today.month).zfill(2),
            )
            .all()
        )

        summary = {}
        for cost_entry in current_month_costs:
            model_name = cost_entry.model
            if model_name not in summary:
                summary[model_name] = {
                    "model": model_name,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "image_count": 0,
                    "total_cost": 0.0,
                    "image_details": [] # NEU: Für detaillierte Bildinfos
                }

            summary[model_name]["total_cost"] += (cost_entry.total_cost or 0.0)

            if cost_entry.input_tokens is not None:
                summary[model_name]["total_input_tokens"] += cost_entry.input_tokens
            if cost_entry.output_tokens is not None:
                summary[model_name]["total_output_tokens"] += cost_entry.output_tokens
            
            if cost_entry.image_cost is not None and cost_entry.image_cost > 0:
                summary[model_name]["image_count"] += 1
                # Extrahiere quality und size aus dem Modelnamen für detailliertere Anzeige
                quality = cost_entry.image_quality if cost_entry.image_quality else "N/A"
                size = cost_entry.image_size if cost_entry.image_size else "N/A" # NEU: Direkt aus DB
                
                summary[model_name]["image_details"].append({
                    "quality": quality,
                    "size": size,
                    "cost": cost_entry.image_cost # Einzelkosten des Bildes
                })

        return list(summary.values())
    finally:
        db.close()


def get_all_cost_entries():
    """Liefert alle Kosten-Einträge als Liste von Dicts, nach Datum DESC sortiert."""
    db = CostsSessionLocal()
    try:
        entries = db.query(Cost).order_by(Cost.date.desc()).all()
        result = []
        for e in entries:
            result.append(
                {
                    "id": e.id,
                    "date": e.date,
                    "model": e.model,
                    "input_tokens": e.input_tokens,
                    "output_tokens": e.output_tokens,
                    "image_quality": e.image_quality,
                    "image_cost": e.image_cost,
                    "total_cost": e.total_cost,
                }
            )
        return result
    finally:
        db.close()


def save_cost_entry(
    date,
    model,
    input_tokens,
    output_tokens,
    image_quality,
    image_size, # NEUER PARAMETER
    image_cost,
    total_cost,
    provider=None,
    source_type=None,
):
    db = CostsSessionLocal()
    new_cost = Cost(
        date=date,
        model=model,
        provider=provider,
        source_type=source_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        image_quality=image_quality,
        image_size=image_size, # NEU
        image_cost=image_cost,
        total_cost=total_cost,
    )
    db.add(new_cost)
    db.commit()
    db.close()
