"""
In-memory account-choice guard for chat mail actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PendingMailAccountChoice:
    action: str  # "send" | "reply" | "list_latest"
    accounts: list[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)


_PENDING_BY_CHAT: Dict[int, PendingMailAccountChoice] = {}


def set_pending_account_choice(chat_id: int, pending: PendingMailAccountChoice) -> None:
    _PENDING_BY_CHAT[int(chat_id)] = pending


def get_pending_account_choice(chat_id: int) -> Optional[PendingMailAccountChoice]:
    return _PENDING_BY_CHAT.get(int(chat_id))


def pop_pending_account_choice(chat_id: int) -> Optional[PendingMailAccountChoice]:
    return _PENDING_BY_CHAT.pop(int(chat_id), None)

