import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "codex_debug_hypothesis_review_runner.py"
)
SPEC = importlib.util.spec_from_file_location(
    "codex_debug_hypothesis_review_runner",
    SCRIPT_PATH,
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


FIXTURE_DIR = MODULE.MODEL_ROUTING_DIR / "debug-review-fixtures"


class TestCodexDebugHypothesisReviewRunner(unittest.TestCase):
    def test_prompt_summary_uses_visible_codex_or_wording(self) -> None:
        summary = MODULE.prompt_summary(
            workflow_id="WF-DEBUG-001",
            task_label="Bounded debug review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.0004,
            cost_estimate_confidence_percent=81,
        )

        self.assertEqual(summary["choice_1"], "Codex")
        self.assertEqual(summary["choice_2"], "OR")
        self.assertIn("1 = Codex", summary["operator_prompt_lines"])
        self.assertIn("2 = OR", summary["operator_prompt_lines"])

    def test_prompt_summary_blocks_or_when_roi_is_negative(self) -> None:
        summary = MODULE.prompt_summary(
            workflow_id="WF-DEBUG-ROI-NEG-001",
            task_label="Bounded debug review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.0004,
            cost_estimate_confidence_percent=81,
            estimated_codex_saved_tokens=900,
            estimated_codex_or_overhead_tokens=1400,
            minimum_net_codex_saved_tokens=250,
        )

        self.assertEqual(summary["selected_path"], "codex_only_or_roi_gate")
        self.assertEqual(summary["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(summary["or_roi"]["status"], "NEGATIVE")
        self.assertNotIn("choice_2", summary)

    def test_prompt_summary_shows_or_when_roi_is_positive(self) -> None:
        summary = MODULE.prompt_summary(
            workflow_id="WF-DEBUG-ROI-POS-001",
            task_label="Bounded debug review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.0004,
            cost_estimate_confidence_percent=81,
            estimated_codex_saved_tokens=3200,
            estimated_codex_or_overhead_tokens=900,
            minimum_net_codex_saved_tokens=500,
        )

        self.assertEqual(summary["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(summary["choice_2"], "OR")
        self.assertEqual(summary["or_roi"]["status"], "POSITIVE")
        self.assertTrue(any("OR ROI Gate: POSITIVE" in line for line in summary["operator_prompt_lines"]))

    def test_resolve_delegated_runtime_mode_requires_explicit_runtime(self) -> None:
        _, _, _, fallback = MODULE.resolve_delegated_runtime_mode(
            workflow_id="WF-DEBUG-001",
            task_label="Bounded debug review",
            normal_target_model="5.4 medium",
            delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
            fixture_result_json=None,
            use_local_or_fixture=False,
            execute_direct_or=False,
            or_local_fixture_response_path=None,
        )

        self.assertIsNotNone(fallback)
        assert fallback is not None
        self.assertEqual(fallback["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK")
        self.assertEqual(fallback["delegated_runtime_reason_code"], "DELEGATED_RUNTIME_MODE_REQUIRED")

    def test_run_consumer_flow_prompt_writes_visible_gate(self) -> None:
        input_payload = MODULE.load_json(FIXTURE_DIR / "debug_hypothesis_input_package_current_shape_2026-06-24.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            original_run_root = MODULE.RUN_ROOT
            MODULE.RUN_ROOT = Path(temp_dir)
            try:
                result = MODULE.run_consumer_flow(
                    workflow_id="WF-DEBUG-PROMPT-001",
                    task_label="Debug prompt proof",
                    normal_target_model="5.4 medium",
                    operator_choice="prompt",
                    delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                    estimated_or_cost=0.0004,
                    cost_estimate_confidence_percent=81,
                    input_payload=input_payload,
                )
                self.assertEqual(result["choice_2"], "OR")
                self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
                prompt_path = Path(temp_dir) / "WF-DEBUG-PROMPT-001" / "consumer_operator_choice_prompt.json"
                self.assertTrue(prompt_path.exists())
            finally:
                MODULE.RUN_ROOT = original_run_root

    def test_run_consumer_flow_delegated_fixture_passes(self) -> None:
        input_payload = MODULE.load_json(FIXTURE_DIR / "debug_hypothesis_input_package_current_shape_2026-06-24.json")
        fixture_path = FIXTURE_DIR / "debug_hypothesis_or_fixture_response_current_shape_2026-06-24.json"

        with tempfile.TemporaryDirectory() as temp_dir:
            original_run_root = MODULE.RUN_ROOT
            MODULE.RUN_ROOT = Path(temp_dir)
            try:
                result = MODULE.run_consumer_flow(
                    workflow_id="WF-DEBUG-DELEGATED-001",
                    task_label="Debug delegated fixture proof",
                    normal_target_model="5.4 medium",
                    operator_choice="delegated",
                    delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                    estimated_or_cost=0.0004,
                    cost_estimate_confidence_percent=81,
                    input_payload=input_payload,
                    fixture_result_json=fixture_path,
                    use_local_or_fixture=True,
                    or_local_fixture_response_path=fixture_path,
                )
                self.assertEqual(result["validation_result"], "PASS")
                self.assertEqual(result["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION")
                delegated_path = Path(temp_dir) / "WF-DEBUG-DELEGATED-001" / "consumer_operator_choice_delegated.json"
                self.assertTrue(delegated_path.exists())
                saved = json.loads(delegated_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["validation_result"], "PASS")
            finally:
                MODULE.RUN_ROOT = original_run_root


if __name__ == "__main__":
    unittest.main()
