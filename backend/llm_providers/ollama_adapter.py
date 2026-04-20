"""Legacy import path for the Ollama capability layer.

Implementation: :mod:`backend.llm_providers.ollama.adapter`.
"""

from backend.llm_providers.ollama.adapter import (
    OllamaCapabilities,
    OllamaOutcome,
    SkillAffinity,
    ToolCallFailure,
    apply_synthesis_call_contract,
    build_compact_synthesis_messages,
    build_default_capabilities,
    build_text_outcome,
    build_tool_outcome,
    classify_tool_call_failure,
    clear_cached_capabilities,
    get_cached_capabilities,
    get_or_create_capabilities,
    get_skill_affinity,
    get_skill_affinity_registry,
    has_deterministic_fallback,
    is_tool_blind_model,
    match_intent_to_skills,
    set_cached_native_tool_support,
)

__all__ = [
    "OllamaCapabilities",
    "OllamaOutcome",
    "SkillAffinity",
    "ToolCallFailure",
    "apply_synthesis_call_contract",
    "build_compact_synthesis_messages",
    "build_default_capabilities",
    "build_text_outcome",
    "build_tool_outcome",
    "classify_tool_call_failure",
    "clear_cached_capabilities",
    "get_cached_capabilities",
    "get_or_create_capabilities",
    "get_skill_affinity",
    "get_skill_affinity_registry",
    "has_deterministic_fallback",
    "is_tool_blind_model",
    "match_intent_to_skills",
    "set_cached_native_tool_support",
]
