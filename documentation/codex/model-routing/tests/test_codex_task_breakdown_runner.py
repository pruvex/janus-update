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
    "codex_task_breakdown_runner",
    SCRIPTS_DIR / "codex_task_breakdown_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_response_summary(cost: float = 0.00016096) -> dict[str, object]:
    return {
        "generation_id": "gen-test-task-breakdown-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 475,
            "completion_tokens": 473,
            "cost": cost,
        },
    }


class TestCodexTaskBreakdownRunner(unittest.TestCase):
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
            workflow_id="WF-TB-PROMPT-001",
            task_label="Task breakdown",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00018,
            cost_estimate_confidence_percent=75.0,
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-TB-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "spec_path": "documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md",
                                "task_file_path": "documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md",
                                "backlog_item": "N/A",
                                "target_task": "TASK-SPEC21.3",
                                "target_subtask": "N/A",
                                "decision": "TASK DESIGN COMPLETE",
                                "source_of_truth": "Spec 21 and TASK-SPEC21 artifact remain the only source of truth for this bounded slice.",
                                "files": [
                                    "documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1",
                                    "documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py",
                                    "documentation/codex/model-routing/scripts/bounded_or_worker_outcome.py",
                                    "documentation/codex/skills/janus-health-check/scripts/health_snapshot.py",
                                    "documentation/codex/model-routing/tests/",
                                ],
                                "acceptance_criteria": "file-first capture artifacts for accepted and rejected bounded runs; actual OR cost surfaced after completion when usage exists; health_snapshot.py ingests bounded OR telemetry without breaking non-OR behavior; incomplete capture or missing usage cannot be reported as accepted success",
                                "tests": "fixture-driven complete capture and telemetry generation; negative coverage for missing usage or incomplete capture; healthcheck ingestion coverage against bounded OR telemetry; regression coverage that existing healthcheck behavior stays unchanged without OR input",
                                "execution_model": "5.4",
                                "readiness": "READY_FOR_PRECHECK",
                                "next_skill": "janus-preimplementation-check",
                                "model_recommendation": "5.4",
                                "notes": ["Bounded single-target refinement only.", "Codex remains final handoff writer."],
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
        ), patch.object(
            runner,
            "validate_rendered_breakdown",
            return_value=(0, "", ""),
        ):
            result = runner.run_consumer_flow(
                workflow_id="WF-TB-FIXTURE-001",
                task_label="Task breakdown delegated fixture",
                normal_target_model="5.4 medium",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00018,
                cost_estimate_confidence_percent=75.0,
                input_package_json=Path("development/openrouter-skill-tests/janus-task-breakdown/task_breakdown_input_package.json"),
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
                execute_direct_or=False,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "TASK_BREAKDOWN_READY_FOR_CODEX_HANDOFF_WRITE")
        self.assertEqual(result["selected_path"], "delegated_task_breakdown_review")


if __name__ == "__main__":
    unittest.main()
