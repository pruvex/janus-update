# backend/data/schemas.py

from datetime import datetime
from enum import Enum
import json
from typing import List, Optional, Dict, Any, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# --- Tool Schemas ---
class GenerateImageToolArgs(BaseModel):
    prompt: str = Field(
        ...,
        description=(
            "Detaillierte Bildbeschreibung — für OpenAI/DALL·E- und vergleichbare Modelle "
            "**möglichst auf Englisch** formulieren (bessere Bildqualität und Treffer). "
            "WICHTIG: Nutze IMMER DIESES Tool für Bilder/Fotos. NIEMALS create_pdf für Bilder nutzen!"
        ),
    )
    size: Optional[str] = Field(
        "1024x1024",
        description="Das gewünschte Bildformat. Standard ist '1024x1024'."
    )
    quality: Optional[str] = Field(
        "low",
        description="Bildqualität. Standard für den Chat ist 'low'. Erlaubte Werte: low, standard, hd.",
        pattern="^(low|standard|hd)$"
    )
    response_format: Optional[str] = Field(
        "url",
        description="Immer 'url' nutzen."
    )


class CrossChatMemoryToolArgs(BaseModel):
    query: str


class SearchSummariesArgs(BaseModel):
    query: str = Field(
        ..., description="Der Suchbegriff oder die Frage nach vergangenen Ereignissen."
    )


class GrantPermissionArgs(BaseModel):
    skill_id: str = Field(
        ...,
        description="Die exakte kanonische Skill-ID, die dauerhaft freigegeben werden soll (z.B. 'communication.read_email' oder 'filesystem.delete_file').",
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Legacy-Kompatibilitätsfeld. Wenn gesetzt, wird es intern auf die kanonische Skill-ID normalisiert.",
    )


class RevokePermissionArgs(BaseModel):
    skill_id: str = Field(
        ...,
        description="Die exakte kanonische Skill-ID, deren dauerhafte Freigabe entzogen werden soll.",
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Legacy-Kompatibilitätsfeld. Wenn gesetzt, wird es intern auf die kanonische Skill-ID normalisiert.",
    )


_KNOWLEDGE_VS_MEMORY = (
    "Nur für Inhalte aus hochgeladenen Dokumenten (PDFs) in der Wissensdatenbank/Chroma. "
    "NICHT verwenden, um dauerhafte Nutzer-Fakten zu speichern — dafür ist memory.write gedacht. "
    "NICHT für Smalltalk-Erinnerungen: gesprächsbezogene Fakten über den User → memory.write / memory.read."
)


class QueryKnowledgeBaseArgs(BaseModel):
    query_text: str = Field(
        ...,
        description=(
            "Stichwortsuche in indexierten Dokumenten (semantische Treffer, z.B. 'Hauptstadt', '§12'). "
            + _KNOWLEDGE_VS_MEMORY
        ),
    )
    filename: Optional[str] = Field(
        None,
        description="PFLICHT wenn die User-Anfrage einen Dateinamen enthält (z.B. 'aegypten.pdf'): Setze hier den exakten Dateinamen ein, um die Suche auf diese Datei einzuschränken. Ohne diesen Parameter werden ALLE Dokumente durchsucht, was zu falschen Ergebnissen führt!",
    )
    n_results: Optional[int] = Field(10, description="Maximale Anzahl Chunks/Treffer (Standard 10).")


class OpenKnowledgeDocumentArgs(BaseModel):
    filename: str = Field(
        ...,
        description=(
            "Dateiname aus der Wissensdatenbank; öffnet die PDF in der UI. "
            + _KNOWLEDGE_VS_MEMORY
        ),
    )


class ListKnowledgeDocumentsArgs(BaseModel):
    limit: Optional[int] = Field(100, description="Maximale Anzahl an Dokumenten in der Antwort.")
    filter_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optionaler Metadaten-Filter für die Dokumentliste. "
            "Liste verfügbarer PDFs — nicht mit memory.read verwechseln (das ist Langzeitgedächtnis)."
        ),
    )


class GetFullDocumentTextArgs(BaseModel):
    filename: str = Field(
        ...,
        description=(
            "Volltext eines registrierten Dokuments (DB/Chroma/PDF-Datei). "
            + _KNOWLEDGE_VS_MEMORY
        ),
    )
    absolute_path: Optional[str] = Field(
        None,
        description="Path-Pinning for Disambiguation: Nutze dieses Feld, um eine spezifische Dublette via absolutem Pfad zu lesen, wenn das System dich dazu auffordert (z.B. '[NICHT INDIZIERT - AKTION ERFORDERLICH...]'). Wenn absolute_path gesetzt ist, hat dieser Parameter ABSOLUTE PRIORITÄT: filename wird ignoriert, keine Dubletten-Prüfung, direktes Lesen vom angegebenen Pfad.",
    )


class PdfTextModification(BaseModel):
    search: str = Field(..., description="Der exakte, wörtliche Text aus der PDF, der ersetzt werden soll.")
    replace: str = Field(..., description="Der korrigierte Text. Für Löschen leer lassen.")


class EditPdfTextInPlaceArgs(BaseModel):
    original_filename: str = Field(
        ...,
        description=(
            "PDF im Benutzer-Dokumentenordner, die korrigiert werden soll (Wissens-/Dokumentenkontext). "
            "Kein Ersatz für memory.update — dort geht es um gespeicherte Nutzer-Fakten, nicht um PDF-Bytes."
        ),
    )
    modifications: Optional[List[PdfTextModification]] = Field(
        default=None,
        description="Batch-Liste aller Korrekturen. Bevorzugter Modus.",
    )
    edit_mode: Optional[Literal["inplace", "rebuild_v1"]] = Field(
        default=None,
        description="Optionaler Ausführungsmodus. Ohne Angabe entscheidet die Runtime per Env-Default (sonst 'inplace'). 'rebuild_v1' ist aktuell ein sicherer Fallback-Pfad.",
    )
    shadow_run: Optional[bool] = Field(
        default=False,
        description="Wenn true, werden zusätzlich Layout-Artefakte für Vergleich/QC erzeugt, ohne den Outputmodus zu ändern.",
    )
    search_text: Optional[str] = Field(
        default=None,
        description="Legacy: einzelner Suchtext. Wird intern in 'modifications' umgewandelt.",
    )
    replace_text: Optional[str] = Field(
        default=None,
        description="Legacy: einzelner Ersatztext. Wird intern in 'modifications' umgewandelt.",
    )


