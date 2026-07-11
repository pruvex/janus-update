import pytest

from backend.data.models import User, UserRoutine
from backend.services.orchestrator.intent_engine import intent_engine
from backend.services.workflow.routine_intent_skills import detect_routine_request_skills, routine_skill_probes
from backend.services.workflow.routine_runner import RoutineRunner


def test_routine_skill_probe_registry_covers_core_families():
    skill_ids = {skill_id for skill_id, _ in routine_skill_probes()}
    assert {
        "calendar.list_events",
        "system.weather",
        "system.routing",
        "system.wikipedia_summary",
        "system.websearch",
        "system.rss_news",
        "system.price_comparison",
        "system.local_business",
        "video.search",
    }.issubset(skill_ids)


@pytest.mark.parametrize(
    "phrase",
    [
        "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
        "Pruefe Termine fuer heute und Wetter in Koeln",
    ],
)
def test_generic_registry_detects_calendar_weather(phrase: str):
    assert detect_routine_request_skills(intent_engine, phrase) == frozenset(
        {"calendar.list_events", "system.weather"}
    )


def test_generic_registry_detects_calendar_wikipedia_combo():
    phrase = "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin."
    skills = detect_routine_request_skills(intent_engine, phrase)
    assert skills == frozenset({"calendar.list_events", "system.wikipedia_summary"})


def test_generic_registry_detects_calendar_websearch_combo():
    phrase = "Zeig meine Termine heute und suche im Internet nach OpenAI API Preisen."
    skills = detect_routine_request_skills(intent_engine, phrase)
    assert skills == frozenset({"calendar.list_events", "system.websearch"})


def test_generic_registry_blocks_pure_recall_without_tool_combo():
    phrase = "Was weiss ich ueber Max?"
    skills = detect_routine_request_skills(intent_engine, phrase)
    assert skills == frozenset()


class _ExecutorStub:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def call_internal_skill(self, skill_id, args):
        self.calls.append((skill_id, dict(args)))
        return self.responses.get(skill_id) or {"status": "ok", "data": {"summary": skill_id}}


@pytest.mark.asyncio
async def test_generic_saved_calendar_wikipedia_routine_reused_semantically(db_session):
    user = User(username="generic-wiki", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.add(
        UserRoutine(
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
            step_fingerprint="calendar-wikipedia-generic",
            user_approved=True,
            offer_state="accepted",
        )
    )
    db_session.commit()

    runner = RoutineRunner(
        db_session,
        _ExecutorStub(
            {
                "calendar.list_events": {"status": "ok", "data": {"summary": "0 Termine"}},
                "system.wikipedia_summary": {"status": "ok", "data": {"summary": "Berlin ist..."}},
            }
        ),
    )
    result = await runner.execute_by_trigger(
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin.",
        user_id=user.id,
    )

    assert result.found is True
    assert result.executed is True
    assert result.matched_trigger == "semantic:calendar.list_events,system.wikipedia_summary"
    assert "passende gespeicherte Routine" in result.response_text
    assert runner.executor.calls == [
        ("calendar.list_events", {"range": "today"}),
        ("system.wikipedia_summary", {"query": "Berlin"}),
    ]
