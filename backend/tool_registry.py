# backend/tool_registry.py
import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel
from backend import llm_gateway, schemas
from sqlalchemy.orm import Session
from backend import crud, vector_service
from backend.database import get_db
from fastapi import Depends
from backend import filesystem_manager

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

async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    """
    Generates an image based on a text prompt using DALL-E 3.
    Use this tool whenever a user asks to create, draw, or generate an image.
    """
    return await llm_gateway.generate_image_tool(
        api_key=api_key, prompt=prompt, size=size, quality=quality, response_format=response_format
    )

def cross_chat_memory_tool(query: str, db: Session): # Der Query wird ignoriert, aber vom LLM erwartet
    """
    Retrieves summaries of the last few conversations to answer questions about the past.
    Use this tool whenever the user asks about topics discussed in previous, separate chats.
    This is your primary method for accessing long-term, cross-chat memory.
    """
    # Wir holen einfach die letzten 5 Chats (ohne den aktuellen)
    all_chats = crud.get_chats(db, include_archived=True)
    
    # Ignoriere den allerletzten Chat, da er der aktuelle ist.
    # Sortiere nach Erstellungsdatum, um die neuesten zuerst zu bekommen.
    recent_chats = sorted(all_chats, key=lambda chat: chat.created_at, reverse=True)[1:6]
    
    if not recent_chats:
        return {"output": "Keine früheren Chats zum Überprüfen gefunden."}
        
    # Formatiere die Ergebnisse für die LLM-Antwort
    output_snippets = ["--- ZUSAMMENFASSUNGEN DER LETZTEN CHATS ---"]
    for chat in recent_chats:
        if chat.summary: # Nur Chats mit einer Zusammenfassung anzeigen
            output_snippets.append(f"Thema des Chats '{chat.title}': {chat.summary}")
            
    if len(output_snippets) == 1: # Wenn kein Chat eine Zusammenfassung hatte
        return {"output": "Keine relevanten Zusammenfassungen in früheren Chats gefunden."}
        
    return {"output": "\n".join(output_snippets)}

register_tool(Tool(func=generate_image_tool, args_schema=schemas.GenerateImageToolArgs))
register_tool(Tool(func=cross_chat_memory_tool, args_schema=schemas.CrossChatMemoryToolArgs))

# --- Filesystem Tools ---

def create_file_tool(path: str, content: str = ""):
    """Erstellt eine neue Datei in einem erlaubten Workspace. Pfade können absolut sein (z.B. 'D:\\Projekte\\neu.txt') oder relativ zu einem Workspace (z.B. 'neu.txt')."""
    return filesystem_manager.create_file(path, content)

def read_file_tool(path: str):
    """Liest den Inhalt einer Datei aus einem erlaubten Workspace."""
    return filesystem_manager.read_file(path)

def delete_file_tool(path: str):
    """Löscht eine Datei aus einem erlaubten Workspace. Diese Aktion kann nicht rückgängig gemacht werden."""
    return filesystem_manager.delete_file(path)

def list_directory_tool(path: str = "."):
    """Listet den Inhalt eines Ordners auf. Verwende '.' oder '' für eine Übersicht der erlaubten Workspaces."""
    return filesystem_manager.list_directory(path)

def create_directory_tool(path: str):
    """Erstellt einen neuen, leeren Ordner in einem erlaubten Workspace."""
    return filesystem_manager.create_directory(path)

def delete_directory_tool(path: str):
    """Löscht einen Ordner und dessen gesamten Inhalt. Sei vorsichtig, diese Aktion kann nicht rückgängig gemacht werden."""
    return filesystem_manager.delete_directory(path)

def rename_file_tool(old_path: str, new_path: str):
    """Benennt eine Datei oder einen Ordner innerhalb der erlaubten Workspaces um."""
    return filesystem_manager.rename_file(old_path, new_path)

def move_file_tool(source_path: str, destination_path: str):
    """Verschiebt eine Datei oder einen Ordner innerhalb der erlaubten Workspaces."""
    return filesystem_manager.move_file(source_path, destination_path)


register_tool(Tool(func=create_file_tool, args_schema=schemas.CreateFileArgs))
register_tool(Tool(func=read_file_tool, args_schema=schemas.ReadFileArgs))
register_tool(Tool(func=delete_file_tool, args_schema=schemas.DeleteFileArgs))
register_tool(Tool(func=list_directory_tool, args_schema=schemas.ListDirectoryArgs))
register_tool(Tool(func=create_directory_tool, args_schema=schemas.CreateDirectoryArgs))
register_tool(Tool(func=delete_directory_tool, args_schema=schemas.DeleteDirectoryArgs))
register_tool(Tool(func=rename_file_tool, args_schema=schemas.RenameFileArgs))
register_tool(Tool(func=move_file_tool, args_schema=schemas.MoveFileArgs))

def get_all_tool_definitions():
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]
