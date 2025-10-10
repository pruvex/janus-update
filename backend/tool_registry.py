# backend/tool_registry.py

import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.data import schemas
from backend.services import filesystem_manager
import base64

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

def save_mp3_tool(path: str, content: str):
    """Speichert MP3-Audiodaten als Binärdatei im Workspace. Der Inhalt MUSS ein gültiger Base64-kodierter String der MP3-Daten sein. Wenn reiner Text übergeben wird, wird dieser automatisch in Sprache umgewandelt und gespeichert."""
    
    # Ensure content is bytes for base64.b64decode
    if isinstance(content, str):
        content_bytes = content.encode('utf-8') # Encode to bytes first
    else:
        content_bytes = content # Assume it's already bytes

    try:
        # Try to decode as base64
        decoded_content = base64.b64decode(content_bytes)
        # If successful, proceed with saving
        return filesystem_manager.create_file(path, decoded_content, is_binary=True)
    except (base64.binascii.Error, UnicodeDecodeError) as e:
        # If decoding fails, assume it's raw text and try to synthesize
        logger.warning(f"Content for save_mp3_tool is not valid base64 ({e}). Attempting to synthesize text.")
        
        # Import tts_service here to avoid circular dependency if imported at top
        from backend.services.tts_service import get_tts_service
        tts_service = get_tts_service()

        try:
            # Synthesize the text (content is still the original string here)
            audio_bytes = tts_service.synthesize(text=content, lang="de", fmt="mp3") # Assuming German and MP3
            
            # Save the synthesized audio
            return filesystem_manager.create_file(path, audio_bytes, is_binary=True)
        except Exception as tts_e:
            logger.error(f"Failed to synthesize and save MP3 from raw text: {tts_e}")
            return {
                "output": f"Fehler beim Speichern der MP3-Datei. Der Inhalt war kein gültiger Base64-String und die Sprachsynthese des Textes ist fehlgeschlagen: {tts_e}"
            }


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


# --- Hilfsfunktionen für den Rest der Anwendung ---


def get_all_tool_definitions():
    """Gibt die Definitionen aller registrierten Tools für das LLM zurück."""
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]


def get_all_tools() -> Dict[str, Tool]:
    """Gibt das gesamte Tool-Registry-Wörterbuch zurück."""
    return TOOL_REGISTRY
