import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("janus_backend")

_CAPABILITY_CACHE: Dict[str, "OllamaCapabilities"] = {}


@dataclass(frozen=True)
class OllamaCapabilities:
    model: str
    base_url: str
    supports_native_tools: bool = True
    supports_streaming: bool = True
    supports_json_mode: bool = True
    tool_blind: bool = False
    prefers_text_only_synthesis: bool = True

    @property
    def cache_key(self) -> str:
        return f"{str(self.base_url or '').strip().lower()}::{str(self.model or '').strip().lower()}"


def _capability_cache_key(model: str, base_url: str) -> str:
    return f"{str(base_url or '').strip().lower()}::{str(model or '').strip().lower()}"


def is_tool_blind_model(model: str) -> bool:
    normalized = str(model or "").strip().lower()
    if not normalized:
        return False
    return "gemma2" in normalized or "gemma-2" in normalized


def build_default_capabilities(model: str, base_url: str) -> OllamaCapabilities:
    tool_blind = is_tool_blind_model(model)
    return OllamaCapabilities(
        model=model,
        base_url=base_url,
        supports_native_tools=not tool_blind,
        supports_streaming=True,
        supports_json_mode=True,
        tool_blind=tool_blind,
        prefers_text_only_synthesis=True,
    )


def get_cached_capabilities(model: str, base_url: str) -> Optional[OllamaCapabilities]:
    return _CAPABILITY_CACHE.get(_capability_cache_key(model, base_url))


def clear_cached_capabilities() -> None:
    _CAPABILITY_CACHE.clear()


def get_or_create_capabilities(model: str, base_url: str) -> OllamaCapabilities:
    cached = get_cached_capabilities(model, base_url)
    if cached is not None:
        return cached
    created = build_default_capabilities(model, base_url)
    _CAPABILITY_CACHE[created.cache_key] = created
    return created


def set_cached_native_tool_support(model: str, base_url: str, supports_native_tools: bool) -> OllamaCapabilities:
    existing = get_or_create_capabilities(model, base_url)
    updated = OllamaCapabilities(
        model=existing.model,
        base_url=existing.base_url,
        supports_native_tools=bool(supports_native_tools),
        supports_streaming=existing.supports_streaming,
        supports_json_mode=existing.supports_json_mode,
        tool_blind=existing.tool_blind,
        prefers_text_only_synthesis=existing.prefers_text_only_synthesis,
    )
    _CAPABILITY_CACHE[updated.cache_key] = updated
    return updated


def build_compact_synthesis_messages(
    messages: List[Dict[str, Any]],
    *,
    system_prompt: str,
    keep_last: int = 3,
) -> List[Dict[str, Any]]:
    non_system_history = [msg for msg in (messages or []) if str(msg.get("role") or "") != "system"]
    capped_history = non_system_history[-keep_last:] if keep_last > 0 else non_system_history
    return [{"role": "system", "content": system_prompt}] + capped_history


def apply_synthesis_call_contract(api_call_params: Dict[str, Any], *, call_type: str = "synthesis") -> Dict[str, Any]:
    normalized = dict(api_call_params or {})
    normalized.pop("tools", None)
    normalized.pop("tool_choice", None)
    normalized.pop("force_tool_name", None)
    normalized.pop("strict_tool_calls", None)
    normalized["call_type"] = call_type
    return normalized


@dataclass
class OllamaOutcome:
    mode: str
    text: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_assistant_response: Optional[Dict[str, Any]] = None
    degraded: bool = False

    def to_response_payload(self) -> Dict[str, Any]:
        if self.mode == "tool_code":
            return {
                "type": "tool_code",
                "tool_calls": list(self.tool_calls),
                "usage": dict(self.usage),
                "cost": {"total_cost": 0.0},
                "raw_assistant_response": self.raw_assistant_response,
            }
        return {
            "type": "text",
            "text": self.text,
            "image_url": None,
            "usage": dict(self.usage),
            "cost": {"total_cost": 0.0},
            "finish_reason": self.finish_reason,
            "degraded": self.degraded,
        }


