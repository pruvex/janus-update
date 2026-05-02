"""Unit tests for TASK-065 Contextual Entity Resolver (calendar snapshot → event_id)."""

from datetime import date

import pytest

from backend.services.orchestrator.entity_resolver import (
    ContextualEntityResolver,
    _resolver_tokenize,
)
from backend.services.orchestrator.intent_engine import _normalize_text


class TestResolverTokenizer:
    def test_keeps_two_char_brand_tokens(self):
        n = _normalize_text("O2 Shop")
        assert _resolver_tokenize(n) == ["o2", "shop"]

    def test_drops_numeric_only(self):
        n = _normalize_text("test 123 foo")
        assert _resolver_tokenize(n) == ["test", "foo"]


@pytest.fixture
def resolver():
    return ContextualEntityResolver()


class TestEntityResolverMutation:
    def test_short_query_blocked(self, resolver):
        # Single char → no tokens ≥2 and len(normalized) < 3
        r = resolver.resolve("a", {"events": []}, "MUTATION")
        assert r.status == "NOT_FOUND"
        assert r.reason == "query_too_short"
        assert r.dispatcher_hint == "CLARIFY_USER"

    def test_empty_snapshot_fallback_list(self, resolver):
        r = resolver.resolve(
            "fitnessstudio",
            {"events": []},
            "MUTATION",
        )
        assert r.status == "NOT_FOUND"
        assert r.reason == "empty_snapshot"
        assert r.dispatcher_hint == "FALLBACK_TO_LIST"

    def test_resolved_fuzzy_fragment(self, resolver):
        snap = {
            "events": [
                {
                    "id": "ev_gym",
                    "title": "Sport im Fitnessstudio",
                    "location": "Fitness X Berlin",
                    "start": "2026-05-03T18:00:00+02:00",
                    "end": "2026-05-03T19:00:00+02:00",
                },
                {
                    "id": "ev_other",
                    "title": "Arzt termin",
                    "location": "",
                    "start": "2026-05-04T10:00:00+02:00",
                    "end": "2026-05-04T11:00:00+02:00",
                },
            ]
        }
        # Query as strong substring of title (PR + TSR both high vs. single distractor)
        r = resolver.resolve("fitnessstudio", snap, "MUTATION")
        assert r.status == "RESOLVED"
        assert r.dispatcher_hint == "PROCEED"
        assert r.resolved_event is not None
        assert r.resolved_event.event_id == "ev_gym"

    def test_identical_titles_ambiguous_without_temporal(self, resolver):
        snap = {
            "events": [
                {
                    "id": "e1",
                    "title": "Yoga",
                    "location": "",
                    "start": "2026-05-03T09:00:00+02:00",
                    "end": "2026-05-03T10:00:00+02:00",
                },
                {
                    "id": "e2",
                    "title": "Yoga",
                    "location": "",
                    "start": "2026-05-04T09:00:00+02:00",
                    "end": "2026-05-04T10:00:00+02:00",
                },
            ]
        }
        fixed = date(2026, 5, 1)
        r = resolver.resolve("Yoga", snap, "MUTATION", today=fixed)
        assert r.status == "AMBIGUOUS"
        assert r.dispatcher_hint == "FALLBACK_TO_LIST"

    def test_identical_titles_resolved_via_morgen(self, resolver):
        snap = {
            "events": [
                {
                    "id": "e_today",
                    "title": "Yoga",
                    "location": "",
                    "start": "2026-05-01T09:00:00+02:00",
                    "end": "2026-05-01T10:00:00+02:00",
                },
                {
                    "id": "e_morgen",
                    "title": "Yoga",
                    "location": "",
                    "start": "2026-05-02T09:00:00+02:00",
                    "end": "2026-05-02T10:00:00+02:00",
                },
            ]
        }
        fixed = date(2026, 5, 1)
        r = resolver.resolve(
            "Yoga morgen absagen",
            snap,
            "MUTATION",
            today=fixed,
        )
        assert r.status == "RESOLVED"
        assert r.dispatcher_hint == "PROCEED"
        assert r.reason == "identical_titles_resolved_by_temporal_anchor"
        assert r.resolved_event is not None
        assert r.resolved_event.event_id == "e_morgen"


