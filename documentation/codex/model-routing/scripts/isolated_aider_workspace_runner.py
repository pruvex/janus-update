#!/usr/bin/env python3
"""Prompt/local/delegated helper for isolated temp-workspace Aider worker runs."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from janus_worker_contract import (
    REQUIRED_FORBIDDEN_ACTIONS,
    validate_shadow_evaluation_manifest_file,
    validate_worker_task_package_file,
    write_worker_result_dir,
    write_worker_task_package,
)
from janus_worker_gateway import (
    validate_gateway_contract,
    validate_shadow_evaluation_run_bundle,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "isolated-aider-worker-runs"
CENTRAL_USAGE_LOG_PATH = REPO_ROOT / "documentation" / "codex" / "model-routing" / "or_operator_usage_log.jsonl"
TASK_PACKAGE_FILENAME = "worker_task_package.json"
SECRET_VALUE_MARKERS = (
    "bearer ",
    "sk-",
    "x-janus-internal:",
    "api-key:",
    "password=",
    "token=",
)
LIVE_RETEST_ALLOWED_STEPS = (
    "api_health_check",
    "create_chat",
    "run_bound_prompt",
    "collect_evidence",
)
LIVE_RETEST_FORBIDDEN_AUTHORITY = {
    "final_pass",
    "release",
    "git",
    "routing",
    "broad_shell",
    "secret_write",
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_string_values(nested)


def package_contains_secret_value(package: dict[str, Any]) -> bool:
    for value in iter_string_values(package):
        lowered = value.lower()
        if any(marker in lowered for marker in SECRET_VALUE_MARKERS):
            return True
    return False


def validate_live_retest_contract(package: dict[str, Any]) -> list[str]:
    contract = package.get("live_retest_contract")
    if contract is None:
        return []
    issues: list[str] = []
    if not isinstance(contract, dict):
        return ["live_retest_contract must be an object"]
    if contract.get("mode") != "LIVE_TEST_EXECUTION":
        issues.append("live_retest_contract.mode must be LIVE_TEST_EXECUTION")
    if contract.get("live_test_scope") != "local_bounded_retest":
        issues.append("live_retest_contract.live_test_scope must be local_bounded_retest")
    if contract.get("allowed_steps") != list(LIVE_RETEST_ALLOWED_STEPS):
        issues.append("live_retest_contract.allowed_steps must exactly match the bounded allowlist")
    local_auth = contract.get("local_auth")
    if not isinstance(local_auth, dict):
        issues.append("live_retest_contract.local_auth must be an object")
    else:
        if local_auth.get("mode") != "runtime_only":
            issues.append("live_retest_contract.local_auth.mode must be runtime_only")
        if local_auth.get("secret_material_included") is not False:
            issues.append("live_retest_contract.local_auth.secret_material_included must be false")
    forbidden_authority = set(contract.get("forbidden_authority") or [])
    missing = sorted(LIVE_RETEST_FORBIDDEN_AUTHORITY - forbidden_authority)
    if missing:
        issues.append("live_retest_contract.forbidden_authority missing: " + ", ".join(missing))
    if package_contains_secret_value(package):
        issues.append("package contains a forbidden secret-like value")
    return issues


def normalize_choice(choice: str) -> str:
    value = choice.strip().lower()
    if value == "prompt":
        return "prompt"
    if value in {"local", "codex", "1"}:
        return "local"
    if value in {"or", "openrouter", "delegated", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, delegated/openrouter/or/2")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, env=env)


def build_run_dir(root: Path, workflow_id: str) -> Path:
    return root / workflow_id


def package_prompt_text(package: dict[str, Any], package_path: Path) -> str:
    prompt_text = package.get("task_prompt")
    if isinstance(prompt_text, str) and prompt_text.strip():
        return prompt_text
    prompt_path_value = package.get("task_prompt_path")
    if isinstance(prompt_path_value, str) and prompt_path_value.strip():
        prompt_path = (REPO_ROOT / prompt_path_value).resolve()
        return prompt_path.read_text(encoding="utf-8")
    raise SystemExit(f"{package_path} must define task_prompt or task_prompt_path.")


def compact_command_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for item in results:
        compact.append(
            {
                "label": item.get("label"),
                "expected_exit_codes": item.get("expected_exit_codes"),
                "actual_exit_code": item.get("actual_exit_code"),
                "ok": item.get("ok"),
            }
        )
    return compact


def write_central_usage_log(
    *,
    workflow_id: str,
    operator_choice: str,
    task_label: str,
    normal_target_model: str,
    or_model: str,
    estimated_or_cost: float,
    confidence_percent: int,
    allowed_edit_paths: list[str],
    package_path: Path,
    run_dir: Path,
    result: dict[str, Any],
    notes: list[Any],
    codex_followup_state: str,
    actual_or_cost: float | None = None,
) -> None:
    payload = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "log_version": 1,
        "runner": "isolated_aider_workspace_runner",
        "workflow_id": workflow_id,
        "skill": result.get("skill", "lean-dev-worker"),
        "task_label": task_label,
        "operator_choice": operator_choice,
        "selected_path": result.get("selected_path"),
        "final_outcome": result.get("final_outcome"),
        "validation_result": result.get("validation_result"),
        "codex_followup_state": codex_followup_state,
        "normal_target_model": normal_target_model,
        "or_model_provider": f"OpenRouter / {or_model}",
        "estimated_or_cost": estimated_or_cost,
        "actual_or_cost": actual_or_cost,
        "cost_estimate_confidence_percent": confidence_percent,
        "bounded_scope": allowed_edit_paths,
        "package_path": str(package_path),
        "run_directory": str(run_dir),
        "changed_files": result.get("changed_files", []),
        "copy_back_files": result.get("copy_back_files", []),
        "repo_side_effects": bool(result.get("repo_root_new_aider_artifacts")) or bool(result.get("gitignore_changed_during_run")),
        "repo_root_new_aider_artifacts": result.get("repo_root_new_aider_artifacts", []),
        "gitignore_changed_during_run": result.get("gitignore_changed_during_run"),
        "pre_command_results": compact_command_results(result.get("pre_command_results", [])),
        "post_command_results": compact_command_results(result.get("post_command_results", [])),
        "notes": notes,
    }
    append_jsonl(CENTRAL_USAGE_LOG_PATH, payload)


def resolve_workspace_files(package: dict[str, Any], package_path: Path) -> list[dict[str, Any]]:
    items = package.get("workspace_files")
    if not isinstance(items, list) or not items:
        raise SystemExit(f"{package_path} must define a non-empty workspace_files list.")
    resolved: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"{package_path} workspace_files[{index}] must be an object.")
        repo_path_value = str(item.get("repo_path") or "").strip()
        workspace_path_value = str(item.get("workspace_path") or "").strip()
        if not repo_path_value or not workspace_path_value:
            raise SystemExit(f"{package_path} workspace_files[{index}] must define repo_path and workspace_path.")
        resolved.append(
            {
                "repo_path": repo_path_value.replace("\\", "/"),
                "workspace_path": workspace_path_value.replace("\\", "/"),
                "allow_edit": bool(item.get("allow_edit", False)),
                "copy_back": bool(item.get("copy_back", False)),
            }
        )
    return resolved


def validate_package(package: dict[str, Any], package_path: Path) -> dict[str, Any]:
    task_label = str(package.get("task_label") or "").strip()
    if not task_label:
        raise SystemExit(f"{package_path} must define task_label.")

    workspace_files = resolve_workspace_files(package, package_path)
    allowed_edit_paths = [item["workspace_path"] for item in workspace_files if item["allow_edit"]]
    if not allowed_edit_paths:
        raise SystemExit(f"{package_path} must allow at least one editable workspace file.")

    copy_back_paths = [item["workspace_path"] for item in workspace_files if item["copy_back"]]
    if not copy_back_paths:
        raise SystemExit(f"{package_path} must mark at least one workspace file for copy_back.")
    if any(path not in allowed_edit_paths for path in copy_back_paths):
        raise SystemExit(f"{package_path} copy_back files must also be allow_edit files.")

    pre_commands = package.get("pre_commands") or []
    post_commands = package.get("post_commands") or []
    if not isinstance(pre_commands, list) or not isinstance(post_commands, list):
        raise SystemExit(f"{package_path} pre_commands/post_commands must be lists.")
    live_retest_issues = validate_live_retest_contract(package)
    if live_retest_issues:
        raise SystemExit(f"{package_path} live retest contract invalid: {'; '.join(live_retest_issues)}")

    return {
        "task_label": task_label,
        "task_prompt": package_prompt_text(package, package_path),
        "worker_profile": str(package.get("worker_profile") or "").strip() or "aider-openrouter",
        "acceptance_criteria": package.get("acceptance_criteria") or ["Produce reviewable bounded worker artifacts only."],
        "requested_actions": package.get("requested_actions") or ["edit"],
        "workspace_files": workspace_files,
        "allowed_edit_paths": allowed_edit_paths,
        "copy_back_paths": copy_back_paths,
        "pre_commands": pre_commands,
        "post_commands": post_commands,
        "notes": package.get("notes") or [],
    }


def model_slug(model_id: str) -> str:
    return model_id.strip().replace("\\", "/").replace("/", "__").replace(":", "_").replace(".", "_")


def load_shadow_task_package(path: Path) -> dict[str, Any]:
    validation = validate_worker_task_package_file(path)
    if validation["validation_result"] == "FAIL":
        raise RuntimeError(f"shadow task package invalid: {path}")
    return load_json(path)


def build_runner_package_from_shadow_task(
    shadow_task_package_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    shadow_package = load_shadow_task_package(shadow_task_package_path)
    class_root = shadow_task_package_path.parent
    class_root_rel = class_root.relative_to(repo_root).as_posix()
    allowed_edit_paths = [path.replace("\\", "/") for path in shadow_package.get("allowed_edit_paths", [])]
    workspace_files = [
        {
            "repo_path": f"{class_root_rel}/{relative_path}",
            "workspace_path": relative_path,
            "allow_edit": True,
            "copy_back": True,
        }
        for relative_path in allowed_edit_paths
    ]
    post_commands: list[dict[str, Any]] = []
    for item in shadow_package.get("checks", []):
        if not isinstance(item, dict):
            continue
        post_commands.append(
            {
                "label": str(item.get("label") or "shadow_check"),
                "command": item.get("command") or [],
                "expected_exit_codes": item.get("expected_exit_codes", [0]),
            }
        )
    return {
        "task_label": shadow_package["task_label"],
        "worker_profile": shadow_package["worker_profile"],
        "task_prompt": package_prompt_text(shadow_package, shadow_task_package_path),
        "workspace_files": workspace_files,
        "pre_commands": [],
        "post_commands": post_commands,
        "acceptance_criteria": shadow_package.get("acceptance_criteria") or [],
        "requested_actions": shadow_package.get("requested_actions") or ["edit"],
        "notes": [
            f"shadow_work_class={shadow_package.get('shadow_work_class', 'N_A')}",
            "shadow_evaluation_package=true",
        ],
    }


def read_text_map(repo_paths: list[Path]) -> dict[Path, str]:
    return {path: path.read_text(encoding="utf-8") for path in repo_paths}


def restore_repo_files(baseline_texts: dict[Path, str]) -> None:
    for path, content in baseline_texts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def cost_hint_payload(run_dir: Path) -> dict[str, Any]:
    cost_path = run_dir / "COST.json"
    if not cost_path.exists():
        return {}
    return load_json(cost_path)


def has_cost_hint(cost_payload: dict[str, Any]) -> bool:
    if not isinstance(cost_payload, dict):
        return False
    if cost_payload.get("usage_available") is True:
        return True
    return any(
        key in cost_payload
        for key in ("actual_or_cost_usd", "estimated_or_cost_usd", "total_cost_usd")
    )


def build_shadow_class_summary_markdown(
    *,
    class_id: str,
    expected_models: list[str],
    run_records: list[dict[str, Any]],
    comparison_status: str,
) -> str:
    lines = [
        f"# Shadow Comparison Summary: {class_id}",
        "",
        f"- Comparison status: {comparison_status}",
        f"- Expected models: {', '.join(expected_models)}",
        "",
        "## Runs",
        "",
    ]
    for record in run_records:
        lines.extend(
            [
                f"### {record['model_id']}",
                f"- Final outcome: {record['final_outcome']}",
                f"- Gateway status: {record['gateway_status']}",
                f"- Validation result: {record['validation_result']}",
                f"- Result status: {record['result_status']}",
                f"- Cost hint available: {'yes' if record['cost_hint_available'] else 'no'}",
                f"- Changed files: {', '.join(record['changed_files']) if record['changed_files'] else 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_shadow_evaluation_summary_markdown(
    *,
    evaluation_id: str,
    bundle_status: str,
    class_summary_paths: list[str],
) -> str:
    lines = [
        f"# Shadow Evaluation Summary: {evaluation_id}",
        "",
        f"- Bundle status: {bundle_status}",
        "",
        "## Class summaries",
        "",
    ]
    for path in class_summary_paths:
        lines.append(f"- {path}")
    lines.append("")
    return "\n".join(lines)


def run_shadow_evaluation_bundle(
    *,
    shadow_eval_manifest_path: Path,
    normal_target_model: str,
    estimated_or_cost: float,
    confidence_percent: int,
    workflow_id: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    manifest_validation = validate_shadow_evaluation_manifest_file(
        shadow_eval_manifest_path,
        repo_root=root,
    )
    if manifest_validation["validation_result"] == "FAIL":
        raise RuntimeError("shadow evaluation manifest is not execution-ready")

    manifest = load_json(shadow_eval_manifest_path)
    evaluation_id = str(manifest.get("evaluation_id") or "SHADOW-EVAL").strip()
    sandbox_root = (root / str(manifest.get("sandbox_root") or "")).resolve()
    run_root = sandbox_root / "runs"
    resolved_workflow_id = workflow_id or f"{evaluation_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    evaluation_run_dir = build_run_dir(run_root, resolved_workflow_id)
    evaluation_run_dir.mkdir(parents=True, exist_ok=True)

    class_summary_paths: list[str] = []
    class_records: list[dict[str, Any]] = []

    for entry in manifest.get("shadow_work_classes", []):
        if not isinstance(entry, dict):
            continue
        class_id = str(entry.get("class_id") or "").strip().lower()
        task_package_path = (root / str(entry.get("task_package_path") or "")).resolve()
        expected_models = [str(model).strip() for model in entry.get("comparison_models", []) if str(model).strip()]
        if not class_id or not expected_models:
            continue

        runner_package = build_runner_package_from_shadow_task(
            task_package_path,
            repo_root=root,
        )
        class_dir = evaluation_run_dir / class_id
        class_dir.mkdir(parents=True, exist_ok=True)
        runner_package_path = class_dir / "shadow_runner_input.json"
        write_json(runner_package_path, runner_package)
        validated_package = validate_package(runner_package, runner_package_path)

        baseline_repo_paths = [
            (root / item["repo_path"]).resolve()
            for item in validated_package["workspace_files"]
        ]
        baseline_texts = read_text_map(baseline_repo_paths)
        run_records: list[dict[str, Any]] = []

        for model_id in expected_models:
            model_dir = class_dir / model_slug(model_id)
            model_dir.mkdir(parents=True, exist_ok=True)
            result = delegated_run(
                workflow_id=f"{resolved_workflow_id}-{class_id}-{model_slug(model_id)}",
                run_dir=model_dir,
                validated_package=validated_package,
                package_path=runner_package_path,
                normal_target_model=normal_target_model,
                or_model=model_id,
                estimated_or_cost=estimated_or_cost,
                confidence_percent=confidence_percent,
            )
            result_payload = load_json(model_dir / "RESULT.json")
            cost_payload = cost_hint_payload(model_dir)
            run_records.append(
                {
                    "model_id": model_id,
                    "run_directory": model_dir.relative_to(root).as_posix(),
                    "final_outcome": result.get("final_outcome", "N_A"),
                    "gateway_status": result.get("gateway_status", "N_A"),
                    "validation_result": result.get("validation_result", "FAIL"),
                    "result_status": str(result_payload.get("status") or "N_A"),
                    "changed_files": result.get("changed_files", []),
                    "cost_hint_available": has_cost_hint(cost_payload),
                }
            )
            restore_repo_files(baseline_texts)

        blocked_reviewable = any(record["gateway_status"] == "WORKER_NON_SUCCESS_REVIEWABLE" for record in run_records)
        invalid_run = any(record["validation_result"] != "PASS" for record in run_records) or len(run_records) != 2
        comparison_status = (
            "SHADOW_CLASS_COMPARISON_INVALID"
            if invalid_run
            else "SHADOW_CLASS_COMPARISON_BLOCKED_REVIEWABLE"
            if blocked_reviewable
            else "SHADOW_CLASS_COMPARISON_READY"
        )
        summary_payload = {
            "class_id": class_id,
            "task_package_path": task_package_path.relative_to(root).as_posix(),
            "expected_models": expected_models,
            "model_runs": run_records,
            "comparison_status": comparison_status,
        }
        write_json(class_dir / "comparison_summary.json", summary_payload)
        write_text(
            class_dir / "comparison_summary.md",
            build_shadow_class_summary_markdown(
                class_id=class_id,
                expected_models=expected_models,
                run_records=run_records,
                comparison_status=comparison_status,
            ),
        )
        class_summary_paths.append((class_dir / "comparison_summary.json").relative_to(root).as_posix())
        class_records.append(summary_payload)

    bundle_validation = validate_shadow_evaluation_run_bundle(
        shadow_eval_manifest_path,
        evaluation_run_dir,
        repo_root=root,
    )
    evaluation_summary = {
        "evaluation_id": evaluation_id,
        "workflow_id": resolved_workflow_id,
        "manifest_path": shadow_eval_manifest_path.relative_to(root).as_posix(),
        "evaluation_run_directory": evaluation_run_dir.relative_to(root).as_posix(),
        "class_summary_paths": class_summary_paths,
        "class_records": class_records,
        "bundle_status": bundle_validation["gateway_status"],
        "validation_result": bundle_validation["validation_result"],
    }
    write_json(evaluation_run_dir / "evaluation_summary.json", evaluation_summary)
    write_text(
        evaluation_run_dir / "evaluation_summary.md",
        build_shadow_evaluation_summary_markdown(
            evaluation_id=evaluation_id,
            bundle_status=bundle_validation["gateway_status"],
            class_summary_paths=class_summary_paths,
        ),
    )
    return {
        "evaluation_id": evaluation_id,
        "workflow_id": resolved_workflow_id,
        "evaluation_run_directory": evaluation_run_dir.relative_to(root).as_posix(),
        "bundle_validation": bundle_validation,
        "class_summary_paths": class_summary_paths,
    }


def prompt_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    or_model: str,
    estimated_or_cost: float,
    confidence_percent: int,
    allowed_edit_paths: list[str],
    notes: list[Any],
) -> dict[str, Any]:
    return {
        "summary_header": "ISOLATED AIDER WORKER GATE",
        "workflow_id": workflow_id,
        "skill": "lean-dev-worker",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "OR",
        "or_model_provider": f"OpenRouter / {or_model}",
        "editable_paths": allowed_edit_paths,
        "operator_prompt_lines": [
            "1 = Codex",
            "2 = OR",
            "OR ist hier die guenstige bounded Worker-Option auf isoliertem Temp-Workspace.",
            f"Fest empfohlenes OR-Modell: {or_model}",
            f"Voraussichtliche OR-Kosten: {estimated_or_cost:.8f} USD",
            f"Evidenzgenauigkeit: {confidence_percent}%",
        ],
        "boundaries": [
            "Temp-Workspace ausserhalb des Repo-Roots",
            "Nur allowlisted Dateien",
            "Keine Git- oder Release-Autoritaet",
            "Codex bleibt finaler Reviewer und Acceptance-Owner",
        ],
        "notes": notes,
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, or_model: str) -> dict[str, Any]:
    return {
        "summary_header": "ISOLATED AIDER WORKER RESULT",
        "workflow_id": workflow_id,
        "skill": "lean-dev-worker",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "or_model_provider": f"OpenRouter / {or_model}",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex path. No isolated OR worker run was made.",
    }


def build_gateway_task_package(validated_package: dict[str, Any], package_path: Path, or_model: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for item in validated_package.get("post_commands", []):
        if not isinstance(item, dict):
            continue
        checks.append(
            {
                "label": str(item.get("label") or "post_check"),
                "command": item.get("command") or [],
                "expected_exit_codes": item.get("expected_exit_codes", [0]),
            }
        )

    return {
        "task_label": validated_package["task_label"],
        "worker_profile": str(validated_package.get("worker_profile") or or_model or "aider-openrouter"),
        "allowed_edit_paths": validated_package["allowed_edit_paths"],
        "forbidden_actions": sorted(REQUIRED_FORBIDDEN_ACTIONS),
        "acceptance_criteria": list(validated_package.get("acceptance_criteria") or []),
        "checks": checks,
        "checks_not_required_reason": (
            "No post_commands were defined in the isolated aider package."
            if not checks
            else ""
        ),
        "requested_actions": list(validated_package.get("requested_actions") or ["edit"]),
        "task_prompt_path": str(package_path),
    }


def build_unified_diff(original_text: str, updated_text: str, relative_path: str) -> str:
    if original_text == updated_text:
        return ""
    diff = difflib.unified_diff(
        original_text.splitlines(keepends=True),
        updated_text.splitlines(keepends=True),
        fromfile=f"a/{relative_path}",
        tofile=f"b/{relative_path}",
    )
    return "".join(diff)


def finalize_gateway_result(
    *,
    run_dir: Path,
    task_package_path: Path,
    result_payload: dict[str, Any],
    status: str,
    summary: str,
    changed_files: list[str],
    checks_status: str,
    checks_log: str,
    diff_patch: str,
    cost_payload: dict[str, Any],
) -> dict[str, Any]:
    write_worker_result_dir(
        run_dir,
        status=status,
        summary=summary,
        changed_files=changed_files,
        checks_status=checks_status,
        checks_log=checks_log,
        diff_patch=diff_patch,
        cost_payload=cost_payload,
        metadata={
            "workflow_id": result_payload.get("workflow_id", "N_A"),
            "selected_path": result_payload.get("selected_path", "N_A"),
            "final_outcome": result_payload.get("final_outcome", "N_A"),
        },
    )
    gateway_result = validate_gateway_contract(task_package_path, run_dir)
    result_payload["gateway_status"] = gateway_result["gateway_status"]
    result_payload["task_package_validation"] = gateway_result["task_package"]
    result_payload["result_package_validation"] = gateway_result["result_package"]
    result_payload["validation_result"] = gateway_result["validation_result"]
    return result_payload


def repo_root_aider_artifacts() -> list[str]:
    return sorted(path.name for path in REPO_ROOT.glob(".aider*"))


def execute_checked_commands(
    command_specs: list[dict[str, Any]],
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    all_ok = True
    for index, spec in enumerate(command_specs, start=1):
        if not isinstance(spec, dict):
            raise SystemExit(f"Command spec #{index} must be an object.")
        label = str(spec.get("label") or f"command_{index}")
        command = spec.get("command")
        expected_exit_codes = spec.get("expected_exit_codes", [0])
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise SystemExit(f"Command spec '{label}' must define a string list under command.")
        if not isinstance(expected_exit_codes, list) or not all(isinstance(item, int) for item in expected_exit_codes):
            raise SystemExit(f"Command spec '{label}' must define integer expected_exit_codes.")

        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"=== {label} ===\n")
        completed = run_command(command, cwd, env)
        with log_path.open("a", encoding="utf-8") as handle:
            if completed.stdout:
                handle.write(completed.stdout)
                if not completed.stdout.endswith("\n"):
                    handle.write("\n")
            if completed.stderr:
                handle.write(completed.stderr)
                if not completed.stderr.endswith("\n"):
                    handle.write("\n")
        ok = completed.returncode in expected_exit_codes
        if not ok:
            all_ok = False
        results.append(
            {
                "label": label,
                "command": command,
                "expected_exit_codes": expected_exit_codes,
                "actual_exit_code": completed.returncode,
                "ok": ok,
            }
        )
    return results, all_ok


def delegated_run(
    *,
    workflow_id: str,
    run_dir: Path,
    validated_package: dict[str, Any],
    package_path: Path,
    normal_target_model: str,
    or_model: str,
    estimated_or_cost: float,
    confidence_percent: int,
) -> dict[str, Any]:
    root_aider_before = repo_root_aider_artifacts()
    gitignore_path = REPO_ROOT / ".gitignore"
    gitignore_hash_before = sha256_file(gitignore_path) if gitignore_path.exists() else ""

    log_path = run_dir / "test_output.log"
    report_path = run_dir / "worker_report.md"
    task_package_path = run_dir / TASK_PACKAGE_FILENAME
    write_text(log_path, "")

    workspace = Path(tempfile.mkdtemp(prefix="janus-aider-worker-"))
    worker_task_path = workspace / "worker_task.md"
    baseline_hashes: dict[str, str] = {}
    baseline_texts: dict[str, str] = {}
    gateway_task_package = build_gateway_task_package(validated_package, package_path, or_model)
    write_worker_task_package(task_package_path, gateway_task_package)

    try:
        for item in validated_package["workspace_files"]:
            source_path = (REPO_ROOT / item["repo_path"]).resolve()
            target_path = workspace / item["workspace_path"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            baseline_hashes[item["workspace_path"]] = sha256_file(target_path)
            baseline_texts[item["workspace_path"]] = target_path.read_text(encoding="utf-8")

        write_text(worker_task_path, validated_package["task_prompt"])

        env = os.environ.copy()
        api_key = env.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        if "/" not in or_model.strip():
            raise RuntimeError("or-model must be a provider/model identifier.")
        env["OPENAI_API_KEY"] = api_key
        env["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

        pre_results, pre_ok = execute_checked_commands(
            validated_package["pre_commands"],
            cwd=workspace,
            env=env,
            log_path=log_path,
        )

        aider_command = [
            "aider",
            "--model",
            or_model,
            "--no-auto-commits",
            "--yes-always",
            "--message-file",
            "worker_task.md",
            *[item["workspace_path"] for item in validated_package["workspace_files"]],
        ]
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write("=== AIDER RUN ===\n")
        aider_completed = run_command(aider_command, workspace, env)
        with log_path.open("a", encoding="utf-8") as handle:
            if aider_completed.stdout:
                handle.write(aider_completed.stdout)
                if not aider_completed.stdout.endswith("\n"):
                    handle.write("\n")
            if aider_completed.stderr:
                handle.write(aider_completed.stderr)
                if not aider_completed.stderr.endswith("\n"):
                    handle.write("\n")

        post_results, post_ok = execute_checked_commands(
            validated_package["post_commands"],
            cwd=workspace,
            env=env,
            log_path=log_path,
        )

        changed_files: list[str] = []
        diff_chunks: list[str] = []
        for item in validated_package["workspace_files"]:
            workspace_path = workspace / item["workspace_path"]
            current_hash = sha256_file(workspace_path)
            if current_hash != baseline_hashes[item["workspace_path"]]:
                changed_files.append(item["workspace_path"])
                diff_chunks.append(
                    build_unified_diff(
                        baseline_texts[item["workspace_path"]],
                        workspace_path.read_text(encoding="utf-8"),
                        item["workspace_path"],
                    )
                )
        changed_files = sorted(set(changed_files))
        diff_patch = "".join(chunk for chunk in diff_chunks if chunk)

        scope_drift = sorted(path for path in changed_files if path not in validated_package["allowed_edit_paths"])

        copy_back_files: list[str] = []
        if pre_ok and post_ok and not scope_drift and aider_completed.returncode == 0:
            for item in validated_package["workspace_files"]:
                if item["workspace_path"] in validated_package["copy_back_paths"]:
                    source_path = workspace / item["workspace_path"]
                    target_path = (REPO_ROOT / item["repo_path"]).resolve()
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                    copy_back_files.append(item["repo_path"])

        root_aider_after = repo_root_aider_artifacts()
        new_root_aider = sorted(path for path in root_aider_after if path not in root_aider_before)
        gitignore_hash_after = sha256_file(gitignore_path) if gitignore_path.exists() else ""
        gitignore_changed = gitignore_hash_before != gitignore_hash_after

        passed = (
            pre_ok
            and post_ok
            and aider_completed.returncode == 0
            and not scope_drift
            and not new_root_aider
            and not gitignore_changed
        )

        report_lines = [
            "# Worker Report",
            "",
            "## POC Summary",
            "",
            "- Worker: aider",
            f"- Model: {or_model}",
            f"- Scope: isolated temp workspace outside the repository root",
            f"- Task label: {validated_package['task_label']}",
            "",
            "## Command checks",
            "",
            f"- Pre-check success: {'yes' if pre_ok else 'no'}",
            f"- Aider exit code: {aider_completed.returncode}",
            f"- Post-check success: {'yes' if post_ok else 'no'}",
            "",
            "## Changed files inside temp workspace",
            "",
            f"- Changed files: {', '.join(changed_files) if changed_files else 'none'}",
            f"- Scope drift files: {', '.join(scope_drift) if scope_drift else 'none'}",
            "",
            "## Isolation checks",
            "",
            f"- Repo-root .aider* artifacts before run: {len(root_aider_before)}",
            f"- Repo-root .aider* artifacts after run: {len(root_aider_after)}",
            f"- New repo-root .aider* artifacts: {', '.join(new_root_aider) if new_root_aider else 'none'}",
            f"- .gitignore file hash changed during run: {'yes' if gitignore_changed else 'no'}",
            "",
            "## Practical verdict",
            "",
            "Pass." if passed else "Blocked.",
            "",
            "## Go/No-Go Answer",
            "",
            (
                "- Go: isolated Aider worker result is ready for Codex review."
                if passed
                else "- No-Go: isolated Aider worker result did not satisfy the bounded acceptance bar."
            ),
        ]
        write_text(report_path, "\r\n".join(report_lines) + "\r\n")

        result = {
            "summary_header": "ISOLATED AIDER WORKER RESULT",
            "workflow_id": workflow_id,
            "skill": "lean-dev-worker",
            "task_label": validated_package["task_label"],
            "normal_target_model": normal_target_model,
            "or_model_provider": f"OpenRouter / {or_model}",
            "selected_path": "isolated_aider_temp_workspace_live" if passed else "isolated_aider_temp_workspace_reject",
            "final_outcome": "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW" if passed else "ISOLATED_AIDER_REJECT_AND_FALLBACK",
            "validation_result": "PASS" if passed else "FAIL",
            "package_path": str(package_path),
            "run_directory": str(run_dir),
            "temp_workspace_removed": True,
            "log_path": str(log_path),
            "report_path": str(report_path),
            "changed_files": changed_files,
            "scope_drift_files": scope_drift,
            "copy_back_files": copy_back_files,
            "pre_command_results": pre_results,
            "post_command_results": post_results,
            "aider_exit_code": aider_completed.returncode,
            "repo_root_new_aider_artifacts": new_root_aider,
            "gitignore_changed_during_run": gitignore_changed,
            "operator_message": (
                "Isolated OR worker produced a bounded result. Codex must review and decide whether to accept or harden locally."
                if passed
                else "Isolated OR worker failed bounded acceptance checks. Fallback to Codex-only."
            ),
        }
        summary = (
            "Worker run completed inside an isolated temp workspace. "
            + ("The result is structurally reviewable by Codex." if passed else "The result failed bounded acceptance and should fall back to Codex.")
        )
        checks_status = "pass" if passed else "fail"
        cost_payload = {
            "usage_available": False,
            "estimated_or_cost_usd": estimated_or_cost,
            "cost_estimate_confidence_percent": confidence_percent,
            "or_model_provider": f"OpenRouter / {or_model}",
        }
        result = finalize_gateway_result(
            run_dir=run_dir,
            task_package_path=task_package_path,
            result_payload=result,
            status="success" if passed else "failed",
            summary=summary,
            changed_files=changed_files,
            checks_status=checks_status,
            checks_log=log_path.read_text(encoding="utf-8"),
            diff_patch=diff_patch,
            cost_payload=cost_payload,
        )
        write_json(run_dir / "operator_choice_delegated.json", result)
        write_central_usage_log(
            workflow_id=workflow_id,
            operator_choice="2",
            task_label=validated_package["task_label"],
            normal_target_model=normal_target_model,
            or_model=or_model,
            estimated_or_cost=estimated_or_cost,
            confidence_percent=confidence_percent,
            allowed_edit_paths=validated_package["allowed_edit_paths"],
            package_path=package_path,
            run_dir=run_dir,
            result=result,
            notes=list(validated_package["notes"]) if isinstance(validated_package["notes"], list) else [],
            codex_followup_state="READY_FOR_CODEX_REVIEW" if passed else "CODEX_FALLBACK_REQUIRED",
            actual_or_cost=None,
        )
        return result
    except Exception as exc:
        result = {
            "summary_header": "ISOLATED AIDER WORKER RESULT",
            "workflow_id": workflow_id,
            "skill": "lean-dev-worker",
            "task_label": validated_package["task_label"],
            "normal_target_model": normal_target_model,
            "or_model_provider": f"OpenRouter / {or_model}",
            "selected_path": "isolated_aider_temp_workspace_blocked",
            "final_outcome": "ISOLATED_AIDER_BLOCKED_AND_FALLBACK",
            "validation_result": "FAIL",
            "package_path": str(package_path),
            "run_directory": str(run_dir),
            "temp_workspace_removed": True,
            "log_path": str(log_path),
            "report_path": str(report_path),
            "changed_files": [],
            "scope_drift_files": [],
            "copy_back_files": [],
            "pre_command_results": [],
            "post_command_results": [],
            "aider_exit_code": None,
            "repo_root_new_aider_artifacts": [],
            "gitignore_changed_during_run": False,
            "operator_message": f"Isolated OR worker blocked before a bounded result was accepted: {exc}",
        }
        write_text(report_path, f"# Worker Report\n\nBlocked: {exc}\n")
        result = finalize_gateway_result(
            run_dir=run_dir,
            task_package_path=task_package_path,
            result_payload=result,
            status="blocked",
            summary=f"Worker run blocked before producing an acceptable bounded result: {exc}",
            changed_files=[],
            checks_status="not_run",
            checks_log=log_path.read_text(encoding="utf-8") if log_path.exists() else f"{exc}\n",
            diff_patch="",
            cost_payload={
                "usage_available": False,
                "estimated_or_cost_usd": estimated_or_cost,
                "cost_estimate_confidence_percent": confidence_percent,
                "or_model_provider": f"OpenRouter / {or_model}",
            },
        )
        write_json(run_dir / "operator_choice_delegated.json", result)
        write_central_usage_log(
            workflow_id=workflow_id,
            operator_choice="2",
            task_label=validated_package["task_label"],
            normal_target_model=normal_target_model,
            or_model=or_model,
            estimated_or_cost=estimated_or_cost,
            confidence_percent=confidence_percent,
            allowed_edit_paths=validated_package["allowed_edit_paths"],
            package_path=package_path,
            run_dir=run_dir,
            result=result,
            notes=list(validated_package["notes"]) if isinstance(validated_package["notes"], list) else [],
            codex_followup_state="CODEX_FALLBACK_REQUIRED",
            actual_or_cost=None,
        )
        return result
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Isolated temp-workspace Aider worker helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--shadow-eval-manifest-json", type=Path, default=None)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--or-model", default="openrouter/qwen/qwen3-coder-30b-a3b-instruct")
    parser.add_argument("--estimated-or-cost", type=float, default=0.00080)
    parser.add_argument("--cost-estimate-confidence-percent", type=int, default=70)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    if args.shadow_eval_manifest_json:
        if choice != "delegated":
            raise SystemExit("shadow-eval-manifest-json currently supports delegated execution only.")
        result = run_shadow_evaluation_bundle(
            shadow_eval_manifest_path=args.shadow_eval_manifest_json.resolve(),
            normal_target_model=args.normal_target_model,
            estimated_or_cost=args.estimated_or_cost,
            confidence_percent=args.cost_estimate_confidence_percent,
            workflow_id=args.workflow_id,
        )
        output(result)
        return 0 if result["bundle_validation"]["validation_result"] == "PASS" else 1

    if not args.input_package_json:
        raise SystemExit("input-package-json is required unless shadow-eval-manifest-json is provided.")

    package_path = args.input_package_json.resolve()
    package = load_json(package_path)
    validated_package = validate_package(package, package_path)
    workflow_id = args.workflow_id or f"ISOLATED-AIDER-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(args.run_root.resolve(), workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    gateway_task_package = build_gateway_task_package(validated_package, package_path, args.or_model)
    write_worker_task_package(run_dir / TASK_PACKAGE_FILENAME, gateway_task_package)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            or_model=args.or_model,
            estimated_or_cost=args.estimated_or_cost,
            confidence_percent=args.cost_estimate_confidence_percent,
            allowed_edit_paths=validated_package["allowed_edit_paths"],
            notes=list(validated_package["notes"]) if isinstance(validated_package["notes"], list) else [],
        )
        result = finalize_gateway_result(
            run_dir=run_dir,
            task_package_path=run_dir / TASK_PACKAGE_FILENAME,
            result_payload=result,
            status="local",
            summary="Prompt mode only. The bounded worker run has not started and is awaiting operator choice.",
            changed_files=[],
            checks_status="not_run",
            checks_log="Awaiting operator choice.\n",
            diff_patch="",
            cost_payload={
                "usage_available": False,
                "estimated_or_cost_usd": args.estimated_or_cost,
                "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
                "or_model_provider": f"OpenRouter / {args.or_model}",
            },
        )
        write_json(run_dir / "operator_choice_prompt.json", result)
        write_central_usage_log(
            workflow_id=workflow_id,
            operator_choice="prompt",
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            or_model=args.or_model,
            estimated_or_cost=args.estimated_or_cost,
            confidence_percent=args.cost_estimate_confidence_percent,
            allowed_edit_paths=validated_package["allowed_edit_paths"],
            package_path=package_path,
            run_dir=run_dir,
            result=result,
            notes=list(validated_package["notes"]) if isinstance(validated_package["notes"], list) else [],
            codex_followup_state="AWAITING_OPERATOR_CHOICE",
            actual_or_cost=None,
        )
        output(result)
        return 0

    if choice == "local":
        result = local_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            or_model=args.or_model,
        )
        result = finalize_gateway_result(
            run_dir=run_dir,
            task_package_path=run_dir / TASK_PACKAGE_FILENAME,
            result_payload=result,
            status="local",
            summary="Operator chose the local Codex path. No isolated OR worker run was executed.",
            changed_files=[],
            checks_status="not_run",
            checks_log="Operator chose the local Codex path.\n",
            diff_patch="",
            cost_payload={
                "usage_available": False,
                "estimated_or_cost_usd": args.estimated_or_cost,
                "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
                "or_model_provider": f"OpenRouter / {args.or_model}",
            },
        )
        write_json(run_dir / "operator_choice_local.json", result)
        write_central_usage_log(
            workflow_id=workflow_id,
            operator_choice="1",
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            or_model=args.or_model,
            estimated_or_cost=args.estimated_or_cost,
            confidence_percent=args.cost_estimate_confidence_percent,
            allowed_edit_paths=validated_package["allowed_edit_paths"],
            package_path=package_path,
            run_dir=run_dir,
            result=result,
            notes=list(validated_package["notes"]) if isinstance(validated_package["notes"], list) else [],
            codex_followup_state="LOCAL_CODEX_PATH_SELECTED",
            actual_or_cost=None,
        )
        output(result)
        return 0

    result = delegated_run(
        workflow_id=workflow_id,
        run_dir=run_dir,
        validated_package=validated_package,
        package_path=package_path,
        normal_target_model=args.normal_target_model,
        or_model=args.or_model,
        estimated_or_cost=args.estimated_or_cost,
        confidence_percent=args.cost_estimate_confidence_percent,
    )
    output(result)
    return 0 if result.get("validation_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
