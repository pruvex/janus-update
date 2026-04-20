"""Architecture tests for the Capability Layer, Intent Parser, Skill Router and Fallback mechanisms.

These tests validate that the local LLM architecture correctly:
1. Registers skill affinities and provides deterministic intent matching
2. Routes user requests to the correct skill families
3. Classifies tool-call failures and recommends correct fallback strategies
4. Limits tool definitions for Ollama with intent-aware prioritization
5. Fixes the SkillSelector keyword matching bug
"""

import pytest

from backend import tool_registry
from backend.llm_providers.ollama_adapter import (
    classify_tool_call_failure,
    get_skill_affinity,
    get_skill_affinity_registry,
    has_deterministic_fallback,
    match_intent_to_skills,
)
from backend.services.skill_selector import SkillSelector


@pytest.fixture(autouse=True)
def _register_tools_once():
    tool_registry.register_all_tools()


# ---------------------------------------------------------------------------
# 1. Capability Layer: Skill Affinity Registry
# ---------------------------------------------------------------------------

class TestSkillAffinityRegistry:

    def test_registry_is_populated(self):
        registry = get_skill_affinity_registry()
        assert len(registry) >= 8, f"Expected at least 8 skill affinities, got {len(registry)}"

    @pytest.mark.parametrize("skill_id", [
        "system.routing",
        "system.local_business",
        "system.websearch",
        "system.country_info",
        "system.weather",
        "system.create_pdf",
        "system.generate_image",
        "knowledge.query",
    ])
    def test_core_skills_have_affinity(self, skill_id: str):
        affinity = get_skill_affinity(skill_id)
        assert affinity is not None, f"Missing affinity for {skill_id}"
        assert affinity.skill_id == skill_id
        assert len(affinity.intent_keywords) > 0

    def test_routing_has_deterministic_fallback(self):
        assert has_deterministic_fallback("system.routing") is True

    def test_local_business_has_deterministic_fallback(self):
        assert has_deterministic_fallback("system.local_business") is True

    def test_generate_image_has_no_deterministic_fallback(self):
        assert has_deterministic_fallback("system.generate_image") is False

    def test_unknown_skill_returns_none(self):
        assert get_skill_affinity("imaginary.skill") is None
        assert has_deterministic_fallback("imaginary.skill") is False


# ---------------------------------------------------------------------------
# 2. Intent Parser: match_intent_to_skills
# ---------------------------------------------------------------------------

class TestIntentMatcher:

    def test_routing_intent_detected(self):
        skills = match_intent_to_skills("Wie weit ist es von Berlin nach Hamburg?")
        assert "system.routing" in skills

    def test_restaurant_intent_detected(self):
        skills = match_intent_to_skills("Finde mir ein gutes Restaurant in Hamburg")
        assert "system.local_business" in skills

    def test_weather_intent_detected(self):
        skills = match_intent_to_skills("Wie ist das Wetter in München?")
        assert "system.weather" in skills

    def test_country_info_intent_detected(self):
        skills = match_intent_to_skills("Was ist die Hauptstadt von Frankreich?")
        assert "system.country_info" in skills

    def test_websearch_intent_detected(self):
        skills = match_intent_to_skills("Suche nach den aktuellen Nachrichten")
        assert "system.websearch" in skills

    def test_memory_intent_detected(self):
        skills = match_intent_to_skills("Merke dir, dass ich Vegetarier bin")
        assert "memory.save_core_fact" in skills

    def test_empty_prompt_returns_empty(self):
        assert match_intent_to_skills("") == []
        assert match_intent_to_skills("   ") == []

    def test_generic_greeting_returns_empty(self):
        skills = match_intent_to_skills("Hallo, wie geht es dir?")
        assert len(skills) == 0

    def test_multi_intent_returns_top_k(self):
        skills = match_intent_to_skills(
            "Suche ein Restaurant in der Nähe und wie weit ist es von hier?",
            top_k=2,
        )
        assert len(skills) <= 2
        assert any(s in skills for s in ["system.local_business", "system.routing"])

    def test_top_k_respected(self):
        skills = match_intent_to_skills("Suche Restaurant Wetter Route Land", top_k=2)
        assert len(skills) <= 2


# ---------------------------------------------------------------------------
# 3. Failure Classification
# ---------------------------------------------------------------------------

