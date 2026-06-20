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


def _load_dispatcher_module():
    import codex_bounded_delegation_dispatcher as dispatcher

    return dispatcher


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
        result = dispatcher.with_codex_owned_outcome(dispatcher.prompt_summary(args, workflow_id))
        write_json(run_dir / "consumer_operator_choice_prompt.json", result)
        return result
    if choice == "local":
        result = dispatcher.with_codex_owned_outcome(dispatcher.local_summary(args, workflow_id))
        write_json(run_dir / "consumer_operator_choice_local.json", result)
        return result
    result = dispatcher.with_codex_owned_outcome(dispatcher.invoke_debug_hypothesis_review(args, workflow_id))
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

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
            estimated_or_cost=args.estimated_or_cost,
            cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
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
    if args.fixture_result_json is None:
        raise SystemExit("--fixture-result-json is required for operator-choice delegated in local validation mode")

    input_payload = load_json(args.input_package_json.resolve())
    input_issues = validate_input_package(input_payload)
    write_json(run_dir / "input_package.json", input_payload)

    result_payload = load_json(args.fixture_result_json.resolve())
    result_issues = validate_result_payload(result_payload)
    delegated_result_markdown = render_result_markdown(result_payload)
    write_text(run_dir / "delegated_result.md", delegated_result_markdown)

    validation_pass = not input_issues and not result_issues
    validation_summary = {
        "workflow_id": workflow_id,
        "input_validation_pass": not input_issues,
        "result_validation_pass": not result_issues,
        "input_issues": input_issues,
        "result_issues": result_issues,
        "redaction_ready": input_payload.get("redaction_ready"),
        "redaction_check": result_payload.get("redaction_check"),
        "accepted_for_local_debug": validation_pass and result_payload.get("status") == "PASS",
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    operator_summary = {
        "summary_header": "DEBUG HYPOTHESIS REVIEW RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-debug",
        "task_label": args.task_label,
        "selected_path": "delegated_assist_only_hypothesis_review",
        "normal_target_model": args.normal_target_model,
        "delegated_model_label": args.delegated_model_label,
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": (
            "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION"
            if validation_pass
            else "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK"
        ),
        "input_package_path": str(run_dir / "input_package.json"),
        "delegated_result_path": str(run_dir / "delegated_result.md"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "operator_message": (
            "Delegated debug hypothesis review stayed bounded and assist-only. Codex must still validate the hypotheses and choose the next local debug step."
            if validation_pass
            else "Delegated debug hypothesis review failed bounded validation. Fallback to Codex-only debug is required."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
