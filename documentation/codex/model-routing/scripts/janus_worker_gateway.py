#!/usr/bin/env python3
"""Validation-only entry point for the Janus worker gateway contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from janus_worker_contract import (
    load_json,
    validate_shadow_evaluation_manifest_file,
    validate_worker_result_dir,
    validate_worker_task_package_file,
)


REPO_ROOT = Path(__file__).resolve().parents[4]


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def validate_gateway_contract(task_package_json: Path, result_dir: Path | None = None) -> dict[str, Any]:
    task_result = validate_worker_task_package_file(task_package_json)
    result_payload: dict[str, Any] | None = None

    if result_dir is not None:
        result_payload = validate_worker_result_dir(
            result_dir,
            allowed_edit_paths=task_result.get("allowed_edit_paths", []),
        )

    validation_result = task_result["validation_result"]
    if result_payload is not None and result_payload["validation_result"] == "FAIL":
        validation_result = "FAIL"

    if validation_result == "PASS" and result_payload is None:
        gateway_status = "TASK_PACKAGE_READY"
    elif validation_result == "PASS" and result_payload is not None:
        gateway_status = result_payload["contract_status"]
    else:
        gateway_status = "GATEWAY_CONTRACT_REJECTED"

    return {
        "summary_header": "JANUS WORKER GATEWAY CONTRACT",
        "gateway_status": gateway_status,
        "validation_result": validation_result,
        "task_package": task_result,
        "result_package": result_payload,
        "operator_message": _operator_message(gateway_status),
    }


def validate_shadow_evaluation_bundle(
    shadow_eval_manifest_json: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    manifest_result = validate_shadow_evaluation_manifest_file(
        shadow_eval_manifest_json,
        repo_root=repo_root or REPO_ROOT,
    )
    validation_result = manifest_result["validation_result"]
    gateway_status = (
        "SHADOW_EVALUATION_READY"
        if validation_result == "PASS"
        else "SHADOW_EVALUATION_REJECTED"
    )
    return {
        "summary_header": "JANUS WORKER SHADOW EVALUATION BUNDLE",
        "gateway_status": gateway_status,
        "validation_result": validation_result,
        "shadow_evaluation_manifest": manifest_result,
        "operator_message": _shadow_operator_message(gateway_status),
    }


def validate_shadow_class_comparison(
    comparison_summary_json: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    try:
        summary = load_json(comparison_summary_json)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "summary_header": "JANUS WORKER SHADOW CLASS COMPARISON",
            "comparison_status": "SHADOW_CLASS_COMPARISON_INVALID",
            "validation_result": "FAIL",
            "issues": [f"comparison summary unreadable: {exc}"],
            "class_id": "N_A",
            "task_package_validation": None,
            "run_validations": {},
        }

    issues: list[str] = []
    class_id = str(summary.get("class_id") or "").strip().lower() or "N_A"
    task_package_path_value = str(summary.get("task_package_path") or "").strip().replace("\\", "/")
    expected_models = _normalized_models(summary.get("expected_models"))
    model_runs = summary.get("model_runs")
    task_package_validation: dict[str, Any] | None = None
    allowed_edit_paths: list[str] = []

    if not task_package_path_value:
        issues.append("missing task_package_path")
    else:
        task_package_path = (root / task_package_path_value).resolve()
        task_package_validation = validate_worker_task_package_file(task_package_path)
        allowed_edit_paths = task_package_validation.get("allowed_edit_paths", [])
        if task_package_validation["validation_result"] == "FAIL":
            issues.append("task package is invalid for class comparison")

    if len(expected_models) != 2:
        issues.append("expected_models must contain exactly two unique models")

    if not isinstance(model_runs, list) or len(model_runs) != 2:
        issues.append("model_runs must contain exactly two run entries")
        model_runs = [] if not isinstance(model_runs, list) else model_runs

    seen_models: set[str] = set()
    run_validations: dict[str, Any] = {}
    blocked_reviewable = False

    for index, item in enumerate(model_runs, start=1):
        if not isinstance(item, dict):
            issues.append(f"model_runs[{index}] must be an object")
            continue

        model_id = str(item.get("model_id") or "").strip().replace("\\", "/")
        if not model_id:
            issues.append(f"model_runs[{index}] missing model_id")
            continue
        if model_id in seen_models:
            issues.append(f"duplicate model_id in model_runs: {model_id}")
        seen_models.add(model_id)
        if expected_models and model_id not in expected_models:
            issues.append(f"unexpected model_id in model_runs: {model_id}")

        run_directory_value = str(item.get("run_directory") or "").strip().replace("\\", "/")
        if not run_directory_value:
            issues.append(f"{model_id} missing run_directory")
            continue

        run_directory = (root / run_directory_value).resolve()
        result_validation = validate_worker_result_dir(run_directory, allowed_edit_paths=allowed_edit_paths)
        run_validations[model_id] = result_validation
        if result_validation["validation_result"] == "FAIL":
            issues.append(f"{model_id} result package is invalid")
            continue

        cost_path = run_directory / "COST.json"
        try:
            cost_payload = load_json(cost_path)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{model_id} COST.json unreadable: {exc}")
            continue
        if not _has_cost_or_usage_hint(cost_payload):
            issues.append(f"{model_id} result package is missing cost or usage hint")

        if result_validation["contract_status"] == "WORKER_NON_SUCCESS_REVIEWABLE":
            blocked_reviewable = True
        elif result_validation["contract_status"] != "WORKER_SUCCESS_REVIEWABLE":
            issues.append(f"{model_id} result package is not reviewable success")

    missing_models = sorted(set(expected_models) - seen_models)
    if missing_models:
        issues.append("missing model_runs for: " + ", ".join(missing_models))

    if issues:
        comparison_status = "SHADOW_CLASS_COMPARISON_INVALID"
        validation_result = "FAIL"
    elif blocked_reviewable:
        comparison_status = "SHADOW_CLASS_COMPARISON_BLOCKED_REVIEWABLE"
        validation_result = "PASS"
    else:
        comparison_status = "SHADOW_CLASS_COMPARISON_READY"
        validation_result = "PASS"

    return {
        "summary_header": "JANUS WORKER SHADOW CLASS COMPARISON",
        "comparison_status": comparison_status,
        "validation_result": validation_result,
        "issues": issues,
        "class_id": class_id,
        "task_package_validation": task_package_validation,
        "run_validations": run_validations,
    }


def validate_shadow_evaluation_run_bundle(
    shadow_eval_manifest_json: Path,
    evaluation_run_dir: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    manifest_result = validate_shadow_evaluation_manifest_file(
        shadow_eval_manifest_json,
        repo_root=root,
    )
    issues: list[str] = []
    class_validations: dict[str, dict[str, Any]] = {}
    blocked_reviewable = False

    if manifest_result["validation_result"] == "FAIL":
        issues.extend(manifest_result["issues"])
    else:
        manifest = load_json(shadow_eval_manifest_json)
        for entry in manifest.get("shadow_work_classes", []):
            if not isinstance(entry, dict):
                continue
            class_id = str(entry.get("class_id") or "").strip().lower()
            if not class_id:
                continue
            comparison_summary_path = evaluation_run_dir / class_id / "comparison_summary.json"
            comparison_validation = validate_shadow_class_comparison(
                comparison_summary_path,
                repo_root=root,
            )
            class_validations[class_id] = comparison_validation
            if comparison_validation["validation_result"] == "FAIL":
                issues.append(f"{class_id} comparison summary is invalid")
            elif comparison_validation["comparison_status"] == "SHADOW_CLASS_COMPARISON_BLOCKED_REVIEWABLE":
                blocked_reviewable = True

    if issues:
        gateway_status = "SHADOW_EVALUATION_RUNS_REJECTED"
        validation_result = "FAIL"
    elif blocked_reviewable:
        gateway_status = "SHADOW_EVALUATION_RUNS_BLOCKED_REVIEWABLE"
        validation_result = "PASS"
    else:
        gateway_status = "SHADOW_EVALUATION_RUNS_READY"
        validation_result = "PASS"

    return {
        "summary_header": "JANUS WORKER SHADOW EVALUATION RUN BUNDLE",
        "gateway_status": gateway_status,
        "validation_result": validation_result,
        "shadow_evaluation_manifest": manifest_result,
        "class_validations": class_validations,
        "issues": issues,
        "operator_message": _shadow_run_operator_message(gateway_status),
    }


def _operator_message(gateway_status: str) -> str:
    if gateway_status == "TASK_PACKAGE_READY":
        return "Task package is contract-valid. No worker has been executed by this validation-only gateway slice."
    if gateway_status == "WORKER_SUCCESS_REVIEWABLE":
        return "Worker result is structurally reviewable by Codex. Codex must still review diff and evidence."
    if gateway_status == "WORKER_NON_SUCCESS_REVIEWABLE":
        return "Worker did not claim success, but the result package is structurally reviewable for retry or fallback."
    return "Gateway contract rejected the package fail-closed."


def _shadow_operator_message(gateway_status: str) -> str:
    if gateway_status == "SHADOW_EVALUATION_READY":
        return "Shadow evaluation bundle is structurally ready. Live model runs are still out of scope for this slice."
    return "Shadow evaluation bundle failed bounded validation and must not be used for live comparison runs yet."


def _shadow_run_operator_message(gateway_status: str) -> str:
    if gateway_status == "SHADOW_EVALUATION_RUNS_READY":
        return "Shadow evaluation runs are structurally comparable and ready for Codex review."
    if gateway_status == "SHADOW_EVALUATION_RUNS_BLOCKED_REVIEWABLE":
        return "Shadow evaluation runs produced clean fail-closed blocker evidence and are reviewable for retry or fallback."
    return "Shadow evaluation run bundle failed bounded validation and must not be treated as comparable evidence."


def _normalized_models(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    models: list[str] = []
    seen: set[str] = set()
    for item in value:
        model_id = str(item or "").strip().replace("\\", "/")
        if model_id and model_id not in seen:
            seen.add(model_id)
            models.append(model_id)
    return models


def _has_cost_or_usage_hint(cost_payload: dict[str, Any]) -> bool:
    if not isinstance(cost_payload, dict):
        return False
    if cost_payload.get("usage_available") is True:
        return True
    return any(
        key in cost_payload
        for key in ("actual_or_cost_usd", "estimated_or_cost_usd", "total_cost_usd")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Janus worker task and result contracts.")
    parser.add_argument("--task-package-json", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, default=None)
    args = parser.parse_args()

    result = validate_gateway_contract(args.task_package_json.resolve(), args.result_dir.resolve() if args.result_dir else None)
    output(result)
    return 0 if result["validation_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
