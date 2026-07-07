#!/usr/bin/env python3
"""Contract helpers for the Janus worker gateway.

This module intentionally contains no live worker execution. It validates the
task package Codex may hand to a bounded worker and the normalized result
package Codex must receive back before reviewing any delegated work.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_RESULT_ARTIFACTS = (
    "RESULT.json",
    "RESULT.md",
    "DIFF.patch",
    "FILES_CHANGED.txt",
    "CHECKS.log",
    "COST.json",
)

SUCCESS_STATUSES = {"success"}
NON_SUCCESS_STATUSES = {"failed", "blocked", "local"}
VALID_RESULT_STATUSES = SUCCESS_STATUSES | NON_SUCCESS_STATUSES
REQUIRED_SHADOW_WORK_CLASS_IDS = {
    "docs_fleissarbeit",
    "test_fixture_arbeit",
}

REQUIRED_FORBIDDEN_ACTIONS = {
    "commit",
    "push",
    "tag",
    "merge",
    "release",
    "publish",
    "dependency",
    "secret",
    "auth",
    "security",
    "privacy",
    "migration",
    "architecture",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _as_non_empty_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _as_non_empty_string(item)
        if text:
            items.append(text.replace("\\", "/"))
    return items


def _lower_string_set(value: Any) -> set[str]:
    return {item.strip().lower() for item in _string_list(value)}


def _line_items(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip().replace("\\", "/") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_worker_task_package(package: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []

    task_label = _as_non_empty_string(package.get("task_label"))
    if not task_label:
        issues.append("missing task_label")

    profile = _as_non_empty_string(package.get("worker_profile"))
    if not profile:
        issues.append("missing worker_profile")

    allowed_edit_paths = _string_list(package.get("allowed_edit_paths"))
    if not allowed_edit_paths:
        issues.append("allowed_edit_paths must contain at least one path")

    if len(set(allowed_edit_paths)) != len(allowed_edit_paths):
        issues.append("allowed_edit_paths must not contain duplicates")

    acceptance_criteria = _string_list(package.get("acceptance_criteria"))
    if not acceptance_criteria:
        issues.append("acceptance_criteria must contain at least one item")

    checks = package.get("checks")
    checks_not_required_reason = _as_non_empty_string(package.get("checks_not_required_reason"))
    if not isinstance(checks, list):
        issues.append("checks must be a list")
    elif not checks and not checks_not_required_reason:
        issues.append("checks must not be empty unless checks_not_required_reason is set")

    forbidden_actions = _lower_string_set(package.get("forbidden_actions"))
    missing_forbidden = sorted(REQUIRED_FORBIDDEN_ACTIONS - forbidden_actions)
    if missing_forbidden:
        issues.append("forbidden_actions missing required boundaries: " + ", ".join(missing_forbidden))

    requested_actions = _lower_string_set(package.get("requested_actions", []))
    forbidden_requested = sorted(requested_actions & REQUIRED_FORBIDDEN_ACTIONS)
    if forbidden_requested:
        issues.append("requested_actions contains forbidden actions: " + ", ".join(forbidden_requested))

    has_prompt = bool(_as_non_empty_string(package.get("task_prompt")))
    has_prompt_path = bool(_as_non_empty_string(package.get("task_prompt_path")))
    if not has_prompt and not has_prompt_path:
        issues.append("task_prompt or task_prompt_path is required")

    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "contract_status": "TASK_PACKAGE_VALID" if not issues else "TASK_PACKAGE_INVALID",
        "issues": issues,
        "task_label": task_label or "N_A",
        "worker_profile": profile or "N_A",
        "allowed_edit_paths": allowed_edit_paths,
        "required_result_artifacts": list(REQUIRED_RESULT_ARTIFACTS),
    }


def validate_worker_task_package_file(path: Path) -> dict[str, Any]:
    try:
        package = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "validation_result": "FAIL",
            "contract_status": "TASK_PACKAGE_INVALID",
            "issues": [f"task package unreadable: {exc}"],
            "task_label": "N_A",
            "worker_profile": "N_A",
            "allowed_edit_paths": [],
            "required_result_artifacts": list(REQUIRED_RESULT_ARTIFACTS),
        }
    return validate_worker_task_package(package)


def _normalized_repo_relpath(value: Any) -> str:
    return _as_non_empty_string(value).replace("\\", "/")


def validate_shadow_evaluation_manifest(
    manifest: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    package_validations: dict[str, dict[str, Any]] = {}

    evaluation_id = _as_non_empty_string(manifest.get("evaluation_id"))
    if not evaluation_id:
        issues.append("missing evaluation_id")

    sandbox_root = _normalized_repo_relpath(manifest.get("sandbox_root"))
    if not sandbox_root:
        issues.append("missing sandbox_root")

    if manifest.get("real_repo_writeback_allowed") is not False:
        issues.append("real_repo_writeback_allowed must be false")
    if manifest.get("global_worker_release_allowed") is not False:
        issues.append("global_worker_release_allowed must be false")
    if manifest.get("real_consumer_activation_allowed") is not False:
        issues.append("real_consumer_activation_allowed must be false")

    class_entries = manifest.get("shadow_work_classes")
    if not isinstance(class_entries, list):
        issues.append("shadow_work_classes must be a list")
        class_entries = []

    if len(class_entries) != 2:
        issues.append("shadow_work_classes must contain exactly two class definitions")

    seen_class_ids: set[str] = set()
    seen_package_paths: set[str] = set()

    for index, entry in enumerate(class_entries, start=1):
        if not isinstance(entry, dict):
            issues.append(f"shadow_work_classes[{index}] must be an object")
            continue

        class_id = _normalized_repo_relpath(entry.get("class_id")).lower()
        if not class_id:
            issues.append(f"shadow_work_classes[{index}] missing class_id")
            continue
        if class_id not in REQUIRED_SHADOW_WORK_CLASS_IDS:
            issues.append(f"shadow_work_classes[{index}] unknown class_id: {class_id}")
        if class_id in seen_class_ids:
            issues.append(f"shadow_work_classes[{index}] duplicate class_id: {class_id}")
        seen_class_ids.add(class_id)

        package_path_value = _normalized_repo_relpath(entry.get("task_package_path"))
        if not package_path_value:
            issues.append(f"{class_id} missing task_package_path")
        elif sandbox_root and not package_path_value.startswith(sandbox_root.rstrip("/") + "/"):
            issues.append(f"{class_id} task_package_path must stay under sandbox_root")
        elif package_path_value in seen_package_paths:
            issues.append(f"{class_id} task_package_path must be unique")
        else:
            seen_package_paths.add(package_path_value)

        comparison_models = _string_list(entry.get("comparison_models"))
        if len(comparison_models) != 2:
            issues.append(f"{class_id} comparison_models must contain exactly two models")
        elif len(set(comparison_models)) != 2:
            issues.append(f"{class_id} comparison_models must not contain duplicates")
        invalid_models = [model for model in comparison_models if "/" not in model]
        if invalid_models:
            issues.append(f"{class_id} comparison_models must use provider/model identifiers")

        if repo_root is None or not package_path_value:
            continue

        package_path = (repo_root / package_path_value).resolve()
        package_validation = validate_worker_task_package_file(package_path)
        package_validations[class_id] = package_validation
        if package_validation["validation_result"] == "FAIL":
            issues.append(f"{class_id} task package is invalid")
            continue

        try:
            package_payload = load_json(package_path)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{class_id} task package unreadable: {exc}")
            continue

        declared_class_id = _normalized_repo_relpath(package_payload.get("shadow_work_class")).lower()
        if declared_class_id != class_id:
            issues.append(f"{class_id} task package shadow_work_class mismatch")

    if seen_class_ids and seen_class_ids != REQUIRED_SHADOW_WORK_CLASS_IDS:
        missing_class_ids = sorted(REQUIRED_SHADOW_WORK_CLASS_IDS - seen_class_ids)
        unexpected_class_ids = sorted(seen_class_ids - REQUIRED_SHADOW_WORK_CLASS_IDS)
        if missing_class_ids:
            issues.append("missing required shadow work classes: " + ", ".join(missing_class_ids))
        if unexpected_class_ids:
            issues.append("unexpected shadow work classes: " + ", ".join(unexpected_class_ids))

    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "contract_status": "SHADOW_EVALUATION_READY" if not issues else "SHADOW_EVALUATION_INVALID",
        "issues": issues,
        "evaluation_id": evaluation_id or "N_A",
        "sandbox_root": sandbox_root or "N_A",
        "required_shadow_work_classes": sorted(REQUIRED_SHADOW_WORK_CLASS_IDS),
        "package_validations": package_validations,
    }


def validate_shadow_evaluation_manifest_file(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    try:
        manifest = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "validation_result": "FAIL",
            "contract_status": "SHADOW_EVALUATION_INVALID",
            "issues": [f"shadow evaluation manifest unreadable: {exc}"],
            "evaluation_id": "N_A",
            "sandbox_root": "N_A",
            "required_shadow_work_classes": sorted(REQUIRED_SHADOW_WORK_CLASS_IDS),
            "package_validations": {},
        }
    return validate_shadow_evaluation_manifest(manifest, repo_root=repo_root)


def write_worker_task_package(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, payload)


def _read_result_json(result_dir: Path, issues: list[str]) -> dict[str, Any]:
    result_path = result_dir / "RESULT.json"
    if not result_path.exists():
        return {}
    try:
        payload = load_json(result_path)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"RESULT.json unreadable: {exc}")
        return {}
    if not isinstance(payload, dict):
        issues.append("RESULT.json must contain an object")
        return {}
    return payload


def _read_cost_json(result_dir: Path, issues: list[str]) -> dict[str, Any]:
    cost_path = result_dir / "COST.json"
    if not cost_path.exists():
        return {}
    try:
        payload = load_json(cost_path)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"COST.json unreadable: {exc}")
        return {}
    if not isinstance(payload, dict):
        issues.append("COST.json must contain an object")
        return {}
    return payload


def validate_worker_result_dir(result_dir: Path, allowed_edit_paths: list[str] | None = None) -> dict[str, Any]:
    issues: list[str] = []
    allowed = set(path.replace("\\", "/") for path in (allowed_edit_paths or []))

    if not result_dir.exists() or not result_dir.is_dir():
        return {
            "validation_result": "FAIL",
            "contract_status": "RESULT_PACKAGE_INVALID",
            "issues": [f"result directory does not exist: {result_dir}"],
            "status": "N_A",
            "changed_files": [],
            "missing_artifacts": list(REQUIRED_RESULT_ARTIFACTS),
        }

    missing_artifacts = [name for name in REQUIRED_RESULT_ARTIFACTS if not (result_dir / name).exists()]
    if missing_artifacts:
        issues.append("missing required result artifacts: " + ", ".join(missing_artifacts))

    result_payload = _read_result_json(result_dir, issues)
    cost_payload = _read_cost_json(result_dir, issues)
    changed_files = _line_items(result_dir / "FILES_CHANGED.txt")

    status = str(result_payload.get("status") or "").strip().lower()
    if status not in VALID_RESULT_STATUSES:
        issues.append("RESULT.json status must be one of: " + ", ".join(sorted(VALID_RESULT_STATUSES)))

    scope_drift = sorted(path for path in changed_files if allowed and path not in allowed)
    if scope_drift:
        issues.append("changed files outside allowed_edit_paths: " + ", ".join(scope_drift))

    checks_status = str(result_payload.get("checks_status") or "").strip().lower()
    checks_log_empty = (result_dir / "CHECKS.log").exists() and not (result_dir / "CHECKS.log").read_text(
        encoding="utf-8"
    ).strip()

    if status in SUCCESS_STATUSES:
        if not changed_files:
            issues.append("success result must list at least one changed file")
        if (result_dir / "DIFF.patch").exists() and not (result_dir / "DIFF.patch").read_text(
            encoding="utf-8"
        ).strip():
            issues.append("success result must include a non-empty DIFF.patch")
        if checks_status != "pass":
            issues.append("success result requires RESULT.json checks_status=pass")
        if checks_log_empty:
            issues.append("success result requires a non-empty CHECKS.log")

    usage_available = cost_payload.get("usage_available")
    if usage_available is True and not any(
        key in cost_payload for key in ("actual_or_cost_usd", "estimated_or_cost_usd", "total_cost_usd")
    ):
        issues.append("COST.json usage_available=true requires cost metadata")
    if usage_available not in {True, False, None}:
        issues.append("COST.json usage_available must be true, false, or omitted")

    if issues:
        contract_status = "RESULT_PACKAGE_INVALID"
        if status == "success":
            contract_status = "WORKER_SUCCESS_REJECTED"
    elif status == "success":
        contract_status = "WORKER_SUCCESS_REVIEWABLE"
    else:
        contract_status = "WORKER_NON_SUCCESS_REVIEWABLE"

    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "contract_status": contract_status,
        "issues": issues,
        "status": status or "N_A",
        "changed_files": changed_files,
        "scope_drift_files": scope_drift,
        "missing_artifacts": missing_artifacts,
        "required_result_artifacts": list(REQUIRED_RESULT_ARTIFACTS),
    }


def write_worker_result_dir(
    result_dir: Path,
    *,
    status: str,
    summary: str,
    changed_files: list[str],
    checks_status: str,
    checks_log: str,
    diff_patch: str,
    cost_payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> None:
    result_dir.mkdir(parents=True, exist_ok=True)
    normalized_changed = [path.replace("\\", "/") for path in changed_files]
    result_payload: dict[str, Any] = {
        "status": status,
        "checks_status": checks_status,
        "changed_files_count": len(normalized_changed),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if metadata:
        result_payload.update(metadata)

    write_json(result_dir / "RESULT.json", result_payload)
    write_text(result_dir / "RESULT.md", summary.rstrip() + "\n")
    write_text(result_dir / "DIFF.patch", diff_patch)
    write_text(
        result_dir / "FILES_CHANGED.txt",
        ("\n".join(normalized_changed) + "\n") if normalized_changed else "",
    )
    write_text(result_dir / "CHECKS.log", checks_log)
    write_json(result_dir / "COST.json", cost_payload)
