#!/usr/bin/env python3
"""Read-only Janus health snapshot for bounded hygiene checks."""

from __future__ import annotations

import argparse
import collections
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

KNOWN_ROOT_RUNTIME_DB_ARTIFACTS = {
    "janus.db": "stray root copy; active Janus runtime DB belongs under %APPDATA%/Janus Projekt/janus.db",
    "janus_fallback.db": "fallback root DB; normal runtime should still resolve to %APPDATA%/Janus Projekt/janus.db",
    "chat_history.db": "legacy local split-chat DB artifact; not the intended active Janus runtime DB path",
    "costs.db": "legacy local split-cost DB artifact; not the intended active Janus runtime DB path",
}

KNOWN_ROOT_LEGACY_LOG_ARTIFACTS = {
    ".codex-vite-err.log": "legacy root Vite error log; current versioned dev start path writes Vite logs under documentation/logs/dev-runtime/",
    ".codex-vite-out.log": "legacy root Vite output log; current versioned dev start path writes Vite logs under documentation/logs/dev-runtime/",
    "backend_hotfix.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_hotfix.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_live.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_live.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_persist.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_persist.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_restart.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_restart.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_start.log": "legacy root backend start log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_start_manual.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_start_manual.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_verify.err.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "backend_verify.out.log": "legacy root backend helper log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "startdev.log": "legacy root start-dev log; current versioned startup telemetry belongs under documentation/logs and dev runtime logs under documentation/logs/dev-runtime/",
    "tmp_uv8011_err.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
    "tmp_uv8011_out.log": "legacy root temporary backend log; current versioned backend dev/runtime logs belong under documentation/logs/dev-runtime/",
}


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.STDOUT).rstrip("\n")
    except Exception as exc:
        return f"ERROR: {exc}"


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDES or (part == "backend" and "venv" in path.parts) for part in path.parts)


def large_files(repo: Path, limit: int = 20) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    tracked = git(repo, "ls-files")
    candidates = tracked.splitlines() if tracked and not tracked.startswith("ERROR:") else []
    for rel in candidates:
        path = repo / rel
        if not path.is_file() or should_skip(Path(rel)):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > 500 * 1024:
            found.append((size, rel))
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
        if (
            path.is_file()
            and path.suffix.lower() in patterns
            and path.name not in KNOWN_ROOT_RUNTIME_DB_ARTIFACTS
            and path.name not in KNOWN_ROOT_LEGACY_LOG_ARTIFACTS
        ):
            items.append(path.name)
    return items[:limit]


def root_runtime_db_artifacts(repo: Path, limit: int = 20) -> list[str]:
    items: list[str] = []
    for path in repo.iterdir():
        if path.is_file() and path.name in KNOWN_ROOT_RUNTIME_DB_ARTIFACTS:
            items.append(f"{path.name}: {KNOWN_ROOT_RUNTIME_DB_ARTIFACTS[path.name]}")
    return items[:limit]


def root_legacy_log_artifacts(repo: Path, limit: int = 20) -> list[str]:
    items: list[str] = []
    for path in repo.iterdir():
        if path.is_file() and path.name in KNOWN_ROOT_LEGACY_LOG_ARTIFACTS:
            items.append(f"{path.name}: {KNOWN_ROOT_LEGACY_LOG_ARTIFACTS[path.name]}")
    return items[:limit]


