from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz
from backend.tools import calendar_tools
from dateutil import parser

# Definiere die Zeitzone für Berlin
BERLIN_TZ = pytz.timezone("Europe/Berlin")


def _md(r):
    """ToolResultV1 → dict for assertions."""
    return r.model_dump()


# Mock für den Google Calendar Service
@pytest.fixture
def mock_calendar_service():
    with patch("backend.tools.calendar_tools._get_calendar_service") as mock_service:
        mock_events = MagicMock()
        mock_service.return_value.events.return_value = mock_events
        mock_events.insert.return_value.execute.return_value = {
            "summary": "Test Termin",
            "id": "test_id",
        }
        mock_events.delete.return_value.execute.return_value = {}
        mock_events.get.return_value.execute.return_value = {
            "summary": "Alter Termin",
            "start": {"dateTime": "2025-11-12T10:00:00+01:00", "timeZone": "Europe/Berlin"},
            "end": {"dateTime": "2025-11-12T11:00:00+01:00", "timeZone": "Europe/Berlin"},
            "id": "test_id",
        }
        mock_events.update.return_value.execute.return_value = {
            "summary": "Aktualisierter Termin",
            "id": "test_id",
        }
        yield mock_service


@pytest.fixture(autouse=True)
def mock_datetime_now():
    fixed_now_dt = datetime(2025, 11, 12, 10, 0, 0)
    fixed_now_localized = BERLIN_TZ.localize(fixed_now_dt)
    fixed_today = date(2025, 11, 12)

    # Mock the datetime module (dt) and date class directly
    with patch("backend.tools.calendar_tools.dt.datetime", wraps=datetime) as mock_dt_class:
        mock_dt_class.now.return_value = fixed_now_dt  # `now()` without timezone
        mock_dt_class.side_effect = lambda *args, **kwargs: datetime(
            *args, **kwargs
        )  # Ensure constructor works

        with patch("backend.tools.calendar_tools.date", wraps=date) as mock_date_class:
            mock_date_class.today.return_value = fixed_today
            mock_date_class.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            # Patch dateparser.parse with specific side effects for known relative date strings
            original_dateparser_parse = calendar_tools.dateparser.parse

            def custom_dateparser_parse(date_string, *args, **kwargs):
                current_settings = kwargs.get("settings", {})
                current_settings["RELATIVE_BASE"] = (
                    fixed_now_localized  # Use localized fixed_now as relative base
                )
                kwargs["settings"] = current_settings  # Ensure settings are passed to original

                # Predefined responses for specific test strings
                if date_string == "morgen um 15 Uhr":
                    return BERLIN_TZ.localize(datetime(2025, 11, 13, 15, 0, 0))
                elif date_string == "nächsten Freitag":
                    return BERLIN_TZ.localize(datetime(2025, 11, 14, 0, 0, 0))
                elif date_string == "übermorgen um 10 Uhr":
                    return BERLIN_TZ.localize(datetime(2025, 11, 14, 10, 0, 0))
                elif date_string == "nächsten Montag":
                    return BERLIN_TZ.localize(datetime(2025, 11, 17, 0, 0, 0))
                elif date_string == "nächsten Mittwoch":
                    return BERLIN_TZ.localize(datetime(2025, 11, 19, 0, 0, 0))
                elif date_string == "ungültiges datum":
                    return None
                elif date_string == "noch ein ungültiges datum":
                    return None
                else:
                    return original_dateparser_parse(date_string, *args, **kwargs)

            with patch(
                "backend.tools.calendar_tools.dateparser.parse", side_effect=custom_dateparser_parse
            ):
                yield


# Test für create_calendar_event
@pytest.mark.asyncio
async def test_create_calendar_event_natural_language(mock_calendar_service):
    summary = "Besprechung"
    start_time_str = "morgen um 15 Uhr"

    # Annahme: Heute ist der 12. November 2025 (durch Mocking)
    # Erwartetes Datum für "morgen" ist der 13. November 2025
    expected_start_dt = BERLIN_TZ.localize(datetime(2025, 11, 13, 15, 0, 0))
    expected_end_dt = BERLIN_TZ.localize(
        datetime(2025, 11, 13, 16, 0, 0)
    )  # Standardmäßig 1 Stunde später
    result = _md(await calendar_tools.create_calendar_event(summary, start_time_str))

    assert result["status"] == "ok"
    assert "erfolgreich erstellt" in (result.get("message") or "")

    # Überprüfe, ob der Kalenderdienst mit den korrekten geparsten Daten aufgerufen wurde
    mock_calendar_service.return_value.events.return_value.insert.assert_called_once()
    call_args = mock_calendar_service.return_value.events.return_value.insert.call_args[1]["body"]

    assert call_args["summary"] == summary
    assert parser.isoparse(call_args["start"]["dateTime"]).astimezone(BERLIN_TZ).replace(
        microsecond=0
    ) == expected_start_dt.replace(microsecond=0)
    assert parser.isoparse(call_args["end"]["dateTime"]).astimezone(BERLIN_TZ).replace(
        microsecond=0
    ) == expected_end_dt.replace(microsecond=0)
    assert call_args["start"]["timeZone"] == "Europe/Berlin"
    assert call_args["end"]["timeZone"] == "Europe/Berlin"


