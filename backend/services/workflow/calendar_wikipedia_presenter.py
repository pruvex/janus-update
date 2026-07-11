from __future__ import annotations

import json
import re
from typing import Any, Callable

from backend.services.workflow.routine_schema import RoutineStep

CALENDAR_WIKIPEDIA_SKILL_IDS = frozenset({"calendar.list_events", "system.wikipedia_summary"})
_PASSIVE_HINT_RE = re.compile(
    r"\n\nIch habe (?:dafuer eine passende Routine gespeichert|gerade einen wiederverwendbaren Ablauf erkannt)\b.*",
    re.IGNORECASE | re.DOTALL,
)
_LEGACY_TRUNCATION_SUFFIX_RE = re.compile(r"\.\.\.\s*\[Text für lokales LLM gekürzt\.\]")


def normalize_wikipedia_query(value: str | None) -> str:
    return " ".join(str(value or "").casefold().split())


def wikipedia_queries_match(left: str | None, right: str | None) -> bool:
    left_norm = normalize_wikipedia_query(left)
    right_norm = normalize_wikipedia_query(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True
    return left_norm in right_norm or right_norm in left_norm


def is_calendar_wikipedia_combo_steps(steps: list[RoutineStep] | list[dict[str, Any]]) -> bool:
    skill_ids: set[str] = set()
    for step in steps:
        if isinstance(step, RoutineStep):
            skill_ids.add(step.skill_id)
        elif isinstance(step, dict):
            skill_id = str(step.get("skill_id") or "").strip()
            if skill_id:
                skill_ids.add(skill_id)
    return skill_ids == CALENDAR_WIKIPEDIA_SKILL_IDS


def sanitize_wikipedia_display_text(text: str) -> str:
    return _LEGACY_TRUNCATION_SUFFIX_RE.sub("... (Auszug)", str(text or "")).strip()


def _strip_response_hints(text: str) -> str:
    return _PASSIVE_HINT_RE.sub("", str(text or "")).strip()


def _is_generic_llm_fallback(text: str) -> bool:
    normalized = str(text or "").casefold()
    return (
        "ich konnte diesmal keine stabile antwort erzeugen" in normalized
        or (
            "es ist ein fehler aufgetreten:" in normalized
            and "provider:" in normalized
            and "direkt noch einmal" in normalized
        )
    )


def _iter_tool_payloads(tool_results: Any) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    payloads: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for item in tool_results or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower()
        skill_id = str(item.get("_skill_id") or item.get("skill_id") or "").strip().lower()
        normalized = skill_id or name
        wrapper_args = item.get("args") if isinstance(item.get("args"), dict) else {}
        result = item.get("result") if isinstance(item.get("result"), dict) else None
        if result is not None:
            payload = result
        else:
            raw = item.get("_raw_content") or item.get("content") or "{}"
            try:
                payload = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
            except Exception:
                continue
        if isinstance(payload, dict):
            payloads.append((normalized, payload, wrapper_args))
    return payloads


def calendar_and_wikipedia_tools_ok(tool_results: Any) -> bool:
    saw_calendar = False
    saw_wikipedia = False
    for normalized, payload, _args in _iter_tool_payloads(tool_results):
        if payload.get("status") != "ok":
            continue
        if normalized in {"calendar.list_events", "calendar_list_events"}:
            saw_calendar = True
        elif normalized in {"system.wikipedia_summary", "system_wikipedia_summary"}:
            saw_wikipedia = True
    return saw_calendar and saw_wikipedia


def extract_calendar_message_from_tool_results(tool_results: Any) -> str:
    for normalized, payload, _args in _iter_tool_payloads(tool_results):
        if normalized not in {"calendar.list_events", "calendar_list_events"}:
            continue
        if payload.get("status") != "ok":
            continue
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        candidate = (
            str(data.get("listing_text") or "").strip()
            or str(payload.get("message") or "").strip()
            or str(payload.get("output") or "").strip()
        )
        if candidate:
            return candidate
        events = data.get("events")
        event_count = data.get("event_count")
        if isinstance(events, list) and len(events) == 0:
            return "Keine Termine im angegebenen Zeitraum gefunden."
        if event_count == 0:
            return "Keine Termine im angegebenen Zeitraum gefunden."
    return ""


def extract_wikipedia_tool_message(payload: dict[str, Any]) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    candidate = (
        str(data.get("summary") or "").strip()
        or str(payload.get("message") or "").strip()
        or str(payload.get("output") or "").strip()
    )
    return sanitize_wikipedia_display_text(candidate)


def extract_wikipedia_context_from_tool_results(
    tool_results: Any,
) -> tuple[str, str, str]:
    """Return (query, title, summary_message)."""
    for normalized, payload, wrapper_args in _iter_tool_payloads(tool_results):
        if normalized not in {"system.wikipedia_summary", "system_wikipedia_summary"}:
            continue
        if payload.get("status") != "ok":
            continue
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        query = (
            str(wrapper_args.get("query") or "").strip()
            or str(data.get("title") or "").strip()
        )
        title = str(data.get("title") or query or "").strip()
        summary = extract_wikipedia_tool_message(payload)
        return query, title, summary
    return "", "", ""


def _find_wikipedia_step(steps: list[RoutineStep]) -> RoutineStep | None:
    return next((step for step in steps if step.skill_id == "system.wikipedia_summary"), None)


def _derive_wikipedia_snapshot_text(
    *,
    final_text: str,
    calendar_message: str,
    tool_wikipedia_message: str,
    combo_text: str,
) -> str:
    text = _strip_response_hints(final_text)
    combo = str(combo_text or "").strip()

    if calendar_message and text.startswith(calendar_message):
        remainder = text[len(calendar_message) :].strip()
        if remainder:
            return sanitize_wikipedia_display_text(remainder)

    if calendar_message and calendar_message in text:
        remainder = text.split(calendar_message, 1)[1].strip()
        if remainder and len(remainder) >= 40:
            return sanitize_wikipedia_display_text(remainder)

    if combo and text and text != combo and len(text) > len(combo):
        if calendar_message and calendar_message in text:
            remainder = text.split(calendar_message, 1)[1].strip()
            if remainder:
                return sanitize_wikipedia_display_text(remainder)
        if tool_wikipedia_message and tool_wikipedia_message in text:
            return sanitize_wikipedia_display_text(tool_wikipedia_message)

    if tool_wikipedia_message:
        return sanitize_wikipedia_display_text(tool_wikipedia_message)
    return ""


def derive_wikipedia_snapshot_query(
    steps: list[RoutineStep],
    tool_results: list[dict[str, Any]] | None = None,
) -> str:
    wiki_step = _find_wikipedia_step(steps)
    step_query = ""
    if wiki_step is not None:
        step_query = str((wiki_step.args or {}).get("query") or "").strip()
    tool_query, title, _summary = extract_wikipedia_context_from_tool_results(tool_results or [])
    return tool_query or title or step_query


def enrich_steps_with_wikipedia_snapshot(
    steps: list[RoutineStep],
    *,
    final_text: str,
    tool_results: list[dict[str, Any]] | None = None,
    build_combo_response: Callable[[Any], str] | None = None,
) -> list[RoutineStep]:
    if not is_calendar_wikipedia_combo_steps(steps):
        return steps

    snapshot_query = derive_wikipedia_snapshot_query(steps, tool_results)
    if not snapshot_query:
        return steps

    calendar_message = extract_calendar_message_from_tool_results(tool_results or [])
    _query, _title, tool_wikipedia_message = extract_wikipedia_context_from_tool_results(tool_results or [])
    combo_text = build_combo_response(tool_results or []) if build_combo_response else ""
    snapshot_text = _derive_wikipedia_snapshot_text(
        final_text=final_text,
        calendar_message=calendar_message,
        tool_wikipedia_message=tool_wikipedia_message,
        combo_text=combo_text,
    )
    if not snapshot_text:
        return steps

    enriched: list[RoutineStep] = []
    for step in steps:
        if step.skill_id != "system.wikipedia_summary":
            enriched.append(step)
            continue
        enriched.append(
            step.model_copy(
                update={
                    "output_snapshot": snapshot_text,
                    "snapshot_query": snapshot_query,
                }
            )
        )
    return enriched


def should_preserve_llm_calendar_wikipedia_answer(
    llm_text: str,
    tool_results: Any,
    *,
    build_combo_response: Callable[[Any], str],
) -> bool:
    text = _strip_response_hints(str(llm_text or "")).strip()
    if not text or _is_generic_llm_fallback(text):
        return False
    if "calendar.list_events" in text or "system.wikipedia_summary" in text:
        return False
    if not calendar_and_wikipedia_tools_ok(tool_results):
        return False

    combo = str(build_combo_response(tool_results) or "").strip()
    if not combo:
        return len(text) >= 60
    if text == combo:
        return False
    return len(text) >= max(60, int(len(combo) * 0.55))


def resolve_calendar_wikipedia_final_text(
    llm_text: str,
    tool_results: Any,
    *,
    build_combo_response: Callable[[Any], str],
) -> str:
    if should_preserve_llm_calendar_wikipedia_answer(
        llm_text,
        tool_results,
        build_combo_response=build_combo_response,
    ):
        return _strip_response_hints(str(llm_text or "")).strip()
    combo = str(build_combo_response(tool_results) or "").strip()
    if combo:
        return combo
    return _strip_response_hints(str(llm_text or "")).strip()


def resolve_routine_wikipedia_display_message(
    *,
    wiki_step: RoutineStep | None,
    requested_query: str | None,
    tool_result: dict[str, Any],
) -> str:
    if (
        wiki_step is not None
        and str(wiki_step.output_snapshot or "").strip()
        and str(wiki_step.snapshot_query or "").strip()
        and wikipedia_queries_match(wiki_step.snapshot_query, requested_query)
    ):
        return sanitize_wikipedia_display_text(str(wiki_step.output_snapshot))

    return extract_wikipedia_tool_message(tool_result)
