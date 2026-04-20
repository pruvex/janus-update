import logging
from sqlalchemy.orm import Session

from backend.data.models import AppState
from backend.services.skill_router import SkillNotFoundError, skill_router
from backend.services.tool_manager import tool_manager

logger = logging.getLogger("janus_backend")

# Basis-Risiko-Matrix aus Phase A (Auszug für die wichtigsten)
RISK_MATRIX = {
    "delete_file": "restricted",
    "delete_directory": "restricted",
    "send_email": "confirm_required",
    "create_file": "confirm_required",
    "edit_pdf_text_in_place": "confirm_required",
    "knowledge.edit_pdf": "confirm_required",
    "knowledge.hardened_edit": "confirm_required",
}

NON_GRANTABLE_SKILLS = {
    "system.grant_permission",
    "system.revoke_permission",
}


class PolicyEngine:
    @staticmethod
    def normalize_permission_target(tool_name: str) -> str:
        requested = str(tool_name or "").strip()
        if not requested:
            return ""

        try:
            resolved_name = skill_router.resolve_tool_name(requested)
        except SkillNotFoundError:
            resolved_name = requested

        return str(tool_manager.get_skill_id(resolved_name) or resolved_name)

    @staticmethod
    def evaluate(tool_name: str, db: Session) -> str:
        """Prüft die Berechtigung. Returnt: 'ALLOW', 'DENY' oder 'REQUIRE_CONSENT'."""
        normalized_name = PolicyEngine.normalize_permission_target(tool_name)
        risk_level = RISK_MATRIX.get(normalized_name, RISK_MATRIX.get(tool_name, "read_only"))

        if risk_level == "read_only":
            return "ALLOW"

        state_key = f"permission:{normalized_name}"
        saved_state = None
        if db:
            saved_state = db.query(AppState).filter(AppState.key == state_key).first()

        if saved_state and saved_state.value == "always_allow":
            logger.info(f"POLICY: Tool '{normalized_name}' via 'always_allow' freigegeben.")
            return "ALLOW"

        return "REQUIRE_CONSENT"

    @staticmethod
    def can_persist_permission(tool_name: str):
        normalized_name = PolicyEngine.normalize_permission_target(tool_name)
        if not normalized_name:
            return False, "missing_skill_id"
        if normalized_name in NON_GRANTABLE_SKILLS:
            return False, "meta_skill_blocked"
        return True, "allowed"

    @staticmethod
    def has_permanent_permission(tool_name: str, db: Session) -> bool:
        if not db:
            return False
        normalized_name = PolicyEngine.normalize_permission_target(tool_name)
        state_key = f"permission:{normalized_name}"
        existing = db.query(AppState).filter(AppState.key == state_key).first()
        return bool(existing and existing.value == "always_allow")

    @staticmethod
    def grant_permanent_permission(tool_name: str, db: Session):
        """Speichert die 'Immer erlauben' Entscheidung."""
        normalized_name = PolicyEngine.normalize_permission_target(tool_name)
        state_key = f"permission:{normalized_name}"
        existing = db.query(AppState).filter(AppState.key == state_key).first()
        if existing:
            existing.value = "always_allow"
        else:
            new_state = AppState(key=state_key, value="always_allow")
            db.add(new_state)
        db.commit()
        logger.info(f"POLICY: 'Immer erlauben' für '{normalized_name}' gespeichert.")

    @staticmethod
    def revoke_permanent_permission(tool_name: str, db: Session):
        normalized_name = PolicyEngine.normalize_permission_target(tool_name)
        state_key = f"permission:{normalized_name}"
        existing = db.query(AppState).filter(AppState.key == state_key).first()
        if existing:
            db.delete(existing)
            db.commit()
            logger.info(f"POLICY: Erlaubnis für '{normalized_name}' WIDERRUFEN.")
            return True
        return False
