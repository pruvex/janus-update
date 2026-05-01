# backend/api/routers/calendar.py
"""
Calendar API Router für Janus Calendar Modal.
REST-Endpoints für Event-CRUD und Sync-Operationen.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.data.database import get_db
from backend.data.schemas_calendar import (
    CalendarEventsResponse,
    CreateEventRequest,
    UpdateEventRequest,
    JanusCalendarEvent,
    CalendarAIPlanRequest,
    CalendarAIPlan,
    CalendarSyncStatus,
)
from backend.services.calendar import CalendarService, CalendarAIEngine

logger = logging.getLogger("janus_backend.calendar_router")

router = APIRouter(prefix="/calendar", tags=["calendar"])


# Singleton-Instanzen
_calendar_service = CalendarService()
_calendar_ai_engine = CalendarAIEngine()


@router.get("/events", response_model=CalendarEventsResponse)
async def get_events(
    start: Optional[str] = Query(None, description="Startdatum (ISO 8601 oder natürliche Sprache)"),
    end: Optional[str] = Query(None, description="Enddatum (ISO 8601 oder natürliche Sprache)"),
    days: int = Query(30, description="Anzahl Tage in Zukunft (Fallback)"),
    db: Session = Depends(get_db),
) -> CalendarEventsResponse:
    """
    Holt Events aus Google Calendar für den angegebenen Zeitraum.
    
    Returns:
        CalendarEventsResponse mit normalisierten Events und Konflikten.
    """
    try:
        logger.info(f"GET /events - start={start}, end={end}, days={days}")
        
        response = await _calendar_service.get_events(
            start_date=start,
            end_date=end,
            days_in_future=days,
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendar events: {str(e)}",
        )


@router.post("/events", response_model=JanusCalendarEvent, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: CreateEventRequest,
    db: Session = Depends(get_db),
) -> JanusCalendarEvent:
    """
    Erstellt ein neues Event in Google Calendar.
    
    Args:
        request: Event-Daten (Titel, Start, Ende, etc.)
        
    Returns:
        Erstelltes JanusCalendarEvent.
    """
    try:
        logger.info(f"POST /events - title={request.title}, start={request.start}")
        
        # Validierung: Endzeit muss nach Startzeit sein
        if request.end <= request.start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            )
        
        result = await _calendar_service.create_event(request)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create calendar event",
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}",
        )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    """
    Löscht ein Event aus Google Calendar.
    
    Args:
        event_id: Google Event-ID
    """
    try:
        logger.info(f"DELETE /events/{event_id}")
        
        success = await _calendar_service.delete_event(event_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete calendar event",
            )
        
        # 204 No Content - kein Body
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}",
        )


@router.put("/events/{event_id}", response_model=JanusCalendarEvent)
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    db: Session = Depends(get_db),
) -> JanusCalendarEvent:
    """
    Aktualisiert ein existierendes Event.
    
    Args:
        event_id: Google Event-ID
        request: Zu ändernde Felder
        
    Returns:
        Aktualisiertes JanusCalendarEvent.
    """
    try:
        logger.info(f"PUT /events/{event_id}")
        
        # Validierung: Wenn beide Zeiten angegeben, Endzeit nach Startzeit
        if request.start is not None and request.end is not None:
            if request.end <= request.start:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time",
                )
        
        result = await _calendar_service.update_event(event_id, request)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update calendar event",
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}",
        )


@router.get("/sync/status", response_model=CalendarSyncStatus)
async def get_sync_status(
    db: Session = Depends(get_db),
) -> CalendarSyncStatus:
    """
    Gibt den aktuellen Synchronisations-Status zurück.
    
    Phase 1: Einfacher Status (immer "synced").
    Phase 3: Echter Delta-Sync-Status.
    """
    try:
        # Phase 1: Platzhalter
        return CalendarSyncStatus(
            status="synced",
            last_sync=datetime.utcnow(),
            source="google",
        )
        
    except Exception as e:
        logger.error(f"Error in get_sync_status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}",
        )


@router.post("/ai/plan", response_model=CalendarAIPlan)
async def generate_ai_plan(
    request: CalendarAIPlanRequest,
    db: Session = Depends(get_db),
) -> CalendarAIPlan:
    """
    Generiert einen AI-Plan basierend auf natürlichsprachlichem Befehl.
    
    Phase 1: Platzhalter.
    Phase 4: Vollständige Implementation.
    """
    try:
        logger.info(f"POST /ai/plan - command={request.command[:50]}...")
        
        # Hole aktuelle Events als Kontext
        events_response = await _calendar_service.get_events(
            days_in_future=7,
            start_date=request.date if request.date else None,
        )
        
        plan = await _calendar_ai_engine.generate_plan(
            command=request.command,
            events=events_response.events,
            date=request.date,
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error in generate_ai_plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI plan: {str(e)}",
        )
