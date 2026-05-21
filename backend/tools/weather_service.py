import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import dateparser
import requests
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.renderers.attribution import append_quelle_line, weather_source_label

logger = logging.getLogger("janus_backend")


class CleanGetWeatherFromApiToolArgs(BaseModel):
    city: str = Field(
        ...,
        description=(
            "Stadt oder Ort für die Vorhersage, nur der Ortsname aus der Nutzeranfrage "
            "(z.B. 'Berlin', 'München Schwabing'). Keine Zusätze wie 'Wetter' oder 'bitte'."
        ),
    )
    date_str: Optional[str] = Field(
        None,
        description=(
            "Bezugsdatum in natürlicher Sprache, z.B. 'heute', 'morgen', 'Samstag', '15. April'. "
            "Leer lassen für die Vorhersage für heute."
        ),
    )


def _get_weather_code_description(code: int) -> str:
    weather_codes = {
        0: "Klarer Himmel",
        1: "Leicht bewölkt",
        2: "Teils bewölkt",
        3: "Bedeckt",
        45: "Nebel",
        48: "Raureifnebel",
        51: "Leichter Nieselregen",
        53: "Mäßiger Nieselregen",
        55: "Dichter Nieselregen",
        56: "Leichter gefrierender Nieselregen",
        57: "Dichter gefrierender Nieselregen",
        61: "Leichter Regen",
        63: "Mäßiger Regen",
        65: "Starker Regen",
        66: "Leichter gefrierender Regen",
        67: "Starker gefrierender Regen",
        71: "Leichter Schneefall",
        73: "Mäßiger Schneefall",
        75: "Starker Schneefall",
        77: "Schneekörner",
        80: "Leichte Regenschauer",
        81: "Mäßige Regenschauer",
        82: "Heftige Regenschauer",
        85: "Leichte Schneeschauer",
        86: "Starke Schneeschauer",
        95: "Gewitter",
        96: "Gewitter mit leichtem Hagel",
        99: "Gewitter mit starkem Hagel",
    }
    return weather_codes.get(code, "Unbekanntes Wetterphänomen")


