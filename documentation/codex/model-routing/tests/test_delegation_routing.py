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

    def test_normalize_operator_choice_supports_four_choices_and_legacy_aliases(self) -> None:
        self.assertEqual(delegation_routing.normalize_operator_choice("1", self.manifest), "1")
        self.assertEqual(delegation_routing.normalize_operator_choice("2", self.manifest), "2")
        self.assertEqual(delegation_routing.normalize_operator_choice("3", self.manifest), "3")
        self.assertEqual(delegation_routing.normalize_operator_choice("4", self.manifest), "4")
        self.assertEqual(delegation_routing.normalize_operator_choice("cursor", self.manifest), "3")
        self.assertEqual(delegation_routing.normalize_operator_choice("openrouter", self.manifest), "2")
        self.assertEqual(delegation_routing.normalize_operator_choice("cursor-api", self.manifest), "4")

    def test_documentation_draft_review_recommends_cursor_api(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="documentation_draft_review",
            task_id="TASK-DU-001",
        )

        self.assertEqual(gate["recommended_backend"], "cursor")
        self.assertEqual(gate["recommended_choice"], "4")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "4 = Cursor API"])
        self.assertEqual(gate["models"]["cursor_api"], "gpt-5.4-mini-medium")
        self.assertEqual(gate["models"]["openrouter"], "codex-cli/gpt-5.4-read-only-sidecar")
        self.assertEqual(gate["roi"]["status"], "POSITIVE")

    def test_quickchange_gate_hides_composer_and_recommends_cursor_api(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="quickchange_patch_review",
            task_id="TASK-QC-001",
        )

        self.assertEqual(gate["recommended_backend"], "cursor")
        self.assertEqual(gate["recommended_choice"], "4")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "4 = Cursor API"])
        self.assertEqual(gate["visible_backends"], ["codex", "openrouter", "cursor"])

    def test_health_check_review_keeps_or_recommended_but_exposes_api_option(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="health_check_review",
            task_id="TASK-HC-001",
        )

        self.assertEqual(gate["recommended_backend"], "openrouter")
        self.assertEqual(gate["recommended_choice"], "2")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "4 = Cursor API"])
        self.assertEqual(gate["models"]["cursor_api"], "gpt-5.4-mini-medium")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")

    def test_test_fixture_worker_exposes_or_composer_and_api(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="test_fixture_worker",
            task_id="TASK-TP-003",
        )

        self.assertEqual(gate["recommended_backend"], "cursor")
        self.assertEqual(gate["recommended_choice"], "3")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "3 = Cursor Composer", "4 = Cursor API"])
        self.assertEqual(gate["models"]["cursor_composer"], "composer-2.5")
        self.assertEqual(gate["models"]["cursor_api"], "kimi-k2.7-code")
        self.assertEqual(gate["models"]["openrouter"], "qwen/qwen3-coder-30b-a3b-instruct")

    def test_debug_repro_hides_openrouter_and_api(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="debug_repro_investigation",
            task_id="TASK-DBG-002",
        )

        self.assertEqual(gate["recommended_backend"], "cursor")
        self.assertEqual(gate["recommended_choice"], "3")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "3 = Cursor Composer"])
        self.assertEqual(gate["visible_backends"], ["codex", "cursor"])
        self.assertNotIn("openrouter", gate["models"])

    def test_execution_write_apply_gate_uses_deterministic_apply_as_option_two(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="execution_write_apply_candidate",
            task_id="TASK-EX-002",
        )

        self.assertEqual(gate["recommended_backend"], "deterministic_apply")
        self.assertEqual(gate["recommended_choice"], "2")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = Deterministic Apply"])
        self.assertEqual(gate["visible_backends"], ["codex", "cursor"])
        self.assertEqual(gate["models"]["cursor"], "deterministic_local_apply")

    def test_negative_roi_keeps_execution_patch_external_options_visible_but_codex_recommended(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="execution_patch_candidate",
            task_id="TASK-EX-001",
            estimated_codex_saved_tokens=12000,
            estimated_delegation_overhead_tokens=11000,
            minimum_net_codex_saved_tokens=10000,
        )

        self.assertEqual(gate["visible_backends"], ["codex", "openrouter", "cursor"])
        self.assertEqual(gate["recommended_backend"], "codex")
        self.assertEqual(gate["recommended_choice"], "1")
        self.assertEqual(gate["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "3 = Cursor Composer", "4 = Cursor API"])
        self.assertEqual(gate["roi"]["status"], "NEGATIVE")
        self.assertEqual(gate["negative_roi_visibility_mode"], "keep_visible_non_recommended")

    def test_negative_roi_still_hides_external_backends_for_default_lanes(self) -> None:
        gate = delegation_routing.build_gate(
            manifest=self.manifest,
            task_list=self.task_list,
            lane_id="quickchange_patch_review",
            task_id="TASK-QC-001",
            estimated_codex_saved_tokens=7000,
            estimated_delegation_overhead_tokens=6500,
            minimum_net_codex_saved_tokens=3000,
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
