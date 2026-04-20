from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class SaveMp3Renderer(BaseRenderer):
    skill_id = "system.save_mp3"

    def render(self, data: dict) -> str:
        file_path = str(data.get("file_path") or "").strip()
        filename = str(data.get("filename") or "audio.mp3").strip() or "audio.mp3"

        if file_path:
            return "\n".join(
                [
                    "**MP3 erfolgreich gespeichert**",
                    "",
                    f"- **Datei:** `{filename}`",
                    f"- **Pfad:** `{file_path}`",
                ]
            )

        return "\n".join(
            [
                "**MP3 erfolgreich gespeichert**",
                "",
                f"- **Datei:** `{filename}`",
            ]
        )


register_renderer(SaveMp3Renderer())
