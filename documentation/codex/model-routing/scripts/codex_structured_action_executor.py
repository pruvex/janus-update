#!/usr/bin/env python3
"""Deterministic local executor for delegated OR/Sidecar action requests."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT_DEFAULT = MODEL_ROUTING_DIR / "structured-action-runs"
SCHEMA_PATH = MODEL_ROUTING_DIR / "schemas" / "codex_delegated_action_request.schema.json"
NODE_BINARY = Path(r"C:\nvm4w\nodejs\node.exe")
NODE_CMD = str(NODE_BINARY if NODE_BINARY.exists() else "node")

ACTION_TYPES = {
    "draft_markdown",
    "propose_patch",
    "run_generator",
    "run_validator",
    "summarize_results",
}

# TASK-SPEC17.3 extends the intake skeleton with exactly one deterministic
# generator route plus one deterministic validator route. Broader validator
# families and later fallback integration still belong to later slices.
SUPPORTED_ACTION_TYPES_V1_SLICE = {
    "draft_markdown",
    "propose_patch",
    "run_generator",
    "run_validator",
}

SUPPORTED_GENERATOR_IDS_V1_SLICE = {
    "compile_testspec_to_testplan_v1",
}

SUPPORTED_VALIDATOR_IDS_V1_SLICE = {
    "validate_runner_v1",
}


class RequestValidationError(RuntimeError):
    """Raised when the delegated request is invalid."""


@dataclass
class ExecutionResult:
    executor_status: str
    detail: str
    action_summary: dict[str, Any]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel_repo(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def resolve_run_relative(value: str, run_dir: Path) -> Path:
    if value.startswith("__RUN_DIR__/"):
        return (run_dir / value.removeprefix("__RUN_DIR__/")).resolve()
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def ensure_within(base: Path, target: Path, label: str) -> None:
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError as exc:
        raise RequestValidationError(f"{label} escapes allowed base: {target}") from exc


def validate_schema_reference() -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    if schema.get("title") != "Codex Delegated Action Request":
        raise RequestValidationError("Unexpected schema title.")
    return schema


def validate_request_shape(request: dict[str, Any]) -> None:
    required = [
        "schema_version",
        "workflow_id",
        "skill_id",
        "action_type",
        "summary",
        "requires_codex_review",
        "non_goals",
    ]
    for field in required:
        if field not in request:
            raise RequestValidationError(f"Missing required field: {field}")

    if request["schema_version"] != "codex_delegated_action_request.v1":
        raise RequestValidationError(f"Unsupported schema_version: {request['schema_version']}")
    if request["action_type"] not in ACTION_TYPES:
        raise RequestValidationError(f"Unsupported action_type: {request['action_type']}")
    if request["requires_codex_review"] is not True:
        raise RequestValidationError("requires_codex_review must be true.")
    if not isinstance(request["non_goals"], list) or not request["non_goals"]:
        raise RequestValidationError("non_goals must be a non-empty list.")

    payload = request.get("action_payload")
    action_type = request["action_type"]
    if action_type in {"draft_markdown", "propose_patch", "run_generator", "run_validator", "summarize_results"} and not isinstance(payload, dict):
        raise RequestValidationError(f"{action_type} requires object action_payload.")

    if action_type == "draft_markdown":
        if payload.get("format") != "markdown":
            raise RequestValidationError("draft_markdown requires format=markdown.")
        if not isinstance(payload.get("content"), str) or not payload["content"].strip():
            raise RequestValidationError("draft_markdown requires non-empty content.")

    if action_type == "propose_patch":
        if payload.get("patch_format") != "unified_diff":
            raise RequestValidationError("propose_patch requires patch_format=unified_diff.")
        if not isinstance(payload.get("allowed_files"), list) or not payload["allowed_files"]:
            raise RequestValidationError("propose_patch requires non-empty allowed_files.")
        if not isinstance(payload.get("patch_text"), str) or not payload["patch_text"].strip():
            raise RequestValidationError("propose_patch requires non-empty patch_text.")

    if action_type == "run_generator":
        if not isinstance(payload.get("generator_id"), str) or not payload["generator_id"].strip():
            raise RequestValidationError("run_generator requires generator_id.")
        if not isinstance(payload.get("inputs"), dict):
            raise RequestValidationError("run_generator requires object inputs.")
        if not isinstance(payload.get("declared_output_artifacts"), list) or not payload["declared_output_artifacts"]:
            raise RequestValidationError("run_generator requires declared_output_artifacts.")

    if action_type == "run_validator":
        if not isinstance(payload.get("validator_id"), str) or not payload["validator_id"].strip():
            raise RequestValidationError("run_validator requires validator_id.")
        if not isinstance(payload.get("inputs"), dict):
            raise RequestValidationError("run_validator requires object inputs.")


def extract_patch_paths(patch_text: str) -> list[str]:
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            candidate = line[6:].strip()
            if candidate != "/dev/null":
                paths.append(candidate)
        elif line.startswith("*** Update File: "):
            paths.append(line.removeprefix("*** Update File: ").strip())
        elif line.startswith("*** Add File: "):
            paths.append(line.removeprefix("*** Add File: ").strip())
        elif line.startswith("*** Delete File: "):
            paths.append(line.removeprefix("*** Delete File: ").strip())
    return sorted(set(paths))


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def handle_draft_markdown(request: dict[str, Any], run_dir: Path) -> ExecutionResult:
    payload = request["action_payload"]
    output_path = run_dir / "draft_output.md"
    write_text(output_path, payload["content"].rstrip() + "\n")
    return ExecutionResult(
        executor_status="PASS",
        detail="Draft markdown artifact stored in run directory only.",
        action_summary={
            "artifact_path": rel_repo(output_path),
            "format": payload["format"],
        },
    )


def handle_propose_patch(request: dict[str, Any], run_dir: Path) -> ExecutionResult:
    payload = request["action_payload"]
    allowed = sorted(str(item).replace("\\", "/") for item in payload["allowed_files"])
    touched = extract_patch_paths(payload["patch_text"])
    disallowed = [item for item in touched if item not in allowed]
    if disallowed:
        raise RequestValidationError(f"Patch touches files outside allowlist: {', '.join(disallowed)}")
    patch_path = run_dir / "proposed_patch.diff"
    write_text(patch_path, payload["patch_text"].rstrip() + "\n")
    return ExecutionResult(
        executor_status="PASS",
        detail="Patch captured for Codex review only; no apply attempted.",
        action_summary={
            "artifact_path": rel_repo(patch_path),
            "allowed_files": allowed,
            "touched_files": touched,
            "auto_apply": False,
        },
    )


def resolve_declared_outputs(payload: dict[str, Any], run_dir: Path) -> list[Path]:
    outputs = [resolve_run_relative(value, run_dir) for value in payload.get("declared_output_artifacts", [])]
    for output in outputs:
        try:
            ensure_within(REPO_ROOT, output, "declared_output_artifact")
        except RequestValidationError:
            ensure_within(run_dir, output, "declared_output_artifact")
    return outputs


def handle_run_generator(request: dict[str, Any], run_dir: Path) -> ExecutionResult:
    payload = request["action_payload"]
    generator_id = payload["generator_id"]
    declared_outputs = resolve_declared_outputs(payload, run_dir)
    inputs = payload["inputs"]

    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    exit_code_path = run_dir / "exit_code.txt"

    if generator_id not in SUPPORTED_GENERATOR_IDS_V1_SLICE:
        raise RequestValidationError(
            f"Unsupported generator_id in TASK-SPEC17.2 executor slice: {generator_id}"
        )

    if generator_id != "compile_testspec_to_testplan_v1":
        raise RequestValidationError(
            f"Generator route not implemented in TASK-SPEC17.2 executor slice: {generator_id}"
        )

    spec_path = resolve_run_relative(str(inputs.get("spec_path", "")), run_dir)
    test_run_id = str(inputs.get("test_run_id", "")).strip()
    output_dir = resolve_run_relative(str(inputs.get("output_dir", "__RUN_DIR__/generated")), run_dir)

    if not spec_path.exists():
        raise RequestValidationError(f"Generator input spec_path does not exist: {spec_path}")
    if not test_run_id:
        raise RequestValidationError("compile_testspec_to_testplan_v1 requires test_run_id.")

    ensure_within(REPO_ROOT, spec_path, "spec_path")
    try:
        ensure_within(REPO_ROOT, output_dir, "output_dir")
    except RequestValidationError:
        ensure_within(run_dir, output_dir, "output_dir")

    plan_path = (output_dir / f"{test_run_id}_plan.json").resolve()
    runner_path = (output_dir / f"{test_run_id}_generated.spec.js").resolve()
    handover_path = (output_dir / f"{test_run_id}_skill2_handover.txt").resolve()
    expected_outputs_without_handover = [plan_path, runner_path]
    expected_outputs_with_handover = [plan_path, runner_path, handover_path]

    include_skill2_handover = False
    if declared_outputs == expected_outputs_without_handover:
        include_skill2_handover = False
    elif declared_outputs == expected_outputs_with_handover:
        include_skill2_handover = True
    else:
        raise RequestValidationError(
            "declared_output_artifacts must exactly match the compile_testspec_to_testplan_v1 expected output set with or without skill2 handover."
        )

    command = [
        NODE_CMD,
        "tests/e2e/generator/compile-testspec-to-testplan.mjs",
        "--spec",
        rel_repo(spec_path),
        "--test-run-id",
        test_run_id,
        "--output-dir",
        rel_repo(output_dir),
    ]
    if not include_skill2_handover:
        command.append("--skip-skill2-handover")
    completed = run_command(command, REPO_ROOT)
    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)
    write_text(exit_code_path, f"{completed.returncode}\n")

    expected_outputs = expected_outputs_with_handover if include_skill2_handover else expected_outputs_without_handover
    missing_outputs = [path for path in expected_outputs if not path.exists()]
    if completed.returncode != 0 or missing_outputs:
        raise RequestValidationError(
            f"Generator execution failed or output missing for {generator_id}. exit_code={completed.returncode} missing_outputs={','.join(rel_repo(path) for path in missing_outputs) or 'none'}"
        )

    return ExecutionResult(
        executor_status="PASS",
        detail="Generator executed through deterministic local mapping.",
        action_summary={
            "generator_id": generator_id,
            "command": command,
            "output_artifacts": [rel_repo(path) for path in expected_outputs],
            "stdout_path": rel_repo(stdout_path),
            "stderr_path": rel_repo(stderr_path),
            "exit_code_path": rel_repo(exit_code_path),
        },
    )


def handle_run_validator(request: dict[str, Any], run_dir: Path) -> ExecutionResult:
    payload = request["action_payload"]
    validator_id = payload["validator_id"]
    inputs = payload["inputs"]

    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    exit_code_path = run_dir / "exit_code.txt"

    if validator_id not in SUPPORTED_VALIDATOR_IDS_V1_SLICE:
        raise RequestValidationError(
            f"Unsupported validator_id in TASK-SPEC17.3 executor slice: {validator_id}"
        )

    plan_path = resolve_run_relative(str(inputs.get("plan_path", "")), run_dir)
    runner_path = resolve_run_relative(str(inputs.get("runner_path", "")), run_dir)
    if not plan_path.exists():
        raise RequestValidationError(f"Validator input plan_path does not exist: {plan_path}")
    if not runner_path.exists():
        raise RequestValidationError(f"Validator input runner_path does not exist: {runner_path}")
    command = [
        NODE_CMD,
        "tests/e2e/generator/validate-runner.mjs",
        "--plan",
        rel_repo(plan_path),
        "--runner",
        rel_repo(runner_path),
    ]

    completed = run_command(command, REPO_ROOT)
    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)
    write_text(exit_code_path, f"{completed.returncode}\n")
    if completed.returncode != 0:
        raise RequestValidationError(f"Validator execution failed for {validator_id}. exit_code={completed.returncode}")

    return ExecutionResult(
        executor_status="PASS",
        detail="Validator executed through deterministic local mapping.",
        action_summary={
            "validator_id": validator_id,
            "command": command,
            "stdout_path": rel_repo(stdout_path),
            "stderr_path": rel_repo(stderr_path),
            "exit_code_path": rel_repo(exit_code_path),
        },
    )


def handle_request(request: dict[str, Any], run_dir: Path) -> ExecutionResult:
    action_type = request["action_type"]
    if action_type not in SUPPORTED_ACTION_TYPES_V1_SLICE:
        raise RequestValidationError(
            f"Action type not enabled in current structured executor slice: {action_type}"
        )
    if action_type == "draft_markdown":
        return handle_draft_markdown(request, run_dir)
    if action_type == "propose_patch":
        return handle_propose_patch(request, run_dir)
    if action_type == "run_generator":
        return handle_run_generator(request, run_dir)
    if action_type == "run_validator":
        return handle_run_validator(request, run_dir)
    raise RequestValidationError(f"Action type not implemented in current structured executor slice: {action_type}")


def build_run_dir(run_root: Path, workflow_id: str) -> Path:
    return run_root / workflow_id / datetime.now().strftime("%Y%m%d-%H%M%S")


def main_with_args(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute one delegated structured action request.")
    parser.add_argument("--request-json", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=RUN_ROOT_DEFAULT)
    args = parser.parse_args(argv)

    request_path = args.request_json.resolve()
    if not request_path.exists():
        raise SystemExit(f"Request JSON does not exist: {request_path}")

    request = load_json(request_path)
    workflow_id = str(request.get("workflow_id", "UNKNOWN-WORKFLOW")).strip() or "UNKNOWN-WORKFLOW"
    run_dir = build_run_dir(args.run_root.resolve(), workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    write_json(run_dir / "request_copy.json", request)
    summary: dict[str, Any] = {
        "workflow_id": workflow_id,
        "skill_id": request.get("skill_id"),
        "action_type": request.get("action_type"),
        "executor_status": "FAILED",
        "schema_validation": "NOT_RUN",
        "mapping_resolution": "NOT_RUN",
        "allowlist_status": "NOT_RUN",
        "output_artifact_status": "NOT_RUN",
        "codex_review_required": request.get("requires_codex_review"),
    }

    try:
        schema = validate_schema_reference()
        validate_request_shape(request)
        write_json(
            run_dir / "validation_result.json",
            {
                "status": "PASS",
                "schema_path": rel_repo(SCHEMA_PATH),
                "schema_title": schema.get("title"),
            },
        )
        summary["schema_validation"] = "PASS"

        result = handle_request(request, run_dir)
        summary["executor_status"] = result.executor_status
        summary["mapping_resolution"] = "PASS"
        summary["allowlist_status"] = "PASS"
        summary["output_artifact_status"] = "PASS"
        summary["detail"] = result.detail
        summary["action_summary"] = result.action_summary
    except RequestValidationError as exc:
        write_json(
            run_dir / "validation_result.json",
            {
                "status": "FAIL",
                "error": str(exc),
                "schema_path": rel_repo(SCHEMA_PATH),
            },
        )
        summary["schema_validation"] = "FAIL" if summary["schema_validation"] == "NOT_RUN" else summary["schema_validation"]
        summary["detail"] = str(exc)
    finally:
        summary["run_directory"] = rel_repo(run_dir)
        write_json(run_dir / "executor_summary.json", summary)
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    return 0 if summary["executor_status"] == "PASS" else 1


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
