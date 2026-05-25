#!/usr/bin/env python3
"""Search WHAT_I_LEARNED.md without loading the whole file into context."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def split_patterns(text: str) -> list[str]:
    chunks = re.split(r"(?m)^## \[PATTERN\] ", text)
    if len(chunks) <= 1:
        return []
    return ["## [PATTERN] " + chunk.strip() for chunk in chunks[1:] if chunk.strip()]


def score_pattern(pattern: str, terms: list[str]) -> int:
    lower = pattern.lower()
    title = pattern.splitlines()[0].lower() if pattern.splitlines() else ""
    score = 0
    query = " ".join(terms).lower()
    if query and query in lower:
        score += 25
    for term in terms:
        needle = term.lower()
        if not needle:
            continue
        score += lower.count(needle)
        if needle in title:
            score += 10
        if f"#{needle}" in title:
            score += 20
        if re.search(rf"(?im)^\- \*\*Tags:\*\*.*\b{re.escape(needle)}\b", pattern):
            score += 8
    return score


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Janus WHAT_I_LEARNED patterns.")
    parser.add_argument("--file", type=Path, default=Path("WHAT_I_LEARNED.md"))
    parser.add_argument("--query", required=True, help="Space-separated search terms or exact error text")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--context-lines", type=int, default=8)
    args = parser.parse_args()

    if not args.file.exists():
        print(f"WHAT_I_LEARNED SEARCH FAILED: missing file {args.file}")
        return 1

    terms = [term for term in re.split(r"\s+", args.query.strip()) if len(term) > 1]
    patterns = split_patterns(args.file.read_text(encoding="utf-8-sig", errors="replace"))
    ranked = sorted(
        ((score_pattern(pattern, terms), pattern) for pattern in patterns),
        key=lambda item: item[0],
        reverse=True,
    )
    matches = [(score, pattern) for score, pattern in ranked if score > 0][: args.limit]

    print("WHAT_I_LEARNED SEARCH")
    print(f"- Query: {args.query}")
    print(f"- Matches: {len(matches)}")
    for index, (score, pattern) in enumerate(matches, start=1):
        lines = pattern.splitlines()
        print(f"\n## Match {index} (score {score})")
        for line in lines[: args.context_lines]:
            print(line)
        if len(lines) > args.context_lines:
            print("...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