class HardenedEditPdfArgs(BaseModel):
    original_filename: str = Field(
        ...,
        description="PDF mit Backup-Workflow bearbeiten (sicherer Composite). Dokumenten-Tool, nicht Gedächtnis.",
    )
    modifications: List[PdfTextModification] = Field(
        ...,
        description="Batch-Liste aller Korrekturen fuer den sicheren Edit-Lauf.",
    )
    backup_directory: Optional[str] = Field(
        default="backups",
        description="Zielordner fuer die Sicherungskopie innerhalb des Workspaces.",
    )


# --- Skill Contract Schemas ---
class SkillResponse(BaseModel):
    status: Literal["ok", "error", "permission_required", "dry_run_success"]
    data: Any = None
    error: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None


class SkillMetadata(BaseModel):
    description: Optional[str] = Field(
        default=None,
        description="Menschenlesbare Skill-Beschreibung (für Agent-Planner Prompts und UI).",
    )
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    latency_class: Literal["fast", "normal", "slow"] = "normal"
    tags: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    sandbox_level: Literal["unrestricted", "workspace_only", "read_only_fs", "full"] = "unrestricted"
    depends_on: List[str] = Field(default_factory=list)
    is_agent_ready: bool = True
    max_calls_per_turn: int = Field(default=3, ge=1)
    optimal_model_tier: Optional[Union[str, Dict[str, str]]] = Field(
        default=None,
        description="MoA-Tier für Skill-Level Model-Routing. Kann String (legacy) oder Dict {provider: tier} sein. Erlaubte Werte: 'speed', 'logic', 'vision', 'balanced'. None = User-Basismodell.",
    )
    timeout_ms: Optional[int] = Field(
        default=None,
        description="Maximale Ausführungszeit in ms. Wird vom ToolExecutor via asyncio.wait_for() enforced.",
    )
    output_schema: Optional[Any] = Field(
        default=None,
        description="Optionales Pydantic-Modell (Klasse) zur zentralen Output-Validierung durch den Executor. Wird programmatisch gesetzt, nicht aus JSON geladen.",
    )
    synthesis_directives: Optional[str] = Field(
        default=None,
        description="Prompt-Direktive die automatisch in den System-Prompt injiziert wird wenn dieser Skill aktiv ist.",
    )
    output_schema_hint: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON-Schema-Hint aus dem Skill-JSON. Wird dem LLM als Strukturvorgabe mitgegeben.",
    )
    deterministic_renderer: bool = Field(
        default=False,
        description="Wenn true, MUSS die Ausgabe menschlicher Text sein. JSON-Ausgabe wird als Fehler behandelt.",
    )


# --- Price Comparison Output Contract ---
class PriceEntry(BaseModel):
    product_name: str
    variant: Optional[str] = None
    price: float = Field(..., ge=0, description="Preis in lokaler Währung")
    currency: str = Field(default="EUR")
    source: str = Field(..., description="z.B. 'idealo.de' oder 'geizhals.de'")
    condition: Literal["new", "refurbished"] = "new"
    includes_shipping: bool = False
    url: Optional[str] = None
    # Verification Phase fields
    live_verified: bool = Field(default=False, description="Ob der Preis durch Live-Crawl verifiziert wurde")
    live_price: Optional[float] = Field(default=None, description="Verifizierter Live-Preis (kann vom snippet-Preis abweichen)")
    verified_at: Optional[str] = Field(default=None, description="ISO-Timestamp der Verifikation")
    verification_status: Optional[str] = Field(default=None, description="Status: 'verified', 'mismatch', 'unavailable', 'skipped'")


class PriceComparisonOutput(BaseModel):
    query: str
    locale: str = "de_DE"
    currency: str = "EUR"
    results: List[PriceEntry]
    refurbished_tip: Optional[PriceEntry] = None
    retrieved_at: str = Field(..., description="ISO-Timestamp der Abfrage")


# --- Websearch Output Contract V2.0 ---
class WebSearchItem(BaseModel):
    title: str = Field(..., description="Titel des Suchergebnisses")
    description: Optional[str] = Field(None, description="Kurzbeschreibung / Snippet")
    date: Optional[str] = Field(None, description="Erscheinungsdatum (ISO oder Freitext)")
    source_url: str = Field(..., description="URL der Quelle")
    thumbnail_url: Optional[str] = Field(None, description="[ROADMAP] Thumbnail-URL des Eintrags")


class WebSearchOutput(BaseModel):
    query: str = Field(..., description="Normalisierte Suchanfrage")
    locale: str = Field(default="de_DE")
    items: List[WebSearchItem] = Field(default_factory=list, description="Strukturierte Ergebnis-Liste aus sources")
    text: str = Field(default="", description="Rohtext des LLM für die Synthese (backward compat)")
    price_enrichment: Optional[Dict[str, Any]] = Field(None, description="Internes Ergebnis aus system.price_comparison (Seamless Integration Ebene 8)")
    source: str = Field(default="unknown", description="Provider-Name (openai/gemini/duckduckgo)")
    retrieved_at: str = Field(..., description="ISO-Timestamp der Abfrage")


