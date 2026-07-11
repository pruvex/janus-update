import json
from datetime import date

import pytest

from backend.data.models import User, UserRoutineCandidate, UserRoutineOfferLog
from backend.services.chat_orchestrator import _resolve_routine_offer_messages
from backend.services.orchestrator.intent_engine import intent_engine
from backend.services.workflow.routine_schema import RoutineCreate, RoutineStep
from backend.services.workflow.routine_runner import RoutineRunner
from backend.services.workflow.routine_store import RoutineStore
from backend.services.workflow.workflow_offer_service import (
    find_pending_offer,
    handle_offer_response,
    maybe_learn_routine_passively,
    maybe_append_workflow_offer,
    should_handle_offer_follow_up,
)


class _RegistryStub:
    def __init__(self) -> None:
        self._available_skills = {"calendar.list_events", "system.weather", "system.routing"}


class _ExecutorStub:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def call_internal_skill(self, skill_id, args):
        self.calls.append((skill_id, dict(args)))
        return self.responses.get(skill_id) or {"status": "ok", "data": {"summary": skill_id}}


def _registry() -> _RegistryStub:
    return _RegistryStub()


def test_maybe_append_workflow_offer_adds_marker_for_candidate():
    text = maybe_append_workflow_offer(
        "Hier ist dein Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ],
        user_text="Was steht heute an und wie wird das Wetter?",
        messages=[],
    )

    assert "als Routine" in text
    pending = find_pending_offer([{"role": "assistant", "content": text}])
    assert pending is not None
    assert pending.suggested_name == "Routine Kalender Wetter"
    assert [step.skill_id for step in pending.steps] == ["calendar.list_events", "system.weather"]


def test_maybe_learn_routine_passively_creates_silent_candidate_without_offer_marker(db_session):
    db_session.add(User(username="workflow-passive-create", hashed_password="x"))
    db_session.commit()

    result = maybe_learn_routine_passively(
        "Hier ist dein Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Berlin"}, "risk_level": "medium"},
        ],
        user_text="Pruefe meine Termine fuer heute und gib mir dazu das Wetter in Berlin.",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=77,
    )

    assert result.handled is True
    assert result.learning_state == "candidate_created"
    assert "als Routine" not in result.final_text
    assert "JANUS_ROUTINE_OFFER" not in result.final_text
    assert find_pending_offer([{"role": "assistant", "content": result.final_text}]) is None


def test_maybe_learn_routine_passively_promotes_second_matching_case_with_passive_hint(db_session):
    user = User(username="workflow-passive-promote", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    first = maybe_learn_routine_passively(
        "Keine Termine.\n\nDas Wetter fuer Berlin (heute).",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Berlin"}, "risk_level": "medium"},
        ],
        user_text="Pruefe meine Termine fuer heute und gib mir dazu das Wetter in Berlin.",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=17,
    )
    second = maybe_learn_routine_passively(
        "Keine Termine.\n\nDas Wetter fuer Berlin (heute).",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Berlin"}, "risk_level": "medium"},
        ],
        user_text="Pruefe meine Termine fuer heute und gib mir dazu das Wetter in Berlin.",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=18,
    )

    assert first.learning_state == "candidate_created"
    assert second.handled is True
    assert second.learning_state == "promoted"
    assert "Ich habe dafuer eine passende Routine gespeichert." in second.final_text
    assert "JANUS_ROUTINE_OFFER" not in second.final_text


