from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER_RE = re.compile(r"^\s*\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}\s*$")


class PlaceholderResolutionError(ValueError):
    """Raised when a bounded routine placeholder cannot be resolved."""


def resolve_routine_step_args(
    args: dict[str, Any],
    *,
    memory_context: dict[str, Any] | None = None,
    arg_bindings: dict[str, str] | None = None,
) -> dict[str, Any]:
    context = memory_context or {}
    bindings = arg_bindings or {}
    return {
        key: _resolve_value(
            value,
            memory_context=context,
            arg_key=str(key),
            arg_bindings=bindings,
        )
        for key, value in dict(args or {}).items()
    }


def _resolve_value(
    value: Any,
    *,
    memory_context: dict[str, Any],
    arg_key: str,
    arg_bindings: dict[str, str],
) -> Any:
    if isinstance(value, dict):
        return {
            key: _resolve_value(
                nested,
                memory_context=memory_context,
                arg_key=str(key),
                arg_bindings=arg_bindings,
            )
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [
            _resolve_value(
                nested,
                memory_context=memory_context,
                arg_key=arg_key,
                arg_bindings=arg_bindings,
            )
            for nested in value
        ]
    if not isinstance(value, str):
        return value

    match = _PLACEHOLDER_RE.match(value)
    if match:
        placeholder_key = str(match.group(1) or "").strip()
        return resolve_placeholder_value(
            placeholder_key,
            memory_context=memory_context,
            arg_key=arg_key,
            arg_bindings=arg_bindings,
        )

    binding = arg_bindings.get(arg_key)
    if binding and not str(value).strip():
        return _resolve_binding(binding, memory_context)

    return value


def resolve_placeholder_value(
    placeholder_key: str,
    *,
    memory_context: dict[str, Any] | None = None,
    arg_key: str | None = None,
    arg_bindings: dict[str, str] | None = None,
) -> Any:
    context = memory_context or {}
    bindings = arg_bindings or {}
    normalized_key = str(placeholder_key or "").strip()
    if not normalized_key:
        raise PlaceholderResolutionError("placeholder key must not be blank")

    resolved = _lookup_context_value(context, normalized_key)
    if resolved is not _MISSING:
        return resolved

    binding = bindings.get(str(arg_key or "").strip()) if arg_key else None
    if binding:
        resolved = _resolve_binding(binding, context)
        if resolved is not _MISSING:
            return resolved

    raise PlaceholderResolutionError(f"unresolved placeholder: {normalized_key}")


def _resolve_binding(binding: str, memory_context: dict[str, Any]) -> Any:
    normalized = str(binding or "").strip()
    if not normalized:
        return _MISSING
    if normalized.startswith("memory:"):
        normalized = normalized.split(":", 1)[1].strip()
    return _lookup_context_value(memory_context, normalized)


def _lookup_context_value(memory_context: dict[str, Any], key: str) -> Any:
    if key in memory_context:
        return memory_context[key]

    current: Any = memory_context
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        return _MISSING
    return current


class _MissingValue:
    pass


_MISSING = _MissingValue()
