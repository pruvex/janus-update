from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.data.models import User, UserRoutine
from backend.services.orchestrator.intent_engine import intent_engine
from backend.services.workflow.placeholder_resolver import (
    PlaceholderResolutionError,
    resolve_routine_step_args,
)
from backend.services.workflow.routine_schema import RoutineStep, RoutineStepsDocument
from backend.services.workflow.calendar_wikipedia_presenter import (
    resolve_routine_wikipedia_display_message,
    sanitize_wikipedia_display_text,
)


@dataclass
class RoutineExecutionResult:
    found: bool
    executed: bool
    routine_id: int | None
    routine_name: str | None
    matched_trigger: str | None
    status: str
    response_text: str
    executed_steps: list[str]
    tool_results: list[dict[str, Any]]
    failed_step: str | None = None


class RoutineRunner:
    def __init__(self, db: Session, executor: Any) -> None:
        self.db = db
        self.executor = executor

    async def execute_by_trigger(
        self,
        user_text: str,
        *,
        user_id: int | None = None,
        memory_context: dict[str, Any] | None = None,
    ) -> RoutineExecutionResult:
        routine, matched_trigger = self._find_matching_routine(
            user_text,
            user_id=user_id,
            memory_context=memory_context,
        )
        if routine is None:
            return RoutineExecutionResult(
                found=False,
                executed=False,
                routine_id=None,
                routine_name=None,
                matched_trigger=None,
                status="not_found",
                response_text="Keine Routine gefunden.",
                executed_steps=[],
                tool_results=[],
            )
        return await self.execute_routine(
            routine,
            matched_trigger=matched_trigger,
            memory_context=memory_context,
            user_text=user_text if _is_semantic_routine_match(matched_trigger) else None,
        )

    async def execute_routine(
        self,
        routine: UserRoutine,
        *,
        matched_trigger: str | None = None,
        memory_context: dict[str, Any] | None = None,
        user_text: str | None = None,
    ) -> RoutineExecutionResult:
        document = RoutineStepsDocument.model_validate(routine.steps_json or {})
        executed_steps: list[str] = []
        tool_results: list[dict[str, Any]] = []
        blocked_reason: str | None = None

        if user_text and _is_semantic_routine_match(matched_trigger):
            semantic_block_reason = _semantic_reuse_block_reason(
                document,
                user_text,
                memory_context=memory_context,
            )
            if semantic_block_reason:
                return self._finalize_run(
                    routine,
                    matched_trigger=matched_trigger,
                    status="blocked",
                    response_text=(
                        f"Routine `{routine.name}` wurde nicht wiederverwendet. {semantic_block_reason}"
                    ),
                    executed_steps=executed_steps,
                    tool_results=tool_results,
                    failed_step=None,
                    increment_run=False,
                )

        for step in document.steps:
            try:
                step_args = step.args
                if user_text:
                    step_args = _rebind_semantic_step_args(
                        step,
                        user_text,
                        memory_context=memory_context,
                    )
                resolved_args = resolve_routine_step_args(
                    step_args,
                    memory_context=memory_context,
                    arg_bindings=step.arg_bindings,
                )
            except PlaceholderResolutionError as exc:
                blocked_reason = f"Placeholder-Aufloesung fehlgeschlagen: {exc}"
                return self._finalize_run(
                    routine,
                    matched_trigger=matched_trigger,
                    status="blocked",
                    response_text=(
                        f"Routine `{routine.name}` wurde vor `{step.skill_id}` gestoppt. {blocked_reason}"
                    ),
                    executed_steps=executed_steps,
                    tool_results=tool_results,
                    failed_step=step.skill_id,
                    increment_run=False,
                )

            raw_result = await self._execute_step(step.skill_id, resolved_args)
            normalized_result = _normalize_tool_result(raw_result)
            tool_results.append(
                {
                    "skill_id": step.skill_id,
                    "args": resolved_args,
                    "result": normalized_result,
                }
            )

            status = str(normalized_result.get("status") or "").strip().lower()
            if status not in {"ok", "dry_run_success"}:
                blocked_reason = _extract_error_message(normalized_result)
                return self._finalize_run(
                    routine,
                    matched_trigger=matched_trigger,
                    status="blocked",
                    response_text=(
                        f"Routine `{routine.name}` wurde bei `{step.skill_id}` gestoppt. {blocked_reason}"
                    ),
                    executed_steps=executed_steps,
                    tool_results=tool_results,
                    failed_step=step.skill_id,
                    increment_run=True,
                )

            executed_steps.append(step.skill_id)

        summary = _build_success_summary(
            routine.name,
            tool_results,
            semantic_match=_is_semantic_routine_match(matched_trigger),
            steps=document.steps,
            user_text=user_text,
        )
        return self._finalize_run(
            routine,
            matched_trigger=matched_trigger,
            status="ok",
            response_text=summary,
            executed_steps=executed_steps,
            tool_results=tool_results,
            failed_step=None,
            increment_run=True,
        )

    def _find_matching_routine(
        self,
        user_text: str,
        *,
        user_id: int | None = None,
        memory_context: dict[str, Any] | None = None,
    ) -> tuple[UserRoutine | None, str | None]:
        resolved_user_id = user_id or self._resolve_user_id()
        if resolved_user_id is None:
            return None, None

        routines = (
            self.db.query(UserRoutine)
            .filter(UserRoutine.user_id == resolved_user_id)
            .order_by(UserRoutine.created_at.asc(), UserRoutine.id.asc())
            .all()
        )
        for routine in routines:
            matched_trigger = intent_engine.detect_routine_trigger(user_text, routine.trigger_phrases or [])
            if matched_trigger:
                return routine, matched_trigger

        semantic_matches: list[tuple[UserRoutine, str]] = []
        for routine in routines:
            skill_signature = _routine_skill_signature(routine)
            matched_trigger = intent_engine.match_routine_semantic_signature(user_text, skill_signature)
            if matched_trigger and _routine_constraints_match_user_text(
                routine,
                user_text,
                memory_context=memory_context,
            ):
                semantic_matches.append((routine, matched_trigger))

        if len(semantic_matches) > 1:
            return None, None
        if len(semantic_matches) == 1:
            return semantic_matches[0]
        return None, None

    def _resolve_user_id(self) -> int | None:
        user = self.db.query(User).order_by(User.id.asc()).first()
        return int(user.id) if user is not None else None

    async def _execute_step(self, skill_id: str, resolved_args: dict[str, Any]) -> dict[str, Any]:
        if hasattr(self.executor, "call_internal_skill"):
            result = await self.executor.call_internal_skill(skill_id, resolved_args)
            if isinstance(result, dict):
                return result
        if hasattr(self.executor, "execute_tool_call"):
            result = await self.executor.execute_tool_call(skill_id, resolved_args, is_internal_call=True)
            if isinstance(result, dict):
                return result
        raise TypeError("executor must provide call_internal_skill(...) or execute_tool_call(...)")

    def _finalize_run(
        self,
        routine: UserRoutine,
        *,
        matched_trigger: str | None,
        status: str,
        response_text: str,
        executed_steps: list[str],
        tool_results: list[dict[str, Any]],
        failed_step: str | None,
        increment_run: bool,
    ) -> RoutineExecutionResult:
        if increment_run:
            routine.run_count = int(routine.run_count or 0) + 1
            routine.last_run_at = datetime.utcnow()
            self.db.add(routine)
            self.db.commit()
            self.db.refresh(routine)

        return RoutineExecutionResult(
            found=True,
            executed=status == "ok",
            routine_id=routine.id,
            routine_name=routine.name,
            matched_trigger=matched_trigger,
            status=status,
            response_text=response_text,
            executed_steps=executed_steps,
            tool_results=tool_results,
            failed_step=failed_step,
        )


