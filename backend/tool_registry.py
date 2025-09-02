# backend/tool_registry.py
import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel
from backend import llm_gateway, schemas
from sqlalchemy.orm import Session
from backend import crud, vector_service
from backend.database import get_db
from fastapi import Depends

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

def get_all_tool_definitions():
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]