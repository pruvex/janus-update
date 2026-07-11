import pytest

from backend.data.models import User, UserRoutine
from backend.services.workflow.routine_runner import RoutineRunner
from backend.services.workflow.workflow_offer_service import (
    find_pending_offer,
    handle_offer_response,
    maybe_append_workflow_offer,
)


class _RegistryStub:
    def __init__(self) -> None:
        self._available_skills = {
            "calendar.list_events",
            "system.weather",
            "system.wikipedia_summary",
            "communication.list_emails",
        }


class _ExecutorStub:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def call_internal_skill(self, skill_id, args):
        self.calls.append((skill_id, dict(args)))
        response = self.responses.get(skill_id)
        if callable(response):
            return response(args)
        return response or {"status": "ok", "data": {"summary": skill_id}}


@pytest.mark.asyncio
async def test_execute_by_trigger_runs_steps_and_updates_metadata(db_session):
    user = User(username="runner", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Morgen-Routine",
        trigger_phrases=["Morgen-Routine", "Start meinen Tag"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "{{user.city}}"},
                    "arg_bindings": {"city": "memory:wohnort"},
                },
            ],
        },
        step_fingerprint="abc",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()
    db_session.refresh(routine)

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "3 Termine"}},
            "system.weather": {"status": "ok", "data": {"summary": "18C und sonnig"}},
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Bitte starte meine Morgen-Routine",
        user_id=user.id,
        memory_context={"wohnort": "Koeln"},
    )

    db_session.refresh(routine)
    assert result.found is True
    assert result.executed is True
    assert result.status == "ok"
    assert result.matched_trigger == "Morgen-Routine"
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.weather", {"city": "Koeln"}),
    ]
    assert routine.run_count == 1
    assert routine.last_run_at is not None
    assert "18C und sonnig" in result.response_text


@pytest.mark.asyncio
async def test_execute_by_trigger_stops_on_permission_block(db_session):
    user = User(username="runner-block", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Inbox-Routine",
        trigger_phrases=["Inbox-Routine"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {"order": 2, "skill_id": "communication.list_emails", "args": {"unread_only": True}, "arg_bindings": {}},
            ],
        },
        step_fingerprint="def",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()
    db_session.refresh(routine)

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "2 Termine"}},
            "communication.list_emails": {
                "status": "permission_required",
                "error": {"message": "Zustimmung fuer Mail-Zugriff erforderlich."},
            },
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger("Inbox-Routine", user_id=user.id)

    db_session.refresh(routine)
    assert result.executed is False
    assert result.status == "blocked"
    assert result.failed_step == "communication.list_emails"
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("communication.list_emails", {"unread_only": True}),
    ]
    assert routine.run_count == 1
    assert "Zustimmung" in result.response_text


@pytest.mark.asyncio
async def test_offer_save_to_execute_roundtrip(db_session):
    db_session.add(User(username="workflow-runner", hashed_password="x"))
    db_session.commit()

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
        user_text="Bitte pruefe Termine und Wetter",
        messages=[],
    )
    pending = find_pending_offer([{"role": "assistant", "content": offer_text}])
    assert pending is not None

    save_result = handle_offer_response(
        "Ja, speichere das",
        messages=[{"role": "assistant", "content": offer_text}],
        db=db_session,
        capability_registry=_RegistryStub(),
        chat_id=99,
    )
    assert save_result.saved_routine_id is not None

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "1 Termin"}},
            "system.weather": {"status": "ok", "data": {"summary": "Sonnig"}},
        }
    )
    runner = RoutineRunner(db_session, executor)

    execute_result = await runner.execute_by_trigger(
        pending.suggested_name,
        memory_context={"wohnort": "Koeln"},
    )

    assert execute_result.executed is True
    assert execute_result.routine_id == save_result.saved_routine_id
    assert executor.calls[1] == ("system.weather", {"city": "Koeln"})


