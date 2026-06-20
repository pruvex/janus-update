from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

ELIGIBILITY_SPEC = importlib.util.spec_from_file_location(
    "bounded_or_worker_eligibility",
    SCRIPTS_DIR / "bounded_or_worker_eligibility.py",
)
eligibility = importlib.util.module_from_spec(ELIGIBILITY_SPEC)
assert ELIGIBILITY_SPEC and ELIGIBILITY_SPEC.loader
sys.modules[ELIGIBILITY_SPEC.name] = eligibility
ELIGIBILITY_SPEC.loader.exec_module(eligibility)

DISPATCHER_SPEC = importlib.util.spec_from_file_location(
    "codex_bounded_delegation_dispatcher",
    SCRIPTS_DIR / "codex_bounded_delegation_dispatcher.py",
)
dispatcher = importlib.util.module_from_spec(DISPATCHER_SPEC)
assert DISPATCHER_SPEC and DISPATCHER_SPEC.loader
sys.modules[DISPATCHER_SPEC.name] = dispatcher
DISPATCHER_SPEC.loader.exec_module(dispatcher)

DOC_RUNNER_SPEC = importlib.util.spec_from_file_location(
    "doc_skill_mini_fixed_or_live_runner",
    SCRIPTS_DIR / "doc_skill_mini_fixed_or_live_runner.py",
)
doc_runner = importlib.util.module_from_spec(DOC_RUNNER_SPEC)
assert DOC_RUNNER_SPEC and DOC_RUNNER_SPEC.loader
sys.modules[DOC_RUNNER_SPEC.name] = doc_runner
DOC_RUNNER_SPEC.loader.exec_module(doc_runner)

DEBUG_RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_debug_hypothesis_review_runner",
    SCRIPTS_DIR / "codex_debug_hypothesis_review_runner.py",
)
debug_runner = importlib.util.module_from_spec(DEBUG_RUNNER_SPEC)
assert DEBUG_RUNNER_SPEC and DEBUG_RUNNER_SPEC.loader
sys.modules[DEBUG_RUNNER_SPEC.name] = debug_runner
DEBUG_RUNNER_SPEC.loader.exec_module(debug_runner)

TRIAGE_RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_test_result_triage_review_runner",
    SCRIPTS_DIR / "codex_test_result_triage_review_runner.py",
)
triage_runner = importlib.util.module_from_spec(TRIAGE_RUNNER_SPEC)
assert TRIAGE_RUNNER_SPEC and TRIAGE_RUNNER_SPEC.loader
sys.modules[TRIAGE_RUNNER_SPEC.name] = triage_runner
TRIAGE_RUNNER_SPEC.loader.exec_module(triage_runner)


