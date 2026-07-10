from __future__ import annotations

import json
from typing import Any

from backend.services.workflow.routine_schema import RoutineStep

_SUCCESS_STATUSES = {"ok", "dry_run_success", "success", "completed"}


def extract_routine_steps(trace_payload: Any) -> list[RoutineStep]:
    raw_steps = _coerce_trace_steps(trace_payload)
    extracted_steps: list[RoutineStep] = []
    order = 1
    for item in raw_steps:
        if not _is_success(item):
            continue
        skill_id = _extract_skill_id(item)
        if not skill_id:
            continue
        args = item.get("args") or item.get("arguments_json") or item.get("_arguments_json") or {}
        if not isinstance(args, dict):
            args = {}
        arg_bindings = item.get("arg_bindings") or {}
        if not isinstance(arg_bindings, dict):
            arg_bindings = {}
        extracted_steps.append(
            RoutineStep(order=order, skill_id=skill_id, args=dict(args), arg_bindings=dict(arg_bindings))
        )
        order += 1
    return extracted_steps


def _extract_skill_id(item: dict[str, Any]) -> str:
    raw = str(item.get("skill_id") or item.get("_skill_id") or item.get("name") or "").strip()
    if raw == "calendar_list_events":
        return "calendar.list_events"
    if raw == "system_weather":
        return "system.weather"
    return raw


def _coerce_trace_steps(trace_payload: Any) -> list[dict[str, Any]]:
    if isinstance(trace_payload, list):
        return [item for item in trace_payload if isinstance(item, dict)]
    if isinstance(trace_payload, dict):
        if isinstance(trace_payload.get("tool_calls"), list):
            return [item for item in trace_payload["tool_calls"] if isinstance(item, dict)]
        if isinstance(trace_payload.get("steps"), list):
            return [item for item in trace_payload["steps"] if isinstance(item, dict)]
    return []


def iter_trace_items(trace_payload: Any) -> list[dict[str, Any]]:
    return _coerce_trace_steps(trace_payload)


def _parse_content_payload(item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("_raw_content") or item.get("content")
    if raw is None:
        return {}
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _status_is_success(status: str) -> bool:
    return str(status or "").strip().lower() in _SUCCESS_STATUSES


def _payload_indicates_success(payload: dict[str, Any]) -> bool:
    if not payload:
        return False
    if "success" in payload:
        return bool(payload.get("success"))
    if _status_is_success(str(payload.get("status") or "")):
        return True
    return False


def _is_success(item: dict[str, Any]) -> bool:
    if "success" in item:
        return bool(item.get("success"))
    top_status = str(item.get("status") or "").strip().lower()
    if top_status:
        return _status_is_success(top_status)
    return _payload_indicates_success(_parse_content_payload(item))
