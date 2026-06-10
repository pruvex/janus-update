#!/usr/bin/env python3
"""Check whether Codex or Janus healthcheck reminders are due today."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


STATE_PATH = Path.home() / ".codex" / "skill_logs" / "healthcheck_reminder_state.json"
LOG_PATH = Path.home() / ".codex" / "skill_logs" / "codex_skill_runs.jsonl"


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def append_log(payload: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def first_saturday(dt: datetime) -> bool:
    if dt.weekday() != 5:
        return False
    return 1 <= dt.day <= 7


def due_items(now: datetime, state: dict, mark: bool) -> list[dict]:
    today = now.date().isoformat()
    items: list[dict] = []

    checks = []
    if now.weekday() == 0:
        checks.append(
            {
                "id": f"codex-weekly-skill-healthcheck:{today}",
                "name": "Codex Weekly Skill Healthcheck",
                "kind": "CODEX_WEEKLY",
                "message": "Heute ist Montag; der Codex Weekly Skill Healthcheck ist faellig.",
                "run_hint": r"C:\Users\pruve\.codex\skills\codex-health-check\scripts\weekly_healthcheck.py",
            }
        )
    if now.weekday() == 5:
        mode = "MONTHLY" if first_saturday(now) else "WEEKLY"
        checks.append(
            {
                "id": f"janus-{mode.lower()}-healthcheck:{today}",
                "name": f"Janus {mode} Healthcheck",
                "kind": f"JANUS_{mode}",
                "message": f"Heute ist Samstag; der Janus {mode} Healthcheck ist faellig.",
                "run_hint": r"C:\KI\Janus-Projekt\documentation\codex\skills\janus-health-check\scripts\health_snapshot.py",
            }
        )

    reminded = state.setdefault("reminded", {})
    for check in checks:
        if reminded.get(check["id"]):
            continue
        items.append(check)
        if mark:
            reminded[check["id"]] = datetime.now(timezone.utc).isoformat()
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timezone", default="Europe/Berlin")
    parser.add_argument("--mark-reminded", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    now = datetime.now(ZoneInfo(args.timezone))
    state = load_state()
    items = due_items(now, state, args.mark_reminded)
    if args.mark_reminded and items:
        save_state(state)
    append_log(
        {
            "skill_name": "codex-start-of-work-check",
            "script": "due_healthchecks.py",
            "status": "due" if items else "clear",
            "duration_ms": 0,
            "metrics": {"due_count": len(items), "date": now.date().isoformat()},
        }
    )
    if args.json:
        print(json.dumps({"date": now.date().isoformat(), "due": items}, ensure_ascii=False, indent=2))
        return 0
    if not items:
        print("CLEAR: no healthcheck reminders due today.")
        return 0
    for item in items:
        print(f"DUE: {item['message']} Soll ich ihn jetzt starten? Antworte ok.")
        print(f"ID: {item['id']}")
        print(f"RUN_HINT: {item['run_hint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
