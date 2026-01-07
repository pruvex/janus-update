# backend/data/schemas.py

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from typing import List, Literal, Optional, Dict, Any


# --- Tool Schemas ---
class GenerateImageToolArgs(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = Field(
        "standard",
        description="Die Qualität des generierten Bildes. Unterstützte Werte sind 'standard' und 'hd'.",
        pattern="^(standard|hd)$"
    )
    response_format: Optional[str] = "url"


class CrossChatMemoryToolArgs(BaseModel):
    query: str


# --- Message Schemas ---
class MessageBase(BaseModel):
    sender: str
    content: str
    image_path: Optional[str] = None


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    chat_id: int
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )


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
    project_id: Optional[int] = None


# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass


class ProjectCreateWithContext(ProjectBase):
    active_provider: str
    active_model: str

class ProjectFileResponse(BaseModel):
    id: int
    filename: str
    file_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    files: List[ProjectFileResponse] = []

    class Config:
        from_attributes = True

# --- Chat Schemas ---
class ChatBase(BaseModel):
    title: Optional[str] = "Neuer Chat"


class ChatCreate(ChatBase):
    project_id: Optional[int] = None


class Chat(ChatBase):
    id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    project_id: Optional[int] = None

    class Config:
        from_attributes = True


class ChatResponse(ChatBase):
    id: int
    title: str
    created_at: datetime
    is_archived: bool
    project_id: Optional[int] = None

    class Config:
        from_attributes = True


class ChatTitleUpdate(BaseModel):
    title: str


# --- Filesystem Tool Schemas ---
class CreateFileArgs(BaseModel):
    path: str
    content: Optional[str] = ""
    is_binary: Optional[bool] = False


class SaveMp3Args(BaseModel):
    content: str = Field(
        ...,
        description="Der zu vertonende Text.",
    )
    filename: str = Field(..., description="Der Zieldateiname für die MP3.")
    voice: Optional[str] = Field(
        "fable",
        description="Stimme zur Vertonung.",
    )


class ReadFileArgs(BaseModel):
    path: str


class DeleteFileArgs(BaseModel):
    path: str


class ListDirectoryArgs(BaseModel):
    path: str
    pattern: Optional[str] = None


class CreateDirectoryArgs(BaseModel):
    path: str


class DeleteDirectoryArgs(BaseModel):
    path: str


class MoveFileArgs(BaseModel):
    source_path: str
    destination_path: str


class RenameFileArgs(BaseModel):
    old_path: str
    new_path: str


class MoveFilesArgs(BaseModel):
    source_directory: str
    destination_directory: str
    pattern: str


class ListAllowedWorkspacesArgs(BaseModel):
    pass


class FindLocalBusinessArgs(BaseModel):
    query: str = Field(..., description="Was gesucht wird.")
    location: Optional[str] = Field(None, description="Der Ort.")


class WebsearchToolArgs(BaseModel):
    query: str = Field(..., description="Die Suchanfrage.")


class ReadUrlContentArgs(BaseModel):
    url: str = Field(..., description="Die vollständige URL.")


class CreatePdfFromMarkdownArgs(BaseModel):
    content: str = Field(..., description="Der Inhalt der PDF-Datei im Markdown-Format.")
    filename: str = Field(..., description="Der gewünschte Dateiname.")
    location: str = Field("Documents", description="Der Speicherort.")
    include_image: bool = Field(False, description="Bild einfügen?")
    font_size: int = Field(default=11, description="Die Schriftgröße.")
    image_width: int = Field(default=0, description="Die gewünschte Breite des Bildes.")


class GetWeatherFromApiToolArgs(BaseModel):
    city: str = Field(..., description="Die Stadt.")
    date_str: Optional[str] = Field(None, description="Optional: Ein Datum.")


class GetCountryInfoToolArgs(BaseModel):
    country_name: str = Field(..., description="Der offizielle englische Name des Landes.")
    info_type: str = Field(..., description="Die Art der Information.")


class GetLatestNewsRssToolArgs(BaseModel):
    query: Optional[str] = Field(None, description="Das Thema.")
    source: Optional[str] = Field(None, description="Die spezifische Quelle.")


class GetWikipediaSummaryArgs(BaseModel):
    query: str = Field(..., description="Das Thema.")
    lang: str = Field("de", description="Sprachcode.")


class GetCalendarEventsArgs(BaseModel):
    days_in_future: Optional[int] = Field(7, description="Anzahl Tage.")
    start_date: Optional[str] = Field(None, description="Startdatum.")
    end_date: Optional[str] = Field(None, description="Enddatum.")


class CreateCalendarEventArgs(BaseModel):
    summary: str = Field(..., description="Titel.")
    start_time_str: str = Field(..., description="Startzeit.")
    location: Optional[str] = Field(default=None, description="Ort.")
    description: Optional[str] = Field(default=None, description="Details.")


