from backend.llm_providers.ollama_adapter import (
    build_default_capabilities,
    build_text_outcome,
    build_tool_outcome,
    clear_cached_capabilities,
    get_cached_capabilities,
    set_cached_native_tool_support,
)


def setup_function() -> None:
    clear_cached_capabilities()


def test_build_default_capabilities_marks_gemma2_as_tool_blind():
    capabilities = build_default_capabilities("gemma2:27b", "http://localhost:11434/v1")

    assert capabilities.tool_blind is True
    assert capabilities.supports_native_tools is False
    assert capabilities.prefers_text_only_synthesis is True


def test_cached_capabilities_can_override_native_tool_support():
    model = "llama3.1:8b"
    base_url = "http://localhost:11434/v1"

    set_cached_native_tool_support(model, base_url, False)
    capabilities = get_cached_capabilities(model, base_url)

    assert capabilities is not None
    assert capabilities.supports_native_tools is False
    assert capabilities.tool_blind is False


def test_build_text_outcome_has_canonical_payload_shape():
    result = build_text_outcome(text="Hallo", usage={"input_tokens": 2}, finish_reason="stop", degraded=True)

    assert result["type"] == "text"
    assert result["text"] == "Hallo"
    assert result["usage"]["input_tokens"] == 2
    assert result["finish_reason"] == "stop"
    assert result["degraded"] is True


def test_build_tool_outcome_has_canonical_payload_shape():
    result = build_tool_outcome(
        tool_calls=[{"id": "1", "type": "function", "function": {"name": "system.test", "arguments": "{}"}}],
        usage={"output_tokens": 4},
        raw_assistant_response={"role": "assistant", "content": "{}"},
    )

    assert result["type"] == "tool_code"
    assert result["tool_calls"][0]["function"]["name"] == "system.test"
    assert result["usage"]["output_tokens"] == 4
    assert result["raw_assistant_response"]["role"] == "assistant"
