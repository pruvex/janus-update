#!/usr/bin/env python3
"""Prompt/local helper for the janus-quickchange workspace-write sidecar pilot."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SIDECAR_RUNNER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_sidecar_skill_runner.ps1"
SIDECAR_BRIDGE_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_sidecar_bridge.py"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def normalize_choice(choice: str) -> str:
    value = choice.strip().lower()
    if value == "prompt":
        return "prompt"
    if value in {"local", "codex", "1"}:
        return "local"
    if value in {"sidecar", "openrouter", "or", "2"}:
        return "sidecar"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, openrouter/or/2/sidecar")


def build_run_dir(workflow_id: str) -> Path:
    return MODEL_ROUTING_DIR / "sidecar-runs" / workflow_id


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def prompt_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    sidecar_model: str,
    editable_paths: list[str],
    max_touched_files: int,
    diff_size_cap: str,
) -> dict[str, Any]:
    return {
        "summary_header": "CODEX SIDECAR WRITE GATE",
        "workflow_id": workflow_id,
        "skill": "janus-quickchange",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "OpenRouter",
        "sidecar_model_provider": f"OpenRouter sidecar / {sidecar_model}",
        "sandbox": "workspace-write",
        "editable_paths": editable_paths,
        "max_touched_files": max_touched_files,
        "diff_size_cap": diff_size_cap,
        "validation_after_run": "Codex App checks changed files, patch, and local validation before acceptance.",
        "abort_rules": [
            "Abort if changed file falls outside allowlist.",
            "Abort if touched file count exceeds cap.",
            "Abort if delete, rename, or move appears.",
            "Abort if validation fails locally.",
        ],
        "boundaries": [
            "No Git commands by the sidecar.",
            "No release or routing authority.",
            "No backlog, CURRENT_STATE, or registry authority.",
            "Codex App remains final reviewer and acceptance owner.",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, sidecar_model: str) -> dict[str, Any]:
    return {
        "summary_header": "CODEX SIDECAR WRITE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-quickchange",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "sidecar_model_provider": f"Codex CLI sidecar / {sidecar_model}",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex quickchange path. No OpenRouter write attempt was made.",
    }


def invoke_dry_run(
    *,
    run_directory: Path,
    prompt_path: Path,
    sidecar_model: str,
    editable_paths: list[str],
    max_touched_files: int,
) -> subprocess.CompletedProcess[str]:
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SIDECAR_RUNNER_PATH),
        "-RunDirectory",
        str(run_directory),
        "-PromptPath",
        str(prompt_path),
        "-Model",
        sidecar_model,
        "-Sandbox",
        "workspace-write",
        "-ApprovalPolicy",
        "never",
        "-CaptureGitDiff",
        "-FailOnDeleteRenameMove",
    ]
    if max_touched_files > 0:
        command.extend(["-MaxTouchedFiles", str(max_touched_files)])
    if editable_paths:
        command.extend(["-EditablePath", ",".join(editable_paths)])
    return run_command(command, REPO_ROOT)


def invoke_live_run(
    *,
    run_directory: Path,
    prompt_path: Path,
    sidecar_model: str,
    editable_paths: list[str],
    max_touched_files: int,
) -> subprocess.CompletedProcess[str]:
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SIDECAR_RUNNER_PATH),
        "-RunDirectory",
        str(run_directory),
        "-PromptPath",
        str(prompt_path),
        "-Model",
        sidecar_model,
        "-Sandbox",
        "workspace-write",
        "-ApprovalPolicy",
        "never",
        "-CaptureGitDiff",
        "-FailOnDeleteRenameMove",
        "-Execute",
    ]
    if max_touched_files > 0:
        command.extend(["-MaxTouchedFiles", str(max_touched_files)])
    if editable_paths:
        command.extend(["-EditablePath", ",".join(editable_paths)])
    return run_command(command, REPO_ROOT)


def invoke_structured_bridge(*, run_directory: Path, workflow_id: str, task_label: str) -> subprocess.CompletedProcess[str]:
    command = [
        "python",
        str(SIDECAR_BRIDGE_PATH),
        "--sidecar-run-dir",
        str(run_directory),
        "--workflow-id",
        f"{workflow_id}-STRUCTURED",
        "--skill-id",
        "janus-quickchange",
        "--bridge-mode",
        "patch",
        "--summary",
        f"Bridge accepted quickchange patch proposal into structured review flow for: {task_label}",
        "--non-goal",
        "No auto apply",
        "--non-goal",
        "No repo authority update",
        "--execute",
    ]
    return run_command(command, REPO_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Quickchange workspace-write sidecar pilot helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--prompt-path", type=Path, default=None)
    parser.add_argument("--sidecar-model", default="gpt-5.4")
    parser.add_argument("--editable-path", action="append", default=[])
    parser.add_argument("--max-touched-files", type=int, default=3)
    parser.add_argument("--diff-size-cap", default="small quickchange diff only")
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--structured-review-flow", action="store_true")
    parser.add_argument("--structured-review-source-run-dir", type=Path, default=None)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"SIDECAR-QUICKCHANGE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            sidecar_model=args.sidecar_model,
            editable_paths=args.editable_path,
            max_touched_files=args.max_touched_files,
            diff_size_cap=args.diff_size_cap,
        )
        write_json(run_dir / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = local_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            sidecar_model=args.sidecar_model,
        )
        write_json(run_dir / "operator_choice_local.json", result)
        output(result)
        return 0

    if args.prompt_path is None:
        raise SystemExit("--prompt-path is required for operator-choice sidecar")
    prompt_path = args.prompt_path.resolve()
    if not prompt_path.exists():
        raise SystemExit(f"Prompt path does not exist: {prompt_path}")

    if args.execute_live:
        completed = invoke_live_run(
            run_directory=run_dir,
            prompt_path=prompt_path,
            sidecar_model=args.sidecar_model,
            editable_paths=args.editable_path,
            max_touched_files=args.max_touched_files,
        )
    else:
        completed = invoke_dry_run(
            run_directory=run_dir,
            prompt_path=prompt_path,
            sidecar_model=args.sidecar_model,
            editable_paths=args.editable_path,
            max_touched_files=args.max_touched_files,
        )

    write_text(run_dir / "runner_stdout.txt", completed.stdout)
    write_text(run_dir / "runner_stderr.txt", completed.stderr)

    summary_path = run_dir / "summary.json"
    validation_path = run_dir / "validation_summary.json"
    if not summary_path.exists():
        output(
            {
                "summary_header": "CODEX SIDECAR WRITE RESULT",
                "workflow_id": workflow_id,
                "selected_path": "sidecar_dry_run_failed",
                "validation_result": "FAIL",
                "final_outcome": "SUMMARY_MISSING",
            }
        )
        return 1

    summary = load_json(summary_path)
    validation_summary = load_json(validation_path) if validation_path.exists() else {}
    result = {
        "summary_header": "CODEX SIDECAR WRITE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-quickchange",
        "task_label": args.task_label,
        "selected_path": "sidecar_workspace_write_live" if args.execute_live else "sidecar_workspace_write_dry_run",
        "validation_result": "PASS" if summary.get("status") in {"DRY_RUN", "PASS"} else "FAIL",
        "final_outcome": "LIVE_WRITE_ACCEPTED" if args.execute_live and summary.get("status") == "PASS" else "DRY_RUN_VALIDATED" if summary.get("status") == "DRY_RUN" else "LIVE_WRITE_INVALID" if args.execute_live else "DRY_RUN_INVALID",
        "runner_summary_path": str(summary_path),
        "validation_summary_path": str(validation_path),
        "allowlist_ok": validation_summary.get("allowlist_ok"),
        "touched_file_cap_ok": validation_summary.get("touched_file_cap_ok"),
        "delete_rename_move_ok": validation_summary.get("delete_rename_move_ok"),
        "operator_message": "Live delegated quickchange write was attempted." if args.execute_live else "Dry-run only. No delegated write execution was performed.",
    }

    if args.structured_review_flow and result["validation_result"] == "PASS":
        bridge_source_run_dir = args.structured_review_source_run_dir.resolve() if args.structured_review_source_run_dir else None
        if bridge_source_run_dir is None:
            result["structured_bridge_status"] = "SKIPPED"
            result["operator_message"] = (
                "Dry-run succeeded. Structured patch review was not started because this helper needs --structured-review-source-run-dir pointing to an accepted PASS sidecar write package."
            )
        else:
            bridge_result = invoke_structured_bridge(
                run_directory=bridge_source_run_dir,
                workflow_id=workflow_id,
                task_label=args.task_label,
            )
            write_text(run_dir / "structured_bridge_stdout.txt", bridge_result.stdout)
            write_text(run_dir / "structured_bridge_stderr.txt", bridge_result.stderr)
            if bridge_result.returncode != 0:
                result["validation_result"] = "FAIL"
                result["final_outcome"] = "DRY_RUN_VALIDATED_BUT_STRUCTURED_BRIDGE_FAILED"
                result["structured_bridge_status"] = "FAIL"
                result["operator_message"] = "Dry-run succeeded, but the structured patch review flow failed."
            else:
                result["structured_bridge_status"] = "PASS"
                result["structured_bridge_summary"] = load_json(run_dir / "structured_bridge_stdout.txt")
                result["final_outcome"] = "DRY_RUN_VALIDATED_AND_STRUCTURED_REVIEW_READY"
                result["operator_message"] = "Dry-run succeeded and the structured patch review flow captured the proposed patch for Codex review."
    write_json(run_dir / "operator_summary.json", result)
    output(result)
    return 0 if result["validation_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
