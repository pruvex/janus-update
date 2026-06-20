#!/usr/bin/env python3
"""Bounded helper for validated execution write-apply candidate flows."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "execution-write-apply-runs"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_choice(choice: str) -> str:
    value = choice.strip().lower()
    if value == "prompt":
        return "prompt"
    if value in {"local", "codex", "1"}:
        return "local"
    if value in {"delegated", "sidecar", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, delegated/2/sidecar")


def build_run_dir(workflow_id: str) -> Path:
    return RUN_ROOT / workflow_id


def prompt_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE GATE",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "Delegated",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded workspace-write execution candidate backed by an accepted proposal-first execution package and Codex-owned acceptance",
        "operator_prompt_lines": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded execution_write_apply_candidate Delegation-Pfad nutzen?",
        ],
        "boundaries": [
            "No delegated broad repo write authority",
            "No delegated test execution",
            "No delegated task completion claim",
            "Codex remains validation and acceptance owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex execution path. No delegated execution write-apply candidate path was used.",
    }


def validate_accepted_source(run_dir: Path) -> dict[str, Any]:
    input_path = run_dir / "input_package.json"
    validation_path = run_dir / "validation_summary.json"
    operator_path = run_dir / "operator_summary.json"
    delegated_result_path = run_dir / "delegated_result.md"
    summary_path = run_dir / "summary.json"
    diff_path = run_dir / "git_diff.patch"
    changed_files_path = run_dir / "changed_files.txt"
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    exit_code_path = run_dir / "exit_code.txt"

    issues: list[str] = []
    if not input_path.exists():
        issues.append("missing input_package.json")
    if not validation_path.exists():
        issues.append("missing validation_summary.json")
    if not operator_path.exists():
        issues.append("missing operator_summary.json")
    if not delegated_result_path.exists():
        issues.append("missing delegated_result.md")
    if not summary_path.exists():
        issues.append("missing summary.json")
    if not diff_path.exists():
        issues.append("missing git_diff.patch")
    if not changed_files_path.exists():
        issues.append("missing changed_files.txt")
    if not stdout_path.exists():
        issues.append("missing stdout.log")
    if not stderr_path.exists():
        issues.append("missing stderr.log")
    if not exit_code_path.exists():
        issues.append("missing exit_code.txt")

    input_payload: dict[str, Any] = load_json(input_path) if input_path.exists() else {}
    validation_payload: dict[str, Any] = load_json(validation_path) if validation_path.exists() else {}
    operator_payload: dict[str, Any] = load_json(operator_path) if operator_path.exists() else {}
    summary_payload: dict[str, Any] = load_json(summary_path) if summary_path.exists() else {}
    changed_files = []
    if changed_files_path.exists():
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    diff_text = diff_path.read_text(encoding="utf-8-sig") if diff_path.exists() else ""

    if input_payload.get("precheck_status") != "PRE-CHECK PASSED":
        issues.append("source precheck_status is not PRE-CHECK PASSED")
    allowed_files = input_payload.get("allowed_files")
    if not isinstance(allowed_files, list) or not allowed_files:
        issues.append("source allowed_files is empty")
    max_touched_files = input_payload.get("max_touched_files")
    if not isinstance(max_touched_files, int) or max_touched_files < 1:
        issues.append("source max_touched_files is invalid")
    if validation_payload.get("accepted_for_codex_patch_review") is not True:
        issues.append("accepted_for_codex_patch_review is not true")
    validation_status = validation_payload.get("status")
    if validation_status not in {None, "PASS"}:
        issues.append("validation_summary status is not PASS")
    validation_changed_files = validation_payload.get("changed_files")
    if summary_payload.get("status") != "PASS":
        issues.append("source summary status is not PASS")
    if not changed_files:
        issues.append("changed_files.txt is empty")
    if not diff_text.strip():
        issues.append("git_diff.patch is empty")
    if not isinstance(validation_changed_files, list) or not validation_changed_files:
        issues.append("source validation_summary changed_files is empty")
    else:
        if isinstance(allowed_files, list):
            for item in validation_changed_files:
                if item not in allowed_files:
                    issues.append(f"source changed file escapes allowlist: {item}")
        if isinstance(max_touched_files, int) and len(validation_changed_files) > max_touched_files:
            issues.append("source changed_files exceeds max_touched_files")
    if changed_files and isinstance(validation_changed_files, list) and changed_files != validation_changed_files:
        issues.append("changed_files.txt does not match validation_summary changed_files")
    if summary_payload.get("git_diff") and Path(str(summary_payload["git_diff"])).name != "git_diff.patch":
        issues.append("summary git_diff does not point to git_diff.patch")
    if summary_payload.get("changed_files") and Path(str(summary_payload["changed_files"])).name != "changed_files.txt":
        issues.append("summary changed_files does not point to changed_files.txt")
    if operator_payload.get("final_outcome") != "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW":
        issues.append("source final_outcome is not EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW")
    if operator_payload.get("validation_result") != "PASS":
        issues.append("source operator validation_result is not PASS")

    return {
        "input_path": str(input_path),
        "validation_path": str(validation_path),
        "operator_path": str(operator_path),
        "delegated_result_path": str(delegated_result_path),
        "summary_path": str(summary_path),
        "diff_path": str(diff_path),
        "changed_files_path": str(changed_files_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "exit_code_path": str(exit_code_path),
        "allowed_files": allowed_files,
        "max_touched_files": max_touched_files,
        "changed_files": changed_files,
        "issues": issues,
        "input_payload": input_payload,
        "validation_payload": validation_payload,
        "operator_payload": operator_payload,
        "summary_payload": summary_payload,
    }


def main_with_args(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded execution write apply candidate helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default="bounded workspace-write execution candidate / accepted proposal-first evidence path")
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"EXECUTION-WRITE-APPLY-CANDIDATE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
        )
        write_json(run_dir / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = local_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
        )
        write_json(run_dir / "operator_choice_local.json", result)
        output(result)
        return 0

    if args.accepted_source_run_dir is None:
        raise SystemExit("--accepted-source-run-dir is required for operator-choice delegated in local validation mode")

    source_run_dir = args.accepted_source_run_dir.resolve()
    validation = validate_accepted_source(source_run_dir)
    write_json(run_dir / "source_validation.json", validation)

    validation_pass = not validation["issues"]
    operator_summary = {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": args.task_label,
        "selected_path": "delegated_execution_write_apply_candidate",
        "normal_target_model": args.normal_target_model,
        "delegated_model_label": args.delegated_model_label,
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": (
            "EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_CODEX_ACCEPT_REJECT"
            if validation_pass
            else "EXECUTION_WRITE_APPLY_CANDIDATE_REJECT_AND_FALLBACK"
        ),
        "accepted_source_run_dir": str(source_run_dir),
        "source_validation_path": str(run_dir / "source_validation.json"),
        "operator_message": (
            "Delegated execution write-apply candidate is backed by an accepted proposal-first execution package with required validation artifacts present. Codex still owns the explicit accept-or-reject decision, any future live write approval, and final task acceptance."
            if validation_pass
            else "Accepted-source validation failed. Fallback to Codex-only execution is required."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_pass else 1


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
