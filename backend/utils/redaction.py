"""Shared privacy redaction helpers for logs, telemetry, and audit artifacts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any


REDACTION_TEXT = "[REDACTED]"

_SENSITIVE_KEY_RE = re.compile(
    r"^(?:authorization|cookie|set-cookie|x-api-key|api[-_]?key|token|access[-_]?token|"
    r"refresh[-_]?token|id[-_]?token|secret|client[-_]?secret|password|passwd|webhook|"
    r"webhook[-_]?url|provider[-_]?key)$",
    re.IGNORECASE,
)

_TEXT_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}\b", re.IGNORECASE),
    re.compile(r"\b(?:Authorization|Cookie|Set-Cookie)\s*:\s*[^\r\n;]+", re.IGNORECASE),
    re.compile(r"\bSECRET-[A-Za-z0-9._~+/=-]+\b", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),
    re.compile(r"\bsb_(?:publishable|secret)_[A-Za-z0-9_\-]{12,}\b", re.IGNORECASE),
    re.compile(r"https://discord(?:app)?\.com/api/webhooks/[^\s`\"')]+", re.IGNORECASE),
    re.compile(
        r"\b(?:api[-_ ]?key|token|secret|password|passwd|client[-_ ]?secret)\s*[:=]\s*"
        r"[A-Za-z0-9._~+/=\-]{6,}",
        re.IGNORECASE,
    ),
)


def _as_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def redact_sensitive_text(value: str) -> str:
    """Redact common credential and token shapes from free-form text."""

    text = _as_text(value)
    for pattern in _TEXT_PATTERNS:
        text = pattern.sub(REDACTION_TEXT, text)
    return text


def redact_sensitive_value(value: Any) -> Any:
    """Redact nested values while preserving useful non-sensitive structure."""

    if isinstance(value, Mapping):
        redacted = {}
        for key, item in value.items():
            key_str = _as_text(key)
            if _SENSITIVE_KEY_RE.search(key_str):
                redacted[key] = REDACTION_TEXT
            else:
                redacted[key] = redact_sensitive_value(item)
        return redacted
    if isinstance(value, tuple):
        if len(value) == 2 and _SENSITIVE_KEY_RE.search(_as_text(value[0])):
            return (value[0], REDACTION_TEXT)
        return tuple(redact_sensitive_value(item) for item in value)
    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]
    if isinstance(value, set):
        return {redact_sensitive_value(item) for item in value}
    if isinstance(value, bytes):
        return redact_sensitive_text(value)
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def redacted_json(value: Any) -> str:
    """Serialize a value after redaction, falling back to a redacted string."""

    redacted = redact_sensitive_value(value)
    try:
        return json.dumps(redacted, ensure_ascii=False, default=str)
    except Exception:
        return redact_sensitive_text(str(redacted))