def _normalize_tool_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_result, dict):
        return {
            "status": "error",
            "error": {"message": "ungueltiges Tool-Ergebnis"},
        }

    if "status" in raw_result:
        return raw_result

    content = raw_result.get("content")
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except (TypeError, ValueError):
            parsed = None
        if isinstance(parsed, dict) and "status" in parsed:
            return parsed

    return {
        "status": "error",
        "error": {"message": "Tool-Ergebnis konnte nicht normalisiert werden."},
    }


def _extract_error_message(result: dict[str, Any]) -> str:
    error = result.get("error")
    if isinstance(error, dict):
        message = str(error.get("message") or "").strip()
        if message:
            return message
    return "Die Routine konnte nicht vollstaendig ausgefuehrt werden."


def _routine_skill_signature(routine: UserRoutine) -> frozenset[str]:
    document = RoutineStepsDocument.model_validate(routine.steps_json or {})
    return frozenset(step.skill_id for step in document.steps)


def _routine_constraints_match_user_text(
    routine: UserRoutine,
    user_text: str,
    *,
    memory_context: dict[str, Any] | None,
) -> bool:
    document = RoutineStepsDocument.model_validate(routine.steps_json or {})
    skill_ids = {step.skill_id for step in document.steps}

    if skill_ids == frozenset({"calendar.list_events", "system.routing"}):
        date_ref = _extract_requested_calendar_date_reference(user_text)
        origin, destination = _extract_safe_routing_origin_destination(user_text)
        return bool(date_ref and origin and destination)

    if skill_ids == frozenset({"calendar.list_events", "system.weather"}):
        date_ref = _extract_calendar_weather_combo_date_reference(user_text)
        requested_city = _extract_requested_weather_city(user_text)
        return bool(date_ref and requested_city)

    if skill_ids == frozenset({"calendar.list_events", "system.wikipedia_summary"}):
        date_ref = _extract_calendar_context_date_reference(user_text)
        query = _extract_requested_wikipedia_query(user_text)
        return bool(date_ref and query)

    weather_step = next((step for step in document.steps if step.skill_id == "system.weather"), None)
    if weather_step is None:
        return True

    requested_city = _extract_requested_weather_city(user_text)
    return bool(requested_city)


