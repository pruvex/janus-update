#!/usr/bin/env python3
"""Dispatcher for bounded Codex/Sidecar/structured delegation flows."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DOC_RUNNER = MODEL_ROUTING_DIR / "scripts" / "doc_skill_sidecar_draft_runner.py"
PATCH_RUNNER = MODEL_ROUTING_DIR / "scripts" / "quickchange_sidecar_write_pilot_runner.py"
QUICKCHANGE_APPLY_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_quickchange_write_apply_runner.py"
GENERATOR_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_generator_review_runner.py"
DEBUG_REVIEW_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_debug_hypothesis_review_runner.py"
TEST_TRIAGE_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_test_result_triage_review_runner.py"
EXECUTION_PATCH_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_execution_patch_candidate_runner.py"
EXECUTION_WRITE_APPLY_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_execution_write_apply_candidate_runner.py"
RUN_ROOT = MODEL_ROUTING_DIR / "bounded-dispatch-runs"


def normalize_choice(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "prompt":
        return "prompt"
    if normalized in {"local", "codex", "1"}:
        return "local"
    if normalized in {"sidecar", "delegated", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, delegated/2/sidecar")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def output(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def parse_json_output(text: str, label: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} did not return valid JSON.\n{text}") from exc


def summarize_failure_text(text: str, limit: int = 600) -> str:
    collapsed = " ".join(part.strip() for part in text.splitlines() if part.strip())
    return collapsed[:limit] if collapsed else "No failure details captured."


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_write_candidate_entry(payload: dict, expected_target_task: str) -> list[str]:
    required_fields = [
        "workflow_id",
        "bound_skill_context",
        "target_task",
        "spec_path",
        "precheck_status",
        "allowed_files",
        "max_touched_files",
        "manual_validation_gate",
        "delegation_question",
    ]
    issues: list[str] = []
    for field in required_fields:
        if field not in payload:
            issues.append(f"missing input field: {field}")

    target_task = payload.get("target_task")
    if not isinstance(target_task, str) or not target_task.strip():
        issues.append("target_task must be a non-empty string")
    elif target_task != expected_target_task:
        issues.append(f"target_task must exactly match expected target task: {expected_target_task}")

    if payload.get("precheck_status") != "PRE-CHECK PASSED":
        issues.append("precheck_status must be exactly PRE-CHECK PASSED")

    allowed_files = payload.get("allowed_files")
    if not isinstance(allowed_files, list) or not allowed_files:
        issues.append("allowed_files must be a non-empty list")
    elif any(not isinstance(item, str) or not item.strip() for item in allowed_files):
        issues.append("allowed_files entries must be non-empty strings")

    max_touched_files = payload.get("max_touched_files")
    if not isinstance(max_touched_files, int) or max_touched_files < 1:
        issues.append("max_touched_files must be an integer >= 1")

    if not str(payload.get("manual_validation_gate", "")).strip():
        issues.append("manual_validation_gate must be present")
    if not str(payload.get("delegation_question", "")).strip():
        issues.append("delegation_question must be present")

    for flag in ("delete_intent", "rename_intent", "move_intent"):
        if payload.get(flag) is True:
            issues.append(f"{flag} is not allowed in write-candidate entry")
    for field in ("deleted_files", "renamed_files", "moved_files"):
        value = payload.get(field)
        if isinstance(value, list) and value:
            issues.append(f"{field} must be empty for write-candidate entry")

    requested_operations = payload.get("requested_operations")
    if isinstance(requested_operations, list):
        forbidden = [item for item in requested_operations if str(item).strip().lower() in {"delete", "rename", "move"}]
        if forbidden:
            issues.append(f"requested_operations contains forbidden entries: {', '.join(forbidden)}")

    return issues


def build_write_candidate_validator_manifest(payload: dict) -> dict:
    return {
        "validator_id": "validate_write_candidate_entry_v1",
        "inputs": {
            "target_task": payload["target_task"],
            "precheck_status": payload["precheck_status"],
            "allowed_files": [str(item).replace("\\", "/") for item in payload["allowed_files"]],
            "max_touched_files": payload["max_touched_files"],
            "forbid_delete_rename_move": True,
            "manual_validation_gate": payload["manual_validation_gate"],
            "delegation_question": payload["delegation_question"],
        },
    }


def invoke_write_candidate_entry_gate(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.execution_input_package is None:
        raise SystemExit("execution_write_apply_candidate entry gate requires --execution-input-package")

    input_payload = load_json(args.execution_input_package.resolve())
    expected_target_task = args.execution_expected_target_task or args.task_label
    run_dir = RUN_ROOT / workflow_id
    input_copy_path = run_dir / "write_candidate_entry_input.json"
    validation_path = run_dir / "write_candidate_entry_validation.json"
    manifest_path = run_dir / "write_candidate_entry_validator_manifest.json"
    request_path = run_dir / "write_candidate_entry_request.json"

    write_json(input_copy_path, input_payload)
    issues = validate_write_candidate_entry(input_payload, expected_target_task)
    validation_payload = {
        "workflow_id": workflow_id,
        "mode": "execution_write_apply_candidate_entry_gate",
        "expected_target_task": expected_target_task,
        "validation_pass": not issues,
        "issues": issues,
        "delete_rename_move_tripwire": "PASS" if not any("forbidden" in issue or "must be empty" in issue or "_intent" in issue for issue in issues) else "FAIL",
    }
    write_json(validation_path, validation_payload)

    if issues:
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": args.task_class,
            "task_label": args.task_label,
            "selected_path": "delegated_execution_write_apply_candidate_entry_gate",
            "validation_result": "FAIL",
            "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
            "input_package_path": str(input_copy_path),
            "validation_summary_path": str(validation_path),
            "reject_reasons": issues,
            "operator_result_lines": [
                "Ergebnis: Delegated write-candidate Entry abgelehnt",
                "Route: Fallback auf Codex-only vor spaeteren Write-Phasen",
            ],
            "operator_message": (
                "The delegated write-candidate entry failed bounded contract validation. "
                "Codex must keep execution local until a corrected prechecked entry package exists."
            ),
        }

    manifest_payload = build_write_candidate_validator_manifest(input_payload)
    write_json(manifest_path, manifest_payload)
    builder_command = [
        "python",
        str(MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_request_builder.py"),
        "--workflow-id",
        f"{workflow_id}-ENTRY",
        "--skill-id",
        "janus-executioner",
        "--action-type",
        "run_validator",
        "--summary",
        "Capture the bounded execution write-candidate entry contract for later Codex-owned review.",
        "--source-path",
        str(manifest_path),
        "--output-request-json",
        str(request_path),
        "--non-goal",
        "No delegated write apply",
        "--non-goal",
        "No diff capture in entry gate slice",
        "--non-goal",
        "No task completion claim",
    ]
    builder_result = run_command(builder_command)
    write_text(run_dir / "write_candidate_entry_builder_stdout.txt", builder_result.stdout)
    write_text(run_dir / "write_candidate_entry_builder_stderr.txt", builder_result.stderr)
    if builder_result.returncode != 0:
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": args.task_class,
            "task_label": args.task_label,
            "selected_path": "delegated_execution_write_apply_candidate_entry_gate",
            "validation_result": "FAIL",
            "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
            "input_package_path": str(input_copy_path),
            "validation_summary_path": str(validation_path),
            "validator_manifest_path": str(manifest_path),
            "builder_stdout_path": str(run_dir / "write_candidate_entry_builder_stdout.txt"),
            "builder_stderr_path": str(run_dir / "write_candidate_entry_builder_stderr.txt"),
            "operator_result_lines": [
                "Ergebnis: Review-Artefakt fuer Entry-Gate konnte nicht gebaut werden",
                "Route: Fallback auf Codex-only",
            ],
            "operator_message": "Entry contract validation passed, but the reviewable request artifact could not be built.",
        }

    return {
        "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
        "workflow_id": workflow_id,
        "task_class": args.task_class,
        "task_label": args.task_label,
        "selected_path": "delegated_execution_write_apply_candidate_entry_gate",
        "validation_result": "PASS",
        "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_ACCEPTED_FOR_LATER_PHASES",
        "input_package_path": str(input_copy_path),
        "validation_summary_path": str(validation_path),
        "validator_manifest_path": str(manifest_path),
        "structured_request_path": str(request_path),
        "operator_result_lines": [
            "Ergebnis: Delegated write-candidate Entry zugelassen",
            "Route: Nur Entry-Gate bestanden, spaetere Write-Phasen bleiben separat",
        ],
        "operator_message": (
            "The delegated write-candidate entry contract passed bounded validation and was captured as a reviewable artifact. "
            "Later diff, validation-summary, and Codex-owned acceptance phases remain separate."
        ),
    }


def prompt_summary(args: argparse.Namespace, workflow_id: str) -> dict:
    route_notes = {
        "documentation_draft": "Uses the read-only documentation sidecar draft runner.",
        "quickchange_patch_review": "Uses the bounded quickchange patch-review helper and optional structured patch capture.",
        "quickchange_write_apply": "Uses the bounded quickchange write-apply helper backed by accepted workspace-write evidence.",
        "generator_review": "Uses the local structured generator-review helper with deterministic executor validation.",
        "debug_hypothesis_review": "Uses the bounded assist-only debug hypothesis review helper with redaction and Codex-owned validation.",
        "test_result_triage_review": "Uses the bounded assist-only test-result triage review helper with redaction and Codex-owned validation.",
        "execution_patch_candidate": "Uses the bounded execution patch-candidate helper with precheck binding, file-cluster allowlist, and Codex-owned apply/reject authority.",
        "execution_write_apply_candidate": "Uses the bounded execution write-apply candidate helper backed by an accepted proposal-first execution package and Codex-owned future live-write approval.",
    }
    delegated_meaning = {
        "documentation_draft": "Sidecar read-only draft, then Codex review.",
        "quickchange_patch_review": "Sidecar patch proposal flow, still bounded and review-first.",
        "quickchange_write_apply": "Delegated bounded workspace-write quickchange, but Codex still owns diff validation and final acceptance.",
        "generator_review": "Delegated intent, but local deterministic builder/executor path instead of sidecar write execution.",
        "debug_hypothesis_review": "Delegated assist-only hypothesis review, but Codex still owns reproduction, validation, and next debug action.",
        "test_result_triage_review": "Delegated assist-only triage review, but Codex still owns final classification, rerun, and routing decisions.",
        "execution_patch_candidate": "Delegated proposal-only execution patch candidate, but Codex still owns patch review, apply/reject, and final task completion.",
        "execution_write_apply_candidate": "Delegated bounded execution write candidate, but Codex still owns future live-write approval, diff review, validation review, and final task completion.",
    }
    operator_prompt_lines = {
        "documentation_draft": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded documentation_draft Delegation-Pfad nutzen?",
        ],
        "quickchange_patch_review": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded quickchange_patch_review Delegation-Pfad nutzen?",
        ],
        "quickchange_write_apply": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded quickchange_write_apply Delegation-Pfad nutzen?",
        ],
        "generator_review": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded generator_review Delegation-Pfad nutzen?",
        ],
        "debug_hypothesis_review": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded debug_hypothesis_review Delegation-Pfad nutzen?",
        ],
        "test_result_triage_review": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded test_result_triage_review Delegation-Pfad nutzen?",
        ],
        "execution_patch_candidate": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded execution_patch_candidate Delegation-Pfad nutzen?",
        ],
        "execution_write_apply_candidate": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded execution_write_apply_candidate Delegation-Pfad nutzen?",
        ],
    }
    return {
        "summary_header": "BOUNDED DELEGATION DISPATCH GATE",
        "workflow_id": workflow_id,
        "task_class": args.task_class,
        "task_label": args.task_label,
        "normal_target_model": args.normal_target_model,
        "choice_1": "Codex",
        "choice_2": "Delegated",
        "delegated_meaning": delegated_meaning[args.task_class],
        "route_note": route_notes[args.task_class],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
        "operator_prompt_lines": operator_prompt_lines[args.task_class],
        "boundaries": [
            "No production routing",
            "No canonical routing-table update",
            "No Git/release authority by delegated path",
            "Codex App remains final reviewer",
        ],
    }


def local_summary(args: argparse.Namespace, workflow_id: str) -> dict:
    return {
        "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
        "workflow_id": workflow_id,
        "task_class": args.task_class,
        "task_label": args.task_label,
        "selected_path": "codex_only_operator_choice",
        "validation_result": "PASS",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "operator_result_lines": [
            "Ergebnis: Codex lokal ausgewaehlt",
            f"Route: {args.task_class} bleibt lokal",
        ],
        "operator_message": "Operator chose the normal Codex-only path. No delegated helper was invoked.",
    }


def invoke_documentation_draft(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.prompt_path is None:
        raise SystemExit("documentation_draft delegated flow requires --prompt-path")
    command = [
        "python",
        str(DOC_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "sidecar",
        "--prompt-path",
        str(args.prompt_path.resolve()),
        "--workflow-id",
        workflow_id,
    ]
    if args.structured_review_flow:
        command.append("--structured-review-flow")
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"documentation_draft flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "documentation_draft flow")


def invoke_quickchange_patch_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.prompt_path is None:
        raise SystemExit("quickchange_patch_review delegated flow requires --prompt-path")
    if not args.editable_path:
        raise SystemExit("quickchange_patch_review delegated flow requires at least one --editable-path")
    command = [
        "python",
        str(PATCH_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "sidecar",
        "--prompt-path",
        str(args.prompt_path.resolve()),
        "--workflow-id",
        workflow_id,
        "--max-touched-files",
        str(args.max_touched_files),
        "--execute-live",
    ]
    for item in args.editable_path:
        command.extend(["--editable-path", item])
    if args.structured_review_flow:
        command.append("--structured-review-flow")
    if args.structured_review_source_run_dir:
        command.extend(["--structured-review-source-run-dir", str(args.structured_review_source_run_dir.resolve())])
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"quickchange_patch_review flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "quickchange_patch_review flow")


def invoke_quickchange_write_apply(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.accepted_source_run_dir is None:
        raise SystemExit("quickchange_write_apply delegated flow requires --accepted-source-run-dir")
    command = [
        "python",
        str(QUICKCHANGE_APPLY_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--accepted-source-run-dir",
        str(args.accepted_source_run_dir.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"quickchange_write_apply flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "quickchange_write_apply flow")


def invoke_generator_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.generator_manifest is None:
        raise SystemExit("generator_review delegated flow requires --generator-manifest")
    command = [
        "python",
        str(GENERATOR_RUNNER),
        "--workflow-id",
        workflow_id,
        "--skill-id",
        args.generator_skill_id,
        "--generator-manifest",
        str(args.generator_manifest.resolve()),
        "--summary",
        args.generator_summary or f"Run bounded generator-backed structured action review flow for {args.task_label}.",
        "--non-goal",
        "No prompt-level shell delegation",
        "--non-goal",
        "No production routing activation",
        "--validate-generated-output",
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": "generator_review",
            "task_label": args.task_label,
            "selected_path": "codex_local_fallback_after_structured_executor_failure",
            "validation_result": "FAIL",
            "final_outcome": "CODEX_LOCAL_FALLBACK_REQUIRED",
            "operator_result_lines": [
                "Ergebnis: Lokaler Fallback aktiviert",
                "Route: Delegated intent -> structured executor failed -> Codex local",
            ],
            "fallback_reason": "Structured generator or validator execution did not complete successfully.",
            "generator_runner_stdout_excerpt": summarize_failure_text(completed.stdout),
            "generator_runner_stderr_excerpt": summarize_failure_text(completed.stderr),
            "operator_message": (
                "Delegated generator intent stayed bounded, but the structured local path failed. "
                "Codex must take over locally instead of attempting any free delegated shell execution."
            ),
        }
    result = parse_json_output(completed.stdout, "generator_review flow")
    result["selected_path"] = "delegated_intent_local_structured_executor"
    result["task_class"] = "generator_review"
    result["task_label"] = args.task_label
    result["operator_message"] = (
        "Generator review stayed bounded: delegated intent was converted into local builder/executor/validator steps."
    )
    return result


def invoke_debug_hypothesis_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.debug_input_package is None:
        raise SystemExit("debug_hypothesis_review delegated flow requires --debug-input-package")
    if args.debug_fixture_result is None:
        raise SystemExit("debug_hypothesis_review delegated flow requires --debug-fixture-result in local validation mode")
    command = [
        "python",
        str(DEBUG_REVIEW_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(args.debug_input_package.resolve()),
        "--fixture-result-json",
        str(args.debug_fixture_result.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"debug_hypothesis_review flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "debug_hypothesis_review flow")


def invoke_test_result_triage_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.test_triage_input_package is None:
        raise SystemExit("test_result_triage_review delegated flow requires --test-triage-input-package")
    if args.test_triage_fixture_result is None:
        raise SystemExit("test_result_triage_review delegated flow requires --test-triage-fixture-result in local validation mode")
    command = [
        "python",
        str(TEST_TRIAGE_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(args.test_triage_input_package.resolve()),
        "--fixture-result-json",
        str(args.test_triage_fixture_result.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"test_result_triage_review flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "test_result_triage_review flow")


def invoke_execution_patch_candidate(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.execution_input_package is None:
        raise SystemExit("execution_patch_candidate delegated flow requires --execution-input-package")
    command = [
        "python",
        str(EXECUTION_PATCH_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(args.execution_input_package.resolve()),
        "--sidecar-model",
        args.execution_sidecar_model,
        "--sidecar-timeout-seconds",
        str(args.execution_sidecar_timeout_seconds),
    ]
    if args.execution_fixture_result is not None:
        command.extend(["--fixture-result-json", str(args.execution_fixture_result.resolve())])
    if args.execution_live_sidecar:
        command.append("--execute-live-sidecar")
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"execution_patch_candidate flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "execution_patch_candidate flow")


def invoke_execution_write_apply_candidate(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.execution_input_package is not None:
        return invoke_write_candidate_entry_gate(args, workflow_id)
    if args.accepted_source_run_dir is None:
        raise SystemExit(
            "execution_write_apply_candidate delegated flow requires either --execution-input-package or --accepted-source-run-dir"
        )
    command = [
        "python",
        str(EXECUTION_WRITE_APPLY_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--accepted-source-run-dir",
        str(args.accepted_source_run_dir.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"execution_write_apply_candidate flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "execution_write_apply_candidate flow")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch one bounded delegation task to the matching helper.")
    parser.add_argument("--task-class", required=True, choices=["documentation_draft", "quickchange_patch_review", "quickchange_write_apply", "generator_review", "debug_hypothesis_review", "test_result_triage_review", "execution_patch_candidate", "execution_write_apply_candidate"])
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--prompt-path", type=Path, default=None)
    parser.add_argument("--structured-review-flow", action="store_true")
    parser.add_argument("--structured-review-source-run-dir", type=Path, default=None)
    parser.add_argument("--editable-path", action="append", default=[])
    parser.add_argument("--max-touched-files", type=int, default=1)
    parser.add_argument("--generator-manifest", type=Path, default=None)
    parser.add_argument("--generator-skill-id", default="janus-test-pipeline")
    parser.add_argument("--generator-summary", default=None)
    parser.add_argument("--debug-input-package", type=Path, default=None)
    parser.add_argument("--debug-fixture-result", type=Path, default=None)
    parser.add_argument("--test-triage-input-package", type=Path, default=None)
    parser.add_argument("--test-triage-fixture-result", type=Path, default=None)
    parser.add_argument("--execution-input-package", type=Path, default=None)
    parser.add_argument("--execution-expected-target-task", default=None)
    parser.add_argument("--execution-fixture-result", type=Path, default=None)
    parser.add_argument("--execution-sidecar-model", default="gpt-5.4")
    parser.add_argument("--execution-sidecar-timeout-seconds", type=int, default=180)
    parser.add_argument("--execution-live-sidecar", action="store_true")
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    args = parser.parse_args()

    workflow_id = args.workflow_id
    run_dir = RUN_ROOT / workflow_id
    run_dir.mkdir(parents=True, exist_ok=True)
    choice = normalize_choice(args.operator_choice)

    if choice == "prompt":
        result = prompt_summary(args, workflow_id)
        write_json(run_dir / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = local_summary(args, workflow_id)
        write_json(run_dir / "operator_choice_local.json", result)
        output(result)
        return 0

    if args.task_class == "documentation_draft":
        result = invoke_documentation_draft(args, workflow_id)
    elif args.task_class == "quickchange_patch_review":
        result = invoke_quickchange_patch_review(args, workflow_id)
    elif args.task_class == "quickchange_write_apply":
        result = invoke_quickchange_write_apply(args, workflow_id)
    elif args.task_class == "debug_hypothesis_review":
        result = invoke_debug_hypothesis_review(args, workflow_id)
    elif args.task_class == "test_result_triage_review":
        result = invoke_test_result_triage_review(args, workflow_id)
    elif args.task_class == "execution_patch_candidate":
        result = invoke_execution_patch_candidate(args, workflow_id)
    elif args.task_class == "execution_write_apply_candidate":
        result = invoke_execution_write_apply_candidate(args, workflow_id)
    else:
        result = invoke_generator_review(args, workflow_id)

    write_json(run_dir / "dispatcher_result.json", result)
    output(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
