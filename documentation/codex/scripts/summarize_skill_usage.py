#!/usr/bin/env python3
"""Summarize Janus Codex skill usage patterns."""

from __future__ import annotations

import argparse
import collections
import csv
import io
from pathlib import Path


def parse_markdown_table(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []

    header = [part.strip() for part in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        values = [part.strip() for part in line.strip("|").split("|")]
        if len(values) != len(header):
            continue
        rows.append(dict(zip(header, values)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Janus skill usage log.")
    parser.add_argument("--log", type=Path, default=Path("documentation/codex/SKILL_USAGE_LOG.md"))
    parser.add_argument("--csv", action="store_true", help="Emit CSV rows instead of text summary")
    args = parser.parse_args()

    if not args.log.exists():
        print(f"No usage log found: {args.log}")
        return 0

    rows = parse_markdown_table(args.log.read_text(encoding="utf-8-sig"))
    if args.csv:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
        print(output.getvalue(), end="")
        return 0

    by_skill = collections.Counter(row.get("Skill", "N/A") for row in rows)
    by_state = collections.Counter(row.get("State", "N/A") for row in rows)
    by_model = collections.Counter(row.get("Model", "N/A") for row in rows)
    frictions = [row for row in rows if row.get("Friction", "none").lower() not in {"none", "n/a", ""}]
    optimizations = [row for row in rows if row.get("Optimization", "none").lower() not in {"none", "n/a", ""}]

    print("JANUS SKILL USAGE SUMMARY")
    print(f"- Entries: {len(rows)}")
    print("- Skills: " + (", ".join(f"{k}={v}" for k, v in by_skill.most_common()) or "none"))
    print("- States: " + (", ".join(f"{k}={v}" for k, v in by_state.most_common()) or "none"))
    print("- Models: " + (", ".join(f"{k}={v}" for k, v in by_model.most_common()) or "none"))
    print(f"- Friction entries: {len(frictions)}")
    print(f"- Optimization entries: {len(optimizations)}")

    if frictions:
        print("\nTop friction examples:")
        for row in frictions[-5:]:
            print(f"- {row.get('Date')} {row.get('Skill')}: {row.get('Friction')}")

    if optimizations:
        print("\nRecent optimization ideas:")
        for row in optimizations[-5:]:
            print(f"- {row.get('Date')} {row.get('Skill')}: {row.get('Optimization')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

