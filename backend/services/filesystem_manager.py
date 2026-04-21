# backend/services/filesystem_manager.py — Diamond Filesystem-Skills (ToolResultV1, Pfad-Härtung).

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
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
                if resolved_path.is_dir() and resolved_path.resolve() not in resolved_paths:
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


def _reject_unsafe_path_segments(user_path: str) -> None:
    """Verhindert Path-Traversal über explizite '..' Segmente (zusätzlich zur resolve/is_relative_to-Prüfung)."""
    cleaned = user_path.strip().replace("\\", "/")
    if not cleaned:
        raise PermissionError("Pfad darf nicht leer sein.")
    parts = Path(cleaned).parts
    if ".." in parts:
        raise PermissionError(
            "Pfadsegmente '..' (übergeordnete Verzeichnisse) sind nicht erlaubt. "
            "Nutze einen kanonischen Pfad innerhalb eines freigegebenen Workspace-Ordners."
        )


def _validate_glob_pattern(pattern: Optional[str]) -> None:
    if pattern is None or not str(pattern).strip():
        return
    normalized = str(pattern).replace("\\", "/")
    if ".." in normalized:
        raise PermissionError(
            "Suchmuster dürfen keine übergeordneten Pfadsegmente ('..') enthalten."
        )


def _fs_err(
    code: str,
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    started: float,
) -> ToolResultV1:
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
    return ToolResultV1(
        status="error",
        data={},
        message=message,
        error=ToolErrorDetails(code=code, message=message, details=details),
        metadata={"execution_time_ms": elapsed_ms},
    )


def _fs_ok(
    data: Dict[str, Any],
    *,
    message: Optional[str] = None,
    started: float,
) -> ToolResultV1:
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
    return ToolResultV1(
        status="ok",
        data=data,
        message=message,
        metadata={"execution_time_ms": elapsed_ms},
    )


def _map_filesystem_exception(started: float, exc: Exception) -> ToolResultV1:
    if isinstance(exc, FileNotFoundError):
        return _fs_err("NOT_FOUND", f"Fehler: {exc}", started=started)
    if isinstance(exc, PermissionError):
        return _fs_err("PERMISSION_DENIED", f"Fehler: {exc}", started=started)
    logger.error("Unbehandelter Filesystem-Fehler: %s", exc, exc_info=True)
    return _fs_err("OPERATION_FAILED", f"Fehler: {exc}", started=started)


def _resolve_and_validate_path(user_path: str, must_exist: bool = True) -> Path:
    """Findet den korrekten, absoluten Pfad und validiert ihn."""
    _reject_unsafe_path_segments(user_path)
    allowed_workspaces = _get_allowed_workspaces()  # Lade die Workspaces bei jedem Aufruf
    cleaned_path = Path(user_path.strip().replace("\\", "/"))

    # Determine if the path is absolute based on its anchor (drive letter, root)
    is_absolute_path = bool(cleaned_path.anchor)

    if is_absolute_path:
        resolved = cleaned_path.resolve()
        # Check if path is in a workspace (for must_exist validation)
        in_workspace = False
        for ws in allowed_workspaces:
            if resolved.is_relative_to(ws.resolve()):
                in_workspace = True
                if must_exist and not resolved.exists():
                    raise FileNotFoundError(f"Pfad '{user_path}' existiert nicht.")
                return resolved
        # If absolute path is not in a workspace, still return it
        # The @requires_path_auth decorator will handle permission checking
        if must_exist and not resolved.exists():
            raise FileNotFoundError(f"Pfad '{user_path}' existiert nicht.")
        return resolved
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


