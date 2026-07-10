#!/usr/bin/env python3
"""Build a compact AUDIT_PACKAGE.md for final review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=30)
    except Exception as exc:  # pragma: no cover - defensive CLI behavior
        return 1, str(exc)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def git_section(cwd: Path, only: list[str]) -> tuple[str, str]:
    scope_args = ["--", *only] if only else []
    code, status = run(["git", "status", "--short", *scope_args], cwd)
    if code != 0:
        return "Git status unavailable.", "Diff summary unavailable."
    _, stat = run(["git", "diff", "--stat", *scope_args], cwd)
    _, names = run(["git", "diff", "--name-only", *scope_args], cwd)
    changed = status or names or "No uncommitted changes detected."
    summary = stat or "No diff stat available."
    return changed, summary


def inventory_paths(paths: list[str], cwd: Path) -> str:
    if not paths:
        return "No explicit artifact inventory provided."

    rows: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_absolute():
            path = cwd / path
        path = path.resolve()
        if not path.exists():
            rows.append(f"MISSING {path}")
            continue
        if path.is_file():
            rows.append(f"FILE {path} ({path.stat().st_size} bytes)")
            continue
        files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        rows.append(f"DIR {path} ({len(files)} files)")
        for item in files[:80]:
            rows.append(f"  FILE {item} ({item.stat().st_size} bytes)")
        if len(files) > 80:
            rows.append(f"  ... {len(files) - 80} more files omitted")
    return "\n".join(rows)


def read_optional(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    if not path.exists():
        return f"Provided file not found: {path}"
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text[:12000]


def read_required_excerpt(path_text: str, limit: int = 12000) -> str:
    if not path_text:
        return "N/A WITH REASON - No file provided."
    path = Path(path_text)
    if not path.exists():
        return f"MISSING FILE: {path}"
    return path.read_text(encoding="utf-8", errors="replace").strip()[:limit]


def extract_markdown_section(path_text: str, marker: str, limit: int = 12000) -> str:
    if not path_text or not marker:
        return "N/A WITH REASON - No backlog source or marker provided."
    path = Path(path_text)
    if not path.exists():
        return f"MISSING FILE: {path}"
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(rf"^###\s+{re.escape(marker)}\b.*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return f"MISSING MARKER: {marker} in {path}"
    start = match.start()
    line_end = text.find("\n", start)
    if line_end == -1:
        return text[start:].strip()[:limit]
    next_heading = re.search(r"(?m)^(## |### )", text[line_end + 1 :])
    section_end = len(text) if not next_heading else line_end + 1 + next_heading.start()
    section = text[start:section_end]
    return section.strip()[:limit]


def append_run_log(payload: dict) -> None:
    log_dir = Path.home() / ".codex" / "skill_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    with (log_dir / "codex_skill_runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def render_reaudit_delta(blocker: str, delta: str, prior: str) -> str:
    if not any([blocker, delta, prior]):
        return "No re-audit delta provided."
    lines = []
    if blocker:
        lines.append(f"Primary blocker: {blocker}")
    if prior:
        lines.append(f"Prior audit/package: {prior}")
    if delta:
        lines.append("")
        lines.append(delta)
    return "\n".join(lines)


def main() -> int:
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--out", default="AUDIT_PACKAGE.md")
    parser.add_argument("--goal", default="Review completed Codex skill optimization work.")
    parser.add_argument("--validation-file", default="")
    parser.add_argument("--notes-file", default="")
    parser.add_argument("--risks", default="No known unresolved high-risk issues.")
    parser.add_argument("--open-issues", default="None reported.")
    parser.add_argument("--reaudit-blocker", default="")
    parser.add_argument("--reaudit-delta", default="")
    parser.add_argument("--prior-audit", default="")
    parser.add_argument("--spec-status", default="N/A WITH REASON - Not provided.")
    parser.add_argument("--task-file", default="")
    parser.add_argument("--precheck-file", default="")
    parser.add_argument("--backlog-file", default="")
    parser.add_argument("--backlog-marker", default="")
    parser.add_argument("--manual-janus-evidence", default="N/A WITH REASON - No manual Janus check required or recorded.")
    parser.add_argument("--pipeline-completion", default="remaining tasks none; implementation complete yes")
    parser.add_argument("--only", action="append", default=[], help="Restrict git diff/status summary to these repo-relative paths.")
    parser.add_argument("--include", action="append", default=[], help="Artifact file or directory to inventory.")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = cwd / out

    changed, diff_summary = git_section(cwd, args.only)
    inventory = inventory_paths(args.include, cwd)
    validation = read_optional(args.validation_file) or "Validation evidence not provided."
    notes = read_optional(args.notes_file)
    reaudit = render_reaudit_delta(args.reaudit_blocker, args.reaudit_delta, args.prior_audit)
    task_excerpt = read_required_excerpt(args.task_file)
    precheck_excerpt = read_required_excerpt(args.precheck_file)
    backlog_excerpt = extract_markdown_section(args.backlog_file, args.backlog_marker)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    body = f"""# AUDIT_PACKAGE

Generated: {generated}

## Goal

{args.goal}

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: {args.spec_status}
- Task File: {args.task_file or "N/A WITH REASON - No task file provided."}
- Backlog Item: {args.backlog_marker or "N/A WITH REASON - No backlog marker provided."}
- Pre-Implementation Check: {args.precheck_file or "N/A WITH REASON - No precheck file provided."}
- Manual Janus Evidence: {args.manual_janus_evidence}
- Pipeline Completion Status: {args.pipeline_completion}

## Backlog Item

```text
{backlog_excerpt}
```

## Task Acceptance Scope

```text
{task_excerpt}
```

## Pre-Implementation Check

```text
{precheck_excerpt}
```

## Changed Files

```text
{changed}
```

## Artifact Inventory

```text
{inventory}
```

## Diff Summary

```text
{diff_summary}
```

## Validation

```text
{validation}
```

## Notes

{notes or "No additional notes provided."}

## Risks

{args.risks}

## Open Issues

{args.open_issues}

## Re-Audit Delta

{reaudit}

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: janus-final-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: {out}
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

If Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`. For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
"""
    new_bytes = body.encode("utf-8")
    existing_bytes = out.read_bytes() if out.exists() else b""
    reused_existing = existing_bytes == new_bytes
    if not reused_existing:
        out.write_text(body, encoding="utf-8")
    package_bytes = out.read_bytes() if out.exists() else new_bytes
    print(out)
    append_run_log(
        {
            "skill_name": "codex-audit-package-builder",
            "script": "build_audit_package.py",
            "status": "success",
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "metrics": {
                "output": str(out),
                "include_count": len(args.include),
                "reused_existing": reused_existing,
                "package_bytes": len(package_bytes),
                "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
                "reaudit": bool(args.reaudit_blocker or args.reaudit_delta or args.prior_audit),
                "only_count": len(args.only),
            },
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