def build_text_outcome(
    *,
    text: Optional[str],
    usage: Optional[Dict[str, Any]] = None,
    finish_reason: Optional[str] = None,
    degraded: bool = False,
) -> Dict[str, Any]:
    return OllamaOutcome(
        mode="text",
        text=text,
        usage=dict(usage or {}),
        finish_reason=finish_reason,
        degraded=degraded,
    ).to_response_payload()


def build_tool_outcome(
    *,
    tool_calls: List[Dict[str, Any]],
    usage: Optional[Dict[str, Any]] = None,
    raw_assistant_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return OllamaOutcome(
        mode="tool_code",
        tool_calls=list(tool_calls or []),
        usage=dict(usage or {}),
        raw_assistant_response=raw_assistant_response,
    ).to_response_payload()


@dataclass(frozen=True)
class SkillAffinity:
    """Describes how a skill family behaves under local LLM constraints."""
    skill_id: str
    intent_keywords: Tuple[str, ...] = ()
    provider_agnostic_fallback: str = "text_synthesis"
    requires_external_api: bool = False
    max_context_tokens: int = 2500
    deterministic_fallback_available: bool = False


_SKILL_AFFINITY_REGISTRY: Dict[str, SkillAffinity] = {}


def _build_default_affinity_registry() -> Dict[str, SkillAffinity]:
    return {
        "system.routing": SkillAffinity(
            skill_id="system.routing",
            intent_keywords=("route", "entfernung", "distanz", "fahrt", "fahrzeit", "strecke", "kilometer", "km", "wie weit", "wie lange"),
            provider_agnostic_fallback="deterministic_osrm",
            requires_external_api=False,
            max_context_tokens=1500,
            deterministic_fallback_available=True,
        ),
        "system.local_business": SkillAffinity(
            skill_id="system.local_business",
            intent_keywords=("restaurant", "pizzeria", "café", "cafe", "bar", "hotel", "apotheke", "arzt", "supermarkt", "baumarkt", "kino", "museum", "geschäft", "laden"),
            provider_agnostic_fallback="deterministic_osm",
            requires_external_api=False,
            max_context_tokens=2500,
            deterministic_fallback_available=True,
        ),
        "system.websearch": SkillAffinity(
            skill_id="system.websearch",
            intent_keywords=("suche", "recherche", "google", "web", "aktuell", "nachrichten", "news"),
            provider_agnostic_fallback="duckduckgo_scrape",
            requires_external_api=False,
            max_context_tokens=2500,
            deterministic_fallback_available=True,
        ),
        "system.country_info": SkillAffinity(
            skill_id="system.country_info",
            intent_keywords=("hauptstadt", "einwohner", "bevölkerung", "währung", "land", "country", "capital"),
            provider_agnostic_fallback="restcountries_api",
            requires_external_api=False,
            max_context_tokens=1500,
            deterministic_fallback_available=True,
        ),
        "system.weather": SkillAffinity(
            skill_id="system.weather",
            intent_keywords=("wetter", "temperatur", "regen", "sonne", "prognose", "weather"),
            provider_agnostic_fallback="openmeteo_api",
            requires_external_api=False,
            max_context_tokens=1500,
            deterministic_fallback_available=True,
        ),
        "system.create_pdf": SkillAffinity(
            skill_id="system.create_pdf",
            intent_keywords=("pdf", "dokument", "bericht", "report"),
            provider_agnostic_fallback="text_synthesis",
            requires_external_api=False,
            max_context_tokens=3000,
            deterministic_fallback_available=False,
        ),
        "system.generate_image": SkillAffinity(
            skill_id="system.generate_image",
            intent_keywords=("bild", "zeichne", "male", "foto", "image", "generiere"),
            provider_agnostic_fallback="none",
            requires_external_api=True,
            max_context_tokens=1000,
            deterministic_fallback_available=False,
        ),
        "memory.save_core_fact": SkillAffinity(
            skill_id="memory.save_core_fact",
            intent_keywords=("merke", "erinner", "speicher", "vergiss nicht", "mein", "ich bin", "ich habe"),
            provider_agnostic_fallback="text_synthesis",
            requires_external_api=False,
            max_context_tokens=800,
            deterministic_fallback_available=False,
        ),
        "knowledge.query": SkillAffinity(
            skill_id="knowledge.query",
            intent_keywords=("dokument", "pdf", "wissen", "knowledge", "suche in"),
            provider_agnostic_fallback="chroma_rag",
            requires_external_api=False,
            max_context_tokens=2000,
            deterministic_fallback_available=True,
        ),
    }


def get_skill_affinity_registry() -> Dict[str, SkillAffinity]:
    global _SKILL_AFFINITY_REGISTRY
    if not _SKILL_AFFINITY_REGISTRY:
        _SKILL_AFFINITY_REGISTRY = _build_default_affinity_registry()
    return dict(_SKILL_AFFINITY_REGISTRY)


def get_skill_affinity(skill_id: str) -> Optional[SkillAffinity]:
    return get_skill_affinity_registry().get(str(skill_id or "").strip())


def match_intent_to_skills(user_prompt: str, *, top_k: int = 3) -> List[str]:
    """Return up to *top_k* skill IDs whose intent keywords match the prompt.

    This is a fast, deterministic pre-filter that runs *before* the LLM sees
    any tools.  It allows the gateway to narrow the tool list for local models
    that struggle with large tool catalogs.
    """
    lowered = str(user_prompt or "").strip().lower()
    if not lowered:
        return []

    scored: List[Tuple[int, str]] = []
    for skill_id, affinity in get_skill_affinity_registry().items():
        hits = sum(1 for kw in affinity.intent_keywords if kw in lowered)
        if hits > 0:
            scored.append((hits, skill_id))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [skill_id for _hits, skill_id in scored[:top_k]]


def has_deterministic_fallback(skill_id: str) -> bool:
    affinity = get_skill_affinity(skill_id)
    return bool(affinity and affinity.deterministic_fallback_available)


@dataclass
class ToolCallFailure:
    skill_id: str
    error_code: str
    is_retryable: bool
    should_degrade_to_text: bool
    fallback_strategy: str


def classify_tool_call_failure(
    skill_id: str,
    error_code: str,
    provider: str,
) -> ToolCallFailure:
    """Classify a failed tool call and recommend a recovery strategy."""
    normalized_code = str(error_code or "").strip().upper()
    normalized_provider = str(provider or "").strip().lower()
    affinity = get_skill_affinity(skill_id)

    retryable_codes = {"TIMEOUT", "RATE_LIMIT", "NETWORK_ERROR", "503", "504"}
    terminal_codes = {"SKILL_NOT_FOUND", "INVALID_ARGUMENTS", "SANDBOX_VIOLATION", "MISSING_CONTENT"}

    is_retryable = normalized_code in retryable_codes
    is_terminal = normalized_code in terminal_codes

    if is_terminal:
        return ToolCallFailure(
            skill_id=skill_id,
            error_code=normalized_code,
            is_retryable=False,
            should_degrade_to_text=True,
            fallback_strategy="error_report",
        )

    if affinity and affinity.deterministic_fallback_available and normalized_provider == "ollama":
        return ToolCallFailure(
            skill_id=skill_id,
            error_code=normalized_code,
            is_retryable=is_retryable,
            should_degrade_to_text=False,
            fallback_strategy=affinity.provider_agnostic_fallback,
        )

    return ToolCallFailure(
        skill_id=skill_id,
        error_code=normalized_code,
        is_retryable=is_retryable,
        should_degrade_to_text=not is_retryable,
        fallback_strategy="retry" if is_retryable else "text_synthesis",
    )
