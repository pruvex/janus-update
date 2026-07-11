from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_backlog_handoff_review_runner",
    SCRIPTS_DIR / "codex_backlog_handoff_review_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_input_payload() -> dict[str, object]:
    return {
        "workflow_id": "WF-BACKLOG-HANDOFF-PACKAGE-001",
        "bound_skill_context": "janus-backlog-handoff",
        "mode": "SELECTED_HANDOFF",
        "selected_backlog_id": "BACKLOG-109",
        "selected_item": {
            "backlog_id": "BACKLOG-109",
            "title": "Lokale DB-Snapshots vor riskanten Debug-, Repair- und Migrationsschritten anlegen",
            "status": "READY",
        },
        "allowed_entry_points": [
            "PRE_IMPLEMENTATION_VERIFICATION",
            "SPEC_PIPELINE_START",
            "ROUTING_BLOCKED",
        ],
        "expected_best_entry_point": "PRE_IMPLEMENTATION_VERIFICATION",
        "expected_artifact_path": "documentation/tasks/backlog_BACKLOG-109_lokale_db_snapshots_vor_riskanten_debug_repair_und_migrationsschritten.md",
        "expected_next_skill": "janus-preimplementation-check",
        "artifact_exists": False,
        "expected_output": "One bounded selected-handoff review recommendation only.",
        "redaction_ready": True,
    }


def make_response_summary(cost: float = 0.00017933) -> dict[str, object]:
    return {
        "generation_id": "gen-test-handoff-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 1046,
            "completion_tokens": 393,
            "cost": cost,
        },
    }


class TestCodexBacklogHandoffReviewRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_run_root = runner.RUN_ROOT
        self.original_model_routing_dir = runner.MODEL_ROUTING_DIR
        runner.RUN_ROOT = self.temp_path / "runs"
        runner.MODEL_ROUTING_DIR = self.temp_path / "model-routing"
        self.addCleanup(self._restore_paths)

    def _restore_paths(self) -> None:
        runner.RUN_ROOT = self.original_run_root
        runner.MODEL_ROUTING_DIR = self.original_model_routing_dir

    def test_prompt_summary_contains_visible_gate_fields(self) -> None:
        result = runner.prompt_summary(
            workflow_id="WF-BACKLOG-HANDOFF-PROMPT-001",
            task_label="Backlog handoff review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00018,
            cost_estimate_confidence_percent=76.0,
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])
        self.assertIn(
            "Fest empfohlenes OR-Modell: qwen/qwen3-coder-30b-a3b-instruct",
            result["operator_prompt_lines"],
        )
        self.assertIn("No delegated backlog move or status write", result["boundaries"][0])

    def test_prompt_summary_aborts_when_estimate_missing(self) -> None:
        result = runner.prompt_summary(
            workflow_id="WF-BACKLOG-HANDOFF-PROMPT-002",
            task_label="Backlog handoff review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=None,
            cost_estimate_confidence_percent=76.0,
        )

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertIn("estimated_or_cost", result["missing_gate_fields"])

    def test_local_summary_keeps_codex_only(self) -> None:
        result = runner.local_summary(
            workflow_id="WF-BACKLOG-HANDOFF-LOCAL-001",
            task_label="Backlog handoff review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
        )

        self.assertEqual(result["selected_path"], "codex_only_operator_choice")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")

    def test_run_consumer_flow_rejects_invalid_input_package(self) -> None:
        bad_payload = make_input_payload()
        bad_payload["selected_backlog_id"] = "BACKLOG-999"
        bad_path = self.temp_path / "bad_input.json"
        bad_path.write_text(json.dumps(bad_payload), encoding="utf-8")

        result = runner.run_consumer_flow(
            workflow_id="WF-BACKLOG-HANDOFF-BAD-001",
            task_label="Backlog handoff delegated bad package",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00018,
            cost_estimate_confidence_percent=76.0,
            input_package_json=bad_path,
            use_local_or_fixture=True,
            or_local_fixture_response_path=self.temp_path / "unused.json",
            execute_direct_or=False,
        )

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["selected_path"], "input_package_invalid")

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-BACKLOG-HANDOFF-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "status": "PASS",
                                "selected_backlog_id": "BACKLOG-109",
                                "mode": "SELECTED_HANDOFF",
                                "recommended_entry_point": "PRE_IMPLEMENTATION_VERIFICATION",
                                "routing_reason": "READY item with clear bounded local task and low routing ambiguity.",
                                "routing_confidence": "HIGH",
                                "required_artifact_path": "documentation/tasks/backlog_BACKLOG-109_lokale_db_snapshots_vor_riskanten_debug_repair_und_migrationsschritten.md",
                                "artifact_action": "CREATE_NEW",
                                "recommended_next_skill": "janus-preimplementation-check",
                                "next_skill_copy_prompt": "Prepare pre-implementation verification for BACKLOG-109.",
                                "handoff_scope": {
                                    "backlog_item": "BACKLOG-109",
                                    "entry_point": "PRE_IMPLEMENTATION_VERIFICATION",
                                    "required_artifact": "documentation/tasks/backlog_BACKLOG-109_lokale_db_snapshots_vor_riskanten_debug_repair_und_migrationsschritten.md",
                                    "required_next_skill": "janus-preimplementation-check",
                                    "evidence_paths": ["documentation/backlog/BACKLOG.md#BACKLOG-109"],
                                    "dropped_context": [],
                                },
                                "manual_review_needed": "NO",
                                "notes": ["Bounded handoff review only."],
                            }
                        )
                    }
                }
            ]
        }
        (run_dir / "response_body.json").write_text(json.dumps(response_body), encoding="utf-8")
        (run_dir / "response_summary.json").write_text(json.dumps(make_response_summary()), encoding="utf-8")
        input_path = self.temp_path / "good_input.json"
        input_path.write_text(json.dumps(make_input_payload()), encoding="utf-8")

        with patch.object(
            runner,
            "invoke_file_first_wrapper",
            return_value=type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        ), patch.object(
            runner,
            "run_healthcheck",
            return_value={"status": "PASS"},
        ):
            result = runner.run_consumer_flow(
                workflow_id="WF-BACKLOG-HANDOFF-FIXTURE-001",
                task_label="Backlog handoff delegated fixture",
                normal_target_model="5.4 medium",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00018,
                cost_estimate_confidence_percent=76.0,
                input_package_json=input_path,
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
                execute_direct_or=False,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "BACKLOG_HANDOFF_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(result["selected_path"], "delegated_backlog_handoff_review")
        self.assertIn("OR-Modell: qwen/qwen3-coder-30b-a3b-instruct", result["operator_result_lines"])

        telemetry_path = Path(result["telemetry_jsonl_path"])
        self.assertTrue(telemetry_path.exists())
        row = json.loads(telemetry_path.read_text(encoding="utf-8").strip())
        self.assertEqual(row["or_model"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(row["validation_result"], "PASS")


if __name__ == "__main__":
    unittest.main()
