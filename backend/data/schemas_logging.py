"""
Pydantic models for strict validation of logging events.
Schema matches the Supabase logs_raw table exactly.
"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class LogEventPayload(BaseModel):
    """Strict payload model for log events with enforced fields."""
    model_config = ConfigDict(extra='allow')  # Allow extra fields for flexibility
    
    input_hash: Optional[str] = Field(default=None, description="Hash of input data for deduplication")
    output_summary: Optional[str] = Field(default=None, description="Summary of output/result")
    error_code: Optional[str] = Field(default=None, description="Error code if status is error")


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
    trace_id: Optional[str] = Field(default=None, description="Trace identifier for request tracking")


class LogEventCreate(LogEventBase):
    """
    Model for creating a new log event.
    All fields are optional except event_type.
    """
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique event identifier for UPSERT idempotency")


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


class InsightCreate(BaseModel):
    """
    Model for creating a new insight record.
    Schema matches the Supabase logs_insights table.
    """
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique insight identifier")
    skill: str = Field(..., description="Skill name")
    model: str = Field(..., description="Model name")
    calls: int = Field(..., description="Total number of calls")
    error_rate: float = Field(..., description="Error rate (0.0 to 1.0)")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds")
    patterns: List[str] = Field(default_factory=list, description="Detected patterns")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of analysis")
    time_window_hours: int = Field(default=1, description="Time window in hours used for analysis")


class Insight(InsightCreate):
    """
    Complete insight model with database ID.
    Represents a row in the logs_insights table.
    """
    id: str = Field(..., description="Unique insight identifier")

    model_config = ConfigDict(from_attributes=True)


class ActionCreate(BaseModel):
    """
    Model for creating a new action record.
    Schema matches the Supabase logs_actions table.
    """
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique action identifier")
    skill: str = Field(..., description="Skill name")
    model: str = Field(..., description="Model name")
    action_type: str = Field(..., description="Type of action (SCALE_UP, MODEL_SWITCH, etc.)")
    priority: str = Field(..., description="Priority level (LOW, MEDIUM, HIGH, CRITICAL)")
    reason: str = Field(..., description="Reason for action")
    current_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold that triggered action")
    recommendation: str = Field(..., description="Specific recommendation")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of action generation")
    time_window_hours: int = Field(default=1, description="Time window in hours used for analysis")


class Action(ActionCreate):
    """
    Complete action model with database ID.
    Represents a row in the logs_actions table.
    """
    id: str = Field(..., description="Unique action identifier")

    model_config = ConfigDict(from_attributes=True)
