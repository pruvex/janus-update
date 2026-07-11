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
        "task_class": "execution_patch_candidate",
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
        "estimated_codex_saved_tokens": None,
        "estimated_codex_or_overhead_tokens": None,
        "minimum_net_codex_saved_tokens": 0,
        "require_positive_or_roi": False,
    }
    payload.update(overrides)
    return Namespace(**payload)


def make_allowed_eligibility(selected_or_model: str = "deepseek/deepseek-v4-flash") -> dict[str, object]:
    return {
        "eligibility_result": "OR_ALLOWED",
        "reason_code": "OR_ALLOWED",
        "message": "Allowed for productive Dev-workhorse path.",
        "selected_or_model": selected_or_model,
        "budget_profile": "execution_patch_candidate",
        "per_call_cap_usd": 0.002,
        "session_cap_usd": 0.01,
        "evidence_status": "PASS",
    }


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
        self.assertIn(
            "Fest empfohlenes OR-Modell: moonshotai/kimi-k2.5",
            result["operator_prompt_lines"],
        )
        self.assertTrue(
            any("Pre-Call-Kostenbasis:" in line for line in result["operator_prompt_lines"])
        )
        self.assertEqual(result["selected_or_model"], "moonshotai/kimi-k2.5")
        self.assertEqual(result["budget_profile"], "execution_patch_candidate")
        self.assertIn("Proposal-only code patch candidate work", result["pre_call_cost_basis"])
        self.assertIn("already existing bounded delegated runtime path", result["operator_message"])
        self.assertNotIn("later bounded slice", result["operator_message"])
        self.assertIn("grants no new delegated runtime approval", result["boundaries"][0])

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

    def test_prompt_summary_blocks_task_class_outside_sealed_contract(self) -> None:
        result = runner.prompt_summary(make_args(task_class="test_result_triage_review"))

        self.assertEqual(result["selected_path"], "codex_only_pre_gate")
        self.assertEqual(result["eligibility_reason_code"], "TASK_CLASS_NOT_ALLOWED")

    def test_prompt_summary_hides_execution_write_apply_candidate_when_visibility_is_partial(self) -> None:
        result = runner.prompt_summary(
            make_args(
                task_class="execution_write_apply_candidate",
                accepted_source_run_dir=Path("fixtures/accepted-source"),
            )
        )

        self.assertEqual(result["selected_path"], "codex_only_visibility_hidden")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["visibility_status"], "HIDDEN_PARTIAL_CANDIDATE")
        self.assertIn("HIDDEN_PARTIAL_CANDIDATE", result["operator_result_lines"][1])
        self.assertIn("hidden", result["operator_message"].lower())

    def test_parse_args_rejects_assist_only_task_class_from_productive_runner(self) -> None:
        argv = [
            "codex_dev_workhorse_runner.py",
            "--task-class",
            "test_result_triage_review",
            "--task-label",
            "Out of scope",
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "prompt",
            "--workflow-id",
            "WF-SPEC25-3-NEG-001",
        ]

        with patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit):
                runner.parse_args()

    def test_prompt_summary_uses_fixed_model_from_contract_when_arg_missing(self) -> None:
        result = runner.prompt_summary(make_args(selected_or_model=None))

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["selected_or_model"], "moonshotai/kimi-k2.5")
        self.assertIn(
            "Fest empfohlenes OR-Modell: moonshotai/kimi-k2.5",
            result["operator_prompt_lines"],
        )

    def test_build_dispatcher_command_uses_fixed_model_when_arg_missing(self) -> None:
        args = make_args(
            selected_or_model=None,
            execution_input_package=Path("fixtures/execution-input.json"),
        )

        command = runner._build_dispatcher_command(args)

        self.assertEqual(
            command[command.index("--selected-or-model") + 1],
            "moonshotai/kimi-k2.5",
        )

    def test_build_dispatcher_command_ignores_conflicting_cli_model(self) -> None:
        args = make_args(
            selected_or_model="qwen/qwen3.5-flash-02-23",
            execution_input_package=Path("fixtures/execution-input.json"),
        )

        command = runner._build_dispatcher_command(args)

        self.assertEqual(
            command[command.index("--selected-or-model") + 1],
            "moonshotai/kimi-k2.5",
        )

    def test_gate_binds_model_once_for_dispatcher_and_telemetry(self) -> None:
        args = make_args(
            operator_choice="or",
            selected_or_model="qwen/qwen3.5-flash-02-23",
            execution_input_package=Path("fixtures/execution-input.json"),
        )
        result = {
            "selected_path": "delegated_execution_patch_candidate",
            "validation_result": "PASS",
            "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
            "fallback_used": "NO",
            "rework_required": "NO",
            "actual_or_cost": 0.00012345,
            "operator_result_lines": ["Ergebnis: EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW"],
            "operator_message": "Delegated review completed.",
            "codex_owned_outcome_status": "EXECUTION_PATCH_CANDIDATE_PENDING_CODEX_REVIEW",
        }

        with patch.object(
            runner,
            "evaluate_productive_dev_workhorse_path",
            return_value=make_allowed_eligibility("model/A"),
        ):
            gate = runner.prompt_summary(args)

        self.assertEqual(gate["selected_or_model"], "model/A")

        with patch.object(
            runner,
            "evaluate_productive_dev_workhorse_path",
            side_effect=AssertionError("Eligibility must not be re-evaluated after the gate."),
        ):
            command = runner._build_dispatcher_command(args)
            telemetry = runner._build_session_telemetry_row(args, result)

        self.assertEqual(command[command.index("--selected-or-model") + 1], "model/A")
        self.assertEqual(telemetry["or_model"], "model/A")

    def test_prompt_summary_aborts_when_cost_basis_missing(self) -> None:
        with patch.object(runner, "_build_pre_call_cost_basis", return_value=None):
            result = runner.prompt_summary(make_args())

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertIn("pre_call_cost_basis", result["missing_gate_fields"])
        self.assertEqual(result["selected_path"], "codex_only_prompt_data_missing")

    def test_prompt_summary_blocks_or_when_roi_is_negative(self) -> None:
        result = runner.prompt_summary(
            make_args(
                estimated_codex_saved_tokens=1000,
                estimated_codex_or_overhead_tokens=2000,
                minimum_net_codex_saved_tokens=250,
            )
        )

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["selected_path"], "codex_only_or_roi_gate")
        self.assertEqual(result["or_roi"]["status"], "NEGATIVE")
        self.assertEqual(result["or_roi"]["net_codex_saved_tokens"], -1000)
        self.assertIn("OR ROI Gate", result["operator_result_lines"][0])

    def test_prompt_summary_shows_or_choice_when_roi_is_positive(self) -> None:
        result = runner.prompt_summary(
            make_args(
                estimated_codex_saved_tokens=4000,
                estimated_codex_or_overhead_tokens=1200,
                minimum_net_codex_saved_tokens=500,
            )
        )

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["or_roi"]["status"], "POSITIVE")
        self.assertEqual(result["or_roi"]["net_codex_saved_tokens"], 2800)
        self.assertTrue(any("OR ROI Gate: POSITIVE" in line for line in result["operator_prompt_lines"]))

    def test_local_summary_keeps_codex_only(self) -> None:
        result = runner.local_summary(make_args(operator_choice="local"))

        self.assertEqual(result["selected_path"], "codex_only_operator_choice")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")

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

    def test_or_choice_keeps_execution_write_apply_candidate_codex_only_when_visibility_hidden(self) -> None:
        args = make_args(
            task_class="execution_write_apply_candidate",
            accepted_source_run_dir=Path("fixtures/accepted-source"),
        )

        with patch.object(runner, "invoke_bounded_delegation_dispatch") as mocked:
            result = runner.or_choice_summary(args)

        mocked.assert_not_called()
        self.assertEqual(result["selected_path"], "codex_only_visibility_hidden")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")

    def test_build_dispatcher_command_forwards_execution_write_live_sidecar_flags(self) -> None:
        args = make_args(
            task_class="execution_write_apply_candidate",
            accepted_source_run_dir=Path("fixtures/accepted-source"),
        )
        args.execution_sidecar_model = "gpt-5.4"
        args.execution_sidecar_timeout_seconds = 240
        args.execution_live_sidecar = True

        command = runner._build_dispatcher_command(args)

        self.assertIn("--execution-sidecar-model", command)
        self.assertIn("gpt-5.4", command)
        self.assertIn("--execution-sidecar-timeout-seconds", command)
        self.assertIn("240", command)
        self.assertIn("--execution-live-sidecar", command)

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
            "selected_path": "delegated_execution_patch_candidate",
            "validation_result": "PASS",
            "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
            "fallback_used": "NO",
            "rework_required": "NO",
            "actual_or_cost": 0.00045678,
            "response_summary_path": str(response_summary_path),
            "operator_result_lines": ["Ergebnis: EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW"],
            "operator_message": "Delegated review completed.",
            "codex_owned_outcome_status": "EXECUTION_PATCH_CANDIDATE_PENDING_CODEX_REVIEW",
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
            "final_outcome": "EXECUTION_PATCH_CANDIDATE_REJECT_AND_FALLBACK",
            "fallback_used": "YES",
            "rework_required": "YES",
            "operator_result_lines": ["Ergebnis: EXECUTION_PATCH_CANDIDATE_REJECT_AND_FALLBACK"],
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

    def test_finalize_result_telemetry_uses_fixed_model_when_arg_missing(self) -> None:
        result = {
            "selected_path": "delegated_execution_patch_candidate",
            "validation_result": "PASS",
            "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
            "fallback_used": "NO",
            "rework_required": "NO",
            "actual_or_cost": 0.00012345,
            "operator_result_lines": ["Ergebnis: EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW"],
            "operator_message": "Delegated review completed.",
            "codex_owned_outcome_status": "EXECUTION_PATCH_CANDIDATE_PENDING_CODEX_REVIEW",
        }
        args = make_args(operator_choice="or", selected_or_model=None)

        with patch.object(
            runner,
            "_run_healthcheck",
            return_value=("PASS", str(self.temp_path / "healthcheck_summary.json")),
        ):
            finalized = runner.finalize_productive_dev_workhorse_result(args, result)

        row = json.loads(Path(finalized["session_telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(row["or_model"], "moonshotai/kimi-k2.5")

    def test_finalize_result_telemetry_ignores_conflicting_cli_model(self) -> None:
        result = {
            "selected_path": "delegated_execution_patch_candidate",
            "validation_result": "PASS",
            "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
            "fallback_used": "NO",
            "rework_required": "NO",
            "actual_or_cost": 0.00012345,
            "operator_result_lines": ["Ergebnis: EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW"],
            "operator_message": "Delegated review completed.",
            "codex_owned_outcome_status": "EXECUTION_PATCH_CANDIDATE_PENDING_CODEX_REVIEW",
        }
        args = make_args(operator_choice="or", selected_or_model="qwen/qwen3.5-flash-02-23")

        with patch.object(
            runner,
            "_run_healthcheck",
            return_value=("PASS", str(self.temp_path / "healthcheck_summary.json")),
        ):
            finalized = runner.finalize_productive_dev_workhorse_result(args, result)

        row = json.loads(Path(finalized["session_telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(row["or_model"], "moonshotai/kimi-k2.5")


if __name__ == "__main__":
    unittest.main()
