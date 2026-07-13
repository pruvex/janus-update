"""Deterministic provider/model resolution for Phase-B transport dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Type

from backend.llm_providers.shared.base_transport import BaseTransport
from backend.llm_providers.transports.gemini_native import GeminiNativeTransport
from backend.llm_providers.transports.ollama_local import OllamaLocalTransport
from backend.llm_providers.transports.openai_compat import OpenAICompatTransport

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

TRANSPORT_REGISTRY: Dict[str, Type[BaseTransport]] = {
    "openai_compat": OpenAICompatTransport,
    "gemini_native": GeminiNativeTransport,
    "ollama_local": OllamaLocalTransport,
}

_CODEX_PLACEHOLDER_PROVIDERS = frozenset({"openai-codex"})

_PROVIDER_RESOLUTION: Dict[str, tuple[str, Optional[str], Optional[str], str]] = {
    "openai": ("openai_compat", "openai", None, "api_key"),
    "openrouter": ("openai_compat", "openrouter", OPENROUTER_BASE_URL, "api_key"),
    "gemini": ("gemini_native", "gemini", None, "api_key"),
    "google": ("gemini_native", "google", None, "api_key"),
    "ollama": ("ollama_local", None, None, "none"),
}


class RuntimeLLMResolutionError(ValueError):
    """Raised when provider/model cannot be resolved to a supported transport."""


@dataclass(frozen=True)
class ResolvedLLM:
    provider: str
    model_id: str
    api_mode: str
    transport_class: Type[BaseTransport]
    credential_provider: Optional[str]
    base_url: Optional[str]
    auth_mode: str


def get_transport_registry() -> Dict[str, Type[BaseTransport]]:
    """Return a copy of the api_mode -> transport class registry."""
    return dict(TRANSPORT_REGISTRY)


def get_transport_class_for_api_mode(api_mode: str) -> Type[BaseTransport]:
    normalized_mode = str(api_mode or "").strip().lower()
    transport_class = TRANSPORT_REGISTRY.get(normalized_mode)
    if transport_class is None:
        raise RuntimeLLMResolutionError(f"Unknown api_mode: {api_mode!r}")
    return transport_class


def _normalize_provider(provider: str) -> str:
    return str(provider or "").strip().lower()


def _normalize_model(model: str) -> str:
    return str(model or "").strip()


def resolve(
    provider: str,
    model: str,
    *,
    auth_mode: str = "api_key",
) -> ResolvedLLM:
    """
    Resolve provider/model to api_mode, credential metadata, and transport class.

    Credential metadata only; this module does not load keys or tokens.
    """
    normalized_provider = _normalize_provider(provider)
    model_id = _normalize_model(model)

    if not normalized_provider:
        raise RuntimeLLMResolutionError("Provider must be non-empty")

    if normalized_provider in _CODEX_PLACEHOLDER_PROVIDERS:
        raise RuntimeLLMResolutionError(
            "Provider 'openai-codex' requires codex_responses transport (Epic 5); "
            "not available in Phase B"
        )

    mapping = _PROVIDER_RESOLUTION.get(normalized_provider)
    if mapping is None:
        raise RuntimeLLMResolutionError(f"Unsupported provider: {provider!r}")

    api_mode, credential_provider, base_url, resolved_auth_mode = mapping

    return ResolvedLLM(
        provider=normalized_provider,
        model_id=model_id,
        api_mode=api_mode,
        transport_class=get_transport_class_for_api_mode(api_mode),
        credential_provider=credential_provider,
        base_url=base_url,
        auth_mode=resolved_auth_mode,
    )
