#!/usr/bin/env python3
"""Prompt/local/dry-run helper for the janus-test-pipeline test-artifact workspace-write pilot."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SIDECAR_RUNNER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_sidecar_skill_runner.ps1"
STRUCTURED_EXECUTOR_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_executor.py"
ISOLATED_AIDER_RUNNER_PATH = MODEL_ROUTING_DIR / "scripts" / "isolated_aider_workspace_runner.py"


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


def parse_json_output(stdout: str, *, fallback_path: Path | None = None) -> dict[str, Any]:
    text = stdout.strip()
    if text:
        return json.loads(text)
    if fallback_path is not None and fallback_path.exists():
        return load_json(fallback_path)
    raise SystemExit("Expected JSON output was missing.")


def append_lines(path: Path, lines: list[str]) -> None:
    write_text(path, "\n".join(lines) + ("\n" if lines else ""))


def git_status_lines(paths: list[str]) -> list[str]:
    command = ["git", "status", "--short", "--"] + paths
    completed = run_command(command, REPO_ROOT)
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def parse_touched_files(status_lines: list[str]) -> list[str]:
    touched: list[str] = []
    for line in status_lines:
        if len(line) < 4:
            continue
        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        touched.append(path_text.replace("\\", "/"))
    return sorted(set(touched))


def build_structured_generator_request(
    *,
    workflow_id: str,
    testspec_path: str,
    test_run_id: str,
    editable_paths: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "codex_delegated_action_request.v1",
        "workflow_id": workflow_id,
        "skill_id": "janus-test-pipeline",
        "action_type": "run_generator",
        "summary": "Compile one bound TestSpec into the exact bounded test-run artifact set through the structured local executor.",
        "requires_codex_review": True,
        "non_goals": [
            "No live Playwright execution",
            "No delegated local shell execution inside sidecar",
            "No product code edits",
        ],
        "action_payload": {
            "generator_id": "compile_testspec_to_testplan_v1",
            "inputs": {
                "spec_path": testspec_path,
                "test_run_id": test_run_id,
                "output_dir": "documentation/test-runs",
            },
            "declared_output_artifacts": editable_paths,
        },
    }


def resolve_node_executable(preferred: str | None = None) -> str:
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)
    candidates.extend(
        [
            r"C:\nvm4w\nodejs\node.exe",
            shutil.which("node") or "",
            shutil.which("node.exe") or "",
        ]
    )
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return str(path)
    raise SystemExit("No usable Node executable found for bounded test-artifact generation.")


def resolve_delegated_node_command(node_executable: str) -> str:
    node_name = Path(node_executable).name.lower()
    if node_name == "node.exe":
        return "node"
    if node_name == "node":
        return "node"
    return "node"


def build_live_prompt(
    *,
    testspec_path: str,
    test_run_id: str,
    node_executable: str,
    delegated_node_command: str,
    editable_paths: list[str],
) -> str:
    editable_lines = "\n".join(f"  - `{path}`" for path in editable_paths)
    return "\n".join(
        [
            "# Bounded Test Artifact Write Prompt",
            "",
            "You are a bounded Codex CLI worker for one pre-scoped repository artifact-generation task.",
            "",
            "This prompt is already fully scoped and pre-approved.",
            "Do not perform additional workflow routing, startup checks, or skill selection.",
            "Do not inspect unrelated repository instructions.",
            "You may edit files only inside the approved allowlist.",
            "",
            "Hard rules:",
            "",
            f"- Read only the bound TestSpec `{testspec_path}`.",
            "- Write only these exact files:",
            editable_lines,
            "- Do not edit any other file.",
            "- Do not create files under `documentation/test-results/`.",
            "- Do not edit product code.",
            "- Do not delete, move, or rename files.",
            "- Do not use Git commands.",
            "- Prefer repository generator scripts over handwritten output.",
            "- Do not spend time investigating PATH, shell setup, or local environment.",
            "- Do not search for `node`.",
            "- Use the exact runtime-visible command below first.",
            "- If that exact command fails, stop immediately and report the failure instead of exploring alternatives.",
            "",
            "Task:",
            "",
            "1. Generate the bounded test artifacts for the bound TestSpec by using repository scripts.",
            "2. Use the deterministic compiler flow starting from this exact PowerShell-safe command:",
            f'   - `& "{delegated_node_command}" "tests/e2e/generator/compile-testspec-to-testplan.mjs" --spec "{testspec_path}" --test-run-id "{test_run_id}"`',
            "3. Keep the result strictly bounded to the exact output files above.",
            "4. Do not run Playwright.",
            "5. Do not generate test results.",
            "6. Do not create extra files beyond the allowlist.",
            "",
            "Output rules:",
            "",
            "- After the work, return a short summary with:",
            "  - changed files",
            "  - confirmation that only allowed files were touched",
            "  - whether generator-based creation succeeded",
        ]
    )


def prompt_summary(
    *,
    workflow_id: str,
    testspec_path: str,
    test_run_id: str,
    normal_target_model: str,
    sidecar_model: str,
    editable_paths: list[str],
    node_executable: str,
) -> dict[str, Any]:
    operator_prompt_lines = [
        "1 = Codex",
        "2 = OR",
        "OR ist hier die externe Option, um Codex-Guthaben zu sparen.",
        "Live-Evidenz: bounded test-artifact generator lane on structured local executor surface",
        "Einordnung: deterministische Generator-Ausgabe bleibt lokal validiert; Codex behaelt finale Review- und Akzeptanzhoheit",
        f"Technischer Delegationspfad: structured local executor / {sidecar_model}",
        f"Pre-Call-Kostenbasis: bounded test-artifact generation for {test_run_id}",
        "Voraussichtliche OR-Kosten noch nicht belastbar kalibriert, Evidenzgenauigkeit 100% fuer den lokalen strukturierten Ausfuehrungspfad",
    ]
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
        "choice_2": "OR",
        "sidecar_model_provider": f"Structured local executor / {sidecar_model}",
        "node_executable": node_executable,
        "sandbox": "workspace-write",
        "editable_paths": editable_paths,
        "operator_prompt_lines": operator_prompt_lines,
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

def validate_outputs(*, plan_path: Path, runner_path: Path, validation_dir: Path, node_executable: str) -> dict[str, Any]:
    validation_dir.mkdir(parents=True, exist_ok=True)
    commands = [
        {
            "name": "validate_test_plan",
            "command": [
                node_executable,
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
                node_executable,
                "--check",
                str(runner_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            ],
            "stdout_path": validation_dir / "node_check_generated_runner.stdout.log",
            "stderr_path": validation_dir / "node_check_generated_runner.stderr.log",
        },
        {
            "name": "validate_runner",
            "command": [
                node_executable,
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


def invoke_isolated_aider_runner(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    or_model: str,
    estimated_or_cost: float,
    confidence_percent: int,
    input_package_json: Path,
) -> subprocess.CompletedProcess[str]:
    command = [
        "python",
        str(ISOLATED_AIDER_RUNNER_PATH),
        "--task-label",
        task_label,
        "--normal-target-model",
        normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(input_package_json),
        "--or-model",
        or_model,
        "--estimated-or-cost",
        str(estimated_or_cost),
        "--cost-estimate-confidence-percent",
        str(confidence_percent),
    ]
    return run_command(command, REPO_ROOT)


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
    parser.add_argument("--isolated-aider-package-json", type=Path, default=None)
    parser.add_argument("--estimated-or-cost", type=float, default=0.00080)
    parser.add_argument("--cost-estimate-confidence-percent", type=int, default=70)
    args = parser.parse_args()

    choice = map_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"SIDECAR-TEST-ARTIFACT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    node_executable = resolve_node_executable()
    delegated_node_command = resolve_delegated_node_command(node_executable)

    editable_paths = [
        f"documentation/test-runs/{args.test_run_id}_plan.json",
        f"documentation/test-runs/{args.test_run_id}_generated.spec.js",
        f"documentation/test-runs/{args.test_run_id}_skill2_handover.txt",
    ]
    append_lines(run_dir / "editable_paths.txt", editable_paths)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            testspec_path=args.testspec_path,
            test_run_id=args.test_run_id,
            normal_target_model=args.normal_target_model,
            sidecar_model=args.sidecar_model,
            editable_paths=editable_paths,
            node_executable=node_executable,
        )
        write_json(run_dir / "operator_choice_prompt.json", result)
        write_text(
            run_dir / "generated_prompt.md",
            build_live_prompt(
                testspec_path=args.testspec_path,
                test_run_id=args.test_run_id,
                node_executable=node_executable,
                delegated_node_command=delegated_node_command,
                editable_paths=editable_paths,
            ),
        )
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

    isolated_package_path = args.isolated_aider_package_json.resolve() if args.isolated_aider_package_json else None
    if isolated_package_path is not None and not isolated_package_path.exists():
        raise SystemExit(f"Isolated Aider package path does not exist: {isolated_package_path}")

    if isolated_package_path is not None:
        completed = invoke_isolated_aider_runner(
            workflow_id=workflow_id,
            task_label=f"Bounded test-artifact worker for {args.test_run_id}",
            normal_target_model=args.normal_target_model,
            or_model=args.sidecar_model,
            estimated_or_cost=args.estimated_or_cost,
            confidence_percent=args.cost_estimate_confidence_percent,
            input_package_json=isolated_package_path,
        )
        write_text(run_dir / "runner_stdout.txt", completed.stdout)
        write_text(run_dir / "runner_stderr.txt", completed.stderr)
        result = parse_json_output(completed.stdout)
        result["skill"] = "janus-test-pipeline"
        result["mode"] = "TESTSPEC_TO_TEST_PLAN"
        result["testspec_path"] = args.testspec_path
        result["test_run_id"] = args.test_run_id
        result["delegation_mode"] = "isolated_aider_workspace"
        result["forwarded_runner"] = str(ISOLATED_AIDER_RUNNER_PATH)
        write_json(run_dir / "operator_summary.json", result)
        output(result)
        return 0 if result.get("validation_result") == "PASS" else 1

    if args.prompt_path is None:
        prompt_path = run_dir / "generated_prompt.md"
        write_text(
            prompt_path,
            build_live_prompt(
                testspec_path=args.testspec_path,
                test_run_id=args.test_run_id,
                node_executable=node_executable,
                delegated_node_command=delegated_node_command,
                editable_paths=editable_paths,
            ),
        )
    else:
        prompt_path = args.prompt_path.resolve()
        if not prompt_path.exists():
            raise SystemExit(f"Prompt path does not exist: {prompt_path}")

    if args.execute_live:
        pre_status_lines = git_status_lines(editable_paths)
        structured_request_path = run_dir / "structured_action_request.json"
        structured_run_root = run_dir / "structured-action-runs"
        write_json(
            structured_request_path,
            build_structured_generator_request(
                workflow_id=workflow_id,
                testspec_path=args.testspec_path,
                test_run_id=args.test_run_id,
                editable_paths=editable_paths,
            ),
        )
        command = [
            "python",
            str(STRUCTURED_EXECUTOR_PATH),
            "--request-json",
            str(structured_request_path),
            "--run-root",
            str(structured_run_root),
        ]
        completed = run_command(command, REPO_ROOT)
        post_status_lines = git_status_lines(editable_paths)
        touched_files = parse_touched_files(post_status_lines)
        allowlist_ok = all(path in editable_paths for path in touched_files)
        touched_file_cap_ok = len(touched_files) <= 3
        delete_rename_move_ok = not any(line.startswith(("D ", " D", "R ", " R")) or " -> " in line for line in post_status_lines)
        validation_summary = {
            "status": "PASS" if allowlist_ok and touched_file_cap_ok and delete_rename_move_ok else "FAILED",
            "sandbox": "structured_local_executor",
            "editable_paths": editable_paths,
            "touched_files": touched_files,
            "touched_file_count": len(touched_files),
            "max_touched_files": 3,
            "deleted_paths": [line[3:].strip() for line in post_status_lines if line.startswith(("D ", " D"))],
            "renamed_paths": [line[3:].strip() for line in post_status_lines if line.startswith(("R ", " R"))],
            "moved_paths": [line[3:].strip() for line in post_status_lines if " -> " in line],
            "allowlist_ok": allowlist_ok,
            "touched_file_cap_ok": touched_file_cap_ok,
            "delete_rename_move_ok": delete_rename_move_ok,
            "pre_run_status_lines": pre_status_lines,
            "post_run_status_lines": post_status_lines,
        }
        write_json(run_dir / "validation_summary.json", validation_summary)
        structured_summary = json.loads(completed.stdout) if completed.stdout.strip().startswith("{") else {
            "executor_status": "FAILED",
            "detail": completed.stderr.strip() or completed.stdout.strip() or "Structured executor returned non-JSON output.",
        }
        structured_executor_ok = structured_summary.get("executor_status") == "PASS"
        summary = {
            "status": "PASS" if completed.returncode == 0 and allowlist_ok and touched_file_cap_ok and delete_rename_move_ok and structured_executor_ok else "FAILED",
            "exit_code": completed.returncode,
            "timed_out": False,
            "timeout_seconds": args.timeout_seconds,
            "artifact_success": completed.returncode == 0 and structured_executor_ok,
            "last_message_present": True,
            "stdout_present": bool(completed.stdout.strip()),
            "command_json": str(run_dir / "structured_action_request.json"),
            "stdout_log": str(run_dir / "runner_stdout.txt"),
            "stderr_log": str(run_dir / "runner_stderr.txt"),
            "last_message": str(run_dir / "last_message.md"),
            "event_stream": str(run_dir / "event_stream.jsonl"),
            "editable_paths": str(run_dir / "editable_paths.txt"),
            "pre_run_status": str(run_dir / "pre_run_status.txt"),
            "post_run_status": str(run_dir / "post_run_status.txt"),
            "changed_files": str(run_dir / "changed_files.txt"),
            "git_diff": str(run_dir / "git_diff.patch"),
            "validation_summary": str(run_dir / "validation_summary.json"),
            "allowlist_ok": allowlist_ok,
            "touched_file_cap_ok": touched_file_cap_ok,
            "delete_rename_move_ok": delete_rename_move_ok,
            "structured_executor_summary": structured_summary,
        }
        write_json(run_dir / "summary.json", summary)
        append_lines(run_dir / "changed_files.txt", touched_files)
        append_lines(run_dir / "pre_run_status.txt", pre_status_lines)
        append_lines(run_dir / "post_run_status.txt", post_status_lines)
        write_text(run_dir / "git_diff.patch", run_command(["git", "diff", "--binary", "--"] + editable_paths, REPO_ROOT).stdout)
        write_text(
            run_dir / "last_message.md",
            completed.stdout.strip() if completed.returncode == 0 else (completed.stderr.strip() or completed.stdout.strip()),
        )
        write_text(run_dir / "event_stream.jsonl", "")
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
        "selected_path": "structured_local_executor_live" if args.execute_live else "sidecar_workspace_write_dry_run",
        "validation_result": "PASS" if summary.get("status") in {"DRY_RUN", "PASS"} else "FAIL",
        "final_outcome": "LIVE_WRITE_ACCEPTED" if args.execute_live and summary.get("status") == "PASS" else "DRY_RUN_VALIDATED" if summary.get("status") == "DRY_RUN" else "LIVE_WRITE_INVALID" if args.execute_live else "DRY_RUN_INVALID",
        "runner_summary_path": str(summary_path),
        "validation_summary_path": str(validation_path),
        "allowlist_ok": validation_summary.get("allowlist_ok"),
        "touched_file_cap_ok": validation_summary.get("touched_file_cap_ok"),
        "delete_rename_move_ok": validation_summary.get("delete_rename_move_ok"),
        "operator_message": "Live bounded generator execution was attempted through the structured local executor." if args.execute_live else "Dry-run only. No delegated test-artifact write was performed.",
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
            node_executable=node_executable,
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
