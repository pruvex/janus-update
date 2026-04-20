"""Tests for proactive suggestion directive builder."""

from __future__ import annotations

import pytest

from backend.services.orchestrator.prompt_registry import prompt_registry
from backend.services.orchestrator.suggestion_engine import SuggestionEngine


def test_prompt_registry_has_suggestion_keys() -> None:
    for key in (
        "suggestion_mode_0",
        "suggestion_mode_1",
        "suggestion_mode_1_tagged",
        "suggestion_mode_2",
        "suggestion_mode_2_tagged",
    ):
        assert len(prompt_registry.get_directive(key)) > 10


def test_mode_off_returns_registry_directive_no_suggestions() -> None:
    d = SuggestionEngine.build_suggestion_directive(
        0,
        [],
        "",
        "Erkläre mir bitte Quantencomputing in zwei Sätzen.",
    )
    assert d == prompt_registry.get_directive("suggestion_mode_0")


def test_mode_smart_default_without_tags() -> None:
    d = SuggestionEngine.build_suggestion_directive(
        1,
        [],
        "",
        "Was sind die Öffnungszeiten vom Museum?",
    )
    assert d == prompt_registry.get_directive("suggestion_mode_1")


def test_mode_smart_with_relevance_tags_uses_tagged_directive() -> None:
    tool_payload = {
        "status": "ok",
        "data": {},
        "metadata": {
            "suggestion": {
                "relevance_tags": ["local_business", "poi"],
            }
        },
    }
    d = SuggestionEngine.build_suggestion_directive(
        1,
        [tool_payload],
        "",
        "Zeig mir Restaurants in München.",
    )
    expected = prompt_registry.get_directive("suggestion_mode_1_tagged").format(
        tags_line="local_business, poi",
    )
    assert d == expected


def test_mode_proactive_with_memory_facts() -> None:
    mem = "KONTEXT-WISSEN: Der Nutzer mag italienisches Essen. GESPEICHERT AM 2026-01-01."
    d = SuggestionEngine.build_suggestion_directive(
        2,
        [],
        mem,
        "Ich fahre nach Berlin, was soll ich unternehmen?",
    )
    assert d == prompt_registry.get_directive("suggestion_mode_2")


def test_mode_proactive_sparse_memory_still_uses_mode_2_format() -> None:
    d = SuggestionEngine.build_suggestion_directive(
        2,
        [],
        "",
        "Kurze Frage: wie spät ist es?",
    )
    assert d == prompt_registry.get_directive("suggestion_mode_2")


def test_mode_proactive_with_tags_uses_mode_2_tagged() -> None:
    tool_payload = {
        "status": "ok",
        "data": {},
        "metadata": {
            "suggestion": {
                "relevance_tags": ["weather", "time"],
            }
        },
    }
    d = SuggestionEngine.build_suggestion_directive(
        2,
        [tool_payload],
        "",
        "Wird es morgen regnen?",
    )
    expected = prompt_registry.get_directive("suggestion_mode_2_tagged").format(
        tags_line="weather, time",
    )
    assert d == expected


def test_anti_spam_short_message_returns_none() -> None:
    assert SuggestionEngine.build_suggestion_directive(1, [], "", "ok") is None
    assert SuggestionEngine.build_suggestion_directive(0, [], "", "danke") is None


def test_greeting_returns_none() -> None:
    assert SuggestionEngine.build_suggestion_directive(2, [], "", "Hallo!") is None
