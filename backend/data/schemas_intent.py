"""
Pydantic schemas for the auxiliary intent action/subject classifier.
"""

from __future__ import annotations

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

IntentAction = Literal[
    "recall",
    "tell_fact",
    "mutate",
    "create",
    "search",
    "general",
    "clarify",
]

IntentSubject = Literal["self", "contact", "pet", "calendar", "none"]

IntentSource = Literal["aux_llm", "regex_fallback", "merged"]


class ActionSubjectResult(BaseModel):
    """Bounded auxiliary classifier result contract for intent M1."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    action: IntentAction
    subject: IntentSubject
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str = Field(...)
    source: IntentSource

    @field_validator("evidence", mode="before")
    @classmethod
    def _trim_evidence(cls, value: str) -> str:
        trimmed = (value or "").strip()
        return trimmed[:80]

    @classmethod
    def from_provider_payload(
        cls,
        payload: Any,
        *,
        source: IntentSource = "aux_llm",
    ) -> "ActionSubjectResult":
        """Parse and validate provider JSON into a bounded result."""
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            raise ValueError("provider payload must be a JSON object")

        return cls(
            action=payload["action"],
            subject=payload["subject"],
            confidence=float(payload["confidence"]),
            evidence=str(payload.get("evidence", "")),
            source=source,
        )

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "subject": self.subject,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


def validate_action_subject_payload(payload: Any) -> Optional[ActionSubjectResult]:
    """Fail closed on invalid provider output."""
    try:
        return ActionSubjectResult.from_provider_payload(payload)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        return None
