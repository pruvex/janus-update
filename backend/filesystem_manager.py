import os
import shutil
import logging
import json
from pathlib import Path
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')

# --- Konfiguration der Workspaces ---
CONFIG_FILE = Path(get_app_data_dir()) / "config.json"
DEFAULT_WORKSPACE = Path(get_app_data_dir()) / "workspace"
DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)

def _get_allowed_workspaces() -> list[Path]:
    """Lädt die vom Benutzer konfigurierten Workspaces aus der config.json."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                config = json.load(f)
            
            user_workspaces = config.get("filesystem_workspaces", [])
            resolved_paths = [Path(p).resolve() for p in user_workspaces if os.path.isdir(p)]
            
            if resolved_paths:
                if DEFAULT_WORKSPACE.resolve() not in resolved_paths:
                    resolved_paths.append(DEFAULT_WORKSPACE.resolve())
                return resolved_paths
    except Exception as e:
        logger.error(f"Fehler beim Laden der Workspace-Konfiguration: {e}")
    
    return [DEFAULT_WORKSPACE.resolve()]

ALLOWED_WORKSPACES = _get_allowed_workspaces()
logger.info(f"Erlaubte Filesystem-Workspaces: {[str(p) for p in ALLOWED_WORKSPACES]}")


def _resolve_and_validate_path(user_path: str) -> Path:
    """
    Validiert einen vom Benutzer bereitgestellten Pfad gegen die Liste der erlaubten Workspaces.
    Dies ist die zentrale Sicherheitsfunktion.
    """
    cleaned_path = user_path.strip()
    
    # Versuche, den Pfad basierend auf einem der Workspaces aufzulösen
    for workspace in ALLOWED_WORKSPACES:
        # Prüfe, ob der user_path möglicherweise ein absoluter Pfad ist, der in einem Workspace liegt
        try:
            resolved_path = Path(cleaned_path).resolve()
            if resolved_path.is_relative_to(workspace):
                return resolved_path
        except: # Fehler bei der Auflösung ignorieren, wenn der Pfad nicht existiert
            pass
            
        # Behandle den Pfad als relativ zum Workspace
        potential_path = (workspace / cleaned_path).resolve()
        if potential_path.is_relative_to(workspace):
            return potential_path

    raise PermissionError(f"Zugriff verweigert. Der Pfad '{user_path}' befindet sich außerhalb aller konfigurierten Workspaces.")


def create_file(path: str, content: str = "") -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if safe_path.exists():
            return {"output": f"Fehler: '{path}' existiert bereits."}
        
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding='utf-8')
        logger.info(f"Datei erstellt: {safe_path}")
        return {"output": f"Datei '{path}' wurde erfolgreich erstellt."}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Datei '{path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

def read_file(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_file():
            return {"output": f"Fehler: '{path}' ist keine Datei oder existiert nicht."}
        
        content = safe_path.read_text(encoding='utf-8')
        return {"output": f"Inhalt von '{path}':\n---\n{content}\n---"}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Datei '{path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

def delete_file(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_file():
            return {"output": f"Fehler: '{path}' ist keine Datei oder existiert nicht."}
        
        safe_path.unlink()
        logger.info(f"Datei gelöscht: {safe_path}")
        return {"output": f"Datei '{path}' wurde erfolgreich gelöscht."}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Datei '{path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

def list_directory(path: str) -> dict:
    try:
        # Sonderfall: Wenn der Pfad leer oder '.' ist, zeige die Wurzeln der Workspaces an
        if path.strip() in ['.', '', '/']:
            ws_names = [f"{w.name}/" for w in ALLOWED_WORKSPACES]
            return {"output": "Verfügbare Workspaces (Stammverzeichnisse):\n" + "\n".join(ws_names)}

        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_dir():
            return {"output": f"Fehler: '{path}' ist kein Ordner oder existiert nicht."}
        
        items = [f"{item.name}{'/' if item.is_dir() else ''}" for item in safe_path.iterdir()]
        output = f"Inhalt von '{path}':\n" + "\n".join(items) if items else f"Der Ordner '{path}' ist leer."
        return {"output": output}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler beim Auflisten des Ordners '{path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

def create_directory(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if safe_path.exists():
            return {"output": f"Fehler: '{path}' existiert bereits."}
        
        safe_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ordner erstellt: {safe_path}")
        return {"output": f"Ordner '{path}' wurde erfolgreich erstellt."}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Ordners '{path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

def delete_directory(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path)
        if not safe_path.is_dir():
            return {"output": f"Fehler: '{path}' ist kein Ordner oder existiert nicht."}
        if safe_path in ALLOWED_WORKSPACES:
             return {"output": f"Fehler: Ein konfiguriertes Workspace-Stammverzeichnis darf nicht gelöscht werden."}
        
        shutil.rmtree(safe_path)
        logger.info(f"Ordner rekursiv gelöscht: {safe_path}")
        return {"output": f"Ordner '{path}' und sein Inhalt wurden gelöscht."}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Ordners '{path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

def move_file(source_path: str, destination_path: str) -> dict:
    try:
        safe_source = _resolve_and_validate_path(source_path)
        safe_dest = _resolve_and_validate_path(destination_path)

        if not safe_source.exists():
            return {"output": f"Fehler: Quelle '{source_path}' existiert nicht."}
        if safe_dest.exists():
            return {"output": f"Fehler: Ziel '{destination_path}' existiert bereits."}
        if safe_path in ALLOWED_WORKSPACES:
            return {"output": f"Fehler: Ein Workspace-Stammverzeichnis kann nicht verschoben/umbenannt werden."}
            
        safe_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(safe_source), str(safe_dest))
        logger.info(f"Verschoben/Umbenannt: {safe_source} -> {safe_dest}")
        return {"output": f"'{source_path}' wurde erfolgreich nach '{destination_path}' verschoben/umbenannt."}
    except PermissionError as e:
        return {"output": f"Fehler: {e}"}
    except Exception as e:
        logger.error(f"Fehler bei der Operation von '{source_path}': {e}")
        return {"output": f"Ein unerwarteter Fehler ist aufgetreten: {e}"}

rename_file = move_file