@pytest.mark.asyncio
async def test_execute_by_trigger_returns_not_found_when_missing(db_session):
    db_session.add(User(username="workflow-empty", hashed_password="x"))
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger("Unbekannte Routine")

    assert result.found is False
    assert result.status == "not_found"
    assert result.response_text == "Keine Routine gefunden."


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_weather_without_routine_name(db_session):
    user = User(username="semantic-runner", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "{{user.city}}"},
                    "arg_bindings": {"city": "memory:wohnort"},
                },
            ],
        },
        step_fingerprint="calendar-weather",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()
    db_session.refresh(routine)

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "2 Termine"}},
            "system.weather": {"status": "ok", "data": {"summary": "20C und bewoelkt"}},
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        user_id=user.id,
        memory_context={"wohnort": "Koeln"},
    )

    assert result.found is True
    assert result.executed is True
    assert result.status == "ok"
    assert result.matched_trigger == "semantic:calendar.list_events,system.weather"
    assert "passende gespeicherte Routine" in result.response_text
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.weather", {"city": "Koeln"}),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "phrase",
    [
        "Pruefe Termine fuer heute und Wetter in Koeln",
        "Zeig mir meine Termine heute und das Wetter in Koeln",
        "Termine und Wetter Koeln heute",
        "Kalender und Wetter fuer heute in Koeln",
    ],
)
async def test_execute_by_trigger_semantic_match_natural_calendar_weather_phrases(db_session, phrase):
    user = User(username="semantic-natural", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Kalender Wetter",
        trigger_phrases=["Routine Kalender Wetter"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {"order": 2, "skill_id": "system.weather", "args": {"city": "Koeln", "date_str": "heute"}, "arg_bindings": {}},
            ],
        },
        step_fingerprint="calendar-weather-natural",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "0 Termine"}},
            "system.weather": {"status": "ok", "data": {"summary": "Sonnig"}},
        }
    )
    runner = RoutineRunner(db_session, executor)
    result = await runner.execute_by_trigger(phrase, user_id=user.id)

    assert result.found is True
    assert result.executed is True
    assert result.matched_trigger == "semantic:calendar.list_events,system.weather"
    assert "passende gespeicherte Routine" in result.response_text


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_formats_calendar_wikipedia_naturally(db_session):
    user = User(username="semantic-wiki-render", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Kalender Wikipedia",
        trigger_phrases=["Routine Kalender Wikipedia"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.wikipedia_summary",
                    "args": {"query": "Berlin"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-wikipedia-render",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.wikipedia_summary": {
                "status": "ok",
                "data": {
                    "title": "Berlin",
                    "summary": "Berlin ist die Hauptstadt Deutschlands.",
                    "url": "https://de.wikipedia.org/wiki/Berlin",
                },
            },
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin.",
        user_id=user.id,
    )

    assert result.executed is True
    assert result.matched_trigger == "semantic:calendar.list_events,system.wikipedia_summary"
    assert "Ich habe deine passende gespeicherte Routine genutzt." in result.response_text
    assert "Keine Termine im angegebenen Zeitraum gefunden." in result.response_text
    assert "Berlin ist die Hauptstadt Deutschlands." in result.response_text
    assert "calendar.list_events" not in result.response_text
    assert "events: []" not in result.response_text
    assert "erfolgreich ausgefuehrt" not in result.response_text


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_reuses_wikipedia_snapshot_for_same_query(db_session):
    user = User(username="semantic-wiki-snapshot", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Kalender Wikipedia",
        trigger_phrases=["Routine Kalender Wikipedia"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.wikipedia_summary",
                    "args": {"query": "Berlin"},
                    "arg_bindings": {},
                    "output_snapshot": (
                        "Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum."
                    ),
                    "snapshot_query": "Berlin",
                },
            ],
        },
        step_fingerprint="calendar-wikipedia-snapshot",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.wikipedia_summary": {
                "status": "ok",
                "data": {
                    "title": "Berlin",
                    "summary": "Berlin ist die Hauptstadt Deutschlands.",
                    "url": "https://de.wikipedia.org/wiki/Berlin",
                },
            },
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin.",
        user_id=user.id,
    )

    assert result.executed is True
    assert "wichtiges europaeisches Zentrum" in result.response_text
    assert "Berlin ist die Hauptstadt Deutschlands." not in result.response_text


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_rebind_uses_fresh_wikipedia_summary(db_session):
    user = User(username="semantic-wiki-rebind", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Kalender Wikipedia",
        trigger_phrases=["Routine Kalender Wikipedia"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.wikipedia_summary",
                    "args": {"query": "Berlin"},
                    "arg_bindings": {},
                    "output_snapshot": (
                        "Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum."
                    ),
                    "snapshot_query": "Berlin",
                },
            ],
        },
        step_fingerprint="calendar-wikipedia-rebind",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.wikipedia_summary": {
                "status": "ok",
                "data": {
                    "title": "Muenchen",
                    "summary": "Muenchen ist die Landeshauptstadt Bayerns.",
                    "url": "https://de.wikipedia.org/wiki/Muenchen",
                },
            },
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Muenchen.",
        user_id=user.id,
    )

    assert result.executed is True
    assert executor.calls[1] == ("system.wikipedia_summary", {"query": "Muenchen"})
    assert "Landeshauptstadt Bayerns" in result.response_text
    assert "wichtiges europaeisches Zentrum" not in result.response_text


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_formats_calendar_weather_naturally(db_session):
    user = User(username="semantic-render", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "{{user.city}}"},
                    "arg_bindings": {"city": "memory:wohnort"},
                },
            ],
        },
        step_fingerprint="calendar-weather-render",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.weather": {
                "status": "ok",
                "data": {
                    "forecast": "Das Wetter fuer Koeln (heute, 09.07.2026) im Ueberblick:\n* Zustand: Bedeckt\n\nQuelle: Open-Meteo"
                },
            },
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        user_id=user.id,
        memory_context={"wohnort": "Koeln"},
    )

    assert result.executed is True
    assert "Ich habe deine passende gespeicherte Routine genutzt." in result.response_text
    assert "Keine Termine im angegebenen Zeitraum gefunden." in result.response_text
    assert "Das Wetter fuer Koeln" in result.response_text
    assert "calendar.list_events" not in result.response_text
    assert "events: []" not in result.response_text


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_does_not_run_unrelated_request(db_session):
    user = User(username="semantic-guard", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "Koeln"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-weather",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Wie wird das Wetter in Berlin?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_rebinds_different_weather_city(db_session):
    user = User(username="semantic-city-guard", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "{{user.city}}"},
                    "arg_bindings": {"city": "memory:wohnort"},
                },
            ],
        },
        step_fingerprint="calendar-weather",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.weather": {
                "status": "ok",
                "message": "In Berlin wird es heute sonnig.",
                "data": {"city": "Berlin"},
            },
        }
    )
    runner = RoutineRunner(db_session, executor)
    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und wie wird das Wetter in Berlin?",
        user_id=user.id,
        memory_context={"wohnort": "Koeln"},
    )

    assert result.found is True
    assert result.executed is True
    assert result.status == "ok"
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.weather", {"city": "Berlin"}),
    ]


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_rebinds_different_weather_date_reference(db_session):
    user = User(username="semantic-date-guard", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "{{user.city}}"},
                    "arg_bindings": {"city": "memory:wohnort"},
                },
            ],
        },
        step_fingerprint="calendar-weather",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.weather": {
                "status": "ok",
                "message": "In Koeln wird es morgen regnerisch.",
                "data": {"city": "Koeln", "date_str": "morgen"},
            },
        }
    )
    runner = RoutineRunner(db_session, executor)
    result = await runner.execute_by_trigger(
        "habe ich heute noch termine und wie wird morgen das wetter in Koeln?",
        user_id=user.id,
        memory_context={"wohnort": "Koeln"},
    )

    assert result.found is True
    assert result.executed is True
    assert result.status == "ok"
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.weather", {"city": "Koeln", "date_str": "morgen"}),
    ]


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_routing_without_routine_name(db_session):
    user = User(username="semantic-routing-runner", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"from_city": "Berlin", "to_city": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()
    db_session.refresh(routine)

    executor = _ExecutorStub(
        {
            "calendar.list_events": {
                "status": "ok",
                "data": {"events": [], "listing_text": "", "event_count": 0},
                "message": "Keine Termine im angegebenen Zeitraum gefunden.",
            },
            "system.routing": {
                "status": "ok",
                "message": "Die Entfernung von Berlin nach Hamburg betraegt etwa 290 Kilometer.",
                "data": {
                    "origin": "Berlin",
                    "destination": "Hamburg",
                    "distance_km": 290,
                    "duration_text": "3 Std.",
                },
            },
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        user_id=user.id,
    )

    assert result.found is True
    assert result.executed is True
    assert result.status == "ok"
    assert result.matched_trigger == "semantic:calendar.list_events,system.routing"
    assert "passende gespeicherte Routine" in result.response_text
    assert "Keine Termine im angegebenen Zeitraum gefunden." in result.response_text
    assert "Berlin nach Hamburg" in result.response_text
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.routing", {"from_city": "Berlin", "to_city": "Hamburg"}),
    ]


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_routing_rebinds_fresh_route(db_session):
    user = User(username="semantic-routing-rebind", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Berlin", "destination": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-rebind",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "1 Termin"}},
            "system.routing": {"status": "ok", "data": {"summary": "route ok"}},
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute und wie weit ist es von Koeln nach Paris?",
        user_id=user.id,
    )

    assert result.executed is True
    assert result.matched_trigger == "semantic:calendar.list_events,system.routing"
    assert executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.routing", {"origin": "Koeln", "destination": "Paris"}),
    ]


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_routing_rebinds_fresh_date(db_session):
    user = User(username="semantic-routing-date", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"from_city": "Berlin", "to_city": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-date",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "0 Termine"}},
            "system.routing": {"status": "ok", "data": {"summary": "route ok"}},
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Welche Termine habe ich morgen und wie weit ist es von Berlin nach Hamburg?",
        user_id=user.id,
    )

    assert result.executed is True
    assert executor.calls[0] == ("calendar.list_events", {"range": "tomorrow"})


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_routing_rejects_missing_date_reference(db_session):
    user = User(username="semantic-routing-missing-date", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Berlin", "destination": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-missing-date",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Welche Termine habe ich und wie weit ist es von Berlin nach Hamburg?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_routing_rejects_conflicting_date_reference(db_session):
    user = User(username="semantic-routing-conflicting-date", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Berlin", "destination": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-conflicting-date",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute oder morgen und wie weit ist es von Berlin nach Hamburg?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_calendar_routing_rejects_multiple_superficial_routines(db_session):
    user = User(username="semantic-routing-ambiguous-routines", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    first_routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing One",
        trigger_phrases=["Routine Calendar Routing One"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Berlin", "destination": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-ambiguous-1",
        user_approved=True,
        offer_state="accepted",
    )
    second_routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing Two",
        trigger_phrases=["Routine Calendar Routing Two"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Koeln", "destination": "Paris"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-ambiguous-2",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(first_routine)
    db_session.add(second_routine)
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_rejects_missing_routing_parameters(db_session):
    user = User(username="semantic-routing-missing", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Berlin", "destination": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-missing",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute und wie weit ist die Strecke?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_rejects_missing_weather_city(db_session):
    user = User(username="semantic-weather-missing-city", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine List Events",
        trigger_phrases=["Routine List Events"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.weather",
                    "args": {"city": "Koeln"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-weather-missing-city",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und wie wird das Wetter?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_rejects_ambiguous_multiple_routines(db_session):
    user = User(username="semantic-ambiguous", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    for city in ("Koeln", "Berlin"):
        db_session.add(
            UserRoutine(
                user_id=user.id,
                name=f"Routine Weather {city}",
                trigger_phrases=[f"Routine Weather {city}"],
                steps_json={
                    "version": 1,
                    "steps": [
                        {
                            "order": 1,
                            "skill_id": "calendar.list_events",
                            "args": {"range": "today"},
                            "arg_bindings": {},
                        },
                        {
                            "order": 2,
                            "skill_id": "system.weather",
                            "args": {"city": city},
                            "arg_bindings": {},
                        },
                    ],
                },
                step_fingerprint=f"calendar-weather-{city.lower()}",
                user_approved=True,
                offer_state="accepted",
            )
        )
    db_session.commit()

    runner = RoutineRunner(db_session, _ExecutorStub({}))
    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und wie wird das Wetter?",
        user_id=user.id,
    )

    assert result.found is False
    assert result.status == "not_found"


@pytest.mark.asyncio
async def test_execute_by_trigger_semantic_match_does_not_reuse_stale_routing_values(db_session):
    user = User(username="semantic-routing-stale", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    routine = UserRoutine(
        user_id=user.id,
        name="Routine Calendar Routing",
        trigger_phrases=["Routine Calendar Routing"],
        steps_json={
            "version": 1,
            "steps": [
                {"order": 1, "skill_id": "calendar.list_events", "args": {"range": "today"}, "arg_bindings": {}},
                {
                    "order": 2,
                    "skill_id": "system.routing",
                    "args": {"origin": "Berlin", "destination": "Hamburg"},
                    "arg_bindings": {},
                },
            ],
        },
        step_fingerprint="calendar-routing-stale",
        user_approved=True,
        offer_state="accepted",
    )
    db_session.add(routine)
    db_session.commit()

    executor = _ExecutorStub(
        {
            "calendar.list_events": {"status": "ok", "data": {"summary": "0 Termine"}},
            "system.routing": {"status": "ok", "data": {"summary": "route ok"}},
        }
    )
    runner = RoutineRunner(db_session, executor)

    result = await runner.execute_by_trigger(
        "Welche Termine habe ich heute und wie weit ist es von Koeln nach Paris?",
        user_id=user.id,
    )

    assert result.executed is True
    assert executor.calls[1] == ("system.routing", {"origin": "Koeln", "destination": "Paris"})
    assert executor.calls[1] != ("system.routing", {"origin": "Berlin", "destination": "Hamburg"})
