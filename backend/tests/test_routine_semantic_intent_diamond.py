import pytest

from backend.services.orchestrator.intent_engine import intent_engine
from backend.services.workflow.workflow_detector import DetectedWorkflow, detect_workflow_candidate
from backend.services.workflow.workflow_offer_service import suggest_routine_name
from backend.services.workflow.routine_schema import RoutineStep, build_step_fingerprint


CALENDAR_WEATHER_PHRASES = [
    "Was steht heute in meinem Kalender und wie wird das Wetter in Koeln?",
    "Pruefe Termine fuer heute und Wetter in Koeln",
    "Zeig mir meine Termine heute und das Wetter in Koeln",
    "Termine und Wetter Koeln heute",
    "Kalender und Wetter fuer heute in Koeln",
    "Pruefe meine Termine fuer heute und gib mir dazu das Wetter in Berlin.",
]

CALENDAR_WEATHER_NEGATIVE_PHRASES = [
    "Nur Wetter in Muenchen",
    "Wie wird das Wetter in Koeln?",
    "Was steht heute im Kalender?",
]


@pytest.mark.parametrize("phrase", CALENDAR_WEATHER_PHRASES)
def test_routine_request_skills_detect_calendar_weather_combo(phrase: str):
    skills = intent_engine.detect_routine_request_skills(phrase)
    assert skills == frozenset({"calendar.list_events", "system.weather"})


@pytest.mark.parametrize("phrase", CALENDAR_WEATHER_NEGATIVE_PHRASES)
def test_routine_request_skills_reject_incomplete_calendar_weather_combo(phrase: str):
    skills = intent_engine.detect_routine_request_skills(phrase)
    assert skills != frozenset({"calendar.list_events", "system.weather"})


def test_match_routine_semantic_signature_calendar_weather_variants():
    routine_skills = frozenset({"calendar.list_events", "system.weather"})
    for phrase in CALENDAR_WEATHER_PHRASES:
        matched = intent_engine.match_routine_semantic_signature(phrase, routine_skills)
        assert matched == "semantic:calendar.list_events,system.weather", phrase


def test_suggest_routine_name_uses_skill_combo_labels():
    detected = detect_workflow_candidate(
        [
            {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
            {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
        ]
    )
    assert detected.is_offer_candidate
    assert suggest_routine_name(detected) == "Routine Kalender Wetter"


def test_suggest_routine_name_calendar_routing_combo():
    steps = [
        RoutineStep(order=1, skill_id="calendar.list_events", args={"start_date": "2026-07-09"}),
        RoutineStep(order=2, skill_id="system.routing", args={"origin": "Berlin", "destination": "Hamburg"}),
    ]
    detected = DetectedWorkflow(
        steps=steps,
        fingerprint=build_step_fingerprint(steps),
        skill_count=2,
        is_offer_candidate=True,
        reject_reason=None,
        is_learning_candidate=True,
    )
    assert suggest_routine_name(detected) == "Routine Kalender Routing"
