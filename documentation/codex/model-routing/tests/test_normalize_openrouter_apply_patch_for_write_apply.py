from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

BRIDGE_SPEC = importlib.util.spec_from_file_location(
    "normalize_openrouter_apply_patch_for_write_apply",
    SCRIPTS_DIR / "normalize_openrouter_apply_patch_for_write_apply.py",
)
bridge = importlib.util.module_from_spec(BRIDGE_SPEC)
assert BRIDGE_SPEC and BRIDGE_SPEC.loader
sys.modules[BRIDGE_SPEC.name] = bridge
BRIDGE_SPEC.loader.exec_module(bridge)

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_execution_write_apply_candidate_runner_for_openrouter_bridge",
    SCRIPTS_DIR / "codex_execution_write_apply_candidate_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class NormalizeOpenRouterApplyPatchForWriteApplyTests(unittest.TestCase):
    def create_source_run_dir(
        self,
        root: Path,
        *,
        calls: list[dict],
        changed_files: list[str],
    ) -> Path:
        run_dir = root / "accepted-openrouter-source"
        write_json(
            run_dir / "input_package.json",
            {
                "precheck_status": "PRE-CHECK PASSED",
                "allowed_files": changed_files,
                "max_touched_files": len(changed_files),
            },
        )
        write_json(
            run_dir / "validation_summary.json",
            {
                "workflow_id": "WF-QWEN-EXEC-001",
                "validation_result": "PASS",
                "touched_files": changed_files,
            },
        )
        write_json(
            run_dir / "operator_summary.json",
            {
                "workflow_id": "WF-QWEN-EXEC-001",
                "validation_result": "PASS",
                "final_outcome": "QWEN_RESPONSES_EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
            },
        )
        write_json(run_dir / "apply_patch_calls.json", {"calls": calls})
        write_text(run_dir / "stdout.log", "ok\n")
        write_text(run_dir / "stderr.log", "")
        write_text(run_dir / "exit_code.txt", "0\n")
        return run_dir

    def test_bridge_normalizes_openrouter_operation_diff_and_write_apply_runner_accepts_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            working_dir = root / "repo"
            target = working_dir / "backend/services/contact_manager.py"
            write_text(target, "def label():\n    return 'old'\n")
            changed_files = ["backend/services/contact_manager.py"]
            source_run_dir = self.create_source_run_dir(
                root,
                changed_files=changed_files,
                calls=[
                    {
                        "id": "st_1",
                        "type": "openrouter:apply_patch",
                        "status": "completed",
                        "operation_type": "update_file",
                        "path": "backend/services/contact_manager.py",
                        "diff": "@@ -1,2 +1,2 @@\n def label():\n-    return 'old'\n+    return 'new'\n",
                    }
                ],
            )
            output_dir = root / "normalized-source"

            summary = bridge.build_normalized_package(
                source_run_dir,
                output_dir,
                working_directory=working_dir,
            )

            self.assertEqual(summary["status"], "PASS")
            validation = runner.validate_accepted_source(
                output_dir,
                working_directory=working_dir,
                require_source_snapshots=True,
            )
            self.assertEqual(validation["issues"], [])
            self.assertEqual(validation["changed_files"], changed_files)
            diff_text = (output_dir / "git_diff.patch").read_text(encoding="utf-8")
            self.assertIn("--- a/backend/services/contact_manager.py", diff_text)
            self.assertIn("+++ b/backend/services/contact_manager.py", diff_text)
            self.assertIn("-    return 'old'", diff_text)
            self.assertIn("+    return 'new'", diff_text)

            apply_dir = root / "apply-run"
            completed = runner.invoke_local_apply_run(
                run_directory=apply_dir,
                working_directory=working_dir,
                source_diff_path=output_dir / "git_diff.patch",
                editable_paths=changed_files,
                max_touched_files=1,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "def label():\n    return 'new'\n")

    def test_bridge_normalizes_apply_patch_call_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            working_dir = root / "repo"
            target = working_dir / "backend/services/contact_manager.py"
            write_text(target, "old\n")
            changed_files = ["backend/services/contact_manager.py"]
            source_run_dir = self.create_source_run_dir(
                root,
                changed_files=changed_files,
                calls=[
                    {
                        "id": "apc_1",
                        "type": "apply_patch_call",
                        "status": "completed",
                        "name": "openrouter:apply_patch",
                        "patch": (
                            "*** Begin Patch\n"
                            "*** Update File: backend/services/contact_manager.py\n"
                            "@@\n"
                            "-old\n"
                            "+new\n"
                            "*** End Patch"
                        ),
                    }
                ],
            )
            output_dir = root / "normalized-source"

            summary = bridge.build_normalized_package(
                source_run_dir,
                output_dir,
                working_directory=working_dir,
            )

            self.assertEqual(summary["status"], "PASS")
            diff_text = (output_dir / "git_diff.patch").read_text(encoding="utf-8")
            self.assertIn("-old", diff_text)
            self.assertIn("+new", diff_text)

    def test_bridge_rejects_changed_files_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            working_dir = root / "repo"
            write_text(working_dir / "backend/services/contact_manager.py", "old\n")
            source_run_dir = self.create_source_run_dir(
                root,
                changed_files=["backend/services/contact_manager.py"],
                calls=[
                    {
                        "id": "st_1",
                        "type": "openrouter:apply_patch",
                        "status": "completed",
                        "operation_type": "update_file",
                        "path": "backend/services/contact_manager.py",
                        "diff": "@@ -1 +1 @@\n-old\n+new\n",
                    }
                ],
            )
            validation_path = source_run_dir / "validation_summary.json"
            payload = json.loads(validation_path.read_text(encoding="utf-8"))
            payload["touched_files"] = ["backend/services/other.py"]
            write_json(validation_path, payload)

            with self.assertRaises(SystemExit) as ctx:
                bridge.build_normalized_package(
                    source_run_dir,
                    root / "normalized-source",
                    working_directory=working_dir,
                )

            self.assertIn("normalized changed files do not match", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
