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
    def test_build_operator_prompt_lines_include_model_cost_and_confidence(self) -> None:
        lines = gate_prompt.build_operator_prompt_lines(
            choice_2_label="OR-Arbeitspferd",
            selected_or_model="openai/gpt-oss-20b",
            estimated_or_cost=0.000321,
            cost_estimate_confidence_percent=88.0,
        )

        self.assertEqual(lines[0], "1 = Codex")
        self.assertEqual(lines[1], "2 = OR-Arbeitspferd")
        self.assertIn("openai/gpt-oss-20b", lines[2])
        self.assertIn("0.000321000", lines[3])
        self.assertIn("88%", lines[3])

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

        self.assertEqual(result["choice_2"], "OR-Arbeitspferd")
        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertIn("2 = OR-Arbeitspferd", result["operator_prompt_lines"])
        self.assertIn("qwen/qwen3.5-flash-02-23", result["operator_prompt_lines"][2])

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
        self.assertIn("estimated_or_cost", result["missing_gate_fields"])
        self.assertIn("cost_estimate_confidence_percent", result["missing_gate_fields"])


if __name__ == "__main__":
    unittest.main()
