"""Contextual Entity Resolver — TASK-065.

Resolves an imprecise user query (e.g. "Fitnesstudio") to a specific calendar
event from the in-memory calendar_snapshot using a multi-step fuzzy cascade.

Pipeline stages:
  N  — Normalization + short-query guard (resolver-specific tokenizer, min 2 chars)
  T  — Temporal Context Layer: extracts "morgen", weekday names, etc. and resolves
       identical-title ambiguity via date alignment BEFORE scoring fires.
  S  — Adaptive scoring: TSR + PR with topology-aware weighting + location bonus
  R  — Resolution: classify status, assign dispatcher_hint

Contract:
  • resolved_event is populated only when status == "RESOLVED".
  • candidates always present (empty list for NOT_FOUND).
  • Staleness of event_id vs. live API is a CALLER concern, not this module.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

from rapidfuzz import fuzz as rfuzz

from backend.services.orchestrator.intent_engine import _normalize_text

logger = logging.getLogger("janus_backend")

OperationType = Literal["READ", "MUTATION"]
DispatcherHint = Literal["PROCEED", "FALLBACK_TO_LIST", "CLARIFY_USER"]
ResolutionStatus = Literal["RESOLVED", "AMBIGUOUS", "WEAK_MATCH", "NOT_FOUND"]

# ─────────────────────────────────────────────────────────────────────────────
# Thresholds (exact — do not adjust without updating design docs)
# ─────────────────────────────────────────────────────────────────────────────
_TIER_EXACT: float = 108.0
_TIER_HIGH: float = 82.0
_TIER_MEDIUM: float = 65.0
_TIER_WEAK: float = 45.0
_DELTA_RESOLVED_MIN: float = 15.0    # Δ_top2 required to promote to RESOLVED
_LOC_FLOOR: float = 62.0             # minimum location TSR to add bonus
_LOC_BONUS_MULTIPLIER: float = 0.15  # normal location bonus weight
_LOC_PENALTY_MULTIPLIER: float = 0.08  # reduced weight when S_title < 60 (location-dominant)
_LOC_TITLE_WEAKNESS: float = 60.0   # S_title below this → apply location penalty
_LOCATION_CHARS: int = 35            # truncate location to avoid full-address pollution
_COMPOUND_LEN: int = 8               # single token longer than this is treated as compound

# Day-name → weekday index (Monday=0)
_WEEKDAY_MAP: Dict[str, int] = {
    "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3,
    "freitag": 4, "samstag": 5, "sonntag": 6,
}

_TEMPORAL_RE = re.compile(
    r"\b(heute|morgen|übermorgen|uebermorgen|"
    r"montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b",
    re.IGNORECASE,
)

# Deictic / anaphoric expressions that signal "I mean the thing we just talked about"
# Includes personal pronouns, demonstratives, and implicit reference phrases.
_DEICTIC_RE = re.compile(
    r"\b(da(?:rauf|bei|zu|für|hin|nach|von)?|dort|"
    r"den|dem|das|die|ihn|ihm|ihr|es|sie|"
    r"diesen?|diesem|dieser|jenen?|jenem|jener|"
    r"dazu|dabei|daf[uü]r|dort(?:hin)?|"
    r"den termin|diesen termin|den appointment|"
    r"ihn|mitzubringen|mitbringen|mitnehmen)\b",
    re.IGNORECASE,
)


def _has_deictic_reference(text: str) -> bool:
    """Return True if the raw query contains a deictic / anaphoric reference.

    Deictic words signal that the user is pointing to something previously
    discussed, not naming a calendar event explicitly.  Examples:
    - "da Handtuch nicht vergessen"           → "da"
    - "den bitte absagen"                     → "den"
    - "Handtuch mitzubringen"                 → "mitzubringen" (implicit carry-along)
    - "ihn auf 15 Uhr verschieben"            → "ihn"
    """
    return bool(_DEICTIC_RE.search(text))


# ─────────────────────────────────────────────────────────────────────────────
# Stage N helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolver_tokenize(text_norm: str) -> List[str]:
    """Resolver-specific tokenizer.

    Rules differ deliberately from ``_calendar_snapshot_anchor_tokens``:
    - Minimum token length: 2 (keeps brand names like "o2", "vw").
    - Rejects only purely-numeric tokens ("123" dropped, "3m" kept).
    - Does NOT apply _CALENDAR_SNAPSHOT_STOPWORDS — rapidfuzz handles common
      words gracefully; stripping them would destroy temporal/context signals.
    """
    tokens: List[str] = []
    for raw in text_norm.split():
        w = raw.strip("-_.").strip()
        if len(w) < 2 or w.isdigit():
            continue
        tokens.append(w)
    return tokens


def _expand_hyphens(text_norm: str) -> str:
    """Return a hyphen-expanded variant: 'fitness-studio' → 'fitness studio'."""
    return text_norm.replace("-", " ")


# ─────────────────────────────────────────────────────────────────────────────
# Stage T — Temporal Context Layer
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_temporal_anchor(anchor: str, today: date) -> Optional[date]:
    """Map a lowercase temporal keyword to an absolute date."""
    if anchor == "heute":
        return today
    if anchor == "morgen":
        return today + timedelta(days=1)
    if anchor in ("übermorgen", "uebermorgen"):
        return today + timedelta(days=2)
    wd = _WEEKDAY_MAP.get(anchor)
    if wd is not None:
        days_ahead = (wd - today.weekday()) % 7 or 7  # always next occurrence
        return today + timedelta(days=days_ahead)
    return None


def _extract_temporal_date(query_raw: str, today: date) -> Optional[date]:
    """Return the first resolvable temporal date found in the raw query."""
    for m in _TEMPORAL_RE.finditer(query_raw.lower()):
        resolved = _resolve_temporal_anchor(m.group(1), today)
        if resolved is not None:
            return resolved
    return None


def _event_start_date(event: Dict[str, Any]) -> Optional[date]:
    """Parse the event's start field to a plain date (timezone-unaware)."""
    raw = event.get("start")
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Stage S — Scoring
# ─────────────────────────────────────────────────────────────────────────────

