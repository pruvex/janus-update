# backend/tools/calendar_tools.py

import asyncio
import calendar
import datetime as dt
import json
import logging
import os.path
import re
import time
from datetime import date
from typing import Optional

import dateparser
import keyring
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from thefuzz import fuzz

from backend.data.schemas_tools import ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

# WICHTIG: Kein Top-Level Import von contact_manager, um Zirkelbezüge zu vermeiden!

logger = logging.getLogger("janus_backend")

# Konstanten
GOOGLE_TOKEN_KEY = "janus_google_token"
GOOGLE_CLIENT_SECRETS_KEY = "janus_google_client_secrets"
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BERLIN_TZ = pytz.timezone("Europe/Berlin")

_CAL_TAGS = ["calendar", "appointment"]


def _cal_ok(
    data: dict,
    *,
    message: Optional[str] = None,
    started_at: float,
    suggest_follow_up: bool = True,
    primary_entity_id: Optional[str] = None,
) -> ToolResultV1:
    return tool_ok_v1(
        data,
        message=message,
        tags=_CAL_TAGS,
        started_at=started_at,
        suggest_follow_up=suggest_follow_up,
        primary_entity_id=primary_entity_id,
    )


def _cal_err(
    code: str,
    message: str,
    *,
    details: Optional[dict] = None,
    started_at: float,
) -> ToolResultV1:
    return tool_err_v1(code, message, details=details, tags=_CAL_TAGS, started_at=started_at)


# Hilfsfunktionen für die Google-Authentifizierung
def _get_google_client_secrets():
    client_secrets_json = keyring.get_password(
        "janus_google_credentials", GOOGLE_CLIENT_SECRETS_KEY
    )
    if client_secrets_json:
        return json.loads(client_secrets_json)

    # Fallback: Lade aus Umgebungsvariablen und speichere im Keyring
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if client_id and client_secret:
        client_secrets = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"],
                "javascript_origins": ["http://localhost"],
            }
        }
        keyring.set_password(
            "janus_google_credentials", GOOGLE_CLIENT_SECRETS_KEY, json.dumps(client_secrets)
        )
        logger.info("Google Client-Geheimnisse aus Umgebungsvariablen geladen und im Keyring gespeichert.")
        return client_secrets

    logger.error("Google Client-Geheimnisse weder im Keyring noch in Umgebungsvariablen gefunden.")
    return None


def _get_calendar_service():
    creds = None
    token_json = keyring.get_password("janus_google_tokens", GOOGLE_TOKEN_KEY)
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            client_secrets = _get_google_client_secrets()
            if not client_secrets:
                raise Exception("Google Client-Geheimnisse nicht verfügbar.")
            flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
            creds = flow.run_local_server(port=0)

        keyring.set_password("janus_google_tokens", GOOGLE_TOKEN_KEY, creds.to_json())
        logger.info("Google Calendar Token im Keyring gespeichert/aktualisiert.")

    return build("calendar", "v3", credentials=creds)


