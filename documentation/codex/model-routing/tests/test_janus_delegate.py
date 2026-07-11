from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
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
            "WF-4CHOICE-TEST-001",
            *args,
        ])
        return janus_delegate.route(parsed)

    def test_prompt_mode_shows_four_choice_gate_for_fixture_worker(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "3 = Cursor Composer", "4 = Cursor API"])
        self.assertEqual(result["recommended_backend"], "cursor")
        self.assertEqual(result["recommended_choice"], "3")
        self.assertIn("3. Cursor Composer", result["operator_message"])

    def test_quickchange_prompt_mode_hides_composer_but_shows_api(self) -> None:
        result = self.route("--lane", "quickchange_patch_review", "--task-id", "TASK-QC-001", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "4 = Cursor API"])
        self.assertEqual(result["recommended_choice"], "4")

    def test_backlog_handoff_openrouter_choice_uses_option_two(self) -> None:
        result = self.route(
            "--lane",
            "backlog_handoff_review",
            "--task-id",
            "TASK-BH-001",
            "--operator-choice",
            "2",
            "--input-package-json",
            "development/openrouter-skill-tests/janus-backlog-handoff/backlog_handoff_input_package.json",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertEqual(result["planned_runner"], "codex_backlog_handoff_review_runner.py")

    def test_execution_patch_prompt_mode_exposes_all_four_choices(self) -> None:
        result = self.route(
            "--lane",
            "execution_patch_candidate",
            "--task-id",
            "TASK-EX-001",
            "--operator-choice",
            "prompt",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "3 = Cursor Composer", "4 = Cursor API"])
        self.assertEqual(result["recommended_choice"], "3")

    def test_execution_patch_negative_roi_prompt_mode_keeps_choices_visible_but_recommends_codex(self) -> None:
        result = self.route(
            "--lane",
            "execution_patch_candidate",
            "--task-id",
            "TASK-EX-001",
            "--operator-choice",
            "prompt",
            "--estimated-codex-saved-tokens",
            "14000",
            "--estimated-delegation-overhead-tokens",
            "4500",
            "--minimum-net-codex-saved-tokens",
            "10000",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = OpenRouter", "3 = Cursor Composer", "4 = Cursor API"])
        self.assertEqual(result["recommended_choice"], "1")
        self.assertIn("Hinweis:", result["operator_message"])

    def test_execution_write_apply_prompt_mode_keeps_deterministic_choice_two(self) -> None:
        result = self.route(
            "--lane",
            "execution_write_apply_candidate",
            "--task-id",
            "TASK-EX-002",
            "--operator-choice",
            "prompt",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Deterministic Apply"])
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
        self.assertIn("codex_execution_write_apply_candidate_runner.py", " ".join(result["planned_command"]))

    def test_cursor_composer_choice_plans_shared_cursor_runner(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "3")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "cursor")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_DRY_RUN_READY")
        self.assertEqual(result["selected_model"], "composer-2.5")
        self.assertEqual(result["cursor_pool"], "auto_composer")
        self.assertIn("--cursor-pool", result["planned_command"])
        self.assertIn("auto_composer", result["planned_command"])
        self.assertTrue(Path(result["planned_command"][1]).is_absolute())
        self.assertTrue(str(result["planned_command"][1]).endswith("janus_cursor_worker_runner.py"))

    def test_cursor_api_choice_plans_same_runner_with_api_pool(self) -> None:
        result = self.route("--lane", "execution_patch_candidate", "--task-id", "TASK-EX-001", "--operator-choice", "4")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "cursor")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_DRY_RUN_READY")
        self.assertEqual(result["selected_model"], "kimi-k2.7-code")
        self.assertEqual(result["cursor_pool"], "api")
        self.assertIn("--cursor-pool", result["planned_command"])
        self.assertIn("api", result["planned_command"])

    def test_cursor_api_choice_stays_available_for_execution_patch_even_when_roi_is_negative(self) -> None:
        result = self.route(
            "--lane",
            "execution_patch_candidate",
            "--task-id",
            "TASK-EX-001",
            "--operator-choice",
            "4",
            "--estimated-codex-saved-tokens",
            "14000",
            "--estimated-delegation-overhead-tokens",
            "4500",
            "--minimum-net-codex-saved-tokens",
            "10000",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_DRY_RUN_READY")
        self.assertEqual(result["selected_model"], "kimi-k2.7-code")
        self.assertEqual(result["cursor_pool"], "api")

    def test_openrouter_choice_keeps_or_as_option_two_plan_only(self) -> None:
        result = self.route("--lane", "test_fixture_worker", "--task-id", "TASK-TP-003", "--operator-choice", "2")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "openrouter")
        self.assertEqual(result["final_outcome"], "OPENROUTER_WORKER_DRY_RUN_READY")
        self.assertFalse(result["live_execution_allowed"])
        self.assertEqual(result["selected_model"], "qwen/qwen3-coder-30b-a3b-instruct")
        self.assertEqual(result["planned_runner"], "test_pipeline_sidecar_write_pilot_runner.py")

    def test_debug_repro_prompt_mode_stays_composer_only_when_or_has_no_shell_authority(self) -> None:
        result = self.route("--lane", "debug_repro_investigation", "--task-id", "TASK-DBG-002", "--operator-choice", "prompt")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "3 = Cursor Composer"])
        self.assertEqual(result["recommended_choice"], "3")

    def test_live_execution_rejects_cursor_override_for_codex_only_lane(self) -> None:
        result = self.route("--lane", "live_test_execution", "--task-id", "TASK-TP-004", "--operator-choice", "3")

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["final_outcome"], "DELEGATION_BACKEND_NOT_AVAILABLE")

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
                    "workflow_id": "WF-4CHOICE-TEST-001",
                    "selected_model": "composer-2.5",
                    "cursor_pool": "auto_composer",
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
                "3",
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
