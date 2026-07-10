from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy.orm import Session

from backend.data.models import User, UserRoutineOfferLog
from backend.services.capability_registry import CapabilityRegistry
from backend.services.workflow.routine_schema import RoutineCreate, RoutineStep, RoutineStepsDocument
from backend.services.workflow.routine_store import DuplicateRoutineError, RoutineStore, RoutineValidationError
from backend.services.workflow.workflow_detector import (
    DetectedWorkflow,
    detect_learning_candidate,
    detect_workflow_candidate,
)

OFFER_MARKER_PREFIX = "<!-- JANUS_ROUTINE_OFFER:"
OFFER_MARKER_SUFFIX = " -->"
_DONT_ASK_RE = re.compile(r"\b(?:nicht mehr fragen|frag mich nicht mehr|nie wieder fragen)\b", re.IGNORECASE)


@dataclass
class PendingRoutineOffer:
    fingerprint: str
    suggested_name: str
    steps: list[RoutineStep]
    chat_id: int | None = None


@dataclass
class OfferResponseResult:
    handled: bool
    response_text: str | None = None
    saved_routine_id: int | None = None
    offer_state: str | None = None


@dataclass
class PassiveRoutineLearningResult:
    final_text: str
    handled: bool
    learning_state: str | None = None
    candidate_id: int | None = None
    saved_routine_id: int | None = None


def maybe_append_workflow_offer(
    final_text: str,
    *,
    tool_results: list[dict[str, Any]],
    user_text: str,
    messages: list[dict[str, Any]] | None = None,
    routines_offer_enabled: bool = True,
) -> str:
    if not routines_offer_enabled:
        return final_text
    if find_pending_offer(messages or []):
        return final_text

    detected = detect_workflow_candidate(
        tool_results,
        routines_offer_enabled=routines_offer_enabled,
        is_recall_turn=_is_recall_turn(user_text),
        is_greeting_turn=_is_greeting_turn(user_text),
        is_medical_turn=_is_medical_turn(user_text),
    )
    if not detected.is_offer_candidate:
        return final_text

    suggested_name = suggest_routine_name(detected)
    offer_text = (
        f"{final_text.rstrip()}\n\n"
        f"Ich habe gerade einen wiederverwendbaren Ablauf erkannt. "
        f"Wenn du moechtest, kann ich ihn als Routine `{suggested_name}` speichern. "
        f"Antworte mit `Ja`, `Nein` oder `Nicht mehr fragen`."
    )
    return f"{offer_text}\n{encode_offer_marker(detected, suggested_name)}"


def maybe_learn_routine_passively(
    final_text: str,
    *,
    tool_results: list[dict[str, Any]],
    user_text: str,
    messages: list[dict[str, Any]] | None,
    db: Session,
    capability_registry: CapabilityRegistry,
    chat_id: int | None = None,
    routines_offer_enabled: bool = True,
) -> PassiveRoutineLearningResult:
    existing_step_sets: list[set[str]] = []
    if not routines_offer_enabled:
        return PassiveRoutineLearningResult(final_text=final_text, handled=False)
    if find_pending_offer(messages or []):
        return PassiveRoutineLearningResult(final_text=final_text, handled=False)

    user_id = _resolve_routine_user_id(db)
    if user_id is None:
        return PassiveRoutineLearningResult(final_text=final_text, handled=False)

    store = RoutineStore(db, capability_registry)
    routines = store.list_by_user(user_id)
    existing_step_sets = [_routine_skill_set(routine.steps_json) for routine in routines]
    denylisted_fingerprints = _load_denylisted_fingerprints(db, user_id)

    detected = detect_workflow_candidate(
        tool_results,
        routines_offer_enabled=routines_offer_enabled,
        is_recall_turn=_is_recall_turn(user_text),
        is_greeting_turn=_is_greeting_turn(user_text),
        is_medical_turn=_is_medical_turn(user_text),
        denylisted_fingerprints=denylisted_fingerprints,
        existing_routine_step_sets=existing_step_sets,
    )
    if not detected.is_offer_candidate:
        if detected.reject_reason in {"similar_routine_exists", "fingerprint_denylisted"}:
            return PassiveRoutineLearningResult(final_text=final_text, handled=True, learning_state="suppressed")
        return PassiveRoutineLearningResult(final_text=final_text, handled=False)

    active_candidate = store.get_active_candidate_by_fingerprint(user_id, detected.fingerprint)
    if active_candidate is None:
        active_candidate = store.get_active_candidate_by_equivalent_steps(user_id, detected.steps)
    if active_candidate is not None:
        routine_name = suggest_routine_name(detected)
        try:
            saved_routine = store.promote_candidate_to_routine(
                active_candidate.id,
                name=routine_name,
                trigger_phrases=[routine_name],
                source_chat_id=chat_id,
                offer_state="auto_promoted",
            )
        except (DuplicateRoutineError, RoutineValidationError):
            return PassiveRoutineLearningResult(final_text=final_text, handled=False)
        return PassiveRoutineLearningResult(
            final_text=_append_passive_saved_hint(final_text),
            handled=True,
            learning_state="promoted",
            candidate_id=active_candidate.id,
            saved_routine_id=saved_routine.id,
        )

    active_candidates = store.list_active_candidates(user_id)
    active_candidate_step_groups = [
        RoutineStepsDocument.model_validate(candidate.steps_json or {}).steps
        for candidate in active_candidates
    ]
    learning_detected = detect_learning_candidate(
        tool_results,
        routines_offer_enabled=routines_offer_enabled,
        is_recall_turn=_is_recall_turn(user_text),
        is_greeting_turn=_is_greeting_turn(user_text),
        is_medical_turn=_is_medical_turn(user_text),
        denylisted_fingerprints=denylisted_fingerprints,
        existing_routine_step_sets=existing_step_sets,
        existing_candidate_fingerprints={
            str(candidate.step_fingerprint or "").strip()
            for candidate in active_candidates
            if str(candidate.step_fingerprint or "").strip()
        },
        existing_candidate_step_sets=active_candidate_step_groups,
    )
    if not learning_detected.is_learning_candidate:
        return PassiveRoutineLearningResult(final_text=final_text, handled=True, learning_state="suppressed")

    created = store.create_candidate(
        user_id=user_id,
        steps=learning_detected.steps,
        source_chat_id=chat_id,
    )
    return PassiveRoutineLearningResult(
        final_text=final_text,
        handled=True,
        learning_state="candidate_created",
        candidate_id=created.id,
    )