def _score_pair(q_norm: str, target_norm: str) -> tuple[float, float]:
    """Return (TSR, PR) for a query/target pair, taking the max across the
    hyphen-expanded variant to handle 'fitness-studio' ↔ 'fitnessstudio'."""
    tsr = rfuzz.token_set_ratio(q_norm, target_norm)
    pr = rfuzz.partial_ratio(q_norm, target_norm)
    # Hyphen-expanded variant
    q_exp = _expand_hyphens(q_norm)
    t_exp = _expand_hyphens(target_norm)
    if q_exp != q_norm or t_exp != target_norm:
        tsr = max(tsr, rfuzz.token_set_ratio(q_exp, t_exp))
        pr = max(pr, rfuzz.partial_ratio(q_exp, t_exp))
    return float(tsr), float(pr)


def _s_title(tsr: float, pr: float, title_norm: str) -> float:
    """Compute weighted S_title with adaptive weights based on title topology.

    Single-token compound titles (e.g. "zahnarzttermin") rely almost entirely
    on partial_ratio because token_set_ratio cannot find intra-token similarity.
    Multi-word titles use TSR as the dominant signal.
    """
    tokens = _resolver_tokenize(title_norm)
    is_single_compound = len(tokens) == 1 and len(title_norm) > _COMPOUND_LEN
    if is_single_compound:
        return 0.25 * tsr + 0.75 * pr
    return 0.65 * tsr + 0.35 * pr


