# backend/tool_registry.py

import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.data import schemas
from backend.services import filesystem_manager
import base64
import logging
import binascii

logger = logging.getLogger("janus_backend")

# --- Werkzeug-Klassen und Registrierungs-Logik ---


class Tool:
    def __init__(self, func: Callable, args_schema: Optional[BaseModel] = None):
        self.func = func
        self.args_schema = args_schema
        self.name = func.__name__
        self.description = inspect.getdoc(func)
        self.llm_definition = self._build_llm_definition()

    def _build_llm_definition(self) -> Dict[str, Any]:
        schema = (
            self.args_schema.model_json_schema()
            if self.args_schema
            else {"properties": {}, "required": []}
        )
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }


TOOL_REGISTRY: Dict[str, Tool] = {}


def register_tool(tool: Tool):
    TOOL_REGISTRY[tool.name] = tool


# --- Werkzeug-Funktionen ---

from backend.llm_providers.openai_service import OpenAIServiceProvider


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_image_tool(
    api_key: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    **kwargs,
) -> Dict:
    """Generiert ein Bild basierend auf einer Texteingabe unter Verwendung von DALL-E 3."""
    provider = OpenAIServiceProvider()
    response = await provider.generate_image(
        api_key, "dall-e-3", prompt, size=size, quality=quality, **kwargs
    )
    return {
        "url": response.get("image_url"),
        "usage": response.get("usage"),
        "cost": response.get("cost"),
    }


from backend.services.websearch import perform_websearch
from backend.services.memory_manager import cross_chat_memory_tool
from backend.tools.pdf_generator import create_pdf_from_markdown


# Filesystem Tools
def create_file_tool(path: str, content: str | bytes = "", is_binary: bool = False):
    """Erstellt eine neue Datei im Workspace."""
    return filesystem_manager.create_file(path, content, is_binary)

def save_mp3_tool(path: str, content: str, llm_provider: str | None = None, voice_id: str | None = None) -> str:
    """
    Speichert eine MP3-Datei. Der Inhalt kann entweder Base64-kodiert sein oder reiner Text,
    der dann automatisch in Sprache umgewandelt wird.
    """
    from backend.services.tts_service import get_tts_service
    from backend.main import load_config

    config = load_config()

    try:
        # Versuch 1: Angenommen, der Inhalt ist gültiger Base64-Code
        logger.debug("Attempting to decode content as Base64.")
        # Python's b64decode ist streng und benötigt korrekte "padding" Zeichen (=)
        # Wir fügen sie hinzu, falls die KI sie vergessen hat.
        missing_padding = len(content) % 4
        if missing_padding:
            content += '=' * (4 - missing_padding)
        
        audio_bytes = base64.b64decode(content, validate=True)
        logger.info("Base64 content successfully decoded.")

    except (binascii.Error, ValueError) as e:
        # Versuch 2: Fallback, wenn der Inhalt kein Base64, sondern reiner Text ist.
        logger.warning(f"Content is not valid Base64 ({e}). Attempting to synthesize text directly.")
        
        try:
            # NEU & KORREKT: Rufen Sie den TTS-Service auf, um aus dem Text Audio zu erzeugen.
            # Der `content` ist hier der zu sprechende Text.
            tts_service_instance = get_tts_service(config=config)
            audio_bytes = tts_service_instance.synthesize(
                text=content,
                voice=voice_id,  # Verwendet die vom Benutzer ausgewählte Stimme
                provider=llm_provider, # Stellt sicher, dass der richtige Provider genutzt wird
            )
            if not audio_bytes:
                raise ValueError("TTS synthesis returned empty audio data.")
            logger.info("Successfully synthesized text to audio.")

        except Exception as synth_error:
            # Wenn auch die Synthese fehlschlägt, geben wir einen klaren Fehler zurück.
            error_message = f"Failed to process content for MP3 saving. It was not valid Base64, and TTS synthesis also failed: {synth_error}"
            logger.error(error_message)
            return f'{{"error": "{error_message}"}}'

    # Egal ob aus Base64 dekodiert oder neu synthetisiert, hier speichern wir die Binärdaten.
    try:
        filesystem_manager.create_file(path, content=audio_bytes, is_binary=True)
        success_message = f"Datei '{path}' wurde erfolgreich erstellt."
        logger.info(success_message)
        return f'{{"output": "{success_message}"}}'
    except Exception as file_error:
        error_message = f"Failed to write MP3 file to '{path}': {file_error}"
        logger.error(error_message)
        return f'{{"error": "{error_message}"}}'