def _get_retry_session(retries=3, backoff_factor=1.5, status_forcelist=(500, 502, 504)):
    """
    Erstellt eine Requests-Session mit automatischer Wiederholung bei Fehlern.
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_weather_from_api_tool(
    city: str = None,
    location: str = None,
    date_str: Optional[str] = None,
    api_key: str = "",
    **kwargs,
) -> ToolResultV1:
    """
    Wettervorhersage via Open-Meteo mit robuster Retry-Strategie.
    Akzeptiert sowohl 'city' als auch 'location' als Parameter.
    Gibt ToolResultV1 zurück.
    """
    started_at = time.perf_counter()
    skill_name = "system.weather"

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    try:
        # Fallback: Wenn 'city' fehlt, nimm 'location'
        target_city = city or location

        if not target_city:
            logger.warning("skill=%s status=error code=INVALID_INPUT", skill_name)
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="INVALID_INPUT",
                    message="Kein Ort angegeben. Bitte gib eine Stadt an.",
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        if not api_key or api_key.strip().lower() == "todo":
            try:
                fallback_response = requests.get(
                    f"https://wttr.in/{target_city}?format=3", timeout=10
                )
                fallback_response.raise_for_status()
                fc_raw = fallback_response.text.strip()
                if not fc_raw:
                    raise requests.RequestException("wttr.in returned an empty response")
                q_lbl = weather_source_label("wttr.in")
                fc_body = append_quelle_line(fc_raw, q_lbl) if q_lbl else fc_raw
                logger.info("skill=%s status=ok source=wttr.in city=%s ms=%s", skill_name, target_city, _elapsed_ms())
                return ToolResultV1(
                    status="ok",
                    data={
                        "forecast": fc_body,
                        "source": "wttr.in",
                        "city": target_city,
                    },
                    metadata={"execution_time_ms": _elapsed_ms()},
                )
            except requests.RequestException as exc:
                logger.warning("wttr.in fallback failed: %s", exc)
                # Fallback versucht, aber wir können weiter mit der normalen API.

        # Timeout auch für Geocoding erhöhen
        geolocator = Nominatim(user_agent="janus_projekt_weather_tool", timeout=15)
        location = geolocator.geocode(target_city)
        if not location:
            logger.warning("skill=%s status=error code=NOT_FOUND city=%s", skill_name, target_city)
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="NOT_FOUND",
                    message=f"Stadt '{target_city}' konnte nicht gefunden werden.",
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        lat, lon = location.latitude, location.longitude

        target_date = datetime.now()  # Default: Heute
        if date_str:
            # FIX: Nutzung von dateparser für deutsche Wochentage ("Samstag")
            parsed_date = dateparser.parse(
                date_str,
                languages=["de", "en"],
                settings={
                    "PREFER_DATES_FROM": "future",  # Wenn "Samstag" gesagt wird, meine den kommenden
                    "TIMEZONE": "Europe/Berlin",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                },
            )
            if parsed_date:
                target_date = parsed_date
                logger.info(f"Wetter-Datum '{date_str}' interpretiert als: {target_date.date()}")
            else:
                logger.warning(f"Konnte Datum '{date_str}' nicht parsen, nutze heute.")

        api_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max"
            "&timezone=Europe/Berlin&forecast_days=10"  # Erhöht auf 10 Tage für längere Vorhersagen
        )

        # Nutzung der Session mit Retries
        session = _get_retry_session()
        # User-Agent ist wichtig für Open-Meteo!
        headers = {"User-Agent": "JanusAI/1.0 (janus.projekt@example.com)"}

        response = session.get(api_url, headers=headers, timeout=10)

        response.raise_for_status()
        data = response.json()
        daily_data = data.get("daily", {})
        forecast_dates = daily_data.get("time", [])
        day_index = 0

        if forecast_dates:
            try:
                # Suche das passendste Datum in der Liste
                target_date_str = target_date.strftime("%Y-%m-%d")
                day_index = forecast_dates.index(target_date_str)
            except ValueError:
                # Datum nicht in Vorhersage (zu weit in Zukunft/Vergangenheit)
                logger.warning("skill=%s status=error code=DATE_OUT_OF_RANGE date=%s", skill_name, date_str)
                return ToolResultV1(
                    status="error",
                    data={},
                    error=ToolErrorDetails(
                        code="DATE_OUT_OF_RANGE",
                        message=(
                            f"Keine Wetterdaten für den {target_date.strftime('%d.%m.%Y')} verfügbar "
                            f"(nur nächste 10 Tage)."
                        ),
                    ),
                    metadata={"execution_time_ms": _elapsed_ms()},
                )

        if not forecast_dates or day_index >= len(forecast_dates):
            logger.warning("skill=%s status=error code=NO_DATA city=%s", skill_name, target_city)
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="NO_DATA",
                    message="Keine Vorhersagedaten verfügbar.",
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        weather_date = daily_data["time"][day_index]
        temp_max = daily_data["temperature_2m_max"][day_index]
        temp_min = daily_data["temperature_2m_min"][day_index]
        prec_prob = daily_data["precipitation_probability_max"][day_index]
        wind_speed_max = daily_data["wind_speed_10m_max"][day_index]
        weather_desc = _get_weather_code_description(daily_data["weather_code"][day_index])

        # Besseres Datumsformat für die Ausgabe
        date_output = datetime.fromisoformat(weather_date).strftime("%d.%m.%Y")

        display_city = target_city.title()
        output = (
            f"Wettervorhersage für {display_city} am {date_output} ({date_str if date_str else 'heute'}): "
            f"Es wird {weather_desc.lower()} erwartet. Höchsttemperatur: {temp_max}°C, Tiefsttemperatur: {temp_min}°C. "
            f"Niederschlagswahrscheinlichkeit: {prec_prob}%. Windböen bis zu {wind_speed_max} km/h."
        )
        om_lbl = weather_source_label("open-meteo")
        forecast_text = append_quelle_line(output, om_lbl) if om_lbl else output
        logger.info("skill=%s status=ok city=%s ms=%s", skill_name, target_city, _elapsed_ms())
        return ToolResultV1(
            status="ok",
            data={
                "forecast": forecast_text,
                "city": display_city,
                "date": date_output,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "precipitation_probability": prec_prob,
                "wind_speed_max": wind_speed_max,
                "weather_description": weather_desc,
                "source": "open-meteo",
            },
            metadata={"execution_time_ms": _elapsed_ms()},
        )

    except Exception as e:
        logger.error("skill=%s status=error code=API_UNAVAILABLE error=%s ms=%s", skill_name, e, _elapsed_ms(), exc_info=True)
        target_city = city or location or "?"
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="API_UNAVAILABLE",
                message=(
                    f"Die Wetter-API antwortet nicht. Bitte benutze stattdessen das Tool 'system.websearch' "
                    f"mit der Anfrage: 'Wetter in {target_city} {date_str if date_str else 'heute'}'."
                ),
                details={"exception": str(e)},
            ),
            metadata={"execution_time_ms": _elapsed_ms()},
        )


def get_full_weather_forecast(location: str, days: int = 16) -> Dict[str, Any]:
    """Tagesraster mit Niederschlagswahrscheinlichkeit für optionale Kalender-Anreicherung.

    Open-Meteo (gleiche Ebene wie ``get_weather_from_api_tool``). Bei leerem Ort oder
    API-/Geocode-Fehler: ``{\"forecast\": {}}`` — kein Raise.

    Vertrag für ``calendar.find_slots``: unter ``forecast`` je ISO-Datum ein Dict mit
    ``precipitation_probability_max`` (0–100).
    """
    forecast: Dict[str, Dict[str, int]] = {}
    loc_query = str(location or "").strip()
    if not loc_query:
        return {"forecast": {}}

    cap = max(1, min(int(days), 16))

    try:
        geolocator = Nominatim(user_agent="janus_projekt_weather_tool", timeout=15)
        geo = geolocator.geocode(loc_query)
        if not geo:
            return {"forecast": {}}

        lat, lon = geo.latitude, geo.longitude
        api_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&daily=precipitation_probability_max"
            "&timezone=Europe%2FBerlin"
            f"&forecast_days={cap}"
        )
        session = _get_retry_session()
        headers = {"User-Agent": "JanusAI/1.0 (janus.projekt@example.com)"}
        resp = session.get(api_url, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        daily = payload.get("daily") or {}
        times = daily.get("time") or []
        probs = daily.get("precipitation_probability_max") or []
        for i, day in enumerate(times):
            if i >= len(probs) or probs[i] is None:
                continue
            try:
                p = int(probs[i])
            except (TypeError, ValueError):
                continue
            forecast[str(day)] = {"precipitation_probability_max": p}
    except Exception as exc:
        logger.debug("get_full_weather_forecast: skipped (%s)", exc)
        return {"forecast": {}}

    return {"forecast": forecast}
