# backend/api/routers/calendar.py
"""
Calendar API Router für Janus Calendar Modal.
REST-Endpoints für Event-CRUD und Sync-Operationen.
"""

import inspect
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.data.database import get_db
from backend.data.schemas import MutationProposal
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
from backend.services.calendar.calendar_memory import SNAPSHOT_DAYS, upsert_calendar_snapshot

logger = logging.getLogger("janus_backend.calendar_router")

router = APIRouter(prefix="/calendar", tags=["calendar"])


# Singleton-Instanzen
_calendar_service = CalendarService()
_calendar_ai_engine = CalendarAIEngine()


def _ai_plan_context_window(target_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Erweitertes Fenster um target_date (YYYY-MM-DD) für LLM-Kontext."""
    if not target_date or not str(target_date).strip():
        return None, None
    ds = str(target_date).strip()
    try:
        d = datetime.strptime(ds, "%Y-%m-%d")
    except ValueError:
        return None, None
    start = (d - timedelta(days=7)).strftime("%Y-%m-%d")
    end = (d + timedelta(days=14)).strftime("%Y-%m-%d")
    return start, end


async def _refresh_calendar_memory_snapshot(db: Session) -> Dict[str, Any]:
    """Refresh the compact calendar snapshot without changing API response shapes."""
    result = _calendar_service.get_events(days_in_future=SNAPSHOT_DAYS)
    if inspect.isawaitable(result):
        result = await result
    else:
        logger.debug("Calendar memory refresh skipped: get_events mock/result is not awaitable.")
        return {}
    if getattr(result, "sync_status", None) != "synced":
        return {}
    return upsert_calendar_snapshot(db, getattr(result, "events", []) or [])


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
        if response.sync_status == "synced":
            upsert_calendar_snapshot(db, response.events)
        
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
        await _refresh_calendar_memory_snapshot(db)
        
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
        await _refresh_calendar_memory_snapshot(db)
        
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
        await _refresh_calendar_memory_snapshot(db)
        
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


@router.post("/sync/memory")
async def refresh_memory_snapshot(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Erzwingt einen Full-Replace des Kalender-Memory-Spiegels.

    Der Live-Kalender bleibt die Quelle der Wahrheit; dieser Endpoint aktualisiert
    nur den kompakten Kontext-Cache für Chat-Antworten.
    """
    try:
        snapshot = await _refresh_calendar_memory_snapshot(db)
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar snapshot could not be refreshed",
            )
        return {
            "status": "ok",
            "event_count": len(snapshot.get("events", [])),
            "generated_at": snapshot.get("generated_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_memory_snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh calendar memory snapshot: {str(e)}",
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
        start_d, end_d = _ai_plan_context_window(request.date)
        events_response = await _calendar_service.get_events(
            start_date=start_d or (request.date if request.date else None),
            end_date=end_d,
            days_in_future=21 if not request.date else 30,
        )
        extra: Dict[str, Any] = dict(request.context) if isinstance(request.context, dict) else {}
        plan = await _calendar_ai_engine.generate_plan(
            command=request.command,
            events=events_response.events,
            date=request.date,
            extra_context=extra,
        )
        return plan
        
    except Exception as e:
        logger.error(f"Error in generate_ai_plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI plan: {str(e)}",
        )


# ── TASK-067: In-memory MutationProposal (human-in-the-loop) — API-Hooks ───


@router.get(
    "/mutation-proposals/pending/{chat_id}",
    response_model=None,
    responses={404: {"description": "No pending proposal for this chat"}},
)
async def get_pending_mutation_proposal_api(chat_id: int) -> Dict[str, Any]:
    """Debug/Admin: Pending-Kalendermutation für einen Chat auslesen."""
    from backend.services.calendar import mutation_guard_store as mgs

    p = mgs.get_pending_mutation_proposal(chat_id)
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending mutation proposal for this chat",
        )
    return p.model_dump(mode="json")


@router.delete("/mutation-proposals/pending/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pending_mutation_proposal_api(chat_id: int) -> Response:
    """Debug/Admin: Ausstehendes Proposal verwerfen (kein Google PATCH)."""
    from backend.services.calendar import mutation_guard_store as mgs

    mgs.clear_pending_mutation_proposal(chat_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/mutation-proposals/stage", response_model=MutationProposal)
async def stage_mutation_proposal_api(proposal: MutationProposal) -> MutationProposal:
    """Modal-/Test-Client: Proposal in denselben Store legen wie der Chat-Tool-Guard."""
    from backend.services.calendar import mutation_guard_store as mgs

    cid = int(proposal.chat_id)
    mgs.set_pending_mutation_proposal(cid, proposal)
    mgs.log_proposal_created(
        proposal.proposal_id,
        chat_id=cid,
        event_id=str(proposal.event_id),
    )
    return proposal