def handle_offer_response(
    user_text: str,
    *,
    messages: list[dict[str, Any]],
    db: Session,
    capability_registry: CapabilityRegistry,
    chat_id: int | None = None,
) -> OfferResponseResult:
    pending = find_pending_offer(messages)
    if pending is None:
        return OfferResponseResult(handled=False)

    if _DONT_ASK_RE.search(user_text):
        _create_offer_log(db, pending=pending, offer_state="denylisted", chat_id=chat_id)
        return OfferResponseResult(
            handled=True,
            response_text="Alles klar, ich frage fuer diesen Ablauf nicht noch einmal nach.",
            offer_state="denylisted",
        )

    normalized = str(user_text or "").strip()
    if not normalized:
        return OfferResponseResult(handled=False)

    if _looks_like_decline(normalized):
        _create_offer_log(db, pending=pending, offer_state="declined", chat_id=chat_id)
        return OfferResponseResult(
            handled=True,
            response_text="Verstanden, ich speichere diesen Ablauf nicht als Routine.",
            offer_state="declined",
        )

    if not _looks_like_confirm(normalized):
        return OfferResponseResult(handled=False)

    store = RoutineStore(db, capability_registry)
    user_id = _resolve_routine_user_id(db)
    if user_id is None:
        return OfferResponseResult(
            handled=True,
            response_text="Ich konnte die Routine gerade nicht speichern, weil kein lokaler Nutzerkontext verfuegbar ist.",
            offer_state="save_blocked",
        )

    try:
        created = store.create_routine(
            RoutineCreate(
                user_id=user_id,
                name=pending.suggested_name,
                trigger_phrases=[pending.suggested_name],
                steps=pending.steps,
                source_chat_id=chat_id,
                user_approved=True,
                offer_state="accepted",
            )
        )
    except DuplicateRoutineError:
        _create_offer_log(db, pending=pending, offer_state="duplicate", chat_id=chat_id)
        return OfferResponseResult(
            handled=True,
            response_text=f"Die Routine `{pending.suggested_name}` ist fuer dich bereits gespeichert.",
            offer_state="duplicate",
        )
    except RoutineValidationError as exc:
        return OfferResponseResult(
            handled=True,
            response_text=f"Ich konnte die Routine gerade nicht speichern: {exc}",
            offer_state="save_failed",
        )

    _create_offer_log(db, pending=pending, offer_state="accepted", chat_id=chat_id)
    return OfferResponseResult(
        handled=True,
        response_text=f"Erledigt, ich habe den Ablauf als Routine `{created.name}` gespeichert.",
        saved_routine_id=created.id,
        offer_state="accepted",
    )


