# Finale, korrekte und stabile Version: backend/filesystem_manager.py

import os
import shutil
import logging
import json
from pathlib import Path
from typing import Optional
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

CONFIG_FILE = Path(get_app_data_dir()) / "config.json"
DEFAULT_WORKSPACE = Path(get_app_data_dir()) / "workspace"
DEFAULT_WORKSPACE.mkdir(parents=True, exist_ok=True)

PLACEHOLDER_MAP = {
    "{DESKTOP}": Path.home() / "Desktop",
    "{DOCUMENTS}": Path.home() / "Documents",
    "{DOWNLOADS}": Path.home() / "Downloads",
}


def _get_allowed_workspaces() -> list[Path]:
    """Lädt die vom Benutzer konfigurierten Workspaces und priorisiert sie korrekt."""
    resolved_paths = []

    # Beginne die Liste IMMER mit den benutzerdefinierten Pfaden.
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            user_workspaces = config.get("filesystem_workspaces", [])
            for path_str in user_workspaces:
                final_path_str = PLACEHOLDER_MAP.get(path_str.upper(), path_str)
                resolved_path = Path(final_path_str).resolve()
                if (
                    resolved_path.is_dir()
                    and resolved_path.resolve() not in resolved_paths
                ):
                    resolved_paths.append(resolved_path.resolve())
    except Exception as e:
        logger.error(f"Fehler beim Laden der Workspace-Konfiguration: {e}")

    # Füge den Desktop-Pfad standardmäßig hinzu
    desktop_path = Path.home() / "Desktop"
    if desktop_path.is_dir() and desktop_path.resolve() not in resolved_paths:
        resolved_paths.append(desktop_path.resolve())

    # Füge den Standard-Workspace am ENDE als Fallback hinzu.
    if DEFAULT_WORKSPACE.resolve() not in resolved_paths:
        resolved_paths.append(DEFAULT_WORKSPACE.resolve())

    return resolved_paths


def _resolve_and_validate_path(user_path: str, must_exist: bool = True) -> Path:
    """Findet den korrekten, absoluten Pfad und validiert ihn."""
    allowed_workspaces = (
        _get_allowed_workspaces()
    )  # Lade die Workspaces bei jedem Aufruf
    cleaned_path = Path(user_path.strip().replace("\\", "/"))

    # Determine if the path is absolute based on its anchor (drive letter, root)
    is_absolute_path = bool(cleaned_path.anchor)

    if is_absolute_path:
        resolved = cleaned_path.resolve()
        for ws in allowed_workspaces:
            if resolved.is_relative_to(ws.resolve()):
                if must_exist and not resolved.exists():
                    raise FileNotFoundError(f"Pfad '{user_path}' existiert nicht.")
                return resolved
        # If it's an absolute path but not relative to any allowed workspace
        raise PermissionError(f"Absoluter Pfad '{user_path}' ist nicht erlaubt.")
    else:  # Handle relative paths
        # First, check if the path starts with a workspace name
        for ws in allowed_workspaces:
            if cleaned_path.parts and cleaned_path.parts[0].lower() == ws.name.lower():
                potential_path = (ws / Path(*cleaned_path.parts[1:])).resolve()
                if potential_path.is_relative_to(ws.resolve()):
                    if must_exist:
                        if potential_path.exists():
                            return potential_path
                    else:
                        return potential_path

        # If not, then check for relative paths in all workspaces
        for ws in allowed_workspaces:
            potential_path = (ws / cleaned_path).resolve()
            if potential_path.is_relative_to(ws.resolve()):
                if must_exist:
                    if potential_path.exists():
                        return potential_path
                else:
                    return potential_path

    # If no path could be resolved (neither absolute nor relative within allowed workspaces)
    raise FileNotFoundError(f"Pfad '{user_path}' existiert nicht.")


def create_file(path: str, content: str | bytes = "", is_binary: bool = False) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=False)
        if safe_path.exists():
            return {"output": f"Fehler: '{path}' existiert bereits."}
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        if is_binary:
            if isinstance(content, str):
                content = content.encode("latin-1") # Assuming binary content passed as latin-1 encoded string
            safe_path.write_bytes(content)
        else:
            if isinstance(content, bytes):
                content = content.decode("utf-8") # Assuming text content passed as utf-8 encoded bytes
            safe_path.write_text(content, encoding="utf-8")
        logger.info(f"Datei erstellt: {safe_path}")
        return {"output": f"Datei '{path}' wurde erfolgreich erstellt."}
    except Exception as e:
        logger.error(f"Fehler bei create_file: {e}")
        return {"output": f"Fehler: {e}"}


def read_file(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=True)
        content = safe_path.read_text(encoding="utf-8")
        return {"output": f"Inhalt von '{path}':\n---\n{content}\n---"}
    except Exception as e:
        logger.error(f"Fehler bei read_file: {e}")
        return {"output": f"Fehler: {e}"}


def delete_file(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=True)
        safe_path.unlink()
        logger.info(f"Datei gelöscht: {safe_path}")
        return {"output": f"Datei '{path}' wurde erfolgreich gelöscht."}
    except Exception as e:
        logger.error(f"Fehler bei delete_file: {e}")
        return {"output": f"Fehler: {e}"}


