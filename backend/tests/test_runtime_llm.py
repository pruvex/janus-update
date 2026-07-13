import pytest

from backend.llm_providers.runtime_llm import (
    OPENROUTER_BASE_URL,
    ResolvedLLM,
    RuntimeLLMResolutionError,
    get_transport_class_for_api_mode,
    get_transport_registry,
    resolve,
)
from backend.llm_providers.transports.gemini_native import GeminiNativeTransport
from backend.llm_providers.transports.ollama_local import OllamaLocalTransport
from backend.llm_providers.transports.openai_compat import OpenAICompatTransport
from backend.services import llm_gateway


@pytest.mark.parametrize(
    ("provider", "model", "api_mode", "transport_class", "credential_provider", "base_url", "auth_mode"),
    [
        ("openai", "gpt-5.4-mini", "openai_compat", OpenAICompatTransport, "openai", None, "api_key"),
        (
            "openrouter",
            "anthropic/claude-sonnet-4",
            "openai_compat",
            OpenAICompatTransport,
            "openrouter",
            OPENROUTER_BASE_URL,
            "api_key",
        ),
        ("gemini", "gemini-3-flash-preview", "gemini_native", GeminiNativeTransport, "gemini", None, "api_key"),
        ("google", "gemini-3-flash-preview", "gemini_native", GeminiNativeTransport, "google", None, "api_key"),
        ("ollama", "llama3", "ollama_local", OllamaLocalTransport, None, None, "none"),
    ],
)
def test_resolve_maps_supported_providers_deterministically(
    provider,
    model,
    api_mode,
    transport_class,
    credential_provider,
    base_url,
    auth_mode,
):
    first = resolve(provider, model)
    second = resolve(provider, model)

    assert first == second
    assert isinstance(first, ResolvedLLM)
    assert first.provider == provider
    assert first.model_id == model
    assert first.api_mode == api_mode
    assert first.transport_class is transport_class
    assert first.credential_provider == credential_provider
    assert first.base_url == base_url
    assert first.auth_mode == auth_mode


def test_resolve_openai_codex_placeholder_fails_without_transport():
    with pytest.raises(RuntimeLLMResolutionError, match="codex_responses transport"):
        resolve("openai-codex", "gpt-5.4")


@pytest.mark.parametrize("provider", ["", "   ", "anthropic", "deepseek", "unknown-provider"])
def test_resolve_rejects_invalid_or_unknown_providers(provider):
    with pytest.raises(RuntimeLLMResolutionError):
        resolve(provider, "model-id")


def test_get_transport_registry_exposes_phase_b_transports_only():
    registry = get_transport_registry()

    assert set(registry) == {"openai_compat", "gemini_native", "ollama_local"}
    assert registry["openai_compat"] is OpenAICompatTransport
    assert registry["gemini_native"] is GeminiNativeTransport
    assert registry["ollama_local"] is OllamaLocalTransport
    assert "codex_responses" not in registry


def test_get_transport_class_for_api_mode_rejects_unknown_mode():
    with pytest.raises(RuntimeLLMResolutionError, match="Unknown api_mode"):
        get_transport_class_for_api_mode("codex_responses")


def test_llm_gateway_registry_seam_is_non_consuming_delegate():
    assert llm_gateway.get_transport_registry() == get_transport_registry()
    assert (
        llm_gateway.get_transport_class_for_api_mode("gemini_native")
        is GeminiNativeTransport
    )