def create_file(path: str, content: str = "", is_binary: bool = False) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=False)
        if safe_path.exists():
            msg = f"Fehler: '{path}' existiert bereits."
            return _fs_err("ALREADY_EXISTS", msg, started=started)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        if is_binary:
            logger.debug(
                "create_file: is_binary=True. Content type: %s. First 100 bytes: %s",
                type(content),
                content[:100] if isinstance(content, bytes) else content[:100].encode("utf-8"),
            )
            if isinstance(content, str):
                content = content.encode(
                    "latin-1"
                )  # Assuming binary content passed as latin-1 encoded string
            safe_path.write_bytes(content)
        else:
            if isinstance(content, bytes):
                content = content.decode("utf-8")  # Assuming text content passed as utf-8 encoded bytes
            safe_path.write_text(content, encoding="utf-8")
        logger.info(f"Datei erstellt: {safe_path}")
        out = f"Datei '{path}' wurde erfolgreich erstellt."
        return _fs_ok({"output": out, "path": str(safe_path)}, message=out, started=started)
    except Exception as e:
        return _map_filesystem_exception(started, e)


def read_file(path: str) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=True)
        if safe_path.suffix.lower() == ".pdf":
            msg = (
                "Fehler: Datei ist binaer und kann nicht als Text gelesen werden "
                f"('{path}')."
            )
            return _fs_err("UNSUPPORTED_MEDIA_TYPE", msg, started=started)

        raw_bytes = safe_path.read_bytes()
        if b"\x00" in raw_bytes[:1024]:
            msg = (
                "Fehler: Datei ist binaer und kann nicht als Text gelesen werden "
                f"('{path}')."
            )
            return _fs_err("UNSUPPORTED_MEDIA_TYPE", msg, started=started)

        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            msg = (
                "Fehler: Datei ist binaer und kann nicht als Text gelesen werden "
                f"('{path}')."
            )
            return _fs_err("UNSUPPORTED_MEDIA_TYPE", msg, started=started)

        body = f"Inhalt von '{path}':\n---\n{content}\n---"
        short = f"Text aus '{path}' geladen ({len(content)} Zeichen)."
        return _fs_ok({"output": body, "path": str(safe_path)}, message=short, started=started)
    except Exception as e:
        return _map_filesystem_exception(started, e)


def delete_file(path: str) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=True)
        safe_path.unlink()
        logger.info(f"Datei gelöscht: {safe_path}")
        out = f"Datei '{path}' wurde erfolgreich gelöscht."
        return _fs_ok({"output": out, "path": str(safe_path)}, message=out, started=started)
    except Exception as e:
        return _map_filesystem_exception(started, e)


def list_directory(path: str, pattern: Optional[str] = None) -> ToolResultV1:
    started = time.perf_counter()
    try:
        _validate_glob_pattern(pattern)
        allowed_workspaces = _get_allowed_workspaces()
        if path.strip() in [".", "", "/"]:
            ws_names = [f"{w.name}/" for w in allowed_workspaces]
            out = f"Es sind {len(ws_names)} Workspaces verfügbar: {', '.join(ws_names)}"
            return _fs_ok(
                {"output": out, "count": len(ws_names), "items": ws_names},
                message=out,
                started=started,
            )

        safe_path = _resolve_and_validate_path(path, must_exist=True)

        if pattern:
            items = list(safe_path.glob(pattern))
            output_intro = (
                f"Es wurden {len(items)} Einträge passend zu '{pattern}' in '{path}' gefunden."
            )
        else:
            items = list(safe_path.iterdir())
            output_intro = f"Es wurden {len(items)} Einträge in '{path}' gefunden."

        item_names = [f"{item.name}{'/' if item.is_dir() else ''}" for item in items]

        if 0 < len(item_names) < 25:
            output = f"{output_intro}\n" + "\n".join(item_names)
        else:
            output = output_intro

        return _fs_ok(
            {"output": output, "count": len(items), "items": item_names},
            message=output_intro,
            started=started,
        )
    except Exception as e:
        return _map_filesystem_exception(started, e)


def create_directory(path: str) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=False)
        if safe_path.exists():
            msg = f"Fehler: '{path}' existiert bereits."
            return _fs_err("ALREADY_EXISTS", msg, started=started)
        safe_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ordner erstellt: {safe_path}")
        out = f"Ordner '{path}' wurde erfolgreich erstellt."
        return _fs_ok({"output": out, "path": str(safe_path)}, message=out, started=started)
    except Exception as e:
        return _map_filesystem_exception(started, e)