def test_maybe_learn_routine_passively_promotes_equivalent_calendar_routing_with_order_and_arg_drift(db_session):
    user = User(username="workflow-passive-calendar-routing", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    today = date.today().isoformat()

    first = maybe_learn_routine_passively(
        "Keine Termine.\n\nDie Entfernung von Berlin nach Hamburg betraegt etwa 290 Kilometer.",
        tool_results=[
            {
                "skill_id": "system.routing",
                "status": "ok",
                "args": {"from_city": "Berlin", "to_city": "Hamburg"},
                "risk_level": "medium",
            },
            {
                "skill_id": "calendar.list_events",
                "status": "ok",
                "args": {"start_date": today, "end_date": today},
                "risk_level": "low",
            },
        ],
        user_text="Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=4235,
    )
    second = maybe_learn_routine_passively(
        "Keine Termine.\n\nDie Entfernung von Berlin nach Hamburg betraegt etwa 290 Kilometer.",
        tool_results=[
            {
                "skill_id": "calendar.list_events",
                "status": "ok",
                "args": {"range": "today"},
                "risk_level": "low",
            },
            {
                "skill_id": "system.routing",
                "status": "ok",
                "args": {"origin": "Berlin", "destination": "Hamburg"},
                "risk_level": "medium",
            },
        ],
        user_text="Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=4239,
    )

    assert first.learning_state == "candidate_created"
    assert second.handled is True
    assert second.learning_state == "promoted"
    assert "Ich habe dafuer eine passende Routine gespeichert." in second.final_text
    assert "JANUS_ROUTINE_OFFER" not in second.final_text


def test_maybe_learn_routine_passively_keeps_distinct_calendar_routing_route_separate(db_session):
    user = User(username="workflow-passive-calendar-routing-distinct", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    today = date.today().isoformat()

    first = maybe_learn_routine_passively(
        "Keine Termine.\n\nDie Entfernung von Berlin nach Hamburg betraegt etwa 290 Kilometer.",
        tool_results=[
            {
                "skill_id": "system.routing",
                "status": "ok",
                "args": {"from_city": "Berlin", "to_city": "Hamburg"},
                "risk_level": "medium",
            },
            {
                "skill_id": "calendar.list_events",
                "status": "ok",
                "args": {"start_date": today, "end_date": today},
                "risk_level": "low",
            },
        ],
        user_text="Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=5001,
    )
    second = maybe_learn_routine_passively(
        "Keine Termine.\n\nDie Entfernung von Koeln nach Paris betraegt etwa 490 Kilometer.",
        tool_results=[
            {
                "skill_id": "calendar.list_events",
                "status": "ok",
                "args": {"range": "today"},
                "risk_level": "low",
            },
            {
                "skill_id": "system.routing",
                "status": "ok",
                "args": {"origin": "Koeln", "destination": "Paris"},
                "risk_level": "medium",
            },
        ],
        user_text="Welche Termine habe ich heute und wie weit ist es von Koeln nach Paris?",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=5002,
    )

    assert first.learning_state == "candidate_created"
    assert second.learning_state == "candidate_created"
    assert second.saved_routine_id is None
    assert (
        db_session.query(UserRoutineCandidate)
        .filter(UserRoutineCandidate.user_id == user.id, UserRoutineCandidate.status == "active")
        .count()
        == 2
    )


def test_maybe_learn_routine_passively_suppresses_legacy_offer_when_similar_saved_routine_exists(db_session):
    user = User(username="workflow-passive-suppress-existing", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    store = RoutineStore(db_session, _registry())
    store.create_routine(
        RoutineCreate(
            user_id=user.id,
            name="Routine List Events",
            trigger_phrases=["Routine List Events"],
            steps=[
                RoutineStep(order=1, skill_id="calendar.list_events", args={"days_in_future": 0}),
                RoutineStep(order=2, skill_id="system.weather", args={"city": "Berlin", "date_str": "heute"}),
            ],
            user_approved=True,
            offer_state="accepted",
        )
    )

    result = maybe_learn_routine_passively(
        "Keine Termine.\n\nDas Wetter fuer Berlin (heute).",
        tool_results=[
            {"name": "calendar_list_events", "status": "success", "args": {"days_in_future": 0}},
            {"name": "system_weather", "status": "success", "args": {"city": "Berlin", "date_str": "heute"}},
        ],
        user_text="Pruefe meine Termine fuer heute und gib mir dazu das Wetter in Berlin.",
        messages=[],
        db=db_session,
        capability_registry=_registry(),
        chat_id=19,
    )

    assert result.handled is True
    assert result.learning_state == "suppressed"
    assert "JANUS_ROUTINE_OFFER" not in result.final_text
    assert "als Routine" not in result.final_text


def test_handle_offer_response_accept_saves_routine(db_session):
    db_session.add(User(username="workflow", hashed_password="x"))
    db_session.commit()

    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ],
        user_text="Bitte pruefe Termine und Wetter",
        messages=[],
    )

    result = handle_offer_response(
        "Ja, speichere das",
        messages=[{"role": "assistant", "content": offer_text}],
        db=db_session,
        capability_registry=_registry(),
        chat_id=42,
    )

    assert result.handled is True
    assert result.offer_state == "accepted"
    assert result.saved_routine_id is not None


def test_handle_offer_response_decline_logs_outcome(db_session):
    db_session.add(User(username="workflow", hashed_password="x"))
    db_session.commit()

    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ],
        user_text="Bitte pruefe Termine und Wetter",
        messages=[],
    )

    result = handle_offer_response(
        "Nicht mehr fragen",
        messages=[{"role": "assistant", "content": offer_text}],
        db=db_session,
        capability_registry=_registry(),
        chat_id=7,
    )

    logged = db_session.query(UserRoutineOfferLog).order_by(UserRoutineOfferLog.id.desc()).first()
    assert result.handled is True
    assert result.offer_state == "denylisted"
    assert logged is not None
    assert logged.offer_state == "denylisted"