# Werkzeug-Funktionen
async def get_calendar_events(
    days_in_future: int = 7, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> ToolResultV1:
    t0 = time.perf_counter()
    try:
        service = _get_calendar_service()

        if start_date:
            try:
                parsed_start_date = dateparser.parse(
                    start_date,
                    languages=["de", "en"],
                    settings={
                        "PREFER_DATES_FROM": "future",
                        "TIMEZONE": "Europe/Berlin",
                        "RETURN_AS_TIMEZONE_AWARE": True,
                    },
                )
                if parsed_start_date is None:
                    raise ValueError(f"Konnte Startdatum '{start_date}' nicht parsen.")
                time_min = parsed_start_date.isoformat()
                if end_date:
                    parsed_end_date = dateparser.parse(
                        end_date,
                        languages=["de", "en"],
                        settings={
                            "PREFER_DATES_FROM": "future",
                            "TIMEZONE": "Europe/Berlin",
                            "RETURN_AS_TIMEZONE_AWARE": True,
                        },
                    )
                    if parsed_end_date is None:
                        raise ValueError(f"Konnte Enddatum '{end_date}' nicht parsen.")
                    time_max = (parsed_end_date.replace(hour=23, minute=59, second=59)).isoformat()
                else:
                    time_max = (
                        parsed_start_date.replace(hour=23, minute=59, second=59)
                    ).isoformat()
            except (ValueError, TypeError) as e:
                return _cal_err(
                    "DATE_PARSE_FAILED",
                    f"Das Datum '{start_date}' oder '{end_date}' konnte nicht verstanden werden. Fehler: {e}",
                    started_at=t0,
                )
        else:
            time_min = dt.datetime.now(BERLIN_TZ).isoformat()
            time_max = (dt.datetime.now(BERLIN_TZ) + dt.timedelta(days=days_in_future)).isoformat()

        events_result = await asyncio.to_thread(
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=25,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute
        )
        events = events_result.get("items", [])
        if not events:
            return _cal_ok(
                {"events": [], "listing_text": "", "event_count": 0},
                message="Keine Termine im angegebenen Zeitraum gefunden.",
                started_at=t0,
            )

        formatted_events = []
        for event in events:
            start_str = event["start"].get("dateTime", event["start"].get("date"))
            start_dt = dateparser.parse(
                start_str,
                languages=["de", "en"],
                settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            end_str = event["end"].get("dateTime", event["end"].get("date"))
            end_dt = dateparser.parse(
                end_str,
                languages=["de", "en"],
                settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            formatted_time = (
                f"Ganztägig am {start_dt.strftime('%d.%m.%Y')}"
                if "date" in event["start"]
                else f"Am {start_dt.strftime('%d.%m.%Y')} von {start_dt.strftime('%H:%M')} bis {end_dt.strftime('%H:%M')} Uhr"
            )
            event_details = [
                f"Titel: {event.get('summary', 'Kein Titel')}",
                f"Zeit: {formatted_time}",
                f"Event-ID: {event['id']}",
            ]
            if event.get("location"):
                event_details.append(f"Ort: {event['location']}")
            if event.get("description"):
                event_details.append(
                    f"Beschreibung: {event['description'].replace(' ', ' ').strip()[:150]}"
                )
            formatted_events.append(" - " + "\n   ".join(event_details))
        listing_text = "Hier sind deine nächsten Termine:\n" + "\n\n".join(formatted_events)
        return _cal_ok(
            {
                "events": events,
                "listing_text": listing_text,
                "event_count": len(events),
            },
            message=listing_text.split("\n")[0] if listing_text else None,
            started_at=t0,
        )
    except Exception as e:
        return _cal_err(
            "CALENDAR_LIST_FAILED",
            f"Fehler beim Abrufen der Kalendertermine: {str(e)}",
            started_at=t0,
        )


async def create_calendar_event(
    summary: str,
    start_time_str: str,
    location: Optional[str] = None,
    description: Optional[str] = None,
    # Dependency Injection Argumente (werden vom Executor gefüllt):
    db: Session = None,
    api_key: str = None,
    provider: str = None,
    model: str = None,
) -> ToolResultV1:
    """
    Erstellt einen Kalendereintrag und prüft automatisch auf neue Kontakte im Kontext.
    """
    t0 = time.perf_counter()
    # LOKALER IMPORT VERHINDERT ZIRKELBEZUG (llm_gateway <-> calendar_tools)
    from backend.services import contact_manager

    try:
        service = _get_calendar_service()

        if start_time_str and "uhr" in start_time_str.lower() and ":" not in start_time_str:
            start_time_str = re.sub(r"(\d+)\s*uhr", r"\1:00", start_time_str, flags=re.IGNORECASE)
        try:
            normalized_time_str = (
                start_time_str.lower().replace("am ", "").replace("um ", "").replace("den ", "")
            )
            start_dt = dateparser.parse(
                normalized_time_str,
                languages=["de", "en"],
                settings={
                    "TIMEZONE": "Europe/Berlin",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "PREFER_DATES_FROM": "future",
                },
            )
            if start_dt is None:
                return _cal_err(
                    "DATE_PARSE_FAILED",
                    f"Konnte Startzeit '{start_time_str}' nicht parsen.",
                    started_at=t0,
                )
        except Exception as e:
            return _cal_err("DATE_PARSE_FAILED", f"Fehler beim Parsen des Datums: {e}", started_at=t0)

        time_min_check = start_dt.replace(hour=0, minute=0, second=0).isoformat()
        time_max_check = start_dt.replace(hour=23, minute=59, second=59).isoformat()
        existing_events_result = await asyncio.to_thread(
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min_check,
                timeMax=time_max_check,
                singleEvents=True,
            )
            .execute
        )
        existing_events = existing_events_result.get("items", [])

        for event in existing_events:
            existing_summary = event.get("summary", "")
            similarity = fuzz.ratio(summary.lower(), existing_summary.lower())
            existing_start_str = event["start"].get("dateTime", event["start"].get("date"))
            existing_start_dt = dateparser.parse(
                existing_start_str,
                settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            if not existing_start_dt or not existing_start_dt.tzinfo:
                continue
            time_difference = abs(start_dt - existing_start_dt)
            if similarity > 85 and time_difference < dt.timedelta(minutes=15):
                logger.warning(
                    f"Duplikat-Termin gefunden (Ähnlichkeit: {similarity}%, Zeitdifferenz: {time_difference}). Erstellung wird abgebrochen."
                )
                return _cal_ok(
                    {
                        "duplicate_skipped": True,
                        "similar_event_summary": existing_summary,
                    },
                    message=(
                        f"Ein sehr ähnlicher Termin ('{existing_summary}') existiert bereits zu dieser Zeit. "
                        "Der Termin wurde nicht erneut erstellt."
                    ),
                    started_at=t0,
                    suggest_follow_up=False,
                )

        end_dt = start_dt + dt.timedelta(hours=1)
        has_time = bool(
            re.search(r"(\d{1,2}:\d{2}|\d{1,2}\s*uhr)", start_time_str.lower())
        ) or not (start_dt.hour == 0 and start_dt.minute == 0)
        event_body = {"summary": summary, "location": location, "description": description}
        if not has_time:
            event_body["start"] = {"date": start_dt.strftime("%Y-%m-%d")}
            event_body["end"] = {"date": (start_dt + dt.timedelta(days=1)).strftime("%Y-%m-%d")}
        else:
            event_body["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Berlin"}
            event_body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Berlin"}

        created_event = await asyncio.to_thread(
            service.events().insert(calendarId="primary", body=event_body).execute
        )

        output_msg = f"Termin '{created_event.get('summary')}' wurde erfolgreich erstellt."

        # --- AUTONOME NEBENEFFEKTE ---
        if db and api_key and provider:
            try:
                full_text_for_extraction = (
                    f"Event Summary: {summary}\n"
                    f"Event Location: {location}\n"
                    f"Event Details: {description}"
                )

                logger.info(f"Autonomes Tool: Starte Kontaktextraktion für Event '{summary}'")

                asyncio.create_task(
                    contact_manager.extract_and_save_contact(
                        text_block=full_text_for_extraction,
                        api_key=api_key,
                        provider=provider,
                        model=model,
                    )
                )
                output_msg += " (Ich prüfe im Hintergrund, ob neue Kontakte enthalten sind.)"
            except Exception as e:
                logger.error(f"Fehler bei autonomer Kontaktextraktion: {e}")
        # ---------------------------

        return _cal_ok(
            {
                "event_id": created_event.get("id"),
                "summary": created_event.get("summary"),
            },
            message=output_msg,
            started_at=t0,
            primary_entity_id=str(created_event.get("id")) if created_event.get("id") else None,
        )
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Termins: {str(e)}", exc_info=True)
        return _cal_err(
            "CALENDAR_CREATE_FAILED",
            f"Fehler beim Erstellen des Termins: {str(e)}",
            started_at=t0,
        )


async def delete_calendar_event(event_id: str) -> ToolResultV1:
    t0 = time.perf_counter()
    try:
        service = _get_calendar_service()
        await asyncio.to_thread(
            service.events().delete(calendarId="primary", eventId=event_id).execute
        )
        return _cal_ok(
            {"event_id": event_id, "deleted": True},
            message="Der angegebene Termin wurde erfolgreich gelöscht.",
            started_at=t0,
            primary_entity_id=str(event_id),
        )
    except Exception as e:
        if "Not Found" in str(e):
            return _cal_err(
                "NOT_FOUND",
                f"Ein Termin mit der ID '{event_id}' konnte nicht gefunden werden.",
                started_at=t0,
            )
        return _cal_err(
            "CALENDAR_DELETE_FAILED",
            f"Fehler beim Löschen des Termins: {str(e)}",
            started_at=t0,
        )


async def update_calendar_event(
    event_id: str,
    summary: Optional[str] = None,
    start_time_str: Optional[str] = None,
    end_time_str: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
) -> ToolResultV1:
    t0 = time.perf_counter()
    try:
        service = _get_calendar_service()
        event = await asyncio.to_thread(
            service.events().get(calendarId="primary", eventId=event_id).execute
        )

        if start_time_str and "uhr" in start_time_str.lower() and ":" not in start_time_str:
            start_time_str = re.sub(r"(\d+)\s*uhr", r"\1:00", start_time_str, flags=re.IGNORECASE)
        if end_time_str and "uhr" in end_time_str.lower() and ":" not in end_time_str:
            end_time_str = re.sub(r"(\d+)\s*uhr", r"\1:00", end_time_str, flags=re.IGNORECASE)

        if summary:
            event["summary"] = summary
        if location:
            event["location"] = location
        if description is not None:
            event["description"] = description

        if start_time_str:
            parsed_start_dt = dateparser.parse(
                start_time_str,
                languages=["de", "en"],
                settings={
                    "TIMEZONE": "Europe/Berlin",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "PREFER_DATES_FROM": "future",
                },
            )
            if parsed_start_dt is None:
                return _cal_err(
                    "DATE_PARSE_FAILED",
                    f"Konnte Startdatum '{start_time_str}' nicht parsen.",
                    started_at=t0,
                )
            if not end_time_str:
                old_start_dt = dateparser.parse(
                    event["start"].get("dateTime", event["start"].get("date")),
                    settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
                )
                old_end_dt = dateparser.parse(
                    event["end"].get("dateTime", event["end"].get("date")),
                    settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
                )
                duration = old_end_dt - old_start_dt
                new_end_dt = parsed_start_dt + duration
                event["end"] = {"dateTime": new_end_dt.isoformat(), "timeZone": "Europe/Berlin"}
            has_time_in_new_start_str = bool(
                re.search(r"(\d{1,2}:\d{2}|\d{1,2}\s*uhr)", start_time_str.lower())
            )
            if not has_time_in_new_start_str:
                event["start"] = {"date": parsed_start_dt.strftime("%Y-%m-%d")}
                if not end_time_str:
                    event["end"] = {
                        "date": (parsed_start_dt + dt.timedelta(days=1)).strftime("%Y-%m-%d")
                    }
            else:
                event["start"] = {
                    "dateTime": parsed_start_dt.isoformat(),
                    "timeZone": "Europe/Berlin",
                }
        if end_time_str:
            parsed_end_dt = dateparser.parse(
                end_time_str,
                languages=["de", "en"],
                settings={
                    "TIMEZONE": "Europe/Berlin",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "PREFER_DATES_FROM": "future",
                },
            )
            if parsed_end_dt is None:
                return _cal_err(
                    "DATE_PARSE_FAILED",
                    f"Konnte Enddatum '{end_time_str}' nicht parsen.",
                    started_at=t0,
                )
            has_time_in_new_end_str = bool(
                re.search(r"(\d{1,2}:\d{2}|\d{1,2}\s*uhr)", end_time_str.lower())
            )
            if not has_time_in_new_end_str:
                event["end"] = {"date": (parsed_end_dt + dt.timedelta(days=1)).strftime("%Y-%m-%d")}
            else:
                event["end"] = {"dateTime": parsed_end_dt.isoformat(), "timeZone": "Europe/Berlin"}

        updated_event = await asyncio.to_thread(
            service.events().update(calendarId="primary", eventId=event["id"], body=event).execute
        )
        return _cal_ok(
            {"event_id": updated_event.get("id"), "summary": updated_event.get("summary")},
            message=f"Termin '{updated_event.get('summary')}' wurde erfolgreich aktualisiert.",
            started_at=t0,
            primary_entity_id=str(updated_event.get("id")) if updated_event.get("id") else None,
        )
    except Exception as e:
        return _cal_err(
            "CALENDAR_UPDATE_FAILED",
            f"Fehler beim Aktualisieren des Termins: {str(e)}",
            started_at=t0,
        )


async def find_free_time_slots(
    year: int, month: int, location_for_weather: Optional[str] = None
) -> ToolResultV1:
    t0 = time.perf_counter()
    try:
        events_data = await get_calendar_events(days_in_future=31)
        if events_data.status != "ok":
            return events_data
        listing = events_data.data.get("listing_text", "") or ""
        busy_days = set()
        for line in listing.split("\n"):
            if " am " in line:
                try:
                    day_str = line.split(" am ")[1].split(" von ")[0].strip()
                    parsed_date = dateparser.parse(
                        day_str,
                        languages=["de"],
                        settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
                    ).date()
                    if parsed_date and parsed_date.year == year and parsed_date.month == month:
                        busy_days.add(parsed_date.day)
                except (ValueError, TypeError):
                    continue

        today = date.today()
        num_days_in_month = calendar.monthrange(year, month)[1]
        free_days_info = []
        weather_forecast = {}
        if location_for_weather:
            # Optional Wetter-Anreicherung (Modul kann fehlen — dann still weglassen)
            try:
                from .weather_tools import get_full_weather_forecast  # type: ignore

                forecast_data = get_full_weather_forecast(location_for_weather, days=16)
                wf = forecast_data.get("forecast") if isinstance(forecast_data, dict) else {}
                if wf:
                    weather_forecast = wf
            except Exception as exc:
                logger.warning(
                    "calendar.find_slots: Wetter-Anreicherung übersprungen (%s)",
                    exc,
                )

        for day in range(1, num_days_in_month + 1):
            current_day = date(year, month, day)
            if current_day >= today and day not in busy_days:
                day_str_iso = current_day.strftime("%Y-%m-%d")
                info = current_day.strftime("%d. %B %Y")
                if (
                    day_str_iso in weather_forecast
                    and weather_forecast[day_str_iso].get("precipitation_probability_max", 100) < 40
                ):
                    info += " (voraussichtlich trocken)"
                free_days_info.append(info)

        if not free_days_info:
            return _cal_ok(
                {"free_days": [], "month": month, "year": year},
                message="In diesem Monat wurden keine freien Tage gefunden.",
                started_at=t0,
            )
        listing_text = "Folgende Tage sind im Kalender noch komplett frei:\n" + "\n\n".join(
            f"- {d}" for d in free_days_info
        )
        return _cal_ok(
            {"free_days": free_days_info, "month": month, "year": year, "listing_text": listing_text},
            message=listing_text,
            started_at=t0,
        )
    except Exception as e:
        return _cal_err(
            "FREE_SLOTS_FAILED",
            f"Fehler bei der Suche nach freien Tagen: {str(e)}",
            started_at=t0,
        )


async def find_address_and_update_calendar_event(event_title_query: str, location_query: str) -> ToolResultV1:
    from backend.services.websearch import execute_websearch
    from backend.utils.config_loader import load_model_catalog
    import keyring

    t0 = time.perf_counter()
    try:
        calendar_data = await get_calendar_events(days_in_future=90)
        calendar_data_str = calendar_data.data.get("listing_text", "")

        match = re.search(
            f"Titel:.*?{re.escape(event_title_query)}.*?Event-ID: (\\S+)",
            calendar_data_str,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return _cal_err(
                "NOT_FOUND",
                f"Ich konnte keinen Termin finden, der auf '{event_title_query}' passt.",
                started_at=t0,
            )

        event_id = match.group(1)
        config = load_model_catalog()
        provider = str(config.get("last_used_provider", "openai")).lower()
        api_key = keyring.get_password("Janus-Projekt", provider)
        if not api_key:
            return _cal_err(
                "CONFIG_MISSING",
                f"API key für Provider '{provider}' nicht konfiguriert.",
                started_at=t0,
            )

        search_result = await execute_websearch(
            query=location_query,
            api_key=api_key,
            provider=provider,
        )
        web_content = search_result.get("text", "")

        address_match = re.search(
            r"([A-Za-zß-]+\s?\w*\.?\s?\d{1,4}[a-z]?,\s*\d{5}\s*[A-Za-zß-]+)", web_content
        )
        if not address_match:
            return _cal_err(
                "ADDRESS_NOT_FOUND",
                f"Ich konnte keine genaue Adresse für '{location_query}' im Web finden.",
                started_at=t0,
            )

        found_address = address_match.group(0)
        update_result = await update_calendar_event(event_id=event_id, location=found_address)
        if update_result.status != "ok":
            return update_result
        return _cal_ok(
            {
                "event_id": event_id,
                "location_query": location_query,
                "found_address": found_address,
            },
            message=(
                f"Ich habe den Termin '{event_title_query}' erfolgreich mit der Adresse "
                f"'{found_address}' aktualisiert."
            ),
            started_at=t0,
            primary_entity_id=str(event_id),
        )
    except Exception as e:
        return _cal_err("UNEXPECTED_ERROR", f"Ein unerwarteter Fehler ist aufgetreten: {e}", started_at=t0)


async def update_calendar_event_description(
    event_title_query: str, new_description_part: str
) -> ToolResultV1:
    t0 = time.perf_counter()
    try:
        calendar_data = await get_calendar_events(days_in_future=90)
        if calendar_data.status != "ok":
            return calendar_data

        events = calendar_data.data.get("events", [])
        found_event = next(
            (
                event
                for event in events
                if re.search(event_title_query, event.get("summary", ""), re.IGNORECASE)
            ),
            None,
        )
        if not found_event:
            return _cal_err(
                "NOT_FOUND",
                f"Ich konnte keinen Termin finden, der auf '{event_title_query}' passt.",
                started_at=t0,
            )

        event_id = found_event["id"]
        old_description = found_event.get("description", "")
        updated_description = f"{old_description.strip()}\n{new_description_part.strip()}".strip()

        if updated_description == old_description.strip():
            return _cal_ok(
                {"event_id": event_id, "unchanged": True},
                message=(
                    f"Die Beschreibung für '{event_title_query}' enthält bereits die Information."
                ),
                started_at=t0,
                primary_entity_id=str(event_id),
            )

        update_result = await update_calendar_event(
            event_id=event_id, description=updated_description
        )
        if update_result.status != "ok":
            return update_result
        return _cal_ok(
            {"event_id": event_id, "updated": True},
            message=f"Ich habe die Beschreibung für '{event_title_query}' erfolgreich aktualisiert.",
            started_at=t0,
            primary_entity_id=str(event_id),
        )
    except Exception as e:
        return _cal_err("UNEXPECTED_ERROR", f"Ein unerwarteter Fehler ist aufgetreten: {e}", started_at=t0)


async def find_and_update_calendar_event(
    event_title_query: str,
    new_start_time: Optional[str] = None,
    new_end_time: Optional[str] = None,
    new_summary: Optional[str] = None,
    new_location: Optional[str] = None,
    new_description: Optional[str] = None,
    cancel_event: Optional[bool] = False,
) -> ToolResultV1:
    t0 = time.perf_counter()
    try:
        calendar_data = await get_calendar_events(days_in_future=90)
        if calendar_data.status != "ok":
            return calendar_data

        events = calendar_data.data.get("events", [])

        best_match = None
        highest_score = 0
        for event in events:
            summary = event.get("summary", "")
            score = fuzz.token_set_ratio(event_title_query.lower(), summary.lower())
            if score > highest_score:
                highest_score = score
                best_match = event

        if not best_match or highest_score < 75:
            return _cal_err(
                "NOT_FOUND",
                f"Ich konnte keinen Termin finden, der eindeutig auf '{event_title_query}' passt.",
                started_at=t0,
            )

        found_event = best_match
        event_id = found_event["id"]

        if cancel_event:
            delete_result = await delete_calendar_event(event_id=event_id)
            if delete_result.status != "ok":
                return delete_result
            return _cal_ok(
                {"event_id": event_id, "cancelled": True},
                message=f"Termin '{found_event.get('summary')}' wurde erfolgreich abgesagt.",
                started_at=t0,
                primary_entity_id=str(event_id),
            )

        if new_start_time:
            original_start_str = found_event["start"].get(
                "dateTime", found_event["start"].get("date")
            )
            original_start_dt = dateparser.parse(
                original_start_str,
                settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            if not original_start_dt:
                return _cal_err(
                    "DATE_PARSE_FAILED",
                    "Konnte das ursprüngliche Startdatum nicht verarbeiten.",
                    started_at=t0,
                )

            parsed_new_start_dt = dateparser.parse(
                new_start_time,
                languages=["de", "en"],
                settings={
                    "TIMEZONE": "Europe/Berlin",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "PREFER_DATES_FROM": "future",
                },
            )
            if parsed_new_start_dt is None:
                return _cal_err(
                    "DATE_PARSE_FAILED",
                    f"Konnte die neue Startzeit '{new_start_time}' nicht verstehen.",
                    started_at=t0,
                )

            time_only_pattern = re.compile(
                r"^\s*\d{1,2}(:\d{2})?(\s*(uhr|am|pm))?\s*$", re.IGNORECASE
            )
            date_keywords = [
                "morgen",
                "heute",
                "übermorgen",
                "montag",
                "dienstag",
                "mittwoch",
                "donnerstag",
                "freitag",
                "samstag",
                "sonntag",
                "jan",
                "feb",
                "mär",
                "apr",
                "mai",
                "jun",
                "jul",
                "aug",
                "sep",
                "okt",
                "nov",
                "dez",
            ]

            is_time_only_input = time_only_pattern.match(new_start_time) and not any(
                keyword in new_start_time.lower() for keyword in date_keywords
            )

            is_suspiciously_today = (
                parsed_new_start_dt.date() == dt.date.today()
                and "heute" not in new_start_time.lower()
            )

            if is_time_only_input or is_suspiciously_today:
                logger.info(
                    f"Reine Zeitangabe erkannt. Kombiniere ursprüngliches Datum ({original_start_dt.date()}) mit neuer Zeit ({parsed_new_start_dt.time()})."
                )
                final_start_dt = original_start_dt.replace(
                    hour=parsed_new_start_dt.hour,
                    minute=parsed_new_start_dt.minute,
                    second=0,
                    microsecond=0,
                )
                new_start_time = final_start_dt.isoformat()

        update_result = await update_calendar_event(
            event_id=event_id,
            summary=new_summary,
            start_time_str=new_start_time,
            end_time_str=new_end_time,
            location=new_location,
            description=new_description,
        )
        return update_result
    except Exception as e:
        logger.error(
            f"Ein unerwarteter Fehler ist in find_and_update_calendar_event aufgetreten: {e}",
            exc_info=True,
        )
        return _cal_err(
            "UNEXPECTED_ERROR",
            f"Ein unerwarteter Fehler ist aufgetreten: {e}",
            started_at=t0,
        )