@pytest.mark.asyncio
async def test_create_calendar_event_all_day():
    summary = "Ganztagstermin"
    start_time_str = "2025-11-14"

    mock_service = MagicMock()
    mock_events = MagicMock()
    mock_service.events.return_value = mock_events
    mock_events.list.return_value.execute.return_value = {"items": []}
    mock_events.insert.return_value.execute.return_value = {"summary": summary, "id": "all_day_1"}

    with patch("backend.tools.calendar_tools._get_calendar_service", return_value=mock_service):
        result = _md(await calendar_tools.create_calendar_event(summary, start_time_str))

    assert result["status"] == "ok"
    assert "erfolgreich erstellt" in (result.get("message") or "")

    mock_events.insert.assert_called_once()
    call_args = mock_events.insert.call_args[1]["body"]

    assert call_args["summary"] == summary
    assert "date" in call_args["start"]
    assert "date" in call_args["end"]
    assert call_args["start"]["date"] == "2025-11-14"
    assert call_args["end"]["date"] == "2025-11-15"
    assert "dateTime" not in call_args["start"]
    assert "dateTime" not in call_args["end"]


@pytest.mark.asyncio
async def test_create_calendar_event_invalid_date_format(mock_calendar_service):
    summary = "Ungültiger Termin"
    start_time_str = "irgendwann"

    result = _md(await calendar_tools.create_calendar_event(summary, start_time_str))

    assert result["status"] == "error"
    assert "Konnte Startzeit 'irgendwann' nicht parsen." in result["error"]["message"]


# Test für update_calendar_event
@pytest.mark.asyncio
async def test_update_calendar_event_natural_language_start_time(mock_calendar_service):
    event_id = "test_id"
    new_start_time_str = (
        "übermorgen um 10 Uhr"  # Annahme: Heute ist 12. Nov 2025, also übermorgen ist 14. Nov 2025
    )

    expected_start_dt = BERLIN_TZ.localize(datetime(2025, 11, 14, 10, 0, 0))
    result = _md(
        await calendar_tools.update_calendar_event(
            event_id=event_id, start_time_str=new_start_time_str
        )
    )

    assert result["status"] == "ok"
    assert "erfolgreich aktualisiert" in (result.get("message") or "")

    mock_calendar_service.return_value.events.return_value.get.assert_called_once_with(
        calendarId="primary", eventId=event_id
    )
    mock_calendar_service.return_value.events.return_value.update.assert_called_once()
    call_args = mock_calendar_service.return_value.events.return_value.update.call_args[1]["body"]

    # Überprüfe, ob 'date' oder 'dateTime' im Start-Objekt vorhanden ist
    if "date" in call_args["start"]:
        assert call_args["start"]["date"] == expected_start_dt.strftime("%Y-%m-%d")
    else:
        assert parser.isoparse(call_args["start"]["dateTime"]).astimezone(BERLIN_TZ).replace(
            microsecond=0
        ) == expected_start_dt.replace(microsecond=0)
        assert call_args["start"]["timeZone"] == "Europe/Berlin"


@pytest.mark.asyncio
async def test_update_calendar_event_invalid_date_format(mock_calendar_service):
    event_id = "test_id"
    new_start_time_str = "falsches datum"

    result = _md(
        await calendar_tools.update_calendar_event(
            event_id=event_id, start_time_str=new_start_time_str
        )
    )

    assert result["status"] == "error"
    assert "Konnte Startdatum 'falsches datum' nicht parsen." in result["error"]["message"]


@pytest.mark.asyncio
async def test_update_calendar_event_metadata_only_uses_patch(mock_calendar_service):
    """Ort ohne Zeiten: PATCH (nur geänderte Felder) + zweites GET zur Verifikation."""
    event_id = "test_id"
    fetched = {
        "summary": "Alter Termin",
        "id": event_id,
        "start": {"dateTime": "2025-11-12T10:00:00+01:00", "timeZone": "Europe/Berlin"},
        "end": {"dateTime": "2025-11-12T11:00:00+01:00", "timeZone": "Europe/Berlin"},
        "etag": '"abc"',
        "kind": "calendar#event",
        "htmlLink": "https://www.google.com/calendar/event",
    }
    verified = {**fetched, "location": "Zu Hause"}
    mock_calendar_service.return_value.events.return_value.get.return_value.execute.side_effect = [
        fetched,
        verified,
    ]
    mock_calendar_service.return_value.events.return_value.patch.return_value.execute.return_value = (
        verified
    )
    result = _md(await calendar_tools.update_calendar_event(event_id=event_id, location="Zu Hause"))

    assert result["status"] == "ok"
    assert mock_calendar_service.return_value.events.return_value.get.call_count == 2
    mock_calendar_service.return_value.events.return_value.patch.assert_called_once()
    mock_calendar_service.return_value.events.return_value.update.assert_not_called()
    pc = mock_calendar_service.return_value.events.return_value.patch.call_args.kwargs
    assert pc["calendarId"] == "primary"
    assert pc["eventId"] == event_id
    assert pc["body"] == {"location": "Zu Hause"}
    assert pc["conferenceDataVersion"] == 0
    assert pc["sendUpdates"] == "none"


