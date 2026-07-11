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
    / "codex_structured_action_executor.py"
)
SPEC = importlib.util.spec_from_file_location("codex_structured_action_executor", SCRIPT_PATH)
executor = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = executor
SPEC.loader.exec_module(executor)


FIXTURE_DIR = executor.MODEL_ROUTING_DIR / "structured-action-fixtures"


class StructuredActionExecutorTests(unittest.TestCase):
    def test_handle_valid_draft_markdown_request(self) -> None:
        request = executor.load_json(FIXTURE_DIR / "delegated_request_draft_markdown_2026-06-14.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            result = executor.handle_request(request, run_dir)

            self.assertEqual(result.executor_status, "PASS")
            self.assertEqual(result.action_summary["format"], "markdown")
            self.assertTrue((run_dir / "draft_output.md").exists())

    def test_rejects_later_slice_action_type(self) -> None:
        request = executor.load_json(FIXTURE_DIR / "delegated_request_invalid_action_type_2026-06-15.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            with self.assertRaises(executor.RequestValidationError) as ctx:
                executor.handle_request(request, run_dir)

        self.assertIn("Unsupported generator_id in TASK-SPEC17.2 executor slice", str(ctx.exception))
        self.assertIn("unknown_generator_v1", str(ctx.exception))

    def test_runs_bound_compile_testspec_generator(self) -> None:
        request = executor.load_json(FIXTURE_DIR / "delegated_request_compile_testspec_to_testplan_2026-06-15.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            result = executor.handle_request(request, run_dir)

            self.assertEqual(result.executor_status, "PASS")
            self.assertEqual(result.action_summary["generator_id"], "compile_testspec_to_testplan_v1")
            output_artifacts = result.action_summary["output_artifacts"]
            self.assertEqual(len(output_artifacts), 2)
            self.assertTrue((run_dir / "stdout.log").exists())
            self.assertTrue((run_dir / "stderr.log").exists())
            self.assertTrue((run_dir / "exit_code.txt").exists())

    def test_runs_bound_compile_testspec_generator_with_skill2_handover(self) -> None:
        request = executor.load_json(FIXTURE_DIR / "delegated_request_compile_testspec_to_testplan_2026-06-15.json")
        test_run_id = "TEST-RUN-2099-12-31-996"
        output_paths = [
            Path("documentation/test-runs") / f"{test_run_id}_plan.json",
            Path("documentation/test-runs") / f"{test_run_id}_generated.spec.js",
            Path("documentation/test-runs") / f"{test_run_id}_skill2_handover.txt",
        ]
        request["action_payload"]["inputs"]["test_run_id"] = test_run_id
        request["action_payload"]["inputs"]["output_dir"] = "documentation/test-runs"
        request["action_payload"]["declared_output_artifacts"] = [
            str(path).replace("\\", "/")
            for path in output_paths
        ]

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                run_dir = Path(temp_dir)
                result = executor.handle_request(request, run_dir)

                self.assertEqual(result.executor_status, "PASS")
                self.assertEqual(result.action_summary["generator_id"], "compile_testspec_to_testplan_v1")
                output_artifacts = result.action_summary["output_artifacts"]
                self.assertEqual(len(output_artifacts), 3)
                self.assertTrue(any(path.endswith("_skill2_handover.txt") for path in output_artifacts))
        finally:
            for path in output_paths:
                absolute_path = executor.REPO_ROOT / path
                if absolute_path.exists():
                    absolute_path.unlink()

    def test_runs_bound_validate_runner_validator(self) -> None:
        request = executor.load_json(FIXTURE_DIR / "delegated_request_validate_runner_2026-06-14.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            result = executor.handle_request(request, run_dir)

            self.assertEqual(result.executor_status, "PASS")
            self.assertEqual(result.action_summary["validator_id"], "validate_runner_v1")
            self.assertTrue((run_dir / "stdout.log").exists())
            self.assertTrue((run_dir / "stderr.log").exists())
            self.assertTrue((run_dir / "exit_code.txt").exists())

    def test_cli_writes_reviewable_failure_artifacts_for_invalid_action_type(self) -> None:
        request_path = FIXTURE_DIR / "delegated_request_invalid_action_type_2026-06-15.json"

        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code = executor.main_with_args(
                [
                    "--request-json",
                    str(request_path),
                    "--run-root",
                    temp_dir,
                ]
            )
            self.assertEqual(exit_code, 1)

            workflow_dir = Path(temp_dir) / "STRUCTURED-ACTION-UNKNOWN-GENERATOR-001"
            run_dirs = [path for path in workflow_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]

            validation_result = json.loads((run_dir / "validation_result.json").read_text(encoding="utf-8"))
            summary = json.loads((run_dir / "executor_summary.json").read_text(encoding="utf-8"))

            self.assertEqual(validation_result["status"], "FAIL")
            self.assertEqual(summary["executor_status"], "FAILED")
            self.assertEqual(summary["schema_validation"], "PASS")
            self.assertIn("TASK-SPEC17.2 executor slice", summary["detail"])

    def test_cli_writes_reviewable_failure_artifacts_for_validator_failure(self) -> None:
        request_path = FIXTURE_DIR / "delegated_request_validate_runner_failure_2026-06-15.json"

        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code = executor.main_with_args(
                [
                    "--request-json",
                    str(request_path),
                    "--run-root",
                    temp_dir,
                ]
            )
            self.assertEqual(exit_code, 1)

            workflow_dir = Path(temp_dir) / "STRUCTURED-ACTION-VALIDATOR-FAIL-001"
            run_dirs = [path for path in workflow_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]

            validation_result = json.loads((run_dir / "validation_result.json").read_text(encoding="utf-8"))
            summary = json.loads((run_dir / "executor_summary.json").read_text(encoding="utf-8"))

            self.assertEqual(validation_result["status"], "FAIL")
            self.assertEqual(summary["executor_status"], "FAILED")
            self.assertEqual(summary["schema_validation"], "PASS")
            self.assertIn("Validator execution failed for validate_runner_v1", summary["detail"])
            self.assertTrue((run_dir / "stdout.log").exists())
            self.assertTrue((run_dir / "stderr.log").exists())
            self.assertTrue((run_dir / "exit_code.txt").exists())


if __name__ == "__main__":
    unittest.main()