def should_handle_offer_follow_up(user_text: str, *, messages: list[dict[str, Any]]) -> bool:
    if find_pending_offer(messages or []) is None:
        return False
    normalized = str(user_text or "").strip()
    if not normalized:
        return False
    if _DONT_ASK_RE.search(normalized):
        return True
    if _looks_like_decline(normalized):
        return True
    return _looks_like_confirm(normalized)


def suggest_routine_name(detected: DetectedWorkflow) -> str:
    first_skill = detected.steps[0].skill_id.rsplit(".", 1)[-1].replace("_", " ").strip()
    return f"Routine {first_skill.title()}"


def encode_offer_marker(detected: DetectedWorkflow, suggested_name: str) -> str:
    payload = {
        "fingerprint": detected.fingerprint,
        "suggested_name": suggested_name,
        "steps": [step.model_dump(mode="json") for step in detected.steps],
    }
    encoded = base64.b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    return f"{OFFER_MARKER_PREFIX}{encoded}{OFFER_MARKER_SUFFIX}"


def find_pending_offer(messages: Iterable[dict[str, Any]]) -> PendingRoutineOffer | None:
    for message in reversed(list(messages)):
        if str(message.get("role") or "") != "assistant":
            continue
        content = str(message.get("content") or "")
        marker = _extract_offer_marker(content)
        if marker is None:
            continue
        steps = [RoutineStep(**step) for step in marker.get("steps") or []]
        return PendingRoutineOffer(
            fingerprint=str(marker.get("fingerprint") or "").strip(),
            suggested_name=str(marker.get("suggested_name") or "").strip(),
            steps=steps,
        )
    return None


def _extract_offer_marker(content: str) -> dict[str, Any] | None:
    start = content.find(OFFER_MARKER_PREFIX)
    if start < 0:
        return None
    end = content.find(OFFER_MARKER_SUFFIX, start)
    if end < 0:
        return None
    encoded = content[start + len(OFFER_MARKER_PREFIX) : end].strip()
    if not encoded:
        return None
    try:
        decoded = base64.b64decode(encoded.encode("ascii")).decode("utf-8")
        payload = json.loads(decoded)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _create_offer_log(db: Session, *, pending: PendingRoutineOffer, offer_state: str, chat_id: int | None) -> None:
    user_id = _resolve_routine_user_id(db)
    if user_id is None:
        return
    row = UserRoutineOfferLog(
        user_id=user_id,
        step_fingerprint=pending.fingerprint,
        offer_state=offer_state,
        chat_id=chat_id,
    )
    db.add(row)
    db.commit()


def _resolve_routine_user_id(db: Session) -> int | None:
    user = db.query(User).order_by(User.id.asc()).first()
    return int(user.id) if user is not None else None


def _looks_like_confirm(user_text: str) -> bool:
    from backend.services.orchestrator.intent_engine import intent_engine

    return intent_engine.detect_routine_save_confirm(user_text)


def _looks_like_decline(user_text: str) -> bool:
    lowered = str(user_text or "").strip().casefold()
    return lowered in {"nein", "nein danke", "lieber nicht", "no"} or lowered.startswith("nein ")


def _append_passive_saved_hint(final_text: str) -> str:
    base = final_text.rstrip()
    hint = "Ich habe dafuer eine passende Routine gespeichert."
    if not base:
        return hint
    return f"{base}\n\n{hint}"


def _routine_skill_set(steps_json: Any) -> set[str]:
    if not isinstance(steps_json, dict):
        return set()
    raw_steps = steps_json.get("steps")
    if not isinstance(raw_steps, list):
        return set()
    values: set[str] = set()
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        skill_id = str(step.get("skill_id") or "").strip()
        if skill_id:
            values.add(skill_id)
    return values


def _load_denylisted_fingerprints(db: Session, user_id: int) -> set[str]:
    rows = (
        db.query(UserRoutineOfferLog)
        .filter(
            UserRoutineOfferLog.user_id == user_id,
            UserRoutineOfferLog.offer_state == "denylisted",
        )
        .all()
    )
    return {
        str(row.step_fingerprint or "").strip()
        for row in rows
        if str(row.step_fingerprint or "").strip()
    }


def _is_recall_turn(user_text: str) -> bool:
    lowered = str(user_text or "").casefold()
    return any(token in lowered for token in ("was weisst", "was weißt", "erinnerst", "weißt du noch"))


def _is_greeting_turn(user_text: str) -> bool:
    lowered = str(user_text or "").strip().casefold()
    return lowered in {"hi", "hallo", "hey", "guten morgen", "guten abend"}


def _is_medical_turn(user_text: str) -> bool:
    lowered = str(user_text or "").casefold()
    return any(token in lowered for token in ("allerg", "medizin", "arzt", "schmerzen", "diagnose"))
