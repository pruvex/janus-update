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
    CURRENT_SHAPE_INPUT_PACKAGE = (
        Path(__file__).resolve().parents[1]
        / "execution-review-fixtures"
        / "backlog_108_execution_patch_candidate_input_package_current_shape_2026-06-24.json"
    )
    CURRENT_SHAPE_FIXTURE_RESPONSE = (
        Path(__file__).resolve().parents[1]
        / "execution-review-fixtures"
        / "direct_or_execution_patch_candidate_current_shape_fixture_response_2026-06-24.json"
    )

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
            "current_seam_context": "Current seam is function-oriented around stage_contact_update_from_memory in contact_manager and handle_memory_write in memory_tools.",
            "signature_context": "_apply_contact_memory_update_directly(db_session: Session, *, target_contact: Any, proposal_payload: Dict[str, Any]) -> Dict[str, Any]; stage_contact_update_from_memory(db_session: Session, *, memory: Any, chat_id: Optional[int] = None) -> Dict[str, Any]; handle_memory_write(params: Dict[str, Any], db: Session, chat_id: int, source_skill: str = 'system.memory_write', original_user_text: Optional[str] = None) -> ToolResultV1",
            "call_shape_examples": [
                "contact_manager.stage_contact_update_from_memory(db, memory=saved, chat_id=chat_id)",
                "_apply_contact_memory_update_directly(db_session, target_contact=target_contact, proposal_payload=proposal_payload)",
            ],
            "exact_code_context_blocks": [
                "backend/services/contact_manager.py::_apply_contact_memory_update_directly\\ndef _apply_contact_memory_update_directly(\\n    db_session: Session,\\n    *,\\n    target_contact: Any,\\n    proposal_payload: Dict[str, Any],\\n) -> Dict[str, Any]:\\n    updates = dict(proposal_payload)\\n    updates[\"proposal_status\"] = \"confirmed\"",
                "backend/tools/memory_tools.py::handle_memory_write\\ncontact_proposal_result = contact_manager.stage_contact_update_from_memory(\\n    db,\\n    memory=saved,\\n    chat_id=chat_id,\\n)",
            ],
            "forbidden_anchors": [
                "class ContactManager",
                "get_or_resolve_contact",
                "persist_contact_updates",
                "store_memory_facts",
            ],
            "required_current_anchors": [
                "stage_contact_update_from_memory",
                "handle_memory_write",
                "memory_write_tool",
            ],
        }

    def test_make_request_body_uses_compact_contract(self) -> None:
        request = runner.make_request_body(self.make_args(), self.make_input_payload())
        user_payload = request["messages"][1]["content"]
        system_prompt = request["messages"][0]["content"]
        response_required = request["response_format"]["json_schema"]["schema"]["required"]

        self.assertIn("return BLOCKED with empty patch_text", system_prompt)
        self.assertIn("\"task_contract\"", user_payload)
        self.assertIn("\"validation_bundle\"", user_payload)
        self.assertIn("\"current_seam_context\"", user_payload)
        self.assertIn("\"signature_context\"", user_payload)
        self.assertIn("\"call_shape_examples\"", user_payload)
        self.assertIn("\"exact_code_context_blocks\"", user_payload)
        self.assertIn("\"forbidden_anchors\"", user_payload)
        self.assertIn("\"required_current_anchors\"", user_payload)
        self.assertIn("\"anchor_rule\"", user_payload)
        self.assertIn("\"newline_rule\"", user_payload)
        self.assertIn("\"signature_rule\"", user_payload)
        self.assertIn("\"context_rule\"", user_payload)
        self.assertIn("\"blocked_rule\"", user_payload)
        self.assertIn("\"placeholder_rule\"", user_payload)
        self.assertIn("\"required_fields\": [", user_payload)
        self.assertIn("\"patch_rule\"", user_payload)
        self.assertIn("changed_files", response_required)
        self.assertIn("suggested_validation_steps", response_required)
        self.assertIn("manual_validation_note", response_required)
        self.assertIn("codex_acceptance_rule", response_required)
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

    def test_postprocess_result_payload_normalizes_blocked_status_when_real_patch_exists(self) -> None:
        payload = {
            "status": "BLOCKED",
            "target_task": "BACKLOG-108",
            "patch_text": (
                "diff --git a/backend/services/chat_orchestrator.py b/backend/services/chat_orchestrator.py\n"
                "--- a/backend/services/chat_orchestrator.py\n"
                "+++ b/backend/services/chat_orchestrator.py\n"
                "@@ -1 +1 @@\n"
                "-from __future__ import annotations\n"
                "+from __future__ import annotations\n"
            ),
            "changed_files": ["backend/services/chat_orchestrator.py"],
            "notes": "Model mislabeled a real patch as BLOCKED.",
        }

        result = runner.postprocess_result_payload(payload, self.make_input_payload())

        self.assertEqual(result["status"], "WEAK_SIGNAL")

    def test_validate_result_payload_accepts_postprocessed_applicable_contract(self) -> None:
        current_lines = runner.resolve_repo_path("backend/services/chat_orchestrator.py").read_text(
            encoding="utf-8-sig"
        ).splitlines()
        old_line = current_lines[0]
        payload = runner.postprocess_result_payload(
            {
                "status": "PASS",
                "target_task": "BACKLOG-108",
                "patch_text": (
                    "diff --git a/backend/services/chat_orchestrator.py b/backend/services/chat_orchestrator.py\n"
                    "--- a/backend/services/chat_orchestrator.py\n"
                    "+++ b/backend/services/chat_orchestrator.py\n"
                    "@@ -1 +1 @@\n"
                    f"-{old_line}\n"
                    f"+{old_line}\n"
                ),
                "notes": "Minimal applicable fixture result.",
            },
            self.make_input_payload(),
        )

        issues = runner.validate_result_payload(payload, self.make_input_payload())

        self.assertEqual(issues, [])

    def test_validate_result_payload_accepts_bounded_blocked_without_patch(self) -> None:
        payload = runner.postprocess_result_payload(
            {
                "status": "BLOCKED",
                "target_task": "BACKLOG-108",
                "patch_text": "",
                "changed_files": [],
                "risk_list": ["Bounded no-patch assessment only."],
                "suggested_validation_steps": self.make_input_payload()["mini_test_plan"],
                "manual_validation_note": "Codex must manually validate this patch locally before task completion.",
                "codex_acceptance_rule": "Codex must review and apply or reject locally.",
                "notes": "No honest patch candidate could be derived inside the allowlist.",
            },
            self.make_input_payload(),
        )

        issues = runner.validate_result_payload(payload, self.make_input_payload())

        self.assertEqual(issues, [])

    def test_validate_result_payload_rejects_placeholder_patch_markers(self) -> None:
        payload = runner.postprocess_result_payload(
            {
                "status": "PASS",
                "target_task": "BACKLOG-108",
                "patch_text": (
                    "--- a/backend/services/chat_orchestrator.py\n"
                    "+++ b/backend/services/chat_orchestrator.py\n"
                    "@@ -1,2 +1,2 @@\n"
                    "-# existing header\n"
                    "+# existing header\n"
                ),
                "notes": "Placeholder diff should fail.",
            },
            self.make_input_payload(),
        )

        issues = runner.validate_result_payload(payload, self.make_input_payload())

        self.assertIn("placeholder patch marker detected: # existing header", issues)

    def test_validate_result_payload_rejects_non_applicable_hunk_context(self) -> None:
        payload = runner.postprocess_result_payload(
            {
                "status": "PASS",
                "target_task": "BACKLOG-108",
                "patch_text": (
                    "--- a/backend/services/chat_orchestrator.py\n"
                    "+++ b/backend/services/chat_orchestrator.py\n"
                    "@@ -42,3 +42,4 @@\n"
                    "-def invented_function_signature(path_id, task_class, estimated_or_cost):\n"
                    "+def invented_function_signature(path_id, task_class, estimated_or_cost, strict_mode=False):\n"
                    "     ...\n"
                    "     return result\n"
                ),
                "notes": "Diff does not match real file context.",
            },
            self.make_input_payload(),
        )

        issues = runner.validate_result_payload(payload, self.make_input_payload())

        self.assertTrue(any("hunk context not found in current file" in issue for issue in issues))

    def test_validate_input_package_accepts_optional_anchor_guidance_fields(self) -> None:
        issues = runner.validate_input_package(self.make_input_payload())

        self.assertEqual(issues, [])

    def test_current_shape_fixture_now_fails_closed_when_repo_shape_drifted(self) -> None:
        input_payload = runner.load_json(self.CURRENT_SHAPE_INPUT_PACKAGE)
        fixture_response = runner.load_json(self.CURRENT_SHAPE_FIXTURE_RESPONSE)

        content = runner.content_from_response(fixture_response)
        parsed = runner.parse_json_from_text(content)
        normalized = runner.postprocess_result_payload(parsed, input_payload)
        issues = runner.validate_result_payload(normalized, input_payload)

        self.assertEqual(normalized["changed_files"], ["backend/services/contact_manager.py"])
        self.assertTrue(any("hunk context not found in current file" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
