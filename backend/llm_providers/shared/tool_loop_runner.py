"""Provider-neutral tool-loop execution extracted from gateway implementations."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from backend.llm_providers.shared.moa import resolve_moa_model

logger = logging.getLogger("janus_backend")

TRANSPORT_TOOL_LOOP_RUNNER_ENABLED = os.getenv(
    "TRANSPORT_TOOL_LOOP_RUNNER_ENABLED", "false"
).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class ToolLoopContext:
    provider: str
    model: str
    api_key: str
    chat_history: List[Dict[str, Any]]
    user_prompt: str
    allowed_skill_ids: Optional[List[str]]
    tool_executor: Any
    max_tool_rounds: int
    image_data: Optional[str] = None
    force_tool_name: Optional[str] = None
    passthrough_kwargs: Dict[str, Any] = field(default_factory=dict)
    current_round: int = 0
    tool_execution_model: str = ""
    moa_active: bool = False
    all_tool_results: List[Dict[str, Any]] = field(default_factory=list)
    loop_cost_eur: float = 0.0
    loop_input_tokens: int = 0
    loop_output_tokens: int = 0
    loop_websearch_queries: int = 0


@dataclass
class NonToolResponseAction:
    kind: str
    response: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[Dict[str, Any]]] = None


HandleNonToolResponse = Callable[
    [Dict[str, Any], ToolLoopContext, Optional[str]],
    Awaitable[NonToolResponseAction],
]

ResolveExecutionModel = Callable[[ToolLoopContext], Tuple[str, bool]]
ResolveMaxToolRounds = Callable[[ToolLoopContext], int]
OnRoundResponse = Callable[[Dict[str, Any], ToolLoopContext], None]


class ToolLoopRunner:
    """Runs provider-neutral tool rounds; gateway hooks handle synthesis and fallback."""

    @staticmethod
    def resolve_tool_execution_model(
        *,
        provider: str,
        model: str,
        chat_history: List[Dict[str, Any]],
        allowed_skill_ids: Optional[List[str]],
    ) -> Tuple[str, bool]:
        user_base_model = model
        forced_model = None
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "system" and "MODEL_OVERRIDE:" in str(msg.get("content", "")):
                    match = re.search(r"MODEL_OVERRIDE:\s*(\S+)", str(msg.get("content", "")))
                    if match:
                        forced_model = match.group(1)
                        logger.info(
                            "ToolLoopRunner: Model override detected from execution_engine: %s",
                            forced_model,
                        )
                        break

        if forced_model:
            return forced_model, True

        tool_execution_model, moa_active = resolve_moa_model(
            provider=provider,
            user_base_model=user_base_model,
            allowed_skill_ids=allowed_skill_ids,
        )

        if allowed_skill_ids and "system.websearch" in allowed_skill_ids:
            ws_model, ws_moa = resolve_moa_model(
                provider=provider,
                user_base_model=user_base_model,
                allowed_skill_ids=["system.websearch"],
            )
            if ws_moa:
                tool_execution_model = ws_model
                moa_active = True
                logger.info(
                    "WEBSEARCH-SKILL-OVERRIDE: Using model: %s for synthesis "
                    "(tier via system.websearch JSON contract) [Provider: %s]",
                    ws_model,
                    provider,
                )

        return tool_execution_model, moa_active

    @staticmethod
    def prepare_tools(
        allowed_skill_ids: Optional[List[str]],
        *,
        filter_tools_by_skill_ids: Callable[[Optional[List[str]]], List[Dict[str, Any]]],
        build_tool_definitions_for_llm: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        all_available_tools = filter_tools_by_skill_ids(allowed_skill_ids)
        return build_tool_definitions_for_llm(all_available_tools)

    @staticmethod
    def _accumulate_usage(context: ToolLoopContext, response: Dict[str, Any]) -> None:
        round_cost = response.get("cost") or {}
        round_usage = response.get("usage") or {}
        context.loop_cost_eur += float(round_cost.get("total_cost", 0.0))
        context.loop_input_tokens += int(round_usage.get("input_tokens", 0))
        context.loop_output_tokens += int(round_usage.get("output_tokens", 0))

    async def run(
        self,
        *,
        service: Any,
        context: ToolLoopContext,
        sanitize_generate_response_kwargs: Callable[..., Dict[str, Any]],
        prepare_history_for_second_call: Callable[..., List[Dict[str, Any]]],
        handle_non_tool_response: HandleNonToolResponse,
        filter_tools_by_skill_ids: Optional[Callable[[Optional[List[str]]], List[Dict[str, Any]]]] = None,
        build_tool_definitions_for_llm: Optional[Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]] = None,
        prevalidate_tool_calls: Optional[Callable[..., Dict[str, Any]]] = None,
        resolve_execution_model: Optional[ResolveExecutionModel] = None,
        resolve_max_tool_rounds: Optional[ResolveMaxToolRounds] = None,
        on_round_response: Optional[OnRoundResponse] = None,
    ) -> Dict[str, Any]:
        if (
            filter_tools_by_skill_ids is None
            or build_tool_definitions_for_llm is None
            or prevalidate_tool_calls is None
        ):
            # Keep the disabled gateway path free of the heavy skill-router import chain.
            from backend.llm_providers.shared.utils import (
                _build_tool_definitions_for_llm,
                _filter_tools_by_skill_ids,
                _prevalidate_tool_calls,
            )

            filter_tools_by_skill_ids = filter_tools_by_skill_ids or _filter_tools_by_skill_ids
            build_tool_definitions_for_llm = (
                build_tool_definitions_for_llm or _build_tool_definitions_for_llm
            )
            prevalidate_tool_calls = prevalidate_tool_calls or _prevalidate_tool_calls

        if resolve_execution_model is not None:
            context.tool_execution_model, context.moa_active = resolve_execution_model(context)
        else:
            context.tool_execution_model, context.moa_active = self.resolve_tool_execution_model(
                provider=context.provider,
                model=context.model,
                chat_history=context.chat_history,
                allowed_skill_ids=context.allowed_skill_ids,
            )
        if resolve_max_tool_rounds is not None:
            context.max_tool_rounds = resolve_max_tool_rounds(context)
        tools_for_call = self.prepare_tools(
            context.allowed_skill_ids,
            filter_tools_by_skill_ids=filter_tools_by_skill_ids,
            build_tool_definitions_for_llm=build_tool_definitions_for_llm,
        )

        while context.current_round < context.max_tool_rounds:
            context.current_round += 1

            loop_kwargs = context.passthrough_kwargs.get("passthrough_kwargs")
            if loop_kwargs is None:
                loop_kwargs = {}
            loop_kwargs = sanitize_generate_response_kwargs(
                loop_kwargs,
                "api_key",
                "model",
                "messages",
                "tools",
                "image_data",
            )

            round_force = context.force_tool_name if context.current_round == 1 else None
            response = await service.generate_response(
                api_key=context.api_key,
                model=context.tool_execution_model,
                messages=context.chat_history,
                tools=tools_for_call,
                image_data=context.image_data if context.current_round == 1 else None,
                force_tool_name=round_force,
                **loop_kwargs,
            )
            self._accumulate_usage(context, response)
            if on_round_response is not None:
                on_round_response(response, context)

            if response.get("type") != "tool_code":
                action = await handle_non_tool_response(response, context, round_force)
                if action.kind == "continue":
                    if action.chat_history is not None:
                        context.chat_history = action.chat_history
                    continue
                if action.response is not None:
                    return action.response

            tool_calls = response.get("tool_calls", [])
            preflight = prevalidate_tool_calls(tool_calls, user_prompt=context.user_prompt)
            validated_tool_calls = preflight["valid_calls"]
            if not validated_tool_calls:
                return response

            executor_results = await context.tool_executor.execute_tool_calls(validated_tool_calls)
            for tool_result in executor_results or []:
                if isinstance(tool_result, dict):
                    context.all_tool_results.append(tool_result)

            context.chat_history = prepare_history_for_second_call(
                chat_history=context.chat_history,
                raw_assistant_response=response.get("raw_assistant_response"),
                tool_results=executor_results,
            )

        return {
            "text": "Maximale Tool-Runden erreicht.",
            "tool_limit_reached": True,
            "_internal_tool_results": context.all_tool_results,
        }
