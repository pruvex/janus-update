#!/usr/bin/env python3
"""Bounded assist-only helper for janus-debug hypothesis review flows.

This helper does not execute local commands, apply patches, or claim fixes.
It packages a redacted debug input, validates a fixture or prebuilt delegated
result, and emits normalized operator-facing artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from argparse import Namespace


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "debug-review-runs"
if str(MODEL_ROUTING_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))

from bounded_or_worker_gate_prompt import (
    build_missing_gate_result,
    build_operator_prompt_lines,
    missing_gate_fields,
)
from bounded_or_worker_eligibility import evaluate_productive_janus_debug_consumer

REQUIRED_INPUT_FIELDS = [
    "workflow_id",
    "bound_skill_context",
    "expected_behavior",
    "actual_behavior",
    "evidence_snippets",
    "iteration_number",
    "explicit_question",
    "redaction_ready",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "primary_failure_code",
    "likely_subsystem",
    "hypotheses",
    "suggested_local_verifiers",
    "instrumentation_suggestion",
    "escalation_trigger",
    "redaction_check",
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


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    snippets = payload.get("evidence_snippets")
    if not isinstance(snippets, list) or not snippets:
        issues.append("evidence_snippets must be a non-empty list")
    elif len(snippets) > 3:
        issues.append("evidence_snippets must contain at most 3 items")
    if payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")
    return issues


def validate_result_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in payload:
            issues.append(f"missing result field: {field}")
    hypotheses = payload.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses:
        issues.append("hypotheses must be a non-empty list")
    else:
        if len(hypotheses) > 3:
            issues.append("hypotheses must contain at most 3 items")
        for index, item in enumerate(hypotheses, start=1):
            if not isinstance(item, dict):
                issues.append(f"hypothesis {index} must be an object")
                continue
            for key in ["title", "confidence", "evidence"]:
                if not item.get(key):
                    issues.append(f"hypothesis {index} missing {key}")
            if item.get("confidence") not in {"LOW", "MEDIUM", "HIGH"}:
                issues.append(f"hypothesis {index} confidence must be LOW, MEDIUM, or HIGH")
    if payload.get("redaction_check") != "PASS":
        issues.append("redaction_check must be PASS")
    if payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status must be PASS, WEAK_SIGNAL, or BLOCKED")
    return issues


def render_result_markdown(result_payload: dict[str, Any]) -> str:
    lines = [
        "DEBUG_HYPOTHESIS_REVIEW",
        f"Status: {result_payload['status']}",
        f"Primary Failure Code: {result_payload['primary_failure_code']}",
        f"Likely Subsystem: {result_payload['likely_subsystem']}",
    ]
    hypotheses = result_payload["hypotheses"]
    for index, item in enumerate(hypotheses, start=1):
        lines.extend(
            [
                f"Hypothesis {index}: {item['title']}",
                f"Hypothesis {index} Confidence: {item['confidence']}",
                f"Hypothesis {index} Evidence: {item['evidence']}",
            ]
        )
    if len(hypotheses) < 3:
        for index in range(len(hypotheses) + 1, 4):
            lines.extend(
                [
                    f"Hypothesis {index}: N/A",
                    f"Hypothesis {index} Confidence: N/A",
                    f"Hypothesis {index} Evidence: N/A",
                ]
            )
    lines.extend(
        [
            f"Suggested Local Verifiers: {result_payload['suggested_local_verifiers']}",
            f"Instrumentation Suggestion: {result_payload['instrumentation_suggestion']}",
            f"Escalation Trigger: {result_payload['escalation_trigger']}",
            f"Redaction Check: {result_payload['redaction_check']}",
            f"Notes: {result_payload['notes']}",
        ]
    )
    return "\n".join(lines) + "\n"


def prompt_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    delegated_model_label: str,
    estimated_or_cost: float | None,
    cost_estimate_confidence_percent: float | None,
) -> dict[str, Any]:
    missing_fields = missing_gate_fields(
        selected_or_model=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
    )
    if missing_fields:
        return build_missing_gate_result(
            workflow_id=workflow_id,
            task_label=task_label,
            selected_path="codex_only_prompt_data_missing",
            missing_fields=missing_fields,
            final_outcome="LOCAL_CODEX_PATH_SELECTED",
            normal_target_model=normal_target_model,
            skill="janus-debug",
        )
    return {
        "summary_header": "DEBUG HYPOTHESIS REVIEW GATE",
        "workflow_id": workflow_id,
        "skill": "janus-debug",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "selected_or_model": delegated_model_label,
        "estimated_or_cost": float(estimated_or_cost),
        "cost_estimate_confidence_percent": float(cost_estimate_confidence_percent),
        "choice_1": "Codex",
        "choice_2": "OR-Arbeitspferd",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded assist-only hypothesis review with no local execution and no final fix claim",
        "operator_prompt_lines": build_operator_prompt_lines(
            choice_2_label="OR-Arbeitspferd",
            selected_or_model=delegated_model_label,
            estimated_or_cost=float(estimated_or_cost),
            cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
        ),
        "boundaries": [
            "No delegated local command execution",
            "No delegated test execution",
            "No delegated final fix claim",
            "Codex remains validation and acceptance owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "DEBUG HYPOTHESIS REVIEW RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-debug",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex debug path. No delegated hypothesis review was used.",
    }


def delegated_selection_recorded_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    delegated_model_label: str,
    estimated_or_cost: float | None,
    cost_estimate_confidence_percent: float | None,
    gate_result: dict[str, Any],
    input_package_path: Path | None,
) -> dict[str, Any]:
    return {
        "summary_header": "DEBUG HYPOTHESIS REVIEW GATE",
        "workflow_id": workflow_id,
        "skill": "janus-debug",
        "task_label": task_label,
        "selected_path": "delegated_selection_recorded_pending_task_spec23_2",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "selected_or_model": delegated_model_label,
        "estimated_or_cost": float(estimated_or_cost) if estimated_or_cost is not None else None,
        "cost_estimate_confidence_percent": (
            float(cost_estimate_confidence_percent)
            if cost_estimate_confidence_percent is not None
            else None
        ),
        "eligibility_result": gate_result.get("eligibility_result"),
        "eligibility_reason_code": gate_result.get("eligibility_reason_code"),
        "evidence_status": gate_result.get("evidence_status", "N_A"),
        "budget_profile": gate_result.get("budget_profile", "N_A"),
        "per_call_cap_usd": gate_result.get("per_call_cap_usd"),
        "session_cap_usd": gate_result.get("session_cap_usd"),
        "execution_status": "NOT_STARTED_SCOPE_BOUNDARY",
        "task_scope_boundary": "TASK-SPEC23.2_REQUIRED_FOR_DELEGATED_EXECUTION",
        "input_package_path": str(input_package_path) if input_package_path else None,
        "validation_result": "PASS",
        "final_outcome": "DELEGATED_SELECTION_RECORDED_PENDING_TASK_SPEC23_2",
        "operator_message": (
            "Operator chose OR-Arbeitspferd, but TASK-SPEC23.1 stays gate-only. "
            "The bounded selection was recorded and no delegated hypothesis review executed."
        ),
    }


def build_consumer_input_package(
    *,
    workflow_id: str,
    bound_skill_context: str,
    expected_behavior: str,
    actual_behavior: str,
    evidence_snippets: list[str],
    iteration_number: int,
    explicit_question: str,
    failure_code: str | None = None,
    redaction_ready: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "workflow_id": workflow_id,
        "bound_skill_context": bound_skill_context,
        "expected_behavior": expected_behavior,
        "actual_behavior": actual_behavior,
        "evidence_snippets": evidence_snippets,
        "iteration_number": iteration_number,
        "explicit_question": explicit_question,
        "redaction_ready": redaction_ready,
    }
    if failure_code:
        payload["failure_code"] = failure_code
    return payload


def evaluate_productive_gate(
    *,
    estimated_or_cost: float | None,
    input_payload: dict[str, Any] | None,
    task_class: str = "debug_hypothesis_review",
) -> dict[str, Any]:
    return evaluate_productive_janus_debug_consumer(
        task_class=task_class,
        estimated_or_cost=estimated_or_cost,
        request_payload=input_payload,
    )


def productive_gate_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    delegated_model_label: str,
    estimated_or_cost: float | None,
    cost_estimate_confidence_percent: float | None,
    input_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    eligibility = evaluate_productive_gate(
        estimated_or_cost=estimated_or_cost,
        input_payload=input_payload,
    )
    if eligibility["eligibility_result"] != "OR_ALLOWED":
        return {
            "summary_header": "DEBUG HYPOTHESIS REVIEW GATE",
            "workflow_id": workflow_id,
            "skill": "janus-debug",
            "task_label": task_label,
            "selected_path": "codex_only_pre_gate",
            "normal_target_model": normal_target_model,
            "delegated_model_label": delegated_model_label,
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility.get("evidence_status", "N_A"),
            "budget_profile": eligibility.get("budget_profile", "N_A"),
            "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
            "session_cap_usd": eligibility.get("session_cap_usd"),
            "validation_result": "PASS",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_result_lines": [
                f"Ergebnis: {eligibility['eligibility_result']}",
                "Route: janus-debug bleibt Codex-only vor dem sichtbaren OR-Gate",
            ],
            "operator_message": eligibility["message"],
        }
    return {
        **prompt_summary(
            workflow_id=workflow_id,
            task_label=task_label,
            normal_target_model=normal_target_model,
            delegated_model_label=delegated_model_label,
            estimated_or_cost=estimated_or_cost,
            cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        ),
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility.get("evidence_status", "N_A"),
        "budget_profile": eligibility.get("budget_profile", "N_A"),
        "per_call_cap_usd": eligibility.get("per_call_cap_usd"),
        "session_cap_usd": eligibility.get("session_cap_usd"),
    }


def _load_dispatcher_module():
    import codex_bounded_delegation_dispatcher as dispatcher

    return dispatcher


def _resolve_input_payload(
    *,
    input_payload: dict[str, Any] | None,
    input_package_path: Path | None,
) -> dict[str, Any] | None:
    if input_payload is not None:
        return input_payload
    if input_package_path is None:
        return None
    return load_json(input_package_path.resolve())


def run_consumer_flow(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    operator_choice: str,
    delegated_model_label: str,
    estimated_or_cost: float | None = None,
    cost_estimate_confidence_percent: float | None = None,
    input_payload: dict[str, Any] | None = None,
    input_package_path: Path | None = None,
    fixture_result_json: Path | None = None,
    use_local_or_fixture: bool = False,
    execute_direct_or: bool = False,
    or_local_fixture_response_path: Path | None = None,
) -> dict[str, Any]:
    dispatcher = _load_dispatcher_module()
    choice = normalize_choice(operator_choice)
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if input_payload is not None:
        package_path = run_dir / "consumer_input_package.json"
        write_json(package_path, input_payload)
        input_package_path = package_path

    args = Namespace(
        task_class="debug_hypothesis_review",
        task_label=task_label,
        normal_target_model=normal_target_model,
        selected_or_model=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        use_local_or_fixture=use_local_or_fixture,
        execute_direct_or=execute_direct_or,
        or_local_fixture_response_path=or_local_fixture_response_path,
        debug_input_package=input_package_path,
        debug_fixture_result=fixture_result_json,
        test_triage_input_package=None,
        test_triage_fixture_result=None,
    )

    if choice == "prompt":
        result = dispatcher.with_codex_owned_outcome(
            productive_gate_summary(
                workflow_id=workflow_id,
                task_label=task_label,
                normal_target_model=normal_target_model,
                delegated_model_label=delegated_model_label,
                estimated_or_cost=estimated_or_cost,
                cost_estimate_confidence_percent=cost_estimate_confidence_percent,
                input_payload=input_payload,
            )
        )
        write_json(run_dir / "consumer_operator_choice_prompt.json", result)
        return result
    if choice == "local":
        result = dispatcher.with_codex_owned_outcome(dispatcher.local_summary(args, workflow_id))
        write_json(run_dir / "consumer_operator_choice_local.json", result)
        return result
    resolved_input_payload = _resolve_input_payload(
        input_payload=input_payload,
        input_package_path=input_package_path,
    )
    gate_result = productive_gate_summary(
        workflow_id=workflow_id,
        task_label=task_label,
        normal_target_model=normal_target_model,
        delegated_model_label=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        input_payload=resolved_input_payload,
    )
    if gate_result["final_outcome"] != "AWAITING_OPERATOR_CHOICE":
        result = dispatcher.with_codex_owned_outcome(
            gate_result
        )
        write_json(run_dir / "consumer_operator_choice_delegated.json", result)
        return result
    result = dispatcher.with_codex_owned_outcome(
        delegated_selection_recorded_summary(
            workflow_id=workflow_id,
            task_label=task_label,
            normal_target_model=normal_target_model,
            delegated_model_label=delegated_model_label,
            estimated_or_cost=estimated_or_cost,
            cost_estimate_confidence_percent=cost_estimate_confidence_percent,
            gate_result=gate_result,
            input_package_path=input_package_path,
        )
    )
    write_json(run_dir / "consumer_operator_choice_delegated.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded debug hypothesis review helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default="bounded delegated review / fixture mode")
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--fixture-result-json", type=Path, default=None)
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"DEBUG-HYPOTHESIS-REVIEW-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    input_payload = None
    if args.input_package_json is not None:
        input_payload = load_json(args.input_package_json.resolve())
        write_json(run_dir / "input_package.json", input_payload)

    if choice == "prompt":
        result = productive_gate_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
            estimated_or_cost=args.estimated_or_cost,
            cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
            input_payload=input_payload,
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

    gate_result = productive_gate_summary(
        workflow_id=workflow_id,
        task_label=args.task_label,
        normal_target_model=args.normal_target_model,
        delegated_model_label=args.delegated_model_label,
        estimated_or_cost=args.estimated_or_cost,
        cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
        input_payload=input_payload,
    )
    if gate_result["final_outcome"] != "AWAITING_OPERATOR_CHOICE":
        write_json(run_dir / "operator_choice_delegated.json", gate_result)
        output(gate_result)
        return 0

    operator_summary = delegated_selection_recorded_summary(
        workflow_id=workflow_id,
        task_label=args.task_label,
        normal_target_model=args.normal_target_model,
        delegated_model_label=args.delegated_model_label,
        estimated_or_cost=args.estimated_or_cost,
        cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
        gate_result=gate_result,
        input_package_path=run_dir / "input_package.json",
    )
    write_json(run_dir / "operator_choice_delegated.json", operator_summary)
    output(operator_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
