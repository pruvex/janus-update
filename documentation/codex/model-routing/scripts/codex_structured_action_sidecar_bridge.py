#!/usr/bin/env python3
"""Bridge one saved sidecar run package into builder -> executor flow."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
BUILDER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_request_builder.py"
EXECUTOR_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_executor.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def load_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge one saved sidecar run into builder -> executor flow.")
    parser.add_argument("--sidecar-run-dir", type=Path, required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--bridge-mode", choices=["draft", "patch"], default="draft")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--non-goal", action="append", dest="non_goals", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    sidecar_run_dir = args.sidecar_run_dir.resolve()
    summary_path = sidecar_run_dir / "summary.json"
    last_message_path = sidecar_run_dir / "last_message.md"
    git_diff_path = sidecar_run_dir / "git_diff.patch"
    changed_files_path = sidecar_run_dir / "changed_files.txt"
    if not summary_path.exists():
        raise SystemExit(f"summary.json missing in sidecar run dir: {sidecar_run_dir}")

    summary = load_json(summary_path)
    if summary.get("status") != "PASS":
        raise SystemExit(f"Sidecar run summary status must be PASS, got: {summary.get('status')}")
    if not summary.get("artifact_success"):
        raise SystemExit("Sidecar run summary requires artifact_success=true.")

    built_request_path = MODEL_ROUTING_DIR / "structured-action-fixtures" / f"{args.workflow_id}_built_from_sidecar.json"
    builder_command = ["python", str(BUILDER_PATH), "--workflow-id", args.workflow_id, "--skill-id", args.skill_id]
    if args.bridge_mode == "draft":
        if not last_message_path.exists():
            raise SystemExit(f"last_message.md missing in sidecar run dir: {sidecar_run_dir}")
        if not summary.get("last_message_present"):
            raise SystemExit("Sidecar run summary requires last_message_present=true for draft bridge mode.")
        builder_command.extend(
            [
                "--action-type",
                "draft_markdown",
                "--summary",
                args.summary,
                "--source-path",
                str(last_message_path),
                "--output-request-json",
                str(built_request_path),
            ]
        )
    else:
        if not git_diff_path.exists():
            raise SystemExit(f"git_diff.patch missing in sidecar run dir: {sidecar_run_dir}")
        if not changed_files_path.exists():
            raise SystemExit(f"changed_files.txt missing in sidecar run dir: {sidecar_run_dir}")
        changed_files = load_lines(changed_files_path)
        if not changed_files:
            raise SystemExit("changed_files.txt is empty for patch bridge mode.")
        builder_command.extend(
            [
                "--action-type",
                "propose_patch",
                "--summary",
                args.summary,
                "--source-path",
                str(git_diff_path),
                "--output-request-json",
                str(built_request_path),
            ]
        )
        for changed_file in changed_files:
            builder_command.extend(["--allowed-file", changed_file])
    for non_goal in args.non_goals:
        builder_command.extend(["--non-goal", non_goal])

    builder_result = run_command(builder_command)
    if builder_result.returncode != 0:
        raise SystemExit(f"Builder failed:\nSTDOUT:\n{builder_result.stdout}\nSTDERR:\n{builder_result.stderr}")

    executor_status = "SKIPPED"
    executor_stdout = ""
    executor_stderr = ""
    if args.execute:
        executor_result = run_command(
            [
                "python",
                str(EXECUTOR_PATH),
                "--request-json",
                str(built_request_path),
            ]
        )
        executor_stdout = executor_result.stdout
        executor_stderr = executor_result.stderr
        executor_status = "PASS" if executor_result.returncode == 0 else "FAIL"
        if executor_result.returncode != 0:
            raise SystemExit(f"Executor failed:\nSTDOUT:\n{executor_stdout}\nSTDERR:\n{executor_stderr}")

    print(
        json.dumps(
            {
                "status": "PASS",
                "bridge_mode": args.bridge_mode,
                "sidecar_run_dir": rel_repo(sidecar_run_dir),
                "built_request_json": rel_repo(built_request_path),
                "builder_status": "PASS",
                "executor_status": executor_status,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
