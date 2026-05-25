#!/usr/bin/env python3
"""Append a standardized Janus Codex skill usage row."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


HEADER = """# Janus Codex Skill Usage Log

Dieses Log ist append-only und dokumentiert substantielle Janus-Skill-Laeufe. Es dient dazu, regelmaessig zu pruefen, ob Routing, Modellwahl, Kontextstrategie, Stop-Gates oder Automatisierung verbessert werden sollten.

Nicht jeder Chat-Satz wird geloggt. Geloggt werden nur echte Arbeitsbloecke mit Skill-Entscheidung, Artefaktbezug, Check, Handoff, Blocker oder Commit-Relevanz.

## Log Format

| Date | Skill | Trigger | Model | Intelligence | Chat | State | Artifacts | Checks | Friction | Optimization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""


def cell(value: str) -> str:
    value = (value or "N/A").replace("\n", " ").replace("|", "/").strip()
    return value or "N/A"


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a Janus skill usage entry.")
    parser.add_argument("--log", type=Path, default=Path("documentation/codex/SKILL_USAGE_LOG.md"))
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--skill", required=True)
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--intelligence", required=True)
    parser.add_argument("--chat", choices=["same", "new", "recommended-new", "unknown"], default="same")
    parser.add_argument("--state", required=True)
    parser.add_argument("--artifacts", default="N/A")
    parser.add_argument("--checks", default="N/A")
    parser.add_argument("--friction", default="none")
    parser.add_argument("--optimization", default="none")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    row = (
        f"| {cell(args.date)} | {cell(args.skill)} | {cell(args.trigger)} | {cell(args.model)} | "
        f"{cell(args.intelligence)} | {cell(args.chat)} | {cell(args.state)} | {cell(args.artifacts)} | "
        f"{cell(args.checks)} | {cell(args.friction)} | {cell(args.optimization)} |"
    )

    if args.dry_run:
        print(row)
        return 0

    if not args.log.exists():
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(HEADER, encoding="utf-8")

    text = args.log.read_text(encoding="utf-8-sig")
    if "| Date | Skill |" not in text:
        raise SystemExit(f"Log file exists but does not look like a skill usage log: {args.log}")

    with args.log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(row + "\n")

    print(f"Recorded skill usage: {args.skill} -> {args.state}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

