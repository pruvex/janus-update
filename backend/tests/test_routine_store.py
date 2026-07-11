from pathlib import Path

import backend.data.models  # noqa: F401
from datetime import datetime, timedelta

from backend.data.models import User, UserRoutine, UserRoutineCandidate, UserRoutineOfferLog
from backend.services.capability_registry import CapabilityRegistry
from backend.services.workflow.routine_schema import RoutineCreate, RoutineStep, RoutineUpdate
from backend.services.workflow.routine_store import (
    DuplicateCandidateError,
    DuplicateRoutineError,
    RoutineStore,
    RoutineValidationError,
)


def _build_registry(tmp_path: Path) -> CapabilityRegistry:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        """
        {
          "version": "1.0.0",
          "categories": {
            "workflow": {
              "display_name": "Workflow",
              "icon": "w",
              "description": "Workflow",
              "abilities": [
                {"id": "calendar.read", "skill_refs": ["calendar.list_events"], "how_to": "x"},
                {"id": "weather.read", "skill_refs": ["system.weather"], "how_to": "x"},
                {"id": "mail.read", "skill_refs": ["communication.list_emails"], "how_to": "x"}
              ],
              "ui_locations": {}
            }
          }
        }
        """,
        encoding="utf-8",
    )
    skills_dir = tmp_path / "skills"
    (skills_dir / "calendar").mkdir(parents=True)
    (skills_dir / "system").mkdir(parents=True)
    (skills_dir / "communication").mkdir(parents=True)
    (skills_dir / "calendar" / "events.json").write_text('{"skill":"calendar.list_events"}', encoding="utf-8")
    (skills_dir / "system" / "weather.json").write_text('{"skill":"system.weather"}', encoding="utf-8")
    (skills_dir / "communication" / "emails.json").write_text('{"skill":"communication.list_emails"}', encoding="utf-8")
    registry = CapabilityRegistry(str(registry_path), str(skills_dir))
    registry.load()
    return registry


