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
    "codex_spec_to_task_runner",
    SCRIPTS_DIR / "codex_spec_to_task_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_response_summary(cost: float = 0.00016096) -> dict[str, object]:
    return {
        "generation_id": "gen-test-spec-to-task-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 475,
            "completion_tokens": 473,
            "cost": cost,
        },
    }


class TestCodexSpecToTaskRunner(unittest.TestCase):
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
            workflow_id="WF-ST-PROMPT-001",
            task_label="Spec to task",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00037,
            cost_estimate_confidence_percent=74.0,
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-ST-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "task_root_id": "TASK-SPEC21",
                                "source_spec": "documentation/SPEC/Spec Done/21_assisted_or_workhorse_mode_for_janus_skills.md",
                                "task_file_path": "documentation/tasks/TASK-SPEC21_assisted_or_workhorse_mode_for_janus_skills.md",
                                "backlog_item": "N/A",
                                "feature_name": "Assistierter OR-Arbeitspferd-Modus fuer Janus-Skills",
                                "generated_at": "2026-07-05T21:45:00",
                                "generated_tasks": [
                                    {
                                        "task_id": "TASK-SPEC21.1",
                                        "title": "Eligibility and redaction gate",
                                        "ziel": "Bound the first gate.",
                                        "scope": "Only the gating slice.",
                                        "files": ["documentation/codex/model-routing/scripts/bounded_or_worker_eligibility.py"],
                                        "steps": ["Add the eligibility gate."],
                                        "acceptance_criteria": ["Eligibility gate is deterministic."],
                                        "tests": ["pytest targeted gating tests"],
                                        "model": "5.4",
                                        "reason": "Core gating logic",
                                        "slice_theme": "eligibility_redaction_gate",
                                    },
                                    {
                                        "task_id": "TASK-SPEC21.2",
                                        "title": "Operator gate normalization",
                                        "ziel": "Normalize operator prompt behavior.",
                                        "scope": "Prompt and wording slice.",
                                        "files": ["documentation/codex/model-routing/scripts/bounded_or_worker_gate_prompt.py"],
                                        "steps": ["Normalize prompt output."],
                                        "acceptance_criteria": ["Prompt wording is consistent."],
                                        "tests": ["pytest targeted prompt tests"],
                                        "model": "5.4",
                                        "reason": "Prompt coherence",
                                        "slice_theme": "operator_gate_normalization",
                                    },
                                    {
                                        "task_id": "TASK-SPEC21.3",
                                        "title": "Telemetry and healthcheck capture",
                                        "ziel": "Capture telemetry for bounded runs.",
                                        "scope": "File-first capture and telemetry slice.",
                                        "files": ["documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1"],
                                        "steps": ["Add telemetry capture."],
                                        "acceptance_criteria": ["Telemetry capture is complete."],
                                        "tests": ["pytest targeted telemetry tests"],
                                        "model": "5.4",
                                        "reason": "Telemetry foundation",
                                        "slice_theme": "telemetry_healthcheck_capture",
                                    },
                                    {
                                        "task_id": "TASK-SPEC21.4",
                                        "title": "Consumer integration without scope widening",
                                        "ziel": "Integrate bounded consumers.",
                                        "scope": "Consumer integration only.",
                                        "files": ["documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py"],
                                        "steps": ["Wire consumer flow."],
                                        "acceptance_criteria": ["Consumer integration stays bounded."],
                                        "tests": ["pytest targeted consumer tests"],
                                        "model": "5.4",
                                        "reason": "Final bounded integration",
                                        "slice_theme": "consumer_integration_without_scope_widening",
                                    },
                                ],
                                "execution_model": "5.4",
                                "next_skill": "janus-task-breakdown",
                                "notes": ["Bounded compilation draft only.", "Codex remains final task writer."],
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
            "validate_rendered_task",
            return_value=(0, "", ""),
        ):
            result = runner.run_consumer_flow(
                workflow_id="WF-ST-FIXTURE-001",
                task_label="Spec to task delegated fixture",
                normal_target_model="5.4 medium",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00037,
                cost_estimate_confidence_percent=74.0,
                input_package_json=Path("development/openrouter-skill-tests/janus-spec-to-task/spec_to_task_input_package.json"),
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
                execute_direct_or=False,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "SPEC_TO_TASK_DRAFT_READY_FOR_CODEX_WRITE")
        self.assertEqual(result["selected_path"], "delegated_spec_to_task_draft")


if __name__ == "__main__":
    unittest.main()
