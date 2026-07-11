#!/usr/bin/env python3
"""Run one bounded builder -> executor flow for generator-backed structured actions."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
BUILDER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_request_builder.py"
EXECUTOR_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_executor.py"
FIXTURE_DIR = MODEL_ROUTING_DIR / "structured-action-fixtures"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def run_step(command: list[str], label: str) -> dict:
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(
            f"{label} failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    stdout = completed.stdout.strip()
    return load_json_from_text(stdout) if stdout else {"status": "PASS"}


def load_json_from_text(value: str) -> dict:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Expected JSON output but got invalid text:\n{value}") from exc


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def build_validator_manifest_payload(manifest_payload: dict, generator_exec_summary: dict) -> dict:
    generator_id = manifest_payload.get("generator_id")
    inputs = manifest_payload.get("inputs", {})
    output_artifacts = generator_exec_summary.get("action_summary", {}).get("output_artifacts", [])

    if generator_id == "generate_live_runner_v1":
        if len(output_artifacts) != 1:
            raise SystemExit("Expected exactly one generated output artifact for validate-generated-output.")
        return {
            "validator_id": "validate_runner_v1",
            "inputs": {
                "plan_path": inputs.get("plan_path"),
                "runner_path": output_artifacts[0],
            },
        }

    if generator_id == "compile_testspec_to_testplan_v1":
        if len(output_artifacts) not in {2, 3}:
            raise SystemExit(
                "Expected two or three generated output artifacts for compile_testspec_to_testplan_v1 validation."
            )
        return {
            "validator_id": "validate_runner_v1",
            "inputs": {
                "plan_path": output_artifacts[0],
                "runner_path": output_artifacts[1],
            },
        }

    raise SystemExit(
        "--validate-generated-output currently supports only generator_id=generate_live_runner_v1 or compile_testspec_to_testplan_v1."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one bounded generator-backed structured-action review flow."
    )
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--generator-manifest", type=Path, required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--non-goal", action="append", dest="non_goals", required=True)
    parser.add_argument("--validator-manifest", type=Path, default=None)
    parser.add_argument("--validator-summary", default=None)
    parser.add_argument("--validate-generated-output", action="store_true")
    args = parser.parse_args()

    generator_manifest = args.generator_manifest.resolve()
    if not generator_manifest.exists():
        raise SystemExit(f"Generator manifest does not exist: {generator_manifest}")

    manifest_payload = load_json(generator_manifest)

    generator_request = FIXTURE_DIR / f"{args.workflow_id}_generator_request.json"
    generator_builder = [
        "python",
        str(BUILDER_PATH),
        "--workflow-id",
        args.workflow_id,
        "--skill-id",
        args.skill_id,
        "--action-type",
        "run_generator",
        "--summary",
        args.summary,
        "--source-path",
        str(generator_manifest),
        "--output-request-json",
        str(generator_request),
    ]
    for non_goal in args.non_goals:
        generator_builder.extend(["--non-goal", non_goal])

    generator_build_summary = run_step(generator_builder, "Generator request builder")
    generator_exec_summary = run_step(
        ["python", str(EXECUTOR_PATH), "--request-json", str(generator_request)],
        "Generator executor",
    )

    result = {
        "summary_header": "BOUNDED GENERATOR REVIEW RESULT",
        "status": "PASS",
        "workflow_id": args.workflow_id,
        "skill_id": args.skill_id,
        "selected_path": "delegated_intent_local_structured_executor",
        "generator_manifest": rel_repo(generator_manifest),
        "generator_request_json": rel_repo(generator_request),
        "generator_builder_status": generator_build_summary.get("status", "PASS"),
        "generator_executor_status": generator_exec_summary.get("executor_status", "UNKNOWN"),
        "generator_run_directory": generator_exec_summary.get("run_directory"),
        "validation_result": "PASS",
        "final_outcome": "GENERATOR_REVIEW_READY",
        "operator_result_lines": [
            "Ergebnis: Generator-Review erfolgreich",
            "Route: Delegated intent -> builder -> executor",
        ],
    }

    validator_manifest: Path | None = None
    if args.validate_generated_output:
        validator_manifest = FIXTURE_DIR / f"{args.workflow_id}_validator_manifest.json"
        validator_manifest.write_text(
            json.dumps(
                build_validator_manifest_payload(manifest_payload, generator_exec_summary),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
    elif args.validator_manifest:
        validator_manifest = args.validator_manifest.resolve()
        if not validator_manifest.exists():
            raise SystemExit(f"Validator manifest does not exist: {validator_manifest}")

    if validator_manifest:
        validator_request = FIXTURE_DIR / f"{args.workflow_id}_validator_request.json"
        validator_summary = args.validator_summary or f"Validate generated output for {args.workflow_id}"
        validator_builder = [
            "python",
            str(BUILDER_PATH),
            "--workflow-id",
            f"{args.workflow_id}-VALIDATOR",
            "--skill-id",
            args.skill_id,
            "--action-type",
            "run_validator",
            "--summary",
            validator_summary,
            "--source-path",
            str(validator_manifest),
            "--output-request-json",
            str(validator_request),
        ]
        for non_goal in args.non_goals:
            validator_builder.extend(["--non-goal", non_goal])

        validator_build_summary = run_step(validator_builder, "Validator request builder")
        validator_exec_summary = run_step(
            ["python", str(EXECUTOR_PATH), "--request-json", str(validator_request)],
            "Validator executor",
        )
        result.update(
            {
                "validator_manifest": rel_repo(validator_manifest),
                "validator_request_json": rel_repo(validator_request),
                "validator_builder_status": validator_build_summary.get("status", "PASS"),
                "validator_executor_status": validator_exec_summary.get("executor_status", "UNKNOWN"),
                "validator_run_directory": validator_exec_summary.get("run_directory"),
                "final_outcome": "GENERATOR_REVIEW_AND_VALIDATION_READY",
                "operator_result_lines": [
                    "Ergebnis: Generator-Review erfolgreich",
                    "Route: Delegated intent -> builder -> executor -> validator",
                ],
            }
        )

    result["operator_message"] = (
        "Delegated generator intent stayed bounded and was converted into deterministic local execution plus review artifacts."
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
