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
    if args.accepted_source_run_dir is None:
        raise SystemExit("execution_write_apply_candidate delegated flow requires --accepted-source-run-dir")
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