class BoundedOrWorkerEligibilityTests(unittest.TestCase):
    def test_assistive_or_pilot_allows_redacted_debug_package(self) -> None:
        payload = {
            "workflow_id": "WF-DEBUG-PILOT-001",
            "bound_skill_context": "janus-debug",
            "expected_behavior": "Delegated review should stay bounded.",
            "actual_behavior": "Delegated review must only receive the minimal package.",
            "evidence_snippets": [
                "validator requested one bounded review only",
                "no secrets appear in the reduced package",
            ],
            "iteration_number": 1,
            "explicit_question": "What is the next local verifier?",
            "redaction_ready": True,
            "failure_code": "RUNNER_ARTIFACT_MISMATCH",
        }

        result = eligibility.evaluate_assistive_or_workhorse_pilot(
            skill_id="janus-debug",
            task_class="debug_hypothesis_review",
            request_payload=payload,
        )

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["reason_code"], "ELIGIBILITY_CONFIRMED")

    def test_assistive_or_pilot_rejects_out_of_scope_task_class(self) -> None:
        result = eligibility.evaluate_assistive_or_workhorse_pilot(
            skill_id="janus-debug",
            task_class="quickchange_patch_review",
            request_payload={"redaction_ready": True, "evidence_snippets": ["narrow"]},
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "TASK_CLASS_NOT_ALLOWED")

    def test_assistive_or_pilot_rejects_debug_payload_with_forbidden_field(self) -> None:
        payload = {
            "workflow_id": "WF-DEBUG-PILOT-002",
            "bound_skill_context": "janus-debug",
            "expected_behavior": "Delegated review should stay bounded.",
            "actual_behavior": "The request package still contains widened context.",
            "evidence_snippets": ["snippet one"],
            "iteration_number": 2,
            "explicit_question": "Which verifier should Codex run?",
            "redaction_ready": True,
            "changed_files": [
                "documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py"
            ],
        }

        result = eligibility.evaluate_assistive_or_workhorse_pilot(
            skill_id="janus-debug",
            task_class="debug_hypothesis_review",
            request_payload=payload,
        )

        self.assertEqual(result["eligibility_result"], "OR_CONTEXT_REDACTION_REQUIRED")
        self.assertIn("forbidden input field: changed_files", result["request_validation_issues"])

    def test_assistive_or_pilot_rejects_triage_payload_with_path_leakage(self) -> None:
        payload = {
            "workflow_id": "WF-TRIAGE-PILOT-001",
            "bound_skill_context": "janus-test-pipeline",
            "test_run_id": "TEST-RUN-2026-06-20-001",
            "result_outcome_summary": "Artifact mismatch after generation stage.",
            "evidence_snippets": ["summary references only the bounded mismatch"],
            "classification_question": "Is this infra or test bug?",
            "redaction_ready": True,
            "test_result_path": "documentation/test-results/TEST-RUN-2026-06-20-001_results.json",
        }

        result = eligibility.evaluate_assistive_or_workhorse_pilot(
            skill_id="janus-test-pipeline",
            task_class="test_result_triage_review",
            request_payload=payload,
        )

        self.assertEqual(result["eligibility_result"], "OR_CONTEXT_REDACTION_REQUIRED")
        self.assertIn("forbidden input field: test_result_path", result["request_validation_issues"])

    def test_assistive_or_pilot_allows_redacted_triage_package(self) -> None:
        payload = {
            "workflow_id": "WF-TRIAGE-PILOT-002",
            "bound_skill_context": "janus-test-pipeline",
            "test_run_id": "TEST-RUN-2026-06-20-002",
            "result_outcome_summary": "Generator mismatch remained after rerun.",
            "evidence_snippets": [
                "failure reproduced in bounded rerun summary",
                "package contains no raw file paths",
            ],
            "classification_question": "Should Codex treat this as infra drift or product bug?",
            "redaction_ready": True,
            "candidate_blocker_category": "infra_or_harness",
        }

        result = eligibility.evaluate_assistive_or_workhorse_pilot(
            skill_id="janus-test-pipeline",
            task_class="test_result_triage_review",
            request_payload=payload,
        )

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["reason_code"], "ELIGIBILITY_CONFIRMED")

    def test_productive_dev_workhorse_path_allows_in_scope_task_class(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="test_result_triage_review",
            estimated_or_cost=0.02,
        )

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["reason_code"], "ELIGIBILITY_CONFIRMED")
        self.assertEqual(result["budget_profile"], "test_result_triage_review")
        self.assertEqual(result["per_call_cap_usd"], 0.03)

    def test_productive_dev_workhorse_path_rejects_existing_workflow_outside_path(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="janus-test-pipeline",
            task_class="test_result_triage_review",
            estimated_or_cost=0.02,
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "PATH_NOT_ALLOWED")

    def test_productive_dev_workhorse_path_rejects_non_allowed_task_class(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="documentation_draft",
            estimated_or_cost=0.005,
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "TASK_CLASS_NOT_ALLOWED")

    def test_productive_dev_workhorse_path_rejects_missing_budget_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "eligibility.json"
            payload = eligibility.load_json(eligibility.DEFAULT_ELIGIBILITY_CONFIG_PATH)
            payload["productive_dev_workhorse_path"]["allowed_task_classes"]["test_result_triage_review"] = {
                "budget_profile": "missing_profile"
            }
            config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            result = eligibility.evaluate_productive_dev_workhorse_path(
                path_id="productive_dev_workhorse_path",
                task_class="test_result_triage_review",
                estimated_or_cost=0.02,
                config_path=config_path,
            )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "BUDGET_PROFILE_MISSING")

    def test_productive_dev_workhorse_path_rejects_missing_estimated_cost(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="execution_patch_candidate",
            estimated_or_cost=None,
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "ESTIMATED_COST_MISSING")
        self.assertEqual(result["budget_profile"], "execution_patch_candidate")

    def test_productive_dev_workhorse_path_rejects_cost_above_per_call_cap(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="execution_patch_candidate",
            estimated_or_cost=0.051,
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "PER_CALL_CAP_EXCEEDED")
        self.assertEqual(result["per_call_cap_usd"], 0.05)

    def test_productive_dev_workhorse_path_rejects_negative_estimated_cost(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="execution_patch_candidate",
            estimated_or_cost=-0.01,
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "ESTIMATED_COST_INVALID")
        self.assertEqual(result["budget_profile"], "execution_patch_candidate")

    def test_productive_dev_workhorse_path_rejects_nan_estimated_cost(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="execution_patch_candidate",
            estimated_or_cost=float("nan"),
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "ESTIMATED_COST_INVALID")
        self.assertEqual(result["budget_profile"], "execution_patch_candidate")

    def test_productive_dev_workhorse_path_rejects_infinite_estimated_cost(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="execution_patch_candidate",
            estimated_or_cost=float("inf"),
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "ESTIMATED_COST_INVALID")
        self.assertEqual(result["budget_profile"], "execution_patch_candidate")

    def test_productive_dev_workhorse_path_rejects_non_numeric_estimated_cost(self) -> None:
        result = eligibility.evaluate_productive_dev_workhorse_path(
            path_id="productive_dev_workhorse_path",
            task_class="execution_patch_candidate",
            estimated_or_cost="not-a-number",
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "ESTIMATED_COST_INVALID")
        self.assertEqual(result["budget_profile"], "execution_patch_candidate")

    def test_doc_skill_allowed_returns_or_allowed(self) -> None:
        result = eligibility.evaluate_doc_skill_fixed_or(
            skill_id="DOC-SKILL-001",
            normal_target_model="5.4 mini low",
            task_intent="documentation_skill",
            governance_flag=False,
        )

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["reason_code"], "ELIGIBILITY_CONFIRMED")
        self.assertEqual(result["selected_or_model"], "openai/gpt-oss-20b")

    def test_doc_skill_unknown_returns_not_eligible(self) -> None:
        result = eligibility.evaluate_doc_skill_fixed_or(
            skill_id="DOC-SKILL-999",
            normal_target_model="5.4 mini low",
            task_intent="documentation_skill",
            governance_flag=False,
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "SKILL_NOT_ALLOWED")

    def test_doc_skill_missing_evidence_returns_evidence_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "eligibility.json"
            payload = eligibility.load_json(eligibility.DEFAULT_ELIGIBILITY_CONFIG_PATH)
            payload["doc_skill_fixed_or"]["skills"]["DOC-SKILL-001"]["evidence_status"] = "PENDING_RECHECK"
            config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            result = eligibility.evaluate_doc_skill_fixed_or(
                skill_id="DOC-SKILL-001",
                normal_target_model="5.4 mini low",
                task_intent="documentation_skill",
                governance_flag=False,
                config_path=config_path,
            )

        self.assertEqual(result["eligibility_result"], "OR_EVIDENCE_MISSING")
        self.assertEqual(result["reason_code"], "EVIDENCE_NOT_CONFIRMED")

    def test_dispatcher_prompt_summary_exposes_allowed_eligibility(self) -> None:
        args = Namespace(
            task_class="debug_hypothesis_review",
            task_label="Eligibility prompt",
            normal_target_model="5.4 medium",
            selected_or_model="qwen/qwen3.5-flash-02-23",
            estimated_or_cost=0.000321,
            cost_estimate_confidence_percent=88.0,
        )
        result = dispatcher.prompt_summary(args, "WF-ELIGIBILITY-001")

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["choice_2"], "OR-Arbeitspferd")
        self.assertIn("2 = OR-Arbeitspferd", result["operator_prompt_lines"])

    def test_dispatcher_entry_gate_allows_triage_review_class(self) -> None:
        result = dispatcher.evaluate_assistive_or_workhorse_dispatcher_eligibility(
            task_class="test_result_triage_review"
        )

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["reason_code"], "ELIGIBILITY_CONFIRMED")

    def test_dispatcher_entry_gate_rejects_legacy_task_class(self) -> None:
        result = dispatcher.evaluate_assistive_or_workhorse_dispatcher_eligibility(
            task_class="quickchange_patch_review"
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "SKILL_NOT_ALLOWED")

    def test_dispatcher_prompt_summary_suppresses_gate_without_cost(self) -> None:
        args = Namespace(
            task_class="debug_hypothesis_review",
            task_label="Eligibility prompt",
            normal_target_model="5.4 medium",
            selected_or_model="qwen/qwen3.5-flash-02-23",
            estimated_or_cost=None,
            cost_estimate_confidence_percent=88.0,
        )
        result = dispatcher.prompt_summary(args, "WF-ELIGIBILITY-002")

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["selected_path"], "codex_only_prompt_data_missing")
        self.assertIn("estimated_or_cost", result["missing_gate_fields"])

    def test_doc_runner_eligibility_summary_keeps_codex_fallback(self) -> None:
        eligibility_result = {
            "eligibility_result": "OR_NOT_ELIGIBLE",
            "reason_code": "TASK_INTENT_MISMATCH",
            "message": "Task intent drifted outside the bounded documentation-skill OR contract.",
            "evidence_status": "LIVE_EVIDENCE_CONFIRMED",
            "selected_or_model": "openai/gpt-oss-20b",
        }
        captured: dict[str, object] = {}

        def fake_output_summary(data: dict[str, object]) -> None:
            captured.update(data)

        original = doc_runner.output_summary
        doc_runner.output_summary = fake_output_summary
        self.addCleanup(setattr, doc_runner, "output_summary", original)

        result_code = doc_runner.eligibility_summary(
            workflow_id="WF-DOC-ELIGIBILITY-001",
            skill_id="DOC-SKILL-001",
            eligibility=eligibility_result,
            final_outcome="CODEX_ONLY_OR_NOT_ELIGIBLE",
        )

        self.assertEqual(result_code, 0)
        self.assertEqual(captured["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(captured["selected_path"], "codex_only_pre_wrapper")
        self.assertEqual(captured["final_outcome"], "CODEX_ONLY_OR_NOT_ELIGIBLE")
        self.assertEqual(captured["codex_owned_outcome_status"], "CODEX_LOCAL_PATH")

    def test_debug_prompt_summary_requires_cost_and_confidence(self) -> None:
        result = debug_runner.prompt_summary(
            workflow_id="WF-DEBUG-001",
            task_label="Debug gate",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3.5-flash-02-23",
            estimated_or_cost=0.00045,
            cost_estimate_confidence_percent=77.0,
        )

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["choice_2"], "OR-Arbeitspferd")

    def test_triage_prompt_summary_suppresses_gate_without_confidence(self) -> None:
        result = triage_runner.prompt_summary(
            workflow_id="WF-TRIAGE-001",
            task_label="Triage gate",
            normal_target_model="5.4 medium",
            delegated_model_label="openai/gpt-oss-20b",
            estimated_or_cost=0.00019,
            cost_estimate_confidence_percent=None,
        )

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertIn("cost_estimate_confidence_percent", result["missing_gate_fields"])

    def test_doc_runner_fail_pre_wrapper_marks_or_rejected_by_codex(self) -> None:
        captured: dict[str, object] = {}

        def fake_output_summary(data: dict[str, object]) -> None:
            captured.update(data)

        original = doc_runner.output_summary
        doc_runner.output_summary = fake_output_summary
        self.addCleanup(setattr, doc_runner, "output_summary", original)

        result_code = doc_runner.fail_pre_wrapper(
            workflow_id="WF-DOC-FAIL-001",
            skill_id="DOC-SKILL-001",
            final_outcome="ABORTED_USAGE_MISSING",
            selected_path="abort_post_wrapper",
            operator_message="usage missing",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model="openai/gpt-oss-20b",
        )

        self.assertEqual(result_code, 0)
        self.assertEqual(captured["codex_owned_outcome_status"], "OR_REJECTED_BY_CODEX")

    def test_dispatcher_assist_only_result_stays_review_pending(self) -> None:
        result = dispatcher.with_codex_owned_outcome(
            {
                "selected_path": "delegated_assist_only_hypothesis_review",
                "validation_result": "PASS",
                "final_outcome": "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION",
            }
        )

        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REVIEW_PENDING_CODEX_DECISION")

    def test_dispatcher_codex_fallback_result_is_not_or_accepted(self) -> None:
        result = dispatcher.with_codex_owned_outcome(
            {
                "selected_path": "codex_local_fallback_after_structured_executor_failure",
                "validation_result": "FAIL",
                "final_outcome": "CODEX_LOCAL_FALLBACK_REQUIRED",
                "fallback_used": "YES",
                "rework_required": "YES",
            }
        )

        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REJECT_AND_FALLBACK")

    def test_dispatcher_rejects_debug_payload_before_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "debug_input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "workflow_id": "WF-DEBUG-DISPATCH-001",
                        "bound_skill_context": "janus-debug",
                        "expected_behavior": "Delegated review should stay bounded.",
                        "actual_behavior": "Legacy fixture leaked changed files.",
                        "evidence_snippets": ["one bounded snippet"],
                        "iteration_number": 1,
                        "explicit_question": "What verifier should Codex run?",
                        "redaction_ready": True,
                        "changed_files": ["backend/services/chat_orchestrator.py"],
                    }
                ),
                encoding="utf-8",
            )

            payload, gate = dispatcher.validate_assistive_or_workhorse_request(
                task_class="debug_hypothesis_review",
                input_package_path=input_path,
            )
            result = dispatcher.build_assistive_or_pilot_reject_result(
                workflow_id="WF-DEBUG-DISPATCH-001",
                task_class="debug_hypothesis_review",
                task_label="Debug pilot gate",
                input_payload=payload,
                eligibility=gate,
            )

        self.assertEqual(result["eligibility_result"], "OR_CONTEXT_REDACTION_REQUIRED")
        self.assertEqual(result["selected_path"], "codex_only_pre_dispatch")
        self.assertIn("forbidden input field: changed_files", result["request_validation_issues"])


if __name__ == "__main__":
    unittest.main()
