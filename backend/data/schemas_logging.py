"""
Pydantic models for strict validation of logging events.
Schema matches the Supabase logs_raw table exactly.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class LogEventBase(BaseModel):
    """Base model for log events with common fields."""
    model_config = ConfigDict(use_enum_values=True)

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    provider: Optional[str] = Field(default=None, description="LLM provider (e.g., 'openai', 'google')")
    model: Optional[str] = Field(default=None, description="Model name")
    skill: Optional[str] = Field(default=None, description="Skill/feature name")
    event_type: str = Field(..., description="Type of event (e.g., 'request', 'response', 'error')")
    status: Optional[str] = Field(default=None, description="Event status (e.g., 'success', 'failure')")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Event payload/data")
    latency_ms: Optional[int] = Field(default=None, description="Latency in milliseconds")


class LogEventCreate(LogEventBase):
    """
    Model for creating a new log event.
    All fields are optional except event_type.
    """
    pass


class LogEvent(LogEventBase):
    """
    Complete log event model with database ID.
    Represents a row in the logs_raw table.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique event identifier")

    model_config = ConfigDict(from_attributes=True)


class LogEventBatch(BaseModel):
    """
    Model for batch insertion of log events.
    """
    events: list[LogEventCreate] = Field(default_factory=list, description="List of log events")

    def add_event(self, event: LogEventCreate) -> None:
        """Add an event to the batch."""
        self.events.append(event)

    def is_empty(self) -> bool:
        """Check if the batch is empty."""
        return len(self.events) == 0

    def size(self) -> int:
        """Get the number of events in the batch."""
        return len(self.events)
