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


def write_shadow_eval_fixture(root: Path) -> Path:
    sandbox_root = root / "development" / "openrouter-skill-tests" / "janus-worker-gateway-shadow-eval"
    docs_dir = sandbox_root / "docs_fleissarbeit"
    fixture_dir = sandbox_root / "test_fixture_arbeit"
    (docs_dir / "docs").mkdir(parents=True)
    (fixture_dir / "fixtures").mkdir(parents=True)
    (fixture_dir / "tests").mkdir(parents=True)

    (docs_dir / "docs" / "target_doc.md").write_text("before docs\n", encoding="utf-8")
    (fixture_dir / "fixtures" / "contact_memory_fixture.json").write_text('{"contact":"before"}\n', encoding="utf-8")
    (fixture_dir / "tests" / "test_contact_memory_fixture.py").write_text("def test_fixture():\n    assert True\n", encoding="utf-8")
    (docs_dir / "task_prompt.md").write_text("Edit docs only.\n", encoding="utf-8")
    (fixture_dir / "task_prompt.md").write_text("Edit fixture/test only.\n", encoding="utf-8")

    (docs_dir / "task_package.json").write_text(
        json.dumps(
            {
                "task_label": "Shadow docs fleissarbeit comparison package",
                "shadow_work_class": "docs_fleissarbeit",
                "worker_profile": "shadow-eval-fixed-pair",
                "allowed_edit_paths": ["docs/target_doc.md"],
                "forbidden_actions": sorted(runner.REQUIRED_FORBIDDEN_ACTIONS),
                "acceptance_criteria": ["Only docs/target_doc.md may change."],
                "checks": [{"label": "python", "command": ["python", "--version"], "expected_exit_codes": [0]}],
                "requested_actions": ["edit"],
                "task_prompt_path": (docs_dir / "task_prompt.md").relative_to(root).as_posix(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (fixture_dir / "task_package.json").write_text(
        json.dumps(
            {
                "task_label": "Shadow test fixture comparison package",
                "shadow_work_class": "test_fixture_arbeit",
                "worker_profile": "shadow-eval-fixed-pair",
                "allowed_edit_paths": [
                    "fixtures/contact_memory_fixture.json",
                    "tests/test_contact_memory_fixture.py",
                ],
                "forbidden_actions": sorted(runner.REQUIRED_FORBIDDEN_ACTIONS),
                "acceptance_criteria": ["Only bounded fixture/test files may change."],
                "checks": [{"label": "python", "command": ["python", "--version"], "expected_exit_codes": [0]}],
                "requested_actions": ["edit"],
                "task_prompt_path": (fixture_dir / "task_prompt.md").relative_to(root).as_posix(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    manifest_path = sandbox_root / "shadow_evaluation_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "evaluation_id": "SPEC30-SHADOW-EVAL-001",
                "sandbox_root": sandbox_root.relative_to(root).as_posix(),
                "real_repo_writeback_allowed": False,
                "global_worker_release_allowed": False,
                "real_consumer_activation_allowed": False,
                "shadow_work_classes": [
                    {
                        "class_id": "docs_fleissarbeit",
                        "task_package_path": (docs_dir / "task_package.json").relative_to(root).as_posix(),
                        "comparison_models": [
                            "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                            "openrouter/moonshotai/kimi-k2.5",
                        ],
                    },
                    {
                        "class_id": "test_fixture_arbeit",
                        "task_package_path": (fixture_dir / "task_package.json").relative_to(root).as_posix(),
                        "comparison_models": [
                            "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                            "openrouter/moonshotai/kimi-k2.5",
                        ],
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


class IsolatedAiderWorkspaceRunnerTests(unittest.TestCase):
    def test_build_runner_package_from_shadow_task_maps_shadow_files_into_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_eval_fixture(root)
            docs_package_path = manifest_path.parent / "docs_fleissarbeit" / "task_package.json"

            payload = runner.build_runner_package_from_shadow_task(docs_package_path, repo_root=root)

        self.assertEqual(payload["workspace_files"][0]["repo_path"], "development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/docs_fleissarbeit/docs/target_doc.md")
        self.assertEqual(payload["workspace_files"][0]["workspace_path"], "docs/target_doc.md")
        self.assertEqual(payload["post_commands"][0]["label"], "python")

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

    def test_run_shadow_evaluation_bundle_writes_class_summaries_and_restores_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_eval_fixture(root)
            docs_file = root / "development" / "openrouter-skill-tests" / "janus-worker-gateway-shadow-eval" / "docs_fleissarbeit" / "docs" / "target_doc.md"
            docs_before = docs_file.read_text(encoding="utf-8")

            original_repo_root = runner.REPO_ROOT
            original_delegated_run = runner.delegated_run
            try:
                runner.REPO_ROOT = root

                def fake_delegated_run(
                    *,
                    workflow_id: str,
                    run_dir: Path,
                    validated_package: dict[str, object],
                    package_path: Path,
                    normal_target_model: str,
                    or_model: str,
                    estimated_or_cost: float,
                    confidence_percent: int,
                ) -> dict[str, object]:
                    changed_files = list(validated_package["allowed_edit_paths"])
                    repo_target = root / validated_package["workspace_files"][0]["repo_path"]
                    repo_target.write_text("mutated during fake run\n", encoding="utf-8")
                    blocked = "kimi-k2.5" in or_model and "test fixture" in str(validated_package["task_label"]).lower()
                    runner.write_worker_result_dir(
                        run_dir,
                        status="blocked" if blocked else "success",
                        summary="blocked" if blocked else "success",
                        changed_files=[] if blocked else changed_files,
                        checks_status="pass",
                        checks_log="ok\n",
                        diff_patch="" if blocked else "diff --git a/file b/file\n",
                        cost_payload={"usage_available": False, "estimated_or_cost_usd": estimated_or_cost},
                    )
                    return {
                        "workflow_id": workflow_id,
                        "final_outcome": "ISOLATED_AIDER_BLOCKED_AND_FALLBACK" if blocked else "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW",
                        "gateway_status": "WORKER_NON_SUCCESS_REVIEWABLE" if blocked else "WORKER_SUCCESS_REVIEWABLE",
                        "validation_result": "PASS",
                        "changed_files": [] if blocked else changed_files,
                    }

                runner.delegated_run = fake_delegated_run

                result = runner.run_shadow_evaluation_bundle(
                    shadow_eval_manifest_path=manifest_path,
                    normal_target_model="5.4 high",
                    estimated_or_cost=0.001,
                    confidence_percent=80,
                    workflow_id="WF-SHADOW-EVAL-TEST-001",
                    repo_root=root,
                )
            finally:
                runner.REPO_ROOT = original_repo_root
                runner.delegated_run = original_delegated_run

            self.assertEqual(result["bundle_validation"]["validation_result"], "PASS")
            self.assertEqual(result["bundle_validation"]["gateway_status"], "SHADOW_EVALUATION_RUNS_BLOCKED_REVIEWABLE")
            self.assertTrue((root / result["evaluation_run_directory"] / "docs_fleissarbeit" / "comparison_summary.json").exists())
            self.assertEqual(docs_file.read_text(encoding="utf-8"), docs_before)


if __name__ == "__main__":
    unittest.main()
