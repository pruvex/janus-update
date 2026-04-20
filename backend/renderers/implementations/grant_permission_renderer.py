from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class GrantPermissionRenderer(BaseRenderer):
    skill_id = "system.grant_permission"

    def render(self, data: dict) -> str:
        skill_id = str(data.get("skill_id") or "Unbekannter Skill").strip()
        action = str(data.get("action") or "granted").strip()
        permission_state = str(data.get("permission_state") or "always_allow").strip()
        already_present = bool(data.get("already_present", False))

        status_text = "war bereits freigegeben" if already_present else "wurde dauerhaft freigegeben"

        lines = [
            "**Freigabe aktualisiert**",
            "",
            f"- **Skill:** `{skill_id}`",
            f"- **Aktion:** {action}",
            f"- **Status:** Der Skill {status_text}.",
            f"- **Berechtigung:** {permission_state}",
        ]

        return "\n".join(lines)


register_renderer(GrantPermissionRenderer())
