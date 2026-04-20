from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class CreatePdfRenderer(BaseRenderer):
    skill_id = "system.create_pdf"

    def render(self, data: dict) -> str:
        file_path = str(data.get("file_path") or "").strip()
        preview_url = str(data.get("preview_url") or "").strip()

        if file_path:
            return "\n".join(
                [
                    "**PDF erfolgreich erstellt**",
                    "",
                    f"- **Datei:** `{file_path}`",
                ]
            )

        if preview_url:
            preview_label = "PDF-Vorschau erzeugt"
            preview_note = "Die Vorschau wurde erfolgreich im Dry-Run-Modus erstellt."
            return "\n".join(
                [
                    f"**{preview_label}**",
                    "",
                    f"- **Status:** {preview_note}",
                    f"- **Preview-URL:** `{preview_url[:80]}{'...' if len(preview_url) > 80 else ''}`",
                ]
            )

        return "PDF-Daten konnten nicht aufbereitet werden."


register_renderer(CreatePdfRenderer())
