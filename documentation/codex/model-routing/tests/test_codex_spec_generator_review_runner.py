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
    "codex_spec_generator_review_runner",
    SCRIPTS_DIR / "codex_spec_generator_review_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def make_response_summary(cost: float = 0.00016096) -> dict[str, object]:
    return {
        "generation_id": "gen-test-spec-generator-001",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 475,
            "completion_tokens": 473,
            "cost": cost,
        },
    }


class TestCodexSpecGeneratorReviewRunner(unittest.TestCase):
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
            workflow_id="WF-SG-PROMPT-001",
            task_label="Spec generator review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.00027,
            cost_estimate_confidence_percent=70.0,
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("1 = Codex", result["operator_prompt_lines"])
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        run_dir = runner.RUN_ROOT / "WF-SG-FIXTURE-001"
        run_dir.mkdir(parents=True, exist_ok=True)
        response_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "status": "PASS",
                                "source_type": "LATEST_DECISION_SUMMARY",
                                "source_path": "documentation/codex/model-routing/codex_first_real_or_pilot_decision_summary_2026-06-16.md",
                                "target_spec_path": "documentation/SPEC/first_real_or_pilot_for_bounded_janus_delegation.md",
                                "recommended_next_skill": "janus-spec-review",
                                "mechanical_cleanup_required": "NO",
                                "notes": [
                                    "Bounded draft only.",
                                    "Codex remains final writer.",
                                ],
                                "structured_spec": {
                                    "routing": {
                                        "target_skill": "janus-spec-review",
                                        "recommended_model": "5.4",
                                        "recommended_reasoning": "medium",
                                        "new_chat": "no",
                                        "complexity_score": 42,
                                        "confidence": "MEDIUM",
                                        "dashboard_hint": "SAFE",
                                        "reason": "Locked decision summary is sufficient for one bounded spec draft.",
                                    },
                                    "feature_identity": {
                                        "Feature Name": "First Real OR Pilot for Bounded Janus Delegation",
                                        "Primary Goal": "Prove one real bounded OR-assisted write task under Codex-owned review and acceptance.",
                                    },
                                    "user_value": [
                                        "Suitable low-risk Janus work can be delegated without losing Codex-owned validation."
                                    ],
                                    "target_surface": {
                                        "Primary Surface": "janus-quickchange bounded delegated write candidate",
                                    },
                                    "user_action_surface": {
                                        "Trigger": "Operator starts a bounded delegation-safe quickchange path."
                                    },
                                    "system_behavior": [
                                        "One tiny allowlisted quickchange returns a reviewable diff, changed-files list, and validation evidence."
                                    ],
                                    "data_persistence": {
                                        "Persistence Required": "NO",
                                        "Stored Artifact": "Spec draft and bounded lane artifacts",
                                    },
                                    "constraints": [
                                        "No authoritative spec write, task creation, or implementation authority is delegated."
                                    ],
                                    "security_privacy": {
                                        "Guardrail": "Allowlist, touched-file cap, and Codex-owned acceptance remain mandatory."
                                    },
                                    "edge_cases": [
                                        "Any missing artifact or allowlist escape discards the delegated result and falls back locally."
                                    ],
                                    "definition_of_done": [
                                        "Wenn die Delegation bounded bleibt, dann entsteht ein reviewbarer Spec-Entwurf mit allen Pflichtsektionen."
                                    ],
                                    "test_strategy": {
                                        "Primary Validation": "Validate required headings and routing block in rendered markdown."
                                    },
                                    "out_of_scope": [
                                        "Broad janus-executioner delegation, release actions, and production routing remain excluded."
                                    ],
                                    "internal_complexity_breakdown": {
                                        "Scope Size": 8,
                                        "Architectural Risk": 7,
                                        "State / Persistence Complexity": 6,
                                        "Cross-System Dependencies": 9,
                                        "Ambiguity Level": 12,
                                        "Total Complexity Score": 42,
                                        "Routing Decision": "5.4",
                                        "Routing Reasoning": "medium",
                                        "Routing Confidence": "MEDIUM",
                                        "Dashboard Hint": "SAFE",
                                    },
                                },
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
                workflow_id="WF-SG-FIXTURE-001",
                task_label="Spec generator delegated fixture",
                normal_target_model="5.4 medium",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.00027,
                cost_estimate_confidence_percent=70.0,
                input_package_json=Path("development/openrouter-skill-tests/janus-spec-generator/spec_generator_input_package.json"),
                use_local_or_fixture=True,
                or_local_fixture_response_path=self.temp_path / "fixture-response.json",
                execute_direct_or=False,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "SPEC_GENERATOR_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(result["selected_path"], "delegated_spec_generator_review")
        self.assertIn("Tatsaechliche OR-Kosten", result["operator_result_lines"][2])


if __name__ == "__main__":
    unittest.main()
