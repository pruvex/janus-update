"""Builds optional system directives for proactive suggestions (modes OFF / SMART / PROACTIVE)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Set, TypedDict

from backend.services.orchestrator.prompt_registry import prompt_registry
from backend.utils import intent_classifier


class SuggestionContextV1(TypedDict):
    """Typed payload for ``gateway_kwargs['_suggestion_context']`` (tool-loop refresh)."""

    base_system: str
    mode: int
    memory_context: str
    user_text: str


def _word_count(user_text: str) -> int:
    p = (user_text or "").strip()
    if not p:
        return 0
    return len(re.split(r"\s+", p))


def _is_ack_or_tiny(user_text: str) -> bool:
    return _word_count(user_text) < 3


def _parse_tool_payload(content: Any) -> Optional[Dict[str, Any]]:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _tags_from_tool_payload(payload: Dict[str, Any]) -> List[str]:
    meta = payload.get("metadata")
    if not isinstance(meta, dict):
        return []
    suggestion = meta.get("suggestion")
    if not isinstance(suggestion, dict):
        return []
    raw_tags = suggestion.get("relevance_tags")
    if not isinstance(raw_tags, list):
        return []
    return [str(t).strip() for t in raw_tags if str(t).strip()]


def _collect_relevance_tags(tool_results: List[Dict[str, Any]]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for item in tool_results:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("metadata"), dict):
            payload: Optional[Dict[str, Any]] = item
        else:
            payload = _parse_tool_payload(item.get("content")) or _parse_tool_payload(item.get("_raw_content"))
        if not payload:
            continue
        for t in _tags_from_tool_payload(payload):
            if t not in seen:
                seen.add(t)
                ordered.append(t)
    return ordered


def tool_loop_buffer_to_result_dicts(buffer: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize tool-loop ``results_buffer`` entries to parsed ToolResult-like dicts (best-effort)."""
    out: List[Dict[str, Any]] = []
    for item in buffer:
        if not isinstance(item, dict):
            continue
        payload = _parse_tool_payload(item.get("content")) or _parse_tool_payload(item.get("_raw_content"))
        if payload:
            out.append(payload)
    return out


def refresh_suggestion_system_message_after_tools(
    chat_history: List[Dict[str, Any]],
    results_buffer: List[Dict[str, Any]],
    suggestion_context: SuggestionContextV1,
) -> None:
    """Recompute suggestion suffix after tools using the frozen base prompt + aggregated tool metadata."""
    if not chat_history:
        return
    first = chat_history[0]
    if str(first.get("role") or "").lower() != "system":
        return
    base = str(suggestion_context.get("base_system") or "")
    raw_mode = suggestion_context.get("mode", 1)
    mode = 1 if raw_mode is None else int(raw_mode)
    memory_context = str(suggestion_context.get("memory_context") or "")
    user_text = str(suggestion_context.get("user_text") or "")
    tool_dicts = tool_loop_buffer_to_result_dicts(results_buffer)
    directive = SuggestionEngine.build_suggestion_directive(mode, tool_dicts, memory_context, user_text)
    if directive:
        first["content"] = f"{base}\n\n{directive}" if base else directive
    else:
        first["content"] = base


class SuggestionEngine:
    """Directive-builder for proactive suggestion modes (no prompt string literals here)."""

    @staticmethod
    def build_suggestion_directive(
        mode: int,
        tool_results: List[Dict[str, Any]],
        memory_context: str,
        user_text: str,
    ) -> Optional[str]:
        if _is_ack_or_tiny(user_text) or intent_classifier.is_greeting(user_text):
            return None

        if mode == 0:
            # STEEL-CONCRETE directive for OFF mode: absolute prohibition of suggestions
            return prompt_registry.get_directive("suggestion_mode_0")

        tags = _collect_relevance_tags(tool_results)

        if mode == 1:
            if not tags:
                return prompt_registry.get_directive("suggestion_mode_1")
            tags_line = ", ".join(tags)
            template = prompt_registry.get_directive("suggestion_mode_1_tagged")
            return template.format(tags_line=tags_line)

        # Mode 2 (PROACTIVE): immer „Travel Planner“-Direktiven aus der Registry — nie auf Mode 1 zurückfallen.
        if mode == 2:
            if tags:
                tags_line = ", ".join(tags)
                return prompt_registry.get_directive("suggestion_mode_2_tagged").format(tags_line=tags_line)
            return prompt_registry.get_directive("suggestion_mode_2")

        return prompt_registry.get_directive("suggestion_mode_1")
