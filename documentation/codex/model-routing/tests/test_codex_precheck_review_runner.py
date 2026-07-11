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
    "codex_precheck_review_runner",
    SCRIPTS_DIR / "codex_precheck_review_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_response_summary(cost: float = 0.00009588) -> dict[str, object]:
    return {
        "generation_id": "gen-test-precheck-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 795,
            "completion_tokens": 149,
            "cost": cost,
        },
    }


class TestCodexPrecheckReviewRunner(unittest.TestCase):
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
            workflow_id="WF-PC-PROMPT-001",
            task_label="Precheck review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00012,
            cost_estimate_confidence_percent=76.0,
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-PC-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "status": "PASS",
                                "target_task": "BACKLOG-114",
                                "precheck_decision": "PRECHECK_PASS_CANDIDATE",
                                "artifact_identity": "PASS",
                                "scope_status": "ATOMIC",
                                "risk_level": "LOW",
                                "blocking_issues": [],
                                "required_evidence": [
                                    "repo-vs-installed parity or diff check for each bound skill copy",
                                    "one visible approved lane workflow verification",
                                    "one hidden lane workflow verification"
                                ],
                                "execution_handoff_ready": "YES",
                                "notes": "Bounded precheck review only; Codex remains final precheck owner."
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
                workflow_id="WF-PC-FIXTURE-001",
                task_label="Precheck delegated fixture",
                normal_target_model="5.4 medium",
                operator_choice="delegated",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00012,
                cost_estimate_confidence_percent=76.0,
                input_package_path=Path("development/openrouter-skill-tests/janus-preimplementation-check/precheck_input_package.json"),
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
                execute_direct_or=False,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "PRECHECK_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(result["selected_path"], "delegated_precheck_review")


if __name__ == "__main__":
    unittest.main()