def _s_final(s_title: float, loc_norm: str, q_norm: str) -> tuple[float, float]:
    """Return (S_final, loc_contribution).

    Location is additive-only, capped at _LOCATION_CHARS characters, and
    penalised when the title signal is too weak (location-dominant query).
    """
    loc_trimmed = loc_norm[:_LOCATION_CHARS]
    if not loc_trimmed:
        return s_title, 0.0

    loc_tsr = float(rfuzz.token_set_ratio(q_norm, loc_trimmed))
    if loc_tsr < _LOC_FLOOR:
        return s_title, 0.0

    if s_title < _LOC_TITLE_WEAKNESS:
        bonus = _LOC_PENALTY_MULTIPLIER * loc_tsr
    else:
        bonus = _LOC_BONUS_MULTIPLIER * loc_tsr

    return s_title + bonus, loc_tsr


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CandidateResult:
    rank: int
    event_id: str
    original_title: str
    start_time: str
    score_final: float
    score_tsr: float
    score_pr: float
    score_loc_bonus: float


@dataclass
class ResolutionResult:
    resolver_version: str = "1.0"
    query_raw: str = ""
    query_normalized: str = ""
    operation_type: OperationType = "READ"
    status: ResolutionStatus = "NOT_FOUND"
    dispatcher_hint: DispatcherHint = "CLARIFY_USER"
    low_confidence: bool = False
    resolved_event: Optional[CandidateResult] = None
    candidates: List[CandidateResult] = field(default_factory=list)
    delta_top2: float = 0.0
    snapshot_event_count: int = 0
    reason: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Context Fallback Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_event_mentions_from_context(
    messages: List[Dict[str, Any]],
    snapshot_events: List[Dict[str, Any]],
) -> List[str]:
    """Extract unique event IDs mentioned in recent messages.

    Looks for event mentions by matching message content against event titles
    from the snapshot. Returns a list of unique event IDs in chronological order.
    """
    if not messages or not snapshot_events:
        return []

    # Build title -> event_id mapping from snapshot
    title_to_ids: Dict[str, List[str]] = {}
    for ev in snapshot_events:
        ev_id = str(ev.get("id") or ev.get("event_id") or "")
        title = str(ev.get("title") or "")
        if ev_id and title:
            title_norm = _normalize_text(title)
            title_to_ids.setdefault(title_norm, []).append(ev_id)

    mentioned_ids: List[str] = []
    seen_ids = set()

    # Scan messages in reverse (most recent first)
    for msg in reversed(messages):
        content = str(msg.get("content") or "")
        if not content:
            continue

        content_norm = _normalize_text(content)

        # Check if any event title is mentioned in this message
        for title_norm, ev_ids in title_to_ids.items():
            if title_norm in content_norm:
                for ev_id in ev_ids:
                    if ev_id not in seen_ids:
                        mentioned_ids.append(ev_id)
                        seen_ids.add(ev_id)

    # Return in chronological order (reverse the reverse)
    return list(reversed(mentioned_ids))


# ─────────────────────────────────────────────────────────────────────────────
# Main resolver
# ─────────────────────────────────────────────────────────────────────────────

