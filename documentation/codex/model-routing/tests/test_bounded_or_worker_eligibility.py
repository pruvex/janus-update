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
        self.assertEqual(result["choice_2"], "OpenRouter")
        self.assertIn("voraussichtliche Kosten", result["operator_prompt_lines"][1])

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
        self.assertEqual(result["choice_2"], "OpenRouter")

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


if __name__ == "__main__":
    unittest.main()
