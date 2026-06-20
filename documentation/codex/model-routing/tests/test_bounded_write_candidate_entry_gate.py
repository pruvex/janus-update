from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "codex_bounded_delegation_dispatcher.py"
)
SPEC = importlib.util.spec_from_file_location("codex_bounded_delegation_dispatcher", SCRIPT_PATH)
dispatcher = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = dispatcher
SPEC.loader.exec_module(dispatcher)

FIXTURE_DIR = dispatcher.MODEL_ROUTING_DIR / "structured-action-fixtures"


class BoundedWriteCandidateEntryGateTests(unittest.TestCase):
    def build_args(self, fixture_name: str) -> Namespace:
        return Namespace(
            task_class="execution_write_apply_candidate",
            task_label="TASK-SPEC18.1",
            normal_target_model="5.4",
            execution_input_package=FIXTURE_DIR / fixture_name,
            execution_expected_target_task="TASK-SPEC18.1",
            accepted_source_run_dir=None,
        )

    def invoke(self, fixture_name: str) -> tuple[dict, Path]:
        args = self.build_args(fixture_name)
        workflow_id = f"TEST-{fixture_name.removesuffix('.json').upper()}"
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        original_run_root = dispatcher.RUN_ROOT
        dispatcher.RUN_ROOT = Path(temp_dir.name)
        self.addCleanup(setattr, dispatcher, "RUN_ROOT", original_run_root)
        result = dispatcher.invoke_execution_write_apply_candidate(args, workflow_id)
        run_dir = dispatcher.RUN_ROOT / workflow_id
        return result, run_dir

    def test_accepts_valid_entry_gate_and_builds_reviewable_request(self) -> None:
        result, run_dir = self.invoke("execution_write_candidate_entry_valid_2026-06-15.json")

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(
            result["final_outcome"],
            "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_ACCEPTED_FOR_LATER_PHASES",
        )
        request_path = Path(result["structured_request_path"])
        self.assertTrue(request_path.exists())
        request = json.loads(request_path.read_text(encoding="utf-8"))
        self.assertEqual(request["action_type"], "run_validator")
        self.assertEqual(
            request["action_payload"]["validator_id"],
            "validate_write_candidate_entry_v1",
        )
        self.assertTrue((run_dir / "write_candidate_entry_validation.json").exists())

    def test_rejects_missing_allowlist(self) -> None:
        result, _ = self.invoke("execution_write_candidate_entry_missing_allowlist_2026-06-15.json")

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(
            result["final_outcome"],
            "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
        )
        self.assertIn("missing input field: allowed_files", result["reject_reasons"])

    def test_rejects_missing_touched_file_cap(self) -> None:
        result, _ = self.invoke("execution_write_candidate_entry_missing_touched_cap_2026-06-15.json")

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(
            result["final_outcome"],
            "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
        )
        self.assertIn("missing input field: max_touched_files", result["reject_reasons"])

    def test_rejects_delete_intent(self) -> None:
        result, _ = self.invoke("execution_write_candidate_entry_delete_intent_2026-06-15.json")

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(
            result["final_outcome"],
            "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
        )
        self.assertIn("delete_intent is not allowed in write-candidate entry", result["reject_reasons"])


if __name__ == "__main__":
    unittest.main()
