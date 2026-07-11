import json

from backend.services.workflow.workflow_detector import detect_learning_candidate, detect_workflow_candidate


def test_detector_extracts_step_order_and_marks_offer_candidate():
    trace = [
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

    detected = detect_workflow_candidate(trace)

    assert detected.is_offer_candidate is True
    assert detected.reject_reason is None
    assert [step.skill_id for step in detected.steps] == ["calendar.list_events", "system.weather"]
    assert [step.order for step in detected.steps] == [1, 2]
    assert detected.skill_count == 2


def test_detector_ignores_failed_steps():
    trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
        {"skill_id": "communication.list_emails", "status": "error", "args": {"unread_only": True}, "risk_level": "high"},
        {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
    ]

    detected = detect_workflow_candidate(trace)

    assert [step.skill_id for step in detected.steps] == ["calendar.list_events", "system.weather"]
    assert detected.is_offer_candidate is True


def test_detector_rejects_single_skill_turns():
    trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
    ]

    detected = detect_workflow_candidate(trace)

    assert detected.is_offer_candidate is False
    assert detected.reject_reason == "insufficient_distinct_skills"


def test_detector_rejects_when_gate_flags_block_offer():
    trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
        {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
    ]

    detected = detect_workflow_candidate(trace, routines_offer_enabled=False)
    assert detected.reject_reason == "routines_offer_disabled"

    detected = detect_workflow_candidate(trace, is_medical_turn=True)
    assert detected.reject_reason == "medical_turn_excluded"

    detected = detect_workflow_candidate(trace, session_cooldown_active=True)
    assert detected.reject_reason == "session_cooldown_active"


def test_detector_rejects_similar_existing_routine():
    trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
        {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "medium"},
    ]

    detected = detect_workflow_candidate(
        trace,
        existing_routine_step_sets=[{"calendar.list_events", "system.weather"}],
    )

    assert detected.is_offer_candidate is False
    assert detected.reject_reason == "similar_routine_exists"


def test_detector_accepts_two_step_live_shape_without_risk_level():
    trace = [
        {"_skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}},
        {"_skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}},
    ]

    detected = detect_workflow_candidate(trace)

    assert detected.is_offer_candidate is True
    assert detected.reject_reason is None
    assert [step.skill_id for step in detected.steps] == ["calendar.list_events", "system.weather"]


def test_detector_accepts_openai_name_only_live_shape():
    trace = [
        {"name": "calendar_list_events", "status": "success", "args": {"days_in_future": 0}},
        {"name": "system_weather", "status": "success", "args": {"city": "Koeln", "date_str": "heute"}},
    ]

    detected = detect_workflow_candidate(trace)

    assert detected.is_offer_candidate is True
    assert detected.reject_reason is None
    assert [step.skill_id for step in detected.steps] == ["calendar.list_events", "system.weather"]


def test_detector_accepts_content_only_tool_result_shape():
    trace = [
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
    ]

    detected = detect_workflow_candidate(trace)

    assert detected.is_offer_candidate is True
    assert detected.reject_reason is None
    assert [step.skill_id for step in detected.steps] == ["calendar.list_events", "system.weather"]


def test_learning_detector_accepts_qualifying_calendar_weather_flow():
    trace = [
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

    detected = detect_learning_candidate(trace)

    assert detected.is_learning_candidate is True
    assert detected.learning_reject_reason is None


def test_learning_detector_rejects_high_risk_steps():
    trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
        {"skill_id": "communication.list_emails", "status": "ok", "args": {"unread_only": True}, "risk_level": "high"},
    ]

    detected = detect_learning_candidate(trace)

    assert detected.is_learning_candidate is False
    assert detected.learning_reject_reason == "high_risk_step"


def test_learning_detector_rejects_sensitive_skills_even_with_low_risk():
    trace = [
        {"skill_id": "calendar.list_events", "status": "ok", "args": {"range": "today"}, "risk_level": "low"},
        {"skill_id": "communication.list_emails", "status": "ok", "args": {"unread_only": True}, "risk_level": "low"},
    ]

    detected = detect_learning_candidate(trace)

    assert detected.is_learning_candidate is False
    assert detected.learning_reject_reason == "sensitive_skill_excluded"


def test_learning_detector_rejects_context_dependent_bindings():
    trace = [
        {
            "skill_id": "calendar.list_events",
            "status": "ok",
            "args": {"range": "today"},
            "arg_bindings": {"range": "{{user.range}}"},
            "risk_level": "low",
        },
        {"skill_id": "system.weather", "status": "ok", "args": {"city": "Koeln"}, "risk_level": "low"},
    ]

    detected = detect_learning_candidate(trace)

    assert detected.is_learning_candidate is False
    assert detected.learning_reject_reason == "context_dependent_step"