class ContextualEntityResolver:
    """Pure function — no I/O, no side effects.  Thread-safe; instantiate once."""

    def resolve(
        self,
        query: str,
        snapshot: Any,
        operation_type: OperationType = "MUTATION",
        *,
        today: Optional[date] = None,
        recent_messages: Optional[List[Dict[str, Any]]] = None,
        is_calendar_mutation: bool = False,
        is_filesystem_intent: bool = False,
        full_user_text: Optional[str] = None,
    ) -> ResolutionResult:
        """Resolve *query* against the calendar *snapshot*.

        Args:
            query: Extracted mutation target (e.g. "Fitnesstudio", "Sport").
                   May be empty when the user phrased the request with only a
                   pronoun (e.g. "ihn absagen") — the deictic fallback handles
                   this case via *full_user_text*.
            snapshot: ``wf.calendar_snapshot`` dict with an ``"events"`` list.
            operation_type: "MUTATION" (conservative) or "READ" (permissive).
            today: Override today's date (for testing). Defaults to date.today().
            recent_messages: Clean chat history (no system prompt) for deictic
                             fallback — use ``orchestrator_context.history[-4:]``.
            is_calendar_mutation: True if orchestrator confirmed mutation intent.
            is_filesystem_intent: True if orchestrator confirmed filesystem intent (TASK-001: BACKLOG-004).
            full_user_text: The complete raw user message.  Used exclusively for
                            deictic detection; never scored against event titles.
        """
        today = today or date.today()

        # Canonical deictic text: prefer the full sentence over mutation_target,
        # because deictic words ("da", "ihn", "den") are stripped or missed by
        # _extract_mutation_target and won't appear in *query*.
        _deictic_src = full_user_text or query

        result = ResolutionResult(
            query_raw=query,
            operation_type=operation_type,
        )

        # ── Stage N: Normalization ──────────────────────────────────────────
        q_norm = _normalize_text(query)
        result.query_normalized = q_norm

        # Short-query guard: no usable tokens AND very short string.
        # Exception: if the full user text contains a deictic reference the
        # guard is bypassed — the deictic fallback can still resolve the event
        # without needing a meaningful fuzzy query.
        q_tokens = _resolver_tokenize(q_norm)
        _full_text_has_deictic = _has_deictic_reference(_deictic_src)
        if not q_tokens and len(q_norm) < 3 and not _full_text_has_deictic:
            result.status = "NOT_FOUND"
            result.reason = "query_too_short"
            result.dispatcher_hint = "CLARIFY_USER"
            return result

        # ── Validate snapshot ───────────────────────────────────────────────
        events_raw: List[Dict[str, Any]] = []
        if isinstance(snapshot, dict):
            events_raw = snapshot.get("events") or []
        if not isinstance(events_raw, list):
            events_raw = []

        valid_events: List[Dict[str, Any]] = []
        for idx, ev in enumerate(events_raw):
            if not isinstance(ev, dict):
                logger.warning("[ENTITY-RESOLVER] snapshot event[%d] is not a dict — skipped", idx)
                continue
            if not ev.get("id") and not ev.get("event_id"):
                logger.warning("[ENTITY-RESOLVER] snapshot event[%d] missing id — skipped", idx)
                continue
            valid_events.append(ev)

        result.snapshot_event_count = len(valid_events)

        if not valid_events:
            result.status = "NOT_FOUND"
            result.reason = "empty_snapshot"
            # 💎 TASK-002: BACKLOG-004 - Filesystem-Intent Veto
            # Bei Filesystem-Intent nicht zu Calendar-List-Events zwingen
            if is_filesystem_intent:
                result.dispatcher_hint = "CLARIFY_USER"
            else:
                result.dispatcher_hint = "FALLBACK_TO_LIST"
            return result

        # ── Stage T: Temporal Context Layer ────────────────────────────────
        temporal_date = _extract_temporal_date(query, today)

        # Identical-title pre-check
        title_groups: Dict[str, List[Dict[str, Any]]] = {}
        for ev in valid_events:
            t_norm = _normalize_text(str(ev.get("title") or ""))
            title_groups.setdefault(t_norm, []).append(ev)

        # ── Stage S: Score all candidates ───────────────────────────────────
        scored: List[CandidateResult] = []
        for ev in valid_events:
            ev_id = str(ev.get("id") or ev.get("event_id") or "")
            title_raw = str(ev.get("title") or "")
            loc_raw = str(ev.get("location") or "")
            start_time = str(ev.get("start") or "")

            t_norm = _normalize_text(title_raw)
            l_norm = _normalize_text(loc_raw)

            if not t_norm:
                continue

            # Exact match short-circuit
            if q_norm == t_norm:
                scored.append(CandidateResult(
                    rank=0,
                    event_id=ev_id,
                    original_title=title_raw,
                    start_time=start_time,
                    score_final=110.0,
                    score_tsr=100.0,
                    score_pr=100.0,
                    score_loc_bonus=0.0,
                ))
                continue

            tsr, pr = _score_pair(q_norm, t_norm)
            st = _s_title(tsr, pr, t_norm)
            sf, loc_bonus = _s_final(st, l_norm, q_norm)

            if sf < _TIER_WEAK:
                continue  # discard noise

            scored.append(CandidateResult(
                rank=0,
                event_id=ev_id,
                original_title=title_raw,
                start_time=start_time,
                score_final=sf,
                score_tsr=tsr,
                score_pr=pr,
                score_loc_bonus=loc_bonus,
            ))

        # Sort descending, assign ranks
        scored.sort(key=lambda c: c.score_final, reverse=True)
        for i, c in enumerate(scored):
            c.rank = i + 1

        result.candidates = scored

        if not scored:
            result.status = "NOT_FOUND"
            result.reason = "below_threshold"
            result.dispatcher_hint = (
                "FALLBACK_TO_LIST" if operation_type == "READ" else "CLARIFY_USER"
            )
            # Fall through to the deictic context fallback (no early return here).
            # The block below may promote NOT_FOUND → RESOLVED when a deictic
            # reference and a single context event are both present.
        else:
            top = scored[0]
            second = scored[1] if len(scored) > 1 else None
            delta = (top.score_final - second.score_final) if second else top.score_final
            result.delta_top2 = round(delta, 2)

            # ── Identical-title gate + Temporal override ─────────────────────
            top_title_norm = _normalize_text(top.original_title)
            identical_group = title_groups.get(top_title_norm, [])
            has_identical_title_collision = len(identical_group) > 1

            if has_identical_title_collision:
                if temporal_date is not None:
                    # Attempt temporal resolution
                    aligned = [
                        ev for ev in identical_group
                        if _event_start_date(ev) == temporal_date
                    ]
                    if len(aligned) == 1:
                        # Temporal anchor resolves the collision
                        winner = aligned[0]
                        ev_id = str(winner.get("id") or winner.get("event_id") or "")
                        matching_candidate = next(
                            (c for c in scored if c.event_id == ev_id), None
                        )
                        if matching_candidate:
                            result.status = "RESOLVED"
                            result.reason = "identical_titles_resolved_by_temporal_anchor"
                            result.resolved_event = matching_candidate
                            result.dispatcher_hint = "PROCEED"
                            result.low_confidence = False
                            return result
                    # 0 or 2+ aligned — still ambiguous
                result.status = "AMBIGUOUS"
                result.reason = "identical_titles"
                result.dispatcher_hint = (
                    "PROCEED" if operation_type == "READ" else "FALLBACK_TO_LIST"
                )
                result.low_confidence = True
                return result

            # ── Classify by tier and delta ───────────────────────────────────
            above_medium = [c for c in scored if c.score_final >= _TIER_MEDIUM]

            if top.score_final >= _TIER_HIGH and delta > _DELTA_RESOLVED_MIN:
                result.status = "RESOLVED"
                result.reason = "single_high_confidence"
                result.resolved_event = top
                result.dispatcher_hint = "PROCEED"
                result.low_confidence = False

            elif top.score_final >= _TIER_MEDIUM and (len(above_medium) >= 2 or delta <= _DELTA_RESOLVED_MIN):
                result.status = "AMBIGUOUS"
                result.reason = "multiple_candidates" if len(above_medium) >= 2 else "delta_too_small"
                if operation_type == "MUTATION":
                    result.dispatcher_hint = "FALLBACK_TO_LIST"
                    result.low_confidence = False
                else:
                    # READ: sub-classify by confidence
                    is_strong = top.score_final >= _TIER_HIGH and delta > 10.0
                    result.dispatcher_hint = "PROCEED"
                    result.low_confidence = not is_strong

            elif top.score_final >= _TIER_WEAK:
                result.status = "WEAK_MATCH"
                result.reason = "below_threshold"
                if operation_type == "MUTATION":
                    # 💎 TASK-002: BACKLOG-004 - Filesystem-Intent Veto
                    # Wenn Filesystem-Intent erkannt wurde, nicht zu Calendar-List-Events zwingen
                    if is_filesystem_intent:
                        result.dispatcher_hint = "CLARIFY_USER"
                        result.low_confidence = False
                        logger.info(
                            "[ENTITY-RESOLVER] WEAK_MATCH skipped for filesystem intent: query=%r",
                            query[:100] + "..." if len(query) > 100 else query
                        )
                    else:
                        result.dispatcher_hint = "FALLBACK_TO_LIST"
                        result.low_confidence = False
                else:
                    result.dispatcher_hint = "PROCEED"
                    result.low_confidence = True

            else:
                result.status = "NOT_FOUND"
                result.reason = "below_threshold"
                result.dispatcher_hint = (
                    "FALLBACK_TO_LIST" if operation_type == "READ" else "CLARIFY_USER"
                )

        # ── Context Fallback: Deictic / Anaphoric References ─────────────────
        # Conditions to activate:
        #   • MUTATION operation only (READ already PROCEEDs with low_confidence)
        #   • Status is NOT_FOUND  OR  WEAK_MATCH (score too low for direct resolution)
        #   • is_calendar_mutation flag is set (orchestrator confirmed mutation intent)
        #   • Exactly one calendar event is mentioned in recent chat history
        #   • One of two implicit-reference signals is present:
        #     A) full_user_text (or query) contains a deictic word ("da", "ihn", …)
        #     B) mutation_target is a very short pronoun-like token (≤ 4 chars, 1 token)
        #        e.g. "ihn", "da", "den" when it survived extraction
        #
        # NOTE: _query_tokens_count <= 2 was deliberately NOT used as the gate —
        # a single-token compound like "Zahnarzttermin" (1 token, 14 chars) should
        # NOT trigger a context fallback just because the score was low.
        _is_unresolved = result.status in ("NOT_FOUND", "WEAK_MATCH")
        _query_tokens_count = len(_resolver_tokenize(q_norm))
        _is_short_pronoun = _query_tokens_count == 1 and len(q_norm) <= 4
        _is_implicit_ref = _full_text_has_deictic or _is_short_pronoun
        if (
            _is_unresolved
            and is_calendar_mutation
            and operation_type == "MUTATION"
            and recent_messages
            and _is_implicit_ref
        ):
            mentioned_ids = _extract_event_mentions_from_context(recent_messages, valid_events)
            if len(mentioned_ids) == 1:
                context_id = mentioned_ids[0]
                context_event = next(
                    (ev for ev in valid_events
                     if str(ev.get("id") or ev.get("event_id") or "") == context_id),
                    None,
                )
                if context_event:
                    ev_id = str(context_event.get("id") or context_event.get("event_id") or "")
                    title_raw = str(context_event.get("title") or "")
                    start_time = str(context_event.get("start") or "")
                    result.status = "RESOLVED"
                    result.reason = "deictic_context_fallback"
                    result.resolved_event = CandidateResult(
                        rank=1,
                        event_id=ev_id,
                        original_title=title_raw,
                        start_time=start_time,
                        score_final=75.0,  # Honest score — context inference, not fuzzy match
                        score_tsr=0.0,
                        score_pr=0.0,
                        score_loc_bonus=0.0,
                    )
                    result.dispatcher_hint = "PROCEED"
                    result.low_confidence = False
                    logger.info(
                        "[ENTITY-RESOLVER] Deictic fallback: resolved to context event %r "
                        "(deictic_in_src=%s, short_pronoun=%s, tokens=%d)",
                        title_raw,
                        _full_text_has_deictic,
                        _is_short_pronoun,
                        _query_tokens_count,
                    )
            elif len(mentioned_ids) > 1:
                logger.debug(
                    "[ENTITY-RESOLVER] Deictic fallback skipped: %d events in context (ambiguous)",
                    len(mentioned_ids),
                )

        return result