class VideoSearchInput(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        description="Natuerliche Suchanfrage fuer ein YouTube-Video (z.B. 'Pizzateig Anleitung').",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=15,
        description="Anzahl der Kandidaten fuer das Ranking vor Endauswahl.",
    )
    min_views: int = Field(
        default=10000,
        ge=0,
        le=2_000_000_000,
        description="Mindestanzahl Views fuer valide Kandidaten.",
    )
    safe_search: bool = Field(
        default=True,
        description="YouTube SafeSearch strict (True) oder none (False).",
    )
    wants_latest: bool = Field(
        ...,
        description=(
            "PFLICHTFELD. True, wenn der Nutzer explizit das neueste/aktuellste/letzte Video verlangt. "
            "Bei normaler Themensuche ohne Neuheitswunsch muss False gesetzt werden."
        ),
    )
    channel_name: str = Field(
        ...,
        description=(
            "MUSS-FELD BEI KANALSUCHE: Wenn der User einen Creator oder Kanal nennt (z.B. 'von XY', "
            "'Kanal XY', 'bei XY'), MUSS der Name 'XY' exakt hier eingetragen werden. Ein leerer String ('') "
            "ist STRENGSTENS VERBOTEN, sobald ein Creator im Text impliziert wird und führt zu falschen Ergebnissen!"
        ),
    )
    # NEU: List-Mode Support (Task 030)
    mode: str = Field(
        default="single",
        description=(
            "PFLICHTFELD. 'single' = ein bestes Video (Standard). "
            "'list' = mehrere Videos als Liste zurueckgeben. "
            "MUSS 'list' sein wenn der Nutzer Woerter wie 'letzten N', 'alle', 'mehrere', 'videos' (Plural) verwendet."
        ),
    )
    published_after: Optional[str] = Field(
        default=None,
        description="ISO-8601 Datum (YYYY-MM-DD). Nur Videos NACH diesem Datum. Nur bei explizitem Datumswunsch setzen.",
    )
    published_before: Optional[str] = Field(
        default=None,
        description="ISO-8601 Datum (YYYY-MM-DD). Nur Videos VOR diesem Datum. Nur bei explizitem Datumswunsch setzen.",
    )
    topic_query: Optional[str] = Field(
        default=None,
        description="Themen-Filter fuer Listen. Z.B. 'elden ring'. YouTube search API wird mit diesem Term + channelId kombiniert.",
    )


class VideoResult(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11)
    title: str
    channel: str
    views: int = Field(..., ge=0)
    thumbnail: str
    watch_url: str
    embed_url: str
    is_embeddable: bool = True
    published_date_human: Optional[str] = Field(
        default=None,
        description="Human-readable upload date formatted as DD.MM.YYYY (e.g., '13.04.2026')."
    )


class VideoSearchOutput(BaseModel):
    # Universal-Container: Single-Mode (selected_video) oder List-Mode (videos, count, mode)
    selected_video: Optional[VideoResult] = Field(None, description="Einzelnes Video (Single-Mode).")
    videos: Optional[List[VideoResult]] = Field(None, description="Liste von Videos (List-Mode).")
    count: Optional[int] = Field(0, ge=0, description="Anzahl der Videos (List-Mode).")
    mode: str = Field("single", description="Modus: 'single' oder 'list'.")
    query: str = Field(..., description="Normalisierte Suchanfrage.")
    retrieved_at: str = Field(..., description="ISO-Timestamp der Abfrage.")


# NEU: Video List Output für List-Mode (Task 030)
class VideoListOutput(BaseModel):
    videos: List[VideoResult] = Field(..., description="Liste der gefundenen Videos.")
    count: int = Field(..., ge=0, description="Anzahl der Videos in der Liste.")
    query: str = Field(..., description="Normalisierte Suchanfrage.")
    retrieved_at: str = Field(..., description="ISO-Timestamp der Abfrage.")
    mode: str = Field(default="list", description="Modus: 'list' für Video-Liste.")


class VideoUnderstandingInput(BaseModel):
    video_id: str = Field(
        ...,
        min_length=11,
        max_length=11,
        description="YouTube Video-ID (11 Zeichen). Kann aus video.search Result entnommen werden.",
    )
    task: str = Field(
        ...,
        description=(
            "PFLICHTFELD. Aufgabentyp: "
            "'summarize' = Zusammenfassung mit Key Points. "
            "'explain' = Vereinfachte Erklärung. "
            "'extract_steps' = Schritt-für-Schritt Anleitung extrahieren."
        ),
    )
    language: str = Field(
        default="de",
        description="Zielsprache für die Ausgabe (ISO 639-1). Standard: 'de'.",
    )
    detail_level: str = Field(
        default="medium",
        description="Detaillevel: 'brief' (3-5 Sätze), 'medium' (strukturiert), 'detailed' (ausführlich).",
    )
    source: str = Field(
        default="chat",
        description="Aufrufquelle: 'chat' (User-Chat-Eingabe) oder 'ui_button' (Video-Player Brain-Button). Nur 'ui_button' erlaubt die Ausführung.",
    )


class VideoUnderstandingOutput(BaseModel):
    video_id: str = Field(..., min_length=11, max_length=11)
    task: str = Field(..., description="Ausgeführter Task-Typ.")
    title: str = Field("", description="Video-Titel (falls verfügbar).")
    summary: str = Field(..., description="Hauptergebnis der Analyse.")
    key_points: List[str] = Field(default_factory=list, description="Kernaussagen als Liste.")
    structured_notes: Optional[Dict[str, Any]] = Field(
        None, description="Strukturierte Notizen (nur bei extract_steps)."
    )
    transcript_source: str = Field(
        ..., description="Quelle: 'youtube_captions', 'yt_dlp', 'whisper_stt', 'unavailable'."
    )
    transcript_language: str = Field("", description="Erkannte Sprache des Transkripts.")
    chunk_count: int = Field(0, ge=0, description="Anzahl verarbeiteter Chunks.")


class AgentSpec(BaseModel):
    name: str
    goal: str
    required_skills: List[str] = Field(default_factory=list)
    instructions: str
    max_iterations: int = Field(default=5, ge=1)


class PlannerProviderProfile(BaseModel):
    """Runtime profile for planner prompting and deterministic planning."""

    provider: str
    requested_model: Optional[str] = None
    planner_model: str
    model_class: Literal["nano", "mini", "standard", "logic", "local"] = "standard"
    is_local: bool = False
    max_iterations_cap: int = Field(default=8, ge=1, le=12)
    allow_llm_planning: bool = True


class PlannerContext(BaseModel):
    """Structured handoff from Intent Engine and orchestrator into AgentPlanner."""

    original_user_text: str = ""
    allowed_skill_ids: List[str] = Field(default_factory=list)
    required_skill_ids: List[str] = Field(default_factory=list)
    priority_skill_ids: List[str] = Field(default_factory=list)
    forbidden_skill_ids: List[str] = Field(default_factory=list)
    negative_constraints: List[str] = Field(default_factory=list)
    completed_skills: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    round_idx: int = Field(default=1, ge=1)
    lockdown_after_pdf: bool = False
    deterministic_planning_allowed: bool = True


