# backend/data/schemas_calendar.py
"""
Pydantic Schemas für Janus Calendar Modal API.
Normalisiert Google Calendar Events in Janus-Format.
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class JanusCalendarEvent(BaseModel):
    """Normalisiertes Event-Format für Janus Calendar Modal."""
    
    id: str = Field(..., description="Einzigartige Event-ID (Google Event-ID)")
    title: str = Field(..., description="Event-Titel/Summary")
    description: Optional[str] = Field(None, description="Event-Beschreibung")
    start: datetime = Field(..., description="Startzeit (ISO 8601 mit TZ)")
    end: datetime = Field(..., description="Endzeit (ISO 8601 mit TZ)")
    timezone: str = Field("Europe/Berlin", description="Primäre Zeitzone")
    location: Optional[str] = Field(None, description="Veranstaltungsort")
    attendees: List[str] = Field(default_factory=list, description="Teilnehmer-Email-Liste")
    source: Literal["google", "outlook", "caldav", "janus-local"] = Field(
        "google", description="Kalender-Quelle"
    )
    external_id: Optional[str] = Field(None, description="Externe ID (z.B. Google Event-ID)")
    recurrence_rule: Optional[str] = Field(None, description="RRULE für wiederkehrende Events")
    status: Literal["confirmed", "tentative", "cancelled"] = Field(
        "confirmed", description="Event-Status"
    )
    sync_state: Literal["synced", "pending", "conflict"] = Field(
        "synced", description="Synchronisations-Status"
    )
    last_modified: datetime = Field(default_factory=datetime.utcnow, description="Letzte Änderung")
    is_all_day: bool = Field(False, description="Ganztägiges Event")
    color: Optional[str] = Field(None, description="Farb-Code für UI")
    html_link: Optional[str] = Field(None, description="Google Calendar HTML-Link zum Termin")
    hangout_link: Optional[str] = Field(None, description="Google Meet / Hangout-Link (falls vorhanden)")
    
    model_config = {"from_attributes": True}


class CalendarEventsResponse(BaseModel):
    """API Response für Events-Liste."""
    
    events: List[JanusCalendarEvent] = Field(default_factory=list)
    conflicts: List[dict] = Field(default_factory=list, description="Überschneidungen")
    sync_status: Literal["synced", "syncing", "error"] = Field("synced")
    total_count: int = Field(0, description="Gesamtzahl Events")


class CreateEventRequest(BaseModel):
    """Request-Body für Event-Erstellung."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Event-Titel")
    start: datetime = Field(..., description="Startzeit (ISO 8601)")
    end: datetime = Field(..., description="Endzeit (ISO 8601)")
    timezone: str = Field("Europe/Berlin", description="Zeitzone")
    location: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    attendees: List[str] = Field(default_factory=list)
    is_all_day: bool = Field(False)


class UpdateEventRequest(BaseModel):
    """Request-Body für Event-Update (alle Felder optional)."""
    
    title: Optional[str] = Field(None, max_length=500)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    timezone: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    attendees: Optional[List[str]] = None
    is_all_day: Optional[bool] = None


class CalendarConflict(BaseModel):
    """Konflikt zwischen zwei Events."""
    
    event_a: str = Field(..., description="ID des ersten Events")
    event_b: str = Field(..., description="ID des zweiten Events")
    overlap_minutes: int = Field(..., description="Überschneidung in Minuten")


class CalendarSyncStatus(BaseModel):
    """Synchronisations-Status Response."""
    
    status: Literal["synced", "syncing", "error", "disconnected"] = Field("synced")
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    source: Literal["google", "outlook", "caldav"] = Field("google")


class CalendarAIAction(BaseModel):
    """Einzelne Aktion aus AI Plan."""
    
    type: Literal["create", "update", "delete", "move"] = Field(...)
    event_id: Optional[str] = Field(None, description="Betroffenes Event (bei update/delete)")
    payload: dict = Field(default_factory=dict, description="Aktions-Details")


class CalendarAIPlan(BaseModel):
    """AI-generierter Plan mit Aktionen."""
    
    summary: str = Field(..., description="Beschreibung der vorgeschlagenen Änderungen")
    actions: List[CalendarAIAction] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = Field("low")


class CalendarAIPlanRequest(BaseModel):
    """Request für AI-Planung."""
    
    command: str = Field(..., min_length=1, max_length=1000, description="Natürlichsprachlicher Befehl")
    date: Optional[str] = Field(None, description="Zieldatum (ISO 8601)")
    context: dict = Field(default_factory=dict, description="Zusätzlicher Kontext")
