"""
BYOK / provider-silo context for LLM calls.

While a chat turn runs with a concrete cloud provider (openai or gemini), any
``call_llm`` that targets the *other* cloud family is blocked. Ollama sessions do
not enforce this rule so local chats can still invoke optional cloud helpers.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar, Token
from typing import Optional

logger = logging.getLogger("janus_backend")

_active_llm_silo: ContextVar[Optional[str]] = ContextVar("janus_active_llm_silo", default=None)


def normalize_llm_silo_provider(provider: Optional[str]) -> Optional[str]:
    """Normalize UI/API provider keys to openai | gemini | ollama | None."""
    raw = str(provider or "").strip().lower()
    if not raw:
        return None
    if raw in ("google",):
        return "gemini"
    if raw in ("openai", "gemini", "ollama"):
        return raw
    return None


def get_active_llm_silo() -> Optional[str]:
    return _active_llm_silo.get()


def push_active_llm_silo(provider: Optional[str]) -> Token:
    """Returns a ContextVar token for :func:`reset_active_llm_silo`."""
    return _active_llm_silo.set(normalize_llm_silo_provider(provider))


def reset_active_llm_silo(token: Token) -> None:
    _active_llm_silo.reset(token)
