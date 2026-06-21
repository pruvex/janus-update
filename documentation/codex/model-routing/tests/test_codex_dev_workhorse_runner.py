from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_dev_workhorse_runner",
    SCRIPTS_DIR / "codex_dev_workhorse_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_args(**overrides: object) -> Namespace:
    payload = {
        "task_class": "test_result_triage_review",
        "task_label": "Bounded Dev runner",
        "normal_target_model": "5.4 medium",
        "operator_choice": "prompt",
        "workflow_id": "WF-SPEC22-2-001",
        "path_id": "productive_dev_workhorse_path",
        "selected_or_model": "openai/gpt-oss-20b",
        "estimated_or_cost": 0.0008,
        "cost_estimate_confidence_percent": 87.0,
        "test_triage_input_package": None,
        "test_triage_fixture_result": None,
        "execution_input_package": None,
        "execution_fixture_result": None,
        "accepted_source_run_dir": None,
        "use_local_or_fixture": False,
        "or_local_fixture_response_path": None,
        "execute_direct_or": False,
    }
    payload.update(overrides)
    return Namespace(**payload)


class CodexDevWorkhorseRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_session_runs_dir = runner.SESSION_RUNS_DIR
        self.original_model_routing_dir = runner.MODEL_ROUTING_DIR
        runner.SESSION_RUNS_DIR = self.temp_path / "sessions"
        runner.MODEL_ROUTING_DIR = self.temp_path / "model-routing"
        self.addCleanup(self._restore_paths)

    def _restore_paths(self) -> None:
        runner.SESSION_RUNS_DIR = self.original_session_runs_dir
        runner.MODEL_ROUTING_DIR = self.original_model_routing_dir

    def test_prompt_summary_contains_visible_gate_fields(self) -> None:
        result = runner.prompt_summary(make_args())

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])
        self.assertEqual(result["selected_or_model"], "openai/gpt-oss-20b")

    def test_prompt_summary_aborts_when_confidence_missing(self) -> None:
        result = runner.prompt_summary(make_args(cost_estimate_confidence_percent=None))

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertIn("cost_estimate_confidence_percent", result["missing_gate_fields"])
        self.assertEqual(result["selected_path"], "codex_only_prompt_data_missing")

    def test_prompt_summary_aborts_when_estimate_missing(self) -> None:
        result = runner.prompt_summary(make_args(estimated_or_cost=None))

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["selected_path"], "codex_only_pre_gate")
        self.assertEqual(result["eligibility_reason_code"], "ESTIMATED_COST_MISSING")

    def test_prompt_summary_blocks_when_path_not_allowed(self) -> None:
        result = runner.prompt_summary(make_args(path_id="janus_debug_workflow"))

        self.assertEqual(result["selected_path"], "codex_only_pre_gate")
        self.assertEqual(result["eligibility_reason_code"], "PATH_NOT_ALLOWED")

    def test_local_summary_keeps_codex_only(self) -> None:
        result = runner.local_summary(make_args(operator_choice="local"))

        self.assertEqual(result["selected_path"], "codex_only_operator_choice")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")

    def test_or_choice_delegates_test_result_triage_review(self) -> None:
        delegated = {
            "selected_path": "delegated_assist_only_test_result_triage_review",
            "final_outcome": "DELEGATED_TRIAGE_REVIEW_READY_FOR_CODEX_REVIEW",
            "validation_result": "PASS",
        }
        args = make_args(
            operator_choice="or",
            test_triage_input_package=Path("fixtures/test-triage-input.json"),
            test_triage_fixture_result=Path("fixtures/test-triage-result.json"),
        )

        with patch.object(runner, "invoke_bounded_delegation_dispatch", return_value=delegated) as mocked:
            result = runner.or_choice_summary(args)

        mocked.assert_called_once_with(args)
        self.assertEqual(result["selected_path"], delegated["selected_path"])
        self.assertEqual(result["final_outcome"], delegated["final_outcome"])

    def test_or_choice_delegates_execution_patch_candidate(self) -> None:
        delegated = {
            "selected_path": "delegated_execution_patch_candidate",
            "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
            "validation_result": "PASS",
        }
        args = make_args(
            task_class="execution_patch_candidate",
            execution_input_package=Path("fixtures/execution-input.json"),
            execution_fixture_result=Path("fixtures/execution-result.json"),
        )

        with patch.object(runner, "invoke_bounded_delegation_dispatch", return_value=delegated) as mocked:
            result = runner.or_choice_summary(args)

        mocked.assert_called_once_with(args)
        self.assertEqual(result["selected_path"], delegated["selected_path"])
        self.assertEqual(result["final_outcome"], delegated["final_outcome"])

    def test_or_choice_delegates_execution_write_apply_candidate(self) -> None:
        delegated = {
            "selected_path": "delegated_execution_write_apply_candidate",
            "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_CODEX_ACCEPT_REJECT",
            "validation_result": "PASS",
        }
        args = make_args(
            task_class="execution_write_apply_candidate",
            accepted_source_run_dir=Path("fixtures/accepted-source"),
        )

        with patch.object(runner, "invoke_bounded_delegation_dispatch", return_value=delegated) as mocked:
            result = runner.or_choice_summary(args)

        mocked.assert_called_once_with(args)
        self.assertEqual(result["selected_path"], delegated["selected_path"])
        self.assertEqual(result["final_outcome"], delegated["final_outcome"])

    def test_or_choice_requires_input_package_for_execution_patch_candidate(self) -> None:
        args = make_args(task_class="execution_patch_candidate")

        with self.assertRaises(SystemExit):
            runner.invoke_bounded_delegation_dispatch(args)

    def test_finalize_result_writes_session_telemetry_and_healthcheck(self) -> None:
        run_dir = self.temp_path / "dispatcher-run"
        run_dir.mkdir(parents=True)
        response_summary_path = run_dir / "response_summary.json"
        response_summary_path.write_text(
            json.dumps(
                {
                    "generation_id": "gen_spec22_4_001",
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 200,
                        "cost": 0.00045678,
                    },
                }
            ),
            encoding="utf-8",
        )
        result = {
            "selected_path": "delegated_assist_only_test_result_triage_review",
            "validation_result": "PASS",
            "final_outcome": "TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION",
            "fallback_used": "NO",
            "rework_required": "NO",
            "actual_or_cost": 0.00045678,
            "response_summary_path": str(response_summary_path),
            "operator_result_lines": ["Ergebnis: TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION"],
            "operator_message": "Delegated review completed.",
            "codex_owned_outcome_status": "DELEGATED_REVIEW_PENDING_CODEX_DECISION",
        }
        args = make_args(operator_choice="or")

        with patch.object(
            runner,
            "_run_healthcheck",
            return_value=("PASS", str(self.temp_path / "healthcheck_summary.json")),
        ):
            finalized = runner.finalize_productive_dev_workhorse_result(args, result)

        telemetry_path = Path(finalized["session_telemetry_jsonl_path"])
        self.assertTrue(telemetry_path.exists())
        row = json.loads(telemetry_path.read_text(encoding="utf-8").strip())
        self.assertEqual(row["routing_mode"], "productive_dev_workhorse_path")
        self.assertEqual(row["validation_result"], "PASS")
        self.assertEqual(row["actual_or_cost"], 0.00045678)
        self.assertEqual(finalized["dev_workhorse_healthcheck_status"], "PASS")
        self.assertIn("Tatsaechliche Kosten: 0.000456780", finalized["operator_result_lines"])

    def test_finalize_result_marks_missing_usage_truthfully(self) -> None:
        result = {
            "selected_path": "abort_post_wrapper",
            "validation_result": "FAIL",
            "final_outcome": "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK",
            "fallback_used": "YES",
            "rework_required": "YES",
            "operator_result_lines": ["Ergebnis: TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK"],
            "operator_message": "Wrapper failed.",
            "codex_owned_outcome_status": "OR_REJECTED_BY_CODEX",
        }
        args = make_args(operator_choice="or")

        with patch.object(
            runner,
            "_run_healthcheck",
            return_value=("PASS", str(self.temp_path / "healthcheck_summary.json")),
        ):
            finalized = runner.finalize_productive_dev_workhorse_result(args, result)

        row = json.loads(Path(finalized["session_telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(row["usage_source"], "fallback_estimate")
        self.assertEqual(row["validation_result"], "FAIL")
        self.assertIn("Tatsaechliche Kosten: N/A (usage missing, fallback documented)", finalized["operator_result_lines"])


if __name__ == "__main__":
    unittest.main()
