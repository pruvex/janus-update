#!/usr/bin/env python3
"""Bounded helper for validated quickchange workspace-write apply flows."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "quickchange-apply-runs"


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
    if value in {"delegated", "sidecar", "openrouter", "or", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, openrouter/or/2/delegated/sidecar")


def build_run_dir(workflow_id: str) -> Path:
    return RUN_ROOT / workflow_id


def prompt_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "QUICKCHANGE WRITE APPLY GATE",
        "workflow_id": workflow_id,
        "skill": "janus-quickchange",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "OpenRouter",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded workspace-write quickchange with exact allowlist, exact file cap, and Codex-owned acceptance",
        "operator_prompt_lines": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded quickchange_write_apply OpenRouter-Pfad nutzen?",
        ],
        "boundaries": [
            "No production routing",
            "No canonical routing-table update",
            "No delegated Git or release authority",
            "Codex remains validation and acceptance owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "QUICKCHANGE WRITE APPLY RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-quickchange",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex quickchange apply path. No OpenRouter write path was used.",
    }


def validate_accepted_source(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "summary.json"
    validation_path = run_dir / "validation_summary.json"
    diff_path = run_dir / "git_diff.patch"
    changed_files_path = run_dir / "changed_files.txt"
    last_message_path = run_dir / "last_message.md"

    issues: list[str] = []
    if not summary_path.exists():
        issues.append("missing summary.json")
    if not validation_path.exists():
        issues.append("missing validation_summary.json")
    if not diff_path.exists():
        issues.append("missing git_diff.patch")
    if not changed_files_path.exists():
        issues.append("missing changed_files.txt")
    if not last_message_path.exists():
        issues.append("missing last_message.md")

    summary: dict[str, Any] = load_json(summary_path) if summary_path.exists() else {}
    validation: dict[str, Any] = load_json(validation_path) if validation_path.exists() else {}
    changed_files = []
    if changed_files_path.exists():
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    if summary.get("status") != "PASS":
        issues.append("summary status is not PASS")
    if validation.get("allowlist_ok") is not True:
        issues.append("allowlist_ok is not true")
    if validation.get("touched_file_cap_ok") is not True:
        issues.append("touched_file_cap_ok is not true")
    if validation.get("delete_rename_move_ok") is not True:
        issues.append("delete_rename_move_ok is not true")
    if not changed_files:
        issues.append("changed_files.txt is empty")

    return {
        "summary_path": str(summary_path),
        "validation_path": str(validation_path),
        "diff_path": str(diff_path),
        "changed_files_path": str(changed_files_path),
        "last_message_path": str(last_message_path),
        "changed_files": changed_files,
        "issues": issues,
        "summary": summary,
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded quickchange write apply helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default="bounded workspace-write sidecar / accepted evidence path")
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"QUICKCHANGE-WRITE-APPLY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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
        "summary_header": "QUICKCHANGE WRITE APPLY RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-quickchange",
        "task_label": args.task_label,
        "selected_path": "delegated_quickchange_write_apply",
        "normal_target_model": args.normal_target_model,
        "delegated_model_label": args.delegated_model_label,
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": (
            "QUICKCHANGE_WRITE_APPLY_READY_FOR_CODEX_ACCEPTANCE"
            if validation_pass
            else "QUICKCHANGE_WRITE_APPLY_REJECT_AND_FALLBACK"
        ),
        "accepted_source_run_dir": str(source_run_dir),
        "source_validation_path": str(run_dir / "source_validation.json"),
        "operator_message": (
            "Delegated quickchange write apply is backed by an accepted bounded workspace-write evidence package. Codex must still validate the diff and accept the final quickchange."
            if validation_pass
            else "Accepted-source validation failed. Fallback to Codex-only quickchange is required."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
