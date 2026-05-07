"""Deterministic Renderer for ``system.weather`` (Diamond Standard).

Converts weather tool-result data into a human-readable Markdown answer
including city, date, temperature range, precipitation, wind, and source.
"""

from backend.renderers.attribution import append_quelle_line, weather_source_label
from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class WeatherRenderer(BaseRenderer):
    """Render a weather forecast result deterministically."""

    skill_id = "system.weather"

    def render(self, data: dict) -> str:
        # The weather handler already builds a human-readable 'forecast' string.
        # If present, use it as the primary output and enrich with structured data.
        forecast = data.get("forecast", "")
        city = data.get("city", "Unbekannt")
        source = data.get("source", "")

        # If the handler already provided a full forecast sentence, return it
        # enriched with source attribution.
        if forecast and len(forecast) > 20:
            lines = [f"**Wetter in {city}**", "", forecast]
            body = "\n".join(lines)
            q = weather_source_label(source)
            # Tool payload already appends „Quelle:“ (weather_service) — nicht doppeln.
            if q and "quelle:" not in forecast.lower():
                return append_quelle_line(body, q)
            return body

        # Fallback: build from structured fields if forecast string is missing
        date = data.get("date", "heute")
        temp_max = data.get("temp_max")
        temp_min = data.get("temp_min")
        precipitation = data.get("precipitation_probability")
        wind_speed = data.get("wind_speed_max")
        weather_desc = data.get("weather_description", "")

        lines = [f"**Wetter in {city} am {date}**", ""]

        if weather_desc:
            lines.append(f"- **Wetterlage:** {weather_desc}")
        if temp_max is not None and temp_min is not None:
            lines.append(f"- **Temperatur:** {temp_min}°C bis {temp_max}°C")
        elif temp_max is not None:
            lines.append(f"- **Höchsttemperatur:** {temp_max}°C")
        if precipitation is not None:
            lines.append(f"- **Niederschlag:** {precipitation}%")
        if wind_speed is not None:
            lines.append(f"- **Windböen:** bis {wind_speed} km/h")
        body = "\n".join(lines)
        q = weather_source_label(source)
        return append_quelle_line(body, q) if q else body


# Auto-register on import
register_renderer(WeatherRenderer())
