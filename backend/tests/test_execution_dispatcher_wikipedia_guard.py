from types import SimpleNamespace

from backend.services.orchestrator.execution_dispatcher import (
    _build_calendar_wikipedia_forced_tool_plan,
    _build_wikipedia_turn_skill_ids,
    _is_calendar_wikipedia_combo,
)
from backend.services.orchestrator.execution_engine import (
    _partition_duplicate_tool_calls,
    _resolve_combo_forced_tool_for_iteration,
)


def test_partition_duplicate_skips_calendar_retry_while_wikipedia_combo_pending():
    seen: set[str] = {"calendar.list_events:today"}
    executed: set[str] = {"calendar.list_events"}
    combo = frozenset({"calendar.list_events", "system.wikipedia_summary"})

    def track(tool_name, arguments):
        key = f"{tool_name}:{arguments.get('range', '')}"
        if key in seen:
            return True
        seen.add(key)
        return False

    tool_calls = [
        {
            "function": {
                "name": "calendar.list_events",
                "arguments": '{"range": "today"}',
            }
        }
    ]
    filtered, blocked, blocked_name = _partition_duplicate_tool_calls(
        tool_calls,
        {
            "_track_tool_call_fn": track,
            "_multi_skill_combo_ids": combo,
            "_kpi_skills_executed": executed,
        },
    )

    assert blocked is False
    assert blocked_name == ""
    assert filtered == []


def test_build_wikipedia_turn_skill_ids_keeps_calendar_skills_for_mixed_turn():
    result = _build_wikipedia_turn_skill_ids(
        [
            "calendar.list_events",
            "calendar.find_and_update_event",
            "system.wikipedia_summary",
            "knowledge.query",
        ],
        calendar_intent=True,
    )

    assert result == [
        "calendar.list_events",
        "calendar.find_and_update_event",
        "system.wikipedia_summary",
    ]


def test_build_wikipedia_turn_skill_ids_clamps_to_wikipedia_for_pure_wikipedia():
    assert _build_wikipedia_turn_skill_ids(
        ["calendar.list_events", "system.wikipedia_summary"],
        calendar_intent=False,
    ) == ["system.wikipedia_summary"]


def test_is_calendar_wikipedia_combo_true_only_for_calendar_read_and_wikipedia():
    query = (
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin."
    )
    assert _is_calendar_wikipedia_combo(
        SimpleNamespace(
            is_calendar_intent=True,
            is_wikipedia_intent=True,
            is_calendar_mutation=False,
            is_calendar_creation=False,
        )
    ) is True
    assert _is_calendar_wikipedia_combo(
        SimpleNamespace(
            is_calendar_intent=True,
            is_wikipedia_intent=False,
            is_calendar_mutation=False,
            is_calendar_creation=False,
        ),
        query,
    ) is True
    assert _is_calendar_wikipedia_combo(
        SimpleNamespace(
            is_calendar_intent=True,
            is_wikipedia_intent=True,
            is_calendar_mutation=True,
            is_calendar_creation=False,
        )
    ) is False
    assert _is_calendar_wikipedia_combo(None) is False


def test_build_calendar_wikipedia_forced_tool_plan_extracts_berlin_query():
    query = (
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin."
    )
    calendar_args, wiki_args = _build_calendar_wikipedia_forced_tool_plan(query)
    assert calendar_args.get("range") == "today"
    assert wiki_args == {"query": "Berlin"}


def test_resolve_combo_forced_tool_for_iteration_round_two_wikipedia():
    query = (
        "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin."
    )
    calendar_args, wiki_args = _build_calendar_wikipedia_forced_tool_plan(query)
    round_one_gateway = {
        "_multi_skill_combo_ids": frozenset({"calendar.list_events", "system.wikipedia_summary"}),
        "_kpi_skills_executed": set(),
        "forced_tool_args": calendar_args,
        "force_tool_name": "calendar.list_events",
        "_combo_wikipedia_forced_args": wiki_args,
        "user_prompt": query,
    }

    round_one_name, round_one_args = _resolve_combo_forced_tool_for_iteration(round_one_gateway, 0)
    assert round_one_name == "calendar.list_events"
    assert round_one_args == calendar_args

    round_two_gateway = {
        "_multi_skill_combo_ids": frozenset({"calendar.list_events", "system.wikipedia_summary"}),
        "_kpi_skills_executed": {"calendar.list_events"},
        "_combo_wikipedia_forced_args": wiki_args,
        "user_prompt": query,
    }
    round_two_name, round_two_args = _resolve_combo_forced_tool_for_iteration(round_two_gateway, 1)
    assert round_two_name == "system.wikipedia_summary"
    assert round_two_args == {"query": "Berlin"}

    completed_gateway = {
        **round_two_gateway,
        "_kpi_skills_executed": {"calendar.list_events", "system.wikipedia_summary"},
    }
    assert _resolve_combo_forced_tool_for_iteration(completed_gateway, 2) == (None, None)
