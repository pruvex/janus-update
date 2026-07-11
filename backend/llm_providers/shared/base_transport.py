"""Abstract transport contract for provider-family API adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTransport(ABC):
    """Minimal provider-family transport contract for non-streaming tool rounds."""

    @abstractmethod
    async def send(
        self,
        *,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute a non-streaming provider request and return the response payload."""
        raise NotImplementedError

    @abstractmethod
    def normalize_tools(self, tools: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """Convert canonical internal tool definitions to provider API format."""
        raise NotImplementedError

    @abstractmethod
    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict[str, Any]],
        raw_assistant_response: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Prepare chat history for the follow-up request after tool execution."""
        raise NotImplementedError
