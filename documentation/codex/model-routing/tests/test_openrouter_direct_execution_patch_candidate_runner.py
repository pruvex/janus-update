from __future__ import annotations

import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "openrouter_direct_execution_patch_candidate_runner.py"
)
SPEC = importlib.util.spec_from_file_location("openrouter_direct_execution_patch_candidate_runner", SCRIPT_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class OpenRouterDirectExecutionPatchCandidateRunnerTests(unittest.TestCase):
    def make_args(self) -> Namespace:
        return Namespace(
            task_label="Execution patch",
            normal_target_model="5.4/medium",
            model="deepseek/deepseek-v4-flash",
            task_class="execution_patch_candidate",
            budget_profile="execution_patch_candidate",
            workflow_id="DIRECT-OR-EXECUTION-FIXTURE-REDESIGN-001",
            input_package_json=None,
            estimated_prompt_tokens=1500,
            estimated_completion_tokens=2600,
            estimated_or_cost=0.000603,
            cost_cap=0.05,
            cost_estimate_confidence_percent=20.0,
            cost_estimate_sample_count=1,
            cost_estimate_mean_abs_error_percent=66.76,
            cost_estimate_p50_error_percent=66.76,
            cost_estimate_p90_error_percent=66.76,
            cost_estimate_basis="fixture",
            prompt_template_hash="sha256:test",
            task_variant="execution_patch_candidate",
            price_snapshot_source="manual",
            price_snapshot_timestamp="2026-06-19T16:10:00+02:00",
            estimated_codex_effort="medium",
            temperature=0.0,
            max_tokens=2600,
            use_local_fixture=True,
            local_fixture_response_path=None,
            execute_live=False,
        )

    def make_input_payload(self) -> dict[str, object]:
        return {
            "workflow_id": "BACKLOG-108-EXECUTION-PATCH-CANDIDATE-001",
            "bound_skill_context": "janus-executioner",
            "target_task": "BACKLOG-108",
            "spec_path": "documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md",
            "precheck_status": "PRE-CHECK PASSED",
            "allowed_files": [
                "backend/services/chat_orchestrator.py",
                "backend/services/contact_manager.py",
            ],
            "max_touched_files": 2,
            "mini_test_plan": [
                "python -m pytest backend/tests/test_contact_manager.py -q",
                "python -m py_compile backend/services/chat_orchestrator.py backend/services/contact_manager.py",
            ],
            "manual_validation_gate": "Codex must verify existing-contact persistence state locally.",
            "delegation_question": "Produce one bounded patch candidate for the existing-contact persistence seam.",
        }

    def test_make_request_body_uses_compact_contract(self) -> None:
        request = runner.make_request_body(self.make_args(), self.make_input_payload())
        user_payload = request["messages"][1]["content"]

        self.assertIn("\"task_contract\"", user_payload)
        self.assertIn("\"validation_bundle\"", user_payload)
        self.assertIn("\"required_fields\": [", user_payload)
        self.assertIn("\"patch_rule\"", user_payload)
        self.assertNotIn("\"field_contract\"", user_payload)

    def test_postprocess_result_payload_fills_missing_optional_fields(self) -> None:
        payload = {
            "status": "PASS",
            "target_task": "BACKLOG-108",
            "patch_text": "diff --git a/backend/services/chat_orchestrator.py b/backend/services/chat_orchestrator.py\n--- a/backend/services/chat_orchestrator.py\n+++ b/backend/services/chat_orchestrator.py\n@@ -1 +1 @@\n-old\n+new\n",
            "notes": "Minimal fixture result.",
        }

        result = runner.postprocess_result_payload(payload, self.make_input_payload())

        self.assertEqual(result["changed_files"], ["backend/services/chat_orchestrator.py"])
        self.assertEqual(
            result["manual_validation_note"],
            "Codex must manually validate this patch locally before task completion.",
        )
        self.assertEqual(
            result["codex_acceptance_rule"],
            "Codex must review and apply or reject locally.",
        )
        self.assertEqual(result["suggested_validation_steps"], self.make_input_payload()["mini_test_plan"])
        self.assertTrue(result["risk_list"])

    def test_validate_result_payload_accepts_postprocessed_minimal_contract(self) -> None:
        payload = runner.postprocess_result_payload(
            {
                "status": "PASS",
                "target_task": "BACKLOG-108",
                "patch_text": "diff --git a/backend/services/chat_orchestrator.py b/backend/services/chat_orchestrator.py\n--- a/backend/services/chat_orchestrator.py\n+++ b/backend/services/chat_orchestrator.py\n@@ -1 +1 @@\n-old\n+new\n",
                "notes": "Minimal fixture result.",
            },
            self.make_input_payload(),
        )

        issues = runner.validate_result_payload(payload, self.make_input_payload())

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
