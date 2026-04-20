# backend/data/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, LargeBinary, Text, JSON, text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.data.database import Base

# --- Encryption Support ---
try:
    from backend.utils.encryption import EncryptedString
    ContentType = EncryptedString
except ImportError:
    try:
        from utils.encryption import EncryptedString
        ContentType = EncryptedString
    except ImportError:
        # Safe fallback for environments without encryption module
        ContentType = Text

# --- MODELLE ---

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    active_provider = Column(String, default="openai", nullable=True)
    active_model = Column(String, default="gpt-5.4-nano", nullable=True)
    
    chats = relationship("Chat", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String)
    file_path = Column(String)
    file_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="files")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    is_indexed = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)
    audit_status = Column(String, default="new", nullable=False)

    project = relationship("Project", back_populates="documents", primaryjoin="Project.id == Document.project_id")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    category = Column(String, nullable=False, default="general", server_default=text("'general'"))
    auto_generated = Column(Boolean, default=True, nullable=False)
    last_topic_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(ContentType, nullable=True)
    summary_embedding_json = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    project = relationship("Project", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="chat", cascade="all, delete-orphan")
    skill_telemetry_entries = relationship("SkillTelemetry", back_populates="chat", cascade="all, delete-orphan")
    orchestrator_kpi_entries = relationship("OrchestratorKPI", back_populates="chat", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)

    chat = relationship("Chat", back_populates="messages")

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)
    snippet = Column(ContentType, nullable=True)
    embedding_json = Column(LargeBinary, nullable=True)
    normalized_text = Column(String, nullable=True)
    text_hash = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    retain_until = Column(DateTime, nullable=True)
    category = Column(String, default="conversation")
    is_core_fact = Column(Boolean, default=False)
    core_priority = Column(Integer, default=0)
    source_type = Column(String, default="text", nullable=True) # "text", "vision", "document"
    source_metadata = Column(JSON, nullable=True) # Für Bild-Hashes, Seitenzahlen etc.
    
    # NEW: Memory Schema V2.1.0 Columns
    priority = Column(Float, default=0.5, nullable=False)
    memory_type = Column(String(20), default="GENERAL", nullable=False)
    ttl = Column(Integer, nullable=True)
    tags = Column(JSON, default=list, nullable=True)
    source_skill = Column(String(100), nullable=True)
    user_editable = Column(Boolean, default=True, nullable=False)
    canonical_key = Column(String(255), nullable=True)
    change_history = Column(JSON, default=list, nullable=True)

    chat = relationship("Chat", back_populates="memories")

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    notes = Column(ContentType, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    category = Column(String, nullable=True)

# --- COMPLETE GENERATED IMAGE MODEL ---
class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String)
    
    # Presets
    style_preset = Column(String, nullable=True)
    variation_preset = Column(String, nullable=True)
    
    # Pfade
    file_path = Column(String) # Lokaler Pfad
    url = Column(String, nullable=True) # Web Pfad / URL
    
    # Provider Infos
    provider = Column(String, default="openai")
    model = Column(String, nullable=True)
    
    # Metadaten
    created_at = Column(DateTime, default=datetime.utcnow)
    parameters = Column(JSON, nullable=True) # Hier speichern wir techn. Parameter
    
    # Upload & Management
    is_uploaded = Column(Boolean, default=False)
    content_hash = Column(String, index=True, nullable=True)
    tags = Column(String, nullable=True)
    
    # Verknüpfungen / Historie
    previous_response_id = Column(String, nullable=True)
    previous_image_id = Column(String, nullable=True)
    provider_response_id = Column(String, nullable=True)
    
    # Quality Gate
    quality_gate_stats = Column(JSON, nullable=True)

    # --- FIX: Alias für Abwärtskompatibilität ---
    # Diese Eigenschaft leitet Anfragen für 'image_url' an das Feld 'url' weiter.
    @property
    def image_url(self):
        return self.url

    @image_url.setter
    def image_url(self, value):
        self.url = value

class Cost(Base):
    __tablename__ = "costs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    provider = Column(String)
    model = Column(String)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    context = Column(String, nullable=True)


class SkillTelemetry(Base):
    __tablename__ = "skill_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    trace_id = Column(String, index=True, nullable=False)
    skill_id = Column(String, index=True, nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    error_code = Column(String, nullable=True)
    arguments_json = Column(JSON, nullable=True)
    response_json = Column(JSON, nullable=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)

    chat = relationship("Chat", back_populates="skill_telemetry_entries")


class OrchestratorKPI(Base):
    __tablename__ = "orchestrator_kpis"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    provider = Column(String, nullable=False, index=True)
    model = Column(String, nullable=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True, index=True)
    is_meta_agent_run = Column(Boolean, default=False, nullable=False)
    t_phase1_research_ms = Column(Float, nullable=True)
    t_phase2_pdf_ms = Column(Float, nullable=True)
    t_final_response_ms = Column(Float, nullable=False, default=0.0)
    retry_path = Column(String, nullable=False, default="none", index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_code = Column(String, nullable=True)

    chat = relationship("Chat", back_populates="orchestrator_kpi_entries")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    # Suggestion-engine preference (1 = default on); reserved for future UI modes
    suggestion_mode = Column(Integer, default=1, nullable=False)

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, index=True)
    name = Column(String)
    scopes = Column(String) 
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class AppState(Base):
    __tablename__ = "app_state"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

# --- VISION / FACE RECOGNITION MODELS ---

class PersonProfile(Base):
    __tablename__ = "person_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # z.B. "Maggie"
    
    # Optionale Metadaten (Haarfarbe, Stil etc. als JSON)
    features = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    encodings = relationship("FaceEncoding", back_populates="person", cascade="all, delete-orphan") # NEU

class FaceEncoding(Base):
    __tablename__ = "face_encodings"
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person_profiles.id")) # WICHTIG: Fremdschlüssel auf "person_profiles.id"
    encoding = Column(LargeBinary, nullable=False)
    person = relationship("PersonProfile", back_populates="encodings")


class Task(Base):
    """Task model with progress tracking support."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)  # pending, in_progress, completed, failed
    
    # Progress tracking fields (0-100)
    progress = Column(Integer, default=0, nullable=False)
    progress_log = Column(JSON, default=list, nullable=True)  # History of progress updates
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Optional relationships
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    chat = relationship("Chat", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
