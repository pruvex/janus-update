from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.services.context.context_counter import estimate_messages_tokens
from backend.utils.config_loader import load_model_catalog

ContextStatus = Literal["green", "yellow", "orange", "red", "overflow"]

PROVIDER_DEFAULTS: dict[str, tuple[int, int]] = {
    "openai": (128000, 16384),
    "gemini": (1000000, 65536),
    "ollama": (8192, 2048),
    "unknown": (4096, 1024),
}


class ModelContextInfo(BaseModel):
    provider: str = "unknown"
    model: str
    max_context_tokens: int
    output_reserve: int
    effective_input_limit: int
    source: str = "fallback"


class ContextStateOutput(BaseModel):
    chat_id: str | None = None
    model: str
    provider: str = "unknown"
    total_tokens: int
    max_context_tokens: int
    output_reserve: int
    effective_input_limit: int
    usage_ratio: float
    usage_percent: float
    status: ContextStatus
    remaining_tokens: int
    warning: str | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    token_method: str = "heuristic_chars_per_token_v1"


def _safe_positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else fallback
    except Exception:
        return fallback


def resolve_model_context(model: str, provider: str | None = None) -> ModelContextInfo:
    model_id = str(model or "").strip()
    requested_provider = str(provider or "unknown").strip().lower() or "unknown"
    fallback_max, fallback_reserve = PROVIDER_DEFAULTS.get(requested_provider, PROVIDER_DEFAULTS["unknown"])
    source = "fallback"

    try:
        catalog = load_model_catalog()
        entry = catalog.get(model_id) if isinstance(catalog, dict) else None
        if isinstance(entry, dict):
            requested_provider = str(entry.get("provider") or requested_provider or "unknown").lower()
            fallback_max, fallback_reserve = PROVIDER_DEFAULTS.get(requested_provider, PROVIDER_DEFAULTS["unknown"])
            max_context = _safe_positive_int(entry.get("max_context_tokens") or entry.get("context_window"), fallback_max)
            output_reserve = _safe_positive_int(entry.get("output_reserve"), fallback_reserve)
            source = "model_catalog" if (entry.get("max_context_tokens") or entry.get("context_window")) else "provider_fallback"
        else:
            max_context = fallback_max
            output_reserve = fallback_reserve
    except Exception:
        max_context = fallback_max
        output_reserve = fallback_reserve

    if output_reserve >= max_context:
        output_reserve = max(1, max_context // 4)
    effective_input_limit = max(1, max_context - output_reserve)
    return ModelContextInfo(
        provider=requested_provider,
        model=model_id,
        max_context_tokens=max_context,
        output_reserve=output_reserve,
        effective_input_limit=effective_input_limit,
        source=source,
    )


def _status_for_ratio(ratio: float) -> ContextStatus:
    if ratio > 1.0:
        return "overflow"
    if ratio >= 0.85:
        return "red"
    if ratio >= 0.70:
        return "orange"
    if ratio >= 0.50:
        return "yellow"
    return "green"


def _warning_for_status(status: ContextStatus, model: str) -> str | None:
    if status == "overflow":
        return f"Das Modell {model} hat zu wenig effektiven Kontext für diesen Chat. Antworten können gekürzt oder fehlerhaft werden."
    if status == "red":
        return f"Der Kontext für {model} ist kritisch voll. Qualität kann deutlich sinken."
    if status == "orange":
        return f"Der Kontext für {model} wird voll. Eine spätere Chat-Komprimierung kann sinnvoll sein."
    if status == "yellow":
        return f"Der Kontext für {model} ist zur Hälfte belegt. Noch kein Eingriff nötig."
    return None


def _actions_for_status(status: ContextStatus) -> list[str]:
    if status in {"red", "overflow"}:
        return ["larger_model", "compress_chat", "new_chat", "send_anyway"]
    if status == "orange":
        return ["compress_chat", "larger_model"]
    return []


def calculate_context_state(
    *,
    chat_id: str | int | None,
    model: str,
    messages: list[Any] | None,
    provider: str | None = None,
) -> ContextStateOutput:
    context_info = resolve_model_context(model=model, provider=provider)
    total_tokens = estimate_messages_tokens(messages or [])
    ratio = total_tokens / context_info.effective_input_limit if context_info.effective_input_limit else 0.0
    status = _status_for_ratio(ratio)
    remaining = context_info.effective_input_limit - total_tokens
    return ContextStateOutput(
        chat_id=str(chat_id) if chat_id is not None else None,
        model=context_info.model,
        provider=context_info.provider,
        total_tokens=total_tokens,
        max_context_tokens=context_info.max_context_tokens,
        output_reserve=context_info.output_reserve,
        effective_input_limit=context_info.effective_input_limit,
        usage_ratio=round(ratio, 6),
        usage_percent=round(ratio * 100, 1),
        status=status,
        remaining_tokens=remaining,
        warning=_warning_for_status(status, context_info.model),
        recommended_actions=_actions_for_status(status),
    )