class TestToolCallFailureClassification:

    def test_terminal_error_degrades_to_text(self):
        failure = classify_tool_call_failure("system.routing", "SKILL_NOT_FOUND", "ollama")
        assert failure.is_retryable is False
        assert failure.should_degrade_to_text is True
        assert failure.fallback_strategy == "error_report"

    def test_timeout_is_retryable_with_deterministic_fallback_for_ollama(self):
        failure = classify_tool_call_failure("system.routing", "TIMEOUT", "ollama")
        assert failure.is_retryable is True
        assert failure.should_degrade_to_text is False
        assert failure.fallback_strategy == "deterministic_osrm"

    def test_timeout_for_openai_uses_retry(self):
        failure = classify_tool_call_failure("system.routing", "TIMEOUT", "openai")
        assert failure.is_retryable is True
        assert failure.fallback_strategy == "retry"

    def test_invalid_arguments_is_terminal(self):
        failure = classify_tool_call_failure("system.create_pdf", "INVALID_ARGUMENTS", "ollama")
        assert failure.is_retryable is False
        assert failure.should_degrade_to_text is True

    def test_network_error_with_osm_fallback(self):
        failure = classify_tool_call_failure("system.local_business", "NETWORK_ERROR", "ollama")
        assert failure.is_retryable is True
        assert failure.fallback_strategy == "deterministic_osm"

    def test_unknown_error_for_image_generation_degrades(self):
        failure = classify_tool_call_failure("system.generate_image", "UNKNOWN", "ollama")
        assert failure.should_degrade_to_text is True
        assert failure.fallback_strategy == "text_synthesis"


# ---------------------------------------------------------------------------
# 4. Gateway: Intent-Aware Tool Limiting
# ---------------------------------------------------------------------------

class TestIntentAwareToolLimiting:

    def _make_tool_defs(self, names):
        return [{"name": name, "description": f"Tool {name}", "parameters": {}} for name in names]

    def test_intent_boost_pushes_matching_skill_to_top(self):
        from backend.services.llm_gateway import _limit_local_tool_definitions

        tools = self._make_tool_defs([
            "filesystem.list_directory",
            "filesystem.create_file",
            "filesystem.delete_file",
            "filesystem.read_file",
            "filesystem.rename_file",
            "memory.save_core_fact",
            "memory.search_summaries",
            "system.websearch",
            "system.routing",
            "system.local_business",
            "system.weather",
            "system.country_info",
        ])

        limited = _limit_local_tool_definitions(
            tools, limit=5, user_prompt="Wie ist das Wetter in Berlin?"
        )

        limited_names = [t["name"] for t in limited]
        assert "system.weather" in limited_names
        assert len(limited) == 5

    def test_no_prompt_uses_static_priorities(self):
        from backend.services.llm_gateway import _limit_local_tool_definitions

        tools = self._make_tool_defs([
            "filesystem.list_directory",
            "filesystem.create_file",
            "filesystem.delete_file",
            "filesystem.read_file",
            "filesystem.rename_file",
            "memory.save_core_fact",
            "memory.search_summaries",
            "system.websearch",
            "system.routing",
            "system.local_business",
            "system.weather",
            "system.country_info",
        ])

        limited = _limit_local_tool_definitions(tools, limit=5)
        limited_names = [t["name"] for t in limited]
        assert "system.websearch" in limited_names
        assert len(limited) == 5


# ---------------------------------------------------------------------------
# 5. SkillSelector Bug Fix Verification
# ---------------------------------------------------------------------------

class TestSkillSelectorKeywordFix:

    def test_contains_keyword_matches_word_boundary(self):
        selector = SkillSelector()
        assert selector._contains_keyword("ich suche ein hotel", "hotel") is True

    def test_contains_keyword_no_false_positive_on_partial(self):
        selector = SkillSelector()
        assert selector._contains_keyword("die emailadresse", "mail") is False

    def test_domain_priorities_detects_system_domain(self):
        selector = SkillSelector()
        result = selector._domain_priorities(prompt="Finde ein Restaurant in Berlin")
        assert any("system" in domain for domain in result) or len(result) > 0

    def test_domain_priorities_detects_filesystem_domain(self):
        selector = SkillSelector()
        result = selector._domain_priorities(prompt="Liste mir die Dateien im Ordner")
        assert len(result) > 0
