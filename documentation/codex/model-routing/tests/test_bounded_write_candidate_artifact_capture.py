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


class BoundedWriteCandidateArtifactCaptureTests(unittest.TestCase):
    def create_source_run_dir(
        self,
        root: Path,
        *,
        include_diff: bool = True,
        include_changed_files: bool = True,
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
        write_json(
            run_dir / "validation_summary.json",
            {
                "accepted_for_codex_patch_review": True,
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
        if include_diff:
            write_text(
                run_dir / "git_diff.patch",
                "--- a/documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py\n"
                "+++ b/documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py\n",
            )
        if include_changed_files:
            write_text(
                run_dir / "changed_files.txt",
                "documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py\n",
            )
        return run_dir

    def test_accepts_complete_artifact_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir))
            result = runner.validate_accepted_source(run_dir)

        self.assertEqual(result["issues"], [])
        self.assertEqual(
            result["changed_files"],
            ["documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py"],
        )

    def test_rejects_missing_diff_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir), include_diff=False)
            result = runner.validate_accepted_source(run_dir)

        self.assertIn("missing git_diff.patch", result["issues"])

    def test_rejects_missing_changed_files_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir), include_changed_files=False)
            result = runner.validate_accepted_source(run_dir)

        self.assertIn("missing changed_files.txt", result["issues"])

    def test_rejects_changed_files_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = self.create_source_run_dir(Path(temp_dir))
            write_text(run_dir / "changed_files.txt", "documentation/codex/model-routing/scripts/other_file.py\n")
            result = runner.validate_accepted_source(run_dir)

        self.assertIn("changed_files.txt does not match validation_summary changed_files", result["issues"])


if __name__ == "__main__":
    unittest.main()
