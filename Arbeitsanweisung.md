Finale Arbeitsanweisung für den Coding Agent
Ziel: Rüsten Sie die Dateisystem-Tools auf, um Filterung und Massenoperationen zu ermöglichen und so komplexe Anfragen in einem Schritt zu bearbeiten.
Schritt 1: backend/schemas.py erweitern
Fügen Sie die neuen Pydantic-Modelle hinzu und passen Sie das bestehende an. Ersetzen Sie den gesamten "Filesystem Tool Schemas"-Block mit diesem neuen Block.
code
Python
# In backend/schemas.py (ersetzen Sie den gesamten Filesystem-Block)

# --- Filesystem Tool Schemas ---
class CreateFileArgs(BaseModel):
    path: str
    content: Optional[str] = ""

class ReadFileArgs(BaseModel):
    path: str

class DeleteFileArgs(BaseModel):
    path: str

# ERWEITERT: Füge einen optionalen Pattern-Parameter hinzu
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
    
# NEUES POWER-TOOL SCHEMA
class MoveFilesArgs(BaseModel):
    source_directory: str
    destination_directory: str
    pattern: str```

---

#### **Schritt 2: `backend/filesystem_manager.py` aufrüsten**

Ersetzen Sie den **gesamten Inhalt** der Datei `backend/filesystem_manager.py` mit diesem neuen Code. Er enthält die verbesserte `list_directory`-Funktion und die brandneue `move_files`-Funktion.

```python
# Vollständige, aufgerüstete Datei: backend/filesystem_manager.py

import os
import shutil
import logging
import json
from pathlib import Path
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

CONFIG_FILE = Path(get_app_data_dir()) / "config.json"
DEFAULT_WORKSPACE = Path(get_app_data_dir()) / "workspace"
DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)

def _get_allowed_workspaces() -> list[Path]:
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                config = json.load(f)
            user_workspaces = config.get("filesystem_workspaces", [])
            resolved_paths = [Path(p).resolve() for p in user_workspaces if p and os.path.isdir(p)]
            if DEFAULT_WORKSPACE.resolve() not in resolved_paths:
                resolved_paths.append(DEFAULT_WORKSPACE.resolve())
            resolved_paths.reverse()
            return resolved_paths
    except Exception as e:
        logger.error(f"Fehler beim Laden der Workspace-Konfiguration: {e}")
    return [DEFAULT_WORKSPACE.resolve()]

ALLOWED_WORKSPACES = _get_allowed_workspaces()
logger.info(f"Erlaubte Filesystem-Workspaces (nach Priorität): {[str(p) for p in ALLOWED_WORKSPACES]}")


def _resolve_and_validate_path(user_path: str) -> Path:
    cleaned_path = Path(user_path.strip().replace('\\', '/'))
    if cleaned_path.is_absolute():
        resolved_path = cleaned_path.resolve()
        for workspace in ALLOWED_WORKSPACES:
            if resolved_path.is_relative_to(workspace):
                return resolved_path
        raise PermissionError(f"Absoluter Pfad '{user_path}' befindet sich außerhalb aller erlaubten Workspaces.")
    for workspace in ALLOWED_WORKSPACES:
        if cleaned_path.parts and cleaned_path.parts[0].lower() == workspace.name.lower():
            potential_path = (workspace.parent / cleaned_path).resolve()
        else:
            potential_path = (workspace / cleaned_path).resolve()
        if potential_path.is_relative_to(workspace):
            return potential_path
    raise PermissionError(f"Zugriff verweigert. Der Pfad '{user_path}' konnte keinem erlaubten Workspace zugeordnet werden.")


def create_file(path: str, content: str = "") -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if safe_path.exists():
            return {"output": f"Fehler: '{path}' existiert bereits."}
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding='utf-8')
        logger.info(f"Datei erstellt: {safe_path}")
        return {"output": f"Datei '{path}' wurde erfolgreich erstellt."}
    except Exception as e:
        logger.error(f"Fehler bei create_file mit Pfad '{path}': {e}")
        return {"output": f"Fehler: {e}"}

