import os
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.data.schemas_tools import ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

logger = logging.getLogger("janus_backend")


async def hardened_edit_pdf(
    original_filename: str,
    modifications: List[Dict[str, str]],
    backup_directory: str = "backups",
    call_internal_skill: Optional[Callable[..., Any]] = None,
    **_kwargs,
) -> ToolResultV1:
    """Composite skill: backup first, then execute hardened PDF edit as one atomic operation."""
    started = time.perf_counter()
    tags = ["knowledge", "composite"]
    try:
        source_path = str(original_filename or "").strip()
        if not source_path:
            return tool_err_v1(
                "INVALID_ARGUMENTS",
                "original_filename darf nicht leer sein.",
                tags=tags,
                started_at=started,
            )

        if not callable(call_internal_skill):
            return tool_err_v1(
                "OPERATION_FAILED",
                "Composite-Context fehlt: call_internal_skill ist nicht verfuegbar.",
                tags=tags,
                started_at=started,
            )

        safe_backup_dir = str(backup_directory or "backups").strip() or "backups"
        safe_backup_dir = safe_backup_dir.replace("\\", "/").strip("/") or "backups"

        file_name = Path(source_path).name
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{safe_backup_dir}/{file_name}.{stamp}.bak"

        mkdir_result = await call_internal_skill(
            "filesystem.create_directory",
            {"path": safe_backup_dir},
        )
        if str(mkdir_result.get("status") or "") != "ok":
            return tool_err_v1(
                "COMPOSITE_STAGE_FAILED",
                "Backup-Ordner konnte nicht erstellt werden.",
                details={"stage": "create_directory", "result": mkdir_result},
                tags=tags,
                started_at=started,
            )

        move_result = await call_internal_skill(
            "filesystem.move_file",
            {"source_path": source_path, "destination_path": backup_path},
        )
        if str(move_result.get("status") or "") != "ok":
            return tool_err_v1(
                "COMPOSITE_STAGE_FAILED",
                "Backup-Move konnte nicht ausgefuehrt werden.",
                details={"stage": "move_backup", "result": move_result},
                tags=tags,
                started_at=started,
            )

        try:
            os.makedirs(os.path.dirname(source_path) or ".", exist_ok=True)
            shutil.copy2(backup_path, source_path)
        except Exception as exc:
            rollback_result = await call_internal_skill(
                "filesystem.move_file",
                {"source_path": backup_path, "destination_path": source_path},
            )
            return tool_err_v1(
                "COMPOSITE_STAGE_FAILED",
                "Original konnte nach Backup nicht wiederhergestellt werden.",
                details={
                    "stage": "restore_original",
                    "exception": str(exc),
                    "rollback": rollback_result,
                },
                tags=tags,
                started_at=started,
            )

        edit_result = await call_internal_skill(
            "knowledge.edit_pdf",
            {
                "original_filename": source_path,
                "modifications": modifications or [],
            },
        )
        if str(edit_result.get("status") or "") != "ok":
            return tool_err_v1(
                "COMPOSITE_STAGE_FAILED",
                "Der sichere PDF-Edit ist fehlgeschlagen.",
                details={
                    "stage": "knowledge.edit_pdf",
                    "backup_path": backup_path,
                    "result": edit_result,
                },
                tags=tags,
                started_at=started,
            )

        data = {
            "operation": "knowledge.hardened_edit",
            "backup_path": backup_path,
            "source_path": source_path,
            "edit_result": edit_result.get("data", edit_result),
        }
        return tool_ok_v1(
            data,
            message="Sicherer PDF-Edit mit Backup abgeschlossen.",
            tags=tags,
            started_at=started,
        )
    except Exception as e:
        logger.error("hardened_edit_pdf: %s", e, exc_info=True)
        return tool_err_v1("OPERATION_FAILED", str(e), tags=tags, started_at=started)
