"""Deterministic Renderer for ``system.weather`` (Diamond Standard)."""

from backend.renderers.attribution import append_quelle_line, weather_source_label
from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class WeatherRenderer(BaseRenderer):
    """Render a weather forecast result deterministically."""

    skill_id = "system.weather"

    def render(self, data: dict) -> str:
        forecast = data.get("forecast", "")
        city = data.get("city", "Unbekannt")
        source = data.get("source", "")

        date = data.get("date", "heute")
        temp_max = data.get("temp_max")
        temp_min = data.get("temp_min")
        precipitation = data.get("precipitation_probability")
        wind_speed = data.get("wind_speed_max")
        weather_desc = data.get("weather_description", "")

        # Preferred deterministic layout for structured weather data.
        if any(v is not None for v in (temp_max, temp_min, precipitation, wind_speed)) or weather_desc:
            lines = [f"Hallo! Heute in {city} ({date}) erwartet dich folgendes Wetter:", ""]
            if weather_desc:
                lines.append(f"* Zustand: {weather_desc}.")
            if temp_max is not None and temp_min is not None:
                lines.append(f"* Temperatur: Max. {temp_max} °C, Min. {temp_min} °C.")
            elif temp_max is not None:
                lines.append(f"* Temperatur: Max. {temp_max} °C.")
            if precipitation is not None:
                lines.append(f"* Regen: {precipitation} % Niederschlagswahrscheinlichkeit.")
            if wind_speed is not None:
                lines.append(f"* Wind: Böen bis {wind_speed} km/h.")
            body = "\n".join(lines)
            q = weather_source_label(source)
            return append_quelle_line(body, q) if q else body

        # Last-resort fallback for unstructured providers (e.g. wttr.in short text).
        lines = [f"**Wetter in {city}**"]
        if forecast:
            lines.extend(["", str(forecast)])
        body = "\n".join(lines)
        q = weather_source_label(source)
        return append_quelle_line(body, q) if q else body


register_renderer(WeatherRenderer())