def _seed_user(db_session) -> User:
    user = User(username="workflow-user", hashed_password="x", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_and_list_routine(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    created = store.create_routine(
        RoutineCreate(
            user_id=user.id,
            name="Morgen-Routine",
            trigger_phrases=["Morgen-Routine", "morgen-routine", "Start meinen Tag"],
            steps=[
                RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"}),
                RoutineStep(order=2, skill_id="system.weather", args={"city": "{{user.city}}"}),
            ],
            user_approved=True,
        )
    )

    routines = store.list_by_user(user.id)
    assert len(routines) == 1
    assert created.id == routines[0].id
    assert routines[0].trigger_phrases == ["Morgen-Routine", "Start meinen Tag"]
    assert routines[0].user_approved is True


def test_duplicate_fingerprint_is_rejected(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)
    payload = RoutineCreate(
        user_id=user.id,
        name="Routine A",
        steps=[
            RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"}),
            RoutineStep(order=2, skill_id="system.weather", args={"city": "Koeln"}),
        ],
    )
    store.create_routine(payload)

    try:
        store.create_routine(payload.model_copy(update={"name": "Routine B"}))
    except DuplicateRoutineError:
        pass
    else:
        raise AssertionError("expected DuplicateRoutineError")


def test_unknown_skill_id_is_rejected(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    try:
        store.create_routine(
            RoutineCreate(
                user_id=user.id,
                name="Broken",
                steps=[RoutineStep(order=1, skill_id="system.unknown", args={})],
            )
        )
    except RoutineValidationError as exc:
        assert "unknown skill_id" in str(exc)
    else:
        raise AssertionError("expected RoutineValidationError")


def test_update_and_delete_routine(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)
    created = store.create_routine(
        RoutineCreate(
            user_id=user.id,
            name="Routine A",
            trigger_phrases=["Routine A"],
            steps=[RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"})],
        )
    )

    updated = store.update_routine(
        created.id,
        RoutineUpdate(name="Routine B", trigger_phrases=["Routine B", "routine b"], offer_state="accepted"),
    )
    assert updated.name == "Routine B"
    assert updated.trigger_phrases == ["Routine B"]
    assert updated.offer_state == "accepted"

    assert store.delete_routine(created.id) is True
    assert store.get_routine(created.id) is None


def test_offer_log_is_persisted(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    log_row = store.create_offer_log(
        user_id=user.id,
        step_fingerprint="abc123",
        offer_state="declined",
        chat_id=42,
    )

    fetched = db_session.query(UserRoutineOfferLog).filter(UserRoutineOfferLog.id == log_row.id).one()
    assert fetched.step_fingerprint == "abc123"
    assert fetched.offer_state == "declined"
    assert fetched.chat_id == 42


def _qualifying_trace():
    return [
        {
            "skill_id": "calendar.list_events",
            "status": "ok",
            "args": {"range": "today"},
            "risk_level": "low",
        },
        {
            "skill_id": "system.weather",
            "status": "ok",
            "args": {"city": "Koeln"},
            "risk_level": "medium",
        },
    ]


def test_record_learning_candidate_creates_internal_candidate_not_visible_routine(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    created = store.record_learning_candidate_if_eligible(
        _qualifying_trace(),
        user_id=user.id,
        source_chat_id=7,
    )

    assert created is not None
    assert created.status == "active"
    assert created.confirmed_at is None
    assert store.list_active_candidates(user.id) == [created]
    assert db_session.query(UserRoutine).filter(UserRoutine.user_id == user.id).count() == 0


def test_record_learning_candidate_is_idempotent_for_same_fingerprint(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    first = store.record_learning_candidate_if_eligible(_qualifying_trace(), user_id=user.id)
    second = store.record_learning_candidate_if_eligible(_qualifying_trace(), user_id=user.id)

    assert first is not None
    assert second is None
    assert len(store.list_active_candidates(user.id)) == 1


def test_expired_candidate_is_not_active_learning_candidate(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    created = store.record_learning_candidate_if_eligible(_qualifying_trace(), user_id=user.id)
    assert created is not None

    created.expires_at = datetime.utcnow() - timedelta(days=1)
    db_session.add(created)
    db_session.commit()

    assert store.list_active_candidates(user.id) == []
    assert store.is_candidate_active(created) is False

    db_session.refresh(created)
    assert created.status == "expired"


def test_promote_candidate_to_routine_marks_candidate_confirmed(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    created = store.record_learning_candidate_if_eligible(_qualifying_trace(), user_id=user.id, source_chat_id=11)
    assert created is not None

    promoted = store.promote_candidate_to_routine(
        created.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        source_chat_id=12,
    )

    db_session.refresh(created)
    assert promoted.user_id == user.id
    assert promoted.offer_state == "auto_promoted"
    assert created.status == "promoted"
    assert created.confirmed_at is not None
    assert store.list_active_candidates(user.id) == []


def test_risky_trace_does_not_create_candidate(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)

    risky_trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
        {"skill_id": "communication.list_emails", "status": "ok", "args": {"unread_only": True}, "risk_level": "high"},
    ]

    created = store.record_learning_candidate_if_eligible(risky_trace, user_id=user.id)

    assert created is None
    assert db_session.query(UserRoutineCandidate).filter(UserRoutineCandidate.user_id == user.id).count() == 0


class _ToolManagerStub:
    """Minimal ToolManager stand-in without CapabilityRegistry._available_skills."""

    def __init__(self, skill_ids: set[str] | None = None) -> None:
        if skill_ids is not None:
            self.tools = {skill_id: object() for skill_id in skill_ids}
            self._skill_mapping: dict[str, str] = {}
            self._skill_metadata = {skill_id: object() for skill_id in skill_ids}
            return
        self._skill_mapping = {
            "calendar_list_events": "calendar.list_events",
            "system_routing": "system.routing",
        }
        self._skill_metadata = {}


def test_create_candidate_accepts_tool_manager_backed_skill_ids(db_session):
    user = _seed_user(db_session)
    store = RoutineStore(
        db_session,
        _ToolManagerStub({"calendar.list_events", "system.routing"}),
    )
    steps = [
        RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"}),
        RoutineStep(order=2, skill_id="system.routing", args={"from_city": "Berlin", "to_city": "Hamburg"}),
    ]

    created = store.create_candidate(user_id=user.id, steps=steps)

    assert created is not None
    assert created.status == "active"


def test_tool_manager_backed_unknown_skill_id_is_rejected(db_session):
    user = _seed_user(db_session)
    store = RoutineStore(db_session, _ToolManagerStub({"calendar.list_events", "system.routing"}))

    try:
        store.create_candidate(
            user_id=user.id,
            steps=[RoutineStep(order=1, skill_id="system.unknown", args={})],
        )
    except RoutineValidationError as exc:
        assert "unknown skill_id" in str(exc)
    else:
        raise AssertionError("expected RoutineValidationError")


def test_validate_skill_ids_accepts_toolmanager_backed_skills(db_session):
    user = _seed_user(db_session)
    store = RoutineStore(db_session, _ToolManagerStub())

    created = store.create_candidate(
        user_id=user.id,
        steps=[
            RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"}),
            RoutineStep(order=2, skill_id="system.routing", args={"from": "Berlin", "to": "Hamburg"}),
        ],
    )

    assert created is not None
    assert created.status == "active"


def test_validate_skill_ids_rejects_unknown_with_toolmanager_stub(db_session):
    user = _seed_user(db_session)
    store = RoutineStore(db_session, _ToolManagerStub())

    try:
        store.create_candidate(
            user_id=user.id,
            steps=[RoutineStep(order=1, skill_id="system.unknown", args={})],
        )
    except RoutineValidationError as exc:
        assert "unknown skill_id" in str(exc)
    else:
        raise AssertionError("expected RoutineValidationError")


def test_create_candidate_rejects_duplicate_active_fingerprint(db_session, tmp_path):
    registry = _build_registry(tmp_path)
    user = _seed_user(db_session)
    store = RoutineStore(db_session, registry)
    steps = [
        RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"}),
        RoutineStep(order=2, skill_id="system.weather", args={"city": "Koeln"}),
    ]

    store.create_candidate(user_id=user.id, steps=steps)

    try:
        store.create_candidate(user_id=user.id, steps=steps)
    except DuplicateCandidateError:
        pass
    else:
        raise AssertionError("expected DuplicateCandidateError")
