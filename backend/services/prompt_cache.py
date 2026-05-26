from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Literal, Optional

logger = logging.getLogger("janus_backend")

PROMPT_CACHE_VERSION = "task056.v1"

SegmentType = Literal[
    "base_prompt",
    "identity_anchor",
    "identity_directive",
    "directive",
    "skill_directive",
    "tool_schema",
    "recent_history",
    "user_input",
    "clock_line",
    "suggestion_suffix",
    "capability_guidance",
    "fact_coupons",
    "policy_injection",
]


@dataclass(frozen=True)
class PromptSegment:
    segment_id: str
    segment_type: str
    content: str
    cacheable: bool
    stability_reason: str
    content_hash: str
    token_estimate: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["content"] = ""
        data["content_length"] = len(self.content or "")
        return data


@dataclass(frozen=True)
class PromptCacheKey:
    provider: str
    model: str
    segment_type: str
    content_hash: str
    prompt_version: str = PROMPT_CACHE_VERSION
    tool_schema_hash: Optional[str] = None
    scope: Optional[str] = None

    def stable_key(self) -> str:
        raw = "|".join(
            [
                self.provider,
                self.model,
                self.segment_type,
                self.prompt_version,
                self.content_hash,
                self.tool_schema_hash or "",
                self.scope or "",
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class PromptCacheEntry:
    key: str
    token_estimate: int
    created_at: float = field(default_factory=time.time)
    hits: int = 0


@dataclass
class PromptCacheDecision:
    enabled: bool
    provider: str
    model: str
    cache_hits: int = 0
    cache_misses: int = 0
    cache_bypassed: int = 0
    estimated_tokens_saved: int = 0
    native_cache_supported: bool = False
    native_cache_applied: bool = False
    token_estimation_method: str = "heuristic"
    reason: Optional[str] = None
    user_scope: Optional[str] = None
    chat_scope: Optional[str] = None
    segments: list[PromptSegment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_bypassed": self.cache_bypassed,
            "estimated_tokens_saved": self.estimated_tokens_saved,
            "native_cache_supported": self.native_cache_supported,
            "native_cache_applied": self.native_cache_applied,
            "token_estimation_method": self.token_estimation_method,
            "reason": self.reason,
            "user_scope": self.user_scope,
            "chat_scope": self.chat_scope,
            "segments": [segment.to_dict() for segment in self.segments],
        }


class PromptCacheStore:
    def __init__(self, max_entries: int = 500, ttl_seconds: int = 3600):
        self._store: Dict[str, PromptCacheEntry] = {}
        self._lock = threading.RLock()
        self._max_entries = max(1, int(max_entries))
        self._ttl_seconds = max(1, int(ttl_seconds))

    def get(self, key: str) -> Optional[PromptCacheEntry]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() - entry.created_at > self._ttl_seconds:
                self._store.pop(key, None)
                return None
            entry.hits += 1
            return entry

    def put(self, key: str, entry: PromptCacheEntry) -> None:
        with self._lock:
            if len(self._store) >= self._max_entries:
                oldest_key = min(self._store, key=lambda item: self._store[item].created_at)
                self._store.pop(oldest_key, None)
            self._store[key] = entry

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_STORE = PromptCacheStore(
    max_entries=int(os.getenv("PROMPT_CACHE_MAX_ENTRIES", "500") or "500"),
    ttl_seconds=int(os.getenv("PROMPT_CACHE_TTL_SECONDS", "3600") or "3600"),
)

_CACHEABLE_SEGMENTS = {
    "base_prompt": "stable base prompt",
    "identity_anchor": "stable per user identity anchor",
    "identity_directive": "stable per user/provider identity directive",
    "directive": "stable registry directive",
    "skill_directive": "stable per selected skill set",
    "tool_schema": "stable schema hash dependent",
}

_DYNAMIC_SEGMENTS = {
    "clock_line": "changes every minute",
    "suggestion_suffix": "depends on user_text and memory_context",
    "capability_guidance": "depends on selected skills and request routing",
    "fact_coupons": "depends on retrieval for current turn",
    "recent_history": "turn dependent",
    "user_input": "current user input",
    "policy_injection": "policy turn dependent",
}

_NATIVE_CACHE_PROVIDERS = {"openai", "gemini", "google"}


def _is_enabled() -> bool:
    value = os.getenv("PROMPT_CACHE_ENABLED", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _hash_content(content: str) -> str:
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


def _estimate_tokens(content: str) -> int:
    words = len((content or "").split())
    return max(0, int(words * 1.3))


def _segment_scope(segment_type: str, user_scope: Optional[str], chat_scope: Optional[str]) -> Optional[str]:
    if segment_type in {"identity_anchor", "identity_directive"}:
        return user_scope or chat_scope
    if segment_type in {"recent_history", "user_input", "fact_coupons", "policy_injection"}:
        return chat_scope
    return None


def build_segments(raw_segments: Dict[str, Any]) -> list[PromptSegment]:
    segments: list[PromptSegment] = []
    for segment_type, value in raw_segments.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            content = "\n".join(str(item) for item in value if str(item or "").strip())
        else:
            content = str(value or "")
        if not content.strip():
            continue
        cacheable = segment_type in _CACHEABLE_SEGMENTS
        reason = _CACHEABLE_SEGMENTS.get(segment_type) or _DYNAMIC_SEGMENTS.get(segment_type) or "unclassified segment"
        segments.append(
            PromptSegment(
                segment_id=f"{segment_type}:{_hash_content(content)[:12]}",
                segment_type=segment_type,
                content=content,
                cacheable=cacheable,
                stability_reason=reason,
                content_hash=_hash_content(content),
                token_estimate=_estimate_tokens(content),
            )
        )
    if segments:
        logger.info("[PROMPT-CACHE] build_segments: %d segments (%d cacheable, %d dynamic)",
                    len(segments),
                    sum(1 for s in segments if s.cacheable),
                    sum(1 for s in segments if not s.cacheable))
    return segments


def decide_prompt_cache(
    *,
    provider: str,
    model: str,
    raw_segments: Dict[str, Any],
    tool_schema_hash: Optional[str] = None,
    user_scope: Optional[str] = None,
    chat_scope: Optional[str] = None,
) -> PromptCacheDecision:
    provider_key = str(provider or "").strip().lower()
    model_key = str(model or "").strip()
    segments = build_segments(raw_segments)
    enabled = _is_enabled()
    decision = PromptCacheDecision(
        enabled=enabled,
        provider=provider_key,
        model=model_key,
        native_cache_supported=provider_key in _NATIVE_CACHE_PROVIDERS,
        reason=None if enabled else "PROMPT_CACHE_ENABLED=false",
        user_scope=user_scope,
        chat_scope=chat_scope,
        segments=segments,
    )
    for segment in segments:
        if not enabled or not segment.cacheable:
            decision.cache_bypassed += 1
            continue
        key = PromptCacheKey(
            provider=provider_key,
            model=model_key,
            segment_type=segment.segment_type,
            content_hash=segment.content_hash,
            tool_schema_hash=tool_schema_hash if segment.segment_type == "tool_schema" else None,
            scope=_segment_scope(segment.segment_type, user_scope, chat_scope),
        ).stable_key()
        entry = _STORE.get(key)
        if entry is None:
            decision.cache_misses += 1
            _STORE.put(key, PromptCacheEntry(key=key, token_estimate=segment.token_estimate))
        else:
            decision.cache_hits += 1
            decision.estimated_tokens_saved += entry.token_estimate
    logger.info("[PROMPT-CACHE] decide: enabled=%s provider=%s model=%s hits=%d misses=%d bypassed=%d est_saved=%d",
                decision.enabled, decision.provider, decision.model,
                decision.cache_hits, decision.cache_misses, decision.cache_bypassed,
                decision.estimated_tokens_saved)
    return decision


def clone_decision_for_route(
    decision: Optional[PromptCacheDecision],
    *,
    provider: str,
    model: str,
) -> Optional[PromptCacheDecision]:
    if decision is None:
        return None
    return PromptCacheDecision(
        enabled=decision.enabled,
        provider=str(provider or "").strip().lower(),
        model=str(model or "").strip(),
        cache_hits=decision.cache_hits,
        cache_misses=decision.cache_misses,
        cache_bypassed=decision.cache_bypassed,
        estimated_tokens_saved=decision.estimated_tokens_saved,
        native_cache_supported=str(provider or "").strip().lower() in _NATIVE_CACHE_PROVIDERS,
        native_cache_applied=decision.native_cache_applied,
        token_estimation_method=decision.token_estimation_method,
        reason=decision.reason,
        user_scope=decision.user_scope,
        chat_scope=decision.chat_scope,
        segments=decision.segments,
    )


def merge_decision_into_usage(usage: Dict[str, Any], decision: Optional[PromptCacheDecision]) -> Dict[str, Any]:
    merged = dict(usage or {})
    if decision is None:
        return merged
    metrics = decision.to_dict()
    merged["prompt_cache"] = metrics
    merged.setdefault("cache_hits", decision.cache_hits)
    merged.setdefault("cache_misses", decision.cache_misses)
    merged.setdefault("cache_bypassed", decision.cache_bypassed)
    merged.setdefault("estimated_tokens_saved", decision.estimated_tokens_saved)
    return merged


def decision_from_gateway_kwargs(gateway_kwargs: Dict[str, Any]) -> Optional[PromptCacheDecision]:
    decision = gateway_kwargs.get("_prompt_cache_decision") if isinstance(gateway_kwargs, dict) else None
    return decision if isinstance(decision, PromptCacheDecision) else None


def reset_prompt_cache_store() -> None:
    _STORE.clear()