class TestDeicticContextFallback:
    """Context fallback fires when: deictic/implicit ref + single event in history."""

    _GYM_SNAP = {
        "events": [
            {
                "id": "ev_gym",
                "title": "Sport im Fitnessstudio",
                "location": "Fitness X Berlin",
                "start": "2026-05-03T18:00:00+02:00",
                "end": "2026-05-03T19:00:00+02:00",
            }
        ]
    }

    _HISTORY_WITH_GYM = [
        {
            "role": "assistant",
            "content": (
                "Dein nächster Termin ist 'Sport im Fitnessstudio' am Sonntag um 18 Uhr."
            ),
        },
        {
            "role": "user",
            "content": "Handtuch nicht vergessen",
        },
    ]

    def test_deictic_word_triggers_context_fallback(self, resolver):
        """'ihn verschieben' → deictic 'ihn' → resolver falls back to context event."""
        history = [
            {
                "role": "assistant",
                "content": "Ich habe den Termin 'Sport im Fitnessstudio' gefunden.",
            },
            {"role": "user", "content": "ihn auf 20 Uhr verschieben"},
        ]
        r = resolver.resolve(
            "ihn",
            self._GYM_SNAP,
            "MUTATION",
            recent_messages=history,
            is_calendar_mutation=True,
        )
        assert r.status == "RESOLVED"
        assert r.reason == "deictic_context_fallback"
        assert r.dispatcher_hint == "PROCEED"
        assert r.resolved_event is not None
        assert r.resolved_event.event_id == "ev_gym"

    def test_implicit_short_query_triggers_context_fallback(self, resolver):
        """Short query 'Handtuch' (1 token) + assistant mentioned event → context fallback."""
        r = resolver.resolve(
            "Handtuch",
            self._GYM_SNAP,
            "MUTATION",
            recent_messages=self._HISTORY_WITH_GYM,
            is_calendar_mutation=True,
        )
        assert r.status == "RESOLVED"
        assert r.reason == "deictic_context_fallback"
        assert r.resolved_event is not None
        assert r.resolved_event.event_id == "ev_gym"

    def test_no_context_fallback_without_deictic_or_short_query(self, resolver):
        """Multi-token query with no deictic → context fallback must NOT fire."""
        history = [
            {
                "role": "assistant",
                "content": "Dein nächster Termin ist 'Sport im Fitnessstudio'.",
            },
        ]
        r = resolver.resolve(
            "Einkaufen Liste fertig machen",  # 4 tokens, no deictic
            self._GYM_SNAP,
            "MUTATION",
            recent_messages=history,
            is_calendar_mutation=True,
        )
        # Should NOT resolve to gym via context — NOT_FOUND or WEAK
        assert r.status in ("NOT_FOUND", "WEAK_MATCH")

    def test_no_context_fallback_without_mutation_flag(self, resolver):
        """Context fallback requires is_calendar_mutation=True."""
        history = [
            {
                "role": "assistant",
                "content": "Dein nächster Termin ist 'Sport im Fitnessstudio'.",
            },
        ]
        r = resolver.resolve(
            "ihn",
            self._GYM_SNAP,
            "MUTATION",
            recent_messages=history,
            is_calendar_mutation=False,  # flag off
        )
        assert r.status != "RESOLVED" or r.reason != "deictic_context_fallback"

    def test_no_context_fallback_with_multiple_context_events(self, resolver):
        """If 2 events mentioned in history → context is ambiguous → no fallback."""
        snap = {
            "events": [
                {
                    "id": "ev_gym",
                    "title": "Sport im Fitnessstudio",
                    "location": "",
                    "start": "2026-05-03T18:00:00+02:00",
                    "end": "2026-05-03T19:00:00+02:00",
                },
                {
                    "id": "ev_yoga",
                    "title": "Yoga",
                    "location": "",
                    "start": "2026-05-04T09:00:00+02:00",
                    "end": "2026-05-04T10:00:00+02:00",
                },
            ]
        }
        history = [
            {
                "role": "assistant",
                "content": (
                    "Du hast heute 'Sport im Fitnessstudio' und morgen 'Yoga'."
                ),
            },
            {"role": "user", "content": "den absagen"},
        ]
        r = resolver.resolve(
            "den",
            snap,
            "MUTATION",
            recent_messages=history,
            is_calendar_mutation=True,
        )
        # Two events in context → ambiguous → must NOT resolve via deictic fallback
        assert r.reason != "deictic_context_fallback"


class TestEntityResolverRead:
    def test_ambiguous_read_proceed_with_low_confidence(self, resolver):
        """Two similar titles close in score → READ may still PROCEED but low_confidence."""
        snap = {
            "events": [
                {
                    "id": "a",
                    "title": "Buy milk at Aldi",
                    "location": "Aldi Süd",
                    "start": "2026-05-03T12:00:00+02:00",
                    "end": "2026-05-03T13:00:00+02:00",
                },
                {
                    "id": "b",
                    "title": "Shopping at Aldi",
                    "location": "Aldi Süd",
                    "start": "2026-05-04T12:00:00+02:00",
                    "end": "2026-05-04T13:00:00+02:00",
                },
            ]
        }
        r = resolver.resolve("Aldi", snap, "READ")
        assert r.status == "AMBIGUOUS"
        assert r.dispatcher_hint == "PROCEED"
        assert r.low_confidence is True
