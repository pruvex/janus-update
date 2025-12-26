# backend/services/tool_manager.py
import inspect
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger("janus_backend")


class ToolDefinition:
    """Repräsentiert ein einzelnes Werkzeug und dessen Metadaten für das LLM."""

    def __init__(
        self,
        func: Callable,
        args_schema: Optional[BaseModel] = None,
        description: Optional[str] = None,
    ):
        self.func = func
        self.args_schema = args_schema
        self.name = func.__name__
        self.description = description or inspect.getdoc(func)
        self.llm_definition = self._build_llm_definition()

    def _build_llm_definition(self) -> Dict[str, Any]:
        """Erstellt das JSON-Schema für die OpenAI/Gemini API."""
        schema = (
            self.args_schema.model_json_schema()
            if self.args_schema
            else {"properties": {}, "required": []}
        )
        if "title" in schema:
            del schema["title"]

        desc = self.description or ""
        # Platzhalter für aktuelles Datum ersetzen, falls im Docstring vorhanden
        if "{current_date}" in desc:
            desc = desc.replace("{current_date}", datetime.now().strftime("%d. %B %Y"))

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": desc,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }


class ToolManager:
    """Singleton-Service zur Verwaltung aller verfügbaren Tools."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolManager, cls).__new__(cls)
            cls._instance.tools: Dict[str, ToolDefinition] = {}
            logger.info("ToolManager initialized.")
        return cls._instance

    def register_tool(
        self,
        func: Callable,
        args_schema: Optional[BaseModel] = None,
        description: Optional[str] = None,
    ):
        """Registriert ein neues Tool."""
        tool = ToolDefinition(func, args_schema, description)
        self.tools[tool.name] = tool
        # logger.debug(f"Tool registered: {tool.name}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Holt ein Tool anhand des Namens."""
        return self.tools.get(name)

    def get_all_tools(self) -> Dict[str, ToolDefinition]:
        """Gibt alle registrierten Tool-Objekte zurück."""
        return self.tools

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gibt die Liste der JSON-Definitionen für das LLM zurück."""
        return [tool.llm_definition for tool in self.tools.values()]


# Global Singleton Instance
tool_manager = ToolManager()
