"""
Memory-Integrity Validation Guard.

Protects the Fact-Extractor from saving hallucinated facts when the model was
explicitly warned about ambiguity (e.g. '!!! SYSTEM-WARNHINWEIS: MEHRERE
DATEIEN GEFUNDEN !!!') but ignored the warning in its final answer.

Usage
-----
    from backend.services.orchestrator.warning_guard import (
        did_model_ignore_warning,
    )

    if did_model_ignore_warning(tool_results, final_text):
        wf.skip_fact_extraction = True
"""
from __future__ import annotations

import json
import logging
from typing import Any, Iterable, List

logger = logging.getLogger("janus_backend")

WARNING_MARKER = "!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!"

# Acknowledgement phrases the model MUST use to pass the guard.
# German (primary) + minimal English fallback.
_ACK_PHRASES = (
    "versionen von",
    "fundorte sind",
    "ich verwende hier die datei",
    "found multiple versions",
    "other locations are",
)


def _iter_tool_texts(tool_results: Iterable[Any]) -> Iterable[str]:
    """Yield string payloads from heterogeneous tool_results entries."""
    if not tool_results:
        return
    for item in tool_results:
        if item is None:
            continue
        if isinstance(item, str):
            yield item
            continue
        if isinstance(item, dict):
            for key in ("content", "text", "output", "result"):
                val = item.get(key)
                if isinstance(val, str):
                    yield val
                elif isinstance(val, dict):
                    try:
                        yield json.dumps(val, ensure_ascii=False)
                    except Exception:
                        yield str(val)
            data = item.get("data")
            if isinstance(data, dict):
                for key in ("content", "text"):
                    val = data.get(key)
                    if isinstance(val, str):
                        yield val
            continue
        # Pydantic / dataclass-ish
        for attr in ("content", "text", "output"):
            val = getattr(item, attr, None)
            if isinstance(val, str):
                yield val
        data = getattr(item, "data", None)
        if isinstance(data, dict):
            for key in ("content", "text"):
                val = data.get(key)
                if isinstance(val, str):
                    yield val


def tool_output_contains_warning(tool_results: Iterable[Any]) -> bool:
    """Return True if any tool output carried the ambiguity warning."""
    for text in _iter_tool_texts(tool_results):
        if WARNING_MARKER in text:
            return True
    return False


def model_acknowledged_warning(final_text: str) -> bool:
    """Return True if the assistant final_text contains a warning acknowledgement."""
    if not final_text:
        return False
    lowered = final_text.lower()
    # Must include *at least one* acknowledgement phrase AND the word "hinweis" / "note".
    has_ack = any(phrase in lowered for phrase in _ACK_PHRASES)
    has_label = ("hinweis" in lowered) or ("note" in lowered)
    return has_ack and has_label


def did_model_ignore_warning(
    tool_results: Iterable[Any],
    final_text: str,
) -> bool:
    """
    Returns True if the tool output carried a SYSTEM-WARNHINWEIS but the
    assistant final_text does not acknowledge it. In that case the caller
    should set ``skip_fact_extraction = True`` to prevent hallucinated
    facts from polluting memory.
    """
    if not tool_output_contains_warning(tool_results):
        return False
    if model_acknowledged_warning(final_text):
        return False
    logger.warning(
        "[WARNING-GUARD] SYSTEM-WARNHINWEIS was present in tool output but the "
        "assistant response did NOT acknowledge ambiguity. Fact extraction blocked."
    )
    return True


__all__: List[str] = [
    "WARNING_MARKER",
    "did_model_ignore_warning",
    "model_acknowledged_warning",
    "tool_output_contains_warning",
]