# --- Message Schemas ---
class MessageBase(BaseModel):
    sender: str
    content: str
    image_path: Optional[str] = None
    modal_request: Optional[Dict[str, Any]] = None
    video_list_metadata: Optional[Dict[str, Any]] = None


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    chat_id: int
    sender: str
    content: str
    timestamp: datetime
    image_path: Optional[str] = None
    modal_request: Optional[Dict[str, Any]] = None
    video_list_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        populate_by_name = True

    @model_validator(mode='before')
    @classmethod
    def map_db_fields(cls, data: Any) -> Any:
        # Wenn wir ein Datenbank-Objekt bekommen (SQLAlchemy Model)
        if hasattr(data, 'role') and hasattr(data, 'created_at'):
            # 1. Role zu Sender mappen
            role = getattr(data, 'role', 'user')
            sender = "model" if role == "assistant" else role
            
            # 2. Created_at zu Timestamp mappen
            timestamp = getattr(data, 'created_at', datetime.utcnow())
            image_path = None
            modal_request = None
            video_list_metadata = None
            metadata_json = getattr(data, 'metadata_json', None)
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                    if isinstance(metadata, dict):
                        candidate = metadata.get("image_path")
                        if candidate:
                            image_path = str(candidate)
                        mr_candidate = metadata.get("modal_request")
                        if isinstance(mr_candidate, dict):
                            modal_request = mr_candidate
                        vlm_candidate = metadata.get("video_list_metadata")
                        if isinstance(vlm_candidate, dict):
                            video_list_metadata = vlm_candidate
                except Exception:
                    image_path = None
                    modal_request = None
                    video_list_metadata = None
            
            # Wir geben ein Dict zurück, das Pydantic versteht
            return {
                "id": data.id,
                "chat_id": data.chat_id,
                "sender": sender,
                "content": data.content,
                "timestamp": timestamp,
                # Image Path aus metadata holen (falls vorhanden), sonst None
                "image_path": image_path,
                "modal_request": modal_request,
                "video_list_metadata": video_list_metadata,
            }
        return data


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
    api_key: Optional[str] = None
    chat_id: Optional[int] = None
    project_id: Optional[int] = None
    audit_file: Optional[str] = None  # 💎 ANTI-HALLUCINATION: Marker for file upload audit intent


class ModalRequestOptions(BaseModel):
    """MCL-Optionen für automatisches Öffnen / Taskleiste (Universal Modal Dossier)."""

    model_config = ConfigDict(extra="ignore")

    auto_open: bool = True
    pinnable: bool = True


class ModalRequest(BaseModel):
    """Optionales Feld in der Chat-API-Antwort: UI öffnet ein Dock-Modal (z. B. Video-Embed)."""

    model_config = ConfigDict(extra="ignore")

    type: str = Field(..., min_length=1, description="MCL-Typ, z. B. video, image, document.")
    payload: Dict[str, Any] = Field(default_factory=dict)
    options: ModalRequestOptions = Field(default_factory=ModalRequestOptions)


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


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    upload_date: datetime
    is_indexed: bool
    error_message: Optional[str] = None
    audit_status: str

    class Config:
        from_attributes = True

# --- Chat Schemas ---
class ChatBase(BaseModel):
    title: Optional[str] = "Neuer Chat"
    category: str = "general"


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
    auto_generated: bool = True
    last_topic_hash: Optional[str] = None

    class Config:
        from_attributes = True


class ChatTitleUpdate(BaseModel):
    title: str


# --- Filesystem Tool Schemas ---
_WORKSPACE_PATH_DESC = (
    "Absoluter Pfad oder pfad relativ zum konfigurierten Workspace. "
    "Nur innerhalb der freigegebenen Workspace-Verzeichnisse erlaubt. "
    "Keine Pfadsegmente '..' (kein Ausbruch aus dem Workspace)."
)


class CreateFileArgs(BaseModel):
    file_path: str = Field(..., description=_WORKSPACE_PATH_DESC)
    content: Optional[str] = ""
    is_binary: Optional[bool] = Field(
        False,
        description="True nur bei Binärdaten; sonst Text als UTF-8.",
    )


class SaveMp3Args(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        description="Der zu vertonende Text. Darf nicht leer sein.",
    )
    filename: str = Field(
        ...,
        min_length=1,
        description="Der Zieldateiname für die MP3 (z.B. 'mein_audio.mp3'). Endung '.mp3' wird automatisch ergänzt falls fehlend.",
    )
    voice: Optional[str] = Field(
        "fable",
        description="Stimme zur Vertonung (z.B. 'fable', 'alloy', 'echo', 'nova', 'onyx', 'shimmer').",
    )


class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description=_WORKSPACE_PATH_DESC)


class DeleteFileArgs(BaseModel):
    file_path: str = Field(..., description=_WORKSPACE_PATH_DESC)


class ListDirectoryArgs(BaseModel):
    path: str = Field(
        ...,
        description=(
            "Workspace-Pfad zum Auflisten. '.' oder leer listet die Namen der freigegebenen Workspaces. "
            + _WORKSPACE_PATH_DESC
        ),
    )
    pattern: Optional[str] = Field(
        None,
        description=(
            "Optionales Glob-Muster relativ zum angegebenen Ordner (z.B. '*.txt'). "
            "Keine '..' im Muster."
        ),
    )


class CreateDirectoryArgs(BaseModel):
    path: str = Field(..., description=_WORKSPACE_PATH_DESC)


class DeleteDirectoryArgs(BaseModel):
    path: str = Field(..., description=_WORKSPACE_PATH_DESC)


class MoveFileArgs(BaseModel):
    source_path: str = Field(..., description=_WORKSPACE_PATH_DESC)
    destination_path: str = Field(..., description=_WORKSPACE_PATH_DESC)


