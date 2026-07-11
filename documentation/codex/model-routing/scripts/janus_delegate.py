#!/usr/bin/env python3
"""Tri-modal operator entry for Codex / Cursor / OpenRouter delegation.

Default behavior is dry-run and contract-oriented. External worker execution is
blocked unless a future caller adds explicit live approval wiring.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SCRIPTS_DIR = MODEL_ROUTING_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from delegation_routing import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    DEFAULT_TASK_LIST_PATH,
    build_gate,
    estimate_run_cost_usd,
    find_lane,
    find_task,
    is_never_delegate,
    lane_model,
    lane_cursor_model,
    load_manifest,
    load_task_list,
    normalize_operator_choice,
    validate_manifest_and_task_list,
)


CURSOR_RUNNER_PATH = SCRIPTS_DIR / "janus_cursor_worker_runner.py"
DETERMINISTIC_APPLY_RUNNER_PATH = SCRIPTS_DIR / "codex_execution_write_apply_candidate_runner.py"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value)


def parse_command_json_output(stdout: str) -> dict[str, Any]:
    parsed = json.loads(stdout)
    if not isinstance(parsed, dict):
        raise ValueError("Delegated command output must be a JSON object")
    return parsed


def build_openrouter_plan(
    *,
    lane_id: str,
    workflow_id: str,
    lane: dict[str, Any],
    task: dict[str, Any] | None,
    input_package_json: Path | None,
    prompt_path: Path | None,
    editable_paths: list[str],
    max_touched_files: int | None,
    accepted_source_run_dir: Path | None,
    estimated_codex_saved_tokens: int | None,
    estimated_delegation_overhead_tokens: int | None,
) -> dict[str, Any]:
    openrouter_config = lane.get("openrouter") if isinstance(lane.get("openrouter"), dict) else {}
    runner_name = openrouter_config.get("runner") if isinstance(openrouter_config, dict) else None
    command = [
        "python",
        str((SCRIPTS_DIR / str(runner_name)).relative_to(REPO_ROOT)) if runner_name else "N_A",
    ]
    if runner_name == "codex_bounded_delegation_dispatcher.py":
        task_class = openrouter_config.get("dispatcher_task_class", lane_id)
        command.extend([
            "--task-class",
            str(task_class),
            "--task-label",
            task.get("title", lane_id) if isinstance(task, dict) else lane_id,
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "prompt",
            "--workflow-id",
            workflow_id,
        ])
        if prompt_path is not None:
            command.extend(["--prompt-path", str(prompt_path)])
        if max_touched_files is not None:
            command.extend(["--max-touched-files", str(max_touched_files)])
        for item in editable_paths:
            command.extend(["--editable-path", item])
        if accepted_source_run_dir is not None:
            command.extend(["--accepted-source-run-dir", str(accepted_source_run_dir)])
    elif runner_name == "codex_dev_workhorse_runner.py":
        command.extend([
            "--task-class",
            lane_id,
            "--task-label",
            task.get("title", lane_id) if isinstance(task, dict) else lane_id,
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "prompt",
            "--workflow-id",
            workflow_id,
            "--path-id",
            "productive_dev_workhorse_path",
        ])
    elif runner_name in {
        "codex_backlog_handoff_review_runner.py",
        "codex_backlog_prioritization_review_runner.py",
        "codex_backlog_intake_review_runner.py",
        "codex_health_check_review_runner.py",
        "codex_feature_design_runner.py",
        "codex_spec_generator_review_runner.py",
        "codex_spec_normalizer_runner.py",
        "codex_spec_review_runner.py",
        "codex_spec_to_task_runner.py",
        "codex_task_breakdown_runner.py",
        "codex_precheck_review_runner.py",
        "codex_debug_hypothesis_review_runner.py",
        "codex_test_result_triage_review_runner.py",
        "codex_skill_router_review_runner.py",
    }:
        command.extend([
            "--task-label",
            task.get("title", lane_id) if isinstance(task, dict) else lane_id,
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "prompt",
            "--workflow-id",
            workflow_id,
        ])
        if runner_name in {
            "codex_skill_router_review_runner.py",
            "codex_backlog_intake_review_runner.py",
            "codex_backlog_prioritization_review_runner.py",
            "codex_backlog_handoff_review_runner.py",
            "codex_health_check_review_runner.py",
            "codex_feature_design_runner.py",
            "codex_spec_generator_review_runner.py",
            "codex_spec_normalizer_runner.py",
            "codex_spec_review_runner.py",
            "codex_spec_to_task_runner.py",
            "codex_task_breakdown_runner.py",
            "codex_precheck_review_runner.py",
        }:
            command.extend([
                "--estimated-or-cost",
                str(openrouter_config.get("prompt_estimated_or_cost", 0.00018)),
                "--cost-estimate-confidence-percent",
                str(openrouter_config.get("prompt_cost_estimate_confidence_percent", 70)),
            ])
    elif runner_name == "test_pipeline_sidecar_write_pilot_runner.py":
        command.extend([
            "--testspec-path",
            "N/A",
            "--test-run-id",
            workflow_id,
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "prompt",
            "--workflow-id",
            workflow_id,
        ])
    else:
        command.extend(["--workflow-id", workflow_id])

    if input_package_json is not None and runner_name != "codex_bounded_delegation_dispatcher.py":
        command.extend(["--input-package-json", str(input_package_json)])
    if runner_name == "codex_dev_workhorse_runner.py" and accepted_source_run_dir is not None:
        command.extend(["--accepted-source-run-dir", str(accepted_source_run_dir)])
    if runner_name == "codex_dev_workhorse_runner.py" and estimated_codex_saved_tokens is not None:
        command.extend(["--estimated-codex-saved-tokens", str(estimated_codex_saved_tokens)])
    if runner_name == "codex_dev_workhorse_runner.py" and estimated_delegation_overhead_tokens is not None:
        command.extend(["--estimated-delegation-overhead-tokens", str(estimated_delegation_overhead_tokens)])

    return {
        "backend": "openrouter",
        "planned_runner": runner_name or "N_A",
        "planned_command": command,
        "live_execution_allowed": False,
        "operator_message": (
            str(openrouter_config.get("transitional_runtime_note"))
            if runner_name == "codex_bounded_delegation_dispatcher.py" and openrouter_config.get("transitional_runtime_note")
            else "OpenRouter remains option 3; janus_delegate currently plans existing OR runners without live calls."
        ),
    }


def build_cursor_command(
    *,
    lane: dict[str, Any],
    lane_id: str,
    workflow_id: str,
    selected_model: str,
    cursor_pool: str,
    input_package_json: Path | None,
    allowlist_file: Path | None,
    accepted_source_run_dir: Path | None,
    execute_live: bool,
) -> list[str]:
    command = [
        "python",
        str(CURSOR_RUNNER_PATH),
        "--lane",
        lane_id,
        "--workflow-id",
        workflow_id,
        "--model",
        selected_model,
    ]
    if cursor_pool in {"auto_composer", "api"}:
        command.extend(["--cursor-pool", cursor_pool])
    command.append("--execute-live" if execute_live else "--dry-run")
    cursor_config = lane.get("cursor") if isinstance(lane.get("cursor"), dict) else {}
    if cursor_config.get("require_allowlist") is True:
        command.append("--require-allowlist")
    if input_package_json is not None:
        command.extend(["--input-package-json", str(input_package_json)])
    if allowlist_file is not None:
        command.extend(["--allowlist-file", str(allowlist_file)])
    if accepted_source_run_dir is not None:
        command.extend(["--accepted-source-run-dir", str(accepted_source_run_dir)])
    return command


def build_deterministic_apply_command(
    *,
    lane_id: str,
    workflow_id: str,
    task: dict[str, Any] | None,
    accepted_source_run_dir: Path | None,
    execute_live: bool,
) -> list[str]:
    if lane_id != "execution_write_apply_candidate":
        raise ValueError(f"deterministic apply command is not supported for lane {lane_id}")
    if accepted_source_run_dir is None:
        raise ValueError("execution_write_apply_candidate deterministic apply requires accepted_source_run_dir")
    command = [
        "python",
        str(DETERMINISTIC_APPLY_RUNNER_PATH.relative_to(REPO_ROOT)),
        "--task-label",
        task.get("title", lane_id) if isinstance(task, dict) else lane_id,
        "--normal-target-model",
        "5.4 medium",
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--accepted-source-run-dir",
        str(accepted_source_run_dir),
    ]
    if execute_live:
        command.append("--execute-live-sidecar")
    return command


def route(args: argparse.Namespace) -> dict[str, Any]:
    normalized_choice = normalize_operator_choice(args.operator_choice, load_manifest(args.manifest))
    if args.execute_live_cursor and normalized_choice not in {"3", "4"}:
        return {
            "validation_result": "FAIL",
            "final_outcome": "CURSOR_LIVE_EXECUTION_REQUIRES_CURSOR_CHOICE",
            "operator_message": "Use --execute-live-cursor only together with operator choice 3=Cursor Composer or 4=Cursor API.",
            "codex_review_required": True,
        }

    manifest = load_manifest(args.manifest)
    task_list = load_task_list(args.task_list)
    manifest_validation = validate_manifest_and_task_list(manifest, task_list)
    if manifest_validation["validation_result"] != "PASS":
        return {
            "validation_result": "FAIL",
            "final_outcome": "DELEGATION_MANIFEST_INVALID",
            "manifest_validation": manifest_validation,
            "codex_review_required": True,
        }

    task = find_task(task_list, task_id=args.task_id, lane_id=args.lane)
    lane_id = args.lane or (task.get("lane_id") if isinstance(task, dict) else None)
    if not lane_id:
        choice = normalized_choice
        if isinstance(task, dict) and choice in {"prompt", "1"}:
            return {
                "validation_result": "PASS",
                "status": "CODEX_ONLY_TASK",
                "task_id": task.get("task_id"),
                "pipeline_mode": task.get("pipeline_mode"),
                "backend": "codex",
                "selected_model": ((task.get("models") or {}).get("codex") or {}).get("model"),
                "operator_gate_lines": ["1 = Codex"],
                "visible_backends": ["codex"],
                "recommended_backend": "codex",
                "selected_path": "codex_only_operator_choice",
                "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
                "codex_review_required": True,
                "codex_final_owner": True,
                "operator_message": "This task has no delegation lane and remains Codex-only.",
            }
        if isinstance(task, dict):
            return {
                "validation_result": "FAIL",
                "task_id": task.get("task_id"),
                "backend": choice,
                "operator_gate_lines": ["1 = Codex"],
                "visible_backends": ["codex"],
                "recommended_backend": "codex",
                "final_outcome": "DELEGATION_BACKEND_NOT_AVAILABLE",
                "operator_message": "This task is Codex-only and cannot be delegated.",
                "codex_review_required": True,
            }
        return {
            "validation_result": "FAIL",
            "final_outcome": "DELEGATION_LANE_REQUIRED",
            "operator_message": "Provide --lane or a task_id that maps to a lane.",
            "codex_review_required": True,
        }
    lane = find_lane(manifest, lane_id)
    if lane is None:
        return {
            "validation_result": "FAIL",
            "final_outcome": "DELEGATION_LANE_UNKNOWN",
            "lane_id": lane_id,
            "codex_review_required": True,
        }

    gate = build_gate(
        manifest=manifest,
        task_list=task_list,
        lane_id=lane_id,
        task_id=args.task_id,
        estimated_codex_saved_tokens=args.estimated_codex_saved_tokens,
        estimated_delegation_overhead_tokens=args.estimated_delegation_overhead_tokens,
        minimum_net_codex_saved_tokens=args.minimum_net_codex_saved_tokens,
    )
    choice = normalized_choice

    if choice == "prompt":
        visible_lines = []
        for choice_row in gate["visible_choices"]:
            model = choice_row.get("model")
            cost_hint = choice_row.get("cost_hint")
            line = f'{choice_row["choice_id"]}. {choice_row["label"]}'
            if isinstance(model, str) and model.strip():
                line += f" - {model}"
            if isinstance(cost_hint, str) and cost_hint.strip():
                line += f" - {cost_hint}"
            if choice_row.get("recommended") is True:
                line += " <- Empfehlung"
            visible_lines.append(line)
        operator_message = "Wie soll ich delegieren?\n\n" + "\n".join(visible_lines) + f"\n\nEmpfehlung: {gate['recommended_choice']}"
        if gate.get("roi", {}).get("status") == "NEGATIVE" and len(gate["visible_choices"]) > 1:
            visibility_reason = str(gate.get("negative_roi_visibility_reason") or "").strip()
            note = (
                visibility_reason
                if visibility_reason
                else "Externe Optionen bleiben als verfuegbare Ausweichlane sichtbar, sind aber aktuell nicht kostenoptimiert empfohlen."
            )
            operator_message += f"\nHinweis: {note}"
        gate.update({
            "validation_result": "PASS",
            "final_outcome": "AWAITING_OPERATOR_CHOICE",
            "operator_message": operator_message,
        })
        return gate

    visible_choice_ids = {item["choice_id"] for item in gate["visible_choices"]}
    if choice not in visible_choice_ids:
        return {
            **gate,
            "backend": choice,
            "validation_result": "FAIL",
            "final_outcome": "DELEGATION_BACKEND_NOT_AVAILABLE",
            "operator_message": f"{choice} is hidden or disabled for this task because eligibility, governance, or ROI did not pass.",
        }

    selected_choice = next(item for item in gate["visible_choices"] if item["choice_id"] == choice)
    selected_backend = str(selected_choice["backend"])
    selected_model = selected_choice.get("model")
    base = {
        **gate,
        "backend": selected_backend,
        "selected_model": selected_model,
        "selected_choice": choice,
        "codex_review_required": True,
        "codex_final_owner": True,
        "validation_result": "PASS",
    }

    if selected_backend == "codex" or is_never_delegate(task, lane_id):
        return {
            **base,
            "backend": "codex",
            "selected_model": lane_model(lane, task, "codex"),
            "selected_path": "codex_only_operator_choice",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_message": "Codex local path selected. No external delegation will run.",
        }

    if selected_backend == "deterministic_apply":
        deterministic_apply = (
            lane_id == "execution_write_apply_candidate"
            and isinstance(lane.get("deterministic_apply_worker"), dict)
            and lane["deterministic_apply_worker"].get("enabled") is True
        )
        if deterministic_apply:
            command = build_deterministic_apply_command(
                lane_id=lane_id,
                workflow_id=args.workflow_id,
                task=task,
                accepted_source_run_dir=args.accepted_source_run_dir,
                execute_live=False,
            )
            return {
                **base,
                "backend": "deterministic_apply",
                "selected_model": "deterministic_local_apply",
                "selected_path": "deterministic_apply_worker_planned_no_live",
                "final_outcome": "DETERMINISTIC_APPLY_DRY_RUN_READY",
                "planned_runner": DETERMINISTIC_APPLY_RUNNER_PATH.name,
                "planned_command": command,
                "live_execution_allowed": False,
                "operator_message": "Option 2 uses the sealed deterministic apply worker for this accepted-source lane; no Cursor live call is executed.",
            }
    if selected_backend == "cursor":
        cursor_pool = str(selected_choice.get("pool") or "auto_composer")
        if not isinstance(selected_model, str) or not selected_model:
            selected_model = lane_cursor_model(lane, manifest, cursor_pool) or "auto"
        command = build_cursor_command(
            lane=lane,
            lane_id=lane_id,
            workflow_id=args.workflow_id,
            selected_model=selected_model,
            cursor_pool=cursor_pool,
            input_package_json=args.input_package_json,
            allowlist_file=args.allowlist_file,
            accepted_source_run_dir=args.accepted_source_run_dir,
            execute_live=args.execute_live_cursor,
        )
        cost_estimate = estimate_run_cost_usd(selected_model, manifest)
        if args.execute_live_cursor:
            completed = run_command(command)
            try:
                downstream = parse_command_json_output(completed.stdout)
            except (ValueError, json.JSONDecodeError) as exc:
                return {
                    **base,
                    "selected_path": "cursor_worker_live_via_delegate_unreadable",
                    "final_outcome": "CURSOR_WORKER_OUTPUT_UNREADABLE",
                    "validation_result": "FAIL",
                    "planned_command": command,
                    "cursor_pool": cursor_pool,
                    "cost_estimate_usd_static": cost_estimate,
                    "live_execution_allowed": True,
                    "downstream_exit_code": completed.returncode,
                    "downstream_stderr": completed.stderr,
                    "operator_message": f"Cursor worker output could not be parsed as JSON: {exc}",
                }
            return {
                **base,
                **downstream,
                "selected_path": "cursor_worker_live_via_delegate",
                "planned_command": command,
                "cursor_pool": cursor_pool,
                "cost_estimate_usd_static": cost_estimate,
                "live_execution_allowed": True,
                "downstream_exit_code": completed.returncode,
                "downstream_stderr": completed.stderr,
            }
        return {
            **base,
            "selected_path": "cursor_worker_planned_no_live",
            "final_outcome": "CURSOR_WORKER_DRY_RUN_READY",
            "planned_command": command,
            "cursor_pool": cursor_pool,
            "cost_estimate_usd_static": cost_estimate,
            "live_execution_allowed": False,
            "operator_message": f"Cursor option {choice} is planned through the shared bounded worker; no live Cursor call is executed.",
        }

    if selected_backend == "openrouter":
        plan = build_openrouter_plan(
            lane_id=lane_id,
            workflow_id=args.workflow_id,
            lane=lane,
            task=task,
            input_package_json=args.input_package_json,
            prompt_path=args.prompt_path,
            editable_paths=args.editable_path,
            max_touched_files=args.max_touched_files,
            accepted_source_run_dir=args.accepted_source_run_dir,
            estimated_codex_saved_tokens=args.estimated_codex_saved_tokens,
            estimated_delegation_overhead_tokens=args.estimated_delegation_overhead_tokens,
        )
        return {
            **base,
            "selected_path": "openrouter_worker_planned_no_live",
            "final_outcome": "OPENROUTER_WORKER_DRY_RUN_READY",
            **plan,
        }

    raise AssertionError(f"Unhandled operator choice: {choice}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tri-modal Codex/Cursor/OpenRouter delegation entry.")
    parser.add_argument("--lane", default=None)
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--task-list", type=Path, default=DEFAULT_TASK_LIST_PATH)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--prompt-path", type=Path, default=None)
    parser.add_argument("--editable-path", action="append", default=[])
    parser.add_argument("--max-touched-files", type=int, default=None)
    parser.add_argument("--allowlist-file", type=Path, default=None)
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    parser.add_argument("--estimated-codex-saved-tokens", type=optional_int, default=None)
    parser.add_argument("--estimated-delegation-overhead-tokens", type=optional_int, default=None)
    parser.add_argument("--minimum-net-codex-saved-tokens", type=optional_int, default=None)
    parser.add_argument("--execute-live-cursor", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-json", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = route(args)
    if args.output_json is not None:
        write_json(args.output_json, result)
    output(result)
    return 0 if result.get("validation_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
