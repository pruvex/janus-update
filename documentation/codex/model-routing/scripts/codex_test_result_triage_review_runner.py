#!/usr/bin/env python3
"""Bounded assist-only helper for janus-test-pipeline triage review flows."""

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
RUN_ROOT = MODEL_ROUTING_DIR / "test-triage-runs"
DEFAULT_TEST_TRIAGE_OR_MODEL = "qwen/qwen3-coder-30b-a3b-instruct"
if str(MODEL_ROUTING_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))

from bounded_or_worker_gate_prompt import (
    build_missing_gate_result,
    build_operator_prompt_lines,
    build_or_roi,
    build_or_roi_gate_result,
    missing_gate_fields,
    should_enforce_or_roi,
)
from bounded_or_worker_eligibility import evaluate_assistive_or_workhorse_pilot

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
    estimated_codex_saved_tokens: int | None = None,
    estimated_codex_or_overhead_tokens: int | None = None,
    minimum_net_codex_saved_tokens: int = 0,
    require_positive_or_roi: bool = False,
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
    roi = build_or_roi(
        estimated_codex_saved_tokens=estimated_codex_saved_tokens,
        estimated_codex_or_overhead_tokens=estimated_codex_or_overhead_tokens,
        minimum_net_codex_saved_tokens=minimum_net_codex_saved_tokens,
    )
    if should_enforce_or_roi(
        estimated_codex_saved_tokens=estimated_codex_saved_tokens,
        estimated_codex_or_overhead_tokens=estimated_codex_or_overhead_tokens,
        require_positive_or_roi=require_positive_or_roi,
    ) and roi["status"] != "POSITIVE":
        return build_or_roi_gate_result(
            workflow_id=workflow_id,
            task_label=task_label,
            selected_path="codex_only_or_roi_gate",
            normal_target_model=normal_target_model,
            skill="janus-test-pipeline",
            task_class="test_result_triage_review",
            roi=roi,
        )
    operator_prompt_lines = build_operator_prompt_lines(
        choice_2_label="OR",
        selected_or_model=delegated_model_label,
        estimated_or_cost=float(estimated_or_cost),
        cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
    )
    if roi["status"] in {"POSITIVE", "NEGATIVE"}:
        operator_prompt_lines.append(
            "OR ROI Gate: "
            f"{roi['status']} (geschaetzte Codex-Ersparnis {roi['estimated_codex_saved_tokens']} Tokens, "
            f"OR-Overhead {roi['estimated_codex_or_overhead_tokens']} Tokens, "
            f"netto {roi['net_codex_saved_tokens']} Tokens)"
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
        "or_roi": roi,
        "choice_1": "Codex",
        "choice_2": "OR",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded assist-only triage review with no live execution and no final PASS decision",
        "operator_prompt_lines": operator_prompt_lines,
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


def build_consumer_input_package(
    *,
    workflow_id: str,
    bound_skill_context: str,
    test_run_id: str,
    result_outcome_summary: str,
    evidence_snippets: list[str],
    classification_question: str,
    candidate_blocker_category: str | None = None,
    redaction_ready: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "workflow_id": workflow_id,
        "bound_skill_context": bound_skill_context,
        "test_run_id": test_run_id,
        "result_outcome_summary": result_outcome_summary,
        "evidence_snippets": evidence_snippets,
        "classification_question": classification_question,
        "redaction_ready": redaction_ready,
    }
    if candidate_blocker_category:
        payload["candidate_blocker_category"] = candidate_blocker_category
    return payload


def evaluate_productive_gate(
    *,
    input_payload: dict[str, Any] | None,
    task_class: str = "test_result_triage_review",
) -> dict[str, Any]:
    return evaluate_assistive_or_workhorse_pilot(
        skill_id="janus-test-pipeline",
        task_class=task_class,
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
    estimated_codex_saved_tokens: int | None = None,
    estimated_codex_or_overhead_tokens: int | None = None,
    minimum_net_codex_saved_tokens: int = 0,
    require_positive_or_roi: bool = False,
) -> dict[str, Any]:
    eligibility = evaluate_productive_gate(input_payload=input_payload)
    if eligibility["eligibility_result"] != "OR_ALLOWED":
        return {
            "summary_header": "TEST RESULT TRIAGE REVIEW GATE",
            "workflow_id": workflow_id,
            "skill": "janus-test-pipeline",
            "task_label": task_label,
            "selected_path": "codex_only_pre_gate",
            "normal_target_model": normal_target_model,
            "delegated_model_label": delegated_model_label,
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility.get("evidence_status", "N_A"),
            "validation_result": "PASS",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_result_lines": [
                f"Ergebnis: {eligibility['eligibility_result']}",
                "Route: janus-test-pipeline bleibt Codex-only vor dem sichtbaren OR-Gate",
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
            estimated_codex_saved_tokens=estimated_codex_saved_tokens,
            estimated_codex_or_overhead_tokens=estimated_codex_or_overhead_tokens,
            minimum_net_codex_saved_tokens=minimum_net_codex_saved_tokens,
            require_positive_or_roi=require_positive_or_roi,
        ),
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility.get("evidence_status", "N_A"),
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
    estimated_codex_saved_tokens: int | None = None,
    estimated_codex_or_overhead_tokens: int | None = None,
    minimum_net_codex_saved_tokens: int = 0,
    require_positive_or_roi: bool = False,
) -> dict[str, Any]:
    dispatcher = _load_dispatcher_module()
    choice = normalize_choice(operator_choice)
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if input_payload is not None:
        package_path = run_dir / "consumer_input_package.json"
        write_json(package_path, input_payload)
        input_package_path = package_path
    resolved_input_payload = _resolve_input_payload(
        input_payload=input_payload,
        input_package_path=input_package_path,
    )

    args = Namespace(
        task_class="test_result_triage_review",
        task_label=task_label,
        normal_target_model=normal_target_model,
        selected_or_model=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        use_local_or_fixture=use_local_or_fixture,
        execute_direct_or=execute_direct_or,
        or_local_fixture_response_path=or_local_fixture_response_path,
        debug_input_package=None,
        debug_fixture_result=None,
        test_triage_input_package=input_package_path,
        test_triage_fixture_result=fixture_result_json,
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
                input_payload=resolved_input_payload,
                estimated_codex_saved_tokens=estimated_codex_saved_tokens,
                estimated_codex_or_overhead_tokens=estimated_codex_or_overhead_tokens,
                minimum_net_codex_saved_tokens=minimum_net_codex_saved_tokens,
                require_positive_or_roi=require_positive_or_roi,
            )
        )
        write_json(run_dir / "consumer_operator_choice_prompt.json", result)
        return result
    if choice == "local":
        result = dispatcher.with_codex_owned_outcome(dispatcher.local_summary(args, workflow_id))
        write_json(run_dir / "consumer_operator_choice_local.json", result)
        return result
    gate_result = productive_gate_summary(
        workflow_id=workflow_id,
        task_label=task_label,
        normal_target_model=normal_target_model,
        delegated_model_label=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        input_payload=resolved_input_payload,
        estimated_codex_saved_tokens=estimated_codex_saved_tokens,
        estimated_codex_or_overhead_tokens=estimated_codex_or_overhead_tokens,
        minimum_net_codex_saved_tokens=minimum_net_codex_saved_tokens,
        require_positive_or_roi=require_positive_or_roi,
    )
    if gate_result["final_outcome"] != "AWAITING_OPERATOR_CHOICE":
        result = dispatcher.with_codex_owned_outcome(gate_result)
        write_json(run_dir / "consumer_operator_choice_delegated.json", result)
        return result
    result = dispatcher.with_codex_owned_outcome(dispatcher.invoke_test_result_triage_review(args, workflow_id))
    write_json(run_dir / "consumer_operator_choice_delegated.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded test result triage review helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default=DEFAULT_TEST_TRIAGE_OR_MODEL)
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--fixture-result-json", type=Path, default=None)
    parser.add_argument("--use-local-or-fixture", action="store_true")
    parser.add_argument("--execute-direct-or", action="store_true")
    parser.add_argument("--or-local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--estimated-codex-saved-tokens", type=int, default=None)
    parser.add_argument("--estimated-codex-or-overhead-tokens", type=int, default=None)
    parser.add_argument("--minimum-net-codex-saved-tokens", type=int, default=0)
    parser.add_argument("--require-positive-or-roi", action="store_true")
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"TEST-TRIAGE-REVIEW-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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
            estimated_codex_saved_tokens=args.estimated_codex_saved_tokens,
            estimated_codex_or_overhead_tokens=args.estimated_codex_or_overhead_tokens,
            minimum_net_codex_saved_tokens=args.minimum_net_codex_saved_tokens,
            require_positive_or_roi=args.require_positive_or_roi,
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
    result = run_consumer_flow(
        workflow_id=workflow_id,
        task_label=args.task_label,
        normal_target_model=args.normal_target_model,
        operator_choice="delegated",
        delegated_model_label=args.delegated_model_label,
        estimated_or_cost=args.estimated_or_cost,
        cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
        input_payload=input_payload,
        input_package_path=run_dir / "input_package.json",
        fixture_result_json=args.fixture_result_json,
        use_local_or_fixture=args.use_local_or_fixture,
        execute_direct_or=args.execute_direct_or,
        or_local_fixture_response_path=args.or_local_fixture_response_path,
        estimated_codex_saved_tokens=args.estimated_codex_saved_tokens,
        estimated_codex_or_overhead_tokens=args.estimated_codex_or_overhead_tokens,
        minimum_net_codex_saved_tokens=args.minimum_net_codex_saved_tokens,
        require_positive_or_roi=args.require_positive_or_roi,
    )
    write_json(run_dir / "operator_choice_delegated.json", result)
    output(result)
    return 0 if result.get("validation_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
