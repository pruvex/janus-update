# Vollständige, finale Version: backend/tool_registry.py

import inspect
import openai
import logging
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from backend import schemas, filesystem_manager

from backend.llm_providers.openai_service import OpenAIServiceProvider

# This function is a standalone wrapper for tool registration.
# It instantiates the provider and calls the appropriate method.
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", **kwargs) -> Dict:
    """
    Generiert ein Bild basierend auf einer Texteingabe unter Verwendung von DALL-E 3.
    """
    provider = OpenAIServiceProvider()
    response = await provider.generate_image(api_key, "dall-e-3", prompt, size=size, quality=quality, **kwargs)
    return {
        "url": response.get("image_url"),
        "usage": response.get("usage"),
        "cost": response.get("cost")
    }

from backend.websearch import perform_websearch
from backend.memory_manager import cross_chat_memory_tool
from sqlalchemy.orm import Session
from backend import crud

logger = logging.getLogger('janus_backend')

class Tool:
    def __init__(self, func: Callable, args_schema: BaseModel):
        self.func = func
        self.args_schema = args_schema
        self.name = func.__name__
        self.description = inspect.getdoc(func)
        self.llm_definition = self._build_llm_definition()

    def _build_llm_definition(self) -> Dict[str, Any]:
        schema = self.args_schema.model_json_schema()
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

# --- Original Tools ---




# --- Filesystem Tools ---
def create_file_tool(path: str, content: str = ""):
    """Erstellt eine neue Datei im Workspace."""
    return filesystem_manager.create_file(path, content)

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
    """Verschiebt mehrere Dateien, die einem Muster (z.B. '*.png') entsprechen, von einem Ordner in einen anderen. Ideal für Massenoperationen."""
    return filesystem_manager.move_files(source_directory, destination_directory, pattern)

def list_allowed_workspaces_tool():
    """Listet alle für Dateioperationen freigegebenen Ordner (Workspaces) auf."""
    return filesystem_manager.list_allowed_workspaces()

# --- Registrierung aller Tools ---
register_tool(Tool(func=generate_image_tool, args_schema=schemas.GenerateImageToolArgs))
register_tool(Tool(func=cross_chat_memory_tool, args_schema=schemas.CrossChatMemoryToolArgs))
register_tool(Tool(func=create_file_tool, args_schema=schemas.CreateFileArgs))
register_tool(Tool(func=read_file_tool, args_schema=schemas.ReadFileArgs))
register_tool(Tool(func=delete_file_tool, args_schema=schemas.DeleteFileArgs))
register_tool(Tool(func=list_directory_tool, args_schema=schemas.ListDirectoryArgs))
register_tool(Tool(func=create_directory_tool, args_schema=schemas.CreateDirectoryArgs))
register_tool(Tool(func=delete_directory_tool, args_schema=schemas.DeleteDirectoryArgs))
register_tool(Tool(func=rename_file_tool, args_schema=schemas.RenameFileArgs))
register_tool(Tool(func=move_file_tool, args_schema=schemas.MoveFileArgs))
register_tool(Tool(func=move_files_tool, args_schema=schemas.MoveFilesArgs)) # NEU
register_tool(Tool(func=list_allowed_workspaces_tool, args_schema=schemas.ListAllowedWorkspacesArgs))
register_tool(Tool(func=perform_websearch, args_schema=schemas.WebsearchToolArgs))

def get_all_tool_definitions():
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]

def get_all_tools() -> Dict[str, Tool]:
    """Gibt das gesamte Tool-Registry-Wörterbuch zurück."""
    return TOOL_REGISTRY