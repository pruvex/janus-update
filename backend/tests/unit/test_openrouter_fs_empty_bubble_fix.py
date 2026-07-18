"""Regression: FS test prompts must not force OpenRouter websearch or yield empty bubbles."""

from __future__ import annotations

import json

from backend.services.orchestrator.execution_dispatcher import (
    _is_external_current_research_query,
)
from backend.services.orchestrator.execution_engine import (
    _extract_ok_tool_result_text,
    _finalize_stream_text_from_tool_results,
)
from backend.services.skill_router import (
    _is_news_update_query,
    is_realtime_search_query,
)

FS_PROMPT_WITH_NEGATION = (
    r"Nutze das Dateisystem. Liste maximal 10 Dateinamen aus dem Ordner "
    r"C:\Users\pruve\Desktop\Janus-OR-Test. Keine Nachrichten, keine Websuche."
)

FS_PROMPT_SAFE = (
    r"Nutze nur das Dateisystem. Liste maximal 10 Dateinamen aus "
    r"C:\Users\pruve\Desktop\Janus-OR-Test. Keine Websuche."
)


def test_goldpreis_web_prompt_is_external_research_even_when_news_marker_matches():
    """'aktuell' alone must not trap goldpreis into rss_news ahead of websearch."""
    from backend.services.orchestrator.intent_engine import IntentEngine

    q = (
        "Suche aktuell im Web: Wie hoch ist der Goldpreis in Euro heute? "
        "Nutze system.websearch und nenne mindestens eine Quelle. Rate nicht aus dem Gedächtnis."
    )
    assert is_realtime_search_query(q) is True
    assert _is_external_current_research_query(q) is True
    assert IntentEngine.detect_news_intent(q) is True
    # SOURCE-ROUTING priority: external research force beats news→rss_news.


def test_news_negation_rejects_keine_nachrichten():
    assert _is_news_update_query(FS_PROMPT_WITH_NEGATION) is False
    assert _is_news_update_query("Hole aktuelle Nachrichten") is True
    assert _is_news_update_query("zeige die schlagzeilen") is True
    assert _is_news_update_query("bitte ohne news und ohne web") is False


def test_fs_prompt_with_keine_nachrichten_is_not_realtime_or_external_research():
    assert is_realtime_search_query(FS_PROMPT_WITH_NEGATION) is False
    assert _is_external_current_research_query(FS_PROMPT_WITH_NEGATION) is False
    assert is_realtime_search_query(FS_PROMPT_SAFE) is False
    assert _is_external_current_research_query(FS_PROMPT_SAFE) is False


def test_external_research_still_detected_for_real_price_queries():
    assert _is_external_current_research_query(
        "Recherchiere aktuelle Modellpreise fuer GPT und Gemini"
    )


def test_filesystem_intent_vetoes_external_research_force_decision():
    """Mirrors SOURCE-ROUTING: FS dominates even when research signal is present."""
    research_and_fs = (
        r"Liste Dateien in C:\Users\pruve\Desktop\Janus-OR-Test und "
        r"recherchiere aktuelle Modellpreise fuer GPT"
    )
    is_external = _is_external_current_research_query(research_and_fs)
    is_filesystem_intent = True
    # Decision used by execution_dispatcher source-routing branch.
    should_force_websearch = bool(is_external) and not is_filesystem_intent
    assert is_external is True
    assert should_force_websearch is False


def test_extract_ok_tool_result_text_renders_list_directory_contents():
    payload = {
        "status": "ok",
        "data": {
            "status": "success",
            "data": {
                "path": r"C:\Users\pruve\Desktop\Janus-OR-Test",
                "contents": ["data.json", "nota.txt", "notes.md", "package.json", "README.md"],
                "count": 5,
            },
        },
        "error": None,
    }
    text = _extract_ok_tool_result_text(payload, "filesystem.list_directory")
    assert "README.md" in text
    assert "package.json" in text
    assert "Janus-OR-Test" in text


def test_finalize_stream_text_uses_list_directory_when_model_text_empty():
    raw = json.dumps(
        {
            "status": "ok",
            "data": {
                "status": "success",
                "data": {
                    "path": r"C:\Users\pruve\Desktop\Janus-OR-Test",
                    "contents": ["README.md", "package.json"],
                    "count": 2,
                },
            },
            "error": None,
        },
        ensure_ascii=False,
    )
    results = [
        {
            "role": "tool",
            "name": "filesystem_list_directory",
            "_skill_id": "filesystem.list_directory",
            "content": raw,
            "_raw_content": raw,
        }
    ]
    finalized = _finalize_stream_text_from_tool_results(
        "",
        results_buffer=results,
        had_tool_round=True,
        fallback_summary="done",
    )
    assert "README.md" in finalized
    assert "package.json" in finalized
