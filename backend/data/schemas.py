from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)  # Stellen Sie sicher, dass ConfigDict importiert wird


# --- Tool Schemas ---
class GenerateImageToolArgs(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = Field(
        "standard",
        description="Die Qualität des generierten Bildes. Unterstützte Werte sind 'standard' und 'hd'.",
        pattern="^(standard|hd)$" # <-- NEU: Regex, um nur 'standard' oder 'hd' zu erlauben
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
    project_id: Optional[int] = None  # NEU


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
    # Wir geben hier erstmal nur eine Liste der Dateinamen oder IDs zurück, um Traffic zu sparen
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
    project_id: Optional[int] = None  # NEU

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
        description="Der zu vertonende Text. Dies sollte der vollständige Text (inklusive SSML-Tags wie <speak>) aus der vorherigen Assistenten-Antwort sein.",
    )
    filename: str = Field(..., description="Der Zieldateiname für die MP3, z.B. 'geschichte.mp3'.")
    voice: Optional[str] = Field(
        "fable",
        description="Nur relevant für SSML/OpenAI. Stimme zur Vertonung. Verfügbar: 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'. Standard ist 'fable'.",
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
    """
    Argumente für die Suche nach lokalen Geschäften und Dienstleistungen.
    """

    query: str = Field(..., description="Was gesucht wird, z.B. 'Pizzeria', 'Kino', 'Supermarkt'.")
    location: Optional[str] = Field(
        None,
        description="Der Ort, in dem gesucht werden soll, z.B. 'Köln', 'Berlin'. Wenn nicht angegeben, wird 'in meiner Nähe' angenommen.",
    )


class WebsearchToolArgs(BaseModel):
    """
    Führt eine allgemeine Websuche für Informationen, Produkte, Personen oder beliebige andere nicht-lokale Anfragen durch.
    NICHT VERWENDEN für lokale Geschäfte, Restaurants oder Dienstleistungen - dafür find_local_business_tool verwenden.
    """

    query: str = Field(..., description="Die Suchanfrage.")


class ReadUrlContentArgs(BaseModel):
    """Liest den reinen Textinhalt einer Webseite, nachdem HTML-Boilerplate entfernt wurde."""
    url: str = Field(..., description="Die vollständige URL der zu lesenden Webseite (muss mit http:// oder https:// beginnen).")


# --- PDF Tool Schema (ERWEITERT) ---
class CreatePdfFromMarkdownArgs(BaseModel):
    content: str = Field(..., description="Der Inhalt der PDF-Datei im Markdown-Format.")
    filename: str = Field(..., description="Der gewünschte Dateiname (z.B. 'zusammenfassung.pdf').")
    location: str = Field(
        "Documents",
        description="Der Speicherort. Mögliche Werte: 'Desktop', 'Documents', 'Downloads'. Standard ist 'Documents'.",
    )
    include_image: bool = Field(
        False,
        description="Setze dies auf 'true', wenn das letzte Bild aus dem Chatverlauf in die PDF eingefügt werden soll.",
    )
    # NEUE PARAMETER
    font_size: int = Field(
        default=11,
        description="Die Schriftgröße für den Haupttext in der PDF. Der Standardwert ist 11. Überschriften sind relativ größer.",
    )
    image_width: int = Field(
        default=0,
        description="Die gewünschte Breite des Bildes in Millimetern. Bei 0 wird die Breite automatisch an die Seite angepasst (ca. 190mm). Gib z.B. 100 an für ein 10cm breites Bild.",
    )


from typing import Optional


class GetWeatherFromApiToolArgs(BaseModel):
    city: str = Field(
        ...,
        description="Die Stadt, für die die Wettervorhersage abgerufen werden soll, z.B. 'Berlin' oder 'Köln'.",
    )
    date_str: Optional[str] = Field(
        None,
        description="Optional: Ein Datum in natürlicher Sprache (z.B. 'Samstag', 'übermorgen', '15. November'), um eine Vorhersage für einen bestimmten Tag zu erhalten. Wenn kein Datum angegeben wird, wird die Vorhersage für den nächsten verfügbaren Tag zurückgegeben.",
    )


class GetCountryInfoToolArgs(BaseModel):
    country_name: str = Field(
        ...,
        description="Der offizielle englische Name des Landes, z.B. 'Germany', 'Peru', 'Japan'.",
    )
    info_type: str = Field(
        ...,
        description="Die Art der Information, die angefragt wird. Mögliche Werte: 'capital' (Hauptstadt), 'population' (Einwohnerzahl), 'currency' (Währung), 'languages' (Sprachen), 'region' (Kontinent/Region).",
    )


class GetLatestNewsRssToolArgs(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Das Thema, nach dem über alle Nachrichtenquellen hinweg gesucht werden soll. Verfeinere diese Suchanfrage IMMER mit relevanten persönlichen Vorlieben (z.B. spezifische Genres, Konsolen, Themen), die im Kontext oder der Faktenlage verfügbar sind.",
    )
    source: Optional[str] = Field(
        None,
        description="Die spezifische Quelle für Top-Schlagzeilen. Verfügbare Quellen sind: 'tagesschau', 'spiegel', 'zeit', 'heise', 'reuters', 'bbc'.",
    )


class GetWikipediaSummaryArgs(BaseModel):
    query: str = Field(
        ...,
        description="Das Thema, der Name oder das Konzept, nach dem in Wikipedia gesucht werden soll.",
    )
    lang: str = Field(
        "de",
        description="Der Sprachcode für die Wikipedia-Version (z.B. 'de' für Deutsch, 'en' für Englisch). Standard ist 'de'.",
    )


class GetCalendarEventsArgs(BaseModel):
    days_in_future: Optional[int] = Field(
        7,
        description="Die Anzahl der Tage, die in die Zukunft geschaut werden soll. Wird ignoriert, wenn start_date gesetzt ist.",
    )
    start_date: Optional[str] = Field(
        None,
        description="Das Startdatum für die Suche im Format YYYY-MM-DD. Wenn angegeben, wird days_in_future ignoriert.",
    )
    end_date: Optional[str] = Field(
        None,
        description="Das Enddatum für die Suche im Format YYYY-MM-DD. Wenn nicht angegeben, wird nur der start_date durchsucht.",
    )


class CreateCalendarEventArgs(BaseModel):
    summary: str = Field(..., description="Der Titel oder die Zusammenfassung des Termins.")
    start_time_str: str = Field(
        ...,
        description=(
            "Die Startzeit des Termins, IMMER als absolutes Datum und Uhrzeit im ISO-8601-Format (YYYY-MM-DDTHH:MM:SS). "
            "Du MUSST relative Angaben wie 'morgen' oder 'nächste Woche' basierend auf dem heutigen Datum (im Systemprompt) "
            "selbstständig in dieses Format umrechnen, BEVOR du das Werkzeug aufrufst."
        ),
    )
    location: Optional[str] = Field(default=None, description="Optionaler Ort des Termins.")
    description: Optional[str] = Field(
        default=None,
        description="Optionale Details oder eine Beschreibung für den Termin, z.B. 'ich lerne heute klavier'.",
    )


class DeleteCalendarEventArgs(BaseModel):
    """Argumente für das Werkzeug delete_calendar_event."""

    event_id: str = Field(
        ...,
        description="Die eindeutige ID des zu löschenden Termins, die zuvor mit get_calendar_events abgerufen wurde.",
    )


class UpdateCalendarEventArgs(BaseModel):
    """Argumente für das Werkzeug update_calendar_event."""

    event_id: str = Field(..., description="Die eindeutige ID des zu ändernden Termins.")
    summary: Optional[str] = Field(None, description="Der neue Titel des Termins.")
    start_time_str: Optional[str] = Field(
        None, description="Die neue Startzeit des Termins als Text."
    )
    end_time_str: Optional[str] = Field(None, description="Die neue Endzeit des Termins als Text.")
    location: Optional[str] = Field(None, description="Der neue Ort des Termins.")
    description: Optional[str] = Field(
        None, description="Die neue, vollständige Beschreibung des Termins."
    )


class FindAddressAndUpdateCalendarEventArgs(BaseModel):
    """Argumente für das Werkzeug find_address_and_update_calendar_event."""

    event_title_query: str = Field(
        ...,
        description="Ein oder zwei Schlüsselwörter aus dem Titel des zu aktualisierenden Kalendereintrags, z.B. 'Magenspülung' oder 'Zahnarzt'.",
    )
    location_query: str = Field(
        ...,
        description="Die Suchanfrage, um die Adresse zu finden, z.B. 'Praxis Dr. Freudenhammer Merheim' oder 'Zahnarzt Müller Köln'.",
    )


# --- START OF CODE ---
# Schemas für die Gedächtnis-Verwaltung im Frontend
class MemoryUpdate(BaseModel):
    snippet: str
    category: str


class MemoryResponse(BaseModel):
    id: int
    snippet: str
    category: str
    created_at: datetime
    last_accessed_at: datetime

    class Config:
        orm_mode = True


# --- Gmail Tool Schemas ---


class GetLatestEmailsArgs(BaseModel):
    """Arguments for the get_latest_emails tool."""

    max_results: Optional[int] = Field(
        5, description="The maximum number of emails to retrieve (default is 5)."
    )
    query: Optional[str] = Field(
        None,
        description="A Gmail search query to filter emails. "
        "Examples: 'from:sender@example.com', 'is:unread', 'subject:project update'",
    )
    # --- START GOLDSTANDARD-FIX ---
    fetch_body: bool = Field(
        False,
        description="Set to true ONLY if the user's request requires the full content of the email, e.g., for 'summarize', 'translate', or 'extract information from'.",
    )
    # --- ENDE GOLDSTANDARD-FIX ---


class SendEmailArgs(BaseModel):
    """Arguments for the send_email tool."""

    to: str = Field(
        ...,
        description="Die E-Mail-Adresse des Empfängers. Mehrere Empfänger können mit Komma getrennt werden.",
    )
    subject: str = Field(..., description="Die Betreffzeile der E-Mail.")
    body: str = Field(..., description="Der Textinhalt der E-Mail.")
    attachment_path: Optional[str] = Field(
        None,
        description="Optional: Der vollständige, absolute Dateipfad zu einer Datei, die als Anhang gesendet werden soll.",
    )


class FindFreeTimeSlotsArgs(BaseModel):
    """Arguments for the find_free_time_slots tool."""

    year: int = Field(..., description="Das Jahr, in dem gesucht werden soll, z.B. 2025.")
    month: int = Field(
        ..., description="Der Monat, in dem gesucht werden soll (als Zahl, z.B. 11 für November)."
    )
    location_for_weather: Optional[str] = Field(
        None,
        description="Optional: Der Ort (Stadt), für den das Wetter geprüft werden soll, um trockene Tage zu markieren.",
    )


class UpdateCalendarEventDescriptionArgs(BaseModel):
    """Argumente für das Werkzeug update_calendar_event_description."""

    event_title_query: str = Field(
        ...,
        description="Ein oder zwei Schlüsselwörter aus dem Titel des zu aktualisierenden Kalendereintrags, z.B. 'Chinesisch Essen' oder 'Klavierunterricht'.",
    )
    new_description_part: str = Field(
        ...,
        description="Der Text, der zur bestehenden Beschreibung des Termins hinzugefügt werden soll, z.B. 'Begleitung: Kalle'.",
    )


class SaveCoreMemoryToolArgs(BaseModel):
    """Arguments for the save_core_memory_tool function."""

    fact: str = Field(
        ..., description="Der reine Fakt oder die Information, die gespeichert werden soll."
    )
    category: str = Field(
        ...,
        description="Eine passende Kategorie für den Fakt, z.B. 'Preference', 'Personal', 'Goal'.",
    )


# --- START OF CODE ---


class FindAndUpdateCalendarEventArgs(BaseModel):
    event_title_query: str = Field(
        ...,
        description="Ein oder zwei Schlüsselwörter aus dem Titel des zu findenden und zu aktualisierenden Termins.",
    )
    new_summary: Optional[str] = Field(None, description="Der neue Titel des Termins.")
    new_start_time: Optional[str] = Field(
        None, description="Die neue Startzeit des Termins als Text."
    )
    new_end_time: Optional[str] = Field(None, description="Die neue Endzeit des Termins als Text.")
    new_location: Optional[str] = Field(None, description="Der neue Ort des Termins.")
    new_description: Optional[str] = Field(None, description="Die neue Beschreibung des Termins.")
    cancel_event: Optional[bool] = Field(
        default=False,
        description="Setze dies auf 'true', um den gefundenen Termin zu stornieren, anstatt ihn zu aktualisieren.",
    )


class ReadEmailArgs(BaseModel):
    email_id: str = Field(description="Die eindeutige ID der zu lesenden E-Mail.")


class GetDistanceArgs(BaseModel):
    origin: str = Field(..., description="Der Startort, z.B. 'München'.")
    destination: str = Field(..., description="Der Zielort, z.B. 'Hamburg'.")
    mode: str = Field(
        "driving",
        description="Die Reiseart: 'driving' (Auto), 'walking' (Zu Fuß), 'cycling' (Fahrrad). Standard ist 'driving'.",
    )


class SetLastUsedModelRequest(BaseModel):
    provider: str
    model: str


class FindContactAndSendEmailArgs(BaseModel):
    name_query: str = Field(
        ..., description="Der Name des Kontakts, an den die E-Mail gesendet werden soll."
    )
    subject: str = Field(..., description="Der Betreff der E-Mail.")
    body: str = Field(..., description="Der Inhalt der E-Mail.")

# --- Image Studio Schemas ---

class GeminiHistory(BaseModel):
    """Stores the previous prompt and image for Gemini refinement."""
    prompt: str
    image_base64: str

class ImageParameters(BaseModel):
    # Erlaubt beliebige Schlüssel-Wert-Paare, um flexibel zu sein
    # z.B. {"quality": "hd", "resolution": "1024x1024", "style": "vivid"}
    model_config = ConfigDict(extra='allow')


class GeneratedImageBase(BaseModel):
    prompt: Optional[str] = None
    style_preset: Optional[str] = None
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
    quality_gate_level: Optional[str] = "none"
    quality_gate_stats: Optional[Dict[str, Any]] = None

class GeneratedImage(GeneratedImageBase):
    id: int
    created_at: datetime
    previous_response_id: Optional[str] = None
    previous_image_id: Optional[str] = None
    quality_gate_stats: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Image Rename Schema ---
class ImageRenameRequest(BaseModel):
    old_path: str = Field(..., description="Der relative Pfad des umzubenennenden Bildes (z.B. 'user_images/old_name.png').")
    new_filename: str = Field(..., description="Der neue vollständige Dateiname des Bildes (z.B. 'new_name.png').")
