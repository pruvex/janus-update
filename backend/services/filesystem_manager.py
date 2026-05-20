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

    # Füge die Standard-Systempfade hinzu ( synchron mit Global Discovery )
    desktop_path = Path.home() / "Desktop"
    if desktop_path.is_dir() and desktop_path.resolve() not in resolved_paths:
        resolved_paths.append(desktop_path.resolve())

    documents_path = Path.home() / "Documents"
    if documents_path.is_dir() and documents_path.resolve() not in resolved_paths:
        resolved_paths.append(documents_path.resolve())

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


_SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    "secrets.json",
    "credentials.json",
}


def _is_sensitive_filesystem_target(value: Optional[str]) -> bool:
    normalized = str(value or "").strip().replace("\\", "/").lower()
    if not normalized:
        return False
    name = Path(normalized).name
    if name in _SENSITIVE_FILE_NAMES:
        return True
    if name.startswith(".env."):
        return True
    if name.endswith(".env") or ".env." in name:
        return True
    if any(marker in name for marker in ("secret", "credential", "api_key", "apikey", "token")):
        return True
    return False


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
        if _is_sensitive_filesystem_target(path):
            return _fs_err(
                "SENSITIVE_FILE_BLOCKED",
                "Fehler: Sicherheitsrelevante Dateien wie .env, Secrets, Tokens oder Credentials duerfen nicht gelesen werden.",
                started=started,
            )
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


def _is_pdf_indexed(file_path: Path) -> bool:
    """Prüft, ob eine PDF-Datei im IndexStore/ChromaDB indiziert ist."""
    if file_path.suffix.lower() != ".pdf":
        return False
    try:
        from backend.services.rag.index_store import IndexStore
        store = IndexStore()
        indexed_file = store.get(str(file_path))
        return indexed_file is not None and len(indexed_file.chunk_ids) > 0
    except Exception as e:
        logger.debug(f"IndexStore check failed for {file_path}: {e}")
        return False


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

        item_names = []
        for item in items:
            name = item.name
            if item.is_file() and item.suffix.lower() == ".pdf":
                if _is_pdf_indexed(item):
                    name = f"{name} [INDIZIERT]"
            item_names.append(f"{name}{'/' if item.is_dir() else ''}")

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


_ALL_DRIVES_EXCLUDE_DIRS = {
    # Windows-System / Noise-Ordner — nie durchsuchen
    "$recycle.bin", "system volume information", "windows", "windows.old",
    "program files", "program files (x86)", "programdata",
    "msocache", "recovery", "perflogs",
    # Entwickler-Noise
    "node_modules", ".git", ".venv", "venv", "__pycache__", ".cache",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", "dist", "build",
    # Browser-Caches & AppData-Untermengen (zu groß, irrelevant)
    "appdata",
}


def _enumerate_local_drives() -> list[Path]:
    """Liefert vorhandene lokale Windows-Laufwerke (C:\\, D:\\, ...)."""
    import string
    drives: list[Path] = []
    for letter in string.ascii_uppercase:
        drive = Path(f"{letter}:\\")
        try:
            if drive.exists():
                drives.append(drive)
        except OSError:
            continue
    return drives


