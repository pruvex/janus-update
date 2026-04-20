from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class WebsearchRenderer(BaseRenderer):
    skill_id = "system.websearch"

    def render(self, data: dict) -> str:
        text = str(data.get("text") or "").strip()
        if text:
            # Cloud-Modelle liefern bereits fertige Antworten mit Zitaten.
            return text

        source = str(data.get("source") or "unbekannt").strip()
        urls = data.get("urls") if isinstance(data.get("urls"), list) else []

        lines = [
            "**Executive Summary: Websuche bereit**",
            "",
            f"- **Quelle:** {source}",
            f"- **Treffer-URLs:** {len(urls)}",
            "- **Text:** keine Cloud-Antwort verfügbar",
        ]

        if urls:
            lines.append("- **Top-URLs:**")
            for url in urls[:5]:
                value = str(url or "").strip()
                if value:
                    lines.append(f"  - `{value}`")

        return "\n".join(lines)


register_renderer(WebsearchRenderer())
