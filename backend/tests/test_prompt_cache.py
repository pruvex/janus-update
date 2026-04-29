from backend.services.prompt_cache import (
    decide_prompt_cache,
    merge_decision_into_usage,
    reset_prompt_cache_store,
)


def setup_function():
    reset_prompt_cache_store()


def test_prompt_cache_marks_clock_and_user_input_as_bypassed(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")

    decision = decide_prompt_cache(
        provider="openai",
        model="gpt-5",
        raw_segments={
            "clock_line": "AKTUELLES DATUM/UHRZEIT: Mittwoch, 29.04.2026, 15:30 Uhr",
            "base_prompt": "Du bist Janus und hilfst präzise.",
            "user_input": "Hallo",
        },
    )

    assert decision.enabled is True
    assert decision.cache_misses == 1
    assert decision.cache_bypassed == 2
    assert decision.native_cache_supported is True
    assert [segment.segment_type for segment in decision.segments] == [
        "clock_line",
        "base_prompt",
        "user_input",
    ]


def test_prompt_cache_reuses_stable_segments_but_not_dynamic_segments(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")
    raw_segments = {
        "base_prompt": "Stabiler Systemprompt mit ausreichend Worten für eine Schätzung.",
        "identity_directive": "Der Nutzer heißt Test.",
        "suggestion_suffix": "Dynamisch abhängig von User Text.",
    }

    first = decide_prompt_cache(
        provider="openai",
        model="gpt-5",
        raw_segments=raw_segments,
        user_scope="Test",
    )
    second = decide_prompt_cache(
        provider="openai",
        model="gpt-5",
        raw_segments=raw_segments,
        user_scope="Test",
    )

    assert first.cache_hits == 0
    assert first.cache_misses == 2
    assert first.cache_bypassed == 1
    assert second.cache_hits == 2
    assert second.cache_misses == 0
    assert second.cache_bypassed == 1
    assert second.estimated_tokens_saved > 0


def test_prompt_cache_user_scope_prevents_identity_cross_user_reuse(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")
    raw_segments = {"identity_directive": "Der Nutzer heißt Test."}

    first = decide_prompt_cache(
        provider="openai",
        model="gpt-5",
        raw_segments=raw_segments,
        user_scope="UserA",
    )
    second = decide_prompt_cache(
        provider="openai",
        model="gpt-5",
        raw_segments=raw_segments,
        user_scope="UserB",
    )

    assert first.cache_misses == 1
    assert second.cache_misses == 1
    assert second.cache_hits == 0


def test_prompt_cache_disabled_still_reports_bypassed(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "false")

    decision = decide_prompt_cache(
        provider="ollama",
        model="local",
        raw_segments={"base_prompt": "Stabil", "user_input": "Dynamisch"},
    )

    assert decision.enabled is False
    assert decision.cache_hits == 0
    assert decision.cache_misses == 0
    assert decision.cache_bypassed == 2
    assert decision.reason == "PROMPT_CACHE_ENABLED=false"
    assert decision.native_cache_supported is False


def test_prompt_cache_usage_merge_is_additive(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")
    decision = decide_prompt_cache(
        provider="openai",
        model="gpt-5",
        raw_segments={"base_prompt": "Stabiler Systemprompt"},
    )

    usage = merge_decision_into_usage({"prompt_tokens": 100}, decision)

    assert usage["prompt_tokens"] == 100
    assert usage["cache_misses"] == 1
    assert usage["prompt_cache"]["provider"] == "openai"
    assert "segments" in usage["prompt_cache"]
    assert usage["prompt_cache"]["segments"][0]["content"] == ""
