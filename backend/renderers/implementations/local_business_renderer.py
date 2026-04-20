from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class LocalBusinessRenderer(BaseRenderer):
    skill_id = "system.local_business"

    def render(self, data: dict) -> str:
        if not data:
            return "Ich konnte keine passenden Ergebnisse finden."

        items = data if isinstance(data, list) else data.get("businesses", [])
        if not isinstance(items, list) or len(items) == 0:
            return "Ich konnte keine passenden Ergebnisse finden."

        lines = ["**Gefundene lokale Ergebnisse**", ""]
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "Unbekannter Eintrag").strip()
            address = str(item.get("address") or "Adresse nicht gefunden").strip()
            phone = str(item.get("phone") or "").strip()
            website = str(item.get("website") or "").strip()
            lines.append(f"**{name}**")
            lines.append(f"Adresse: {address}")
            if phone:
                lines.append(f"Telefon: {phone}")
            if website:
                lines.append(f"Website: {website}")
            lines.append("")

        rendered = "\n".join(lines).strip()
        return rendered or "Ich konnte keine passenden Ergebnisse finden."


register_renderer(LocalBusinessRenderer())
