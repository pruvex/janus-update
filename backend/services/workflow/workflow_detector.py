from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.services.workflow.routine_schema import (
    RoutineStep,
    build_step_fingerprint,
    steps_share_promotion_equivalence,
)
from backend.services.workflow.step_trace_extractor import extract_routine_steps, iter_trace_items


_SENSITIVE_SKILL_PREFIXES = (
    "communication.",
    "memory.",
    "filesystem.",
    "contacts.",
)
_HIGH_RISK_LEVELS = {"high", "critical", "sensitive"}


@dataclass
class DetectedWorkflow:
    steps: list[RoutineStep]
    fingerprint: str
    skill_count: int
    is_offer_candidate: bool
    reject_reason: str | None
    is_learning_candidate: bool = False
    learning_reject_reason: str | None = None


def detect_workflow_candidate(
    trace_payload: object,
    *,
    routines_offer_enabled: bool = True,
    is_recall_turn: bool = False,
    is_greeting_turn: bool = False,
    is_medical_turn: bool = False,
    session_cooldown_active: bool = False,
    denylisted_fingerprints: Iterable[str] | None = None,
    existing_routine_step_sets: Iterable[set[str]] | None = None,
) -> DetectedWorkflow:
    steps = extract_routine_steps(trace_payload)
    fingerprint = build_step_fingerprint(steps) if steps else ""
    denylisted = set(denylisted_fingerprints or [])
    existing_step_sets = list(existing_routine_step_sets or [])
    reject_reason = _evaluate_offer_gate(
        steps,
        fingerprint=fingerprint,
        routines_offer_enabled=routines_offer_enabled,
        is_recall_turn=is_recall_turn,
        is_greeting_turn=is_greeting_turn,
        is_medical_turn=is_medical_turn,
        session_cooldown_active=session_cooldown_active,
        denylisted_fingerprints=denylisted,
        existing_routine_step_sets=existing_step_sets,
        trace_payload=trace_payload,
    )
    unique_skills = {step.skill_id for step in steps}
    return DetectedWorkflow(
        steps=steps,
        fingerprint=fingerprint,
        skill_count=len(unique_skills),
        is_offer_candidate=reject_reason is None,
        reject_reason=reject_reason,
    )


def detect_learning_candidate(
    trace_payload: object,
    *,
    routines_offer_enabled: bool = True,
    is_recall_turn: bool = False,
    is_greeting_turn: bool = False,
    is_medical_turn: bool = False,
    session_cooldown_active: bool = False,
    denylisted_fingerprints: Iterable[str] | None = None,
    existing_routine_step_sets: Iterable[set[str]] | None = None,
    existing_candidate_fingerprints: Iterable[str] | None = None,
    existing_candidate_step_sets: Iterable[list[RoutineStep]] | None = None,
) -> DetectedWorkflow:
    detected = detect_workflow_candidate(
        trace_payload,
        routines_offer_enabled=routines_offer_enabled,
        is_recall_turn=is_recall_turn,
        is_greeting_turn=is_greeting_turn,
        is_medical_turn=is_medical_turn,
        session_cooldown_active=session_cooldown_active,
        denylisted_fingerprints=denylisted_fingerprints,
        existing_routine_step_sets=existing_routine_step_sets,
    )
    if not detected.is_offer_candidate:
        return DetectedWorkflow(
            steps=detected.steps,
            fingerprint=detected.fingerprint,
            skill_count=detected.skill_count,
            is_offer_candidate=False,
            reject_reason=detected.reject_reason,
            is_learning_candidate=False,
            learning_reject_reason=detected.reject_reason,
        )

    learning_reject_reason = _evaluate_learning_gate(
        detected.steps,
        fingerprint=detected.fingerprint,
        trace_payload=trace_payload,
        existing_candidate_fingerprints=set(existing_candidate_fingerprints or []),
        existing_candidate_step_sets=list(existing_candidate_step_sets or []),
    )
    return DetectedWorkflow(
        steps=detected.steps,
        fingerprint=detected.fingerprint,
        skill_count=detected.skill_count,
        is_offer_candidate=True,
        reject_reason=None,
        is_learning_candidate=learning_reject_reason is None,
        learning_reject_reason=learning_reject_reason,
    )


def _evaluate_offer_gate(
    steps: list[RoutineStep],
    *,
    fingerprint: str,
    routines_offer_enabled: bool,
    is_recall_turn: bool,
    is_greeting_turn: bool,
    is_medical_turn: bool,
    session_cooldown_active: bool,
    denylisted_fingerprints: set[str],
    existing_routine_step_sets: list[set[str]],
    trace_payload: object,
) -> str | None:
    if not routines_offer_enabled:
        return "routines_offer_disabled"
    if is_medical_turn:
        return "medical_turn_excluded"
    if is_recall_turn:
        return "recall_turn_excluded"
    if is_greeting_turn:
        return "greeting_turn_excluded"
    if session_cooldown_active:
        return "session_cooldown_active"
    if not steps:
        return "no_successful_steps"
    unique_skills = {step.skill_id for step in steps}
    if len(unique_skills) < 2:
        return "insufficient_distinct_skills"
    if len(steps) < 2:
        return "insufficient_step_count"
    if fingerprint in denylisted_fingerprints:
        return "fingerprint_denylisted"
    if _is_similar_to_existing(steps, existing_routine_step_sets):
        return "similar_routine_exists"
    if len(steps) < 2:
        return "insufficient_step_count"
    return None


def _is_similar_to_existing(steps: list[RoutineStep], existing_step_sets: list[set[str]]) -> bool:
    current = {step.skill_id for step in steps}
    if not current:
        return False
    for existing in existing_step_sets:
        union = current | existing
        if not union:
            continue
        similarity = len(current & existing) / len(union)
        if similarity >= 0.85:
            return True
    return False


def _evaluate_learning_gate(
    steps: list[RoutineStep],
    *,
    fingerprint: str,
    trace_payload: object,
    existing_candidate_fingerprints: set[str],
    existing_candidate_step_sets: list[list[RoutineStep]],
) -> str | None:
    if fingerprint in existing_candidate_fingerprints:
        return "active_candidate_exists"
    for existing_steps in existing_candidate_step_sets:
        if steps_share_promotion_equivalence(steps, existing_steps):
            return "active_candidate_exists"
    if _trace_has_high_risk_step(trace_payload):
        return "high_risk_step"
    for step in steps:
        if _is_sensitive_skill(step.skill_id):
            return "sensitive_skill_excluded"
        if _step_is_context_dependent(step):
            return "context_dependent_step"
    return None


def _is_sensitive_skill(skill_id: str) -> bool:
    normalized = str(skill_id or "").strip().casefold()
    return any(normalized.startswith(prefix) for prefix in _SENSITIVE_SKILL_PREFIXES)


def _step_is_context_dependent(step: RoutineStep) -> bool:
    if step.arg_bindings:
        return True
    for value in step.args.values():
        if isinstance(value, str) and "{{" in value and "}}" in value:
            return True
    return False


def _trace_has_high_risk_step(trace_payload: object) -> bool:
    for item in iter_trace_items(trace_payload):
        risk_level = str(item.get("risk_level") or "").strip().casefold()
        if risk_level in _HIGH_RISK_LEVELS:
            return True
    return False