def _resolve_routine_weather_city(
    step: RoutineStep,
    *,
    memory_context: dict[str, Any] | None,
) -> str | None:
    raw_city = step.args.get("city") if isinstance(step.args, dict) else None
    if isinstance(raw_city, str) and raw_city.strip() and "{{" not in raw_city:
        return raw_city.strip()

    binding = step.arg_bindings.get("city") if isinstance(step.arg_bindings, dict) else None
    if isinstance(binding, str) and binding.startswith("memory:"):
        key = binding.split(":", 1)[1].strip()
        value = (memory_context or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if isinstance(raw_city, str):
        value = raw_city.strip()
        if value and "{{" not in value:
            return value
    return None


def _resolve_routine_weather_date_str(
    step: RoutineStep,
    *,
    memory_context: dict[str, Any] | None,
) -> str | None:
    raw_date = step.args.get("date_str") if isinstance(step.args, dict) else None
    if isinstance(raw_date, str) and raw_date.strip() and "{{" not in raw_date:
        return raw_date.strip()

    binding = step.arg_bindings.get("date_str") if isinstance(step.arg_bindings, dict) else None
    if isinstance(binding, str) and binding.startswith("memory:"):
        key = binding.split(":", 1)[1].strip()
        value = (memory_context or {}).get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if isinstance(raw_date, str):
        value = raw_date.strip()
        if value and "{{" not in value:
            return value
    return None


def _extract_requested_weather_date_str(user_text: str) -> str | None:
    text = str(user_text or "").strip()
    if not text:
        return None

    weather_match = re.search(r"\bwetter\b", text, flags=re.IGNORECASE)
    if not weather_match:
        return None

    head = text[max(0, weather_match.start() - 20): weather_match.start()]
    tail = text[weather_match.end(): min(len(text), weather_match.end() + 50)]
    return _extract_single_relative_date_from_text(f"{head} {tail}")


def _normalize_date_reference(value: str | None) -> str:
    text = str(value or "").casefold().strip()
    if not text:
        return "heute"
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"\s+", " ", text)
    aliases = {
        "today": "heute",
        "tomorrow": "morgen",
        "yesterday": "gestern",
        "day after tomorrow": "uebermorgen",
    }
    return aliases.get(text, text)


def _extract_requested_weather_city(user_text: str) -> str | None:
    text = str(user_text or "").strip()
    if not text:
        return None
    match = re.search(
        r"\bwetter\b.{0,40}\b(?:in|fuer|für)\s+([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .'-]{1,48})",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r"\bund\s+wetter\s+([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß.-]{1,48})(?:\s+(?:heute|morgen|uebermorgen|übermorgen))?\b",
            text,
            flags=re.IGNORECASE,
        )
    if not match:
        match = re.search(
            r"\bwetter\s+([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß.-]{1,48})(?:\s+(?:heute|morgen|uebermorgen|übermorgen))?\b",
            text,
            flags=re.IGNORECASE,
        )
    if not match:
        return None
    city = re.split(r"[?!.;,]|\s+und\b|\s+oder\b", match.group(1), maxsplit=1)[0].strip()
    return city or None


