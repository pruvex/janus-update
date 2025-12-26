import logging
from datetime import datetime
from typing import Dict, Optional

import dateparser
import requests
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("janus_backend")


class CleanGetWeatherFromApiToolArgs(BaseModel):
    city: str = Field(
        ..., description="Die Stadt für die Wettervorhersage. Nenne NUR die Stadt aus der Anfrage."
    )
    date_str: Optional[str] = Field(
        None, description="Das Datum (z.B. 'heute', 'morgen', 'Samstag')."
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


def get_weather_from_api_tool(city: str, date_str: Optional[str] = None) -> Dict[str, str]:
    """
    Wettervorhersage via Open-Meteo mit robuster Retry-Strategie.
    """
    # Timeout auch für Geocoding erhöhen
    geolocator = Nominatim(user_agent="janus_projekt_weather_tool", timeout=15)
    try:
        location = geolocator.geocode(city)
        if not location:
            return {"status": "error", "message": f"Stadt '{city}' konnte nicht gefunden werden."}

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

        # Reduzierter Timeout auf 5s für bessere Reaktionszeit
        response = session.get(api_url, headers=headers, timeout=5)

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
                return {
                    "status": "error",
                    "message": f"Keine Wetterdaten für den {target_date.strftime('%d.%m.%Y')} verfügbar (nur nächste 10 Tage).",
                }

        if not forecast_dates or day_index >= len(forecast_dates):
            return {"status": "error", "message": "Keine Vorhersagedaten verfügbar."}

        weather_date = daily_data["time"][day_index]
        temp_max = daily_data["temperature_2m_max"][day_index]
        temp_min = daily_data["temperature_2m_min"][day_index]
        prec_prob = daily_data["precipitation_probability_max"][day_index]
        wind_speed_max = daily_data["wind_speed_10m_max"][day_index]
        weather_desc = _get_weather_code_description(daily_data["weather_code"][day_index])

        # Besseres Datumsformat für die Ausgabe
        date_output = datetime.fromisoformat(weather_date).strftime("%d.%m.%Y")

        output = (
            f"Wettervorhersage für {city.title()} am {date_output} ({date_str if date_str else 'heute'}): "
            f"Es wird {weather_desc.lower()} erwartet. Höchsttemperatur: {temp_max}°C, Tiefsttemperatur: {temp_min}°C. "
            f"Niederschlagswahrscheinlichkeit: {prec_prob}%. Windböen bis zu {wind_speed_max} km/h."
        )
        logger.info(f"Wetter für {city} abgerufen: {output}")
        return {"status": "success", "output": output}

    except (requests.exceptions.RetryError, requests.exceptions.Timeout, Exception) as e:
        logger.error(f"Wetter-Tool Fehler: {e}")
        # WICHTIG: Wir geben eine Anweisung zurück, keine Fehlermeldung, damit das LLM weicht.
        return {
            "status": "error",
            "output": f"Die Wetter-API antwortet nicht. Bitte benutze stattdessen das Tool 'perform_websearch' mit der Anfrage: 'Wetter in {city} {date_str if date_str else 'heute'}'.",
        }
