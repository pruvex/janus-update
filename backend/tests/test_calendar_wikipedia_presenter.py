from backend.services.workflow.calendar_wikipedia_presenter import (
    enrich_steps_with_wikipedia_snapshot,
    resolve_calendar_wikipedia_final_text,
    resolve_routine_wikipedia_display_message,
    should_preserve_llm_calendar_wikipedia_answer,
    wikipedia_queries_match,
)
from backend.services.workflow.routine_schema import RoutineStep


def _tool_results(calendar_message: str, wiki_summary: str, *, query: str = "Berlin", title: str = "Berlin"):
    return [
        {
            "skill_id": "calendar.list_events",
            "result": {
                "status": "ok",
                "data": {"events": [], "event_count": 0},
                "message": calendar_message,
            },
        },
        {
            "skill_id": "system.wikipedia_summary",
            "args": {"query": query},
            "result": {
                "status": "ok",
                "data": {"title": title, "summary": wiki_summary, "url": "https://de.wikipedia.org/wiki/Berlin"},
            },
        },
    ]


def _combo_builder(tool_results):
    calendar = ""
    wiki = ""
    for item in tool_results:
        if item["skill_id"] == "calendar.list_events":
            calendar = item["result"]["message"]
        if item["skill_id"] == "system.wikipedia_summary":
            wiki = item["result"]["data"]["summary"]
    return f"{calendar}\n\n{wiki}"


def test_should_preserve_llm_answer_when_it_differs_from_combo():
    tool_results = _tool_results(
        "Keine Termine im angegebenen Zeitraum gefunden.",
        "Berlin ist die Hauptstadt Deutschlands.",
    )
    llm_text = (
        "Heute hast du keine Termine.\n\n"
        "Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum."
    )
    assert should_preserve_llm_calendar_wikipedia_answer(
        llm_text,
        tool_results,
        build_combo_response=_combo_builder,
    )


def test_should_not_preserve_identical_combo_text():
    tool_results = _tool_results(
        "Keine Termine im angegebenen Zeitraum gefunden.",
        "Berlin ist die Hauptstadt Deutschlands.",
    )
    combo = _combo_builder(tool_results)
    assert not should_preserve_llm_calendar_wikipedia_answer(
        combo,
        tool_results,
        build_combo_response=_combo_builder,
    )


def test_resolve_final_text_prefers_llm_synthesis():
    tool_results = _tool_results(
        "Keine Termine im angegebenen Zeitraum gefunden.",
        "Berlin ist die Hauptstadt Deutschlands.",
    )
    llm_text = (
        "Heute hast du keine Termine.\n\n"
        "Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum."
    )
    resolved = resolve_calendar_wikipedia_final_text(
        llm_text,
        tool_results,
        build_combo_response=_combo_builder,
    )
    assert resolved == llm_text


def test_enrich_steps_stores_wikipedia_snapshot_from_llm_text():
    steps = [
        RoutineStep(order=1, skill_id="calendar.list_events", args={"range": "today"}),
        RoutineStep(order=2, skill_id="system.wikipedia_summary", args={"query": "Berlin"}),
    ]
    tool_results = _tool_results(
        "Keine Termine im angegebenen Zeitraum gefunden.",
        "Berlin ist die Hauptstadt Deutschlands.",
    )
    final_text = (
        "Keine Termine im angegebenen Zeitraum gefunden.\n\n"
        "Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum."
    )
    enriched = enrich_steps_with_wikipedia_snapshot(
        steps,
        final_text=final_text,
        tool_results=tool_results,
        build_combo_response=_combo_builder,
    )
    wiki_step = enriched[1]
    assert wiki_step.output_snapshot is not None
    assert "wichtiges europaeisches Zentrum" in wiki_step.output_snapshot
    assert wikipedia_queries_match(wiki_step.snapshot_query, "Berlin")


def test_routine_reuse_uses_snapshot_for_same_query():
    wiki_step = RoutineStep(
        order=2,
        skill_id="system.wikipedia_summary",
        args={"query": "Berlin"},
        output_snapshot="Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum.",
        snapshot_query="Berlin",
    )
    message = resolve_routine_wikipedia_display_message(
        wiki_step=wiki_step,
        requested_query="Berlin",
        tool_result={
            "status": "ok",
            "data": {"summary": "Berlin ist die Hauptstadt Deutschlands."},
        },
    )
    assert "wichtiges europaeisches Zentrum" in message


def test_routine_rebind_uses_fresh_tool_summary_for_different_query():
    wiki_step = RoutineStep(
        order=2,
        skill_id="system.wikipedia_summary",
        args={"query": "Berlin"},
        output_snapshot="Berlin ist die Hauptstadt Deutschlands und ein wichtiges europaeisches Zentrum.",
        snapshot_query="Berlin",
    )
    message = resolve_routine_wikipedia_display_message(
        wiki_step=wiki_step,
        requested_query="Muenchen",
        tool_result={
            "status": "ok",
            "data": {"summary": "Muenchen ist die Landeshauptstadt Bayerns."},
        },
    )
    assert message == "Muenchen ist die Landeshauptstadt Bayerns."