def _normalize_city_name(value: str) -> str:
    text = str(value or "").casefold().strip()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text)


def _is_semantic_routine_match(matched_trigger: str | None) -> bool:
    return str(matched_trigger or "").startswith("semantic:")


def _semantic_reuse_block_reason(
    document: RoutineStepsDocument,
    user_text: str,
    *,
    memory_context: dict[str, Any] | None,
) -> str | None:
    skill_ids = {step.skill_id for step in document.steps}

    if skill_ids == frozenset({"calendar.list_events", "system.routing"}):
        date_ref = _extract_requested_calendar_date_reference(user_text)
        if not date_ref:
            return "Fuer die gespeicherte Kalender-Routing-Routine fehlt ein eindeutiger Tagesbezug in der Anfrage."
        origin, destination = _extract_safe_routing_origin_destination(user_text)
        if not (origin and destination):
            return "Fuer die gespeicherte Routing-Routine fehlen eindeutige Start- und Zielangaben in der Anfrage."

    if skill_ids == frozenset({"calendar.list_events", "system.weather"}):
        date_ref = _extract_calendar_weather_combo_date_reference(user_text)
        if not date_ref:
            return "Fuer die gespeicherte Kalender-Wetter-Routine fehlt ein eindeutiger Tagesbezug in der Anfrage."
        if not _extract_requested_weather_city(user_text):
            return "Fuer die gespeicherte Wetter-Routine fehlt der Ort in der Anfrage."

    if skill_ids == frozenset({"calendar.list_events", "system.wikipedia_summary"}):
        date_ref = _extract_calendar_context_date_reference(user_text)
        if not date_ref:
            return "Fuer die gespeicherte Kalender-Wikipedia-Routine fehlt ein eindeutiger Tagesbezug in der Anfrage."
        if not _extract_requested_wikipedia_query(user_text):
            return "Fuer die gespeicherte Wikipedia-Routine fehlt ein eindeutiges Thema in der Anfrage."

    weather_step = next((step for step in document.steps if step.skill_id == "system.weather"), None)
    if weather_step is not None:
        if not _extract_requested_weather_city(user_text):
            return "Fuer die gespeicherte Wetter-Routine fehlt der Ort in der Anfrage."

    return None


def _rebind_semantic_step_args(
    step: RoutineStep,
    user_text: str,
    *,
    memory_context: dict[str, Any] | None,
) -> dict[str, Any]:
    args = dict(step.args or {})
    if step.skill_id == "system.routing":
        origin, destination = _extract_safe_routing_origin_destination(user_text)
        if not (origin and destination):
            raise PlaceholderResolutionError(
                "Routing-Parameter konnten nicht sicher aus der Anfrage gelesen werden."
            )
        _apply_routing_rebind(args, origin, destination)
    elif step.skill_id == "calendar.list_events":
        date_ref = (
            _extract_calendar_context_date_reference(user_text)
            or _extract_calendar_weather_combo_date_reference(user_text)
            or _extract_requested_calendar_date_reference(user_text)
        )
        if date_ref:
            _apply_calendar_date_rebind(args, date_ref)
    elif step.skill_id == "system.weather":
        requested_city = _extract_requested_weather_city(user_text)
        if not requested_city:
            raise PlaceholderResolutionError(
                "Wetter-Ort konnte nicht sicher aus der Anfrage gelesen werden."
            )
        args["city"] = requested_city
        requested_date = _extract_requested_weather_date_str(user_text)
        if requested_date:
            args["date_str"] = requested_date
    elif step.skill_id == "system.wikipedia_summary":
        query = _extract_requested_wikipedia_query(user_text)
        if not query:
            raise PlaceholderResolutionError(
                "Wikipedia-Thema konnte nicht sicher aus der Anfrage gelesen werden."
            )
        args["query"] = query
    return args


