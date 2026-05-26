from datetime import datetime, timezone

from backend.services.calendar.calendar_memory import (
    build_calendar_snapshot,
    classify_event,
    detect_calendar_conflicts,
    event_importance,
    render_calendar_context,
    snapshot_is_stale,
)


def _event(
    title: str,
    start: str,
    end: str,
    *,
    location: str | None = None,
    attendees: list[str] | None = None,
    recurrence_rule: str | None = None,
    is_all_day: bool = False,
) -> dict:
    return {
        "id": title.lower().replace(" ", "_"),
        "title": title,
        "start": start,
        "end": end,
        "location": location,
        "attendees": attendees or [],
        "recurrence_rule": recurrence_rule,
        "is_all_day": is_all_day,
    }


def test_event_enrichment_rules_cover_v1_cases():
    cases = [
        ("Team Sync", None, "meeting", "medium"),
        ("Termin bei Zahnarzt", None, "appointment", "high"),
        ("Focus Deep Work", None, "focus", "low"),
        ("Geburtstag Erna", None, "personal", "low"),
        ("Flug nach Berlin", None, "travel", "high"),
        ("Notizblock", None, "other", "low"),
    ]

    for title, location, expected_type, expected_importance in cases:
        event_type = classify_event(title, location)
        assert event_type == expected_type
        assert event_importance(title, event_type, False) == expected_importance


def test_build_calendar_snapshot_contains_derived_summary_and_enrichment():
    now = datetime(2026, 5, 2, 6, 15, tzinfo=timezone.utc)  # 08:15 Europe/Berlin
    snapshot = build_calendar_snapshot(
        [
            _event("Team Sync", "2026-05-02T14:00:00+02:00", "2026-05-02T15:00:00+02:00"),
            _event("Zahnarzt", "2026-05-03T09:00:00+02:00", "2026-05-03T10:00:00+02:00"),
        ],
        generated_at=now,
    )

    assert snapshot["v"] == 1
    assert snapshot["derived"]["busy_today"] is True
    assert snapshot["derived"]["next_event"]["title"] == "Team Sync"
    assert snapshot["derived"]["event_count_14d"] == 2
    assert "08:00-14:00" in snapshot["derived"]["free_slots_today"]
    assert snapshot["events"][0]["event_type"] == "meeting"
    assert snapshot["events"][0]["importance"] == "medium"
    assert snapshot["events"][1]["movable"] is False


def test_conflict_detection_handles_donnerstag_tante_erna_scenario():
    now = datetime(2026, 5, 2, 6, 15, tzinfo=timezone.utc)
    snapshot = build_calendar_snapshot(
        [
            _event(
                "Team Sync",
                "2026-05-07T14:00:00+02:00",
                "2026-05-07T15:00:00+02:00",
            )
        ],
        generated_at=now,
    )

    conflicts = detect_calendar_conflicts(
        snapshot,
        "Donnerstag fahre ich zu Tante Erna",
        now=now,
    )

    assert conflicts
    assert conflicts[0]["type"] == "hard"
    assert conflicts[0]["event"]["title"] == "Team Sync"
    assert conflicts[0]["event"]["importance"] == "medium"


def test_conflict_detection_ignores_stale_snapshot():
    now = datetime(2026, 5, 2, 6, 15, tzinfo=timezone.utc)
    snapshot = build_calendar_snapshot(
        [_event("Team Sync", "2026-05-02T14:00:00+02:00", "2026-05-02T15:00:00+02:00")],
        generated_at=datetime(2026, 5, 2, 5, 0, tzinfo=timezone.utc),
    )

    assert snapshot_is_stale(snapshot, now=now) is True
    assert detect_calendar_conflicts(snapshot, "Heute plane ich etwas um 14 Uhr", now=now) == []


def test_render_calendar_context_is_bounded_and_query_gated():
    now = datetime(2026, 5, 2, 6, 15, tzinfo=timezone.utc)
    snapshot = build_calendar_snapshot(
        [
            _event("Team Sync", "2026-05-02T14:00:00+02:00", "2026-05-02T15:00:00+02:00"),
            _event("Übermorgen Event", "2026-05-04T12:00:00+02:00", "2026-05-04T13:00:00+02:00"),
        ],
        generated_at=now,
    )

    assert render_calendar_context(snapshot, "Erzähl mir einen Witz", now=now) == ""
    block = render_calendar_context(snapshot, "Welche Termine habe ich heute?", now=now, char_cap=800)
    assert "KALENDER-SNAPSHOT" in block
    assert "Team Sync" in block
    assert "Übermorgen Event" not in block
