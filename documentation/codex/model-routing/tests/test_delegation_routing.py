from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


spec = importlib.util.spec_from_file_location("delegation_routing", SCRIPTS_DIR / "delegation_routing.py")
delegation_routing = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = delegation_routing
spec.loader.exec_module(delegation_routing)


class DelegationRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = delegation_routing.load_manifest()
        self.task_list = delegation_routing.load_task_list()

    def test_manifest_and_task_list_validate(self) -> None:
        result = delegation_routing.validate_manifest_and_task_list(self.manifest, self.task_list)

        self.assertEqual(result["validation_result"], "PASS", result["issues"])
        self.assertGreaterEqual(result["lane_count"], 13)
        self.assertGreaterEqual(result["task_count"], 15)

    def test_documentation_draft_review_gate_recommends_transitional_delegate_path(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="documentation_draft_review",
            task_id="TASK-DU-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "codex-cli/gpt-5.4-read-only-sidecar")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_quickchange_patch_review_gate_recommends_openrouter_without_cursor_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="quickchange_patch_review",
            task_id="TASK-QC-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "3 = OpenRouter"])
        self.assertEqual(gate["visible_backends"], ["codex", "openrouter"])
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_backlog_handoff_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="backlog_handoff_review",
            task_id="TASK-BH-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_backlog_prioritization_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="backlog_prioritization_review",
            task_id="TASK-BP-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_backlog_intake_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="backlog_intake_review",
            task_id="TASK-BI-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_skill_router_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="skill_router_review",
            task_id="TASK-SR-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_health_check_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="health_check_review",
            task_id="TASK-HC-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_feature_design_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="feature_design_review",
            task_id="TASK-FD-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_spec_generator_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="spec_generator_review",
            task_id="TASK-SG-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_spec_normalizer_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="spec_normalizer_review",
            task_id="TASK-SN-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_spec_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="spec_review",
            task_id="TASK-SR-002",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_spec_to_task_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="spec_to_task_review",
            task_id="TASK-ST-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_task_breakdown_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="task_breakdown_review",
            task_id="TASK-TB-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_precheck_review_gate_recommends_openrouter_with_tri_modal_visibility(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="precheck_review",
            task_id="TASK-PC-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "auto")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_calibrated_cost_defaults_match_current_low_risk_tuning(self) -> None:
        quickchange_openrouter = self.manifest["lanes"]["quickchange_patch_review"]["openrouter"]
        debug_openrouter = self.manifest["lanes"]["debug_hypothesis_review"]["openrouter"]
        triage_openrouter = self.manifest["lanes"]["test_result_triage_review"]["openrouter"]
        spec_generator_openrouter = self.manifest["lanes"]["spec_generator_review"]["openrouter"]
        spec_to_task_openrouter = self.manifest["lanes"]["spec_to_task_review"]["openrouter"]
        execution_openrouter = self.manifest["lanes"]["execution_patch_candidate"]["openrouter"]

        self.assertEqual(quickchange_openrouter["prompt_estimated_or_cost"], 0.00013)
        self.assertEqual(quickchange_openrouter["prompt_cost_estimate_confidence_percent"], 65)
        self.assertEqual(debug_openrouter["prompt_estimated_or_cost"], 0.00048)
        self.assertEqual(debug_openrouter["prompt_cost_estimate_confidence_percent"], 85)
        self.assertEqual(triage_openrouter["prompt_estimated_or_cost"], 0.00031)
        self.assertEqual(triage_openrouter["prompt_cost_estimate_confidence_percent"], 90)
        self.assertEqual(spec_generator_openrouter["prompt_estimated_or_cost"], 0.00075)
        self.assertEqual(spec_generator_openrouter["prompt_cost_estimate_confidence_percent"], 85)
        self.assertEqual(spec_to_task_openrouter["prompt_estimated_or_cost"], 0.00072)
        self.assertEqual(spec_to_task_openrouter["prompt_cost_estimate_confidence_percent"], 74)
        self.assertNotIn("prompt_estimated_or_cost", execution_openrouter)

    def test_test_fixture_worker_gate_recommends_cursor_and_keeps_or_as_option_three(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="test_fixture_worker",
            task_id="TASK-TP-003",
        )

        self.assertEqual(gate["recommended_backend"], "cursor")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(gate["models"]["cursor"], "composer-2.5")
        self.assertEqual(gate["models"]["openrouter"], "moonshotai/kimi-k2.5")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_negative_roi_hides_external_backends(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="execution_patch_candidate",
            task_id="TASK-EX-001",
            estimated_codex_saved_tokens=12000,
            estimated_delegation_overhead_tokens=11000,
            minimum_net_codex_saved_tokens=10000,
        )

        self.assertEqual(gate["visible_backends"], ["codex"])
        self.assertEqual(gate["recommended_backend"], "codex")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex"])
        self.assertEqual(gate["roi"]["status"], "NEGATIVE")

    def test_never_delegate_tasks_are_codex_only(self) -> None:
        for task_id, lane_id in (
            ("TASK-TP-004", "live_test_execution"),
            ("TASK-TP-006", "diamond_retest_audit"),
        ):
            gate = delegation_routing.build_gate(
                manifest=self.manifest,
                task_list=self.task_list,
                lane_id=lane_id,
                task_id=task_id,
            )

            self.assertEqual(gate["visible_backends"], ["codex"])
            self.assertEqual(gate["recommended_backend"], "codex")


if __name__ == "__main__":
    unittest.main()