def list_directory(path: str, pattern: Optional[str] = None) -> dict:
    try:
        allowed_workspaces = _get_allowed_workspaces()
        if path.strip() in [".", "", "/"]:
            ws_names = [f"{w.name}/" for w in allowed_workspaces]
            return {
                "output": f"Es sind {len(ws_names)} Workspaces verfügbar: {', '.join(ws_names)}",
                "count": len(ws_names),
                "items": ws_names,
            }

        safe_path = _resolve_and_validate_path(path, must_exist=True)

        if pattern:
            items = list(safe_path.glob(pattern))
            output_intro = f"Es wurden {len(items)} Einträge passend zu '{pattern}' in '{path}' gefunden."
        else:
            items = list(safe_path.iterdir())
            output_intro = f"Es wurden {len(items)} Einträge in '{path}' gefunden."

        item_names = [f"{item.name}{'/' if item.is_dir() else ''}" for item in items]

        if 0 < len(item_names) < 25:
            output = f"{output_intro}\n" + "\n".join(item_names)
        else:
            output = output_intro

        return {"output": output, "count": len(items), "items": item_names}
    except Exception as e:
        logger.error(f"Fehler bei list_directory: {e}")
        return {"output": f"Fehler: {e}"}


def create_directory(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=False)
        if safe_path.exists():
            return {"output": f"Fehler: '{path}' existiert bereits."}
        safe_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ordner erstellt: {safe_path}")
        return {"output": f"Ordner '{path}' wurde erfolgreich erstellt."}
    except Exception as e:
        logger.error(f"Fehler bei create_directory: {e}")
        return {"output": f"Fehler: {e}"}


def delete_directory(path: str) -> dict:
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=True)
        if safe_path in _get_allowed_workspaces():
            return {
                "output": "Fehler: Ein Workspace-Stammverzeichnis darf nicht gelöscht werden."
            }
        shutil.rmtree(safe_path)
        logger.info(f"Ordner rekursiv gelöscht: {safe_path}")
        return {"output": f"Ordner '{path}' und sein Inhalt wurden gelöscht."}
    except Exception as e:
        logger.error(f"Fehler bei delete_directory: {e}")
        return {"output": f"Fehler: {e}"}


def move_file(source_path: str, destination_path: str) -> dict:
    try:
        safe_source = _resolve_and_validate_path(source_path, must_exist=True)
        safe_dest = _resolve_and_validate_path(destination_path, must_exist=False)

        if safe_dest.exists():
            return {"output": f"Fehler: Ziel '{destination_path}' existiert bereits."}
        if safe_source in ALLOWED_WORKSPACES:
            return {
                "output": "Fehler: Ein Workspace-Stammverzeichnis kann nicht verschoben/umbenannt werden."
            }
        safe_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(safe_source), str(safe_dest))
        logger.info(f"Verschoben/Umbenannt: {safe_source} -> {safe_dest}")
        return {
            "output": f"'{source_path}' wurde erfolgreich nach '{destination_path}' verschoben/umbenannt."
        }
    except Exception as e:
        logger.error(f"Fehler bei move_file: {e}")
        return {"output": f"Fehler: {e}"}


rename_file = move_file


def move_files(source_directory: str, destination_directory: str, pattern: str) -> dict:
    try:
        safe_source_dir = _resolve_and_validate_path(source_directory, must_exist=True)
        safe_dest_dir = _resolve_and_validate_path(
            destination_directory, must_exist=False
        )

        if not safe_dest_dir.exists():
            safe_dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Zielordner '{destination_directory}' wurde erstellt.")

        files_to_move = [f for f in safe_source_dir.glob(pattern) if f.is_file()]
        if not files_to_move:
            return {
                "output": f"Keine Dateien passend zum Muster '{pattern}' in '{source_directory}' gefunden."
            }

        moved_count = 0
        errors = []
        for file_path in files_to_move:
            try:
                shutil.move(str(file_path), str(safe_dest_dir))
                moved_count += 1
            except Exception as e:
                errors.append(f"Konnte '{file_path.name}' nicht verschieben: {e}")

        logger.info(
            f"{moved_count} Dateien passend zu '{pattern}' nach '{safe_dest_dir}' verschoben."
        )

        if errors:
            error_details = "\n".join(errors)
            output = f"{moved_count} von {len(files_to_move)} Dateien erfolgreich verschoben. Fehler:\n{error_details}"
        else:
            output = f"Alle {moved_count} Dateien passend zu '{pattern}' wurden erfolgreich nach '{destination_directory}' verschoben."

        return {
            "output": output,
            "moved_count": moved_count,
            "error_count": len(errors),
        }

    except Exception as e:
        logger.error(f"Fehler bei move_files: {e}")
        return {"output": f"Fehler: {e}"}


def list_allowed_workspaces() -> dict:
    """Gibt eine Liste der erlaubten Arbeitsbereiche zurück."""
    workspaces = _get_allowed_workspaces()
    workspace_paths = [str(ws) for ws in workspaces]
    return {
        "output": f"Erlaubte Arbeitsbereiche:\n" + "\n".join(workspace_paths),
        "workspaces": workspace_paths,
    }
