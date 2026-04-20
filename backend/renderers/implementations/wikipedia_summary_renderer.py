from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class WikipediaSummaryRenderer(BaseRenderer):
    skill_id = "system.wikipedia_summary"

    def render(self, data: dict) -> str:
        title = str(data.get("title") or "Unbekannter Artikel").strip()
        summary = str(data.get("summary") or "").strip()
        url = str(data.get("url") or "").strip()

        lines = [
            "**Executive Summary: Wikipedia-Daten bereit**",
            "",
            f"- **Titel:** {title}",
            f"- **Zusammenfassungslänge:** {len(summary)} Zeichen",
        ]

        if url:
            lines.append(f"- **URL:** `{url}`")
        if summary:
            lines.append(f"- **Vorschau:** {summary[:160].replace(chr(10), ' ')}")

        return "\n".join(lines)


register_renderer(WikipediaSummaryRenderer())
