import pytest

from backend.llm_providers.shared.tool_call_adapter import get_tool_call_adapter
from backend.llm_providers.transports.gemini_native import GeminiNativeTransport


class FakeGeminiService:
    def __init__(self):
        self.generate_response_calls = []
        self.prepare_history_calls = []
        self.convert_tools_calls = []
        self._tool_adapter = get_tool_call_adapter("gemini")

    async def generate_response(
        self,
        api_key,
        model,
        messages,
        tools=None,
        **kwargs,
    ):
        self.generate_response_calls.append(
            {
                "api_key": api_key,
                "model": model,
                "messages": messages,
                "tools": tools,
                "kwargs": kwargs,
            }
        )
        return {
            "type": "tool_code",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "system_weather",
                        "arguments": "{}",
                    },
                }
            ],
        }

    def prepare_history_for_second_call(
        self,
        chat_history,
        raw_assistant_response,
        tool_results,
    ):
        self.prepare_history_calls.append(
            {
                "chat_history": chat_history,
                "raw_assistant_response": raw_assistant_response,
                "tool_results": tool_results,
            }
        )
        return chat_history + [raw_assistant_response] + tool_results

    def _convert_tools_to_gemini_format(self, tools):
        self.convert_tools_calls.append(list(tools))
        return self._tool_adapter.convert_tools_to_gemini_format(tools)


@pytest.mark.asyncio
async def test_gemini_native_transport_delegates_send_to_service():
    service = FakeGeminiService()
    transport = GeminiNativeTransport(service)

    messages = [{"role": "user", "content": "hello"}]
    tools = [{"name": "system.weather", "description": "weather", "parameters": {"type": "object", "properties": {}}}]
    response = await transport.send(
        api_key="test-key",
        model="gemini-test",
        messages=messages,
        tools=tools,
        force_tool_name="system.weather",
    )

    assert len(service.generate_response_calls) == 1
    call = service.generate_response_calls[0]
    assert call["api_key"] == "test-key"
    assert call["model"] == "gemini-test"
    assert call["messages"] == messages
    assert call["tools"] == tools
    assert call["kwargs"] == {"force_tool_name": "system.weather"}
    assert response["type"] == "tool_code"
    assert response["tool_calls"][0]["function"]["name"] == "system_weather"


def test_gemini_native_transport_normalize_tools_uses_adapter_boundary():
    service = FakeGeminiService()
    transport = GeminiNativeTransport(service)
    tools = [
        {
            "name": "system.weather",
            "description": "weather",
            "parameters": {"type": "object", "properties": {}},
        }
    ]

    normalized = transport.normalize_tools(tools)

    assert service.convert_tools_calls == [tools]
    assert normalized[0]["function_declarations"][0]["name"] == "system_weather"


def test_gemini_native_transport_normalize_tools_empty_input():
    service = FakeGeminiService()
    transport = GeminiNativeTransport(service)

    assert transport.normalize_tools(None) == []
    assert transport.normalize_tools([]) == []
    assert service.convert_tools_calls == []


def test_gemini_native_transport_delegates_prepare_history_to_service():
    service = FakeGeminiService()
    transport = GeminiNativeTransport(service)
    chat_history = [{"role": "user", "content": "hello"}]
    raw_assistant_response = {"role": "assistant", "tool_calls": []}
    tool_results = [{"role": "tool", "content": "ok"}]

    prepared = transport.prepare_history_for_second_call(
        chat_history,
        raw_assistant_response,
        tool_results,
    )

    assert len(service.prepare_history_calls) == 1
    assert service.prepare_history_calls[0]["chat_history"] == chat_history
    assert service.prepare_history_calls[0]["raw_assistant_response"] == raw_assistant_response
    assert service.prepare_history_calls[0]["tool_results"] == tool_results
    assert prepared == chat_history + [raw_assistant_response] + tool_results