def read_file_tool(path: str):
    """Liest den Inhalt einer Datei aus dem Workspace."""
    return filesystem_manager.read_file(path)


def delete_file_tool(path: str):
    """Löscht eine Datei aus dem Workspace."""
    return filesystem_manager.delete_file(path)


def list_directory_tool(path: str = ".", pattern: Optional[str] = None):
    """Listet den Inhalt eines Ordners auf. Kann mit einem Wildcard-Muster wie '*.png' oder 'test*' filtern."""
    return filesystem_manager.list_directory(path, pattern)


def create_directory_tool(path: str):
    """Erstellt einen neuen, leeren Ordner im Workspace."""
    return filesystem_manager.create_directory(path)


def delete_directory_tool(path: str):
    """Löscht einen Ordner und dessen gesamten Inhalt aus dem Workspace."""
    return filesystem_manager.delete_directory(path)


def rename_file_tool(old_path: str, new_path: str):
    """Benennt eine Datei oder einen Ordner um."""
    return filesystem_manager.rename_file(old_path, new_path)


def move_file_tool(source_path: str, destination_path: str):
    """Verschiebt eine einzelne Datei oder einen Ordner."""
    return filesystem_manager.move_file(source_path, destination_path)


def move_files_tool(source_directory: str, destination_directory: str, pattern: str):
    """Verschiebt mehrere Dateien, die einem Muster (z.B. '*.png') entsprechen, von einem Ordner in einen anderen."""
    return filesystem_manager.move_files(
        source_directory, destination_directory, pattern
    )


def list_allowed_workspaces_tool():
    """Listet alle für Dateioperationen freigegebenen Ordner (Workspaces) auf."""
    return filesystem_manager.list_allowed_workspaces()


# --- Hilfsfunktionen für den Rest der Anwendung ---


def get_all_tool_definitions():
    """Gibt die Definitionen aller registrierten Tools für das LLM zurück."""
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]


def get_all_tools() -> Dict[str, Tool]:
    """Gibt das gesamte Tool-Registry-Wörterbuch zurück."""
    return TOOL_REGISTRY


# --- Registrierung aller Tools ---

register_tool(Tool(func=generate_image_tool, args_schema=schemas.GenerateImageToolArgs))
register_tool(
    Tool(func=cross_chat_memory_tool, args_schema=schemas.CrossChatMemoryToolArgs)
)
register_tool(Tool(func=perform_websearch, args_schema=schemas.WebsearchToolArgs))

# Filesystem
register_tool(Tool(func=create_file_tool, args_schema=schemas.CreateFileArgs))
register_tool(Tool(func=save_mp3_tool, args_schema=schemas.SaveMp3Args))
register_tool(Tool(func=read_file_tool, args_schema=schemas.ReadFileArgs))
register_tool(Tool(func=delete_file_tool, args_schema=schemas.DeleteFileArgs))
register_tool(Tool(func=list_directory_tool, args_schema=schemas.ListDirectoryArgs))
register_tool(Tool(func=create_directory_tool, args_schema=schemas.CreateDirectoryArgs))
register_tool(Tool(func=delete_directory_tool, args_schema=schemas.DeleteDirectoryArgs))
register_tool(Tool(func=rename_file_tool, args_schema=schemas.RenameFileArgs))
register_tool(Tool(func=move_file_tool, args_schema=schemas.MoveFileArgs))
register_tool(Tool(func=move_files_tool, args_schema=schemas.MoveFilesArgs))
register_tool(
    Tool(
        func=list_allowed_workspaces_tool, args_schema=schemas.ListAllowedWorkspacesArgs
    )
)

# Unser neues PDF Werkzeug, jetzt korrekt registriert
register_tool(
    Tool(func=create_pdf_from_markdown, args_schema=schemas.CreatePdfFromMarkdownArgs)
)