def read_file(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_file():
            return {"output": f"Fehler: '{path}' ist keine Datei oder existiert nicht."}
        content = safe_path.read_text(encoding='utf-8')
        return {"output": f"Inhalt von '{path}':\n---\n{content}\n---"}
    except Exception as e:
        logger.error(f"Fehler bei read_file mit Pfad '{path}': {e}")
        return {"output": f"Fehler: {e}"}

def delete_file(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_file():
            return {"output": f"Fehler: '{path}' ist keine Datei oder existiert nicht."}
        safe_path.unlink()
        logger.info(f"Datei gelöscht: {safe_path}")
        return {"output": f"Datei '{path}' wurde erfolgreich gelöscht."}
    except Exception as e:
        logger.error(f"Fehler bei delete_file mit Pfad '{path}': {e}")
        return {"output": f"Fehler: {e}"}

# --- VERBESSERTES TOOL ---
def list_directory(path: str, pattern: Optional[str] = None) -> dict:
    try:
        if path.strip() in ['.', '', '/']:
            ws_names = [f"{w.name}/" for w in ALLOWED_WORKSPACES]
            return {"output": "Verfügbare Workspaces (nach Priorität):\n" + "\n".join(ws_names)}
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_dir():
            return {"output": f"Fehler: '{path}' ist kein Ordner oder existiert nicht."}
        
        # Logik für die Mustersuche
        if pattern:
            items = [f"{item.name}{'/' if item.is_dir() else ''}" for item in safe_path.glob(pattern)]
            output_intro = f"Inhalt von '{path}' passend zu '{pattern}':\n"
        else:
            items = [f"{item.name}{'/' if item.is_dir() else ''}" for item in safe_path.iterdir()]
            output_intro = f"Inhalt von '{path}':\n"
            
        output = output_intro + "\n".join(items) if items else f"Keine passenden Einträge in '{path}' gefunden."
        return {"output": output}
    except Exception as e:
        logger.error(f"Fehler bei list_directory mit Pfad '{path}': {e}")
        return {"output": f"Fehler: {e}"}

def create_directory(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if safe_path.exists():
            return {"output": f"Fehler: '{path}' existiert bereits."}
        safe_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ordner erstellt: {safe_path}")
        return {"output": f"Ordner '{path}' wurde erfolgreich erstellt."}
    except Exception as e:
        logger.error(f"Fehler bei create_directory mit Pfad '{path}': {e}")
        return {"output": f"Fehler: {e}"}

def delete_directory(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_dir():
            return {"output": f"Fehler: '{path}' ist kein Ordner."}
        if safe_path in ALLOWED_WORKSPACES:
             return {"output": "Fehler: Ein Workspace-Stammverzeichnis darf nicht gelöscht werden."}
        shutil.rmtree(safe_path)
        logger.info(f"Ordner rekursiv gelöscht: {safe_path}")
        return {"output": f"Ordner '{path}' und sein Inhalt wurden gelöscht."}
    except Exception as e:
        logger.error(f"Fehler bei delete_directory mit Pfad '{path}': {e}")
        return {"output": f"Fehler: {e}"}

def move_file(source_path: str, destination_path: str) -> dict:
    try:
        safe_source = _resolve_and_validate_path(source_path)
        safe_dest = _resolve_and_validate_path(destination_path)
        if not safe_source.exists():
            return {"output": f"Fehler: Quelle '{source_path}' existiert nicht."}
        if safe_dest.exists():
            return {"output": f"Fehler: Ziel '{destination_path}' existiert bereits."}
        if safe_source in ALLOWED_WORKSPACES:
            return {"output": "Fehler: Ein Workspace-Stammverzeichnis kann nicht verschoben/umbenannt werden."}
        safe_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(safe_source), str(safe_dest))
        logger.info(f"Verschoben/Umbenannt: {safe_source} -> {safe_dest}")
        return {"output": f"'{source_path}' wurde erfolgreich nach '{destination_path}' verschoben/umbenannt."}
    except Exception as e:
        logger.error(f"Fehler bei move_file von '{source_path}': {e}")
        return {"output": f"Fehler: {e}"}

rename_file = move_file

# --- NEUES POWER-TOOL ---
def move_files(source_directory: str, destination_directory: str, pattern: str) -> dict:
    """Verschiebt mehrere Dateien, die einem Muster entsprechen, von einem Ordner in einen anderen."""
    try:
        safe_source_dir = _resolve_and_validate_path(source_directory)
        safe_dest_dir = _resolve_and_validate_path(destination_directory)

        if not safe_source_dir.is_dir():
            return {"output": f"Fehler: Quelle '{source_directory}' ist kein Ordner."}
        if not safe_dest_dir.is_dir():
            return {"output": f"Fehler: Ziel '{destination_directory}' ist kein Ordner."}
        
        files_to_move = list(safe_source_dir.glob(pattern))
        if not files_to_move:
            return {"output": f"Keine Dateien passend zum Muster '{pattern}' in '{source_directory}' gefunden."}

        moved_count = 0
        errors = []
        for file_path in files_to_move:
            if file_path.is_file():
                try:
                    shutil.move(str(file_path), str(safe_dest_dir))
                    moved_count += 1
                except Exception as e:
                    errors.append(f"Konnte '{file_path.name}' nicht verschieben: {e}")
        
        logger.info(f"{moved_count} Dateien passend zu '{pattern}' nach '{safe_dest_dir}' verschoben.")
        
        if errors:
            error_details = "\n".join(errors)
            return {"output": f"{moved_count} von {len(files_to_move)} Dateien erfolgreich verschoben. Fehler:\n{error_details}"}
        else:
            return {"output": f"Alle {moved_count} Dateien passend zu '{pattern}' wurden erfolgreich nach '{destination_directory}' verschoben."}
            
    except Exception as e:
        logger.error(f"Fehler bei move_files: {e}")
        return {"output": f"Fehler: {e}"}
Schritt 3: backend/tool_registry.py aktualisieren
Ersetzen Sie den gesamten Inhalt der Datei backend/tool_registry.py mit dem folgenden Code. Dies stellt sicher, dass die neuen und geänderten Tools korrekt mit den neuen Schemas und Beschreibungen für die KI registriert werden.
code
Python
# Vollständige, aktualisierte Datei: backend/tool_registry.py

import inspect
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel
from backend import llm_gateway, schemas, filesystem_manager
from sqlalchemy.orm import Session
from backend import crud

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
async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    """Generiert ein Bild basierend auf einem Text-Prompt mit DALL-E 3."""
    return await llm_gateway.generate_image_tool(api_key=api_key, prompt=prompt, size=size, quality=quality, response_format=response_format)

def cross_chat_memory_tool(query: str, db: Session):
    """Ruft Zusammenfassungen der letzten Konversationen ab, um Fragen über die Vergangenheit zu beantworten."""
    all_chats = crud.get_chats(db, include_archived=True)
    recent_chats = sorted(all_chats, key=lambda chat: chat.created_at, reverse=True)[1:6]
    if not recent_chats:
        return {"output": "Keine früheren Chats zum Überprüfen gefunden."}
    output_snippets = ["--- ZUSAMMENFASSUNGEN DER LETZTEN CHATS ---"]
    for chat in recent_chats:
        if chat.summary:
            output_snippets.append(f"Thema des Chats '{chat.title}': {chat.summary}")
    if len(output_snippets) == 1:
        return {"output": "Keine relevanten Zusammenfassungen in früheren Chats gefunden."}
    return {"output": "\n".join(output_snippets)}

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

def get_all_tool_definitions():
    return [tool.llm_definition for tool in TOOL_REGISTRY.values()]