def test_should_handle_offer_follow_up_only_when_pending_offer_exists():
    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ],
        user_text="Bitte pruefe Termine und Wetter",
        messages=[],
    )

    assert should_handle_offer_follow_up("Ja", messages=[{"role": "assistant", "content": offer_text}]) is True
    assert should_handle_offer_follow_up("Nein", messages=[{"role": "assistant", "content": offer_text}]) is True
    assert (
        should_handle_offer_follow_up(
            "Ja",
            messages=[{"role": "assistant", "content": "Ich habe einen Mail-Entwurf vorbereitet."}],
        )
        is False
    )


def test_resolve_routine_offer_messages_falls_back_to_db_history_when_wf_messages_empty():
    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ],
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        messages=[],
    )

    db_messages = [
        {"role": "user", "content": "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?"},
        {"role": "assistant", "content": offer_text},
    ]

    resolved = _resolve_routine_offer_messages([], db_messages)
    assert resolved == db_messages
    assert should_handle_offer_follow_up("Ja", messages=resolved) is True


def test_resolve_routine_offer_messages_prefers_in_memory_pending_offer():
    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ],
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        messages=[],
    )

    wf_messages = [{"role": "assistant", "content": offer_text}]
    db_messages = [{"role": "assistant", "content": "Ich habe einen Mail-Entwurf vorbereitet."}]

    resolved = _resolve_routine_offer_messages(wf_messages, db_messages)
    assert resolved == wf_messages


