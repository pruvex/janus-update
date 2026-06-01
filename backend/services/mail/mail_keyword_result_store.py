"""
In-memory store for numbered follow-up selections on mail keyword result lists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class PendingMailKeywordSelection:
    account: str = ""
    provider: str = ""
    category: str = ""
    hits: list[dict] = field(default_factory=list)


_PENDING_BY_CHAT: Dict[int, PendingMailKeywordSelection] = {}


def set_pending_keyword_selection(chat_id: int, pending: PendingMailKeywordSelection) -> None:
    _PENDING_BY_CHAT[int(chat_id)] = pending


def get_pending_keyword_selection(chat_id: int) -> Optional[PendingMailKeywordSelection]:
    return _PENDING_BY_CHAT.get(int(chat_id))


def pop_pending_keyword_selection(chat_id: int) -> Optional[PendingMailKeywordSelection]:
    return _PENDING_BY_CHAT.pop(int(chat_id), None)
