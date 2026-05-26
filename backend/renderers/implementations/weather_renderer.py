"""Deterministic renderer for ``system.weather``."""

from backend.renderers.attribution import append_quelle_line, weather_source_label
from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer


class WeatherRenderer(BaseRenderer):
    """Render a weather forecast result deterministically."""

    skill_id = "system.weather"

    @staticmethod
    def _format_value(value) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, float):
            return f"{value:.1f}"
        return str(value)

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

        # Prefer structured weather fields when available to keep provider output uniform.
        if any(v is not None for v in (temp_max, temp_min, precipitation, wind_speed)) or weather_desc:
            lines = [f"Das Wetter fuer {city} ({date}) im Ueberblick:"]
            if weather_desc:
                lines.append(f"* Zustand: {weather_desc}")
            if temp_max is not None and temp_min is not None:
                lines.append(
                    f"* Temperaturen: Hoechstwerte bis zu {self._format_value(temp_max)} C, "
                    f"Tiefstwerte bei {self._format_value(temp_min)} C"
                )
            elif temp_max is not None:
                lines.append(f"* Temperaturen: Hoechstwerte bis zu {self._format_value(temp_max)} C")
            if precipitation is not None:
                lines.append(f"* Regen: Die Niederschlagswahrscheinlichkeit liegt bei {self._format_value(precipitation)} %")
            if wind_speed is not None:
                lines.append(f"* Wind: Leichte Brisen mit Boeen bis zu {self._format_value(wind_speed)} km/h")
            body = "\n".join(lines)
            q = weather_source_label(source)
            return append_quelle_line(body, q) if q else body

        if forecast and len(str(forecast)) > 0:
            lines = [f"Wetter in {city}:", str(forecast)]
            body = "\n".join(lines)
            q = weather_source_label(source)
            if q and "quelle:" not in str(forecast).lower():
                return append_quelle_line(body, q)
            return body

        lines = [f"Wetter in {city}."]
        body = "\n".join(lines)
        q = weather_source_label(source)
        return append_quelle_line(body, q) if q else body


register_renderer(WeatherRenderer())