class DeleteCalendarEventArgs(BaseModel):
    event_id: str = Field(..., description="ID des Termins.")


class UpdateCalendarEventArgs(BaseModel):
    event_id: str = Field(..., description="ID des Termins.")
    summary: Optional[str] = Field(None, description="Neuer Titel.")
    start_time_str: Optional[str] = Field(None, description="Neue Startzeit.")
    end_time_str: Optional[str] = Field(None, description="Neue Endzeit.")
    location: Optional[str] = Field(None, description="Neuer Ort.")
    description: Optional[str] = Field(None, description="Neue Beschreibung.")


class FindAddressAndUpdateCalendarEventArgs(BaseModel):
    event_title_query: str = Field(..., description="Schlüsselwörter aus dem Titel.")
    location_query: str = Field(..., description="Suchanfrage für Adresse.")


# --- STRUCTURED MEMORY SCHEMAS (V2) ---

# Type Definitions
Predicate = Literal[
    "is", "owns", "name_is", "likes", "allergic_to", "prefers_food", "lives_in"
]
SubjectRole = Literal["user", "pet", "relative"]
RelativeType = Literal[
    "grandmother", "uncle", "aunt", "grandfather", 
    "mother", "father", "sister", "brother", "cousin", "unknown"
]
PetType = Literal["cat", "dog", "unknown"]

class MemoryCategory(str, Enum):
    GESUNDHEIT = "Gesundheit"
    BEZIEHUNGEN = "Beziehungen"
    HAUSTIER_DETAILS = "Haustier-Details"
    VORLIEBEN = "Vorlieben"
    BERUF = "Beruf"
    TERMINE = "Termine"
    ALLGEMEIN = "Allgemein"

class ExtractedFact(BaseModel):
    """Structured fact extracted from user conversation."""
    fact: str = Field(..., description="Der extrahierte Fakt (Deutsch, Template-konform).")
    category: MemoryCategory
    
    # Make these fields optional with default values
    type: Optional[Literal["CORE_IDENTITY", "CORE_DETAIL", "EPHEMERAL", "GENERAL"]] = "GENERAL"
    expires_in_hours: Optional[int] = None
    
    # Make these fields optional with default values
    canonical_key: Optional[str] = Field(None, description="Kanonischer Schlüssel, z.B. 'likes|relative:grandmother:gertrude|cats'")
    subject_role: Optional[str] = None  # Changed from SubjectRole to str
    subject_pet_type: Optional[str] = None  # Changed from PetType to str
    subject_relative_type: Optional[str] = None  # Changed from RelativeType to str
    subject_name: Optional[str] = None
    predicate: Optional[str] = None  # Changed from Predicate to str
    object_value: Optional[str] = None
    evidence: Optional[str] = Field(None, description="Kurzes Zitat aus dem User-Text.")

class FactExtractionResponse(BaseModel):
    """Response containing extracted facts from LLM."""
    facts: List[ExtractedFact]

# Legacy memory models (keep for backward compatibility)
class MemoryBase(BaseModel):
    snippet: str
    category: MemoryCategory = MemoryCategory.ALLGEMEIN
    is_core_fact: bool = False
    core_priority: int = 0

class MemoryCreate(MemoryBase):
    pass

class MemoryUpdate(BaseModel):
    snippet: Optional[str] = None
    category: Optional[MemoryCategory] = None
    is_core_fact: Optional[bool] = None
    core_priority: Optional[int] = None

class MemoryResponse(MemoryBase):
    id: int
    chat_id: int
    created_at: datetime
    last_accessed_at: Optional[datetime]
    expires_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Gmail Tool Schemas ---

class GetLatestEmailsArgs(BaseModel):
    max_results: Optional[int] = Field(5, description="Max emails.")
    query: Optional[str] = Field(None, description="Search query.")
    fetch_body: bool = Field(False, description="Fetch body?")


class SendEmailArgs(BaseModel):
    to: str = Field(..., description="Empfänger.")
    subject: str = Field(..., description="Betreff.")
    body: str = Field(..., description="Inhalt.")
    attachment_path: Optional[str] = Field(None, description="Anhang Pfad.")


class FindFreeTimeSlotsArgs(BaseModel):
    year: int = Field(..., description="Jahr.")
    month: int = Field(..., description="Monat.")
    location_for_weather: Optional[str] = Field(None, description="Ort für Wetter.")


class UpdateCalendarEventDescriptionArgs(BaseModel):
    event_title_query: str = Field(..., description="Titel Query.")
    new_description_part: str = Field(..., description="Text zum Hinzufügen.")


