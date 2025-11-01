# backend/tool_registry.py

# Benötigte Imports ganz oben in der Datei
import os
import base64
import logging
import binascii
import inspect
import io
import re
from typing import Callable, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
from pydub import AudioSegment
from openai import AsyncOpenAI

# Importiere die Services und Schemas, die wir benötigen
from backend.data import schemas
from backend.services import filesystem_manager
from backend.services.websearch import perform_websearch
from backend.services.memory_manager import cross_chat_memory_tool
from backend.tools.pdf_generator import create_pdf_from_markdown
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.services.tts_service import TTSService 
from backend.utils.paths import get_desktop_path


logger = logging.getLogger("janus_backend")
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# --- Tool-Klasse und Registrierungs-Logik ---

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

def split_text_into_chunks(text: str, max_length: int = 4000):
    """
    Teilt einen SSML-Text intelligent in Chunks unterhalb der max_length auf,
    ohne SSML-Tags zu zerschneiden. Behandelt Sätze und Tags als unteilbare Einheiten.
    """
    logger.info("Starting intelligent SSML chunking...")
    
    # Entferne den umschließenden <speak>-Tag für die Verarbeitung
    inner_ssml = re.sub(r'</?speak>', '', text, flags=re.IGNORECASE).strip()
    
    # Zerlege den Text in eine Liste von Sätzen (inkl. Satzzeichen) UND kompletten SSML-Tags.
    # Dies ist der Kern der Logik: Jedes Element ist entweder ein Satz oder ein Tag.
    parts = re.findall(r'(<[^>]+>|[^.!?]+(?:[.!?]|$))', inner_ssml)
    
    chunks = []
    current_chunk = ""
    
    for part in parts:
        part_stripped = part.strip()
        if not part_stripped:
            continue
            
        # Wenn das Hinzufügen des nächsten Teils die Maximallänge überschreiten würde,
        # schließe den aktuellen Chunk ab und beginne einen neuen.
        if len(current_chunk) + len(part_stripped) + 1 > max_length:
            if current_chunk:
                chunks.append(f"<speak>{current_chunk.strip()}</speak>")
            current_chunk = part_stripped
        else:
            current_chunk += " " + part_stripped
    
    # Füge den letzten verbleibenden Chunk hinzu, falls vorhanden.
    if current_chunk:
        chunks.append(f"<speak>{current_chunk.strip()}</speak>")
    
    logger.info(f"SSML text successfully split into {len(chunks)} chunks.")
    return chunks

async def save_mp3_tool(content: str, filename: str, voice: str = "fable") -> Dict[str, str]:
    """
    Speichert Text als MP3. Erkennt SSML und nutzt dann die OpenAI API für hohe Qualität.
    Fällt für reinen Text auf die lokale TTS-Engine zurück. Lange SSML-Texte werden aufgeteilt.
    """
    if not filename.lower().endswith('.mp3'):
        filename += '.mp3'
    filename = os.path.basename(filename)
    desktop_path = get_desktop_path()
    if not desktop_path:
        return {"status": "error", "message": "Desktop-Pfad nicht gefunden."}
    
    speech_file_path = os.path.join(desktop_path, filename)

    is_ssml = content.strip().startswith("<speak>") and content.strip().endswith("</speak>")

    if is_ssml:
        logger.info(f"SSML-Text erkannt. Nutze OpenAI TTS mit Stimme '{voice}' für hohe Qualität.")
        try:
            # Chunking logic for long SSML texts
            ssml_chunks = split_text_into_chunks(content)
            audio_segments = []

            for i, chunk in enumerate(ssml_chunks):
                logger.info(f"Synthesizing chunk {i+1}/{len(ssml_chunks)}...")
                response = await client.audio.speech.create(
                    model="tts-1-hd",
                    voice=voice,
                    input=chunk
                )
                
                # Load audio data into a pydub AudioSegment
                audio_data = io.BytesIO(response.content)
                segment = AudioSegment.from_file(audio_data, format="mp3")
                audio_segments.append(segment)

            logger.info("Füge alle Audio-Teile zusammen...")
            final_audio = sum(audio_segments, AudioSegment.empty())
            
            # Export the final combined audio
            final_audio.export(speech_file_path, format="mp3")

            success_msg = f"Audiodatei erfolgreich mit Stimme '{voice}' unter '{speech_file_path}' gespeichert."
            logger.info(success_msg)
            return {"status": "success", "message": success_msg}
        except Exception as e:
            error_msg = f"Fehler bei der OpenAI TTS-Synthese: {e}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}
    else:
        logger.info("Reiner Text erkannt. Nutze lokale TTS-Engine (Piper).")
        try:
            from backend.main import load_config
            config = load_config()
            tts_service_instance = TTSService(config=config, tts_settings=config.get("tts_settings", {}))
            audio_bytes = tts_service_instance.synthesize(
                text=content,
                voice='piper_de_DE-thorsten-medium',
                speed=1.0
            )
            
            if audio_bytes:
                with open(speech_file_path, "wb") as f:
                    f.write(audio_bytes)
                success_msg = f"Audiodatei erfolgreich mit lokaler Stimme unter '{speech_file_path}' gespeichert."
                logger.info(success_msg)
                return {"status": "success", "message": success_msg}
            else:
                raise RuntimeError("Lokale TTS hat keine Audiodaten zurückgegeben.")

        except Exception as e:
            error_msg = f"Fehler bei der lokalen TTS-Synthese: {e}"
            logger.error(error_msg, exc_info=True)
            return {"status": "error", "message": error_msg}

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


def create_file_tool(path: str, content: str | bytes = "", is_binary: bool = False):
    """Erstellt eine neue Datei im Workspace."""
    return filesystem_manager.create_file(path, content, is_binary)


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


# --- Hilfsfunktionen für den Rest der Anwendung ---


def get_all_tool_definitions():
    """Gibt die Definitionen aller registrierten Tools für das LLM zurück."""
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]


def get_all_tools() -> Dict[str, Tool]:
    """Gibt das gesamte Tool-Registry-Wörterbuch zurück."""
    return TOOL_REGISTRY