def parse_usage_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    header = [part.strip() for part in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        values = [part.strip() for part in line.strip("|").split("|")]
        if len(values) == len(header):
            rows.append(dict(zip(header, values)))
    return rows


def usage_summary(repo: Path, mode: str) -> dict[str, object]:
    log_path = repo / "documentation" / "codex" / "SKILL_USAGE_LOG.md"
    rows = parse_usage_log(log_path)
    data: dict[str, object] = {
        "exists": log_path.exists(),
        "entries": len(rows),
    }
    if mode == "DAILY":
        return data

    by_skill = collections.Counter(row.get("Skill", "N/A") for row in rows)
    by_state = collections.Counter(row.get("State", "N/A") for row in rows)
    by_model = collections.Counter(row.get("Model", "N/A") for row in rows)
    frictions = [row for row in rows if row.get("Friction", "none").lower() not in {"none", "n/a", ""}]
    optimizations = [row for row in rows if row.get("Optimization", "none").lower() not in {"none", "n/a", ""}]
    data.update(
        {
            "by_skill": dict(by_skill.most_common(10)),
            "by_state": dict(by_state.most_common()),
            "by_model": dict(by_model.most_common()),
            "friction_count": len(frictions),
            "optimization_count": len(optimizations),
            "recent_friction": frictions[-5:],
            "recent_optimizations": optimizations[-5:],
        }
    )
    return data


def parse_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _sum_numeric(rows: list[dict[str, object]], field: str) -> float:
    total = 0.0
    for row in rows:
        value = row.get(field)
        if isinstance(value, (int, float)):
            total += float(value)
    return total


def _average_numeric(rows: list[dict[str, object]], field: str) -> float | None:
    values = [float(value) for row in rows if isinstance((value := row.get(field)), (int, float))]
    if not values:
        return None
    return sum(values) / len(values)


def or_telemetry_summary(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    rows = parse_jsonl(path)
    models = sorted({str(row["or_model"]) for row in rows if row.get("or_model") not in {None, "", "N_A"}})
    skills = sorted({str(row["skill_id"]) for row in rows if row.get("skill_id")})
    routing_mode_counts = collections.Counter(str(row.get("routing_mode", "N_A")) for row in rows)
    validation_counts = collections.Counter(str(row.get("validation_result", "N_A")) for row in rows)
    recommendation_counts = collections.Counter(str(row.get("recommendation_signal", "N_A")) for row in rows)
    final_outcome_counts = collections.Counter(str(row.get("final_outcome", "N_A")) for row in rows)
    codex_outcome_counts = collections.Counter(str(row.get("codex_owned_outcome_status", "N_A")) for row in rows)
    fallback_count = sum(1 for row in rows if str(row.get("fallback_used", "NO")).upper() == "YES")
    summary: dict[str, object] = {
        "source": str(path),
        "record_count": len(rows),
        "models_seen": models,
        "skills_seen": skills,
        "routing_mode_counts": dict(routing_mode_counts),
        "estimated_cost_total": round(_sum_numeric(rows, "estimated_or_cost"), 8),
        "actual_cost_total": round(_sum_numeric(rows, "actual_or_cost"), 8),
        "confidence_average": _average_numeric(rows, "cost_estimate_confidence_percent"),
        "fallback_count": fallback_count,
        "validation_result_counts": dict(validation_counts),
        "recommendation_signal_counts": dict(recommendation_counts),
        "final_outcome_counts": dict(final_outcome_counts),
        "codex_owned_outcome_status_counts": dict(codex_outcome_counts),
    }
    if isinstance(summary["confidence_average"], float):
        summary["confidence_average"] = round(summary["confidence_average"], 2)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect a read-only Janus health snapshot.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=["DAILY", "WEEKLY", "MONTHLY"], default="DAILY")
    parser.add_argument(
        "--or-telemetry-jsonl",
        type=Path,
        default=None,
        help="Optional dummy OR telemetry JSONL path for read-only summary ingestion.",
    )
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
        "root_runtime_db_artifacts": root_runtime_db_artifacts(repo),
        "root_legacy_log_artifacts": root_legacy_log_artifacts(repo),
        "skill_usage": usage_summary(repo, args.mode),
    }

    or_summary = or_telemetry_summary(args.or_telemetry_jsonl)
    if or_summary is not None:
        data["or_telemetry"] = or_summary

    if args.mode in {"WEEKLY", "MONTHLY"}:
        data["large_files_over_500kb"] = large_files(repo)

    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
