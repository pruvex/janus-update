"""
Task 013: Memory Identity Preload
Guarantees user name recall via the fixed identity slot:
    canonical_key = "user:physis:heisst:name"  (priority 0.95)

Thread-safe: memory_cache uses its own threading.Lock; DB access is
per-request Session (SQLAlchemy per-request thread model).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from backend.services.memory_budget import MemorySlot

logger = logging.getLogger("janus_backend")

IDENTITY_CANONICAL_KEY = "user:physis:heisst:name"
IDENTITY_PRIORITY      = 0.95
_IDENTITY_TOKENS       = 14   # "User heißt <name>" ≈ 14 tokens worst-case

# Stop-words that should never appear inside a stored name
_NAME_STOP_WORDS: frozenset = frozenset({
    "und", "and", "oder", "but", "also", "als", "mag", "bin", "ist",
    "sich", "mir", "mich", "wir", "sie",
})


def _normalize_name(raw: str) -> Optional[str]:
    """
    Defensive name normalization (Task 016).

    1. Strip whitespace and trailing punctuation.
    2. Enforce Title Case.
    3. If result is > 2 words, truncate to the first word only
       (guards against dirty-data remnants that slipped through the extractor).

    Returns None for empty or trivially invalid values.
    """
    raw = str(raw or "").strip().rstrip(".,!?; ")
    if not raw:
        return None
    # Title-case every word
    candidate = raw.title()
    words = candidate.split()
    if not words:
        return None
    # Reject if first word is a known stop-word (case-insensitive)
    if words[0].lower() in _NAME_STOP_WORDS:
        return None
    # Truncate dirty multi-word remnants (> 2 words → keep only first)
    if len(words) > 2:
        candidate = words[0]
    return candidate or None


@dataclass
class IdentitySlot:
    """Resolved user identity for one request cycle."""
    name: Optional[str]                        # "Captain Janus" | None
    canonical_key: str    = IDENTITY_CANONICAL_KEY
    priority: float       = IDENTITY_PRIORITY
    is_verified: bool     = False
    memory_id: Optional[int] = None
    source: str           = "fallback"         # "cache" | "db" | "fallback"
    created_at: Optional[datetime] = None
    chat_id: Optional[int] = None
    chat_title: str       = ""


def load_identity_slot(db: Session) -> IdentitySlot:
    """
    Resolves the user identity slot.

    1. DB lookup for canonical_key = 'user:physis:heisst:name'.
    2. Warms the RAM cache as a side-effect (memory_cache.get).
    3. Emits [IDENTITY PRELOAD] on hit, [IDENTITY MISSING] on miss.

    Thread-safe: memory_cache has an internal threading.Lock; the
    per-request SQLAlchemy Session is already isolated.
    """
    from backend.data import models
    from backend.services.memory_cache import memory_cache

    record = (
        db.query(models.Memory)
        .filter(models.Memory.canonical_key == IDENTITY_CANONICAL_KEY)
        .order_by(models.Memory.priority.desc())
        .first()
    )

    if record is None:
        logger.info("[IDENTITY MISSING] No identity slot in DB — user name unknown")
        return IdentitySlot(name=None, source="fallback")

    # Warm the RAM cache; emits [CACHE HIT] or [CACHE MISS] inside memory_cache
    cached = memory_cache.get(record.id)
    source = "cache" if cached is not None else "db"

    # snippet is stored as json.dumps(fact_object) — parse it to get object_value
    import json as _json, re as _re
    raw_snippet = getattr(record, "snippet", "") or ""
    name: Optional[str] = None
    try:
        fact_obj = _json.loads(raw_snippet)
        raw_name = (
            fact_obj.get("object_value")
            or fact_obj.get("fact", "")
        )
        # If fact = "User heißt Rolf" → extract "Rolf"
        _m = _re.search(r'hei(?:ß|ss)t\s+(.+)', str(raw_name), _re.IGNORECASE)
        if _m:
            raw_name = _m.group(1).strip()
        name = _normalize_name(str(raw_name))
    except (_json.JSONDecodeError, TypeError, AttributeError):
        # Fallback: legacy plain-text snippet "Der Benutzer heißt Rolf"
        _m2 = _re.search(r'hei(?:ß|ss)t\s+(.+)', raw_snippet, _re.IGNORECASE)
        if _m2:
            name = _normalize_name(_m2.group(1))

    tags_raw = getattr(record, "tags", "") or ""
    is_verified = "verified" in str(tags_raw).lower()

    # ── Temporal metadata for episodic recall ────────────────────────────
    _created_at = getattr(record, "created_at", None)
    _chat_id = getattr(record, "chat_id", None)
    _chat_title = ""
    _GHOST_CHAT_THRESHOLD = 9999
    if _chat_id is not None and _chat_id < _GHOST_CHAT_THRESHOLD:
        try:
            _chat_row = db.query(models.Chat.title).filter(models.Chat.id == _chat_id).first()
            if _chat_row and _chat_row.title:
                _chat_title = _chat_row.title
        except Exception:
            pass
    if not _chat_title:
        _chat_title = "Globales Gedächtnis"
    # ──────────────────────────────────────────────────────────────────────

    logger.info(
        "[IDENTITY PRELOAD] name=%r priority=%.2f source=%s memory_id=%s chat='%s'",
        name,
        float(getattr(record, "priority", 0) or 0),
        source,
        record.id,
        _chat_title,
    )
    return IdentitySlot(
        name=name,
        priority=float(getattr(record, "priority", IDENTITY_PRIORITY) or IDENTITY_PRIORITY),
        is_verified=is_verified,
        memory_id=record.id,
        source=source,
        created_at=_created_at,
        chat_id=_chat_id,
        chat_title=_chat_title,
    )


def ensure_identity_in_slots(
    slots: List["MemorySlot"],
    identity: IdentitySlot,
) -> List["MemorySlot"]:
    """
    Guarantees the identity MemorySlot is at position 0 of the list.

    BUDGET-EXEMPT: must be called AFTER select_slots_by_budget so the
    identity slot is never subject to token eviction.
    Deduplicates if the slot is already present (by memory_id).
    No-op when identity.name is None.
    """
    if not identity.name:
        return slots

    from backend.services.memory_budget import MemorySlot, format_temporal_stamp

    deduped = [
        s for s in slots
        if not (
            (identity.memory_id and getattr(s, "memory_id", None) == identity.memory_id)
            or IDENTITY_CANONICAL_KEY in getattr(s, "text", "")
        )
    ]

    identity_ms = MemorySlot(
        text=f"User heißt {identity.name}",
        tokens=_IDENTITY_TOKENS,
        tier="core_identity",
        priority=identity.priority,
        memory_id=identity.memory_id or 0,
        tags=["identity", "verified"] if identity.is_verified else ["identity"],
        timestamp=format_temporal_stamp(identity.created_at),
        chat_title=identity.chat_title or "Globales Gedächtnis",
    )
    logger.debug(
        "[IDENTITY SLOT] Injected budget-exempt slot: name=%r tier=core_identity ts='%s' chat='%s'",
        identity.name, identity_ms.timestamp, identity_ms.chat_title,
    )
    return [identity_ms] + deduped


