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
    "codex_backlog_intake_review_runner",
    SCRIPTS_DIR / "codex_backlog_intake_review_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_input_payload() -> dict[str, object]:
    return {
        "workflow_id": "WF-BACKLOG-INTAKE-PACKAGE-001",
        "bound_skill_context": "janus-backlog-intake",
        "raw_user_request": "DeepDive cost wording is confusing in the savings area.",
        "source_type": "User Intake",
        "suspected_type": "IMPROVEMENT",
        "target_area": "Frontend",
        "evidence_snippets": [
            "User reports confusing savings wording in DeepDive cost view.",
        ],
        "expected_output": "One bounded READY backlog item draft with acceptance criteria and missing-info assessment.",
        "redaction_ready": True,
    }


def make_response_summary(cost: float = 0.00016096) -> dict[str, object]:
    return {
        "generation_id": "gen-test-backlog-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 475,
            "completion_tokens": 473,
            "cost": cost,
        },
    }


class TestCodexBacklogIntakeReviewRunner(unittest.TestCase):
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
            workflow_id="WF-BACKLOG-PROMPT-001",
            task_label="Backlog intake review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00018,
            cost_estimate_confidence_percent=74.0,
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
        self.assertIn("No delegated backlog write acceptance", result["boundaries"][0])

    def test_prompt_summary_aborts_when_estimate_missing(self) -> None:
        result = runner.prompt_summary(
            workflow_id="WF-BACKLOG-PROMPT-002",
            task_label="Backlog intake review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=None,
            cost_estimate_confidence_percent=74.0,
        )

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertIn("estimated_or_cost", result["missing_gate_fields"])

    def test_local_summary_keeps_codex_only(self) -> None:
        result = runner.local_summary(
            workflow_id="WF-BACKLOG-LOCAL-001",
            task_label="Backlog intake review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
        )

        self.assertEqual(result["selected_path"], "codex_only_operator_choice")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")

    def test_run_consumer_flow_rejects_invalid_input_package(self) -> None:
        bad_payload = make_input_payload()
        bad_payload.pop("redaction_ready")

        result = runner.run_consumer_flow(
            workflow_id="WF-BACKLOG-BAD-001",
            task_label="Backlog intake delegated bad package",
            normal_target_model="5.4 medium",
            operator_choice="delegated",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00018,
            cost_estimate_confidence_percent=74.0,
            input_payload=bad_payload,
            use_local_or_fixture=True,
            or_local_fixture_response_path=self.temp_path / "unused.json",
        )

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["selected_path"], "codex_local_fallback_invalid_input_package")

    def test_run_consumer_flow_prompt_writes_prompt_artifact(self) -> None:
        result = runner.run_consumer_flow(
            workflow_id="WF-BACKLOG-PROMPT-003",
            task_label="Backlog intake prompt path",
            normal_target_model="5.4 medium",
            operator_choice="prompt",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00018,
            cost_estimate_confidence_percent=74.0,
        )

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertTrue((runner.RUN_ROOT / "WF-BACKLOG-PROMPT-003" / "consumer_operator_choice_prompt.json").exists())

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-BACKLOG-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "status": "PASS",
                                "backlog_type": "IMPROVEMENT",
                                "suggested_status": "READY",
                                "title": "DeepDive savings wording is confusing",
                                "kurzbeschreibung": "Savings wording should be clearer in the DeepDive cost view.",
                                "erwartetes_verhalten": "Users understand the savings wording immediately.",
                                "tatsaechliches_verhalten": "The current wording is confusing.",
                                "reproduktion_kontext": "Open DeepDive cost view and read the savings label.",
                                "betroffener_bereich": "Frontend",
                                "nachweise": ["User report from chat"],
                                "akzeptanzkriterien": ["Clarify the savings wording in the DeepDive cost area."],
                                "fehlende_informationen": [],
                                "notes": "Bounded backlog candidate only.",
                            }
                        )
                    }
                }
            ]
        }
        (run_dir / "response_body.json").write_text(json.dumps(response_body), encoding="utf-8")
        (run_dir / "response_summary.json").write_text(json.dumps(make_response_summary()), encoding="utf-8")

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
                workflow_id="WF-BACKLOG-FIXTURE-001",
                task_label="Backlog intake delegated fixture",
                normal_target_model="5.4 medium",
                operator_choice="delegated",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00018,
                cost_estimate_confidence_percent=74.0,
                input_payload=make_input_payload(),
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "BACKLOG_INTAKE_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(result["selected_path"], "delegated_backlog_intake_review")
        self.assertIn("Tatsaechliche Kosten: 0.000160960", result["operator_result_lines"])

        telemetry_path = Path(result["telemetry_jsonl_path"])
        self.assertTrue(telemetry_path.exists())
        row = json.loads(telemetry_path.read_text(encoding="utf-8").strip())
        self.assertEqual(row["or_model"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(row["validation_result"], "PASS")


if __name__ == "__main__":
    unittest.main()
