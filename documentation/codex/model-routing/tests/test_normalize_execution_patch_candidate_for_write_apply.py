from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

BRIDGE_SPEC = importlib.util.spec_from_file_location(
    "normalize_execution_patch_candidate_for_write_apply",
    SCRIPTS_DIR / "normalize_execution_patch_candidate_for_write_apply.py",
)
bridge = importlib.util.module_from_spec(BRIDGE_SPEC)
assert BRIDGE_SPEC and BRIDGE_SPEC.loader
sys.modules[BRIDGE_SPEC.name] = bridge
BRIDGE_SPEC.loader.exec_module(bridge)

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "codex_execution_write_apply_candidate_runner",
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


class NormalizeExecutionPatchCandidateForWriteApplyTests(unittest.TestCase):
    def create_source_run_dir(self, root: Path) -> Path:
        run_dir = root / "accepted-execution-source"
        write_json(
            run_dir / "input_package.json",
            {
                "precheck_status": "PRE-CHECK PASSED",
                "allowed_files": [
                    "backend/services/contact_manager.py",
                    "backend/tools/memory_tools.py",
                ],
                "max_touched_files": 8,
            },
        )
        write_json(
            run_dir / "validation_summary.json",
            {
                "workflow_id": "WF-EXEC-001",
                "validation_result": "PASS",
                "changed_files": [
                    "backend/services/contact_manager.py",
                    "backend/tools/memory_tools.py",
                ],
            },
        )
        write_json(
            run_dir / "operator_summary.json",
            {
                "workflow_id": "WF-EXEC-001",
                "validation_result": "PASS",
                "final_outcome": "DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW",
            },
        )
        write_json(
            run_dir / "patch_candidate_result.json",
            {
                "status": "PASS",
                "patch_text": (
                    "--- a/backend/services/contact_manager.py\n"
                    "+++ b/backend/services/contact_manager.py\n"
                    "@@ -1 +1 @@\n"
                    "-old\n"
                    "+new\n"
                ),
            },
        )
        write_text(run_dir / "stdout.log", "ok\n")
        write_text(run_dir / "stderr.log", "")
        write_text(run_dir / "exit_code.txt", "0\n")
        return run_dir

    def test_bridge_creates_write_apply_source_package_that_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_run_dir = self.create_source_run_dir(root)
            output_dir = root / "normalized-source"

            summary = bridge.build_normalized_package(source_run_dir, output_dir)
            self.assertEqual(summary["status"], "PASS")

            validation = runner.validate_accepted_source(output_dir)
            self.assertEqual(validation["issues"], [])
            self.assertEqual(
                validation["changed_files"],
                ["backend/services/contact_manager.py", "backend/tools/memory_tools.py"],
            )


if __name__ == "__main__":
    unittest.main()
