"""Intent auxiliary classifier contract (M1.1)."""

from __future__ import annotations

import json
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

IntentAction = Literal[
    "recall",
    "tell_fact",
    "mutate",
    "create",
    "search",
    "general",
    "clarify",
]

IntentSubject = Literal[
    "self",
    "contact",
    "pet",
    "calendar",
    "none",
]

IntentSource = Literal["aux_llm", "regex_fallback"]


class ActionSubjectResult(BaseModel):
    action: IntentAction
    subject: IntentSubject
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(max_length=80)
    source: IntentSource = "aux_llm"

    @field_validator("evidence", mode="before")
    @classmethod
    def _trim_evidence(cls, value: Any) -> str:
        return str(value or "")[:80]


def validate_action_subject_payload(
    payload: Union[str, dict[str, Any], None],
) -> Optional[ActionSubjectResult]:
    if payload is None:
        return None
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    try:
        return ActionSubjectResult(**payload)
    except Exception:
        return None
