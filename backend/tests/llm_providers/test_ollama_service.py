from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm_providers.ollama_adapter import clear_cached_capabilities
from backend.llm_providers.ollama_service import OllamaServiceProvider


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


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_routes_to_model_node_base_url(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True},
            {"id": "remote_lab", "name": "Remote Lab", "url": "http://172.20.128.1:11434", "active": False},
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response("node ok")
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="llama3.1:8b@remote_lab",
        messages=[{"role": "user", "content": "hello"}],
    )

    _, client_kwargs = mock_async_openai.call_args
    assert client_kwargs["base_url"] == "http://172.20.128.1:11434/v1"

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert create_kwargs["model"] == "llama3.1:8b"
    assert result["type"] == "text"
    assert result["text"] == "node ok"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_forces_tool_choice_for_system_routing(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response("tool ok")
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="llama3.1:8b",
        messages=[{"role": "user", "content": "route"}],
        tools=[
            {
                "name": "system.routing",
                "description": "routing",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        force_tool_name="system.routing",
    )

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert "tools" in create_kwargs
    assert create_kwargs["tool_choice"] == {
        "type": "function",
        "function": {"name": "system.routing"},
    }
    assert result["type"] == "text"
    assert result["text"] == "tool ok"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_synthesis_mode_removes_tools_and_enables_stream(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_async_openai.return_value = AsyncMock()

    provider = OllamaServiceProvider()
    provider._create_streaming_text_completion = AsyncMock(
        return_value={"text": "synth", "usage": {"input_tokens": 2, "output_tokens": 1}, "finish_reason": "stop"}
    )

    result = await provider.generate_response(
        api_key="dummy",
        model="llama3.1:8b",
        messages=[{"role": "user", "content": "route"}],
        tools=[
            {
                "name": "system.routing",
                "description": "routing",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        force_tool_name="system.routing",
        call_type="synthesis",
    )

    request_payload = provider._create_streaming_text_completion.await_args.args[1]
    assert "tools" not in request_payload
    assert "tool_choice" not in request_payload
    assert request_payload.get("stream") is True
    assert result["type"] == "text"
    assert result["text"] == "synth"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_extracts_pseudo_tool_json_from_text(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    pseudo_calls_text = (
        "Ich nutze zwei Aufrufe.\n\n"
        '{"name":"get_distance_and_route_tool","parameters":{"origin":"Köln, Deutschland","destination":"Paris, Frankreich","mode":"driving"}}\n'
        '{"name":"get_distance_and_route_tool","parameters":{"origin":"Paris, Frankreich","destination":"Mailand, Italien","mode":"driving"}}'
    )

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(pseudo_calls_text)
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="llama3.1:8b",
        messages=[{"role": "user", "content": "Plane Route Koeln Paris Mailand"}],
        tools=[
            {
                "name": "get_distance_and_route_tool",
                "description": "routing",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
    )

    assert result["type"] == "tool_code"
    tool_calls = result.get("tool_calls") or []
    assert len(tool_calls) == 2
    assert tool_calls[0]["function"]["name"] == "get_distance_and_route_tool"
    assert "Köln, Deutschland" in tool_calls[0]["function"]["arguments"]


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_strict_tool_calls_still_allows_pseudo_tool_fallback(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    pseudo_calls_text = (
        '{"name":"system.country_info","parameters":{"country":"Japan","language":"de"}}'
    )
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(pseudo_calls_text)
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="llama3.1:8b",
        messages=[{"role": "user", "content": "Einwohner von Japan?"}],
        tools=[
            {
                "name": "system.country_info",
                "description": "country info",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        force_tool_name="system.country_info",
        strict_tool_calls=True,
    )

    assert result["type"] == "tool_code"
    tool_calls = result.get("tool_calls") or []
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "system.country_info"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_uses_json_prompt_fallback_when_native_tools_marked_unsupported(
    mock_async_openai,
    mock_load_config_data,
):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(
        '{"name":"system.websearch","parameters":{"query":"KI News"}}'
    )
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    provider._set_native_tool_support("llama3.1:8b", "http://localhost:11434/v1", False)
    result = await provider.generate_response(
        api_key="dummy",
        model="llama3.1:8b",
        messages=[{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Suche KI News"}],
        tools=[
            {
                "name": "system.websearch",
                "description": "websearch",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
            }
        ],
    )

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert "tools" not in create_kwargs
    assert "tool_choice" not in create_kwargs
    assert "TOOL-CALL FALLBACK FORMAT" in create_kwargs["messages"][0]["content"]
    assert result["type"] == "tool_code"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_does_not_forward_force_no_tools_to_openai_client(
    mock_async_openai,
    mock_load_config_data,
):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response("strukturierte Antwort")
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="gemma2:27b",
        messages=[{"role": "user", "content": "Analysiere diese Suchergebnisse."}],
        tools=None,
        force_no_tools=True,
    )

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert "force_no_tools" not in create_kwargs
    assert result["type"] == "text"
    assert result["text"] == "strukturierte Antwort"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_gemma_uses_json_prompt_fallback_with_routing_fewshot(
    mock_async_openai,
    mock_load_config_data,
):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(
        '{"name":"system.routing","parameters":{"origin":"Muenchen","destination":"Koeln"}}'
    )
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="gemma2:27b",
        messages=[{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "wie weit ist es von muenchen nach koeln"}],
        tools=[
            {
                "name": "system.routing",
                "description": "routing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                    },
                },
            }
        ],
    )

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert "tools" not in create_kwargs
    assert "tool_choice" not in create_kwargs
    assert "\"name\": \"system.routing\"" in create_kwargs["messages"][0]["content"]
    assert "\"origin\": \"Startort\"" in create_kwargs["messages"][0]["content"]
    assert result["type"] == "tool_code"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_gemma_uses_local_business_specific_json_fallback(
    mock_async_openai,
    mock_load_config_data,
):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(
        '{"name":"system.local_business","parameters":{"query":"italienisches Restaurant","location":"Berlin Prenzlauer Berg","limit":4}}'
    )
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    result = await provider.generate_response(
        api_key="dummy",
        model="gemma2:27b",
        messages=[{"role": "system", "content": "Du bist Janus."}, {"role": "user", "content": "Finde 4 italienische Restaurants in Berlin Prenzlauer Berg."}],
        tools=[
            {
                "name": "system.local_business",
                "description": "local business search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "location": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query", "location"],
                },
            }
        ],
    )

    _, create_kwargs = mock_client.chat.completions.create.await_args
    assert "tools" not in create_kwargs
    assert "tool_choice" not in create_kwargs
    assert '"name": "system.local_business"' in create_kwargs["messages"][0]["content"]
    assert '"query": "italienisches Restaurant"' in create_kwargs["messages"][0]["content"]
    assert "\"location\": \"Berlin Prenzlauer Berg\"" in create_kwargs["messages"][0]["content"]
    assert result["type"] == "tool_code"


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_normalizes_markdown_wrapped_tool_payload(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _mock_text_response(
        """```json
        {"tool_calls":[{"name":"system.local_business","arguments":{"query":"italienische Restaurants","location":"Berlin Prenzlauer Berg","limit":4}}]}
        ```"""
    )
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    provider._set_native_tool_support("gemma2:27b", "http://localhost:11434/v1", False)
    result = await provider.generate_response(
        api_key="dummy",
        model="gemma2:27b",
        messages=[{"role": "user", "content": "finde 4 italienische restaurants"}],
        tools=[
            {
                "name": "system.local_business",
                "description": "local business",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "location": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query", "location"],
                },
            }
        ],
    )

    assert result["type"] == "tool_code"
    tool_calls = result.get("tool_calls") or []
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "system.local_business"
    assert '"location": "Berlin Prenzlauer Berg"' in tool_calls[0]["function"]["arguments"]


@pytest.mark.asyncio
@patch("backend.llm_providers.ollama.service.load_config_data")
@patch("openai.AsyncOpenAI")
async def test_generate_response_self_heals_missing_required_tool_field_once(mock_async_openai, mock_load_config_data):
    mock_load_config_data.return_value = {
        "ollama_nodes": [
            {"id": "localhost", "name": "Localhost", "url": "http://localhost:11434", "active": True}
        ]
    }

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        _mock_text_response('{"name":"system.local_business","parameters":{"query":"italienische Restaurants","limit":4}}'),
        _mock_text_response('{"name":"system.local_business","parameters":{"query":"italienische Restaurants","location":"Berlin Prenzlauer Berg","limit":4}}'),
    ]
    mock_async_openai.return_value = mock_client

    provider = OllamaServiceProvider()
    provider._set_native_tool_support("gemma2:27b", "http://localhost:11434/v1", False)
    result = await provider.generate_response(
        api_key="dummy",
        model="gemma2:27b",
        messages=[{"role": "user", "content": "finde 4 italienische restaurants in berlin prenzlauer berg"}],
        tools=[
            {
                "name": "system.local_business",
                "description": "local business",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "location": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query", "location"],
                },
            }
        ],
    )

    assert result["type"] == "tool_code"
    tool_calls = result.get("tool_calls") or []
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "system.local_business"
    assert '"location": "Berlin Prenzlauer Berg"' in tool_calls[0]["function"]["arguments"]
    assert mock_client.chat.completions.create.await_count == 2


def test_extract_pseudo_tool_calls_from_text_handles_fenced_json_and_trailing_explanation():
    provider = OllamaServiceProvider()
    raw_text = (
        "Ich plane die Route jetzt.\n"
        "```json\n"
        '{"name":"system.routing","parameters":{"origin":"Muenchen","destination":"Koeln"}}\n'
        "```\n"
        "Hinweis: Danach kann ich auch die Dauer berechnen."
    )

    tool_calls = provider._extract_pseudo_tool_calls_from_text(raw_text)
    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "system.routing"
    assert "Muenchen" in tool_calls[0]["function"]["arguments"]


@pytest.mark.asyncio
async def test_generate_structured_response_strips_markdown_json_block_before_validation(monkeypatch):
    provider = OllamaServiceProvider()

    async def _fake_generate_response(**_kwargs):
        return {"type": "text", "text": "```json\n{\"facts\": []}\n```"}

    monkeypatch.setattr(provider, "generate_response", _fake_generate_response)

    class _FactsSchema:
        @staticmethod
        def model_validate(value):
            assert isinstance(value, dict)
            assert "facts" in value
            return value

    parsed, cost = await provider.generate_structured_response(
        api_key="dummy",
        model="llama3.1:8b",
        messages=[{"role": "user", "content": "Extrahiere Fakten"}],
        response_format=_FactsSchema,
    )

    assert parsed == {"facts": []}
    assert cost == {"total_cost": 0.0}
