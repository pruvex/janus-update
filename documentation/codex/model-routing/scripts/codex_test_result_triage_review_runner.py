#!/usr/bin/env python3
"""Bounded assist-only helper for janus-test-pipeline triage review flows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "test-triage-runs"
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
    "test_run_id",
    "result_outcome_summary",
    "evidence_snippets",
    "classification_question",
    "redaction_ready",
]

SUPPORTED_CLASSIFICATIONS = {
    "PRODUCT_BUG",
    "SPEC_GAP",
    "TEST_BUG",
    "INFRA_BLOCKER",
    "PROVIDER_BLOCKER",
    "AUTH_BLOCKER",
    "DUPLICATE",
    "NOT_REPRODUCIBLE",
}

REQUIRED_RESULT_FIELDS = [
    "status",
    "test_run_id",
    "primary_outcome",
    "likely_classification",
    "likely_subsystem",
    "finding_clusters",
    "suggested_next_local_verifiers",
    "suggested_routing",
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
    clusters = payload.get("finding_clusters")
    if not isinstance(clusters, list) or not clusters:
        issues.append("finding_clusters must be a non-empty list")
    else:
        if len(clusters) > 2:
            issues.append("finding_clusters must contain at most 2 items")
        for index, item in enumerate(clusters, start=1):
            if not isinstance(item, dict):
                issues.append(f"finding cluster {index} must be an object")
                continue
            for key in ["title", "confidence", "evidence"]:
                if not item.get(key):
                    issues.append(f"finding cluster {index} missing {key}")
            if item.get("confidence") not in {"LOW", "MEDIUM", "HIGH"}:
                issues.append(f"finding cluster {index} confidence must be LOW, MEDIUM, or HIGH")
    if payload.get("redaction_check") != "PASS":
        issues.append("redaction_check must be PASS")
    if payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status must be PASS, WEAK_SIGNAL, or BLOCKED")
    classification = payload.get("likely_classification")
    if classification not in SUPPORTED_CLASSIFICATIONS:
        issues.append(f"likely_classification must be one of: {', '.join(sorted(SUPPORTED_CLASSIFICATIONS))}")
    return issues


def render_result_markdown(result_payload: dict[str, Any]) -> str:
    lines = [
        "TEST_RESULT_TRIAGE_REVIEW",
        f"Status: {result_payload['status']}",
        f"TEST_RUN_ID: {result_payload['test_run_id']}",
        f"Primary Outcome: {result_payload['primary_outcome']}",
        f"Likely Classification: {result_payload['likely_classification']}",
        f"Likely Subsystem: {result_payload['likely_subsystem']}",
    ]
    clusters = result_payload["finding_clusters"]
    for index, item in enumerate(clusters, start=1):
        lines.extend(
            [
                f"Finding Cluster {index}: {item['title']}",
                f"Finding Cluster {index} Confidence: {item['confidence']}",
                f"Finding Cluster {index} Evidence: {item['evidence']}",
            ]
        )
    if len(clusters) < 2:
        lines.extend(
            [
                "Finding Cluster 2: N/A",
                "Finding Cluster 2 Confidence: N/A",
                "Finding Cluster 2 Evidence: N/A",
            ]
        )
    lines.extend(
        [
            f"Suggested Next Local Verifiers: {result_payload['suggested_next_local_verifiers']}",
            f"Suggested Routing: {result_payload['suggested_routing']}",
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
            skill="janus-test-pipeline",
        )
    return {
        "summary_header": "TEST RESULT TRIAGE REVIEW GATE",
        "workflow_id": workflow_id,
        "skill": "janus-test-pipeline",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "selected_or_model": delegated_model_label,
        "estimated_or_cost": float(estimated_or_cost),
        "cost_estimate_confidence_percent": float(cost_estimate_confidence_percent),
        "choice_1": "Codex",
        "choice_2": "OpenRouter",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded assist-only triage review with no live execution and no final PASS decision",
        "operator_prompt_lines": build_operator_prompt_lines(
            estimated_or_cost=float(estimated_or_cost),
            cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
        ),
        "boundaries": [
            "No delegated live test execution",
            "No delegated runner generation",
            "No delegated final PASS or release decision",
            "Codex remains validation and routing owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "TEST RESULT TRIAGE REVIEW RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-test-pipeline",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex triage path. No delegated triage review was used.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded test result triage review helper.")
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
    workflow_id = args.workflow_id or f"TEST-TRIAGE-REVIEW-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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
        "accepted_for_local_triage": validation_pass and result_payload.get("status") == "PASS",
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    operator_summary = {
        "summary_header": "TEST RESULT TRIAGE REVIEW RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-test-pipeline",
        "task_label": args.task_label,
        "selected_path": "delegated_assist_only_test_result_triage_review",
        "normal_target_model": args.normal_target_model,
        "delegated_model_label": args.delegated_model_label,
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": (
            "TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION"
            if validation_pass
            else "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK"
        ),
        "input_package_path": str(run_dir / "input_package.json"),
        "delegated_result_path": str(run_dir / "delegated_result.md"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "operator_message": (
            "Delegated test-result triage review stayed bounded and assist-only. Codex must still validate the classification and choose the next rerun or routing step."
            if validation_pass
            else "Delegated test-result triage review failed bounded validation. Fallback to Codex-only triage is required."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
