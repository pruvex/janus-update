"""Single-attempt OpenRouter Chat Completions service."""

from __future__ import annotations

import math
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import openai
from pydantic import BaseModel

from backend.llm_providers.runtime_llm import OPENROUTER_BASE_URL
from backend.llm_providers.shared.base_provider import BaseLLMProvider
from backend.llm_providers.shared.tool_call_adapter import get_tool_call_adapter
from backend.services.orchestrator.stream_protocol import StreamEvent


class OpenRouterAuthenticationRejected(RuntimeError):
    """Typed, non-secret signal for an explicit upstream credential rejection."""


class OpenRouterModelIdentityError(RuntimeError):
    """Raised when upstream does not return the exact selected model identity."""


class OpenRouterMalformedResponseError(RuntimeError):
    """Raised when an otherwise successful response lacks required structure."""


def _finite_number(value: Any) -> Optional[float | int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(float(value)) else None


def _finite_integer(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def normalize_openrouter_telemetry(
    usage: Dict[str, Any],
    *,
    response_model: str,
) -> Dict[str, Any]:
    """Copy authoritative fields without converting missing values into zeros."""
    usage = dict(usage or {})
    prompt_details = usage.get("prompt_tokens_details")
    completion_details = usage.get("completion_tokens_details")
    cost_details = usage.get("cost_details")
    prompt_details = prompt_details if isinstance(prompt_details, dict) else {}
    completion_details = completion_details if isinstance(completion_details, dict) else {}
    cost_details = cost_details if isinstance(cost_details, dict) else {}
    return {
        "response_model": str(response_model),
        "prompt_tokens": _finite_integer(usage.get("prompt_tokens")),
        "completion_tokens": _finite_integer(usage.get("completion_tokens")),
        "total_tokens": _finite_integer(usage.get("total_tokens")),
        "cached_tokens": _finite_integer(prompt_details.get("cached_tokens")),
        "cache_write_tokens": _finite_integer(prompt_details.get("cache_write_tokens")),
        "reasoning_tokens": _finite_integer(completion_details.get("reasoning_tokens")),
        "credits_cost": _finite_number(usage.get("cost")),
        "upstream_inference_cost": _finite_number(cost_details.get("upstream_inference_cost")),
    }


class OpenRouterServiceProvider(BaseLLMProvider):
    """Dedicated OpenRouter service with zero SDK and decorator retries."""

    def __init__(
        self,
        *,
        client_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._client_factory = client_factory or openai.AsyncOpenAI
        self._tool_adapter = get_tool_call_adapter("openrouter")

    def _client(self, api_key: str) -> Any:
        return self._client_factory(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            timeout=180.0,
            max_retries=0,
        )

    @staticmethod
    def _require_exact_model(actual_model: Any, selected_model: str) -> str:
        actual = str(actual_model or "").strip()
        if not actual or actual != str(selected_model or "").strip():
            raise OpenRouterModelIdentityError("OpenRouter response model identity mismatch.")
        return actual

    def _convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        return self._tool_adapter.convert_tools_to_openai_format(tools)

    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        image_data: Optional[str] = None,
        force_tool_name: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if image_data is not None:
            raise OpenRouterMalformedResponseError("OpenRouter image input is not enabled by this task.")

        params: Dict[str, Any] = {
            "model": model,
            "messages": [dict(message) for message in messages],
        }
        if max_completion_tokens is not None:
            params["max_tokens"] = max_completion_tokens
        if tools:
            converted = self._convert_tools_to_openai_format(tools)
            if converted:
                params["tools"] = converted
                params["tool_choice"] = (
                    {
                        "type": "function",
                        "function": {"name": self._tool_adapter.outbound_name(force_tool_name)},
                    }
                    if force_tool_name
                    else "auto"
                )

        for forbidden in (
            "requested_skills",
            "force_no_tools",
            "is_image_analysis_request",
            "provider",
            "base_url",
            "api_key",
            "model",
            "messages",
            "tools",
        ):
            kwargs.pop(forbidden, None)
        params.update(kwargs)

        try:
            response = await self._client(api_key).chat.completions.create(**params)
        except openai.AuthenticationError as exc:
            raise OpenRouterAuthenticationRejected(
                "OpenRouter rejected the request credential."
            ) from exc

        self._require_exact_model(getattr(response, "model", None), model)
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise OpenRouterMalformedResponseError("OpenRouter response contains no choices.")
        message = getattr(choices[0], "message", None)
        if message is None:
            raise OpenRouterMalformedResponseError("OpenRouter response contains no message.")

        usage_obj = getattr(response, "usage", None)
        usage = (
            usage_obj.model_dump()
            if usage_obj is not None and hasattr(usage_obj, "model_dump")
            else dict(usage_obj or {})
        )
        telemetry = normalize_openrouter_telemetry(usage, response_model=model)
        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            dumped_calls = [
                call.model_dump() if hasattr(call, "model_dump") else dict(call)
                for call in tool_calls
            ]
            raw_message = (
                message.model_dump()
                if hasattr(message, "model_dump")
                else {"role": "assistant", "tool_calls": dumped_calls}
            )
            return {
                "type": "tool_code",
                "tool_calls": dumped_calls,
                "raw_assistant_response": raw_message,
                "usage": usage,
                "provider": "openrouter",
                "model": model,
                "response_model": model,
                "openrouter_telemetry": telemetry,
            }

        return {
            "type": "text",
            "text": getattr(message, "content", None),
            "content": getattr(message, "content", None),
            "finish_reason": getattr(choices[0], "finish_reason", None),
            "usage": usage,
            "provider": "openrouter",
            "model": model,
            "response_model": model,
            "openrouter_telemetry": telemetry,
        }

    async def generate_response_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        force_tool_name: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        params: Dict[str, Any] = {
            "model": model,
            "messages": [dict(message) for message in messages],
            "stream": True,
        }
        if max_completion_tokens is not None:
            params["max_tokens"] = max_completion_tokens
        if tools:
            converted = self._convert_tools_to_openai_format(tools)
            if converted:
                params["tools"] = converted
                params["tool_choice"] = (
                    {
                        "type": "function",
                        "function": {"name": self._tool_adapter.outbound_name(force_tool_name)},
                    }
                    if force_tool_name
                    else "auto"
                )
        kwargs.pop("image_data", None)
        kwargs.pop("force_no_tools", None)
        params.update(kwargs)

        saw_model_identity = False
        pending_finish: Optional[StreamEvent] = None
        try:
            stream = await self._client(api_key).chat.completions.create(**params)
            async for chunk in stream:
                self._require_exact_model(getattr(chunk, "model", None), model)
                saw_model_identity = True
                usage_obj = getattr(chunk, "usage", None)
                if usage_obj is not None:
                    usage = (
                        usage_obj.model_dump()
                        if hasattr(usage_obj, "model_dump")
                        else dict(usage_obj or {})
                    )
                    telemetry = normalize_openrouter_telemetry(
                        usage,
                        response_model=model,
                    )
                    yield StreamEvent(
                        type="usage",
                        content={
                            "usage": usage,
                            "openrouter_telemetry": telemetry,
                        },
                        metadata={"provider": "openrouter", "model": model},
                    )
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                choice = choices[0]
                delta = getattr(choice, "delta", None)
                if delta is not None:
                    text = getattr(delta, "content", None)
                    if text:
                        yield StreamEvent(
                            type="text_delta",
                            content=str(text),
                            metadata={"provider": "openrouter", "model": model},
                        )
                    for tool_call in getattr(delta, "tool_calls", None) or []:
                        function = getattr(tool_call, "function", None)
                        fragment = {
                            "index": getattr(tool_call, "index", 0),
                            "id": getattr(tool_call, "id", None),
                            "name": getattr(function, "name", None) if function else None,
                            "arguments": getattr(function, "arguments", None) if function else None,
                        }
                        yield StreamEvent(
                            type="tool_delta",
                            content={key: value for key, value in fragment.items() if value is not None},
                            metadata={"provider": "openrouter", "model": model},
                        )
                finish_reason = getattr(choice, "finish_reason", None)
                if finish_reason:
                    pending_finish = StreamEvent(
                        type="finish",
                        content=None,
                        metadata={
                            "provider": "openrouter",
                            "model": model,
                            "finish_reason": str(finish_reason),
                        },
                    )
        except openai.AuthenticationError as exc:
            raise OpenRouterAuthenticationRejected(
                "OpenRouter rejected the request credential."
            ) from exc

        if not saw_model_identity:
            raise OpenRouterModelIdentityError(
                "OpenRouter stream contains no response model identity."
            )
        if pending_finish is None:
            raise OpenRouterMalformedResponseError(
                "OpenRouter stream ended without a completion marker."
            )
        yield pending_finish
        yield StreamEvent(
            type="done",
            content=None,
            metadata={"provider": "openrouter", "model": model},
        )

    async def generate_structured_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        response_format: type[BaseModel],
        **kwargs: Any,
    ) -> tuple[BaseModel, Dict[str, Any]]:
        del api_key, model, messages, response_format, kwargs
        raise OpenRouterMalformedResponseError(
            "Structured OpenRouter generation is not enabled by this task."
        )

    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        narrative_prompt: str,
        preset_context: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        del api_key, model, prompt, narrative_prompt, preset_context, kwargs
        raise OpenRouterMalformedResponseError(
            "OpenRouter image generation is not enabled by this task."
        )

    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict[str, Any]],
        raw_assistant_response: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        history = [dict(message) for message in chat_history]
        history.append(dict(raw_assistant_response or {"role": "assistant", "content": ""}))
        for result in tool_results:
            prepared = dict(result)
            if prepared.get("name"):
                prepared["name"] = self._tool_adapter.outbound_name_for_history(
                    str(prepared["name"])
                )
            history.append(prepared)
        return history
