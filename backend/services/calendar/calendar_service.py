# backend/services/calendar/calendar_service.py
"""
Calendar Service Layer für Janus Calendar Modal.
Wrappt bestehende calendar_tools.py Funktionen und normalisiert Events.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from zoneinfo import ZoneInfo

from backend.data.schemas_calendar import (
    JanusCalendarEvent,
    CreateEventRequest,
    UpdateEventRequest,
    CalendarConflict,
    CalendarEventsResponse,
)
from backend.tools.calendar_tools import (
    get_calendar_events,
    create_calendar_event,
    delete_calendar_event,
    update_calendar_event,
)

logger = logging.getLogger("janus_backend.calendar_service")


class CalendarService:
    """Service Layer für Calendar-Operationen. Wrappt calendar_tools.py."""
    
    BERLIN_TZ = ZoneInfo("Europe/Berlin")
    
    # Farbcodes für verschiedene Quellen
    SOURCE_COLORS = {
        "google": "#4285F4",      # Google Blau
        "outlook": "#0078D4",     # Outlook Blau
        "caldav": "#FF9500",      # Orange
        "janus-local": "#34C759",  # Apple Grün
    }
    
    async def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_in_future: int = 30,
    ) -> CalendarEventsResponse:
        """
        Holt Events von Google Calendar und normalisiert sie.
        
        Args:
            start_date: Startdatum (ISO 8601 oder natürliche Sprache)
            end_date: Enddatum (ISO 8601 oder natürliche Sprache)
            days_in_future: Fallback-Anzahl Tage wenn kein Datum angegeben
            
        Returns:
            CalendarEventsResponse mit normalisierten Events
        """
        try:
            # Nutze bestehende calendar_tools Funktion
            result = await get_calendar_events(
                days_in_future=days_in_future,
                start_date=start_date,
                end_date=end_date,
            )
            
            if not result or not result.get("ok"):
                error_msg = result.get("message", "Unknown error") if result else "No response"
                logger.error(f"Failed to get calendar events: {error_msg}")
                return CalendarEventsResponse(
                    events=[],
                    sync_status="error",
                    total_count=0,
                )
            
            data = result.get("data", {})
            raw_events = data.get("events", [])
            
            # Normalisiere Google Events zu JanusCalendarEvent
            normalized_events = []
            for raw_event in raw_events:
                try:
                    event = self._normalize_google_event(raw_event)
                    normalized_events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to normalize event: {e}")
                    continue
            
            # Erkenne Konflikte
            conflicts = self._detect_conflicts(normalized_events)
            
            return CalendarEventsResponse(
                events=normalized_events,
                conflicts=conflicts,
                sync_status="synced",
                total_count=len(normalized_events),
            )
            
        except Exception as e:
            logger.error(f"Calendar service error in get_events: {e}", exc_info=True)
            return CalendarEventsResponse(
                events=[],
                sync_status="error",
                total_count=0,
            )
    
    async def create_event(
        self,
        request: CreateEventRequest,
    ) -> Optional[JanusCalendarEvent]:
        """
        Erstellt ein neues Event über calendar_tools.
        
        Args:
            request: CreateEventRequest mit Event-Daten
            
        Returns:
            Erstelltes JanusCalendarEvent oder None bei Fehler
        """
        try:
            # Format für calendar_tools
            start_str = request.start.strftime("%Y-%m-%d %H:%M")
            
            # Rufe bestehende Funktion
            result = await create_calendar_event(
                summary=request.title,
                start_time_str=start_str,
                location=request.location,
                description=request.description,
                duration_minutes=self._calculate_duration_minutes(request.start, request.end),
            )
            
            if not result or not result.get("ok"):
                error_msg = result.get("message", "Unknown error") if result else "No response"
                logger.error(f"Failed to create event: {error_msg}")
                return None
            
            # Extrahiere erstelltes Event aus Response
            data = result.get("data", {})
            created_event_data = data.get("created_event")
            
            if created_event_data:
                return self._normalize_google_event(created_event_data)
            
            # Fallback: Baue aus Request
            return JanusCalendarEvent(
                id=data.get("event_id", "unknown"),
                title=request.title,
                description=request.description,
                start=request.start,
                end=request.end,
                timezone=request.timezone,
                location=request.location,
                attendees=request.attendees,
                source="google",
                external_id=data.get("event_id"),
                is_all_day=request.is_all_day,
                color=self.SOURCE_COLORS["google"],
            )
            
        except Exception as e:
            logger.error(f"Calendar service error in create_event: {e}", exc_info=True)
            return None
    
    async def delete_event(self, event_id: str) -> bool:
        """
        Löscht ein Event.
        
        Args:
            event_id: Google Event-ID
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            result = await delete_calendar_event(event_id)
            
            if result and result.get("ok"):
                logger.info(f"Event {event_id} deleted successfully")
                return True
            else:
                error_msg = result.get("message", "Unknown error") if result else "No response"
                logger.error(f"Failed to delete event {event_id}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Calendar service error in delete_event: {e}", exc_info=True)
            return False
    
    async def update_event(
        self,
        event_id: str,
        request: UpdateEventRequest,
    ) -> Optional[JanusCalendarEvent]:
        """
        Aktualisiert ein existierendes Event.
        
        Args:
            event_id: Google Event-ID
            request: UpdateEventRequest mit zu ändernden Feldern
            
        Returns:
            Aktualisiertes JanusCalendarEvent oder None bei Fehler
        """
        try:
            # Baue update_data Dictionary
            update_data = {}
            if request.title is not None:
                update_data["summary"] = request.title
            if request.location is not None:
                update_data["location"] = request.location
            if request.description is not None:
                update_data["description"] = request.description
            
            # Zeit-Felder
            start_time_str = None
            if request.start is not None:
                start_time_str = request.start.strftime("%Y-%m-%d %H:%M")
            
            duration = None
            if request.start is not None and request.end is not None:
                duration = self._calculate_duration_minutes(request.start, request.end)
            elif request.is_all_day is not None:
                duration = 1440 if request.is_all_day else None
            
            result = await update_calendar_event(
                event_id=event_id,
                summary=update_data.get("summary"),
                start_time_str=start_time_str,
                duration_minutes=duration,
                location=update_data.get("location"),
                description=update_data.get("description"),
            )
            
            if not result or not result.get("ok"):
                error_msg = result.get("message", "Unknown error") if result else "No response"
                logger.error(f"Failed to update event {event_id}: {error_msg}")
                return None
            
            # Hole aktualisiertes Event
            data = result.get("data", {})
            updated_event_data = data.get("updated_event")
            
            if updated_event_data:
                return self._normalize_google_event(updated_event_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Calendar service error in update_event: {e}", exc_info=True)
            return None
    
    def _normalize_google_event(self, google_event: Dict[str, Any]) -> JanusCalendarEvent:
        """
        Normalisiert ein Google Calendar Event zu JanusCalendarEvent.
        
        Args:
            google_event: Rohes Google Calendar API Event
            
        Returns:
            JanusCalendarEvent
        """
        # Extrahiere Start/End Zeit
        start_data = google_event.get("start", {})
        end_data = google_event.get("end", {})
        
        # Prüfe auf ganztägiges Event
        is_all_day = "date" in start_data
        
        if is_all_day:
            # Ganztägiges Event
            start_str = start_data.get("date", "")
            end_str = end_data.get("date", "")
            start_dt = datetime.fromisoformat(start_str) if start_str else datetime.now(self.BERLIN_TZ)
            end_dt = datetime.fromisoformat(end_str) if end_str else start_dt
        else:
            # Zeitbasiertes Event
            start_str = start_data.get("dateTime", "")
            end_str = end_data.get("dateTime", "")
            
            if start_str:
                # Parse ISO 8601 mit oder ohne TZ
                if "Z" in start_str:
                    start_str = start_str.replace("Z", "+00:00")
                start_dt = datetime.fromisoformat(start_str)
            else:
                start_dt = datetime.now(self.BERLIN_TZ)
            
            if end_str:
                if "Z" in end_str:
                    end_str = end_str.replace("Z", "+00:00")
                end_dt = datetime.fromisoformat(end_str)
            else:
                end_dt = start_dt + timedelta(hours=1)
        
        # Extrahiere Teilnehmer
        attendees = []
        for attendee in google_event.get("attendees", []):
            email = attendee.get("email")
            if email:
                attendees.append(email)
        
        # Extrahiere Updated-Zeit
        updated_str = google_event.get("updated", "")
        try:
            if updated_str:
                if "Z" in updated_str:
                    updated_str = updated_str.replace("Z", "+00:00")
                last_modified = datetime.fromisoformat(updated_str)
            else:
                last_modified = datetime.utcnow()
        except ValueError:
            last_modified = datetime.utcnow()
        
        return JanusCalendarEvent(
            id=google_event.get("id", ""),
            title=google_event.get("summary", "(Kein Titel)"),
            description=google_event.get("description", ""),
            start=start_dt,
            end=end_dt,
            timezone=start_data.get("timeZone", "Europe/Berlin"),
            location=google_event.get("location"),
            attendees=attendees,
            source="google",
            external_id=google_event.get("id"),
            recurrence_rule=self._extract_recurrence(google_event),
            status=self._map_google_status(google_event.get("status", "confirmed")),
            sync_state="synced",
            last_modified=last_modified,
            is_all_day=is_all_day,
            color=self.SOURCE_COLORS["google"],
        )
    
    def _detect_conflicts(self, events: List[JanusCalendarEvent]) -> List[Dict[str, Any]]:
        """
        Erkennt zeitliche Überschneidungen zwischen Events.
        
        Args:
            events: Liste von JanusCalendarEvents
            
        Returns:
            Liste von Konflikt-Dictionaries
        """
        conflicts = []
        sorted_events = sorted(events, key=lambda e: e.start)
        
        for i, event_a in enumerate(sorted_events):
            for event_b in sorted_events[i + 1:]:
                # Prüfe Überschneidung
                if event_a.start < event_b.end and event_a.end > event_b.start:
                    # Berechne Überschneidung in Minuten
                    overlap_start = max(event_a.start, event_b.start)
                    overlap_end = min(event_a.end, event_b.end)
                    overlap_minutes = int((overlap_end - overlap_start).total_seconds() / 60)
                    
                    conflicts.append({
                        "event_a": event_a.id,
                        "event_b": event_b.id,
                        "overlap_minutes": overlap_minutes,
                    })
        
        return conflicts
    
    def _calculate_duration_minutes(self, start: datetime, end: datetime) -> int:
        """Berechnet Dauer in Minuten zwischen Start und Ende."""
        return int((end - start).total_seconds() / 60)
    
    def _extract_recurrence(self, google_event: Dict[str, Any]) -> Optional[str]:
        """Extrahiert Recurrence-Rule aus Google Event."""
        recurrence = google_event.get("recurrence", [])
        if recurrence:
            return recurrence[0] if isinstance(recurrence, list) else recurrence
        return None
    
    def _map_google_status(self, google_status: str) -> str:
        """Mappt Google Status zu Janus Status."""
        status_map = {
            "confirmed": "confirmed",
            "tentative": "tentative",
            "cancelled": "cancelled",
        }
        return status_map.get(google_status, "confirmed")


# Singleton-Instanz für einfachen Zugriff
_calendar_service = CalendarService()


async def get_calendar_service() -> CalendarService:
    """Factory-Funktion für CalendarService."""
    return _calendar_service
