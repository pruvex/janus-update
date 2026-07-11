from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from backend.data.models import UserRoutine, UserRoutineCandidate, UserRoutineOfferLog
from backend.services.capability_registry import CapabilityRegistry
from backend.services.workflow.routine_schema import (
    RoutineCreate,
    RoutineStep,
    RoutineStepsDocument,
    RoutineUpdate,
    build_step_fingerprint,
    normalize_trigger_phrases,
    steps_share_promotion_equivalence,
)
from backend.services.workflow.workflow_detector import detect_learning_candidate

CANDIDATE_TTL_DAYS = 30


class RoutineValidationError(ValueError):
    """Raised when a routine payload violates the bounded workflow contract."""


class DuplicateRoutineError(RoutineValidationError):
    """Raised when a user already has a routine with the same step fingerprint."""


class DuplicateCandidateError(RoutineValidationError):
    """Raised when a user already has an active candidate with the same step fingerprint."""


class RoutineStore:
    def __init__(self, db: Session, capability_registry: CapabilityRegistry) -> None:
        self.db = db
        self.capability_registry = capability_registry

    def create_routine(self, payload: RoutineCreate) -> UserRoutine:
        steps = list(payload.steps)
        self._validate_skill_ids(steps)
        step_document = RoutineStepsDocument(steps=steps)
        fingerprint = build_step_fingerprint(step_document.steps)
        self._assert_unique_fingerprint(payload.user_id, fingerprint)

        row = UserRoutine(
            user_id=payload.user_id,
            name=payload.name.strip(),
            description=payload.description,
            trigger_phrases=normalize_trigger_phrases(payload.trigger_phrases),
            steps_json=step_document.model_dump(mode="json"),
            step_fingerprint=fingerprint,
            source_chat_id=payload.source_chat_id,
            source_turn_id=payload.source_turn_id,
            user_approved=payload.user_approved,
            offer_state=payload.offer_state,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def create_candidate(
        self,
        *,
        user_id: int,
        steps: list[RoutineStep],
        source_chat_id: int | None = None,
        source_turn_id: int | None = None,
    ) -> UserRoutineCandidate:
        normalized_steps = list(steps)
        self._validate_skill_ids(normalized_steps)
        step_document = RoutineStepsDocument(steps=normalized_steps)
        fingerprint = build_step_fingerprint(step_document.steps)
        self._expire_stale_candidates(user_id)
        existing = self.get_active_candidate_by_fingerprint(user_id, fingerprint)
        if existing is not None:
            raise DuplicateCandidateError(
                f"user {user_id} already has active candidate {existing.id} with fingerprint {fingerprint}"
            )
        equivalent = self.get_active_candidate_by_equivalent_steps(user_id, normalized_steps)
        if equivalent is not None:
            raise DuplicateCandidateError(
                f"user {user_id} already has equivalent active candidate {equivalent.id}"
            )

        now = datetime.utcnow()
        row = UserRoutineCandidate(
            user_id=user_id,
            steps_json=step_document.model_dump(mode="json"),
            step_fingerprint=fingerprint,
            source_chat_id=source_chat_id,
            source_turn_id=source_turn_id,
            status="active",
            created_at=now,
            expires_at=now + timedelta(days=CANDIDATE_TTL_DAYS),
            confirmed_at=None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def promote_candidate_to_routine(
        self,
        candidate_id: int,
        *,
        name: str,
        trigger_phrases: list[str] | None = None,
        source_chat_id: int | None = None,
        source_turn_id: int | None = None,
        offer_state: str = "auto_promoted",
        steps: list[RoutineStep] | None = None,
    ) -> UserRoutine:
        candidate = (
            self.db.query(UserRoutineCandidate)
            .filter(UserRoutineCandidate.id == candidate_id)
            .one_or_none()
        )
        if candidate is None:
            raise RoutineValidationError(f"candidate {candidate_id} not found")
        if not self.is_candidate_active(candidate):
            raise RoutineValidationError(f"candidate {candidate_id} is not active")

        document = RoutineStepsDocument.model_validate(candidate.steps_json or {})
        routine = self.create_routine(
            RoutineCreate(
                user_id=candidate.user_id,
                name=name,
                trigger_phrases=trigger_phrases or [name],
                steps=steps or document.steps,
                source_chat_id=source_chat_id if source_chat_id is not None else candidate.source_chat_id,
                source_turn_id=source_turn_id if source_turn_id is not None else candidate.source_turn_id,
                user_approved=True,
                offer_state=offer_state,
            )
        )

        candidate.status = "promoted"
        candidate.confirmed_at = datetime.utcnow()
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return routine

    def record_learning_candidate_if_eligible(
        self,
        trace_payload: object,
        *,
        user_id: int,
        source_chat_id: int | None = None,
        source_turn_id: int | None = None,
        routines_offer_enabled: bool = True,
        is_recall_turn: bool = False,
        is_greeting_turn: bool = False,
        is_medical_turn: bool = False,
        session_cooldown_active: bool = False,
        denylisted_fingerprints: Iterable[str] | None = None,
        existing_routine_step_sets: Iterable[set[str]] | None = None,
    ) -> UserRoutineCandidate | None:
        self._expire_stale_candidates(user_id)
        active_candidates = self.list_active_candidates(user_id)
        active_fingerprints = {candidate.step_fingerprint for candidate in active_candidates}
        active_candidate_step_groups = [
            RoutineStepsDocument.model_validate(candidate.steps_json or {}).steps
            for candidate in active_candidates
        ]
        detected = detect_learning_candidate(
            trace_payload,
            routines_offer_enabled=routines_offer_enabled,
            is_recall_turn=is_recall_turn,
            is_greeting_turn=is_greeting_turn,
            is_medical_turn=is_medical_turn,
            session_cooldown_active=session_cooldown_active,
            denylisted_fingerprints=denylisted_fingerprints,
            existing_routine_step_sets=existing_routine_step_sets,
            existing_candidate_fingerprints=active_fingerprints,
            existing_candidate_step_sets=active_candidate_step_groups,
        )
        if not detected.is_learning_candidate:
            return None
        return self.create_candidate(
            user_id=user_id,
            steps=detected.steps,
            source_chat_id=source_chat_id,
            source_turn_id=source_turn_id,
        )

    def get_active_candidate_by_fingerprint(
        self,
        user_id: int,
        fingerprint: str,
    ) -> UserRoutineCandidate | None:
        self._expire_stale_candidates(user_id)
        now = datetime.utcnow()
        return (
            self.db.query(UserRoutineCandidate)
            .filter(
                UserRoutineCandidate.user_id == user_id,
                UserRoutineCandidate.step_fingerprint == fingerprint,
                UserRoutineCandidate.status == "active",
                UserRoutineCandidate.expires_at > now,
            )
            .one_or_none()
        )

    def get_active_candidate_by_equivalent_steps(
        self,
        user_id: int,
        steps: list[RoutineStep],
    ) -> UserRoutineCandidate | None:
        for candidate in self.list_active_candidates(user_id):
            document = RoutineStepsDocument.model_validate(candidate.steps_json or {})
            if steps_share_promotion_equivalence(steps, document.steps):
                return candidate
        return None

    def list_active_candidates(self, user_id: int) -> list[UserRoutineCandidate]:
        self._expire_stale_candidates(user_id)
        now = datetime.utcnow()
        return (
            self.db.query(UserRoutineCandidate)
            .filter(
                UserRoutineCandidate.user_id == user_id,
                UserRoutineCandidate.status == "active",
                UserRoutineCandidate.expires_at > now,
            )
            .order_by(UserRoutineCandidate.created_at.asc(), UserRoutineCandidate.id.asc())
            .all()
        )

    def is_candidate_active(self, candidate: UserRoutineCandidate) -> bool:
        if str(candidate.status or "") != "active":
            return False
        expires_at = candidate.expires_at
        if expires_at is None:
            return False
        return expires_at > datetime.utcnow()

    def _expire_stale_candidates(self, user_id: int) -> int:
        now = datetime.utcnow()
        stale_rows = (
            self.db.query(UserRoutineCandidate)
            .filter(
                UserRoutineCandidate.user_id == user_id,
                UserRoutineCandidate.status == "active",
                UserRoutineCandidate.expires_at <= now,
            )
            .all()
        )
        for row in stale_rows:
            row.status = "expired"
            self.db.add(row)
        if stale_rows:
            self.db.commit()
        return len(stale_rows)

    def get_routine(self, routine_id: int) -> UserRoutine | None:
        return self.db.query(UserRoutine).filter(UserRoutine.id == routine_id).one_or_none()

    def list_by_user(self, user_id: int) -> list[UserRoutine]:
        return (
            self.db.query(UserRoutine)
            .filter(UserRoutine.user_id == user_id)
            .order_by(UserRoutine.created_at.asc(), UserRoutine.id.asc())
            .all()
        )

    def update_routine(self, routine_id: int, payload: RoutineUpdate) -> UserRoutine:
        row = self.get_routine(routine_id)
        if row is None:
            raise RoutineValidationError(f"routine {routine_id} not found")

        if payload.name is not None:
            normalized_name = payload.name.strip()
            if not normalized_name:
                raise RoutineValidationError("name must not be blank")
            row.name = normalized_name
        if payload.description is not None:
            row.description = payload.description
        if payload.trigger_phrases is not None:
            row.trigger_phrases = normalize_trigger_phrases(payload.trigger_phrases)
        if payload.user_approved is not None:
            row.user_approved = payload.user_approved
        if payload.offer_state is not None:
            row.offer_state = payload.offer_state

        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete_routine(self, routine_id: int) -> bool:
        row = self.get_routine(routine_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def create_offer_log(
        self,
        *,
        user_id: int,
        step_fingerprint: str,
        offer_state: str,
        chat_id: int | None = None,
    ) -> UserRoutineOfferLog:
        row = UserRoutineOfferLog(
            user_id=user_id,
            step_fingerprint=step_fingerprint,
            offer_state=offer_state,
            chat_id=chat_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def _resolve_available_skill_ids(self) -> set[str]:
        registry = self.capability_registry
        available_skills = getattr(registry, "_available_skills", None)
        if available_skills:
            return {str(skill_id) for skill_id in available_skills if skill_id}

        skill_ids: set[str] = set()
        tools = getattr(registry, "tools", None)
        if isinstance(tools, dict):
            skill_ids.update(str(key) for key in tools.keys() if key)

        mapping = getattr(registry, "_skill_mapping", None)
        if isinstance(mapping, dict):
            skill_ids.update(str(value) for value in mapping.values() if value)

        metadata = getattr(registry, "_skill_metadata", None)
        if isinstance(metadata, dict):
            skill_ids.update(str(key) for key in metadata.keys() if key)

        return skill_ids

    def _validate_skill_ids(self, steps: Iterable[RoutineStep]) -> None:
        available_skills = self._resolve_available_skill_ids()
        missing: list[str] = []
        for step in steps:
            if step.skill_id not in available_skills:
                missing.append(step.skill_id)
        if missing:
            raise RoutineValidationError(f"unknown skill_id(s): {', '.join(sorted(set(missing)))}")

    def _assert_unique_fingerprint(self, user_id: int, fingerprint: str) -> None:
        existing = (
            self.db.query(UserRoutine)
            .filter(UserRoutine.user_id == user_id, UserRoutine.step_fingerprint == fingerprint)
            .one_or_none()
        )
        if existing is not None:
            raise DuplicateRoutineError(
                f"user {user_id} already has routine {existing.id} with fingerprint {fingerprint}"
            )
