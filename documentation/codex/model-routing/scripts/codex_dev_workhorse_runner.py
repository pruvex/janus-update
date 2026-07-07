#!/usr/bin/env python3
"""Dedicated productive Dev-workhorse entry runner for Spec 22."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SESSION_RUNS_DIR = MODEL_ROUTING_DIR / "productive-dev-workhorse-runs"
HEALTH_SNAPSHOT_PATH = (
    REPO_ROOT / "documentation" / "codex" / "skills" / "janus-health-check" / "scripts" / "health_snapshot.py"
)
if str(MODEL_ROUTING_DIR / "scripts") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))
DISPATCHER_PATH = MODEL_ROUTING_DIR / "scripts" / "codex_bounded_delegation_dispatcher.py"
BUDGET_PROFILE_CONFIG_PATH = MODEL_ROUTING_DIR / "config" / "or_task_budget_profiles_2026-06-19.json"

from bounded_or_worker_eligibility import (
    evaluate_existing_skill_operator_gate_visibility,
    evaluate_productive_dev_workhorse_path,
)
from bounded_or_worker_gate_prompt import (
    build_missing_gate_result,
    build_operator_prompt_lines,
    build_visibility_suppressed_result,
    missing_gate_fields,
)


ALLOWED_TASK_CLASSES = {
    "execution_patch_candidate",
    "execution_write_apply_candidate",
}


def _roi_number(args: argparse.Namespace, name: str) -> int | None:
    value = getattr(args, name, None)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_or_roi(args: argparse.Namespace) -> dict[str, Any]:
    saved_tokens = _roi_number(args, "estimated_codex_saved_tokens")
    overhead_tokens = _roi_number(args, "estimated_codex_or_overhead_tokens")
    minimum_net_saved = _roi_number(args, "minimum_net_codex_saved_tokens")
    if minimum_net_saved is None:
        minimum_net_saved = 0

    missing: list[str] = []
    if saved_tokens is None:
        missing.append("estimated_codex_saved_tokens")
    if overhead_tokens is None:
        missing.append("estimated_codex_or_overhead_tokens")

    if missing:
        return {
            "status": "UNKNOWN",
            "missing_fields": missing,
            "estimated_codex_saved_tokens": saved_tokens,
            "estimated_codex_or_overhead_tokens": overhead_tokens,
            "minimum_net_codex_saved_tokens": minimum_net_saved,
            "net_codex_saved_tokens": None,
            "message": "OR ROI cannot be evaluated because Codex token estimates are missing.",
        }

    net_saved = int(saved_tokens) - int(overhead_tokens)
    status = "POSITIVE" if net_saved >= int(minimum_net_saved) else "NEGATIVE"
    return {
        "status": status,
        "missing_fields": [],
        "estimated_codex_saved_tokens": int(saved_tokens),
        "estimated_codex_or_overhead_tokens": int(overhead_tokens),
        "minimum_net_codex_saved_tokens": int(minimum_net_saved),
        "net_codex_saved_tokens": net_saved,
        "message": (
            f"OR ROI {status}: estimated saved Codex tokens {saved_tokens}, "
            f"OR orchestration/review overhead {overhead_tokens}, net {net_saved}, "
            f"minimum required {minimum_net_saved}."
        ),
    }


def _should_enforce_roi(args: argparse.Namespace) -> bool:
    if bool(getattr(args, "require_positive_or_roi", False)):
        return True
    return (
        getattr(args, "estimated_codex_saved_tokens", None) is not None
        or getattr(args, "estimated_codex_or_overhead_tokens", None) is not None
    )


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def _parse_json_output(text: str, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} did not return valid JSON.\n{text}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit(f"{label} did not return a JSON object.")
    return parsed


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _resolve_selected_or_model(args: argparse.Namespace, eligibility: dict[str, Any]) -> str:
    return str(eligibility.get("selected_or_model") or args.selected_or_model or "").strip()


def _bind_canonical_selected_or_model(args: argparse.Namespace, selected_or_model: str) -> str:
    canonical_selected_or_model = str(selected_or_model or "").strip()
    setattr(args, "_canonical_selected_or_model", canonical_selected_or_model)
    return canonical_selected_or_model


def _resolve_canonical_selected_or_model(args: argparse.Namespace) -> str:
    bound_selected_or_model = str(getattr(args, "_canonical_selected_or_model", "") or "").strip()
    if bound_selected_or_model:
        return bound_selected_or_model
    eligibility = evaluate_productive_dev_workhorse_path(
        path_id=args.path_id,
        task_class=args.task_class,
        estimated_or_cost=args.estimated_or_cost,
    )
    return _bind_canonical_selected_or_model(args, _resolve_selected_or_model(args, eligibility))


def _build_pre_call_cost_basis(eligibility: dict[str, Any]) -> dict[str, Any] | None:
    budget_profile_name = str(eligibility.get("budget_profile") or "").strip()
    per_call_cap = eligibility.get("per_call_cap_usd")
    session_cap = eligibility.get("session_cap_usd")
    if not budget_profile_name:
        return None
    if not isinstance(per_call_cap, (int, float)) or not isinstance(session_cap, (int, float)):
        return None
    config = _load_json(BUDGET_PROFILE_CONFIG_PATH)
    profile = ((config.get("profiles") or {}).get(budget_profile_name)) if isinstance(config, dict) else None
    description = str((profile or {}).get("description") or "").strip()
    if not description:
        return None
    display_text = (
        f"Budgetprofil {budget_profile_name}: per-call cap {float(per_call_cap):.9f}, "
        f"session cap {float(session_cap):.9f}, {description}"
    )
    return {
        "budget_profile": budget_profile_name,
        "per_call_cap_usd": float(per_call_cap),
        "session_cap_usd": float(session_cap),
        "description": description,
        "display_text": display_text,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_single_jsonl_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _build_session_paths(workflow_id: str) -> tuple[Path, Path]:
    session_dir = SESSION_RUNS_DIR / workflow_id
    session_jsonl = (
        MODEL_ROUTING_DIR
        / f"or_healthcheck_telemetry_productive_dev_workhorse_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
    )
    return session_dir, session_jsonl


def _actual_cost_from_response_summary(response_summary: dict[str, Any]) -> float | None:
    value = response_summary.get("actual_or_cost")
    if isinstance(value, (int, float)):
        return float(value)
    usage = response_summary.get("usage")
    if isinstance(usage, dict):
        cost = usage.get("cost")
        if isinstance(cost, (int, float)):
            return float(cost)
    return None


def _build_session_telemetry_row(args: argparse.Namespace, result: dict[str, Any]) -> dict[str, Any]:
    canonical_selected_or_model = _resolve_canonical_selected_or_model(args)
    response_summary_path = result.get("response_summary_path")
    response_summary: dict[str, Any] = {}
    if isinstance(response_summary_path, str) and response_summary_path and Path(response_summary_path).exists():
        response_summary = _load_json(Path(response_summary_path))
    usage = response_summary.get("usage") if isinstance(response_summary.get("usage"), dict) else {}
    actual_cost = result.get("actual_or_cost")
    if not isinstance(actual_cost, (int, float)):
        actual_cost = _actual_cost_from_response_summary(response_summary)
    estimated_cost = float(args.estimated_or_cost) if args.estimated_or_cost is not None else 0.0
    usage_source = (
        "response_usage"
        if usage
        else "fallback_estimate"
        if str(result.get("selected_path", "")).startswith("abort_post")
        else "dispatcher_result_only"
        if str(result.get("selected_path", "")).startswith("delegated")
        else "local_codex_only"
    )
    if actual_cost is not None and estimated_cost:
        estimation_error_percent = round(((float(actual_cost) - estimated_cost) / estimated_cost) * 100.0, 2)
        cost_delta = round(float(actual_cost) - estimated_cost, 8)
    else:
        estimation_error_percent = 0.0
        cost_delta = 0.0
    validation_result = str(result.get("validation_result", "PASS"))
    selected_path = str(result.get("selected_path", ""))
    final_outcome = str(result.get("final_outcome", "N_A"))
    recommendation_signal = (
        "OR_PREFERRED"
        if validation_result == "PASS" and selected_path.startswith("delegated")
        else "CODEX_PREFERRED"
    )
    return {
        "workflow_id": args.workflow_id,
        "skill_id": args.task_class,
        "routing_mode": "productive_dev_workhorse_path",
        "selected_path": selected_path,
        "codex_default_model": args.normal_target_model,
        "or_model": canonical_selected_or_model or "N_A",
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "estimated_or_cost": estimated_cost,
        "cost_estimate_confidence_percent": float(args.cost_estimate_confidence_percent or 0.0),
        "cost_estimate_sample_count": 0,
        "cost_estimate_mean_abs_error_percent": 0.0,
        "cost_estimate_p50_error_percent": 0.0,
        "cost_estimate_p90_error_percent": 0.0,
        "cost_estimate_basis": "productive_dev_workhorse_runner",
        "prompt_template_hash": f"{args.task_class}_dev_workhorse_v1",
        "task_variant": args.task_class,
        "price_snapshot_source": "N_A",
        "price_snapshot_timestamp": "",
        "actual_prompt_tokens": int(usage.get("prompt_tokens", 0)) if usage else 0,
        "actual_completion_tokens": int(usage.get("completion_tokens", 0)) if usage else 0,
        "actual_reasoning_tokens": int(usage.get("reasoning_tokens", 0)) if usage else 0,
        "actual_cached_tokens": int(usage.get("cached_tokens", 0)) if usage else 0,
        "actual_or_cost": float(actual_cost) if isinstance(actual_cost, (int, float)) else 0.0,
        "generation_id": str(result.get("generation_id") or response_summary.get("generation_id") or ""),
        "usage_source": usage_source,
        "estimated_codex_effort": "medium",
        "estimation_error_percent": estimation_error_percent,
        "cost_delta_vs_codex_estimate": cost_delta,
        "latency_ms": int(result.get("latency_ms", 0) or 0),
        "validation_result": validation_result,
        "fallback_used": str(result.get("fallback_used", "NO")),
        "rework_required": str(result.get("rework_required", "NO")),
        "final_outcome": final_outcome,
        "reason_for_escalation": "",
        "quality_notes": "Dedicated productive Dev-workhorse telemetry closeout.",
        "recommendation_signal": recommendation_signal,
        "codex_owned_outcome_status": str(result.get("codex_owned_outcome_status", "N_A")),
    }


def _run_healthcheck(session_jsonl_path: Path, session_dir: Path) -> tuple[str, str]:
    command = [
        sys.executable,
        str(HEALTH_SNAPSHOT_PATH),
        "--repo",
        str(REPO_ROOT),
        "--or-telemetry-jsonl",
        str(session_jsonl_path),
    ]
    completed = _run_command(command)
    _write_text(session_dir / "healthcheck_stdout.log", completed.stdout)
    _write_text(session_dir / "healthcheck_stderr.log", completed.stderr)
    _write_text(session_dir / "healthcheck_command.txt", " ".join(command) + "\n")
    if completed.returncode != 0:
        return "FAIL", ""
    parsed = _parse_json_output(completed.stdout, "productive Dev-workhorse healthcheck")
    healthcheck_path = session_dir / "healthcheck_summary.json"
    _write_json(healthcheck_path, parsed)
    return "PASS", str(healthcheck_path)


def _augment_operator_result_lines(result: dict[str, Any], row: dict[str, Any]) -> list[str]:
    lines = [str(line) for line in result.get("operator_result_lines", []) if isinstance(line, str)]
    if not any("Tatsaechliche Kosten:" in line for line in lines):
        if str(row.get("usage_source")) == "response_usage":
            lines.append(f"Tatsaechliche Kosten: {float(row['actual_or_cost']):.9f}")
        elif str(row.get("usage_source")) == "fallback_estimate" or str(row.get("selected_path", "")).startswith(
            "delegated"
        ):
            lines.append("Tatsaechliche Kosten: N/A (usage missing, fallback documented)")
        else:
            lines.append("Tatsaechliche Kosten: N/A (Codex-only Pfad)")
    return lines


def finalize_productive_dev_workhorse_result(
    args: argparse.Namespace,
    result: dict[str, Any],
) -> dict[str, Any]:
    session_dir, session_jsonl_path = _build_session_paths(args.workflow_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    _write_json(session_dir / "dispatcher_result.json", result)
    row = _build_session_telemetry_row(args, result)
    _write_single_jsonl_row(session_jsonl_path, row)
    _write_json(session_dir / "session_telemetry_row.json", row)
    healthcheck_status, healthcheck_summary_path = _run_healthcheck(session_jsonl_path, session_dir)
    augmented = dict(result)
    augmented["session_run_dir"] = str(session_dir)
    augmented["session_telemetry_jsonl_path"] = str(session_jsonl_path)
    augmented["session_telemetry_row_path"] = str(session_dir / "session_telemetry_row.json")
    augmented["dev_workhorse_healthcheck_status"] = healthcheck_status
    augmented["dev_workhorse_healthcheck_summary_path"] = healthcheck_summary_path
    augmented["actual_or_cost"] = row["actual_or_cost"]
    augmented["generation_id"] = row["generation_id"]
    augmented["operator_result_lines"] = _augment_operator_result_lines(result, row)
    augmented["operator_message"] = (
        f"{result.get('operator_message', '').strip()} "
        f"Session telemetry and healthcheck visibility were finalized for the dedicated Dev-workhorse path."
    ).strip()
    _write_json(session_dir / "operator_summary.json", augmented)
    return augmented


def _build_dispatcher_command(args: argparse.Namespace) -> list[str]:
    canonical_selected_or_model = _resolve_canonical_selected_or_model(args)
    command = [
        sys.executable,
        str(DISPATCHER_PATH),
        "--task-class",
        args.task_class,
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        args.workflow_id,
        "--selected-or-model",
        canonical_selected_or_model,
        "--estimated-or-cost",
        str(args.estimated_or_cost),
        "--cost-estimate-confidence-percent",
        str(args.cost_estimate_confidence_percent),
    ]
    if args.task_class == "execution_patch_candidate":
        if args.execution_input_package is None:
            raise SystemExit("execution_patch_candidate requires --execution-input-package")
        command.extend(["--execution-input-package", str(args.execution_input_package.resolve())])
        if args.execution_fixture_result is not None:
            command.extend(["--execution-fixture-result", str(args.execution_fixture_result.resolve())])
    elif args.task_class == "execution_write_apply_candidate":
        if args.execution_input_package is not None:
            command.extend(["--execution-input-package", str(args.execution_input_package.resolve())])
        elif args.accepted_source_run_dir is not None:
            command.extend(["--accepted-source-run-dir", str(args.accepted_source_run_dir.resolve())])
        else:
            raise SystemExit(
                "execution_write_apply_candidate requires --execution-input-package or --accepted-source-run-dir"
            )
        if getattr(args, "execution_live_sidecar", False):
            command.extend(
                [
                    "--execution-sidecar-model",
                    args.execution_sidecar_model,
                    "--execution-sidecar-timeout-seconds",
                    str(args.execution_sidecar_timeout_seconds),
                    "--execution-live-sidecar",
                ]
            )
    if args.use_local_or_fixture:
        command.append("--use-local-or-fixture")
        if args.or_local_fixture_response_path is not None:
            command.extend(["--or-local-fixture-response-path", str(args.or_local_fixture_response_path.resolve())])
    if args.execute_direct_or:
        command.append("--execute-direct-or")
    return command


def invoke_bounded_delegation_dispatch(args: argparse.Namespace) -> dict[str, Any]:
    completed = _run_command(_build_dispatcher_command(args))
    if completed.returncode != 0:
        raise SystemExit(
            "bounded delegated runtime dispatch failed:\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return _parse_json_output(completed.stdout, "bounded delegated runtime dispatch")


def _base_gate_payload(
    *,
    workflow_id: str,
    task_label: str,
    task_class: str,
    normal_target_model: str,
    eligibility: dict[str, Any],
) -> dict[str, Any]:
    return {
        "summary_header": "PRODUCTIVE DEV WORKHORSE GATE",
        "workflow_id": workflow_id,
        "task_label": task_label,
        "task_class": task_class,
        "normal_target_model": normal_target_model,
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "validation_result": "PASS",
    }


def prompt_summary(args: argparse.Namespace) -> dict[str, Any]:
    eligibility = evaluate_productive_dev_workhorse_path(
        path_id=args.path_id,
        task_class=args.task_class,
        estimated_or_cost=args.estimated_or_cost,
    )
    base = _base_gate_payload(
        workflow_id=args.workflow_id,
        task_label=args.task_label,
        task_class=args.task_class,
        normal_target_model=args.normal_target_model,
        eligibility=eligibility,
    )
    if eligibility["eligibility_result"] != "OR_ALLOWED":
        return {
            **base,
            "selected_path": "codex_only_pre_gate",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_result_lines": [
                f"Ergebnis: {eligibility['eligibility_result']}",
                "Route: Codex-only vor dem sichtbaren Gate",
            ],
            "operator_message": eligibility["message"],
            "budget_profile": eligibility.get("budget_profile", "N_A"),
            "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
            "session_cap_usd": eligibility.get("session_cap_usd"),
        }
    visibility = evaluate_existing_skill_operator_gate_visibility(
        subject_type="productive_dev_workhorse_task_class",
        subject_id=args.task_class,
    )
    if visibility["operator_gate_visibility"] != "VISIBLE":
        return {
            **build_visibility_suppressed_result(
                workflow_id=args.workflow_id,
                task_label=args.task_label,
                selected_path="codex_only_visibility_hidden",
                final_outcome="LOCAL_CODEX_PATH_SELECTED",
                normal_target_model=args.normal_target_model,
                visibility_status=visibility["visibility_status"],
                suppression_reason=visibility["reason_code"],
                selected_or_model=visibility.get("selected_or_model") or None,
                skill="janus-executioner",
                task_class=args.task_class,
                evidence_status=eligibility["evidence_status"],
            ),
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility["evidence_status"],
            "budget_profile": eligibility.get("budget_profile", "N_A"),
            "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
            "session_cap_usd": eligibility.get("session_cap_usd"),
        }

    roi = _build_or_roi(args)
    if _should_enforce_roi(args) and roi["status"] != "POSITIVE":
        return {
            **base,
            "selected_path": "codex_only_or_roi_gate",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "or_roi": roi,
            "operator_result_lines": [
                "Ergebnis: OR ROI Gate negativ oder unvollstaendig",
                "Route: Codex direkt, weil OR voraussichtlich keine Netto-Codex-Ersparnis bringt",
                roi["message"],
            ],
            "operator_message": (
                "The task stays on Codex because the estimated Codex savings do not clearly exceed "
                "the Codex overhead for OR briefing, orchestration, and review."
            ),
            "budget_profile": eligibility.get("budget_profile", "N_A"),
            "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
            "session_cap_usd": eligibility.get("session_cap_usd"),
        }

    selected_or_model = _bind_canonical_selected_or_model(args, _resolve_selected_or_model(args, eligibility))
    pre_call_cost_basis = _build_pre_call_cost_basis(eligibility)
    missing_fields = missing_gate_fields(
        selected_or_model=selected_or_model,
        estimated_or_cost=args.estimated_or_cost,
        cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
    )
    if pre_call_cost_basis is None:
        missing_fields.append("pre_call_cost_basis")
    if missing_fields:
        return {
            **build_missing_gate_result(
                workflow_id=args.workflow_id,
                task_label=args.task_label,
                selected_path="codex_only_prompt_data_missing",
                missing_fields=missing_fields,
                final_outcome="LOCAL_CODEX_PATH_SELECTED",
                normal_target_model=args.normal_target_model,
                task_class=args.task_class,
                eligibility_result=eligibility["eligibility_result"],
                eligibility_reason_code=eligibility["reason_code"],
                evidence_status=eligibility.get("evidence_status", "N_A"),
            ),
            "summary_header": "PRODUCTIVE DEV WORKHORSE GATE",
            "budget_profile": eligibility.get("budget_profile", "N_A"),
            "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
            "session_cap_usd": eligibility.get("session_cap_usd"),
        }

    operator_prompt_lines = build_operator_prompt_lines(
        choice_2_label="OR",
        selected_or_model=selected_or_model,
        pre_call_cost_basis=pre_call_cost_basis["display_text"],
        estimated_or_cost=float(args.estimated_or_cost),
        cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
    )
    if roi["status"] in {"POSITIVE", "NEGATIVE"}:
        operator_prompt_lines.append(
            "OR ROI Gate: "
            f"{roi['status']} (geschaetzte Codex-Ersparnis {roi['estimated_codex_saved_tokens']} Tokens, "
            f"OR-Overhead {roi['estimated_codex_or_overhead_tokens']} Tokens, "
            f"netto {roi['net_codex_saved_tokens']} Tokens)"
        )

    return {
        **base,
        "selected_path": "awaiting_operator_choice",
        "selected_or_model": selected_or_model,
        "or_roi": roi,
        "pre_call_cost_basis": pre_call_cost_basis["display_text"],
        "budget_profile_description": pre_call_cost_basis["description"],
        "estimated_or_cost": float(args.estimated_or_cost),
        "cost_estimate_confidence_percent": float(args.cost_estimate_confidence_percent),
        "budget_profile": eligibility.get("budget_profile", "N_A"),
        "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
        "session_cap_usd": eligibility.get("session_cap_usd"),
        "choice_1": "Codex",
        "choice_2": "OR",
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "operator_prompt_lines": operator_prompt_lines,
        "boundaries": [
            "This slice grants no new delegated runtime approval; any existing delegated runtime stays bounded to the sealed productive contract",
            "No production routing",
            "No canonical routing-table update",
            "Codex remains final owner",
        ],
        "operator_message": (
            "The visible Dev-workhorse gate is available with one fixed recommended OR model and one explicit pre-call "
            "cost basis from the sealed productive contract. Codex remains the final owner. If the operator selects "
            "`2 = OR`, the runner uses the already existing bounded delegated runtime path, while this slice itself "
            "grants no new runtime approval."
        ),
    }


def local_summary(args: argparse.Namespace) -> dict[str, Any]:
    eligibility = evaluate_productive_dev_workhorse_path(
        path_id=args.path_id,
        task_class=args.task_class,
        estimated_or_cost=args.estimated_or_cost,
    )
    base = _base_gate_payload(
        workflow_id=args.workflow_id,
        task_label=args.task_label,
        task_class=args.task_class,
        normal_target_model=args.normal_target_model,
        eligibility=eligibility,
    )
    return {
        **base,
        "selected_path": "codex_only_operator_choice",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "operator_result_lines": [
            "Ergebnis: Codex lokal ausgewaehlt",
            "Route: dedizierter Dev-Workhorse-Schritt bleibt lokal",
        ],
        "operator_message": "Operator chose the local Codex path. No delegated helper was invoked.",
    }


def or_choice_summary(args: argparse.Namespace) -> dict[str, Any]:
    gate = prompt_summary(args)
    if gate["final_outcome"] != "AWAITING_OPERATOR_CHOICE":
        return gate
    return invoke_bounded_delegation_dispatch(args)


def normalize_choice(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "prompt":
        return "prompt"
    if normalized in {"local", "codex", "1"}:
        return "local"
    if normalized in {"or", "2", "openrouter", "opr"}:
        return "or"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, or/2/openrouter/opr")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dedicated productive Dev-workhorse entry runner.")
    parser.add_argument("--task-class", required=True, choices=sorted(ALLOWED_TASK_CLASSES))
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--path-id", default="productive_dev_workhorse_path")
    parser.add_argument("--selected-or-model", default=None)
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--test-triage-input-package", type=Path, default=None)
    parser.add_argument("--test-triage-fixture-result", type=Path, default=None)
    parser.add_argument("--execution-input-package", type=Path, default=None)
    parser.add_argument("--execution-fixture-result", type=Path, default=None)
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    parser.add_argument("--execution-sidecar-model", default="gpt-5.4")
    parser.add_argument("--execution-sidecar-timeout-seconds", type=int, default=180)
    parser.add_argument("--execution-live-sidecar", action="store_true")
    parser.add_argument("--use-local-or-fixture", action="store_true")
    parser.add_argument("--or-local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--execute-direct-or", action="store_true")
    parser.add_argument("--estimated-codex-saved-tokens", type=int, default=None)
    parser.add_argument("--estimated-codex-or-overhead-tokens", type=int, default=None)
    parser.add_argument("--minimum-net-codex-saved-tokens", type=int, default=0)
    parser.add_argument("--require-positive-or-roi", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    choice = normalize_choice(args.operator_choice)
    if choice == "prompt":
        payload = prompt_summary(args)
    elif choice == "local":
        payload = finalize_productive_dev_workhorse_result(args, local_summary(args))
    else:
        payload = finalize_productive_dev_workhorse_result(args, or_choice_summary(args))
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
