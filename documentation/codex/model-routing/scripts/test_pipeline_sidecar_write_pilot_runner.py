#!/usr/bin/env python3
"""Prompt/local/dry-run helper for the janus-test-pipeline test-artifact workspace-write pilot."""

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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def map_choice(choice: str) -> str:
    value = choice.strip().lower()
    if value == "prompt":
        return "prompt"
    if value in {"local", "codex", "1"}:
        return "local"
    if value in {"sidecar", "2"}:
        return "sidecar"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, sidecar/2")


def build_run_dir(workflow_id: str) -> Path:
    return MODEL_ROUTING_DIR / "sidecar-runs" / workflow_id


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def append_lines(path: Path, lines: list[str]) -> None:
    write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def prompt_summary(
    *,
    workflow_id: str,
    testspec_path: str,
    test_run_id: str,
    normal_target_model: str,
    sidecar_model: str,
    editable_paths: list[str],
) -> dict[str, Any]:
    return {
        "summary_header": "CODEX SIDECAR TEST-ARTIFACT WRITE GATE",
        "workflow_id": workflow_id,
        "skill": "janus-test-pipeline",
        "mode": "TESTSPEC_TO_TEST_PLAN",
        "testspec_path": testspec_path,
        "test_run_id": test_run_id,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "Sidecar",
        "sidecar_model_provider": f"Codex CLI sidecar / {sidecar_model}",
        "sandbox": "workspace-write",
        "editable_paths": editable_paths,
        "validation_after_run": [
            "validate-test-plan.mjs on generated plan",
            "node --check on generated runner",
            "validate-runner.mjs on plan plus generated runner",
        ],
        "abort_rules": [
            "Abort if any file outside exact output allowlist changes.",
            "Abort if any file in documentation/test-results changes.",
            "Abort if product code changes.",
            "Abort if generated outputs do not validate.",
        ],
        "boundaries": [
            "No live Playwright execution.",
            "No result JSON or result markdown generation.",
            "No product code edits.",
            "Codex App remains final reviewer and acceptance owner.",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, testspec_path: str, test_run_id: str, normal_target_model: str, sidecar_model: str) -> dict[str, Any]:
    return {
        "summary_header": "CODEX SIDECAR TEST-ARTIFACT WRITE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-test-pipeline",
        "mode": "TESTSPEC_TO_TEST_PLAN",
        "testspec_path": testspec_path,
        "test_run_id": test_run_id,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "sidecar_model_provider": f"Codex CLI sidecar / {sidecar_model}",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex test-artifact path. No sidecar write attempt was made.",
    }


def invoke_dry_run(
    *,
    run_directory: Path,
    prompt_path: Path,
    sidecar_model: str,
    editable_paths: list[str],
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
        "-MaxTouchedFiles",
        "2",
    ]
    if editable_paths:
        command.extend(["-EditablePath", ",".join(editable_paths)])
    return run_command(command, REPO_ROOT)


def validate_outputs(*, plan_path: Path, runner_path: Path, validation_dir: Path) -> dict[str, Any]:
    validation_dir.mkdir(parents=True, exist_ok=True)
    commands = [
        {
            "name": "validate_test_plan",
            "command": [
                "node",
                "tests/e2e/generator/validate-test-plan.mjs",
                "--plan",
                str(plan_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            ],
            "stdout_path": validation_dir / "validate_test_plan.stdout.log",
            "stderr_path": validation_dir / "validate_test_plan.stderr.log",
        },
        {
            "name": "node_check_generated_runner",
            "command": [
                "node",
                "--check",
                str(runner_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            ],
            "stdout_path": validation_dir / "node_check_generated_runner.stdout.log",
            "stderr_path": validation_dir / "node_check_generated_runner.stderr.log",
        },
        {
            "name": "validate_runner",
            "command": [
                "node",
                "tests/e2e/generator/validate-runner.mjs",
                "--plan",
                str(plan_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "--runner",
                str(runner_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            ],
            "stdout_path": validation_dir / "validate_runner.stdout.log",
            "stderr_path": validation_dir / "validate_runner.stderr.log",
        },
    ]

    results: list[dict[str, Any]] = []
    for item in commands:
        completed = run_command(item["command"], REPO_ROOT)
        write_text(item["stdout_path"], completed.stdout)
        write_text(item["stderr_path"], completed.stderr)
        results.append(
            {
                "name": item["name"],
                "command": item["command"],
                "exit_code": completed.returncode,
                "stdout_path": str(item["stdout_path"]),
                "stderr_path": str(item["stderr_path"]),
                "passed": completed.returncode == 0,
            }
        )

    return {
        "status": "PASS" if all(item["passed"] for item in results) else "FAIL",
        "checks": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Test-artifact workspace-write sidecar pilot helper.")
    parser.add_argument("--testspec-path", required=True)
    parser.add_argument("--test-run-id", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--prompt-path", type=Path, default=None)
    parser.add_argument("--sidecar-model", default="gpt-5.4")
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()

    choice = map_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"SIDECAR-TEST-ARTIFACT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    editable_paths = [
        f"documentation/test-runs/{args.test_run_id}_plan.json",
        f"documentation/test-runs/{args.test_run_id}_generated.spec.js",
        f"documentation/test-runs/{args.test_run_id}_skill2_handover.txt",
    ]

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            testspec_path=args.testspec_path,
            test_run_id=args.test_run_id,
            normal_target_model=args.normal_target_model,
            sidecar_model=args.sidecar_model,
            editable_paths=editable_paths,
        )
        write_json(run_dir / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = local_summary(
            workflow_id=workflow_id,
            testspec_path=args.testspec_path,
            test_run_id=args.test_run_id,
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
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SIDECAR_RUNNER_PATH),
            "-RunDirectory",
            str(run_dir),
            "-PromptPath",
            str(prompt_path),
            "-Model",
            args.sidecar_model,
            "-Sandbox",
            "workspace-write",
            "-ApprovalPolicy",
            "never",
            "-CaptureGitDiff",
            "-FailOnDeleteRenameMove",
            "-MaxTouchedFiles",
            "3",
            "-TimeoutSeconds",
            str(args.timeout_seconds),
            "-EditablePath",
            ",".join(editable_paths),
            "-Execute",
        ]
        completed = run_command(command, REPO_ROOT)
    else:
        completed = invoke_dry_run(
            run_directory=run_dir,
            prompt_path=prompt_path,
            sidecar_model=args.sidecar_model,
            editable_paths=editable_paths,
        )

    write_text(run_dir / "runner_stdout.txt", completed.stdout)
    write_text(run_dir / "runner_stderr.txt", completed.stderr)

    summary_path = run_dir / "summary.json"
    validation_path = run_dir / "validation_summary.json"
    if not summary_path.exists():
        output(
            {
                "summary_header": "CODEX SIDECAR TEST-ARTIFACT WRITE RESULT",
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
        "summary_header": "CODEX SIDECAR TEST-ARTIFACT WRITE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-test-pipeline",
        "mode": "TESTSPEC_TO_TEST_PLAN",
        "testspec_path": args.testspec_path,
        "test_run_id": args.test_run_id,
        "selected_path": "sidecar_workspace_write_live" if args.execute_live else "sidecar_workspace_write_dry_run",
        "validation_result": "PASS" if summary.get("status") in {"DRY_RUN", "PASS"} else "FAIL",
        "final_outcome": "LIVE_WRITE_ACCEPTED" if args.execute_live and summary.get("status") == "PASS" else "DRY_RUN_VALIDATED" if summary.get("status") == "DRY_RUN" else "LIVE_WRITE_INVALID" if args.execute_live else "DRY_RUN_INVALID",
        "runner_summary_path": str(summary_path),
        "validation_summary_path": str(validation_path),
        "allowlist_ok": validation_summary.get("allowlist_ok"),
        "touched_file_cap_ok": validation_summary.get("touched_file_cap_ok"),
        "delete_rename_move_ok": validation_summary.get("delete_rename_move_ok"),
        "operator_message": "Live delegated test-artifact write was attempted." if args.execute_live else "Dry-run only. No delegated test-artifact write was performed.",
    }

    if args.execute_live and result["validation_result"] == "PASS":
        plan_path = REPO_ROOT / f"documentation/test-runs/{args.test_run_id}_plan.json"
        runner_path = REPO_ROOT / f"documentation/test-runs/{args.test_run_id}_generated.spec.js"
        handover_path = REPO_ROOT / f"documentation/test-runs/{args.test_run_id}_skill2_handover.txt"
        existence_lines = [
            f"plan_exists={plan_path.exists()}",
            f"runner_exists={runner_path.exists()}",
            f"handover_exists={handover_path.exists()}",
        ]
        append_lines(run_dir / "generated_output_existence.txt", existence_lines)
        output_validation = validate_outputs(
            plan_path=plan_path,
            runner_path=runner_path,
            validation_dir=run_dir / "post_validation",
        )
        write_json(run_dir / "post_validation_summary.json", output_validation)
        result["post_validation_summary_path"] = str(run_dir / "post_validation_summary.json")
        result["post_validation_status"] = output_validation["status"]
        if output_validation["status"] != "PASS":
            result["validation_result"] = "FAIL"
            result["final_outcome"] = "LIVE_WRITE_POST_VALIDATION_FAILED"

    write_json(run_dir / "operator_summary.json", result)
    output(result)
    return 0 if result["validation_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
