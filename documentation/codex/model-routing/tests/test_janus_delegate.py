from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
MODEL_ROUTING_DIR = Path(__file__).resolve().parents[1]
FEATURE_DESIGN_NO_LIVE_DOC = MODEL_ROUTING_DIR / "FEATURE_DESIGN_REVIEW_NO_LIVE_PATH_2026-07-07.md"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


spec = importlib.util.spec_from_file_location("janus_delegate", SCRIPTS_DIR / "janus_delegate.py")
janus_delegate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = janus_delegate
spec.loader.exec_module(janus_delegate)


class JanusDelegateTests(unittest.TestCase):
    def route(self, *args: str) -> dict[str, object]:
        parsed = janus_delegate.parse_args([
            "--workflow-id",
            "WF-TRI-MODAL-TEST-001",
            *args,
        ])
        return janus_delegate.route(parsed)

    def test_prompt_mode_shows_tri_modal_gate_for_fixture_worker(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "cursor")

    def test_backlog_intake_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "backlog_intake_review",
            "--task-id",
            "TASK-BI-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-backlog-intake/backlog_intake_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_backlog_intake_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_backlog_prioritization_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "backlog_prioritization_review",
            "--task-id",
            "TASK-BP-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-backlog-prioritization/backlog_prioritization_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_backlog_prioritization_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_backlog_handoff_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "backlog_handoff_review",
            "--task-id",
            "TASK-BH-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-backlog-handoff/backlog_handoff_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_backlog_handoff_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_documentation_draft_openrouter_choice_plans_dispatcher_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "documentation_draft_review",
            "--task-id",
            "TASK-DU-001",
            "--operator-choice",
            "3",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_bounded_delegation_dispatcher.py")
        self.assertIn("--task-class", result["planned_command"])
        self.assertIn("documentation_draft", result["planned_command"])
        self.assertIn("--operator-choice", result["planned_command"])
        self.assertIn("prompt", result["planned_command"])
        self.assertNotIn("--input-package-json", result["planned_command"])
        self.assertIn("bounded read-only documentation draft helper", result["operator_message"])

    def test_quickchange_prompt_mode_shows_shared_gate_without_cursor(self) -> None:
        result = self.route("--lane", "quickchange_patch_review", "--task-id", "TASK-QC-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "3 = OpenRouter"])
        self.assertEqual(result["visible_backends"], ["codex", "openrouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_quickchange_openrouter_choice_plans_dispatcher_with_bounded_args(self) -> None:
        result = self.route(
            "--lane",
            "quickchange_patch_review",
            "--task-id",
            "TASK-QC-001",
            "--operator-choice",
            "3",
            "--prompt-path",
            "documentation/codex/model-routing/fixtures/examples/quickchange_patch_review_prompt_example.md",
            "--editable-path",
            "documentation/codex/model-routing/fixtures/examples/quickchange_patch_review_target_example.txt",
            "--max-touched-files",
            "1",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_bounded_delegation_dispatcher.py")
        self.assertIn("--task-class", result["planned_command"])
        self.assertIn("quickchange_patch_review", result["planned_command"])
        self.assertIn("--prompt-path", result["planned_command"])
        self.assertIn("documentation\\codex\\model-routing\\fixtures\\examples\\quickchange_patch_review_prompt_example.md", result["planned_command"])
        self.assertIn("--editable-path", result["planned_command"])
        self.assertIn("documentation/codex/model-routing/fixtures/examples/quickchange_patch_review_target_example.txt", result["planned_command"])
        self.assertIn("--max-touched-files", result["planned_command"])
        self.assertIn("existing bounded quickchange dispatcher path", result["operator_message"])
    def test_skill_router_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "skill_router_review",
            "--task-id",
            "TASK-SR-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-skill-router/skill_router_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_skill_router_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_health_check_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "health_check_review", "--task-id", "TASK-HC-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_health_check_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "health_check_review",
            "--task-id",
            "TASK-HC-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-health-check/health_check_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_health_check_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_execution_patch_prompt_mode_shows_tri_modal_gate_with_cursor_recommended(self) -> None:
        result = self.route(
            "--lane",
            "execution_patch_candidate",
            "--task-id",
            "TASK-EX-001",
            "--operator-choice",
            "prompt",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["visible_backends"], ["codex", "cursor", "openrouter"])
        self.assertEqual(result["recommended_backend"], "cursor")

    def test_execution_write_apply_prompt_mode_shows_deterministic_apply_gate(self) -> None:
        result = self.route(
            "--lane",
            "execution_write_apply_candidate",
            "--task-id",
            "TASK-EX-002",
            "--operator-choice",
            "prompt",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Deterministic Apply"])
        self.assertEqual(result["visible_backends"], ["codex", "cursor"])
        self.assertEqual(result["recommended_backend"], "deterministic_apply")

    def test_execution_write_apply_option_two_plans_deterministic_apply_runner(self) -> None:
        result = self.route(
            "--lane",
            "execution_write_apply_candidate",
            "--task-id",
            "TASK-EX-002",
            "--operator-choice",
            "2",
            "--input-package-json",
            "documentation/codex/model-routing/fixtures/examples/execution_write_apply_input_package_example.json",
            "--allowlist-file",
            "documentation/codex/model-routing/fixtures/examples/allowlists/execution_patch_allowlist.txt",
            "--accepted-source-run-dir",
            "documentation/codex/model-routing/execution-direct-or-runs/WF-EXEC-PATCH-EXAMPLE-001",
            "--estimated-codex-saved-tokens",
            "28000",
            "--estimated-delegation-overhead-tokens",
            "10000",
            "--minimum-net-codex-saved-tokens",
            "12000",
            "--dry-run",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "deterministic_apply")
        self.assertEqual(result["final_outcome"], "DETERMINISTIC_APPLY_DRY_RUN_READY")
        self.assertEqual(result["selected_model"], "deterministic_local_apply")
        self.assertEqual(result["planned_runner"], "codex_execution_write_apply_candidate_runner.py")
        self.assertIn("--accepted-source-run-dir", result["planned_command"])
        self.assertIn("codex_execution_write_apply_candidate_runner.py", " ".join(result["planned_command"]))
        self.assertIn(
            "documentation\\codex\\model-routing\\execution-direct-or-runs\\WF-EXEC-PATCH-EXAMPLE-001",
            result["planned_command"],
        )
        self.assertNotIn("janus_cursor_worker_runner.py", " ".join(result["planned_command"]))

    def test_feature_design_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "feature_design_review", "--task-id", "TASK-FD-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_feature_design_no_live_doc_exists_and_references_current_lane_contract(self) -> None:
        content = FEATURE_DESIGN_NO_LIVE_DOC.read_text(encoding="utf-8")

        self.assertIn("TASK-FD-001", content)
        self.assertIn("feature_design_review", content)
        self.assertIn("3 = OpenRouter", content)
        self.assertIn("qwen/qwen3-coder-30b-a3b-instruct", content)
        self.assertIn("feature_design_input_package.json", content)

    def test_feature_design_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "feature_design_review",
            "--task-id",
            "TASK-FD-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-feature-design/feature_design_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_feature_design_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_spec_generator_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "spec_generator_review", "--task-id", "TASK-SG-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_spec_generator_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "spec_generator_review",
            "--task-id",
            "TASK-SG-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-spec-generator/spec_generator_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_spec_generator_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_spec_normalizer_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "spec_normalizer_review", "--task-id", "TASK-SN-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_spec_normalizer_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "spec_normalizer_review",
            "--task-id",
            "TASK-SN-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-spec-normalizer/spec_normalizer_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_spec_normalizer_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_spec_review_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "spec_review", "--task-id", "TASK-SR-002", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_spec_review_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "spec_review",
            "--task-id",
            "TASK-SR-002",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-spec-review/spec_review_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_spec_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_spec_to_task_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "spec_to_task_review", "--task-id", "TASK-ST-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_spec_to_task_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "spec_to_task_review",
            "--task-id",
            "TASK-ST-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-spec-to-task/spec_to_task_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_spec_to_task_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_task_breakdown_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "task_breakdown_review", "--task-id", "TASK-TB-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_task_breakdown_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "task_breakdown_review",
            "--task-id",
            "TASK-TB-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-task-breakdown/task_breakdown_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_task_breakdown_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_precheck_prompt_mode_shows_tri_modal_gate(self) -> None:
        result = self.route("--lane", "precheck_review", "--task-id", "TASK-PC-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor", "3 = OpenRouter"])
        self.assertEqual(result["recommended_backend"], "openrouter")

    def test_precheck_openrouter_choice_plans_legacy_runner_through_shared_delegate(self) -> None:
        result = self.route(
            "--lane",
            "precheck_review",
            "--task-id",
            "TASK-PC-001",
            "--operator-choice",
            "3",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-preimplementation-check/precheck_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["recommended_backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_precheck_review_runner.py")
        self.assertIn("--estimated-or-cost", result["planned_command"])
        self.assertIn("--cost-estimate-confidence-percent", result["planned_command"])
        self.assertNotIn("--estimated-codex-saved-tokens", result["planned_command"])
        self.assertNotIn("--estimated-delegation-overhead-tokens", result["planned_command"])

    def test_cursor_choice_plans_cursor_runner_without_live_call(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "2")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "cursor")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_DRY_RUN_READY")
        self.assertFalse(result["live_execution_allowed"])
        self.assertIn("janus_cursor_worker_runner.py", " ".join(result["planned_command"]))
        self.assertEqual(result["selected_model"], "composer-2.5")

    def test_openrouter_choice_keeps_or_as_option_three_plan_only(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "3")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertFalse(result["live_execution_allowed"])
        self.assertEqual(result["selected_model"], "moonshotai/kimi-k2.5")
        self.assertEqual(result["planned_runner"], "test_pipeline_sidecar_write_pilot_runner.py")

    def test_debug_repro_prompt_mode_stays_cursor_only_when_or_has_no_bounded_shell_authority(self) -> None:
        result = self.route("--lane", "debug_repro_investigation", "--task-id", "TASK-DBG-002", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Cursor"])
        self.assertEqual(result["visible_backends"], ["codex", "cursor"])
        self.assertEqual(result["recommended_backend"], "cursor")
        self.assertNotIn("openrouter", result["models"])

    def test_live_execution_rejects_cursor_override(self) -> None:
        result = self.route("--lane", "live_test_execution", "--task-id", "TASK-TP-004", "--operator-choice", "2")

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["final_outcome"], "DELEGATION_BACKEND_NOT_AVAILABLE")
        self.assertEqual(result["visible_backends"], ["codex"])

    def test_codex_choice_for_final_validation_stays_local(self) -> None:
        result = self.route("--task-id", "TASK-EX-003", "--operator-choice", "1")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "codex")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")

    def test_execute_live_cursor_requires_cursor_choice(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "1", "--execute-live-cursor")

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["final_outcome"], "CURSOR_LIVE_EXECUTION_REQUIRES_CURSOR_CHOICE")

    def test_execute_live_cursor_invokes_runner_and_returns_result(self) -> None:
        completed = janus_delegate.subprocess.CompletedProcess(
            args=["python", "documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py"],
            returncode=0,
            stdout=json.dumps(
                {
                    "backend": "cursor",
                    "lane_id": "test_fixture_worker",
                    "workflow_id": "WF-TRI-MODAL-TEST-001",
                    "selected_model": "composer-2.5",
                    "session_id": "sess-123",
                    "validation_result": "PASS",
                    "final_outcome": "CURSOR_WORKER_READY_FOR_CODEX_REVIEW",
                    "changed_files": [
                        "development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/fixtures/contact_memory_fixture.json"
                    ],
                    "changed_outside_allowlist": [],
                    "operator_message": "Cursor worker finished the bounded slice and returned artifacts for Codex review.",
                }
            ),
            stderr="",
        )
        with patch.object(janus_delegate, "run_command", return_value=completed) as mocked_run:
            result = self.route(
                "--lane",
                "test_fixture_worker",
                "--task-id",
                "TASK-TP-003",
                "--operator-choice",
                "2",
                "--execute-live-cursor",
                "--input-package-json",
                "documentation/codex/model-routing/fixtures/examples/test_fixture_worker_input_package_example.json",
                "--allowlist-file",
                "documentation/codex/model-routing/fixtures/examples/allowlists/test_fixture_allowlist.txt",
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_READY_FOR_CODEX_REVIEW")
        self.assertTrue(result["live_execution_allowed"])
        self.assertEqual(result["session_id"], "sess-123")
        self.assertIn("--execute-live", result["planned_command"])
        mocked_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
