from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class ScrapeWebsiteRenderer(BaseRenderer):
    skill_id = "system.scrape_website"

    def render(self, data: dict) -> str:
        url = str(data.get("url") or "Unbekannte URL").strip()
        content = str(data.get("content") or "").strip()
        char_count = data.get("char_count")

        title = "Unbekannter Titel"
        if content:
            first_line = content.splitlines()[0].strip()
            if first_line.lower().startswith("titel:"):
                extracted = first_line.split(":", 1)[1].strip()
                if extracted:
                    title = extracted
            elif first_line:
                title = first_line[:120]

        if not isinstance(char_count, int):
            char_count = len(content) if content else 0

        lines = [
            "**Executive Summary: Website-Inhalt bereit**",
            "",
            f"- **URL:** `{url}`",
            f"- **Titel:** {title}",
            f"- **Länge:** {char_count} Zeichen",
        ]

        if content:
            lines.append(f"- **Vorschau:** {content[:140].replace(chr(10), ' ')}")

        return "\n".join(lines)


register_renderer(ScrapeWebsiteRenderer())
