from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class GenerateImageRenderer(BaseRenderer):
    skill_id = "system.generate_image"

    def render(self, data: dict) -> str:
        message = str(data.get("message") or "Bild erfolgreich generiert.").strip()
        local_image_path = str(data.get("local_image_path") or "").strip()
        image_url = str(data.get("image_url") or "").strip()
        prompt_used = str(data.get("prompt_used") or "").strip()
        cost = data.get("cost")

        lines = [
            "**Bild erfolgreich generiert**",
            "",
            f"- **Status:** {message}",
        ]

        if prompt_used:
            lines.append(f"- **Prompt:** {prompt_used}")
        if local_image_path:
            lines.append(f"- **Datei:** `{local_image_path}`")
        elif image_url:
            lines.append(f"- **Bildpfad:** `{image_url}`")
        if image_url:
            lines.append(f"- **Bild-URL:** `{image_url}`")
        if isinstance(cost, (int, float)):
            lines.append(f"- **Kosten:** {cost:.2f}")

        return "\n".join(lines)


register_renderer(GenerateImageRenderer())