def _apply_routing_rebind(args: dict[str, Any], origin: str, destination: str) -> None:
    origin_keys = [key for key in ("origin", "from_city", "from", "source") if key in args]
    destination_keys = [key for key in ("destination", "to_city", "to", "target") if key in args]
    if origin_keys:
        for key in origin_keys:
            args[key] = origin
    else:
        args["origin"] = origin
    if destination_keys:
        for key in destination_keys:
            args[key] = destination
    else:
        args["destination"] = destination


def _apply_calendar_date_rebind(args: dict[str, Any], date_ref: str) -> None:
    range_map = {
        "heute": "today",
        "morgen": "tomorrow",
        "gestern": "yesterday",
        "uebermorgen": "day_after_tomorrow",
    }
    if "range" in args:
        args["range"] = range_map.get(date_ref, date_ref)
    if "date_str" in args:
        args["date_str"] = date_ref


_RELATIVE_DATE_MARKERS = (
    (r"\buebermorgen\b", "uebermorgen"),
    (r"\bübermorgen\b", "uebermorgen"),
    (r"\bmorgen\b", "morgen"),
    (r"\bheute\b", "heute"),
    (r"\bgestern\b", "gestern"),
    (r"\btoday\b", "heute"),
    (r"\btomorrow\b", "morgen"),
)


def _extract_single_relative_date_from_text(text: str) -> str | None:
    segment = str(text or "").strip()
    if not segment:
        return None
    matches: list[str] = []
    for pattern, normalized in _RELATIVE_DATE_MARKERS:
        if re.search(pattern, segment, flags=re.IGNORECASE):
            if normalized not in matches:
                matches.append(normalized)
    if len(matches) != 1:
        return None
    return matches[0]


