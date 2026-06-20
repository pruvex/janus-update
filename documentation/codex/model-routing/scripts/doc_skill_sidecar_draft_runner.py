#!/usr/bin/env python3
"""Operator-invoked sidecar draft runner for bounded janus-documentation-update tasks.

This helper is for local Codex CLI sidecar delegation only.
It does not enable production routing, OpenRouter routing, or write-capable sidecar use.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SIDECAR_RUNNER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_sidecar_skill_runner.ps1"
SIDECAR_BRIDGE_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_sidecar_bridge.py"
DEFAULT_WORKING_DIRECTORY = REPO_ROOT


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def output_summary(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def norm(text: str) -> str:
    return text.strip().lower()


def map_choice(choice: str) -> str:
    normalized = norm(choice)
    if normalized in {"prompt"}:
        return "prompt"
    if normalized in {"local", "codex", "1"}:
        return "local"
    if normalized in {"sidecar", "2"}:
        return "sidecar"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, or sidecar/2")


def build_run_directory(workflow_id: str) -> Path:
    return MODEL_ROUTING_DIR / "sidecar-runs" / workflow_id


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def prompt_mode_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    sidecar_model: str,
    sandbox: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    return {
        "summary_header": "CODEX SIDECAR DELEGATION GATE",
        "workflow_id": workflow_id,
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "skill": "janus-documentation-update",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "Sidecar",
        "sidecar_model_provider": f"Codex CLI sidecar / {sidecar_model}",
        "sandbox": sandbox,
        "timeout_seconds": timeout_seconds,
        "estimated_cost_quota_impact": (
            "separate local Codex CLI run; direct dollar cost N/A in current local path; "
            "main value is shifting draft work out of the main Codex App loop"
        ),
        "expected_delegation_value": "non-binding documentation draft only",
        "codex_app_review_after_sidecar": (
            "Codex App reviews the draft, decides acceptance, and performs any binding documentation writes locally."
        ),
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
        "operator_prompt_lines": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 das ueber den bounded Delegation-Dispatcher als read-only, non-binding Draft laufen lassen?",
        ],
        "boundaries": [
            "No production routing",
            "No Git or release authority",
            "No file writes by the sidecar",
            "Codex App remains reviewer and governance owner",
        ],
    }


def local_mode_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    sidecar_model: str,
) -> dict[str, Any]:
    return {
        "summary_header": "CODEX SIDECAR DELEGATION RESULT",
        "workflow_id": workflow_id,
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "skill": "janus-documentation-update",
        "normal_target_model": normal_target_model,
        "sidecar_model_provider": f"Codex CLI sidecar / {sidecar_model}",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_result_lines": [
            "Ergebnis: Codex lokal ausgewaehlt",
            "Tatsaechliche Kosten: N/A (kein Sidecar-Lauf)",
        ],
        "operator_message": "Operator chose the normal Codex path. No sidecar run was made.",
    }


def invoke_sidecar(
    *,
    run_directory: Path,
    prompt_path: Path,
    model: str,
    sandbox: str,
    timeout_seconds: int,
    working_directory: Path,
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
        model,
        "-Sandbox",
        sandbox,
        "-ApprovalPolicy",
        "never",
        "-TimeoutSeconds",
        str(timeout_seconds),
        "-Execute",
    ]
    return run_command(command, working_directory)


def invoke_structured_bridge(
    *,
    run_directory: Path,
    workflow_id: str,
    task_label: str,
) -> subprocess.CompletedProcess[str]:
    command = [
        "python",
        str(SIDECAR_BRIDGE_PATH),
        "--sidecar-run-dir",
        str(run_directory),
        "--workflow-id",
        f"{workflow_id}-STRUCTURED",
        "--skill-id",
        "janus-documentation-update",
        "--summary",
        f"Bridge accepted sidecar documentation draft into structured action flow for: {task_label}",
        "--non-goal",
        "No direct repo authority update",
        "--non-goal",
        "No production routing activation",
        "--execute",
    ]
    return run_command(command, REPO_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded sidecar draft runner for janus-documentation-update.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--prompt-path", type=Path, default=None)
    parser.add_argument("--sidecar-model", default="gpt-5.4")
    parser.add_argument("--sandbox", choices=["read-only"], default="read-only")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--working-directory", type=Path, default=DEFAULT_WORKING_DIRECTORY)
    parser.add_argument("--structured-review-flow", action="store_true")
    args = parser.parse_args()

    choice = map_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"SIDECAR-DOC-FLOW-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_directory = build_run_directory(workflow_id)
    run_directory.mkdir(parents=True, exist_ok=True)

    if choice == "prompt":
        summary = prompt_mode_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            sidecar_model=args.sidecar_model,
            sandbox=args.sandbox,
            timeout_seconds=args.timeout_seconds,
        )
        write_json(run_directory / "operator_choice_prompt.json", summary)
        output_summary(summary)
        return 0

    if choice == "local":
        summary = local_mode_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            sidecar_model=args.sidecar_model,
        )
        write_json(run_directory / "operator_choice_local.json", summary)
        output_summary(summary)
        return 0

    if args.prompt_path is None:
        raise SystemExit("--prompt-path is required for operator-choice sidecar")

    prompt_path = args.prompt_path.resolve()
    if not prompt_path.exists():
        raise SystemExit(f"Prompt path does not exist: {prompt_path}")

    wrapper_result = invoke_sidecar(
        run_directory=run_directory,
        prompt_path=prompt_path,
        model=args.sidecar_model,
        sandbox=args.sandbox,
        timeout_seconds=args.timeout_seconds,
        working_directory=args.working_directory.resolve(),
    )

    write_text(run_directory / "sidecar_runner_stdout.txt", wrapper_result.stdout)
    write_text(run_directory / "sidecar_runner_stderr.txt", wrapper_result.stderr)

    summary_path = run_directory / "summary.json"
    last_message_path = run_directory / "last_message.md"
    if not summary_path.exists():
        output_summary(
            {
                "summary_header": "CODEX SIDECAR DELEGATION RESULT",
                "workflow_id": workflow_id,
                "task_label": args.task_label,
                "selected_path": "sidecar_failed",
                "validation_result": "FAIL",
                "final_outcome": "SIDECAR_SUMMARY_MISSING",
                "operator_message": "Sidecar runner did not produce summary.json.",
            }
        )
        return 1

    runner_summary = load_json(summary_path)
    last_message = last_message_path.read_text(encoding="utf-8-sig").strip() if last_message_path.exists() else ""
    status = runner_summary.get("status")
    if status != "PASS" or not last_message:
        output_summary(
            {
                "summary_header": "CODEX SIDECAR DELEGATION RESULT",
                "workflow_id": workflow_id,
                "task_label": args.task_label,
                "selected_path": "sidecar_failed",
                "validation_result": "FAIL",
                "final_outcome": "SIDECAR_DRAFT_NOT_ACCEPTED",
                "runner_summary_path": str(summary_path),
                "last_message_path": str(last_message_path),
                "operator_message": "Sidecar run completed without an accepted PASS draft result.",
            }
        )
        return 1

    result = {
        "summary_header": "CODEX SIDECAR DELEGATION RESULT",
        "workflow_id": workflow_id,
        "task_label": args.task_label,
        "selected_path": "sidecar_read_only_draft",
        "skill": "janus-documentation-update",
        "normal_target_model": args.normal_target_model,
        "sidecar_model_provider": f"Codex CLI sidecar / {args.sidecar_model}",
        "sandbox": args.sandbox,
        "timeout_seconds": args.timeout_seconds,
        "validation_result": "PASS",
        "final_outcome": "SIDECAR_DRAFT_ACCEPTED_FOR_REVIEW",
        "runner_summary_path": str(summary_path),
        "last_message_path": str(last_message_path),
        "operator_result_lines": [
            "Ergebnis: Sidecar-Draft erfolgreich",
            "Route: bounded Delegation-Dispatcher -> documentation_draft",
            "Tatsaechliche Kosten: N/A (lokaler Codex CLI Sidecar-Pfad)",
        ],
        "operator_message": (
            "Read-only sidecar draft completed. Codex App must still review and perform any binding documentation writes locally."
        ),
    }

    if args.structured_review_flow:
        bridge_result = invoke_structured_bridge(
            run_directory=run_directory,
            workflow_id=workflow_id,
            task_label=args.task_label,
        )
        write_text(run_directory / "structured_bridge_stdout.txt", bridge_result.stdout)
        write_text(run_directory / "structured_bridge_stderr.txt", bridge_result.stderr)
        if bridge_result.returncode != 0:
            result["validation_result"] = "FAIL"
            result["final_outcome"] = "SIDECAR_DRAFT_ACCEPTED_BUT_STRUCTURED_BRIDGE_FAILED"
            result["structured_bridge_status"] = "FAIL"
            result["operator_message"] = (
                "Sidecar draft was accepted, but the follow-up structured review flow failed before producing a reviewed local artifact."
            )
            write_json(run_directory / "operator_summary.json", result)
            output_summary(result)
            return 1

        bridge_summary = json.loads(bridge_result.stdout)
        result["structured_bridge_status"] = "PASS"
        result["structured_bridge_summary"] = bridge_summary
        result["final_outcome"] = "SIDECAR_DRAFT_ACCEPTED_AND_STRUCTURED_REVIEW_READY"
        result["operator_result_lines"] = [
            "Ergebnis: Sidecar-Draft erfolgreich",
            "Route: bounded Delegation-Dispatcher -> documentation_draft -> structured review",
            "Structured Review Flow: Builder -> Executor erfolgreich",
            "Tatsaechliche Kosten: N/A (lokaler Codex CLI Sidecar-Pfad)",
        ]
        result["operator_message"] = (
            "Read-only sidecar draft completed and was converted into a structured local review artifact. Codex App still owns any binding documentation write."
        )

    write_json(run_directory / "operator_summary.json", result)
    output_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
