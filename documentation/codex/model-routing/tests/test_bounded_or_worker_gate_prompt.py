from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

GATE_PROMPT_SPEC = importlib.util.spec_from_file_location(
    "bounded_or_worker_gate_prompt",
    SCRIPTS_DIR / "bounded_or_worker_gate_prompt.py",
)
gate_prompt = importlib.util.module_from_spec(GATE_PROMPT_SPEC)
assert GATE_PROMPT_SPEC and GATE_PROMPT_SPEC.loader
sys.modules[GATE_PROMPT_SPEC.name] = gate_prompt
GATE_PROMPT_SPEC.loader.exec_module(gate_prompt)

DISPATCHER_SPEC = importlib.util.spec_from_file_location(
    "codex_bounded_delegation_dispatcher",
    SCRIPTS_DIR / "codex_bounded_delegation_dispatcher.py",
)
dispatcher = importlib.util.module_from_spec(DISPATCHER_SPEC)
assert DISPATCHER_SPEC and DISPATCHER_SPEC.loader
sys.modules[DISPATCHER_SPEC.name] = dispatcher
DISPATCHER_SPEC.loader.exec_module(dispatcher)


class BoundedOrWorkerGatePromptTests(unittest.TestCase):
    def test_build_operator_prompt_lines_include_quota_recommendation_model_cost_and_confidence(self) -> None:
        lines = gate_prompt.build_operator_prompt_lines(
            choice_2_label="OR",
            selected_or_model="openai/gpt-oss-20b",
            estimated_or_cost=0.000321,
            cost_estimate_confidence_percent=88.0,
            operator_recommendation="PREFER_OR",
            operator_recommendation_reason="sehr guenstige deterministische Spur",
        )

        self.assertEqual(lines[0], "1 = Codex")
        self.assertEqual(lines[1], "2 = OR")
        self.assertIn("Codex-Guthaben", lines[2])
        self.assertIn("PREFER_OR", lines[3])
        self.assertIn("sehr guenstige deterministische Spur", lines[4])
        self.assertIn("openai/gpt-oss-20b", lines[5])
        self.assertIn("0.000321000", lines[6])
        self.assertIn("88%", lines[6])

    def test_build_or_roi_marks_negative_when_overhead_exceeds_savings(self) -> None:
        roi = gate_prompt.build_or_roi(
            estimated_codex_saved_tokens=1000,
            estimated_codex_or_overhead_tokens=2000,
            minimum_net_codex_saved_tokens=250,
        )

        self.assertEqual(roi["status"], "NEGATIVE")
        self.assertEqual(roi["net_codex_saved_tokens"], -1000)

    def test_build_or_roi_marks_positive_when_net_exceeds_threshold(self) -> None:
        roi = gate_prompt.build_or_roi(
            estimated_codex_saved_tokens=4000,
            estimated_codex_or_overhead_tokens=1200,
            minimum_net_codex_saved_tokens=500,
        )

        self.assertEqual(roi["status"], "POSITIVE")
        self.assertEqual(roi["net_codex_saved_tokens"], 2800)

    def test_prompt_summary_uses_or_arbeitspferd_for_debug_pilot(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_class": "debug_hypothesis_review",
                "task_label": "Debug gate",
                "normal_target_model": "5.4 medium",
                "selected_or_model": "qwen/qwen3.5-flash-02-23",
                "estimated_or_cost": 0.000321,
                "cost_estimate_confidence_percent": 88.0,
            },
        )()

        result = dispatcher.prompt_summary(args, "WF-GATE-001")

        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("2 = OR", result["operator_prompt_lines"])
        self.assertIn("Codex-Guthaben", result["operator_prompt_lines"][2])

    def test_dispatcher_prompt_summary_blocks_or_when_roi_is_negative(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_class": "debug_hypothesis_review",
                "task_label": "Debug gate",
                "normal_target_model": "5.4 medium",
                "selected_or_model": "qwen/qwen3.5-flash-02-23",
                "estimated_or_cost": 0.000321,
                "cost_estimate_confidence_percent": 88.0,
                "estimated_codex_saved_tokens": 1000,
                "estimated_codex_or_overhead_tokens": 2000,
                "minimum_net_codex_saved_tokens": 250,
                "require_positive_or_roi": False,
            },
        )()

        result = dispatcher.prompt_summary(args, "WF-GATE-ROI-NEG-001")

        self.assertEqual(result["selected_path"], "codex_only_or_roi_gate")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertNotIn("choice_2", result)
        self.assertEqual(result["or_roi"]["status"], "NEGATIVE")

    def test_dispatcher_prompt_summary_shows_or_when_roi_is_positive(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_class": "test_result_triage_review",
                "task_label": "Triage gate",
                "normal_target_model": "5.4 medium",
                "selected_or_model": "qwen/qwen3.5-flash-02-23",
                "estimated_or_cost": 0.000321,
                "cost_estimate_confidence_percent": 88.0,
                "estimated_codex_saved_tokens": 4000,
                "estimated_codex_or_overhead_tokens": 1200,
                "minimum_net_codex_saved_tokens": 500,
                "require_positive_or_roi": False,
            },
        )()

        result = dispatcher.prompt_summary(args, "WF-GATE-ROI-POS-001")

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["or_roi"]["status"], "POSITIVE")
        self.assertTrue(any("OR ROI Gate: POSITIVE" in line for line in result["operator_prompt_lines"]))

    def test_prompt_summary_restores_quickchange_operator_choice_when_shared_gate_is_reenabled(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_class": "quickchange_patch_review",
                "task_label": "Quickchange gate",
                "normal_target_model": "5.4 medium",
                "selected_or_model": "deepseek/deepseek-v4-flash",
                "estimated_or_cost": 0.00025,
                "cost_estimate_confidence_percent": 68.0,
            },
        )()

        result = dispatcher.prompt_summary(args, "WF-GATE-QUICKCHANGE-001")

        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["eligibility_reason_code"], "ELIGIBILITY_CONFIRMED")
        self.assertEqual(result["evidence_status"], "BOUNDED_LIVE_EVIDENCE_CONFIRMED")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_prompt_summary_shows_generator_review_when_visibility_is_approved(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_class": "generator_review",
                "task_label": "Generator gate",
                "normal_target_model": "5.4 medium",
                "selected_or_model": "probe/model",
                "estimated_or_cost": 0.00025,
                "cost_estimate_confidence_percent": 68.0,
            },
        )()

        result = dispatcher.prompt_summary(args, "WF-GATE-GENERATOR-001")

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_visibility"], "VISIBLE")
        self.assertEqual(result["visibility_status"], "VISIBLE_APPROVED")
        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_prompt_summary_shows_execution_write_apply_candidate_when_visibility_is_approved(self) -> None:
        args = type(
            "Args",
            (),
            {
                "task_class": "execution_write_apply_candidate",
                "task_label": "Write apply gate",
                "normal_target_model": "5.4 medium",
                "selected_or_model": "probe/model",
                "estimated_or_cost": 0.00025,
                "cost_estimate_confidence_percent": 68.0,
            },
        )()

        result = dispatcher.prompt_summary(args, "WF-GATE-WRITE-001")

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["operator_gate_visibility"], "VISIBLE")
        self.assertEqual(result["visibility_status"], "VISIBLE_APPROVED")
        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertIn("2 = OR", result["operator_prompt_lines"])

    def test_missing_gate_result_keeps_codex_only_fallback(self) -> None:
        result = gate_prompt.build_missing_gate_result(
            workflow_id="WF-GATE-003",
            task_label="Missing gate data",
            selected_path="codex_only_prompt_data_missing",
            missing_fields=["estimated_or_cost", "cost_estimate_confidence_percent"],
            final_outcome="LOCAL_CODEX_PATH_SELECTED",
            normal_target_model="5.4 medium",
            task_class="debug_hypothesis_review",
            eligibility_result="OR_ALLOWED",
            eligibility_reason_code="ELIGIBILITY_CONFIRMED",
            evidence_status="LIVE_EVIDENCE_CONFIRMED",
        )

        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["operator_gate_visibility"], "HIDDEN_FAIL_CLOSED")
        self.assertIn("estimated_or_cost", result["missing_gate_fields"])
        self.assertIn("cost_estimate_confidence_percent", result["missing_gate_fields"])
        self.assertNotIn("choice_2", result)

    def test_visibility_suppressed_result_keeps_everyday_gate_hidden(self) -> None:
        result = gate_prompt.build_visibility_suppressed_result(
            workflow_id="WF-GATE-004",
            task_label="Hidden partial candidate",
            selected_path="codex_only_visibility_hidden",
            final_outcome="LOCAL_CODEX_PATH_SELECTED",
            normal_target_model="5.4 medium",
            visibility_status="HIDDEN_PARTIAL_CANDIDATE",
            suppression_reason="partial_candidate_not_everyday_ready",
            selected_or_model="deepseek/deepseek-v4-flash",
            task_class="execution_write_apply_candidate",
            evidence_status="BOUNDED_AUDITED_FOUNDATION",
        )

        self.assertEqual(result["operator_gate_visibility"], "HIDDEN")
        self.assertEqual(result["visibility_status"], "HIDDEN_PARTIAL_CANDIDATE")
        self.assertEqual(result["choice_1"], "Codex")
        self.assertNotIn("choice_2", result)
        self.assertIn("partial_candidate_not_everyday_ready", result["operator_message"])

    def test_operator_registry_docs_match_visible_execution_write_apply_contract(self) -> None:
        inventory = (
            Path(__file__).resolve().parents[1]
            / "or_everyday_lane_inventory_2026-06-24.md"
        ).read_text(encoding="utf-8")
        summary = (
            Path(__file__).resolve().parents[1]
            / "or_everyday_operator_registry_summary_2026-06-24.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "| `janus-test-pipeline` | `generator_review` | `1 = Codex`, `2 = OR` | `OR_READY` |",
            inventory,
        )
        self.assertIn(
            "| `janus-executioner` | `execution_write_apply_candidate` via productive Dev-workhorse entry | `1 = Codex`, `2 = OR` | `OR_READY` |",
            inventory,
        )
        self.assertIn(
            "| `janus-test-pipeline` | `generator_review` | `1 = Codex`, `2 = OR` | `openai/gpt-oss-20b` via delegated intent / deterministic local execution | bounded generator-backed review only; Codex remains final reviewer and acceptance owner |",
            summary,
        )
        self.assertIn(
            "| `janus-executioner` | `execution_write_apply_candidate` | `1 = Codex`, `2 = OR` | accepted-source delegated write candidate with deterministic local patch apply | accepted-source-backed only; Codex remains diff reviewer, validation owner, and final acceptance owner |",
            summary,
        )
        self.assertIn(
            "| `janus-executioner` | `execution_write_apply_candidate` | `1 = Codex`, `2 = OR` |",
            summary,
        )


if __name__ == "__main__":
    unittest.main()
