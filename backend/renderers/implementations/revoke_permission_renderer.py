from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class RevokePermissionRenderer(BaseRenderer):
    skill_id = "system.revoke_permission"

    def render(self, data: dict) -> str:
        skill_id = str(data.get("skill_id") or "Unbekannter Skill").strip()
        action = str(data.get("action") or "revoked").strip()
        permission_state = str(data.get("permission_state") or "requires_consent").strip()
        removed = bool(data.get("removed", False))

        status_text = "wurde widerrufen" if removed else "war nicht dauerhaft gesetzt"

        return "\n".join(
            [
                "**Freigabe widerrufen**",
                "",
                f"- **Skill:** `{skill_id}`",
                f"- **Aktion:** {action}",
                f"- **Status:** Die Freigabe {status_text}.",
                f"- **Berechtigung:** {permission_state}",
            ]
        )


register_renderer(RevokePermissionRenderer())
