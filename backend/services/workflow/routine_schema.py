from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RoutineStep(BaseModel):
    order: int = Field(..., ge=1)
    skill_id: str
    args: dict[str, Any] = Field(default_factory=dict)
    arg_bindings: dict[str, str] = Field(default_factory=dict)
    output_snapshot: str | None = None
    snapshot_query: str | None = None

    @field_validator("skill_id")
    @classmethod
    def _skill_id_must_not_be_blank(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("skill_id must not be blank")
        return normalized


class RoutineStepsDocument(BaseModel):
    version: int = 1
    steps: list[RoutineStep]

    @field_validator("steps")
    @classmethod
    def _steps_must_not_be_empty(cls, value: list[RoutineStep]) -> list[RoutineStep]:
        if not value:
            raise ValueError("steps must not be empty")
        return value


class RoutineCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    name: str
    description: str | None = None
    trigger_phrases: list[str] = Field(default_factory=list)
    steps: list[RoutineStep]
    source_chat_id: int | None = None
    source_turn_id: int | None = None
    user_approved: bool = False
    offer_state: str = "saved"

    @field_validator("name")
    @classmethod
    def _name_must_not_be_blank(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("name must not be blank")
        return normalized


class RoutineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_phrases: list[str] | None = None
    user_approved: bool | None = None
    offer_state: str | None = None


def normalize_trigger_phrases(trigger_phrases: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in trigger_phrases:
        phrase = str(value or "").strip()
        if not phrase:
            continue
        folded = phrase.casefold()
        if folded in seen:
            continue
        seen.add(folded)
        normalized.append(phrase)
    return normalized


def build_step_fingerprint(steps: list[RoutineStep]) -> str:
    normalized_parts: list[str] = []
    for step in sorted(steps, key=lambda item: item.order):
        arg_keys = ",".join(sorted(str(key) for key in step.args.keys()))
        normalized_parts.append(f"{step.skill_id}:{arg_keys}")
    material = "|".join(normalized_parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def steps_share_promotion_equivalence(
    left: list[RoutineStep],
    right: list[RoutineStep],
) -> bool:
    """True when two traces are safe to treat as the same passive candidate."""
    if not left or not right:
        return False
    if build_step_fingerprint(left) == build_step_fingerprint(right):
        return True

    left_skills = {step.skill_id for step in left}
    right_skills = {step.skill_id for step in right}
    if left_skills != right_skills:
        return False

    if left_skills == {"calendar.list_events", "system.routing"}:
        return _calendar_routing_steps_equivalent(left, right)
    return False


def _calendar_routing_steps_equivalent(
    left: list[RoutineStep],
    right: list[RoutineStep],
) -> bool:
    left_calendar = _find_step(left, "calendar.list_events")
    right_calendar = _find_step(right, "calendar.list_events")
    left_routing = _find_step(left, "system.routing")
    right_routing = _find_step(right, "system.routing")
    if not left_calendar or not right_calendar or not left_routing or not right_routing:
        return False

    left_calendar_key = _normalize_calendar_constraint(left_calendar.args)
    right_calendar_key = _normalize_calendar_constraint(right_calendar.args)
    if not left_calendar_key or not right_calendar_key or left_calendar_key != right_calendar_key:
        return False

    left_route_key = _normalize_routing_constraint(left_routing.args)
    right_route_key = _normalize_routing_constraint(right_routing.args)
    if not left_route_key or not right_route_key:
        return False
    return left_route_key == right_route_key


def _find_step(steps: list[RoutineStep], skill_id: str) -> RoutineStep | None:
    return next((step for step in steps if step.skill_id == skill_id), None)


def _normalize_calendar_constraint(args: dict[str, Any]) -> str | None:
    if not isinstance(args, dict):
        return None

    days_in_future = args.get("days_in_future")
    if isinstance(days_in_future, int):
        return f"offset:{days_in_future}"
    if isinstance(days_in_future, str) and days_in_future.strip().lstrip("-").isdigit():
        return f"offset:{int(days_in_future.strip())}"

    range_value = _normalize_relative_date_token(args.get("range"))
    if range_value:
        return range_value

    date_str_value = _normalize_relative_date_token(args.get("date_str"))
    if date_str_value:
        return date_str_value

    start_date = _normalize_date_value(args.get("start_date"))
    end_date = _normalize_date_value(args.get("end_date"))
    if start_date and end_date and start_date != end_date:
        return f"between:{start_date}|{end_date}"
    if start_date:
        return start_date
    if end_date:
        return end_date
    return None


def _normalize_date_value(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    relative = _normalize_relative_date_token(text)
    if relative:
        return relative
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return f"date:{text.casefold()}"

    delta_days = (parsed - date.today()).days
    if -1 <= delta_days <= 2:
        return f"offset:{delta_days}"
    return f"date:{parsed.isoformat()}"


def _normalize_relative_date_token(value: Any) -> str | None:
    text = str(value or "").strip().casefold()
    if not text:
        return None
    aliases = {
        "today": 0,
        "heute": 0,
        "tomorrow": 1,
        "morgen": 1,
        "day after tomorrow": 2,
        "uebermorgen": 2,
        "übermorgen": 2,
        "yesterday": -1,
        "gestern": -1,
    }
    offset = aliases.get(text)
    if offset is None:
        return None
    return f"offset:{offset}"


def _normalize_routing_constraint(args: dict[str, Any]) -> str | None:
    if not isinstance(args, dict):
        return None

    origin = _extract_first_string(args, "origin", "from_city", "from", "source")
    destination = _extract_first_string(args, "destination", "to_city", "to", "target")
    if not origin or not destination:
        return None

    mode = _extract_first_string(args, "mode", "travel_mode") or "driving"
    return f"{_normalize_place(origin)}->{_normalize_place(destination)}|mode:{mode.casefold()}"


def _extract_first_string(args: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_place(value: str) -> str:
    normalized = str(value or "").casefold().strip()
    normalized = normalized.replace("deutschland", "").replace("germany", "")
    normalized = " ".join(normalized.replace(",", " ").split())
    return normalized
