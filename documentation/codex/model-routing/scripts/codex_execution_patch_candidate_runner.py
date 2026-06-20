#!/usr/bin/env python3
"""Bounded helper for janus-executioner execution_patch_candidate flows."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "execution-review-runs"
SIDECAR_RUNNER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_sidecar_skill_runner.ps1"
BUILDER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_request_builder.py"
EXECUTOR_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_executor.py"

REQUIRED_INPUT_FIELDS = [
    "workflow_id",
    "bound_skill_context",
    "target_task",
    "spec_path",
    "precheck_status",
    "allowed_files",
    "max_touched_files",
    "mini_test_plan",
    "manual_validation_gate",
    "delegation_question",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "target_task",
    "patch_text",
    "changed_files",
    "risk_list",
    "suggested_validation_steps",
    "manual_validation_note",
    "codex_acceptance_rule",
    "notes",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


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


def resolve_repo_path(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def extract_patch_files(patch_text: str) -> list[str]:
    files: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[len("+++ b/") :].strip())
    return files


def extract_unified_diff(text: str) -> str:
    lines = text.splitlines()
    start_index = None
    for index, line in enumerate(lines):
        if line.startswith("--- a/"):
            start_index = index
            break
    if start_index is None:
        return ""
    patch_lines = lines[start_index:]
    while patch_lines and patch_lines[-1].strip().startswith("```"):
        patch_lines.pop()
    return "\n".join(patch_lines).strip() + ("\n" if patch_lines else "")


def build_compact_task_brief(spec_text: str) -> str:
    lines = [line.rstrip() for line in spec_text.splitlines()]
    collected: list[str] = []
    capture = False
    stop_prefixes = ("- Tests:", "- Model:", "- Reason:", "HANDOFF_SCOPE:")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            capture = True
        if not capture:
            continue
        if any(stripped.startswith(prefix) for prefix in stop_prefixes):
            break
        if stripped.startswith("- Evidence Paths:"):
            break
        collected.append(line)
    compact = "\n".join(collected).strip()
    if not compact:
        compact = "\n".join(lines[:40]).strip()
    return compact[:3500].rstrip()


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    if payload.get("precheck_status") != "PRE-CHECK PASSED":
        issues.append("precheck_status must be exactly PRE-CHECK PASSED")
    allowed_files = payload.get("allowed_files")
    if not isinstance(allowed_files, list) or not allowed_files:
        issues.append("allowed_files must be a non-empty list")
    max_touched_files = payload.get("max_touched_files")
    if not isinstance(max_touched_files, int) or max_touched_files < 1:
        issues.append("max_touched_files must be an integer >= 1")
    mini_test_plan = payload.get("mini_test_plan")
    if not isinstance(mini_test_plan, list) or not mini_test_plan:
        issues.append("mini_test_plan must be a non-empty list")
    if not payload.get("manual_validation_gate"):
        issues.append("manual_validation_gate must be present")
    return issues


def validate_result_payload(result_payload: dict[str, Any], input_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in result_payload:
            issues.append(f"missing result field: {field}")
    if result_payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status must be PASS, WEAK_SIGNAL, or BLOCKED")
    patch_text = result_payload.get("patch_text")
    if not isinstance(patch_text, str) or "--- a/" not in patch_text or "+++ b/" not in patch_text:
        issues.append("patch_text must be unified diff text")
    changed_files = result_payload.get("changed_files")
    if not isinstance(changed_files, list) or not changed_files:
        issues.append("changed_files must be a non-empty list")
    allowed_files = set(input_payload.get("allowed_files", []))
    max_touched_files = input_payload.get("max_touched_files", 0)
    patch_files = extract_patch_files(patch_text or "")
    if patch_files and changed_files != patch_files:
        issues.append("changed_files must match the files declared in patch_text")
    if isinstance(changed_files, list):
        if len(changed_files) > max_touched_files:
            issues.append("changed_files exceeds max_touched_files")
        for item in changed_files:
            if item not in allowed_files:
                issues.append(f"changed file escapes allowlist: {item}")
    risk_list = result_payload.get("risk_list")
    if not isinstance(risk_list, list) or not risk_list:
        issues.append("risk_list must be a non-empty list")
    suggested_validation_steps = result_payload.get("suggested_validation_steps")
    if not isinstance(suggested_validation_steps, list) or not suggested_validation_steps:
        issues.append("suggested_validation_steps must be a non-empty list")
    manual_validation_note = str(result_payload.get("manual_validation_note", ""))
    if "Codex" not in manual_validation_note or "manual" not in manual_validation_note.lower():
        issues.append("manual_validation_note must preserve Codex-owned manual validation")
    codex_acceptance_rule = str(result_payload.get("codex_acceptance_rule", ""))
    if "Codex" not in codex_acceptance_rule or "apply or reject" not in codex_acceptance_rule.lower():
        issues.append("codex_acceptance_rule must preserve Codex apply/reject ownership")
    return issues


def render_result_markdown(result_payload: dict[str, Any]) -> str:
    lines = [
        "EXECUTION_PATCH_CANDIDATE_REVIEW",
        f"Status: {result_payload['status']}",
        f"Target Task: {result_payload['target_task']}",
        "Changed Files:",
    ]
    for item in result_payload["changed_files"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "Risk List:",
            *[f"- {item}" for item in result_payload["risk_list"]],
            "Suggested Validation Steps:",
            *[f"- {item}" for item in result_payload["suggested_validation_steps"]],
            f"Manual Validation Note: {result_payload['manual_validation_note']}",
            f"Codex Acceptance Rule: {result_payload['codex_acceptance_rule']}",
            f"Notes: {result_payload['notes']}",
            "",
            "PATCH_TEXT",
            result_payload["patch_text"],
        ]
    )
    return "\n".join(lines) + "\n"


def prompt_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "EXECUTION PATCH CANDIDATE GATE",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "Delegated",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded proposal-only execution patch candidate with no apply, no test execution, and Codex-owned acceptance",
        "operator_prompt_lines": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded execution_patch_candidate Delegation-Pfad nutzen?",
        ],
        "boundaries": [
            "No delegated final apply",
            "No delegated test execution",
            "No delegated task completion claim",
            "Codex remains validation and acceptance owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex execution path. No delegated execution patch candidate review was used.",
    }


def build_sidecar_prompt(input_payload: dict[str, Any]) -> str:
    spec_path = input_payload["spec_path"]
    spec_excerpt = ""
    spec_file = resolve_repo_path(spec_path)
    if spec_file.exists():
        spec_excerpt = build_compact_task_brief(spec_file.read_text(encoding="utf-8-sig"))
    allowed_files = "\n".join(f"- {item}" for item in input_payload["allowed_files"])
    mini_test_plan = "\n".join(f"- {item}" for item in input_payload["mini_test_plan"])
    return (
        "Produce one bounded proposal-only unified diff patch for janus-executioner.\n"
        "This is read-only proposal work.\n"
        "Work in one pass.\n"
        "Do not claim completion.\n"
        "Do not output analysis, bullets, or commentary.\n"
        "Do not describe git commands.\n"
        "If you cannot produce a safe bounded patch, output exactly: BLOCKED: <reason>\n\n"
        f"Target Task: {input_payload['target_task']}\n"
        f"Precheck Status: {input_payload['precheck_status']}\n"
        f"Delegation Question: {input_payload['delegation_question']}\n"
        f"Max touched files: {input_payload['max_touched_files']}\n"
        "You may inspect only these files if needed, then immediately output the patch:\n"
        f"{allowed_files}\n\n"
        "Patch rules:\n"
        "- Return exactly one unified diff patch only.\n"
        "- Start with --- a/<path> and +++ b/<path>.\n"
        "- Touch only allowed files.\n"
        "- Keep the patch as small as possible.\n"
        "- Prefer the smallest backend-first fix.\n"
        "- Do not widen scope to schema redesign or unrelated memory behavior.\n\n"
        "Codex validation after review:\n"
        f"{mini_test_plan}\n\n"
        "Manual validation ownership stays with Codex:\n"
        f"{input_payload['manual_validation_gate']}\n\n"
        "Compact task brief:\n"
        f"{spec_excerpt}\n"
    )


def invoke_sidecar(
    *,
    run_directory: Path,
    prompt_path: Path,
    model: str,
    timeout_seconds: int,
    working_directory: Path,
    execute_live: bool,
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
        "read-only",
        "-ApprovalPolicy",
        "never",
        "-TimeoutSeconds",
        str(timeout_seconds),
    ]
    if execute_live:
        command.append("-Execute")
    return run_command(command, working_directory)


def synthesize_live_result_payload(input_payload: dict[str, Any], patch_text: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "target_task": input_payload["target_task"],
        "patch_text": patch_text.rstrip() + "\n",
        "changed_files": extract_patch_files(patch_text),
        "risk_list": [
            "Patch is still proposal-only and may miss a hidden schema or migration dependency.",
            "Codex must verify that no broader address normalization behavior regresses outside the bounded file cluster.",
        ],
        "suggested_validation_steps": list(input_payload["mini_test_plan"]),
        "manual_validation_note": (
            "Codex still owns manual Janus validation. This read-only delegated patch proposal does not satisfy manual product verification."
        ),
        "codex_acceptance_rule": (
            "Codex must review this proposal and decide whether to apply or reject it. The delegated path has no apply or completion authority."
        ),
        "notes": "Captured from read-only Codex CLI sidecar patch proposal.",
    }


def run_structured_patch_capture(
    *,
    run_dir: Path,
    workflow_id: str,
    patch_path: Path,
    allowed_files: list[str],
) -> tuple[bool, str, str]:
    request_path = run_dir / "structured_request.json"
    builder_command = [
        "python",
        str(BUILDER_PATH),
        "--workflow-id",
        f"{workflow_id}-STRUCTURED",
        "--skill-id",
        "janus-executioner",
        "--action-type",
        "propose_patch",
        "--summary",
        "Capture bounded execution patch candidate for Codex review only.",
        "--source-path",
        str(patch_path),
        "--output-request-json",
        str(request_path),
        "--non-goal",
        "No auto apply",
        "--non-goal",
        "No task completion claim",
    ]
    for item in allowed_files:
        builder_command.extend(["--allowed-file", item])
    builder_result = run_command(builder_command, REPO_ROOT)
    write_text(run_dir / "structured_builder_stdout.txt", builder_result.stdout)
    write_text(run_dir / "structured_builder_stderr.txt", builder_result.stderr)
    if builder_result.returncode != 0:
        return False, "BUILDER_FAILED", ""

    executor_command = [
        "python",
        str(EXECUTOR_PATH),
        "--request-json",
        str(request_path),
    ]
    executor_result = run_command(executor_command, REPO_ROOT)
    write_text(run_dir / "structured_executor_stdout.txt", executor_result.stdout)
    write_text(run_dir / "structured_executor_stderr.txt", executor_result.stderr)
    if executor_result.returncode != 0:
        return False, "EXECUTOR_FAILED", ""
    return True, "PASS", str(request_path)


def delegated_from_fixture(
    *,
    run_dir: Path,
    workflow_id: str,
    input_payload: dict[str, Any],
    fixture_result_json: Path,
    task_label: str,
    normal_target_model: str,
    delegated_model_label: str,
) -> dict[str, Any]:
    result_payload = load_json(fixture_result_json.resolve())
    result_issues = validate_result_payload(result_payload, input_payload)
    write_text(run_dir / "delegated_result.md", render_result_markdown(result_payload))

    validation_pass = not result_issues
    validation_summary = {
        "workflow_id": workflow_id,
        "mode": "fixture",
        "input_validation_pass": True,
        "result_validation_pass": not result_issues,
        "input_issues": [],
        "result_issues": result_issues,
        "precheck_status": input_payload.get("precheck_status"),
        "allowed_files": input_payload.get("allowed_files"),
        "changed_files": result_payload.get("changed_files"),
        "accepted_for_codex_patch_review": validation_pass and result_payload.get("status") == "PASS",
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    return {
        "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "delegated_execution_patch_candidate",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW" if validation_pass else "FALLBACK_TO_CODEX_ONLY",
        "operator_message": (
            "Delegated execution patch candidate stayed inside the prechecked allowlist and remains proposal-only. "
            "Codex must still review the patch, decide whether to apply or reject it, and keep final task ownership."
            if validation_pass
            else "Delegated execution patch candidate failed bounded validation and must fall back to Codex-only execution."
        ),
    }


def delegated_from_sidecar(
    *,
    run_dir: Path,
    workflow_id: str,
    input_payload: dict[str, Any],
    task_label: str,
    normal_target_model: str,
    sidecar_model: str,
    timeout_seconds: int,
    working_directory: Path,
    execute_live_sidecar: bool,
) -> tuple[int, dict[str, Any]]:
    prompt_path = run_dir / "sidecar_prompt.md"
    prompt_text = build_sidecar_prompt(input_payload)
    write_text(prompt_path, prompt_text)

    wrapper_result = invoke_sidecar(
        run_directory=run_dir,
        prompt_path=prompt_path,
        model=sidecar_model,
        timeout_seconds=timeout_seconds,
        working_directory=working_directory,
        execute_live=execute_live_sidecar,
    )
    write_text(run_dir / "sidecar_runner_stdout.txt", wrapper_result.stdout)
    write_text(run_dir / "sidecar_runner_stderr.txt", wrapper_result.stderr)

    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        return 1, {
            "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-executioner",
            "task_label": task_label,
            "selected_path": "delegated_execution_patch_candidate_sidecar_failed",
            "normal_target_model": normal_target_model,
            "delegated_model_label": f"Codex CLI sidecar / {sidecar_model}",
            "validation_result": "FAIL",
            "final_outcome": "SIDECAR_SUMMARY_MISSING",
            "operator_message": "Sidecar runner did not produce summary.json for execution patch candidate.",
        }

    runner_summary = load_json(summary_path)
    if not execute_live_sidecar:
        validation_result = "PASS" if runner_summary.get("status") == "DRY_RUN" else "FAIL"
        result = {
            "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-executioner",
            "task_label": task_label,
            "selected_path": "delegated_execution_patch_candidate_sidecar_dry_run",
            "normal_target_model": normal_target_model,
            "delegated_model_label": f"Codex CLI sidecar / {sidecar_model}",
            "validation_result": validation_result,
            "final_outcome": "DRY_RUN_VALIDATED" if validation_result == "PASS" else "DRY_RUN_INVALID",
            "runner_summary_path": str(summary_path),
            "sidecar_prompt_path": str(prompt_path),
            "operator_message": "Dry-run validated the read-only sidecar proposal path. No live delegated model call was made.",
        }
        return (0 if validation_result == "PASS" else 1), result

    last_message_path = run_dir / "last_message.md"
    last_message = last_message_path.read_text(encoding="utf-8-sig") if last_message_path.exists() else ""
    patch_text = extract_unified_diff(last_message)
    if runner_summary.get("status") != "PASS" or not patch_text.strip():
        return 1, {
            "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-executioner",
            "task_label": task_label,
            "selected_path": "delegated_execution_patch_candidate_sidecar_failed",
            "normal_target_model": normal_target_model,
            "delegated_model_label": f"Codex CLI sidecar / {sidecar_model}",
            "validation_result": "FAIL",
            "final_outcome": "SIDECAR_PATCH_NOT_ACCEPTED",
            "runner_summary_path": str(summary_path),
            "last_message_path": str(last_message_path),
            "operator_message": "Sidecar run completed but did not return a usable unified diff patch.",
        }

    extracted_patch_path = run_dir / "extracted_patch.diff"
    write_text(extracted_patch_path, patch_text)

    result_payload = synthesize_live_result_payload(input_payload, patch_text)
    result_issues = validate_result_payload(result_payload, input_payload)
    write_text(run_dir / "delegated_result.md", render_result_markdown(result_payload))

    structured_ok, structured_status, structured_request_path = run_structured_patch_capture(
        run_dir=run_dir,
        workflow_id=workflow_id,
        patch_path=extracted_patch_path,
        allowed_files=input_payload["allowed_files"],
    )

    validation_pass = not result_issues and structured_ok
    validation_summary = {
        "workflow_id": workflow_id,
        "mode": "sidecar_read_only_live",
        "input_validation_pass": True,
        "result_validation_pass": not result_issues,
        "input_issues": [],
        "result_issues": result_issues,
        "precheck_status": input_payload.get("precheck_status"),
        "allowed_files": input_payload.get("allowed_files"),
        "changed_files": result_payload.get("changed_files"),
        "structured_capture_status": structured_status,
        "accepted_for_codex_patch_review": validation_pass and result_payload.get("status") == "PASS",
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    result = {
        "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "delegated_execution_patch_candidate_sidecar_live",
        "normal_target_model": normal_target_model,
        "delegated_model_label": f"Codex CLI sidecar / {sidecar_model}",
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW" if validation_pass else "FALLBACK_TO_CODEX_ONLY",
        "runner_summary_path": str(summary_path),
        "last_message_path": str(last_message_path),
        "extracted_patch_path": str(extracted_patch_path),
        "structured_request_path": structured_request_path or "",
        "operator_message": (
            "Read-only sidecar patch proposal completed and was captured as a bounded Codex review artifact."
            if validation_pass
            else "Read-only sidecar patch proposal failed bounded validation and must fall back to Codex-only execution."
        ),
    }
    return (0 if validation_pass else 1), result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded execution patch candidate helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default="bounded delegated review / fixture mode")
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--fixture-result-json", type=Path, default=None)
    parser.add_argument("--sidecar-model", default="gpt-5.4")
    parser.add_argument("--sidecar-timeout-seconds", type=int, default=180)
    parser.add_argument("--working-directory", type=Path, default=REPO_ROOT)
    parser.add_argument("--execute-live-sidecar", action="store_true")
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"EXECUTION-PATCH-CANDIDATE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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

    if args.input_package_json is None:
        raise SystemExit("--input-package-json is required for operator-choice delegated")

    input_payload = load_json(args.input_package_json.resolve())
    input_issues = validate_input_package(input_payload)
    write_json(run_dir / "input_package.json", input_payload)
    if input_issues:
        write_json(
            run_dir / "validation_summary.json",
            {
                "workflow_id": workflow_id,
                "mode": "input_validation_failed",
                "input_validation_pass": False,
                "input_issues": input_issues,
            },
        )
        output(
            {
                "summary_header": "EXECUTION PATCH CANDIDATE RESULT",
                "workflow_id": workflow_id,
                "skill": "janus-executioner",
                "task_label": args.task_label,
                "selected_path": "delegated_execution_patch_candidate",
                "normal_target_model": args.normal_target_model,
                "delegated_model_label": args.delegated_model_label,
                "validation_result": "FAIL",
                "final_outcome": "INVALID_INPUT_PACKAGE",
                "operator_message": "Delegated execution patch candidate input package failed bounded validation.",
            }
        )
        return 1

    if args.fixture_result_json is not None:
        result = delegated_from_fixture(
            run_dir=run_dir,
            workflow_id=workflow_id,
            input_payload=input_payload,
            fixture_result_json=args.fixture_result_json,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
        )
        write_json(run_dir / "operator_summary.json", result)
        output(result)
        return 0 if result["validation_result"] == "PASS" else 1

    exit_code, result = delegated_from_sidecar(
        run_dir=run_dir,
        workflow_id=workflow_id,
        input_payload=input_payload,
        task_label=args.task_label,
        normal_target_model=args.normal_target_model,
        sidecar_model=args.sidecar_model,
        timeout_seconds=args.sidecar_timeout_seconds,
        working_directory=args.working_directory.resolve(),
        execute_live_sidecar=args.execute_live_sidecar,
    )
    write_json(run_dir / "operator_summary.json", result)
    output(result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
