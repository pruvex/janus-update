"""TASK-067: In-memory pending calendar mutation proposals (per chat).

Holds MutationProposal payloads until the user confirms (Ja) or rejects (Nein).
Not durable across server restarts — intentional for MVP guard layer.
"""

from __future__ import annotations

import logging
import re
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

if TYPE_CHECKING:
    from backend.data.schemas import MutationProposal


def tool_args_from_proposal(proposal: "MutationProposal") -> Dict[str, Any]:
    """Kwargs für ``find_and_update_calendar_event`` (ohne Bypass-Flag — kommt über Executor-Context)."""
    args = dict(proposal.proposed_changes or {})
    eid = str(proposal.event_id or "").strip()
    if eid:
        args["event_id"] = eid
    if not str(args.get("event_title_query") or "").strip():
        title = proposal.original_event.get("summary")
        args["event_title_query"] = str(title or "").strip() or "Termin"
    return args


def build_confirmation_prompt_message(proposal: "MutationProposal") -> str:
    """User-facing deutsch — TASK-067 Guided Assistant."""
    orig = proposal.original_event or {}
    title = str(orig.get("summary") or "Termin")
    pch = proposal.proposed_changes or {}
    fragments: List[str] = []

    if bool(pch.get("cancel_event")):
        fragments.append("absagen/löschen")
    if pch.get("new_start_time"):
        fragments.append(f"neuer Beginn: {pch['new_start_time']}")
    if pch.get("new_end_time"):
        fragments.append(f"neues Ende: {pch['new_end_time']}")
    if pch.get("new_summary"):
        fragments.append(f"neuer Titel: {pch['new_summary']}")
    if pch.get("new_location"):
        fragments.append(f"neuer Ort: {pch['new_location']}")
    if pch.get("new_description"):
        desc_preview = str(pch["new_description"])[:160]
        if len(str(pch["new_description"])) > 160:
            desc_preview += "…"
        fragments.append(f"Beschreibung ergänzt/geändert: {desc_preview}")

    summary_line = "; ".join(fragments) if fragments else "(Details siehe Daten)"
    return (
        f"Janus: Ich habe den Termin **{title}** wie folgt vorgemerkt: {summary_line}.\n\n"
        f"Soll ich die Änderung **final speichern**? Antworte mit **Ja** zum Bestätigen "
        f"oder **Nein** zum Abbrechen."
    )

logger = logging.getLogger("janus_backend")

_lock = threading.RLock()

# chat_id → latest pending proposal (exactly one slot per chat)
_pending_by_chat: Dict[int, "MutationProposal"] = {}


def set_pending_mutation_proposal(chat_id: int, proposal: "MutationProposal") -> None:
    with _lock:
        _pending_by_chat[int(chat_id)] = proposal


def get_pending_mutation_proposal(chat_id: Optional[int]) -> Optional["MutationProposal"]:
    if chat_id is None:
        return None
    with _lock:
        return _pending_by_chat.get(int(chat_id))


def pop_pending_mutation_proposal(chat_id: Optional[int]) -> Optional["MutationProposal"]:
    if chat_id is None:
        return None
    with _lock:
        return _pending_by_chat.pop(int(chat_id), None)


def clear_pending_mutation_proposal(chat_id: Optional[int]) -> None:
    if chat_id is None:
        return
    with _lock:
        _pending_by_chat.pop(int(chat_id), None)


def pending_count_for_tests() -> int:
    """Test helper: number of chats with a pending proposal."""
    with _lock:
        return len(_pending_by_chat)


_CONFIRM_RE = re.compile(
    r"^(ja|jawohl|jap|okay|ok|yes|yep|bestätige|bestaetige|genau|stimmt|korrekt|"
    r"mach\s+so|mach\s+das|richtig|passt)(\b|[\s,!?.]|$)",
    re.IGNORECASE,
)
_REJECT_RE = re.compile(
    r"^(nein|nö|no|abbrechen|stop|verwerfen|lieber\s+nicht|nicht\s+speichern)(\b|[\s,!?.]|$)",
    re.IGNORECASE,
)


def classify_confirmation_reply(user_text: str) -> Optional[Literal["confirm", "reject"]]:
    """Interpret a short Ja/Nein style reply while a proposal is pending.

    Returns None if the message is not clearly confirmation or rejection
    (caller should remind the user or continue normal orchestration).
    """
    raw = str(user_text or "").strip().lower()
    if not raw:
        return None
    # Prefer reject if both could match unlikely edge cases.
    if _REJECT_RE.match(raw):
        return "reject"
    if _CONFIRM_RE.match(raw) and len(raw) <= 80:
        return "confirm"
    return None


def log_proposal_created(proposal_id: str, *, chat_id: int, event_id: str) -> None:
    logger.info(
        "[MUTATION-GUARD] Proposal created: proposal_id=%s chat_id=%s event_id=%r",
        proposal_id,
        chat_id,
        event_id,
    )


def log_confirmation_received(proposal_id: str, *, chat_id: int) -> None:
    logger.info(
        "[MUTATION-GUARD] Confirmation received for proposal_id=%s chat_id=%s",
        proposal_id,
        chat_id,
    )


def log_rejection_received(proposal_id: str, *, chat_id: int) -> None:
    logger.info(
        "[MUTATION-GUARD] Rejection received for proposal_id=%s chat_id=%s",
        proposal_id,
        chat_id,
    )