class RenameFileArgs(BaseModel):
    old_path: str = Field(..., description=_WORKSPACE_PATH_DESC)
    new_path: str = Field(..., description=_WORKSPACE_PATH_DESC)


class MoveFilesArgs(BaseModel):
    source_directory: str = Field(..., description=_WORKSPACE_PATH_DESC)
    destination_directory: str = Field(..., description=_WORKSPACE_PATH_DESC)
    file_names: List[str] = Field(
        ...,
        description="Liste der exakten Dateinamen im Quellordner, die verschoben werden sollen.",
    )


class FindFilesArgs(BaseModel):
    pattern: str = Field(
        ...,
        description=(
            "Dateinamen-Glob für die rekursive Suche (z.B. '*.pdf', '*gundula*', 'gundula1.pdf'). "
            "KEINE Pfadsegmente, nur Dateinamen. Wenn das Pattern weder '*' noch '?' enthält, "
            "wird automatisch Substring-Suche verwendet (z.B. 'gundula' → '*gundula*')."
        ),
    )
    root: Optional[str] = Field(
        None,
        description=(
            "Optional: Startordner (Workspace-relativer oder absoluter Pfad). "
            "Wenn leer/None, werden ALLE freigegebenen Workspaces rekursiv durchsucht — "
            "das ist der empfohlene Default, wenn der User keinen Pfad nennt."
        ),
    )
    max_results: Optional[int] = Field(
        100,
        ge=1,
        le=1000,
        description="Obergrenze für Treffer (1–1000, Default 100).",
    )
    search_all_drives: Optional[bool] = Field(
        False,
        description=(
            "Wenn True: durchsucht ALLE lokalen Laufwerke (C:\\, D:\\, ...) — nicht nur freigegebene Workspaces. "
            "SETZE DIESEN PARAMETER AUF TRUE, wenn der User Formulierungen wie 'überall', 'auf dem ganzen Rechner', "
            "'alle Kopien', 'Duplikate', 'wo liegt die Datei überall' benutzt, ODER wenn ein vorheriger find_files-Aufruf "
            "ohne dieses Flag nur 0 oder 1 Treffer lieferte und der User mehr Instanzen erwartet. "
            "Dauert deutlich länger (mehrere Sekunden), überspringt aber automatisch System-/Noise-Ordner. "
            "Wird ignoriert, wenn 'root' gesetzt ist."
        ),
    )


