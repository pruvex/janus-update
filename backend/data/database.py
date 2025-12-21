import datetime
import logging
import os
import re # NEU: Für RegEx zum Parsen der Bildgröße

from backend.utils.paths import get_app_data_dir
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
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
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    summary = Column(String, nullable=True)
    summary_embedding_json = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # HINZUGEFÜGT: Definiert die "andere Seite" der Beziehung.
    # Ein Chat kann viele Memory-Einträge haben.
    # "cascade" sorgt dafür, dass beim Löschen eines Chats auch alle zugehörigen Memories gelöscht werden.
    memories = relationship("Memory", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="chats")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender = Column(String)
    content = Column(Text)
    image_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    chat = relationship("Chat", back_populates="messages")


class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    snippet = Column(String, nullable=False)
    embedding_json = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    last_accessed_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )
    expires_at = Column(DateTime, nullable=True)  # Für kurzlebige Erinnerungen

    # NEU: Ersetzt das alte 'is_core_fact' durch ein flexibleres Kategoriesystem.
    category = Column(String, default="General Fact", nullable=False)
    is_core_fact = Column(Boolean, default=False, nullable=False)  # Markiert Kern-Erinnerungen

    chat = relationship("Chat", back_populates="memories")


# --- NEUE TABELLE FÜR DAS LANGZEITGEDÄCHTNIS ---
class LongTermMemory(Base):
    __tablename__ = "long_term_memory"
    id = Column(Integer, primary_key=True, index=True)
    original_memory_id = Column(Integer)  # Um den Ursprung nachzuverfolgen
    chat_id = Column(Integer, ForeignKey("chats.id"))
    snippet = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=True)
    created_at = Column(DateTime)  # Wir übernehmen den ursprünglichen Zeitstempel
    archived_at = Column(DateTime, default=datetime.datetime.now)


# --- NEUE TABELLE FÜR DAS ADRESSBUCH ---
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, default="Unkategorisiert", nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Beziehungen
    chats = relationship("Chat", back_populates="project")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")


class ProjectFile(Base):
    __tablename__ = "project_files"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    local_path = Column(String, nullable=False)  # Pfad im lokalen Dateisystem
    file_type = Column(String)  # z.B. 'pdf', 'txt', 'url_dump'
    
    # Provider-spezifische IDs (für Hybrid-Nutzung)
    openai_file_id = Column(String, nullable=True) 
    gemini_file_uri = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.now)

    project = relationship("Project", back_populates="files")


class GeneratedImage(Base):
    __tablename__ = "generated_images"
    id = Column(Integer, primary_key=True, index=True)
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Vorerst auskommentiert
    prompt = Column(Text, nullable=True)
    style_preset = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    image_url = Column(String, nullable=False)
    is_uploaded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)



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
        
        # 2. Migration: Prüfen ob 'project_id' in 'chats' existiert (für Bestands-User)
        with engine.connect() as conn:
            # SQLite spezifischer Check
            columns_info = conn.execute(text("PRAGMA table_info(chats)")).fetchall()
            column_names = [col[1] for col in columns_info]  # Index 1 ist der Name
            
            if "project_id" not in column_names:
                logger.info("Migration: Füge 'project_id' Spalte zur Tabelle 'chats' hinzu.")
                conn.execute(text("ALTER TABLE chats ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
                conn.commit()
        
    except OperationalError as e:
        logger.warning(f"Database schema mismatch or locked: {e}.")
    except Exception as e:
        logger.error(f"Error creating/migrating database: {e}", exc_info=True)
        raise


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
