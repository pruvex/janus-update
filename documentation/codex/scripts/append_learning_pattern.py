#!/usr/bin/env python3
"""Append a standardized pattern to WHAT_I_LEARNED.md."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


def clean(value: str) -> str:
    return (value or "N/A").replace("\r", " ").replace("\n", " ").strip() or "N/A"


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a Janus reusable learning pattern.")
    parser.add_argument("--file", type=Path, default=Path("WHAT_I_LEARNED.md"))
    parser.add_argument("--id", required=True, help="Pattern id, for example PromptBudgetEvidenceMustBeSemantic")
    parser.add_argument("--title", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--problem", required=True)
    parser.add_argument("--solution", required=True)
    parser.add_argument("--hardening", required=True)
    parser.add_argument("--tripwire", required=True)
    parser.add_argument("--location", default="N/A")
    parser.add_argument("--epic", default="N/A")
    parser.add_argument("--confidence", choices=["Low", "Medium", "High"], default="High")
    parser.add_argument("--tags", required=True, help="Comma-separated tags")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not re.match(r"^[A-Za-z][A-Za-z0-9]+$", args.id):
        raise SystemExit("--id must be alphanumeric PascalCase/camelCase without spaces")

    text = args.file.read_text(encoding="utf-8-sig", errors="replace") if args.file.exists() else ""
    if f"#{args.id} " in text:
        raise SystemExit(f"Pattern already exists: #{args.id}")

    entry = f"""
## [PATTERN] #{args.id} "{clean(args.title)}"
- **Kontext:** {clean(args.context)} ({args.date}).
- **Problem:** {clean(args.problem)}
- **Loesung:** {clean(args.solution)}
- **Haertung:** {clean(args.hardening)}
- **Tripwire:** {clean(args.tripwire)}
- **Location:** {clean(args.location)}
- **Epic:** {clean(args.epic)}
- **Confidence:** {args.confidence}
- **Tags:** {clean(args.tags)}
""".strip()

    if args.dry_run:
        print(entry)
        return 0

    if not args.file.exists():
        args.file.write_text("# KNOWLEDGE BASE: WHAT I LEARNED\n\n", encoding="utf-8")

    with args.file.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n\n" + entry + "\n")

    print(f"Appended learning pattern: #{args.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

