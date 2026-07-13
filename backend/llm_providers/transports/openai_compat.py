"""OpenAI-compatible transport delegating to the existing OpenAI service seam."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from backend.llm_providers.shared.base_transport import BaseTransport


@runtime_checkable
class OpenAIServiceLike(Protocol):
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        ...

    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict[str, Any]],
        raw_assistant_response: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        ...

    def _convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        ...


class OpenAICompatTransport(BaseTransport):
    """Transport for OpenAI-compatible API families."""

    def __init__(self, service: OpenAIServiceLike):
        self._service = service

    async def send(
        self,
        *,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return await self._service.generate_response(
            api_key,
            model,
            messages,
            tools=tools,
            **kwargs,
        )

    def normalize_tools(self, tools: Optional[List[Any]]) -> List[Dict[str, Any]]:
        if not tools:
            return []
        return self._service._convert_tools_to_openai_format(list(tools))

    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict[str, Any]],
        raw_assistant_response: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return self._service.prepare_history_for_second_call(
            chat_history,
            raw_assistant_response,
            tool_results,
        )
