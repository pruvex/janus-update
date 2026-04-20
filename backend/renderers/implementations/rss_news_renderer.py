from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class RssNewsRenderer(BaseRenderer):
    skill_id = "system.rss_news"

    def render(self, data: dict) -> str:
        source = str(data.get("source") or "unbekannt").strip()
        count = data.get("count")
        headlines = data.get("headlines") if isinstance(data.get("headlines"), list) else []

        if not headlines:
            return f"Ich konnte aktuell keine Schlagzeilen von {source} aufbereiten."

        lines = [f"**Aktuelle Schlagzeilen von {source}**", ""]
        for idx, headline in enumerate(headlines, start=1):
            text = str(headline or "Ohne Titel").strip() or "Ohne Titel"
            lines.append(f"{idx}. {text}")
        if isinstance(count, int):
            lines.append("")
            lines.append(f"- **Anzahl:** {count}")
        return "\n".join(lines)


register_renderer(RssNewsRenderer())
