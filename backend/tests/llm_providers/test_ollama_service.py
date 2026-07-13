from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm_providers.ollama.adapter import clear_cached_capabilities
from backend.llm_providers.ollama.service import OllamaServiceProvider


def _mock_text_response(text: str = "ok"):
    response = MagicMock()
    message = MagicMock()
    message.tool_calls = None
    message.content = text
    response.choices = [MagicMock()]
    response.choices[0].message = message
    response.choices[0].finish_reason = "stop"
    usage = MagicMock()
    usage.prompt_tokens = 12
    usage.completion_tokens = 4
    response.usage = usage
    return response


def setup_function() -> None:
    clear_cached_capabilities()


def test_normalize_non_native_tool_payload_maps_weather_alias_to_canonical_skill():
    provider = OllamaServiceProvider()

    calls = provider._normalize_non_native_tool_payload(
        '{"name":"system.weather.get_current_weather","arguments":{"city":"Berlin"}}',
        [{"name": "system.weather", "parameters": {"type": "object"}}],
    )

    assert calls[0]["function"]["name"] == "system.weather"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_normal_does_not_forward_estimated_prompt_tokens(
    mock_async_openai,
    mock_load_config_data,
):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response("weather ok")
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="qwen2.5-coder:14b",
        messages=[{"role": "user", "content": "Wie ist das Wetter in Berlin?"}],
        _estimated_prompt_tokens=4200,
    )

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert "_estimated_prompt_tokens" not in create_kwargs
    assert result["type"] == "text"
    assert result["text"] == "weather ok"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_synthesis_does_not_forward_estimated_prompt_tokens(
    mock_async_openai,
    mock_load_config_data,
):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_async_openai.return_value = AsyncMock()

    provider = OllamaServiceProvider()
    provider._create_streaming_text_completion = AsyncMock(
        return_value={"text": "synth ok", "usage": {"input_tokens": 2, "output_tokens": 1}, "finish_reason": "stop"}
    )

    result = await provider.generate_response(
        api_key="dummy",
        model="qwen2.5-coder:14b",
        messages=[{"role": "user", "content": "Synthese bitte"}],
        call_type="synthesis",
        _estimated_prompt_tokens=5100,
    )

    request_payload = provider._create_streaming_text_completion.await_args.args[1]
    assert "_estimated_prompt_tokens" not in request_payload
    assert result["type"] == "text"
    assert result["text"] == "synth ok"
