from types import SimpleNamespace

from backend.services.orchestrator.execution_dispatcher import (
    _build_weather_turn_skill_ids,
    _is_calendar_weather_combo,
)


def test_build_weather_turn_skill_ids_keeps_calendar_skills_for_mixed_turn():
    result = _build_weather_turn_skill_ids(
        [
            "calendar.list_events",
            "calendar.find_and_update_event",
            "calendar.create_event",
            "system.weather",
            "knowledge.query",
        ],
        calendar_intent=True,
    )

    assert result == [
        "calendar.list_events",
        "calendar.find_and_update_event",
        "calendar.create_event",
        "system.weather",
    ]


def test_build_weather_turn_skill_ids_clamps_to_weather_for_pure_weather():
    assert _build_weather_turn_skill_ids(
        ["calendar.list_events", "system.weather"],
        calendar_intent=False,
    ) == ["system.weather"]


def test_is_calendar_weather_combo_true_only_for_calendar_read_turn():
    assert _is_calendar_weather_combo(
        SimpleNamespace(
            is_calendar_intent=True,
            is_calendar_mutation=False,
            is_calendar_creation=False,
        )
    ) is True
    assert _is_calendar_weather_combo(
        SimpleNamespace(
            is_calendar_intent=True,
            is_calendar_mutation=True,
            is_calendar_creation=False,
        )
    ) is False
    assert _is_calendar_weather_combo(None) is False
