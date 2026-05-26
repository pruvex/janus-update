"""Calendar snapshot mirror for memory-context injection (TASK-059 V1).

The live calendar remains the source of truth. This module stores a compact,
replaceable snapshot in the existing Memory table and renders a bounded prompt
block for chat turns that are calendar- or planning-related.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

import dateparser
from dateparser.search import search_dates
from sqlalchemy.orm import Session

import backend.data.models as models
from backend.services.memory.crud_service import compute_hash

logger = logging.getLogger("janus_backend.calendar_memory")

BERLIN_TZ = ZoneInfo("Europe/Berlin")
CALENDAR_SNAPSHOT_CATEGORY = "calendar_snapshot"
CALENDAR_SNAPSHOT_KEY = "calendar:snapshot:primary"
SNAPSHOT_VERSION = 1
SNAPSHOT_DAYS = 14
SNAPSHOT_MAX_EVENTS = 30
SNAPSHOT_TTL_MINUTES = 20
PROMPT_CHAR_CAP = 3500
LOCATION_MAX_CHARS = 120

_WORKDAY_START = time(8, 0)
_WORKDAY_END = time(18, 0)
_TIME_RE = re.compile(r"\b([01]?\d|2[0-3])(?::([0-5]\d))?\s*(?:uhr|h)?\b", re.IGNORECASE)
_DATE_SIGNAL_RE = re.compile(
    r"\b(heute|morgen|übermorgen|uebermorgen|montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag|\d{1,2}\.\d{1,2}(?:\.\d{2,4})?)\b",
    re.IGNORECASE,
)
_CALENDAR_QUERY_RE = re.compile(
    r"\b(kalender|termin|termine|meeting|meetings|agenda|heute frei|morgen frei|frei\?|verplant|verfuegbar|verfügbar|busy|free slot|zeitfenster)\b",
    re.IGNORECASE,
)
_PLANNING_SIGNAL_RE = re.compile(
    r"\b(fahre|fahrt|reise|fliege|flug|besuche|treffe|plane|planung|verabredet|unterwegs|ausflug|termin bei)\b",
    re.IGNORECASE,
)


def calendar_mirror_enabled() -> bool:
    """Return whether the calendar memory mirror is enabled."""
    return os.getenv("JANUS_CALENDAR_MIRROR_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "off",
        "no",
    }


def proactive_hints_enabled() -> bool:
    """Return whether proactive calendar hints are enabled for V1."""
    return os.getenv("JANUS_CALENDAR_PROACTIVE_HINTS", "false").strip().lower() in {
        "1",
        "true",
        "on",
        "yes",
    }


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_datetime(value: Any, tz: ZoneInfo = BERLIN_TZ) -> Optional[datetime]:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    elif isinstance(value, str) and value.strip():
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            parsed = dateparser.parse(
                raw,
                languages=["de", "en"],
                settings={"TIMEZONE": "Europe/Berlin", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            dt = parsed if parsed is not None else None
    else:
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _event_value(event: Any, key: str, default: Any = None) -> Any:
    if isinstance(event, dict):
        return event.get(key, default)
    return getattr(event, key, default)


def _truncate(value: Any, max_chars: int) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_chars]


def classify_event(title: str, location: Optional[str] = None) -> str:
    haystack = f"{title or ''} {location or ''}".lower()
    if any(token in haystack for token in ("meeting", "call", "standup", "sync", "1:1")):
        return "meeting"
    if any(token in haystack for token in ("arzt", "zahnarzt", "doctor", "termin bei")):
        return "appointment"
    if any(token in haystack for token in ("fokus", "focus", "deep work", "blocker")):
        return "focus"
    if any(token in haystack for token in ("geburtstag", "birthday", "feier")):
        return "personal"
    if any(token in haystack for token in ("reise", "flug", "flight", "fahrt")):
        return "travel"
    return "other"


def event_importance(title: str, event_type: str, is_all_day: bool) -> str:
    title_l = (title or "").lower()
    if event_type in {"appointment", "travel"} or any(
        token in title_l for token in ("urgent", "wichtig", "deadline")
    ):
        return "high"
    if event_type == "meeting":
        return "medium"
    if is_all_day or event_type in {"focus", "personal", "other"}:
        return "low"
    return "low"


def is_event_movable(event: Any, importance: str) -> bool:
    if importance == "high":
        return False
    attendees = _event_value(event, "attendees", []) or []
    recurrence = _event_value(event, "recurrence_rule") or _event_value(event, "recurrence")
    return not (len(attendees) > 2 or bool(recurrence))


def _snapshot_event(event: Any) -> Optional[Dict[str, Any]]:
    start = _as_datetime(_event_value(event, "start"))
    end = _as_datetime(_event_value(event, "end"))
    if start is None:
        return None
    if end is None or end <= start:
        end = start + timedelta(days=1 if _event_value(event, "is_all_day", False) else 1 / 24)
    title = str(_event_value(event, "title") or _event_value(event, "summary") or "(Kein Titel)")
    location = _truncate(_event_value(event, "location"), LOCATION_MAX_CHARS)
    is_all_day = bool(_event_value(event, "is_all_day", False))
    event_type = classify_event(title, location)
    importance = event_importance(title, event_type, is_all_day)
    return {
        "id": str(_event_value(event, "id") or _event_value(event, "external_id") or ""),
        "title": title[:300],
        "start": start.isoformat(),
        "end": end.isoformat(),
        "is_all_day": is_all_day,
        "location": location,
        "event_type": event_type,
        "importance": importance,
        "movable": is_event_movable(event, importance),
    }


def _event_datetimes(event: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
    return _as_datetime(event.get("start")), _as_datetime(event.get("end"))


def _events_for_day(events: Iterable[Dict[str, Any]], day: date) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    day_start = datetime.combine(day, time.min, tzinfo=BERLIN_TZ)
    day_end = day_start + timedelta(days=1)
    for event in events:
        start, end = _event_datetimes(event)
        if start and end and start < day_end and end > day_start:
            result.append(event)
    return sorted(result, key=lambda e: e.get("start") or "")


def _merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda item: item[0])
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _free_slots_for_day(events: List[Dict[str, Any]], day: date) -> Tuple[List[str], int]:
    work_start = datetime.combine(day, _WORKDAY_START, tzinfo=BERLIN_TZ)
    work_end = datetime.combine(day, _WORKDAY_END, tzinfo=BERLIN_TZ)
    busy: List[Tuple[datetime, datetime]] = []
    for event in events:
        if event.get("is_all_day"):
            continue
        start, end = _event_datetimes(event)
        if not start or not end:
            continue
        clipped_start = max(start, work_start)
        clipped_end = min(end, work_end)
        if clipped_start < clipped_end:
            busy.append((clipped_start, clipped_end))

    merged = _merge_intervals(busy)
    free: List[str] = []
    cursor = work_start
    busy_minutes = 0
    for start, end in merged:
        busy_minutes += int((end - start).total_seconds() // 60)
        if (start - cursor).total_seconds() >= 30 * 60:
            free.append(f"{cursor.strftime('%H:%M')}-{start.strftime('%H:%M')}")
        cursor = max(cursor, end)
    if (work_end - cursor).total_seconds() >= 30 * 60:
        free.append(f"{cursor.strftime('%H:%M')}-{work_end.strftime('%H:%M')}")
    return free[:6], busy_minutes


def build_calendar_snapshot(
    events: Iterable[Any],
    *,
    generated_at: Optional[datetime] = None,
    tz_name: str = "Europe/Berlin",
    source: str = "google",
    max_events: int = SNAPSHOT_MAX_EVENTS,
) -> Dict[str, Any]:
    """Build the compact V1 snapshot payload from normalized calendar events."""
    generated = generated_at or _now_utc()
    generated_local = _as_datetime(generated) or datetime.now(BERLIN_TZ)
    normalized = [item for item in (_snapshot_event(event) for event in events) if item is not None]
    normalized.sort(key=lambda item: item["start"])
    overflow_count = max(0, len(normalized) - max_events)
    capped = normalized[:max_events]
    today_events = _events_for_day(capped, generated_local.date())
    future_events = [
        event
        for event in capped
        if (_event_datetimes(event)[0] is not None and _event_datetimes(event)[0] >= generated_local)
    ]
    free_slots, busy_minutes = _free_slots_for_day(today_events, generated_local.date())
    workday_minutes = int(
        (
            datetime.combine(generated_local.date(), _WORKDAY_END, tzinfo=BERLIN_TZ)
            - datetime.combine(generated_local.date(), _WORKDAY_START, tzinfo=BERLIN_TZ)
        ).total_seconds()
        // 60
    )
    next_event = None
    if future_events:
        first = future_events[0]
        next_event = {
            "title": first.get("title"),
            "start": first.get("start"),
            "importance": first.get("importance"),
        }
    return {
        "v": SNAPSHOT_VERSION,
        "generated_at": generated.astimezone(timezone.utc).isoformat(),
        "tz": tz_name,
        "source": source,
        "derived": {
            "next_event": next_event,
            "busy_today": bool(today_events),
            "free_slots_today": free_slots,
            "day_load_percent": min(100, round((busy_minutes / workday_minutes) * 100)) if workday_minutes else 0,
            "event_count_14d": len(normalized),
            "overflow_count": overflow_count,
        },
        "events": capped,
    }


def upsert_calendar_snapshot(db: Session, events: Iterable[Any], *, source: str = "google") -> Dict[str, Any]:
    """Full-replace the calendar snapshot in Memory."""
    if not calendar_mirror_enabled():
        return {}
    snapshot = build_calendar_snapshot(events, source=source)
    snippet = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    now = datetime.utcnow()
    memory = (
        db.query(models.Memory)
        .filter(models.Memory.category == CALENDAR_SNAPSHOT_CATEGORY)
        .filter(models.Memory.canonical_key == CALENDAR_SNAPSHOT_KEY)
        .first()
    )
    try:
        if memory is None:
            memory = models.Memory(
                chat_id=None,
                snippet=snippet,
                normalized_text=CALENDAR_SNAPSHOT_KEY,
                text_hash=compute_hash(CALENDAR_SNAPSHOT_KEY),
                category=CALENDAR_SNAPSHOT_CATEGORY,
                is_core_fact=False,
                core_priority=0,
                priority=0.45,
                memory_type="EPHEMERAL",
                tags=["calendar", "snapshot"],
                source_skill="calendar.memory_mirror",
                user_editable=False,
                canonical_key=CALENDAR_SNAPSHOT_KEY,
                source_type="calendar",
                source_metadata={"source": source, "schema_version": SNAPSHOT_VERSION},
                last_accessed_at=now,
            )
            db.add(memory)
        else:
            memory.snippet = snippet
            memory.last_accessed_at = now
            memory.source_metadata = {"source": source, "schema_version": SNAPSHOT_VERSION}
        db.commit()
        logger.info("[CALENDAR-MEMORY] Snapshot upserted: events=%d", len(snapshot.get("events", [])))
    except Exception:
        db.rollback()
        logger.warning("[CALENDAR-MEMORY] Snapshot upsert failed", exc_info=True)
    return snapshot


def load_calendar_snapshot(db: Session) -> Optional[Dict[str, Any]]:
    if not calendar_mirror_enabled():
        return None
    memory = (
        db.query(models.Memory)
        .filter(models.Memory.category == CALENDAR_SNAPSHOT_CATEGORY)
        .filter(models.Memory.canonical_key == CALENDAR_SNAPSHOT_KEY)
        .first()
    )
    if not memory or not memory.snippet:
        return None
    try:
        data = json.loads(str(memory.snippet))
    except json.JSONDecodeError:
        logger.warning("[CALENDAR-MEMORY] Invalid snapshot JSON in memory id=%s", memory.id)
        return None
    return data if isinstance(data, dict) and data.get("v") == SNAPSHOT_VERSION else None


def invalidate_calendar_snapshot(db: Session) -> bool:
    """Delete the calendar snapshot from Memory to force fresh data fetch on next query.
    
    This should be called after successful create_event, update_event, or delete_event
    operations to ensure the LLM doesn't rely on stale snapshot data.
    
    Returns:
        True if snapshot was deleted or didn't exist, False on error
    """
    if not calendar_mirror_enabled():
        return True
    try:
        memory = (
            db.query(models.Memory)
            .filter(models.Memory.category == CALENDAR_SNAPSHOT_CATEGORY)
            .filter(models.Memory.canonical_key == CALENDAR_SNAPSHOT_KEY)
            .first()
        )
        if memory:
            db.delete(memory)
            db.commit()
            logger.info("[CALENDAR-MEMORY] Snapshot invalidated (deleted) after calendar mutation")
        else:
            logger.debug("[CALENDAR-MEMORY] No snapshot to invalidate")
        return True
    except Exception:
        db.rollback()
        logger.warning("[CALENDAR-MEMORY] Snapshot invalidation failed", exc_info=True)
        return False


def snapshot_is_stale(snapshot: Dict[str, Any], *, now: Optional[datetime] = None) -> bool:
    generated = _as_datetime(snapshot.get("generated_at"))
    if generated is None:
        return True
    now_local = _as_datetime(now or _now_utc()) or datetime.now(BERLIN_TZ)
    return now_local - generated > timedelta(minutes=SNAPSHOT_TTL_MINUTES)


def should_inject_calendar_context(user_text: str) -> bool:
    text = user_text or ""
    return bool(_CALENDAR_QUERY_RE.search(text) or (_DATE_SIGNAL_RE.search(text) and _PLANNING_SIGNAL_RE.search(text)))


def _format_event_line(event: Dict[str, Any]) -> str:
    start, end = _event_datetimes(event)
    if not start:
        return f"- {event.get('title', '(Kein Titel)')}"
    if event.get("is_all_day"):
        when = f"{start.strftime('%a %d.%m')} ganztägig"
    elif end:
        when = f"{start.strftime('%a %d.%m %H:%M')}-{end.strftime('%H:%M')}"
    else:
        when = start.strftime("%a %d.%m %H:%M")
    loc = f", Ort: {event.get('location')}" if event.get("location") else ""
    return (
        f"- {when}: {event.get('title')} "
        f"(Typ: {event.get('event_type')}, Wichtigkeit: {event.get('importance')}, verschiebbar: {event.get('movable')}){loc}"
    )


def render_calendar_context(
    snapshot: Optional[Dict[str, Any]],
    user_text: str,
    *,
    now: Optional[datetime] = None,
    char_cap: int = PROMPT_CHAR_CAP,
) -> str:
    """Render a bounded calendar block for the LLM prompt."""
    if not snapshot or not should_inject_calendar_context(user_text):
        return ""
    now_local = _as_datetime(now or _now_utc()) or datetime.now(BERLIN_TZ)
    today = now_local.date()
    tomorrow = today + timedelta(days=1)
    events = snapshot.get("events") if isinstance(snapshot.get("events"), list) else []
    today_tomorrow = [
        event
        for event in events
        if any(day_event is event for day in (today, tomorrow) for day_event in _events_for_day([event], day))
    ]
    derived = snapshot.get("derived") or {}
    stale_note = " (Stand evtl. älter als 20 Minuten)" if snapshot_is_stale(snapshot, now=now_local) else ""
    lines = [
        f"### KALENDER-SNAPSHOT (Memory-Spiegel, Quelle bleibt Live-Kalender){stale_note}",
        f"Generiert: {snapshot.get('generated_at')} | Zeitzone: {snapshot.get('tz', 'Europe/Berlin')}",
        "Derived:",
        f"- next_event: {derived.get('next_event')}",
        f"- busy_today: {derived.get('busy_today')} | day_load_percent: {derived.get('day_load_percent')} | event_count_14d: {derived.get('event_count_14d')} | overflow_count: {derived.get('overflow_count', 0)}",
        f"- free_slots_today: {', '.join(derived.get('free_slots_today') or []) or 'keine im Arbeitsfenster'}",
        "Events heute + morgen:",
    ]
    lines.extend(_format_event_line(event) for event in today_tomorrow)
    if not today_tomorrow:
        lines.append("- keine Termine im Snapshot für heute/morgen")
    block = "\n".join(lines)
    if len(block) > char_cap:
        return block[: char_cap - 40].rstrip() + "\n... (Kalender-Snapshot gekürzt)"
    return block


def _extract_user_window(user_text: str, *, now: Optional[datetime] = None) -> Optional[Tuple[datetime, datetime]]:
    text = user_text or ""
    if not (_DATE_SIGNAL_RE.search(text) or _PLANNING_SIGNAL_RE.search(text)):
        return None
    base = _as_datetime(now or _now_utc()) or datetime.now(BERLIN_TZ)
    matches = search_dates(
        text,
        languages=["de", "en"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": base,
            "TIMEZONE": "Europe/Berlin",
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
    )
    parsed_dt = matches[0][1] if matches else dateparser.parse(
        text,
        languages=["de", "en"],
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": base,
            "TIMEZONE": "Europe/Berlin",
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
    )
    if parsed_dt is None:
        return None
    parsed_dt = _as_datetime(parsed_dt) or base
    times = [(int(h), int(m or 0)) for h, m in _TIME_RE.findall(text)]
    if len(times) >= 2:
        start = parsed_dt.replace(hour=times[0][0], minute=times[0][1], second=0, microsecond=0)
        end = parsed_dt.replace(hour=times[1][0], minute=times[1][1], second=0, microsecond=0)
        if end <= start:
            end += timedelta(days=1)
        return start, end
    if len(times) == 1:
        start = parsed_dt.replace(hour=times[0][0], minute=times[0][1], second=0, microsecond=0)
        return start, start + timedelta(hours=2)
    day_start = datetime.combine(parsed_dt.date(), time.min, tzinfo=BERLIN_TZ)
    return day_start, day_start + timedelta(days=1)


def detect_calendar_conflicts(
    snapshot: Optional[Dict[str, Any]],
    user_text: str,
    *,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Detect hard/soft/load conflicts between the user plan and the snapshot."""
    if not snapshot or snapshot_is_stale(snapshot, now=now):
        return []
    window = _extract_user_window(user_text, now=now)
    if not window:
        return []
    planned_start, planned_end = window
    events = snapshot.get("events") if isinstance(snapshot.get("events"), list) else []
    conflicts: List[Dict[str, Any]] = []
    day_events = _events_for_day(events, planned_start.date())
    for event in day_events:
        start, end = _event_datetimes(event)
        if not start or not end:
            continue
        if start < planned_end and end > planned_start:
            conflicts.append({"type": "hard", "event": event})
            continue
        gap_before = abs((planned_start - end).total_seconds()) / 60
        gap_after = abs((start - planned_end).total_seconds()) / 60
        if min(gap_before, gap_after) < 60 and event.get("importance") in {"medium", "high"}:
            conflicts.append({"type": "soft", "event": event})
    timed_minutes = 0
    for event in day_events:
        start, end = _event_datetimes(event)
        if start and end and not event.get("is_all_day"):
            timed_minutes += max(0, int((end - start).total_seconds() // 60))
    if len(day_events) > 6 or timed_minutes > 360:
        conflicts.append({"type": "load", "event_count": len(day_events), "busy_minutes": timed_minutes})
    return conflicts


def render_proactive_calendar_guidance(
    snapshot: Optional[Dict[str, Any]],
    user_text: str,
    *,
    now: Optional[datetime] = None,
) -> str:
    if not proactive_hints_enabled():
        return ""
    conflicts = detect_calendar_conflicts(snapshot, user_text, now=now)
    selected = next((item for item in conflicts if item.get("type") in {"hard", "soft"}), None)
    if not selected:
        return ""
    event = selected.get("event") or {}
    return (
        "PROAKTIVER KALENDER-HINWEIS: Wenn passend, füge maximal einen kurzen Satz hinzu. "
        f"Konflikt={selected.get('type')}; Termin={_format_event_line(event)}. "
        "Nur Fakt + optionale kurze Frage, keine Aktion auslösen."
    )
