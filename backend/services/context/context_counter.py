from __future__ import annotations

import math
from typing import Any, Iterable

SAFETY_MARGIN = 1.1
CHARS_PER_TOKEN = 4
MESSAGE_OVERHEAD_TOKENS = 4


def estimate_text_tokens(text: Any, safety_margin: float = SAFETY_MARGIN) -> int:
    value = "" if text is None else str(text)
    if not value:
        return 0
    return max(1, int(math.ceil((len(value) / CHARS_PER_TOKEN) * safety_margin)))


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or item.get("image_url") or ""
                if text:
                    parts.append(str(text))
            elif item is not None:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, dict):
        text = content.get("text") or content.get("content") or content.get("message") or ""
        return str(text) if text else ""
    return str(content)


def estimate_message_tokens(message: Any) -> int:
    if isinstance(message, dict):
        content = _content_to_text(message.get("content", message.get("text", "")))
        role = str(message.get("role") or message.get("sender") or "")
        return estimate_text_tokens(content) + estimate_text_tokens(role, safety_margin=1.0) + MESSAGE_OVERHEAD_TOKENS
    return estimate_text_tokens(message) + MESSAGE_OVERHEAD_TOKENS


def estimate_messages_tokens(messages: Iterable[Any] | None) -> int:
    if not messages:
        return 0
    return sum(estimate_message_tokens(message) for message in messages)
