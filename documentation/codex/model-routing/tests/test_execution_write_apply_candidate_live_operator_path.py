from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


runner = load_module(
    "codex_execution_write_apply_candidate_runner_live_path",
    SCRIPTS_DIR / "codex_execution_write_apply_candidate_runner.py",
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def snapshot_for(path: Path) -> dict:
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


class ExecutionWriteApplyCandidateLiveOperatorPathTests(unittest.TestCase):
    def test_delegated_live_from_accepted_source_writes_pass_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_run_dir = temp_path / "accepted-source"
            run_dir = temp_path / "live-run"
            working_dir = temp_path / "repo"
            changed_files = ["backend/services/contact_book.py"]
            target_file = working_dir / "backend/services/contact_book.py"
            write_text(target_file, "old\n")

            write_json(
                source_run_dir / "input_package.json",
                {
                    "precheck_status": "PRE-CHECK PASSED",
                    "allowed_files": changed_files,
                    "max_touched_files": 1,
                },
            )
            write_json(
                source_run_dir / "validation_summary.json",
                {
                    "status": "PASS",
                    "accepted_for_codex_patch_review": True,
                    "changed_files": changed_files,
                    "source_file_snapshots": {
                        "backend/services/contact_book.py": snapshot_for(target_file),
                    },
                },
            )
            write_json(
                source_run_dir / "operator_summary.json",
                {
                    "validation_result": "PASS",
                    "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
                },
            )
            write_json(
                source_run_dir / "summary.json",
                {
                    "status": "PASS",
                    "git_diff": str(source_run_dir / "git_diff.patch"),
                    "changed_files": str(source_run_dir / "changed_files.txt"),
                },
            )
            write_text(source_run_dir / "delegated_result.md", "bounded result\n")
            write_text(
                source_run_dir / "git_diff.patch",
                "--- a/backend/services/contact_book.py\n+++ b/backend/services/contact_book.py\n@@\n-old\n+new\n",
            )
            write_text(source_run_dir / "changed_files.txt", "backend/services/contact_book.py\n")
            write_text(source_run_dir / "stdout.log", "ok\n")
            write_text(source_run_dir / "stderr.log", "")
            write_text(source_run_dir / "exit_code.txt", "0\n")

            original_invoke = runner.invoke_local_apply_run
            self.addCleanup(setattr, runner, "invoke_local_apply_run", original_invoke)

            def fake_invoke_local_apply_run(**kwargs):
                apply_dir = kwargs["run_directory"]
                apply_dir.mkdir(parents=True, exist_ok=True)
                write_json(apply_dir / "summary.json", {"status": "PASS", "artifact_success": False})
                write_json(
                    apply_dir / "validation_summary.json",
                    {
                        "allowlist_ok": True,
                        "touched_file_cap_ok": True,
                        "delete_rename_move_ok": True,
                        "touched_files": changed_files[0],
                    },
                )
                write_text(apply_dir / "git_diff.patch", "diff\n")
                write_text(apply_dir / "pre_run_status.txt", " M backend/services/contact_manager.py\n")
                write_text(apply_dir / "post_run_status.txt", " M backend/services/contact_manager.py\n")
                write_text(apply_dir / "last_message.md", "Apply succeeded: yes.\n")

                class Completed:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return Completed()

            runner.invoke_local_apply_run = fake_invoke_local_apply_run

            exit_code, result = runner.delegated_live_from_accepted_source(
                run_dir=run_dir,
                workflow_id="EXEC-WRITE-LIVE-001",
                task_label="BACKLOG-108 live write pilot",
                normal_target_model="5.4 medium",
                working_directory=working_dir,
                source_run_dir=source_run_dir,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["validation_result"], "PASS")
            self.assertEqual(
                result["final_outcome"],
                "EXECUTION_WRITE_APPLY_LIVE_WRITE_READY_FOR_CODEX_ACCEPT_REJECT",
            )
            prompt_text = (run_dir / "apply_instructions.md").read_text(encoding="utf-8")
            self.assertIn("Apply the exact accepted patch", prompt_text)
            self.assertIn("backend/services/contact_book.py", prompt_text)
            live_validation = json.loads((run_dir / "live_validation_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(live_validation["issues"], [])
            self.assertEqual(live_validation["touched_files"], changed_files)
            self.assertTrue(live_validation["apply_succeeded"])

    def test_delegated_live_from_accepted_source_rejects_no_delta_apply_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_run_dir = temp_path / "accepted-source"
            run_dir = temp_path / "live-run"
            working_dir = temp_path / "repo"
            changed_files = ["backend/services/contact_manager.py"]
            target_file = working_dir / "backend/services/contact_manager.py"
            write_text(target_file, "old\n")

            write_json(
                source_run_dir / "input_package.json",
                {
                    "precheck_status": "PRE-CHECK PASSED",
                    "allowed_files": changed_files,
                    "max_touched_files": 1,
                },
            )
            write_json(
                source_run_dir / "validation_summary.json",
                {
                    "status": "PASS",
                    "accepted_for_codex_patch_review": True,
                    "changed_files": changed_files,
                    "source_file_snapshots": {
                        "backend/services/contact_manager.py": snapshot_for(target_file),
                    },
                },
            )
            write_json(
                source_run_dir / "operator_summary.json",
                {
                    "validation_result": "PASS",
                    "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
                },
            )
            write_json(
                source_run_dir / "summary.json",
                {
                    "status": "PASS",
                    "git_diff": str(source_run_dir / "git_diff.patch"),
                    "changed_files": str(source_run_dir / "changed_files.txt"),
                },
            )
            write_text(source_run_dir / "delegated_result.md", "bounded result\n")
            write_text(
                source_run_dir / "git_diff.patch",
                "--- a/backend/services/contact_manager.py\n+++ b/backend/services/contact_manager.py\n@@\n-old\n+new\n",
            )
            write_text(source_run_dir / "changed_files.txt", "backend/services/contact_manager.py\n")
            write_text(source_run_dir / "stdout.log", "ok\n")
            write_text(source_run_dir / "stderr.log", "")
            write_text(source_run_dir / "exit_code.txt", "0\n")

            original_invoke = runner.invoke_local_apply_run
            self.addCleanup(setattr, runner, "invoke_local_apply_run", original_invoke)

            def fake_invoke_local_apply_run(**kwargs):
                apply_dir = kwargs["run_directory"]
                apply_dir.mkdir(parents=True, exist_ok=True)
                write_json(apply_dir / "summary.json", {"status": "PASS", "artifact_success": False})
                write_json(
                    apply_dir / "validation_summary.json",
                    {
                        "allowlist_ok": True,
                        "touched_file_cap_ok": True,
                        "delete_rename_move_ok": True,
                        "touched_files": changed_files,
                    },
                )
                write_text(apply_dir / "git_diff.patch", "preexisting diff\n")
                write_text(apply_dir / "pre_run_status.txt", " M backend/services/contact_manager.py\n")
                write_text(apply_dir / "post_run_status.txt", " M backend/services/contact_manager.py\n")
                write_text(apply_dir / "last_message.md", "Apply succeeded: no.\n")

                class Completed:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return Completed()

            runner.invoke_local_apply_run = fake_invoke_local_apply_run

            exit_code, result = runner.delegated_live_from_accepted_source(
                run_dir=run_dir,
                workflow_id="EXEC-WRITE-LIVE-002",
                task_label="BACKLOG-108 live write pilot",
                normal_target_model="5.4 medium",
                working_directory=working_dir,
                source_run_dir=source_run_dir,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(result["validation_result"], "FAIL")
            self.assertEqual(
                result["final_outcome"],
                "EXECUTION_WRITE_APPLY_LIVE_WRITE_REJECT_AND_FALLBACK",
            )
            live_validation = json.loads((run_dir / "live_validation_summary.json").read_text(encoding="utf-8"))
            self.assertIn("local apply artifact_success is not true", live_validation["issues"])
            self.assertIn("local apply pre_run_status and post_run_status are identical", live_validation["issues"])
            self.assertIn("local apply last_message reports apply failed", live_validation["issues"])

    def test_delegated_live_from_accepted_source_rejects_working_tree_drift_before_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_run_dir = temp_path / "accepted-source"
            run_dir = temp_path / "live-run"
            working_dir = temp_path / "repo"
            changed_files = ["backend/services/contact_manager.py"]
            target_file = working_dir / "backend/services/contact_manager.py"
            write_text(target_file, "current-shape\n")

            write_json(
                source_run_dir / "input_package.json",
                {
                    "precheck_status": "PRE-CHECK PASSED",
                    "allowed_files": changed_files,
                    "max_touched_files": 1,
                },
            )
            write_json(
                source_run_dir / "validation_summary.json",
                {
                    "status": "PASS",
                    "accepted_for_codex_patch_review": True,
                    "changed_files": changed_files,
                    "source_file_snapshots": {
                        "backend/services/contact_manager.py": {
                            "sha256": hashlib.sha256(b"older-shape\n").hexdigest(),
                            "bytes": len(b"older-shape\n"),
                        },
                    },
                },
            )
            write_json(
                source_run_dir / "operator_summary.json",
                {
                    "validation_result": "PASS",
                    "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
                },
            )
            write_json(
                source_run_dir / "summary.json",
                {
                    "status": "PASS",
                    "git_diff": str(source_run_dir / "git_diff.patch"),
                    "changed_files": str(source_run_dir / "changed_files.txt"),
                },
            )
            write_text(source_run_dir / "delegated_result.md", "bounded result\n")
            write_text(
                source_run_dir / "git_diff.patch",
                "--- a/backend/services/contact_manager.py\n+++ b/backend/services/contact_manager.py\n@@\n-old\n+new\n",
            )
            write_text(source_run_dir / "changed_files.txt", "backend/services/contact_manager.py\n")
            write_text(source_run_dir / "stdout.log", "ok\n")
            write_text(source_run_dir / "stderr.log", "")
            write_text(source_run_dir / "exit_code.txt", "0\n")

            original_invoke = runner.invoke_local_apply_run
            self.addCleanup(setattr, runner, "invoke_local_apply_run", original_invoke)

            def fail_if_called(**kwargs):
                raise AssertionError("local apply should not run when source snapshots already drifted")

            runner.invoke_local_apply_run = fail_if_called

            exit_code, result = runner.delegated_live_from_accepted_source(
                run_dir=run_dir,
                workflow_id="EXEC-WRITE-LIVE-003",
                task_label="BACKLOG-108 live write pilot",
                normal_target_model="5.4 medium",
                working_directory=working_dir,
                source_run_dir=source_run_dir,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(result["validation_result"], "FAIL")
            self.assertEqual(result["final_outcome"], "INVALID_ACCEPTED_SOURCE_PACKAGE")
            source_validation = json.loads((run_dir / "source_validation.json").read_text(encoding="utf-8"))
            self.assertIn(
                "working tree drift detected for source snapshot: backend/services/contact_manager.py",
                source_validation["issues"],
            )


if __name__ == "__main__":
    unittest.main()
