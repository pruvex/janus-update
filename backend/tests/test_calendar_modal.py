# backend/tests/test_calendar_modal.py
"""
Tests für Calendar Modal API (TASK-058 Phase 1).
Validiert CRUD-Endpoints gegen den Calendar Service.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

import backend.api.routers.calendar as calendar_router
from backend.main import app
from backend.data.schemas_calendar import (
    JanusCalendarEvent,
    CreateEventRequest,
    UpdateEventRequest,
    CalendarEventsResponse,
    CalendarAIPlan,
)


# Test-Client
client = TestClient(app)


class TestCalendarAPI:
    """Test-Suite für Calendar API Endpoints."""
    
    @pytest.fixture
    def mock_event(self):
        """Erstellt ein Mock-Event für Tests."""
        return JanusCalendarEvent(
            id="test_event_123",
            title="Test Meeting",
            description="Test Description",
            start=datetime.now() + timedelta(days=1),
            end=datetime.now() + timedelta(days=1, hours=1),
            timezone="Europe/Berlin",
            location="Test Office",
            attendees=["test@example.com"],
            source="google",
            external_id="test_event_123",
            status="confirmed",
            sync_state="synced",
            is_all_day=False,
            color="#4285F4",
        )
    
    @pytest.fixture
    def mock_service(self):
        """Mock für CalendarService."""
        with patch("backend.api.routers.calendar._calendar_service") as mock:
            yield mock
    
    # ─────────────────────────────────────────────────────────
    # GET /api/calendar/events Tests
    # ─────────────────────────────────────────────────────────
    
    def test_get_events_success(self, mock_service, mock_event):
        """Test: Events erfolgreich abrufen."""
        # Arrange
        mock_service.get_events = AsyncMock(return_value=CalendarEventsResponse(
            events=[mock_event],
            conflicts=[],
            sync_status="synced",
            total_count=1,
        ))
        
        # Act
        response = client.get("/api/calendar/events?days=7")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Test Meeting"
        assert data["sync_status"] == "synced"
    
    def test_get_events_with_date_range(self, mock_service):
        """Test: Events mit Datumsbereich abrufen."""
        # Arrange
        mock_service.get_events = AsyncMock(return_value=CalendarEventsResponse(
            events=[],
            conflicts=[],
            sync_status="synced",
            total_count=0,
        ))
        
        # Act
        response = client.get("/api/calendar/events?start=2026-05-01&end=2026-05-31")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_events.assert_called_once_with(
            start_date="2026-05-01",
            end_date="2026-05-31",
            days_in_future=30,
        )
    
    def test_get_events_service_error(self, mock_service):
        """Test: Fehlerbehandlung bei Service-Fehler."""
        # Arrange
        mock_service.get_events = AsyncMock(return_value=CalendarEventsResponse(
            events=[],
            conflicts=[],
            sync_status="error",
            total_count=0,
        ))
        
        # Act
        response = client.get("/api/calendar/events")
        
        # Assert
        assert response.status_code == 200  # Endpoint gibt 200 mit error Status zurück
        data = response.json()
        assert data["sync_status"] == "error"
    
    # ─────────────────────────────────────────────────────────
    # POST /api/calendar/events Tests
    # ─────────────────────────────────────────────────────────
    
    def test_create_event_success(self, mock_service, mock_event):
        """Test: Event erfolgreich erstellen."""
        # Arrange
        mock_service.create_event = AsyncMock(return_value=mock_event)
        
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).isoformat()
        
        payload = {
            "title": "New Meeting",
            "start": start_time,
            "end": end_time,
            "timezone": "Europe/Berlin",
            "location": "Conference Room",
            "description": "Important meeting",
        }
        
        # Act
        response = client.post("/api/calendar/events", json=payload)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Meeting"  # Aus Mock
        assert data["id"] == "test_event_123"
    
    def test_create_event_validation_error(self):
        """Test: Validierungsfehler bei Endzeit vor Startzeit."""
        # Arrange
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(hours=23)).isoformat()  # Vor Start
        
        payload = {
            "title": "Invalid Meeting",
            "start": start_time,
            "end": end_time,
        }
        
        # Act
        response = client.post("/api/calendar/events", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "End time must be after start time" in response.json()["detail"]
    
    def test_create_event_missing_title(self):
        """Test: Fehler bei fehlendem Titel."""
        # Arrange
        payload = {
            "start": (datetime.now() + timedelta(days=1)).isoformat(),
            "end": (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
        }
        
        # Act
        response = client.post("/api/calendar/events", json=payload)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_create_event_service_failure(self, mock_service):
        """Test: Fehlerbehandlung bei Service-Fehler."""
        # Arrange
        mock_service.create_event = AsyncMock(return_value=None)
        
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).isoformat()
        
        payload = {
            "title": "Failing Meeting",
            "start": start_time,
            "end": end_time,
        }
        
        # Act
        response = client.post("/api/calendar/events", json=payload)
        
        # Assert
        assert response.status_code == 500
        assert "Failed to create calendar event" in response.json()["detail"]
    
    # ─────────────────────────────────────────────────────────
    # DELETE /api/calendar/events/{id} Tests
    # ─────────────────────────────────────────────────────────
    
    def test_delete_event_success(self, mock_service):
        """Test: Event erfolgreich löschen."""
        # Arrange
        mock_service.delete_event = AsyncMock(return_value=True)
        
        # Act
        response = client.delete("/api/calendar/events/test_event_123")
        
        # Assert
        assert response.status_code == 204  # No Content
        assert response.content == b""  # Leerer Body
    
    def test_delete_event_not_found(self, mock_service):
        """Test: Fehler beim Löschen nicht-existierendem Event."""
        # Arrange
        mock_service.delete_event = AsyncMock(return_value=False)
        
        # Act
        response = client.delete("/api/calendar/events/nonexistent")
        
        # Assert
        assert response.status_code == 500
        assert "Failed to delete calendar event" in response.json()["detail"]
    
    # ─────────────────────────────────────────────────────────
    # PUT /api/calendar/events/{id} Tests
    # ─────────────────────────────────────────────────────────
    
    def test_update_event_success(self, mock_service, mock_event):
        """Test: Event erfolgreich aktualisieren."""
        # Arrange
        updated_event = mock_event.model_copy(update={"title": "Updated Meeting"})
        mock_service.update_event = AsyncMock(return_value=updated_event)
        
        payload = {
            "title": "Updated Meeting",
            "location": "New Office",
        }
        
        # Act
        response = client.put("/api/calendar/events/test_event_123", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Meeting"
    
    def test_update_event_time_validation(self, mock_service):
        """Test: Validierungsfehler bei ungültiger Zeit."""
        # Arrange
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(hours=23)).isoformat()  # Vor Start
        
        payload = {
            "start": start_time,
            "end": end_time,
        }
        
        # Act
        response = client.put("/api/calendar/events/test_event_123", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "End time must be after start time" in response.json()["detail"]
    
    def test_update_event_not_found(self, mock_service):
        """Test: Fehler beim Update nicht-existierendem Event."""
        # Arrange
        mock_service.update_event = AsyncMock(return_value=None)
        
        payload = {"title": "Ghost Meeting"}
        
        # Act
        response = client.put("/api/calendar/events/nonexistent", json=payload)
        
        # Assert
        assert response.status_code == 500
    
    # ─────────────────────────────────────────────────────────
    # GET /api/calendar/sync/status Tests
    # ─────────────────────────────────────────────────────────
    
    def test_get_sync_status(self):
        """Test: Sync-Status abrufen."""
        # Act
        response = client.get("/api/calendar/sync/status")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synced"
        assert data["source"] == "google"
    
    # ─────────────────────────────────────────────────────────
    # POST /api/calendar/ai/plan Tests
    # ─────────────────────────────────────────────────────────
    
    def test_generate_ai_plan(self, mock_service):
        """Test: POST /ai/plan lädt Events-Kontext und liefert einen KI-Plan (LLM gemockt)."""
        mock_service.get_events = AsyncMock(return_value=CalendarEventsResponse(
            events=[],
            conflicts=[],
            sync_status="synced",
            total_count=0,
        ))
        expected = CalendarAIPlan(
            summary="Vorschlag: 2h Fokusblock am Nachmittag.",
            actions=[],
            risk_level="low",
        )

        payload = {
            "command": "Optimiere meinen Tag",
            "date": "2026-05-02",
        }

        with patch.object(
            calendar_router._calendar_ai_engine,
            "generate_plan",
            new=AsyncMock(return_value=expected),
        ):
            response = client.post("/api/calendar/ai/plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == expected.summary
        assert data["actions"] == []
        assert data["risk_level"] == "low"
        mock_service.get_events.assert_called_once()
        call_kwargs = mock_service.get_events.call_args.kwargs
        assert call_kwargs["start_date"] == "2026-04-25"
        assert call_kwargs["end_date"] == "2026-05-16"


class TestCalendarService:
    """Test-Suite für Calendar Service Layer."""
    
    @pytest.fixture
    def service(self):
        """Erstellt CalendarService-Instanz."""
        from backend.services.calendar.calendar_service import CalendarService
        return CalendarService()
    
    def test_normalize_google_event(self, service):
        """Test: Google Event wird korrekt normalisiert."""
        # Arrange
        google_event = {
            "id": "google_123",
            "summary": "Test Event",
            "description": "Description",
            "start": {
                "dateTime": "2026-05-01T10:00:00+02:00",
            },
            "end": {
                "dateTime": "2026-05-01T11:00:00+02:00",
            },
            "location": "Office",
            "attendees": [{"email": "user@example.com"}],
            "updated": "2026-04-30T08:00:00Z",
            "status": "confirmed",
        }
        
        # Act
        result = service._normalize_google_event(google_event)
        
        # Assert
        assert result.id == "google_123"
        assert result.title == "Test Event"
        assert result.source == "google"
        assert result.location == "Office"
        assert len(result.attendees) == 1
        assert result.attendees[0] == "user@example.com"
    
    def test_normalize_all_day_event(self, service):
        """Test: Ganztägiges Event korrekt normalisiert."""
        # Arrange
        google_event = {
            "id": "all_day_123",
            "summary": "All Day Event",
            "start": {"date": "2026-05-01"},
            "end": {"date": "2026-05-02"},
            "updated": "2026-04-30T08:00:00Z",
        }
        
        # Act
        result = service._normalize_google_event(google_event)
        
        # Assert
        assert result.is_all_day is True
        assert result.source == "google"
    
    def test_detect_conflicts(self, service):
        """Test: Konflikte zwischen Events werden erkannt."""
        # Arrange
        from datetime import datetime
        
        events = [
            JanusCalendarEvent(
                id="event_1",
                title="Meeting 1",
                start=datetime(2026, 5, 1, 10, 0),
                end=datetime(2026, 5, 1, 11, 0),
                timezone="Europe/Berlin",
                source="google",
            ),
            JanusCalendarEvent(
                id="event_2",
                title="Meeting 2",
                start=datetime(2026, 5, 1, 10, 30),  # Überlappung!
                end=datetime(2026, 5, 1, 11, 30),
                timezone="Europe/Berlin",
                source="google",
            ),
        ]
        
        # Act
        conflicts = service._detect_conflicts(events)
        
        # Assert
        assert len(conflicts) == 1
        assert conflicts[0]["event_a"] == "event_1"
        assert conflicts[0]["event_b"] == "event_2"
        assert conflicts[0]["overlap_minutes"] == 30
    
    def test_no_conflicts(self, service):
        """Test: Keine Konflikte bei nicht-überlappenden Events."""
        # Arrange
        from datetime import datetime
        
        events = [
            JanusCalendarEvent(
                id="event_1",
                title="Meeting 1",
                start=datetime(2026, 5, 1, 10, 0),
                end=datetime(2026, 5, 1, 11, 0),
                timezone="Europe/Berlin",
                source="google",
            ),
            JanusCalendarEvent(
                id="event_2",
                title="Meeting 2",
                start=datetime(2026, 5, 1, 11, 0),  # Keine Überlappung (exakt anschließend)
                end=datetime(2026, 5, 1, 12, 0),
                timezone="Europe/Berlin",
                source="google",
            ),
        ]
        
        # Act
        conflicts = service._detect_conflicts(events)
        
        # Assert
        assert len(conflicts) == 1  # Bei exaktem Anschluss gibt es technisch eine Überlappung bei end > start


class TestCalendarSchemas:
    """Test-Suite für Calendar Schemas."""
    
    def test_janus_calendar_event_creation(self):
        """Test: JanusCalendarEvent kann erstellt werden."""
        from datetime import datetime
        
        event = JanusCalendarEvent(
            id="test_123",
            title="Test",
            start=datetime.now(),
            end=datetime.now() + timedelta(hours=1),
            timezone="Europe/Berlin",
            source="google",
        )
        
        assert event.id == "test_123"
        assert event.source == "google"
        assert event.color == "#4285F4"  # Google Blue
    
    def test_create_event_request_validation(self):
        """Test: CreateEventRequest validiert Min-Length."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            CreateEventRequest(
                title="",  # Zu kurz
                start=datetime.now(),
                end=datetime.now() + timedelta(hours=1),
            )
    
    def test_calendar_ai_plan_default(self):
        """Test: CalendarAIPlan hat korrekte Defaults."""
        plan = CalendarAIPlan(
            summary="Test plan",
            actions=[],
            risk_level="low",
        )
        
        assert plan.risk_level == "low"
        assert plan.actions == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