def find_files(
    pattern: str,
    root: Optional[str] = None,
    max_results: int = 20,
    search_all_drives: bool = False,
    recursive: bool = True,
) -> ToolResultV1:
    """Rekursive Dateisuche über alle freigegebenen Workspaces (oder einen spezifischen Root).

    Args:
        pattern: Glob-Muster (z.B. '*.pdf', '*gundula*', 'gundula1.pdf'). Nur Dateinamen, keine Pfadsegmente.
                 Wenn das Pattern weder '*' noch '?' enthält, wird es als '*<pattern>*' (Substring-Suche) interpretiert.
        root:    Optional: Workspace-relativer oder absoluter Pfad als Startordner. None → ALLE Workspaces.
        max_results: Harte Obergrenze für Treffer (Default 20 — begrenzt Fakten-Extraktion-Overhead nach Dateisuchen).
        search_all_drives: Wenn True, werden ALLE lokalen Windows-Laufwerke (C:\\, D:\\, ...) durchsucht
                           — unabhängig von Workspaces. Dauert länger, findet aber Duplikate überall.
                           System-/Noise-Ordner (Windows, Program Files, node_modules, .git, ...) werden übersprungen.
        recursive: Wenn False, wird nur das angegebene Verzeichnis durchsucht, nicht die Unterordner.
                   (Default True für Kompatibilität mit bestehendem Verhalten).

    Returns:
        ToolResultV1 mit data.matches (Liste von absoluten Pfaden) und data.count.
    """
    started = time.perf_counter()
    try:
        if not pattern or not str(pattern).strip():
            return _fs_err("INVALID_ARGUMENT", "Fehler: 'pattern' darf nicht leer sein.", started=started)

        _validate_glob_pattern(pattern)
        if _is_sensitive_filesystem_target(pattern):
            return _fs_err(
                "SENSITIVE_FILE_BLOCKED",
                "Fehler: Sicherheitsrelevante Dateien wie .env, Secrets, Tokens oder Credentials duerfen nicht gesucht oder aufgelistet werden.",
                started=started,
            )
        # Pfadsegmente im Pattern verbieten (Suche nur nach Dateinamen):
        if "/" in pattern or "\\" in pattern:
            return _fs_err(
                "INVALID_ARGUMENT",
                "Fehler: 'pattern' darf keine Pfadsegmente enthalten — nur Dateinamen-Glob (z.B. '*.pdf').",
                started=started,
            )

        # Fuzzy-Fallback: Wenn kein Glob-Zeichen vorhanden → Substring-Suche
        effective_pattern = pattern
        if "*" not in pattern and "?" not in pattern:
            effective_pattern = f"*{pattern}*"

        try:
            max_results_int = max(1, min(int(max_results), 1000))
        except Exception:
            max_results_int = 100

        import fnmatch
        import os as _os

        def _walk_onerror(err: OSError) -> None:
            logger.debug("find_files: Überspringe unerreichbaren Pfad (%s)", err)

        def _sweep(sweep_roots: list[Path], apply_exclude: bool, current_matches: list[str], recursive: bool = True) -> bool:
            """Durchsucht sweep_roots rekursiv oder nicht-rekursiv, appendet an current_matches. Returns True wenn truncated."""
            existing = set(current_matches)
            for ws_root in sweep_roots:
                if not ws_root.is_dir():
                    continue
                if str(ws_root) not in searched_roots:
                    searched_roots.append(str(ws_root))
                for dirpath, dirnames, filenames in _os.walk(str(ws_root), onerror=_walk_onerror):
                    if apply_exclude:
                        dirnames[:] = [d for d in dirnames if d.lower() not in _ALL_DRIVES_EXCLUDE_DIRS]
                    # 💎 TASK-005: BACKLOG-005 - Nicht-rekursive Suche
                    # Wenn recursive=False, leere dirnames, um Unterordner zu überspringen
                    if not recursive:
                        dirnames[:] = []
                    for fname in fnmatch.filter(filenames, effective_pattern):
                        full = _os.path.join(dirpath, fname)
                        if full in existing:
                            continue
                        existing.add(full)
                        current_matches.append(full)
                        if len(current_matches) >= max_results_int:
                            return True
            return False

        matches: list[str] = []
        searched_roots: list[str] = []
        auto_escalated = False
        explicit_root = bool(root and str(root).strip() and str(root).strip() not in (".", "/"))
        explicit_all_drives = bool(search_all_drives)

        # 💎 TASK-005: BACKLOG-005 - Heuristik für nicht-rekursive Suche
        # Wenn ein expliziter Root angegeben ist, setze recursive=False standardmäßig
        # um unnötige Unterordner-Scans zu vermeiden (z.B. "vom Desktop", "in diesem Ordner")
        if explicit_root and recursive:
            recursive = False
            logger.info(f"[find_files] Expliziter Root '{root}' erkannt, deaktiviere rekursive Suche für Performance.")

        # --- Phase 1: primärer Sweep ---
        if explicit_root:
            primary_roots = [_resolve_and_validate_path(str(root), must_exist=True)]
            truncated = _sweep(primary_roots, apply_exclude=False, current_matches=matches, recursive=recursive)
        elif explicit_all_drives:
            primary_roots = _enumerate_local_drives()
            truncated = _sweep(primary_roots, apply_exclude=True, current_matches=matches, recursive=recursive)
        else:
            # Default: Workspaces
            primary_roots = _get_allowed_workspaces()
            truncated = _sweep(primary_roots, apply_exclude=False, current_matches=matches, recursive=recursive)

            # --- Phase 2: Auto-Escalation bei ≤1 Treffer ---
            # Wenn Workspace-Suche wenig Erfolg hatte, erweitere auf alle Laufwerke,
            # um mögliche Duplikate/weitere Instanzen zu finden.
            if not truncated and len(matches) <= 1:
                auto_escalated = True
                all_drives = _enumerate_local_drives()
                # Laufwerke skippen, deren Workspace-Roots schon gescannt wurden?
                # Nein — wir müssen andere Pfade auf demselben Drive auch abdecken.
                # Dedupe läuft über existing-Set in _sweep.
                truncated = _sweep(all_drives, apply_exclude=True, current_matches=matches, recursive=recursive)

        if matches:
            preview = "\n".join(matches[:25])
            extra = f"\n... (+{len(matches) - 25} weitere)" if len(matches) > 25 else ""
            escalation_note = " (globale Suche auf allen Laufwerken aktiviert)" if auto_escalated else ""
            out = f"{len(matches)} Treffer für '{pattern}'{escalation_note}:\n{preview}{extra}"
        else:
            out = (
                f"Keine Datei passend zu '{pattern}' gefunden (durchsuchte Roots: {len(searched_roots)})."
            )

        return _fs_ok(
            {
                "output": out,
                "pattern": pattern,
                "effective_pattern": effective_pattern,
                "matches": matches,
                "count": len(matches),
                "searched_roots": searched_roots,
                "truncated": truncated,
                "auto_escalated": auto_escalated,
            },
            message=out,
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


def move_files(source_directory: str, destination_directory: str, file_names: list[str]) -> ToolResultV1:
    started = time.perf_counter()
    try:
        safe_source_dir = _resolve_and_validate_path(source_directory, must_exist=True)
        safe_dest_dir = _resolve_and_validate_path(destination_directory, must_exist=False)

        if not safe_dest_dir.exists():
            safe_dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Zielordner '{destination_directory}' wurde erstellt.")

        files_to_move: list[Path] = []
        for name in file_names:
            file_path = safe_source_dir / name
            if file_path.is_file():
                files_to_move.append(file_path)

        if not files_to_move:
            out = f"Keine der angegebenen Dateien in '{source_directory}' gefunden."
            return _fs_ok(
                {"output": out, "moved_count": 0, "error_count": 0, "items": []},
                message=out,
                started=started,
            )

        moved_count = 0
        errors: list[str] = []
        moved_files: list[str] = []
        for file_path in files_to_move:
            try:
                shutil.move(str(file_path), str(safe_dest_dir))
                moved_count += 1
                moved_files.append(str(file_path))
            except Exception as e:
                errors.append(f"Konnte '{file_path.name}' nicht verschieben: {e}")

        logger.info(
            f"{moved_count} Dateien nach '{safe_dest_dir}' verschoben."
        )

        if errors:
            error_details = "\n".join(errors)
            output = (
                f"{moved_count} von {len(files_to_move)} Dateien erfolgreich verschoben. Fehler:\n"
                f"{error_details}"
            )
        else:
            # 💎 TASK-005: BACKLOG-005 - Detaillierte Ausgabe für verschobene Dateien
            # Zeige die verschobenen Dateien mit ihren Pfaden an
            moved_files_output = "\n".join(moved_files)
            output = (
                f"Alle {moved_count} Dateien wurden erfolgreich nach "
                f"'{destination_directory}' verschoben:\n{moved_files_output}"
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
