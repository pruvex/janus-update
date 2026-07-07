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
    / "codex_quickchange_write_apply_runner.py"
)
SPEC = importlib.util.spec_from_file_location("codex_quickchange_write_apply_runner", SCRIPT_PATH)
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


class QuickchangeWriteApplyRunnerTests(unittest.TestCase):
    def create_source_run_dir(self, root: Path, *, include_last_message: bool = True, include_delegated_result: bool = False) -> Path:
        run_dir = root / "accepted-source"
        changed_files = ["backend/services/contact_manager.py"]

        write_json(
            run_dir / "summary.json",
            {
                "status": "PASS",
                "artifact_success": True,
                "git_diff": str(run_dir / "git_diff.patch"),
                "changed_files": str(run_dir / "changed_files.txt"),
            },
        )
        write_json(
            run_dir / "validation_summary.json",
            {
                "workflow_id": "DIRECT-OR-DEEPSEEK-EXECUTION-POST-WRITE-008",
                "validation_result": "PASS",
                "issues": [],
                "changed_files": changed_files,
                "max_touched_files": 4,
                "status": "PASS",
                "accepted_for_codex_patch_review": True,
            },
        )
        write_text(run_dir / "git_diff.patch", "--- a/backend/services/contact_manager.py\n+++ b/backend/services/contact_manager.py\n")
        write_text(run_dir / "changed_files.txt", "backend/services/contact_manager.py\n")
        if include_last_message:
            write_text(run_dir / "last_message.md", "Accepted source summary\n")
        if include_delegated_result:
            write_text(run_dir / "delegated_result.md", "Accepted delegated result\n")
        return run_dir

    def test_accepts_current_normalized_bridge_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir))
            result = runner.validate_accepted_source(run_dir)

        self.assertEqual(result["issues"], [])
        self.assertTrue(result["normalized_tripwires"]["allowlist_ok"])
        self.assertTrue(result["normalized_tripwires"]["touched_file_cap_ok"])
        self.assertTrue(result["normalized_tripwires"]["delete_rename_move_ok"])

    def test_still_rejects_missing_last_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir), include_last_message=False)
            result = runner.validate_accepted_source(run_dir)

        self.assertIn("missing last_message.md", result["issues"])

    def test_accepts_delegated_result_when_last_message_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(
                Path(temp_dir),
                include_last_message=False,
                include_delegated_result=True,
            )
            result = runner.validate_accepted_source(run_dir)

        self.assertEqual(result["issues"], [])


if __name__ == "__main__":
    unittest.main()
