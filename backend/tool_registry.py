# backend/tool_registry.py

import os
import base64
import logging
import binascii
import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
from pydub import AudioSegment
from backend.data import schemas
from backend.services import filesystem_manager

# Importiere die Services, die wir innerhalb der Tools benötigen
from backend.services.websearch import perform_websearch
from backend.services.memory_manager import cross_chat_memory_tool
from backend.tools.pdf_generator import create_pdf_from_markdown
from backend.llm_providers.openai_service import OpenAIServiceProvider

logger = logging.getLogger("janus_backend")

# --- Die Tool-Klassen und Registrierungs-Logik (bleibt unverändert) ---
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", **kwargs) -> Dict:
    """Generiert ein Bild basierend auf einer Texteingabe unter Verwendung von DALL-E 3."""
    provider = OpenAIServiceProvider()
    response = await provider.generate_image(api_key, "dall-e-3", prompt, size=size, quality=quality, **kwargs)
    return {"url": response.get("image_url"), "usage": response.get("usage"), "cost": response.get("cost")}

def create_file_tool(path: str, content: str | bytes = "", is_binary: bool = False):
    """Erstellt eine neue Datei im Workspace."""
    return filesystem_manager.create_file(path, content, is_binary)

# --- DIE FINALE, KORREKTE save_mp3_tool FUNKTION ---
def save_mp3_tool(path: str, content: str, llm_provider: str | None = None) -> str:
    """
    Speichert eine MP3-Datei. Der Inhalt kann entweder Base64-kodiert sein oder reiner Text,
    der dann automatisch in Sprache umgewandelt wird. Lange Texte werden automatisch aufgeteilt.
    """
    from backend.services.tts_service import get_tts_service
    from backend.main import load_config, load_personalities

    try:
        # Versuch 1: Base64 dekodieren
        logger.debug("Attempting to decode content as Base64.")
        missing_padding = len(content) % 4
        if missing_padding:
            content += '=' * (4 - missing_padding)
        audio_bytes = base64.b64decode(content, validate=True)
        logger.info("Base64 content successfully decoded.")

        filesystem_manager.create_file(path, content=audio_bytes, is_binary=True)
        success_message = f"Datei '{os.path.basename(path)}' wurde erfolgreich gespeichert."
        logger.info(success_message)
        return f'{{"output": "{success_message}"}}'

    except (binascii.Error, ValueError):
        logger.warning("Content is not valid Base64. Attempting to synthesize text directly.")
        try:
            config = load_config()
            personalities = load_personalities()
            tts_service_instance = get_tts_service(config=config)

            active_personality_id = config.get("active_personality", "ai_assistant")
            active_personality = next((p for p in personalities if p.get("id") == active_personality_id), None)
            
            default_settings = {"voice": "openai_alloy", "speed": 1.0}
            personality_tts_settings = active_personality.get("tts_settings", default_settings) if active_personality else default_settings
            
            final_voice = personality_tts_settings.get("voice")
            final_speed = personality_tts_settings.get("speed")
            
            logger.info(f"save_mp3_tool using personality '{active_personality_id}': voice='{final_voice}', speed={final_speed}")

            # --- CHUNKING LOGIK ---
            max_chunk_size = 3800  # Sicherer Wert unter dem 4096-Limit
            text_chunks = []
            
            if len(content) > max_chunk_size:
                logger.info("Text is too long, splitting into chunks...")
                current_chunk = ""
                # Trenne den Text an Absätzen für natürlichere Pausen
                paragraphs = content.split('\n\n')
                for paragraph in paragraphs:
                    if not paragraph.strip():
                        continue
                    if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                        current_chunk += paragraph + "\n\n"
                    else:
                        if current_chunk:
                            text_chunks.append(current_chunk)
                        # Wenn ein einzelner Absatz zu lang ist, wird er hart geteilt
                        while len(paragraph) > max_chunk_size:
                            split_point = paragraph.rfind('.', 0, max_chunk_size)
                            if split_point == -1: split_point = max_chunk_size
                            text_chunks.append(paragraph[:split_point+1])
                            paragraph = paragraph[split_point+1:]
                        current_chunk = paragraph + "\n\n"
                if current_chunk:
                    text_chunks.append(current_chunk)
            else:
                text_chunks.append(content)

            logger.info(f"Text in {len(text_chunks)} Teile aufgeteilt, um API-Limits einzuhalten.")

            audio_segments = []
            temp_files = []
            for i, chunk in enumerate(text_chunks):
                logger.info(f"Synthesizing chunk {i+1}/{len(text_chunks)}...")
                chunk_audio_bytes = tts_service_instance.synthesize(
                    text=chunk, voice=final_voice, speed=final_speed, provider=llm_provider
                )
                
                temp_path = f"temp_chunk_{i}.mp3"
                with open(temp_path, "wb") as f:
                    f.write(chunk_audio_bytes)
                
                audio_segments.append(AudioSegment.from_mp3(temp_path))
                temp_files.append(temp_path)

            logger.info("Combining audio chunks into final file...")
            combined_audio = sum(audio_segments) if audio_segments else AudioSegment.empty()
            
            combined_audio.export(path, format="mp3")
            
            # Aufräumen der temporären Dateien
            for temp_file in temp_files:
                os.remove(temp_file)

            success_message = f"Hörbuch '{os.path.basename(path)}' wurde erfolgreich erstellt."
            logger.info(success_message)
            return f'{{"output": "{success_message}"}}'

        except Exception as synth_error:
            error_message = f"Fehler bei der MP3-Erstellung: {synth_error}"
            logger.error(error_message, exc_info=True)
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
    return filesystem_manager.move_files(source_directory, destination_directory, pattern)

def list_allowed_workspaces_tool():
    """Listet alle für Dateioperationen freigegebenen Ordner (Workspaces) auf."""
    return filesystem_manager.list_allowed_workspaces()

# --- Registrierung aller Tools ---
register_tool(Tool(func=generate_image_tool, args_schema=schemas.GenerateImageToolArgs))
register_tool(Tool(func=cross_chat_memory_tool, args_schema=schemas.CrossChatMemoryToolArgs))
register_tool(Tool(func=perform_websearch, args_schema=schemas.WebsearchToolArgs))
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
register_tool(Tool(func=list_allowed_workspaces_tool, args_schema=schemas.ListAllowedWorkspacesArgs))
register_tool(Tool(func=create_pdf_from_markdown, args_schema=schemas.CreatePdfFromMarkdownArgs))

def get_all_tool_definitions():
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]

def get_all_tools() -> Dict[str, Tool]:
    return TOOL_REGISTRY
