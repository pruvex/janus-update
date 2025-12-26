# backend/services/tool_executor.py
import asyncio
import inspect
import json
import logging
from typing import Any, Dict, List

# Wir importieren das Registry-Modul, um sicherzustellen, dass die Tools registriert werden,
# wenn sie es noch nicht sind.
import backend.tool_registry as registry
from backend.services.tool_manager import tool_manager
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger("janus_backend")


class ToolExecutor:
    def __init__(
        self,
        db: Session,
        api_key: str,
        provider: str,
        model: str,
        additional_context: Dict[str, Any] = None,
    ):
        # Sicherstellen, dass Tools geladen sind
        if not tool_manager.get_all_tools():
            registry.register_all_tools()

        self.db = db
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.additional_context = additional_context or {}  # Speichern des zusätzlichen Kontexts

        # --- MAPPING FÜR GEMINI HALLUZINATIONEN ---
        # Das Ziel muss exakt so heißen wie der Funktionsname
        target_memory_tool = "save_core_memory_fact"

        self.tool_aliases = {
            # Memory Aliase
            "save_user_preference": target_memory_tool,
            "update_core_memory": target_memory_tool,
            "remember_preference_tool": target_memory_tool,
            "save_preference": target_memory_tool,
            "store_memory": target_memory_tool,
            "remember_this": target_memory_tool,
            "add_memory": target_memory_tool,
            "upsert_user_preference": target_memory_tool,
            "remember_user_preference": target_memory_tool,
            "save_memory": target_memory_tool,
            "update_core_memory_users_preference": target_memory_tool,
            "update_user_preferences": target_memory_tool,
            # Fallback
            "save_core_memory_tool": target_memory_tool,
            # Contact Aliase
            "add_contact": "create_or_update_contact_tool",
            "update_contact": "create_or_update_contact_tool",
            "create_contact": "create_or_update_contact_tool",
            # File Aliase
            "write_file": "create_file_tool",
            "make_file": "create_file_tool",
        }

    async def execute_tool_call(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Führt einen einzelnen Tool-Aufruf aus."""

        original_name = tool_name

        # 1. Alias-Prüfung
        if not tool_manager.get_tool(tool_name) and tool_name in self.tool_aliases:
            tool_name = self.tool_aliases[tool_name]
            logger.info(f"Tool-Alias angewendet: '{original_name}' -> '{tool_name}'")

        # 2. Tool vom Manager holen
        tool_def = tool_manager.get_tool(tool_name)

        if not tool_def:
            logger.error(
                f"CRITICAL: Tool '{tool_name}' (Mapped from '{original_name}') nicht im Manager gefunden."
            )
            return {
                "role": "tool",
                "name": original_name,
                "content": f"Error: Tool '{original_name}' not found.",
            }

        try:
            # 3. Argumente bereinigen für Core Memory (Legacy Hack, könnte man auch ins Tool verschieben)
            if tool_name == "save_core_memory_fact":
                fact = (
                    tool_args.get("fact")
                    or tool_args.get("preference")
                    or tool_args.get("new_memory")
                    or tool_args.get("preference_value")
                    or tool_args.get("new_preferences")
                    or tool_args.get("key")
                    or tool_args.get("value")
                )

                if not fact and ("key" in tool_args or "value" in tool_args):
                    parts = []
                    if "key" in tool_args:
                        parts.append(f"{tool_args['key']}")
                    if "value" in tool_args:
                        parts.append(f"{tool_args['value']}")
                    fact = ": ".join(parts)

                if isinstance(fact, dict):
                    fact = ", ".join([f"{k}: {v}" for k, v in fact.items()])

                if fact:
                    tool_args = {"fact": fact, "category": tool_args.get("category", "Preference")}

            logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")

            # 4. Context Injection (Dependency Injection)
            context_vars = {
                "db": self.db,
                "api_key": self.api_key,
                "provider": self.provider,
                "model": self.model,
                **self.additional_context,  # Dynamischen Kontext einfügen
            }

            sig = inspect.signature(tool_def.func)
            final_args = {}

            for param_name, param in sig.parameters.items():
                if param_name in tool_args:
                    final_args[param_name] = tool_args[param_name]
                elif param_name in context_vars:
                    # Hier passiert die Magie: Wir injizieren db, api_key, etc.
                    final_args[param_name] = context_vars[param_name]
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    pass

            # 5. Ausführung
            if asyncio.iscoroutinefunction(tool_def.func):
                result = await tool_def.func(**final_args)
            else:
                result = await asyncio.to_thread(tool_def.func, **final_args)

            # Ergebnis serialisieren
            if isinstance(result, BaseModel):
                result = result.model_dump_json()
            elif isinstance(result, list) and all(isinstance(item, BaseModel) for item in result):
                result = json.dumps([item.model_dump() for item in result], ensure_ascii=False)
            else:
                result = json.dumps(result, ensure_ascii=False)

            return {"role": "tool", "name": original_name, "content": result}

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return {
                "role": "tool",
                "name": original_name,
                "content": f"Error executing tool: {str(e)}",
            }

    async def execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Führt eine Liste von Tool-Aufrufen parallel aus."""
        tasks = []
        for tool_call in tool_calls:
            func_name = tool_call.get("function", {}).get("name")
            try:
                func_args = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            except json.JSONDecodeError:
                func_args = {}

            tasks.append(self.execute_tool_call(func_name, func_args))

        results = await asyncio.gather(*tasks)

        final_results = []
        for i, res in enumerate(results):
            if i < len(tool_calls):
                res["tool_call_id"] = tool_calls[i].get("id")
            final_results.append(res)

        return final_results