class ListAllowedWorkspacesArgs(BaseModel):
    """Keine Parameter; listet konfigurierte Workspace-Stammverzeichnisse (Orientierung für erlaubte Pfade)."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": (
                "Ruft die freigegebenen Workspace-Pfade ab. Keine Pfadargumente; nutze die "
                "zurückgegebenen Wurzelverzeichnisse, um gültige absolute oder relative Pfade zu wählen."
            )
        }
    )


class FindLocalBusinessArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Was gesucht wird: Geschäftsart oder Stichwort (z.B. 'Italienisches Restaurant', 'Apotheke 24h', 'Baumarkt'). "
            "Kurz und sachlich; keine ganzen Nutzersätze."
        ),
        min_length=2,
        pattern=r".*\S.*",
    )
    location: str = Field(
        ...,
        description=(
            "Geografischer Bezug im Format **Stadt, Land** oder **Stadtteil, Stadt, Land** "
            "(z.B. 'Berlin, Deutschland', 'Prenzlauer Berg, Berlin, Deutschland', 'Hamburg, DE'). "
            "Je konkreter Straße/PLZ bekannt sind, desto besser die Trefferqualität."
        ),
        min_length=2,
        pattern=r".*\S.*",
    )
    limit: int = Field(
        5,
        ge=1,
        le=10,
        description="Maximale Anzahl der gewünschten Treffer. Standard ist 5, maximal 10.",
    )


class LocalLLMNodeBase(BaseModel):
    name: str = Field(..., description="Interner Name des lokalen LLM-Nodes.")
    base_url: str = Field(..., description="Grundlegende URL des lokalen Nodes.")
    api_key: Optional[str] = Field(None, description="Optionaler API-Key, falls der Node ihn erfordert.")
    is_active: bool = Field(True, description="Aktivierungsstatus des Nodes.")


class LocalLLMNodeCreate(LocalLLMNodeBase):
    pass


class LocalLLMNode(LocalLLMNodeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WebsearchArgsV2(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        description=(
            "Der genaue Suchbegriff oder die Frage für die Live-Websuche (z.B. 'Aktueller Goldpreis Feinunze EUR', "
            "'iPhone 16 Pro Testbericht'). Mindestens 2 Zeichen; konkret formulieren, damit der Provider passende Treffer liefert."
        ),
    )
    provider: Optional[str] = Field(
        None,
        description=(
            "Optional: Websuche-Backend überschreiben (z.B. 'openai', 'gemini', 'ollama'). "
            "Leer lassen, damit die Runtime den passenden Provider zur aktuellen Janus-Session wählt."
        ),
    )
    model: Optional[str] = Field(
        None,
        description="Optional: Modell-ID für den gewählten Provider (z.B. OpenAI/Gemini-Modellname). Nur setzen, wenn der Nutzer ein bestimmtes Modell verlangt.",
    )


class WebsearchToolArgs(WebsearchArgsV2):
    """Legacy Alias für bestehende Imports/Pfade."""


class ReadUrlContentArgs(BaseModel):
    url: str = Field(
        ...,
        min_length=8,
        description=(
            "Vollständige HTTP(S)-URL der Seite, deren sichtbarer Text extrahiert werden soll "
            "(z.B. 'https://example.com/artikel'). Muss mit http:// oder https:// beginnen; keine Kurz-URLs ohne Schema."
        ),
    )


class ScrapeWebsiteArgs(BaseModel):
    """Strikte Eingabe für system.scrape_website."""
    url: str = Field(
        ...,
        min_length=8,
        description="Die vollständige URL der zu scrapenden Webseite (z.B. 'https://example.com/page'). Muss mit http:// oder https:// beginnen.",
    )


class CreatePdfFromMarkdownArgs(BaseModel):
    content: str = Field(..., description="Der Inhalt der PDF-Datei im Markdown-Format.")
    filename: str = Field(..., description="Der gewünschte Dateiname.")
    location: str = Field(
        "Documents",
        min_length=1,
        max_length=260,
        pattern=r"^[A-Za-z0-9_ .:\\/-]+$",
        description="Zielordner als sandboxed Pfad-String innerhalb erlaubter Workspaces.",
    )
    include_image: bool = Field(False, description="Bild einfügen?")
    font_size: int = Field(default=11, ge=8, le=20, description="Die Schriftgröße.")
    image_width: int = Field(default=0, ge=0, le=800, description="Die gewünschte Breite des Bildes.")
    layout_profile: str = Field(
        default="auto",
        description="Layout-Profil: auto, bericht, bilderbuch, praesentation, magazin.",
    )
    source_prompt: str = Field(
        default="",
        description="Optionaler ursprünglicher Nutzerprompt für Auto-Layout-Erkennung.",
    )
    dry_run: bool = Field(False, description="Wenn true, nur Vorschau erzeugen und keine Datei schreiben.")

    @field_validator("location")
    @classmethod
    def validate_sandboxed_location(cls, value: str) -> str:
        path_value = str(value or "").strip()
        if not path_value:
            raise ValueError("location darf nicht leer sein.")
        normalized = path_value.replace("\\", "/")
        if ".." in [part for part in normalized.split("/") if part]:
            raise ValueError("location darf keine Parent-Traversal-Segmente ('..') enthalten.")
        return path_value


class GetWeatherFromApiToolArgs(BaseModel):
    city: str = Field(
        ...,
        min_length=2,
        description="Die Stadt für die Wettervorhersage (z.B. 'Berlin', 'Hamburg', 'München'). Mindestens 2 Zeichen.",
    )
    date_str: Optional[str] = Field(
        None,
        description="Optionales Datum oder Wochentag (z.B. 'heute', 'morgen', 'Samstag', '2026-03-20'). Ohne Angabe wird 'heute' verwendet.",
    )


class CountryInfoArgs(BaseModel):
    country: str = Field(
        ...,
        min_length=2,
        description=(
            "Ländername oder gängige englische/deutsche Bezeichnung "
            "(z.B. 'Deutschland', 'France', 'United States', 'JP'). Keine Adressen — nur das Land."
        ),
    )
    language: str = Field(
        "de",
        min_length=2,
        max_length=5,
        description="Die gewünschte Ausgabesprache als ISO-639 Code (z. B. 'de' für Deutsch, 'en' für Englisch).",
    )


class GetCountryInfoToolArgs(CountryInfoArgs):
    """Legacy Alias für bestehende Imports/Pfade."""


class GetLatestNewsRssToolArgs(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Optionales Thema zum Filtern der Schlagzeilen (z.B. 'Nintendo', 'KI', 'Fußball'). Ohne Angabe werden alle Top-Schlagzeilen geliefert.",
    )
    source: Optional[str] = Field(
        None,
        description="Die spezifische Quelle: 'spiegel', 'gamestar', 'tagesschau', 'zeit', 'heise', 'reuters', 'bbc'.",
    )


class GetWikipediaSummaryArgs(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        description="Der genaue Suchbegriff für Wikipedia (z.B. 'Eiffelturm', 'Thermodynamik', 'Albert Einstein'). Mindestens 2 Zeichen.",
    )
    lang: str = Field(
        "de",
        min_length=2,
        max_length=5,
        description="Wikipedia-Sprachcode (z.B. 'de' für Deutsch, 'en' für Englisch).",
    )


_CAL_DATETIME_HINT = (
    "Bevorzugt **ISO 8601** mit Datum und Uhrzeit in lokaler Nutzerzeit, Zeitzone Europe/Berlin "
    "(z.B. `2026-04-15T14:30:00` oder `2026-04-15T14:30:00+02:00`). "
    "Alternativ kurze deutsche/englische Formulierungen wie `morgen 15 Uhr` oder `nächsten Freitag 10:00` — "
    "das Backend parst diese gegen Europe/Berlin."
)
_CAL_DATE_ONLY_HINT = (
    "Bevorzugt **ISO 8601 nur Datum**: `YYYY-MM-DD` (z.B. `2026-04-15`). "
    "Alternativ verständliche Datumsangaben (z.B. `15. April 2026`); Auflösung in Europe/Berlin."
)


class GetCalendarEventsArgs(BaseModel):
    days_in_future: Optional[int] = Field(
        7,
        description="Wenn kein start_date gesetzt: Anzahl der Tage ab jetzt (inkl. heute) für die Abfrage.",
    )
    start_date: Optional[str] = Field(
        None,
        description=f"Optionaler Start des Zeitraums. {_CAL_DATE_ONLY_HINT} Kann mit Uhrzeit kombiniert werden.",
    )
    end_date: Optional[str] = Field(
        None,
        description=f"Optionales Ende des Zeitraums (nur sinnvoll mit start_date). {_CAL_DATE_ONLY_HINT}",
    )


class CreateCalendarEventArgs(BaseModel):
    summary: str = Field(..., description="Kurzer Termintitel (wie im Kalender sichtbar).")
    start_time_str: str = Field(
        ...,
        description=f"Start des Termins. {_CAL_DATETIME_HINT} Für ganztägige Termine nur das Datum angeben.",
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Dauer des Termins in Minuten (z.B. 30 für 30 Minuten, 60 für 1 Stunde). WICHTIG: Immer angeben für korrekte Endzeit-Berechnung.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Optional: Ort/Adresse im Format **Straße Hausnummer, PLZ Stadt, Land** wenn bekannt.",
    )
    description: Optional[str] = Field(default=None, description="Optional: Notizen, Links, Agenda.")


class DeleteCalendarEventArgs(BaseModel):
    event_id: str = Field(..., description="Google-Kalender Event-ID (aus list_events / vorherigen Tool-Antworten).")


class UpdateCalendarEventArgs(BaseModel):
    event_id: str = Field(..., description="Google-Kalender Event-ID des zu ändernden Termins.")
    summary: Optional[str] = Field(None, description="Neuer Titel (optional).")
    start_time_str: Optional[str] = Field(
        None,
        description=f"Neue Startzeit (optional). {_CAL_DATETIME_HINT}",
    )
    end_time_str: Optional[str] = Field(
        None,
        description=f"Neue Endzeit (optional). {_CAL_DATETIME_HINT}",
    )
    location: Optional[str] = Field(
        None,
        description="Neuer Ort (optional), Format **Straße, PLZ Stadt, Land** wenn möglich.",
    )
    description: Optional[str] = Field(None, description="Neue oder ersetzte Beschreibung (optional).")


class FindAddressAndUpdateCalendarEventArgs(BaseModel):
    event_title_query: str = Field(
        ...,
        description="Stichworte aus dem Kalendertitel, um den Termin eindeutig zu finden (wie von list_events geliefert).",
    )
    location_query: str = Field(
        ...,
        description=(
            "Websuchbegriff für die Adresse: **POI oder Straße, Stadt, Land** "
            "(z.B. 'Restaurant X Mitte Berlin Deutschland')."
        ),
    )


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
    PHYSIS = "Physis"
    STIL = "Stil"

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

# Legacy memory models (backward compatibility - deprecated)
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


# NEW: Memory Schema V2.1.0 Models
MemoryType = Literal["CORE", "TEMPORAL", "GENERAL"]

class MemoryV2Create(BaseModel):
    """Schema for creating a new memory (V2)."""
    snippet: str
    category: MemoryCategory = MemoryCategory.ALLGEMEIN
    canonical_key: Optional[str] = None
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    memory_type: MemoryType = "GENERAL"
    ttl: Optional[int] = None  # Seconds
    tags: List[str] = Field(default_factory=list)
    source_skill: Optional[str] = None
    user_editable: bool = True
    chat_id: Optional[int] = None
    source_type: str = "text"
    source_metadata: Optional[Dict[str, Any]] = None

class MemoryV2Update(BaseModel):
    """Schema for updating an existing memory (V2)."""
    snippet: Optional[str] = None
    category: Optional[MemoryCategory] = None
    canonical_key: Optional[str] = None
    priority: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    memory_type: Optional[MemoryType] = None
    ttl: Optional[int] = None
    tags: Optional[List[str]] = None
    source_skill: Optional[str] = None
    user_editable: Optional[bool] = None
    expires_at: Optional[datetime] = None

class MemoryV2Response(BaseModel):
    """Schema for memory response (V2)."""
    id: int
    chat_id: Optional[int] = None
    snippet: str
    category: MemoryCategory = MemoryCategory.ALLGEMEIN
    canonical_key: Optional[str] = None
    priority: float = 0.5
    memory_type: MemoryType = "GENERAL"
    ttl: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    source_skill: Optional[str] = None
    user_editable: bool = True
    source_type: str = "text"
    source_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_accessed_at: datetime
    expires_at: Optional[datetime] = None
    retain_until: Optional[datetime] = None
    text_hash: Optional[str] = None
    
    # Legacy fields (backward compatibility)
    is_core_fact: bool = False
    core_priority: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# --- Memory Tool Args Schemas (V2.1 Gold Standard) ---

class MemoryWriteArgs(BaseModel):
    """Arguments for memory_write tool - saves a fact to long-term memory."""
    fact: str = Field(
        ...,
        min_length=1,
        description=(
            "Stabiler Nutzer-Fakt, den das System dauerhaft merken soll (Vorlieben, Name des Hundes, Allergien, Beruf). "
            "NICHT für Text aus PDFs oder Dokumenten — dafür knowledge.query / knowledge.read_full_text. "
            "NICHT für flüchtigen Chat ohne Wiedererkennungswert."
        ),
    )
    subject_name: Optional[str] = Field(None, description="Name des Subjekts (Person, Tier, Objekt).")
    category: MemoryCategory = Field(default=MemoryCategory.ALLGEMEIN, description="Kategorie des Fakts.")
    priority_override: Optional[float] = Field(None, ge=0.0, le=0.95, description="Manuelle Priority (0.0-0.95). Max 0.95.")
    ttl_days: Optional[int] = Field(None, ge=1, le=365, description="TTL in Tagen.")
    tags: Optional[List[str]] = Field(None, description="Zusätzliche Tags.")
    evidence: Optional[str] = Field(None, description="Zitat aus User-Nachricht als Beleg.")


class MemoryReadArgs(BaseModel):
    """Arguments for memory_read tool - searches long-term memory."""
    query: str = Field(
        ...,
        min_length=1,
        description=(
            "Semantische Suche im Langzeitgedächtnis (gespeicherte Fakten über den Nutzer). "
            "NICHT für Inhalte aus hochgeladenen PDFs — dafür knowledge.query."
        ),
    )
    filter_tags: Optional[List[str]] = Field(None, description="Nur Memories mit diesen Tags.")
    min_priority: float = Field(0.0, ge=0.0, le=1.0, description="Minimale Priority (0.0 = alle, 0.8 = nur wichtige).")
    include_expired: bool = Field(False, description="Auch abgelaufene Memories anzeigen (Grace Period)?")
    limit: int = Field(25, ge=1, le=50, description="Maximale Anzahl Ergebnisse (Standard: 25).")


class MemoryUpdateArgs(BaseModel):
    """Arguments for memory_update tool - updates an existing memory."""
    memory_id: int = Field(..., description="ID der zu aktualisierenden Memory (von memory_read).")
    new_fact: str = Field(..., min_length=1, description="Neuer/korrigierter Fakt-Text.")
    new_priority: Optional[float] = Field(None, ge=0.0, le=1.0, description="Neue Priority. Wird ggf. durch Guard gekappt.")


class MemoryHistoryArgs(BaseModel):
    """Arguments for memory_history tool - shows audit trail of a memory."""
    memory_id: int = Field(..., description="ID der Memory (von memory_read).")


# --- Gmail Tool Schemas ---

class GetLatestEmailsArgs(BaseModel):
    max_results: Optional[int] = Field(5, description="Max emails.")
    query: Optional[str] = Field(
        None,
        description=(
            "Gmail-Suchfilter (gleiche Syntax wie in der Gmail-Suche / `q` der Gmail API). "
            "Kombiniere freie Stichwörter mit Operatoren, z. B. `from:news@example.com`, "
            "`subject:Rechnung`, `is:unread`, `after:2026/01/01`, `has:attachment`, `label:important`. "
            "Leer lassen = keine Einschränkung (neueste Mails)."
        ),
    )
    fetch_body: bool = Field(False, description="Fetch body?")


class SendEmailArgs(BaseModel):
    to: str = Field(..., description="Empfänger.")
    subject: str = Field(..., description="Betreff.")
    body: str = Field(..., description="Inhalt.")
    attachment_path: Optional[str] = Field(None, description="Anhang Pfad.")


class FindFreeTimeSlotsArgs(BaseModel):
    year: int = Field(..., description="Vierstelliges Jahr des anzuzeigenden Monats (z.B. 2026).")
    month: int = Field(..., ge=1, le=12, description="Monat 1–12.")
    location_for_weather: Optional[str] = Field(
        None,
        description="Optional: Stadt, Land für Wetterhinweise zu freien Tagen (z.B. 'Berlin, Deutschland').",
    )


class UpdateCalendarEventDescriptionArgs(BaseModel):
    event_title_query: str = Field(
        ...,
        description="Stichworte aus dem Termintitel zur Suche in den geladenen Events.",
    )
    new_description_part: str = Field(
        ...,
        description="Textblock, der an die bestehende Beschreibung angehängt werden soll.",
    )


class SaveCoreMemoryToolArgs(BaseModel):
    fact: str = Field(..., description="Der reine Fakt.")
    category: str = Field(..., description="Kategorie.")


class FindAndUpdateCalendarEventArgs(BaseModel):
    event_title_query: str = Field(
        ...,
        description=(
            "Suchtext für den Termintitel (Fuzzy-Match). "
            "KRITISCH: Dieser Parameter heißt zwingend 'event_title_query' — "
            "NICHT 'query', NICHT 'title', NICHT 'event_name'. "
            "Beispiel: 'event_title_query': 'Aldi'"
        ),
    )
    new_summary: Optional[str] = Field(None, description="Neuer Kalendertitel (optional).")
    new_start_time: Optional[str] = Field(
        None,
        description=f"Neuer Start (optional). {_CAL_DATETIME_HINT}",
    )
    new_end_time: Optional[str] = Field(
        None,
        description=f"Neues Ende (optional). {_CAL_DATETIME_HINT}",
    )
    new_location: Optional[str] = Field(
        None,
        description="Neuer Ort (optional), Format **Straße, PLZ Stadt, Land** wenn möglich.",
    )
    new_description: Optional[str] = Field(None, description="Neue volle oder ergänzte Beschreibung (optional).")
    event_id: Optional[str] = Field(
        None,
        description=(
            "Optional: Google Event-ID wenn bereits durch den Contextual Entity Resolver "
            "(TASK-065) aus dem Kalender-Snapshot aufgelöst — dann ohne Fuzzy-Suche direkt PATCH."
        ),
    )
    cancel_event: Optional[bool] = Field(
        default=False,
        description="Wenn true: Termin löschen statt aktualisieren.",
    )


class ReadEmailArgs(BaseModel):
    email_id: str = Field(description="ID der E-Mail.")


class GetDistanceArgs(BaseModel):
    origin: str = Field(
        ...,
        description=(
            "Startadresse oder -ort: **Stadt, Land** oder **PLZ Stadt, Land** "
            "(z.B. 'München, Deutschland', '10115 Berlin, DE')."
        ),
    )
    destination: str = Field(
        ...,
        description=(
            "Zieladresse oder -ort im gleichen Format wie origin "
            "(z.B. 'Hamburg, Deutschland')."
        ),
    )
    mode: str = Field(
        "driving",
        description="Verkehrsmittel: `driving`, `walking` oder `cycling`.",
    )


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
    apply_preset_to_refine: bool = False
    quality_gate_level: Optional[str] = "none"
    quality_gate_stats: Optional[Dict[str, Any]] = None

class GeneratedImage(GeneratedImageBase):
    id: int
    created_at: datetime
    previous_response_id: Optional[str] = None
    previous_image_id: Optional[str] = None
    quality_gate_stats: Optional[Dict[str, Any]] = None
    style_preset: Optional[str] = None
    variation_preset: Optional[str] = None

    class Config:
        from_attributes = True

class ImageRenameRequest(BaseModel):
    old_path: str = Field(..., description="Pfad alt.")
    new_filename: str = Field(..., description="Dateiname neu.")


# --- Task Schemas with Progress Tracking ---

class TaskProgressUpdate(BaseModel):
    """Schema for updating task progress."""
    progress: int = Field(
        ...,
        ge=0,
        le=100,
        description="Progress percentage (0-100)"
    )
    note: Optional[str] = Field(
        None,
        description="Optional note about this progress update"
    )


class ProgressLogEntry(BaseModel):
    """Single progress log entry."""
    timestamp: datetime
    progress: int
    note: Optional[str] = None


class TaskBase(BaseModel):
    """Base Task schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|failed)$")
    progress: int = Field(default=0, ge=0, le=100)
    chat_id: Optional[int] = None
    project_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|failed)$")
    progress: Optional[int] = Field(None, ge=0, le=100)
    chat_id: Optional[int] = None
    project_id: Optional[int] = None


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: int
    progress_log: List[ProgressLogEntry] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskProgressResponse(BaseModel):
    """Schema for progress update response."""
    task_id: int
    progress: int
    previous_progress: int
    status: str
    note: Optional[str] = None
    updated_at: datetime
    log_entry: ProgressLogEntry


# --- User profile (settings UI) ---
class UserMeResponse(BaseModel):
    """GET /api/users/me — auth probe + ``suggestion_mode`` for the primary DB user."""

    status: str
    user: str
    suggestion_mode: int = Field(default=1, ge=0, le=2)
    # Mirrors persisted chat defaults (same source as GET /api/last-used-model).
    last_used_provider: Optional[str] = None
    last_used_model: Optional[str] = None


class UserSuggestionModeUpdate(BaseModel):
    """PATCH /api/users/me — update proactive suggestion tier."""

    suggestion_mode: int = Field(ge=0, le=2)