def _extract_calendar_context_date_reference(user_text: str) -> str | None:
    text = str(user_text or "").strip()
    if not text:
        return None
    boundary_match = re.search(
        r"\b(?:wetter|wikipedia|routing|entfernung|strecke|nachrichten|news)\b",
        text,
        flags=re.IGNORECASE,
    )
    calendar_segment = text[: boundary_match.start()] if boundary_match else text
    calendar_segment = re.split(
        r"\bund\s+(?:wie|was|gib|gibt)\b",
        calendar_segment,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return _extract_single_relative_date_from_text(calendar_segment)


def _extract_calendar_weather_combo_date_reference(user_text: str) -> str | None:
    date_ref = _extract_calendar_context_date_reference(user_text)
    if date_ref:
        return date_ref
    return _extract_single_relative_date_from_text(str(user_text or "").strip())


def _extract_requested_calendar_date_reference(user_text: str) -> str | None:
    return _extract_single_relative_date_from_text(str(user_text or "").strip())


def _extract_requested_wikipedia_query(user_text: str) -> str | None:
    text = str(user_text or "").strip()
    if not text:
        return None

    def _clean_topic(value: str) -> str:
        cleaned = re.split(
            r"[?!.;,]|\s+und\s+(?:was|wie|gib|gibt)\b",
            value.strip(),
            maxsplit=1,
        )[0].strip()
        return cleaned

    patterns = (
        re.compile(
            r"(?i)wikipedia(?:-|\s*)zusammenfassung(?:\s+(?:zu|über|ueber|von))?\s+"
            r"([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .'-]{0,60}?)(?=\s*[?.!,]|$)"
        ),
        re.compile(
            r"(?i)(?:zusammenfassung|summary)\s+(?:zu|über|ueber|von)\s+"
            r"([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .'-]{0,60}?)(?=\s*[?.!,]|$)"
        ),
        re.compile(
            r"(?i)wikipedia.*?\b(?:zu|über|ueber|von)\s+"
            r"([A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .'-]{0,60}?)(?=\s*[?.!,]|$)"
        ),
    )
    topics: list[str] = []
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        topic = _clean_topic(match.group(1))
        if topic and topic not in topics:
            topics.append(topic)
    if len(topics) != 1:
        return None
    return topics[0]


def _extract_safe_routing_origin_destination(user_text: str) -> tuple[str | None, str | None]:
    text = str(user_text or "").strip()
    if not text:
        return None, None

    def _clean_place(value: str) -> str:
        cleaned = re.split(
            r"[?!.;,]|\s+und\s+(?:wie|was|wieviel|welche)\b",
            value,
            maxsplit=1,
        )[0].strip()
        return cleaned

    patterns = (
        re.compile(
            r"\bvon\s+([A-Za-zÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ][\wÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ .'-]{0,48}?)\s+nach\s+"
            r"([A-Za-zÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ][\wÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ .'-]{0,48})(?=\s*[?!.;,]|$)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bfrom\s+([A-Za-zÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ][\wÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ .'-]{0,48}?)\s+to\s+"
            r"([A-Za-zÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ][\wÃ„Ã–ÃœÃ¤Ã¶Ã¼ÃŸ .'-]{0,48})(?=\s*[?!.;,]|$)",
            re.IGNORECASE,
        ),
    )
    pairs: list[tuple[str, str]] = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            origin = _clean_place(match.group(1))
            destination = _clean_place(match.group(2))
            if not origin or not destination:
                continue
            if re.search(r"\b(?:und|oder|and|or)\b", origin, flags=re.IGNORECASE):
                return None, None
            if re.search(r"\b(?:und|oder|and|or)\b", destination, flags=re.IGNORECASE):
                return None, None
            pair = (origin, destination)
            if pair not in pairs:
                pairs.append(pair)
    if len(pairs) != 1:
        return None, None
    return pairs[0]


def _build_success_summary(
    routine_name: str,
    tool_results: list[dict[str, Any]],
    *,
    semantic_match: bool = False,
    steps: list[RoutineStep] | None = None,
    user_text: str | None = None,
) -> str:
    combo_summary = _build_calendar_weather_success_summary(tool_results)
    if combo_summary:
        if semantic_match:
            return f"Ich habe deine passende gespeicherte Routine genutzt.\n\n{combo_summary}"
        return combo_summary

    combo_summary = _build_calendar_routing_success_summary(tool_results)
    if combo_summary:
        if semantic_match:
            return f"Ich habe deine passende gespeicherte Routine genutzt.\n\n{combo_summary}"
        return combo_summary

    combo_summary = _build_calendar_wikipedia_success_summary(
        tool_results,
        steps=steps,
        user_text=user_text,
    )
    if combo_summary:
        if semantic_match:
            return f"Ich habe deine passende gespeicherte Routine genutzt.\n\n{combo_summary}"
        return combo_summary

    header = f"Routine `{routine_name}` erfolgreich ausgefuehrt."
    if semantic_match:
        header = f"Ich habe deine passende gespeicherte Routine genutzt.\n{header}"
    lines = [header]
    for item in tool_results:
        skill_id = str(item.get("skill_id") or "").strip()
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        status = str(result.get("status") or "").strip().lower()
        summary = _summarize_data(result.get("data"))
        if status in {"ok", "dry_run_success"}:
            lines.append(f"- `{skill_id}`: {summary}")
    return "\n".join(lines)


def _build_calendar_weather_success_summary(tool_results: list[dict[str, Any]]) -> str:
    calendar_message = ""
    weather_message = ""
    saw_calendar = False
    saw_weather = False

    for item in tool_results:
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("skill_id") or "").strip().lower()
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        status = str(result.get("status") or "").strip().lower()
        if status not in {"ok", "dry_run_success"}:
            continue

        if skill_id == "calendar.list_events":
            saw_calendar = True
            calendar_message = _extract_calendar_success_message(result)
        elif skill_id == "system.weather":
            saw_weather = True
            weather_message = _extract_weather_success_message(result)

    if not (saw_calendar and saw_weather and weather_message):
        return ""
    if calendar_message:
        return f"{calendar_message}\n\n{weather_message}"
    return weather_message


def _build_calendar_routing_success_summary(tool_results: list[dict[str, Any]]) -> str:
    calendar_message = ""
    routing_message = ""
    saw_calendar = False
    saw_routing = False

    for item in tool_results:
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("skill_id") or "").strip().lower()
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        status = str(result.get("status") or "").strip().lower()
        if status not in {"ok", "dry_run_success"}:
            continue

        if skill_id == "calendar.list_events":
            saw_calendar = True
            calendar_message = _extract_calendar_success_message(result)
        elif skill_id == "system.routing":
            saw_routing = True
            routing_message = _extract_routing_success_message(result)

    if not (saw_calendar and saw_routing and routing_message):
        return ""
    if calendar_message:
        return f"{calendar_message}\n\n{routing_message}"
    return routing_message