class SaveCoreMemoryToolArgs(BaseModel):
    fact: str = Field(..., description="Der reine Fakt.")
    category: str = Field(..., description="Kategorie.")


class FindAndUpdateCalendarEventArgs(BaseModel):
    event_title_query: str = Field(..., description="Titel Query.")
    new_summary: Optional[str] = Field(None, description="Neuer Titel.")
    new_start_time: Optional[str] = Field(None, description="Neue Startzeit.")
    new_end_time: Optional[str] = Field(None, description="Neue Endzeit.")
    new_location: Optional[str] = Field(None, description="Neuer Ort.")
    new_description: Optional[str] = Field(None, description="Neue Beschreibung.")
    cancel_event: Optional[bool] = Field(default=False, description="Stornieren?")


class ReadEmailArgs(BaseModel):
    email_id: str = Field(description="ID der E-Mail.")


class GetDistanceArgs(BaseModel):
    origin: str = Field(..., description="Startort.")
    destination: str = Field(..., description="Zielort.")
    mode: str = Field("driving", description="Reiseart.")


# --- Planner/Reasoner Layer Schemas ---

class PlannerKeyExtraction(BaseModel):
    """Das ultra-schlanke Output-Schema für den 'Zero-Thinking' Planner."""
    relevant_indices: List[int] = Field(..., description="Eine Liste der Indizes der relevanten Fakten.")


class CandidateAnalysis(BaseModel):
    """Analysis of a single candidate in the decision-making process."""
    candidate_identifier: str = Field(..., description="Unique identifier for the candidate, e.g., 'relative:grandmother:gertrude'")
    candidate_name: str = Field(..., description="Human-readable name of the candidate")
    is_viable: bool = Field(..., description="Whether this candidate is currently viable")
    reasoning_summary: str = Field(..., description="Concise summary of the analysis for this candidate")
    pros: List[Dict] = Field(default_factory=list, description="Positive aspects supporting this candidate (vereinfacht zu Dict).")
    cons: List[Dict] = Field(default_factory=list, description="Negative aspects against this candidate (vereinfacht zu Dict).")
    final_score: float = Field(0.0, description="Numeric score for this candidate")


class DecisionContext(BaseModel):
    """
    Structured decision context generated by the Planner/Reasoner layer.
    """
    status: Literal["ok", "need_more_info", "cannot_answer"] = Field(
        ..., 
        description="Overall status of the decision process"
    )
    task_summary: str = Field(..., description="Concise summary of the user's task or question")
    analysis_summary: str = Field(..., description="Brief summary of the analysis results")
    recommendations: List[CandidateAnalysis] = Field(
        default_factory=list, 
        description="List of analyzed candidates with recommendations"
    )
    clarifying_questions: Optional[List[str]] = Field(
        None, 
        description="Questions needed to proceed, if status is 'need_more_info'"
    )
    assumptions_made: Optional[List[str]] = Field(
        None, 
        description="Any assumptions made during the analysis"
    )


class SetLastUsedModelRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None


class GetLastUsedModelResponse(BaseModel):
    provider: Optional[str]
    model: Optional[str]


class FindContactAndSendEmailArgs(BaseModel):
    name_query: str = Field(..., description="Name Query.")
    subject: str = Field(..., description="Betreff.")
    body: str = Field(..., description="Inhalt.")

# --- Image Studio Schemas ---

class GeminiHistory(BaseModel):
    prompt: str
    image_base64: str

class ImageParameters(BaseModel):
    model_config = ConfigDict(extra='allow')

class GeneratedImageBase(BaseModel):
    prompt: Optional[str] = None
    style_preset: Optional[Dict[str, str]] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    parameters: Optional[ImageParameters] = None
    image_url: str
    is_uploaded: bool = False

class GeneratedImageCreate(BaseModel):
    prompt: str
    provider: str
    model: str
    parameters: Optional[Dict[str, Any]] = None
    reference_image_url: Optional[str] = None
    reference_image_urls: Optional[List[str]] = []
    previous_response_id: Optional[str] = None
    previous_image_id: Optional[str] = None
    mask_image_data: Optional[str] = None
    
    style_preset: Optional[str] = None
    variation_preset: Optional[str] = None
    apply_preset_to_edit: bool = False
    
    quality_gate_level: Optional[str] = "none"
    quality_gate_stats: Optional[Dict[str, Any]] = None

class GeneratedImage(GeneratedImageBase):
    id: int
    created_at: datetime
    previous_response_id: Optional[str] = None
    previous_image_id: Optional[str] = None
    quality_gate_stats: Optional[Dict[str, Any]] = None
    style_preset: str = ""

    class Config:
        from_attributes = True

class ImageRenameRequest(BaseModel):
    old_path: str = Field(..., description="Pfad alt.")
    new_filename: str = Field(..., description="Dateiname neu.")