def test_maybe_append_workflow_offer_adds_marker_for_live_tool_result_shape():
    text = maybe_append_workflow_offer(
        "Hier ist dein Ergebnis.",
        tool_results=[
            {"_skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}},
            {"_skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}},
        ],
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        messages=[],
    )

    assert "als Routine" in text
    pending = find_pending_offer([{"role": "assistant", "content": text}])
    assert pending is not None
    assert [step.skill_id for step in pending.steps] == ["calendar.list_events", "system.weather"]


def test_maybe_append_workflow_offer_adds_marker_for_openai_name_alias_shape():
    text = maybe_append_workflow_offer(
        "Keine Termine.\n\nWetter fuer Koeln.",
        tool_results=[
            {"name": "calendar_list_events", "status": "success", "args": {"days_in_future": 0}},
            {"name": "system_weather", "status": "success", "args": {"city": "Koeln", "date_str": "heute"}},
        ],
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        messages=[],
    )

    assert "als Routine" in text
    pending = find_pending_offer([{"role": "assistant", "content": text}])
    assert pending is not None
    assert [step.skill_id for step in pending.steps] == ["calendar.list_events", "system.weather"]


def test_maybe_append_workflow_offer_adds_marker_for_content_only_tool_result_shape():
    text = maybe_append_workflow_offer(
        "Keine Termine.\n\nDas Wetter fuer Koeln (heute).",
        tool_results=[
            {
                "role": "tool",
                "name": "calendar_list_events",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {"events": [], "listing_text": "", "event_count": 0},
                        "message": "Keine Termine im angegebenen Zeitraum gefunden.",
                        "output": "Keine Termine im angegebenen Zeitraum gefunden.",
                    },
                    ensure_ascii=False,
                ),
            },
            {
                "role": "tool",
                "name": "system_weather",
                "_raw_content": json.dumps(
                    {
                        "status": "ok",
                        "data": {"forecast": "Das Wetter fuer Koeln (heute).", "city": "Koeln"},
                        "message": "Das Wetter fuer Koeln (heute).",
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        messages=[],
    )

    assert "als Routine" in text
    pending = find_pending_offer([{"role": "assistant", "content": text}])
    assert pending is not None
    assert [step.skill_id for step in pending.steps] == ["calendar.list_events", "system.weather"]


def test_detect_routine_semantic_signature_calendar_weather_combo():
    skills = frozenset({"calendar.list_events", "system.weather"})
    matched = intent_engine.match_routine_semantic_signature(
        "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        skills,
    )
    assert matched == "semantic:calendar.list_events,system.weather"
    assert (
        intent_engine.match_routine_semantic_signature(
            "Wie wird das Wetter in Berlin?",
            skills,
        )
        is None
    )


@pytest.mark.asyncio
async def test_saved_calendar_weather_routine_reused_from_natural_request(db_session):
    user = User(username="workflow-semantic", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {
                "skill_id": "system.weather",
                "status": "ok",
                "args": {"city": "{{user.city}}"},
                "arg_bindings": {"city": "memory:wohnort"},
                "risk_level": "medium",
            },
        ],
        user_text="Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        messages=[],
    )

    save_result = handle_offer_response(
        "Ja, speichere das",
        messages=[{"role": "assistant", "content": offer_text}],
        db=db_session,
        capability_registry=_registry(),
        chat_id=55,
    )
    assert save_result.saved_routine_id is not None

    runner = RoutineRunner(
        db_session,
        _ExecutorStub(
            {
                "calendar.list_events": {"status": "ok", "data": {"summary": "1 Termin"}},
                "system.weather": {"status": "ok", "data": {"summary": "Sonnig"}},
            }
        ),
    )
    execute_result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        user_id=user.id,
        memory_context={"wohnort": "Koeln"},
    )

    assert execute_result.executed is True
    assert execute_result.routine_id == save_result.saved_routine_id
    assert execute_result.matched_trigger == "semantic:calendar.list_events,system.weather"
    assert "passende gespeicherte Routine" in execute_result.response_text


def test_detect_routine_semantic_signature_calendar_routing_combo():
    skills = frozenset({"calendar.list_events", "system.routing"})
    matched = intent_engine.match_routine_semantic_signature(
        "Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        skills,
    )
    assert matched == "semantic:calendar.list_events,system.routing"
    assert (
        intent_engine.match_routine_semantic_signature(
            "Wie weit ist es von Berlin nach Hamburg?",
            skills,
        )
        is None
    )


@pytest.mark.asyncio
async def test_saved_calendar_routing_routine_reused_from_natural_request(db_session):
    user = User(username="workflow-semantic-routing", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    offer_text = maybe_append_workflow_offer(
        "Ergebnis.",
        tool_results=[
            {
                "skill_id": "calendar.list_events",
                "status": "ok",
                "args": {"range": "today"},
                "risk_level": "low",
            },
            {
                "skill_id": "system.routing",
                "status": "ok",
                "args": {"from_city": "Berlin", "to_city": "Hamburg"},
                "risk_level": "medium",
            },
        ],
        user_text="Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        messages=[],
    )

    save_result = handle_offer_response(
        "Ja, speichere das",
        messages=[{"role": "assistant", "content": offer_text}],
        db=db_session,
        capability_registry=_registry(),
        chat_id=56,
    )
    assert save_result.saved_routine_id is not None

    runner = RoutineRunner(
        db_session,
        _ExecutorStub(
            {
                "calendar.list_events": {"status": "ok", "data": {"summary": "1 Termin"}},
                "system.routing": {
                    "status": "ok",
                    "message": "Die Entfernung von Berlin nach Hamburg betraegt etwa 290 Kilometer.",
                },
            }
        ),
    )
    execute_result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        user_id=user.id,
    )

    assert execute_result.executed is True
    assert execute_result.routine_id == save_result.saved_routine_id
    assert execute_result.matched_trigger == "semantic:calendar.list_events,system.routing"
    assert "passende gespeicherte Routine" in execute_result.response_text
