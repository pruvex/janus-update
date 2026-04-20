import logging
import time
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.services.policy_engine import PolicyEngine
from backend.services.skill_router import SkillNotFoundError, skill_router
from backend.services.tool_manager import tool_manager

logger = logging.getLogger("janus_backend")


def _resolve_permission_target(skill_id: Optional[str] = None, tool_name: Optional[str] = None) -> Tuple[str, Optional[str]]:
    requested = str(skill_id or tool_name or "").strip()
    if not requested:
        raise ValueError("Es wurde keine Skill-ID angegeben.")

    try:
        resolved_name = skill_router.resolve_tool_name(requested)
    except SkillNotFoundError as exc:
        raise ValueError(str(exc)) from exc

    canonical_skill_id = tool_manager.get_skill_id(resolved_name)
    if not str(canonical_skill_id or "").strip():
        raise ValueError(f"Skill '{requested}' ist nicht registriert.")
    return str(canonical_skill_id), (None if requested == canonical_skill_id else requested)


def _perm_meta(started_at: float) -> Dict[str, Any]:
    return {"execution_time_ms": round((time.perf_counter() - started_at) * 1000.0, 3)}


def grant_permission(skill_id: Optional[str] = None, tool_name: Optional[str] = None, db: Optional[Session] = None) -> ToolResultV1:
    started_at = time.perf_counter()

    try:
        canonical_skill_id, resolved_from = _resolve_permission_target(skill_id=skill_id, tool_name=tool_name)
        allowed, reason = PolicyEngine.can_persist_permission(canonical_skill_id)
        if not allowed:
            msg = f"Für '{canonical_skill_id}' darf keine dauerhafte Freigabe gespeichert werden."
            return ToolResultV1(
                status="error",
                data={},
                message=msg,
                error=ToolErrorDetails(
                    code="PERMISSION_GRANT_NOT_ALLOWED",
                    message=msg,
                    details={"skill_id": canonical_skill_id, "reason": reason},
                ),
                metadata=_perm_meta(started_at),
            )

        already_present = PolicyEngine.has_permanent_permission(canonical_skill_id, db)
        PolicyEngine.grant_permanent_permission(canonical_skill_id, db)
        msg = f"Dauerhafte Freigabe für '{canonical_skill_id}' gespeichert."
        return ToolResultV1(
            status="ok",
            data={
                "skill_id": canonical_skill_id,
                "action": "granted",
                "permission_state": "always_allow",
                "already_present": already_present,
                "resolved_from": resolved_from,
            },
            message=msg,
            metadata=_perm_meta(started_at),
        )
    except ValueError as exc:
        msg = str(exc)
        return ToolResultV1(
            status="error",
            data={},
            message=msg,
            error=ToolErrorDetails(
                code="SKILL_NOT_FOUND",
                message=msg,
                details={"skill_id": str(skill_id or tool_name or "").strip()},
            ),
            metadata=_perm_meta(started_at),
        )
    except Exception as exc:
        logger.error("Fehler beim Speichern der Policy-Entscheidung", exc_info=exc)
        msg = "Fehler beim Speichern der Berechtigung."
        return ToolResultV1(
            status="error",
            data={},
            message=msg,
            error=ToolErrorDetails(
                code="PERMISSION_GRANT_FAILED",
                message=msg,
                details={"error": str(exc), "skill_id": str(skill_id or tool_name or "").strip()},
            ),
            metadata=_perm_meta(started_at),
        )


def revoke_permission(skill_id: Optional[str] = None, tool_name: Optional[str] = None, db: Optional[Session] = None) -> ToolResultV1:
    started_at = time.perf_counter()

    try:
        canonical_skill_id, resolved_from = _resolve_permission_target(skill_id=skill_id, tool_name=tool_name)
        removed = PolicyEngine.revoke_permanent_permission(canonical_skill_id, db)
        msg = f"Freigabe für '{canonical_skill_id}' widerrufen."
        return ToolResultV1(
            status="ok",
            data={
                "skill_id": canonical_skill_id,
                "action": "revoked",
                "permission_state": "requires_consent",
                "removed": bool(removed),
                "resolved_from": resolved_from,
            },
            message=msg,
            metadata=_perm_meta(started_at),
        )
    except ValueError as exc:
        msg = str(exc)
        return ToolResultV1(
            status="error",
            data={},
            message=msg,
            error=ToolErrorDetails(
                code="SKILL_NOT_FOUND",
                message=msg,
                details={"skill_id": str(skill_id or tool_name or "").strip()},
            ),
            metadata=_perm_meta(started_at),
        )
    except Exception as exc:
        logger.error("Fehler beim Widerruf der Policy-Entscheidung", exc_info=exc)
        msg = "Fehler beim Widerruf der Berechtigung."
        return ToolResultV1(
            status="error",
            data={},
            message=msg,
            error=ToolErrorDetails(
                code="PERMISSION_REVOKE_FAILED",
                message=msg,
                details={"error": str(exc), "skill_id": str(skill_id or tool_name or "").strip()},
            ),
            metadata=_perm_meta(started_at),
        )