def delete_directory(path: str) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_path = _resolve_and_validate_path(path, must_exist=True)
        if safe_path in _get_allowed_workspaces():
            msg = "Fehler: Ein Workspace-Stammverzeichnis darf nicht gelöscht werden."
            return _fs_err("WORKSPACE_ROOT_PROTECTED", msg, started=started)
        shutil.rmtree(safe_path)
        logger.info(f"Ordner rekursiv gelöscht: {safe_path}")
        out = f"Ordner '{path}' und sein Inhalt wurden gelöscht."
        return _fs_ok({"output": out, "path": str(safe_path)}, message=out, started=started)
    except Exception as e:
        return _map_filesystem_exception(started, e)


def move_file(source_path: str, destination_path: str) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_source = _resolve_and_validate_path(source_path, must_exist=True)
        safe_dest = _resolve_and_validate_path(destination_path, must_exist=False)

        if safe_dest.exists():
            msg = f"Fehler: Ziel '{destination_path}' existiert bereits."
            return _fs_err("ALREADY_EXISTS", msg, started=started)
        if safe_source in _get_allowed_workspaces():
            msg = "Fehler: Ein Workspace-Stammverzeichnis kann nicht verschoben/umbenannt werden."
            return _fs_err("WORKSPACE_ROOT_PROTECTED", msg, started=started)
        safe_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(safe_source), str(safe_dest))
        logger.info(f"Verschoben/Umbenannt: {safe_source} -> {safe_dest}")
        out = f"'{source_path}' wurde erfolgreich nach '{destination_path}' verschoben/umbenannt."
        return _fs_ok(
            {
                "output": out,
                "source_path": str(safe_source),
                "destination_path": str(safe_dest),
            },
            message=out,
            started=started,
        )
    except Exception as e:
        return _map_filesystem_exception(started, e)


def rename_file(old_path: str, new_path: str) -> ToolResultV1:
    try:
        return move_file(old_path, new_path)
    except Exception as e:
        started = time.perf_counter()
        logger.error("Fehler bei rename_file: %s", e, exc_info=True)
        return _map_filesystem_exception(started, e)


def move_files(source_directory: str, destination_directory: str, pattern: str) -> ToolResultV1:
    started = time.perf_counter()
    try:
        _validate_glob_pattern(pattern)
        safe_source_dir = _resolve_and_validate_path(source_directory, must_exist=True)
        safe_dest_dir = _resolve_and_validate_path(destination_directory, must_exist=False)

        if not safe_dest_dir.exists():
            safe_dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Zielordner '{destination_directory}' wurde erstellt.")

        files_to_move = [f for f in safe_source_dir.glob(pattern) if f.is_file()]
        if not files_to_move:
            out = (
                f"Keine Dateien passend zum Muster '{pattern}' in '{source_directory}' gefunden."
            )
            return _fs_ok(
                {"output": out, "moved_count": 0, "error_count": 0, "items": []},
                message=out,
                started=started,
            )

        moved_count = 0
        errors: list[str] = []
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
            output = (
                f"{moved_count} von {len(files_to_move)} Dateien erfolgreich verschoben. Fehler:\n"
                f"{error_details}"
            )
        else:
            output = (
                f"Alle {moved_count} Dateien passend zu '{pattern}' wurden erfolgreich nach "
                f"'{destination_directory}' verschoben."
            )

        return _fs_ok(
            {
                "output": output,
                "moved_count": moved_count,
                "error_count": len(errors),
                "errors": errors,
            },
            message=output,
            started=started,
        )

    except Exception as e:
        return _map_filesystem_exception(started, e)


def list_allowed_workspaces() -> ToolResultV1:
    """Gibt eine Liste der erlaubten Arbeitsbereiche zurück."""
    started = time.perf_counter()
    try:
        workspaces = _get_allowed_workspaces()
        workspace_paths = [str(ws) for ws in workspaces]
        out = "Erlaubte Arbeitsbereiche:\n" + "\n".join(workspace_paths)
        return _fs_ok(
            {"output": out, "workspaces": workspace_paths},
            message=f"{len(workspace_paths)} freigegebene Workspace(s).",
            started=started,
        )
    except Exception as e:
        return _map_filesystem_exception(started, e)