@pytest.mark.asyncio
async def test_update_calendar_event_metadata_patch_meet_uses_cdv1(mock_calendar_service):
    """Mit hangoutLink soll PATCH conferenceDataVersion=1 nutzen."""
    event_id = "test_id"
    fetched = {
        "summary": "Meet Termin",
        "id": event_id,
        "hangoutLink": "https://meet.google.com/xxx",
        "start": {"dateTime": "2025-11-12T10:00:00+01:00", "timeZone": "Europe/Berlin"},
        "end": {"dateTime": "2025-11-12T11:00:00+01:00", "timeZone": "Europe/Berlin"},
    }
    verified = {**fetched, "description": "Hinweis"}
    mock_calendar_service.return_value.events.return_value.get.return_value.execute.side_effect = [
        fetched,
        verified,
    ]
    mock_calendar_service.return_value.events.return_value.patch.return_value.execute.return_value = (
        verified
    )
    result = _md(await calendar_tools.update_calendar_event(event_id=event_id, description="Hinweis"))
    assert result["status"] == "ok"
    pc = mock_calendar_service.return_value.events.return_value.patch.call_args.kwargs
    assert pc["conferenceDataVersion"] == 1
    assert pc["body"] == {"description": "Hinweis"}


@pytest.mark.asyncio
async def test_update_calendar_event_metadata_fallback_update_when_verify_mismatch(mock_calendar_service):
    """GET nach PATCH ohne gewünschten Ort → einmal events.update mit gemergtem Body."""
    event_id = "test_id"
    fetched = {
        "summary": "Alter Termin",
        "id": event_id,
        "start": {"dateTime": "2025-11-12T10:00:00+01:00", "timeZone": "Europe/Berlin"},
        "end": {"dateTime": "2025-11-12T11:00:00+01:00", "timeZone": "Europe/Berlin"},
        "organizer": {"email": "me@test", "self": True},
    }
    bad_verify = dict(fetched)
    after_full_update = {**bad_verify, "location": "Büro"}
    mock_calendar_service.return_value.events.return_value.get.return_value.execute.side_effect = [
        fetched,
        bad_verify,
    ]
    mock_calendar_service.return_value.events.return_value.patch.return_value.execute.return_value = (
        bad_verify
    )
    mock_calendar_service.return_value.events.return_value.update.return_value.execute.return_value = (
        after_full_update
    )
    result = _md(await calendar_tools.update_calendar_event(event_id=event_id, location="Büro"))
    assert result["status"] == "ok"
    mock_calendar_service.return_value.events.return_value.update.assert_called_once()


# Test für get_calendar_events
@pytest.mark.asyncio
async def test_get_calendar_events_with_natural_language_dates(mock_calendar_service):
    start_date_str = (
        "nächsten Montag"  # Annahme: Heute ist 12. Nov 2025, also nächster Montag ist 17. Nov 2025
    )
    end_date_str = "nächsten Mittwoch"  # Annahme: Heute ist 12. Nov 2025, also nächster Mittwoch ist 19. Nov 2025

    # Mocken der list-Methode für get_calendar_events
    mock_calendar_service.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "summary": "Test Event",
                "start": {"dateTime": "2025-11-17T09:00:00+01:00"},
                "end": {"dateTime": "2025-11-17T10:00:00+01:00"},
                "id": "event1",
            }
        ]
    }

    result = _md(
        await calendar_tools.get_calendar_events(
            start_date=start_date_str, end_date=end_date_str
        )
    )

    assert result["status"] == "ok"
    assert "Test Event" in (result["data"].get("listing_text") or "")

    mock_calendar_service.return_value.events.return_value.list.assert_called_once()
    call_args = mock_calendar_service.return_value.events.return_value.list.call_args[1]

    expected_time_min = BERLIN_TZ.localize(datetime(2025, 11, 17, 0, 0, 0))
    expected_time_max = BERLIN_TZ.localize(datetime(2025, 11, 19, 23, 59, 59))

    parsed_time_min = parser.isoparse(call_args["timeMin"])
    parsed_time_max = parser.isoparse(call_args["timeMax"])

    assert parsed_time_min == expected_time_min
    assert parsed_time_max == expected_time_max


@pytest.mark.asyncio
async def test_get_calendar_events_invalid_date_range(mock_calendar_service):
    start_date_str = "ungültiges datum"
    end_date_str = "noch ein ungültiges datum"

    result = _md(
        await calendar_tools.get_calendar_events(
            start_date=start_date_str, end_date=end_date_str
        )
    )

    assert result["status"] == "error"
    assert "ungültiges datum" in result["error"]["message"]
