from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "isolated_aider_workspace_runner",
    SCRIPTS_DIR / "isolated_aider_workspace_runner.py",
)
runner = importlib.util.module_from_spec(RUNNER_SPEC)
assert RUNNER_SPEC and RUNNER_SPEC.loader
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)


def package_payload() -> dict[str, object]:
    return {
        "task_label": "Test isolated worker",
        "worker_profile": "aider-openrouter-qwen",
        "task_prompt": "Update docs/target.md only.",
        "workspace_files": [
            {
                "repo_path": "docs/target.md",
                "workspace_path": "docs/target.md",
                "allow_edit": True,
                "copy_back": True,
            }
        ],
        "pre_commands": [{"label": "precheck", "command": ["python", "--version"], "expected_exit_codes": [0]}],
        "post_commands": [{"label": "postcheck", "command": ["python", "--version"], "expected_exit_codes": [0]}],
        "acceptance_criteria": ["Only docs/target.md changes are allowed."],
        "requested_actions": ["edit"],
    }


class IsolatedAiderWorkspaceRunnerTests(unittest.TestCase):
    def test_delegated_run_writes_normalized_success_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "target.md").write_text("before\n", encoding="utf-8")

            package_path = root / "input.json"
            package_path.write_text(json.dumps(package_payload(), indent=2), encoding="utf-8")
            validated = runner.validate_package(package_payload(), package_path)
            run_dir = root / "run"
            run_dir.mkdir()

            original_repo_root = runner.REPO_ROOT
            original_usage_log = runner.CENTRAL_USAGE_LOG_PATH
            original_run_command = runner.run_command
            original_repo_root_aider_artifacts = runner.repo_root_aider_artifacts
            original_env = os.environ.copy()
            try:
                runner.REPO_ROOT = root
                runner.CENTRAL_USAGE_LOG_PATH = root / "usage.jsonl"
                runner.repo_root_aider_artifacts = lambda: []
                os.environ["OPENROUTER_API_KEY"] = "test-key"

                def fake_run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
                    if command and command[0] == "aider":
                        target = cwd / "docs" / "target.md"
                        target.write_text("before\nafter\n", encoding="utf-8")
                        return subprocess.CompletedProcess(command, 0, stdout="aider ok\n", stderr="")
                    return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

                runner.run_command = fake_run_command

                result = runner.delegated_run(
                    workflow_id="WF-AIDER-SUCCESS-001",
                    run_dir=run_dir,
                    validated_package=validated,
                    package_path=package_path,
                    normal_target_model="5.4 high",
                    or_model="openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                    estimated_or_cost=0.001,
                    confidence_percent=80,
                )
            finally:
                runner.REPO_ROOT = original_repo_root
                runner.CENTRAL_USAGE_LOG_PATH = original_usage_log
                runner.run_command = original_run_command
                runner.repo_root_aider_artifacts = original_repo_root_aider_artifacts
                os.environ.clear()
                os.environ.update(original_env)

            self.assertEqual(result["final_outcome"], "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW")
            self.assertEqual(result["gateway_status"], "WORKER_SUCCESS_REVIEWABLE")
            self.assertEqual(result["validation_result"], "PASS")
            self.assertTrue((run_dir / "RESULT.json").exists())
            self.assertTrue((run_dir / "RESULT.md").exists())
            self.assertTrue((run_dir / "DIFF.patch").read_text(encoding="utf-8").strip())
            self.assertEqual((root / "docs" / "target.md").read_text(encoding="utf-8"), "before\nafter\n")

    def test_delegated_run_without_openrouter_key_returns_reviewable_blocked_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "target.md").write_text("before\n", encoding="utf-8")
            payload = package_payload()
            package_path = root / "input.json"
            package_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            validated = runner.validate_package(payload, package_path)
            run_dir = root / "run"
            run_dir.mkdir()

            original_repo_root = runner.REPO_ROOT
            original_usage_log = runner.CENTRAL_USAGE_LOG_PATH
            original_repo_root_aider_artifacts = runner.repo_root_aider_artifacts
            original_env = os.environ.copy()
            try:
                runner.REPO_ROOT = root
                runner.CENTRAL_USAGE_LOG_PATH = root / "usage.jsonl"
                runner.repo_root_aider_artifacts = lambda: []
                os.environ.pop("OPENROUTER_API_KEY", None)

                result = runner.delegated_run(
                    workflow_id="WF-AIDER-BLOCKED-001",
                    run_dir=run_dir,
                    validated_package=validated,
                    package_path=package_path,
                    normal_target_model="5.4 high",
                    or_model="openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                    estimated_or_cost=0.001,
                    confidence_percent=80,
                )
            finally:
                runner.REPO_ROOT = original_repo_root
                runner.CENTRAL_USAGE_LOG_PATH = original_usage_log
                runner.repo_root_aider_artifacts = original_repo_root_aider_artifacts
                os.environ.clear()
                os.environ.update(original_env)

            self.assertEqual(result["final_outcome"], "ISOLATED_AIDER_BLOCKED_AND_FALLBACK")
            self.assertEqual(result["gateway_status"], "WORKER_NON_SUCCESS_REVIEWABLE")
            self.assertEqual(result["validation_result"], "PASS")
            self.assertEqual(json.loads((run_dir / "RESULT.json").read_text(encoding="utf-8"))["status"], "blocked")

    def test_delegated_run_with_invalid_profile_returns_reviewable_blocked_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "target.md").write_text("before\n", encoding="utf-8")
            payload = package_payload()
            package_path = root / "input.json"
            package_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            validated = runner.validate_package(payload, package_path)
            run_dir = root / "run"
            run_dir.mkdir()

            original_repo_root = runner.REPO_ROOT
            original_usage_log = runner.CENTRAL_USAGE_LOG_PATH
            original_repo_root_aider_artifacts = runner.repo_root_aider_artifacts
            original_env = os.environ.copy()
            try:
                runner.REPO_ROOT = root
                runner.CENTRAL_USAGE_LOG_PATH = root / "usage.jsonl"
                runner.repo_root_aider_artifacts = lambda: []
                os.environ["OPENROUTER_API_KEY"] = "test-key"

                result = runner.delegated_run(
                    workflow_id="WF-AIDER-BLOCKED-002",
                    run_dir=run_dir,
                    validated_package=validated,
                    package_path=package_path,
                    normal_target_model="5.4 high",
                    or_model="invalid-profile",
                    estimated_or_cost=0.001,
                    confidence_percent=80,
                )
            finally:
                runner.REPO_ROOT = original_repo_root
                runner.CENTRAL_USAGE_LOG_PATH = original_usage_log
                runner.repo_root_aider_artifacts = original_repo_root_aider_artifacts
                os.environ.clear()
                os.environ.update(original_env)

            self.assertEqual(result["final_outcome"], "ISOLATED_AIDER_BLOCKED_AND_FALLBACK")
            self.assertEqual(result["gateway_status"], "WORKER_NON_SUCCESS_REVIEWABLE")
            self.assertEqual(result["validation_result"], "PASS")
            self.assertIn("blocked", (run_dir / "RESULT.md").read_text(encoding="utf-8").lower())

    def test_local_summary_path_writes_reviewable_local_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_path = root / "input.json"
            package_path.write_text(json.dumps(package_payload(), indent=2), encoding="utf-8")
            run_dir = root / "run"
            run_dir.mkdir()
            validated = runner.validate_package(package_payload(), package_path)

            task_package = runner.build_gateway_task_package(
                validated,
                package_path,
                "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
            )
            runner.write_worker_task_package(run_dir / runner.TASK_PACKAGE_FILENAME, task_package)
            result = runner.local_summary(
                workflow_id="WF-AIDER-LOCAL-001",
                task_label="Local only",
                normal_target_model="5.4 high",
                or_model="openrouter/qwen/qwen3-coder-30b-a3b-instruct",
            )
            result = runner.finalize_gateway_result(
                run_dir=run_dir,
                task_package_path=run_dir / runner.TASK_PACKAGE_FILENAME,
                result_payload=result,
                status="local",
                summary="Operator chose the local path.",
                changed_files=[],
                checks_status="not_run",
                checks_log="Local path selected.\n",
                diff_patch="",
                cost_payload={"usage_available": False},
            )

            self.assertEqual(result["gateway_status"], "WORKER_NON_SUCCESS_REVIEWABLE")
            self.assertEqual(result["validation_result"], "PASS")
            self.assertEqual(json.loads((run_dir / "RESULT.json").read_text(encoding="utf-8"))["status"], "local")


if __name__ == "__main__":
    unittest.main()
