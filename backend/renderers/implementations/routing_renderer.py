"""Deterministic Renderer for ``system.routing`` (Diamond Standard).

Converts routing tool-result data into a human-readable Markdown answer
including origin, destination, distance, duration, and Google Maps link.
"""

from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class RoutingRenderer(BaseRenderer):
    """Render a single routing result deterministically."""

    skill_id = "system.routing"

    def render(self, data: dict) -> str:
        origin = data.get("origin", "Unbekannt")
        destination = data.get("destination", "Unbekannt")
        distance_km = data.get("distance_km")
        duration = data.get("duration", "Dauer unbekannt")
        maps_link = data.get("maps_link", "")

        distance_str = f"{distance_km} km" if distance_km is not None else "Distanz unbekannt"

        lines = [
            f"**Route: {origin} → {destination}**",
            "",
            f"- **Distanz:** {distance_str}",
            f"- **Fahrzeit:** {duration}",
        ]

        if maps_link:
            lines.append(f"- **Google Maps:** [Route anzeigen]({maps_link})")

        return "\n".join(lines)


# Auto-register on import
register_renderer(RoutingRenderer())
