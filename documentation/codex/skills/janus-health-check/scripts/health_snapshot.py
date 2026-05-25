#!/usr/bin/env python3
"""Read-only Janus health snapshot for bounded hygiene checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


EXCLUDES = {
    ".git",
    "node_modules",
    "venv",
    ".pytest_cache",
    ".ruff_cache",
    "playwright-report",
    "test-results",
    "__pycache__",
    "dist",
    "build",
    ".vercel",
}

CORE_ARTIFACTS = [
    "AGENTS.md",
    "documentation/CODEX_MIGRATION_PLAN.md",
    "documentation/backlog/BACKLOG.md",
    "documentation/pipeline/PIPELINE_CONTRACT.md",
    "janus-dashboard/data/backlog.snapshot.json",
]


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.STDOUT).rstrip("\n")
    except Exception as exc:
        return f"ERROR: {exc}"


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDES or (part == "backend" and "venv" in path.parts) for part in path.parts)


def large_files(repo: Path, limit: int = 20) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for path in repo.rglob("*"):
        if not path.is_file() or should_skip(path.relative_to(repo)):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > 500 * 1024:
            found.append((size, str(path.relative_to(repo))))
    return sorted(found, reverse=True)[:limit]


def count_backlog_markers(path: Path) -> dict[str, int | str]:
    if not path.exists():
        return {"exists": "NO"}
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return {
        "exists": "YES",
        "in_progress": text.count("IN PROGRESS"),
        "ready": text.count("READY"),
        "needs_info": text.count("NEEDS INFO"),
        "blocked": text.count("BLOCKED"),
    }


def migration_gaps(repo: Path) -> list[str]:
    plan = repo / "documentation" / "CODEX_MIGRATION_PLAN.md"
    if not plan.exists():
        return ["migration plan missing"]
    gaps: list[str] = []
    for line in plan.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "| `" in line and "geplant" in line:
            gaps.append(line.strip())
    return gaps


def root_suspicious(repo: Path, limit: int = 20) -> list[str]:
    patterns = {".tmp", ".bak", ".old", ".log", ".db", ".sqlite", ".exe"}
    items: list[str] = []
    for path in repo.iterdir():
        if path.is_file() and path.suffix.lower() in patterns:
            items.append(path.name)
    return items[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect a read-only Janus health snapshot.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=["DAILY", "WEEKLY", "MONTHLY"], default="DAILY")
    args = parser.parse_args()

    repo = args.repo.resolve()
    status = git(repo, "status", "--porcelain")
    dirty_lines = [] if not status or status.startswith("ERROR:") else status.splitlines()
    staged = [line for line in dirty_lines if not line.startswith("??") and line[0] not in {" ", "?"}]
    unstaged = [line for line in dirty_lines if not line.startswith("??") and len(line) > 1 and line[1] not in {" ", "?"}]
    untracked = [line for line in dirty_lines if line.startswith("??")]

    data = {
        "mode": args.mode,
        "repo": str(repo),
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty_total": len(dirty_lines),
        "staged": len(staged),
        "unstaged": len(unstaged),
        "untracked": len(untracked),
        "core_artifacts": {item: (repo / item).exists() for item in CORE_ARTIFACTS},
        "backlog": count_backlog_markers(repo / "documentation" / "backlog" / "BACKLOG.md"),
        "migration_gaps": migration_gaps(repo),
        "root_suspicious": root_suspicious(repo),
    }

    if args.mode in {"WEEKLY", "MONTHLY"}:
        data["large_files_over_500kb"] = large_files(repo)

    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
