#!/usr/bin/env python3
"""Generate bounded local-fixture skill-context evidence for TASK-SPEC21.4."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SCRIPTS_DIR = MODEL_ROUTING_DIR / "scripts"
DEBUG_RUNNER_PATH = SCRIPTS_DIR / "codex_debug_hypothesis_review_runner.py"
TRIAGE_RUNNER_PATH = SCRIPTS_DIR / "codex_test_result_triage_review_runner.py"

DEBUG_WORKFLOW_ID = "TASK-SPEC21-4-INSTALLED-DEBUG-001"
TRIAGE_WORKFLOW_ID = "TASK-SPEC21-4-INSTALLED-TRIAGE-001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_prompt_shape(prompt_result: dict[str, Any]) -> None:
    lines = prompt_result.get("operator_prompt_lines") or []
    expected_fragments = [
        "1 = Codex",
        "2 = OR-Arbeitspferd",
        "Voraussichtliche Kosten",
        "Genauigkeit",
    ]
    for fragment in expected_fragments:
        if not any(fragment in line for line in lines):
            raise SystemExit(f"Prompt evidence missing expected fragment: {fragment}")


def assert_delegated_shape(result: dict[str, Any]) -> None:
    if result.get("validation_result") != "PASS":
        raise SystemExit("Delegated evidence must validate with PASS")
    if result.get("codex_owned_outcome_status") != "DELEGATED_REVIEW_PENDING_CODEX_DECISION":
        raise SystemExit("Delegated evidence must stay Codex-owned and non-final")


def build_debug_fixture() -> dict[str, Any]:
    return {
        "status": "PASS",
        "primary_failure_code": "RUNNER_ARTIFACT_MISMATCH",
        "likely_subsystem": "test-runner packaging",
        "hypotheses": [
            {
                "title": "The runner consumed an older package shape.",
                "confidence": "HIGH",
                "evidence": "Current bounded package uses allowlist-only fields while the failing slice mentions legacy payload assumptions.",
            }
        ],
        "suggested_local_verifiers": "Compare the installed skill wording and rerun the bounded consumer helper with the refreshed package.",
        "instrumentation_suggestion": "Inspect the generated input package and validation summary before any broader debug action.",
        "escalation_trigger": "Escalate only if the installed skill copy still diverges after sync or the prompt gate stops showing cost/confidence.",
        "redaction_check": "PASS",
        "notes": "Local fixture only; no delegated command execution and no final fix claim.",
    }


def build_triage_fixture() -> dict[str, Any]:
    return {
        "status": "PASS",
        "test_run_id": "TEST-RUN-SPEC21-4",
        "primary_outcome": "INCONCLUSIVE",
        "likely_classification": "TEST_BUG",
        "likely_subsystem": "bounded triage package handoff",
        "finding_clusters": [
            {
                "title": "The bounded triage review remains review-only and should not mutate result evidence.",
                "confidence": "HIGH",
                "evidence": "The delegated summary returns a Codex-owned next-step state and keeps rerun and routing decisions local.",
            }
        ],
        "suggested_next_local_verifiers": "Review the operator summary and confirm Codex still owns classification and rerun choice.",
        "suggested_routing": "Keep the slice inside janus-test-pipeline until Codex finishes the local evidence interpretation.",
        "escalation_trigger": "Escalate if the installed skill wording drifts back to generic delegated wording or if prompt data goes missing.",
        "redaction_check": "PASS",
        "notes": "Local fixture only; no live test execution and no final PASS decision.",
    }


def run_debug_evidence(debug_runner) -> dict[str, Any]:
    run_dir = debug_runner.build_run_dir(DEBUG_WORKFLOW_ID)
    fixture_path = run_dir / "fixture_result.json"
    write_json(fixture_path, build_debug_fixture())

    prompt_result = debug_runner.run_consumer_flow(
        workflow_id=DEBUG_WORKFLOW_ID,
        task_label="installed janus-debug skill-context evidence",
        normal_target_model="5.4 medium",
        operator_choice="prompt",
        delegated_model_label="bounded delegated review / fixture mode",
        estimated_or_cost=0.0004,
        cost_estimate_confidence_percent=81.0,
    )
    assert_prompt_shape(prompt_result)

    delegated_result = debug_runner.run_consumer_flow(
        workflow_id=DEBUG_WORKFLOW_ID,
        task_label="installed janus-debug skill-context evidence",
        normal_target_model="5.4 medium",
        operator_choice="delegated",
        delegated_model_label="bounded delegated review / fixture mode",
        estimated_or_cost=0.0004,
        cost_estimate_confidence_percent=81.0,
        input_payload=debug_runner.build_consumer_input_package(
            workflow_id=DEBUG_WORKFLOW_ID,
            bound_skill_context="installed janus-debug skill copy",
            expected_behavior="The installed skill context should show the bounded Codex-vs-OR gate.",
            actual_behavior="The bounded delegated result should remain assist-only and Codex-owned.",
            evidence_snippets=[
                "Installed janus-debug skill now references build_consumer_input_package(...)",
                "Installed janus-debug skill now references run_consumer_flow(...)",
            ],
            iteration_number=1,
            explicit_question="Which local verifier should Codex run next after the bounded review?",
            failure_code="SPEC21_4_REAL_SKILL_CONTEXT_EVIDENCE_MISSING",
        ),
        fixture_result_json=fixture_path,
    )
    assert_delegated_shape(delegated_result)

    return {
        "workflow_id": DEBUG_WORKFLOW_ID,
        "run_dir": str(run_dir),
        "prompt_path": str(run_dir / "consumer_operator_choice_prompt.json"),
        "delegated_path": str(run_dir / "consumer_operator_choice_delegated.json"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "fixture_result_path": str(fixture_path),
        "prompt_result": read_json(run_dir / "consumer_operator_choice_prompt.json"),
        "delegated_result": read_json(run_dir / "consumer_operator_choice_delegated.json"),
        "validation_summary": read_json(run_dir / "validation_summary.json"),
    }


def run_triage_evidence(triage_runner) -> dict[str, Any]:
    run_dir = triage_runner.build_run_dir(TRIAGE_WORKFLOW_ID)
    fixture_path = run_dir / "fixture_result.json"
    write_json(fixture_path, build_triage_fixture())

    prompt_result = triage_runner.run_consumer_flow(
        workflow_id=TRIAGE_WORKFLOW_ID,
        task_label="installed janus-test-pipeline skill-context evidence",
        normal_target_model="5.4 medium",
        operator_choice="prompt",
        delegated_model_label="bounded delegated review / fixture mode",
        estimated_or_cost=0.0005,
        cost_estimate_confidence_percent=79.0,
    )
    assert_prompt_shape(prompt_result)

    delegated_result = triage_runner.run_consumer_flow(
        workflow_id=TRIAGE_WORKFLOW_ID,
        task_label="installed janus-test-pipeline skill-context evidence",
        normal_target_model="5.4 medium",
        operator_choice="delegated",
        delegated_model_label="bounded delegated review / fixture mode",
        estimated_or_cost=0.0005,
        cost_estimate_confidence_percent=79.0,
        input_payload=triage_runner.build_consumer_input_package(
            workflow_id=TRIAGE_WORKFLOW_ID,
            bound_skill_context="installed janus-test-pipeline skill copy",
            test_run_id="TEST-RUN-SPEC21-4",
            result_outcome_summary="The bounded triage review should stay assist-only and Codex-owned.",
            evidence_snippets=[
                "Installed janus-test-pipeline skill now references build_consumer_input_package(...)",
                "Installed janus-test-pipeline skill now references run_consumer_flow(...)",
            ],
            classification_question="Which bounded classification direction should Codex verify next?",
            candidate_blocker_category="workflow_visibility_evidence",
        ),
        fixture_result_json=fixture_path,
    )
    assert_delegated_shape(delegated_result)

    return {
        "workflow_id": TRIAGE_WORKFLOW_ID,
        "run_dir": str(run_dir),
        "prompt_path": str(run_dir / "consumer_operator_choice_prompt.json"),
        "delegated_path": str(run_dir / "consumer_operator_choice_delegated.json"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "fixture_result_path": str(fixture_path),
        "prompt_result": read_json(run_dir / "consumer_operator_choice_prompt.json"),
        "delegated_result": read_json(run_dir / "consumer_operator_choice_delegated.json"),
        "validation_summary": read_json(run_dir / "validation_summary.json"),
    }


def main() -> int:
    debug_runner = load_module("spec21_debug_runner", DEBUG_RUNNER_PATH)
    triage_runner = load_module("spec21_triage_runner", TRIAGE_RUNNER_PATH)

    summary = {
        "task": "TASK-SPEC21.4",
        "scope": "installed-skill workflow visibility evidence only",
        "debug": run_debug_evidence(debug_runner),
        "triage": run_triage_evidence(triage_runner),
        "live_or_calls_made": 0,
    }

    output_path = MODEL_ROUTING_DIR / "task_spec21_4_skill_context_evidence_summary_2026-06-20.json"
    write_json(output_path, summary)
    print(json.dumps({"status": "PASS", "summary_path": str(output_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
