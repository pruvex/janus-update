from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "codex_execution_write_apply_candidate_runner.py"
)
SPEC = importlib.util.spec_from_file_location("codex_execution_write_apply_candidate_runner", SCRIPT_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class BoundedWriteCandidateValidationAcceptanceTests(unittest.TestCase):
    def create_source_run_dir(
        self,
        root: Path,
        *,
        include_validation_summary: bool = True,
        validation_status: str = "PASS",
    ) -> Path:
        run_dir = root / "accepted-source"
        allowed_files = [
            "documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py",
        ]
        changed_files = list(allowed_files)

        write_json(
            run_dir / "input_package.json",
            {
                "precheck_status": "PRE-CHECK PASSED",
                "allowed_files": allowed_files,
                "max_touched_files": 1,
            },
        )
        if include_validation_summary:
            write_json(
                run_dir / "validation_summary.json",
                {
                    "status": validation_status,
                    "accepted_for_codex_patch_review": validation_status == "PASS",
                    "changed_files": changed_files,
                },
            )
        write_json(
            run_dir / "operator_summary.json",
            {
                "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
                "validation_result": "PASS",
            },
        )
        write_json(
            run_dir / "summary.json",
            {
                "status": "PASS",
                "git_diff": str(run_dir / "git_diff.patch"),
                "changed_files": str(run_dir / "changed_files.txt"),
            },
        )
        write_text(run_dir / "delegated_result.md", "PATCH_TEXT\n--- a/x\n+++ b/x\n")
        write_text(run_dir / "stdout.log", "ok\n")
        write_text(run_dir / "stderr.log", "")
        write_text(run_dir / "exit_code.txt", "0\n")
        write_text(
            run_dir / "git_diff.patch",
            "--- a/documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py\n"
            "+++ b/documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py\n",
        )
        write_text(
            run_dir / "changed_files.txt",
            "documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py\n",
        )
        return run_dir

    def test_rejects_missing_validation_summary_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir), include_validation_summary=False)
            result = runner.validate_accepted_source(run_dir)

        self.assertIn("missing validation_summary.json", result["issues"])

    def test_rejects_failed_local_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir), validation_status="FAIL")
            result = runner.validate_accepted_source(run_dir)

        self.assertIn("validation_summary status is not PASS", result["issues"])
        self.assertIn("accepted_for_codex_patch_review is not true", result["issues"])

    def test_normalizes_codex_owned_final_outcome_for_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_run_dir = self.create_source_run_dir(Path(temp_dir))
            workflow_id = "EXEC-WRITE-VALIDATION-PASS-001"
            original_run_root = runner.RUN_ROOT
            runner.RUN_ROOT = Path(temp_dir) / "write-apply-runs"
            try:
                exit_code = runner.main_with_args(
                    [
                        "--task-label",
                        "TASK-SPEC18.3",
                        "--normal-target-model",
                        "5.4",
                        "--operator-choice",
                        "delegated",
                        "--workflow-id",
                        workflow_id,
                        "--accepted-source-run-dir",
                        str(source_run_dir),
                    ]
                )
                self.assertEqual(exit_code, 0)
                operator_summary = json.loads(
                    (runner.RUN_ROOT / workflow_id / "operator_summary.json").read_text(encoding="utf-8")
                )
            finally:
                runner.RUN_ROOT = original_run_root

        self.assertEqual(operator_summary["validation_result"], "PASS")
        self.assertEqual(
            operator_summary["final_outcome"],
            "EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_CODEX_ACCEPT_REJECT",
        )
        self.assertIn("Codex still owns the explicit accept-or-reject decision", operator_summary["operator_message"])


if __name__ == "__main__":
    unittest.main()