def _build_calendar_wikipedia_success_summary(
    tool_results: list[dict[str, Any]],
    *,
    steps: list[RoutineStep] | None = None,
    user_text: str | None = None,
) -> str:
    calendar_message = ""
    wikipedia_message = ""
    wikipedia_error_message = ""
    saw_calendar = False
    saw_wikipedia = False
    saw_wikipedia_tool = False
    wiki_step = next((step for step in steps or [] if step.skill_id == "system.wikipedia_summary"), None)
    requested_query = _extract_requested_wikipedia_query(user_text or "") if user_text else None

    for item in tool_results:
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("skill_id") or "").strip().lower()
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        status = str(result.get("status") or "").strip().lower()
        if status not in {"ok", "dry_run_success"}:
            if skill_id in {"system.wikipedia_summary", "system_wikipedia_summary"}:
                saw_wikipedia_tool = True
                error_obj = result.get("error") if isinstance(result.get("error"), dict) else {}
                wikipedia_error_message = (
                    str(error_obj.get("message") or "").strip()
                    or str(result.get("message") or "").strip()
                )
            continue

        if skill_id == "calendar.list_events":
            saw_calendar = True
            calendar_message = _extract_calendar_success_message(result)
        elif skill_id in {"system.wikipedia_summary", "system_wikipedia_summary"}:
            saw_wikipedia_tool = True
            saw_wikipedia = True
            wikipedia_message = resolve_routine_wikipedia_display_message(
                wiki_step=wiki_step,
                requested_query=requested_query,
                tool_result=result,
            )

    if saw_calendar and saw_wikipedia and calendar_message and wikipedia_message:
        return f"{calendar_message}\n\n{wikipedia_message}"

    parts = [part for part in (calendar_message, wikipedia_message) if part]
    if parts:
        return "\n\n".join(parts)
    if saw_calendar and saw_wikipedia_tool and wikipedia_error_message:
        if calendar_message:
            return f"{calendar_message}\n\n{wikipedia_error_message}"
        return wikipedia_error_message
    return ""


def _extract_wikipedia_success_message(result: dict[str, Any]) -> str:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    candidate = (
        str(data.get("summary") or "").strip()
        or str(result.get("message") or "").strip()
        or str(result.get("output") or "").strip()
    )
    if candidate:
        return sanitize_wikipedia_display_text(candidate)
    return _summarize_data(data)


def _extract_routing_success_message(result: dict[str, Any]) -> str:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    candidate = (
        str(result.get("message") or "").strip()
        or str(data.get("summary") or "").strip()
        or str(result.get("output") or "").strip()
    )
    if candidate:
        return candidate

    origin = str(data.get("origin") or "").strip()
    destination = str(data.get("destination") or "").strip()
    distance_km = data.get("distance_km")
    duration = str(data.get("duration_text") or data.get("duration") or "").strip()
    if origin and destination and distance_km is not None:
        suffix = f", ca. {duration}" if duration else ""
        return f"Die Entfernung von {origin} nach {destination} betraegt etwa {distance_km} km{suffix}."
    return _summarize_data(data)


def _extract_calendar_success_message(result: dict[str, Any]) -> str:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    candidate = (
        str(data.get("listing_text") or "").strip()
        or str(result.get("message") or "").strip()
        or str(result.get("output") or "").strip()
    )
    if candidate:
        return candidate

    events = data.get("events")
    event_count = data.get("event_count")
    if isinstance(events, list) and len(events) == 0:
        return "Keine Termine im angegebenen Zeitraum gefunden."
    if event_count == 0:
        return "Keine Termine im angegebenen Zeitraum gefunden."
    return _summarize_data(data)


def _extract_weather_success_message(result: dict[str, Any]) -> str:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    candidate = (
        str(data.get("forecast") or "").strip()
        or str(data.get("summary") or "").strip()
        or str(result.get("message") or "").strip()
        or str(result.get("output") or "").strip()
    )
    if candidate:
        return candidate
    return _summarize_data(data)


def _summarize_data(data: Any) -> str:
    if isinstance(data, dict):
        for key in ("summary", "message", "result", "text", "content"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if data:
            first_key = next(iter(data.keys()))
            return f"{first_key}: {data[first_key]}"
    if isinstance(data, list):
        return f"{len(data)} Eintraege"
    if data is None:
        return "ok"
    return str(data)
