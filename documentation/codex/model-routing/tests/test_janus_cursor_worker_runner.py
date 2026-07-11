from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


spec = importlib.util.spec_from_file_location("janus_cursor_worker_runner", SCRIPTS_DIR / "janus_cursor_worker_runner.py")
cursor_runner = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = cursor_runner
spec.loader.exec_module(cursor_runner)


class JanusCursorWorkerRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_runs_dir = cursor_runner.CURSOR_RUNS_DIR
        self.original_log_path = cursor_runner.CURSOR_DELEGATION_LOG_PATH
        cursor_runner.CURSOR_RUNS_DIR = self.temp_path / "runs"
        cursor_runner.CURSOR_DELEGATION_LOG_PATH = self.temp_path / "cursor_delegation_log.jsonl"
        self.addCleanup(self._restore_paths)

    def _restore_paths(self) -> None:
        cursor_runner.CURSOR_RUNS_DIR = self.original_runs_dir
        cursor_runner.CURSOR_DELEGATION_LOG_PATH = self.original_log_path

    def write_valid_package(self) -> Path:
        package_path = self.temp_path / "worker_package.json"
        package_path.write_text(
            json.dumps(
                {
                    "task_label": "Fixture helper",
                    "worker_profile": "cursor-agent",
                    "allowed_edit_paths": ["tests/fixtures/example.py"],
                    "acceptance_criteria": ["writes one bounded fixture"],
                    "checks": [{"label": "unit", "command": ["python", "-m", "pytest", "tests/fixtures"]}],
                    "forbidden_actions": [
                        "commit",
                        "push",
                        "tag",
                        "merge",
                        "release",
                        "publish",
                        "dependency",
                        "secret",
                        "auth",
                        "security",
                        "privacy",
                        "migration",
                        "architecture",
                    ],
                    "requested_actions": ["edit"],
                    "task_prompt": "Write one bounded fixture.",
                }
            ),
            encoding="utf-8",
        )
        return package_path

    def write_allowlist(self, *items: str) -> Path:
        path = self.temp_path / "allowlist.txt"
        path.write_text("\n".join(items) + "\n", encoding="utf-8")
        return path

    def write_accepted_source_run_dir(self) -> Path:
        run_dir = self.temp_path / "accepted-source"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "dispatcher_result.json").write_text(
            json.dumps(
                {
                    "final_outcome": "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
                    "changed_files": [
                        "documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/sandbox/gate_prompt_apply_shadow.py"
                    ],
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "changed_files.txt").write_text(
            "documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_write_apply_candidate/sandbox/gate_prompt_apply_shadow.py\n",
            encoding="utf-8",
        )
        (run_dir / "cursor_response.json").write_text(
            json.dumps({"summary": "Apply the accepted prompt delta exactly once."}),
            encoding="utf-8",
        )
        return run_dir

    def parse(self, *argv: str):
        return cursor_runner.parse_args(list(argv))

    def test_missing_api_key_blocks_before_invoke(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-BLOCK-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        env = os.environ.copy()
        env.pop("CURSOR_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "BLOCKED")
        self.assertEqual(result["final_outcome"], "CURSOR_API_KEY_MISSING")
        self.assertTrue((self.temp_path / "runs" / "WF-CURSOR-BLOCK-001" / "dispatcher_result.json").exists())

    def test_missing_agent_cli_blocks_before_invoke(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-NO-AGENT-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value=None):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "BLOCKED")
        self.assertEqual(result["final_outcome"], "CURSOR_AGENT_CLI_MISSING")

    def test_input_package_can_validate_via_worker_package_reference(self) -> None:
        worker_package_path = self.write_valid_package()
        input_package_path = self.temp_path / "input_package.json"
        input_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Bounded fixture edit",
                    "worker_package_json": "worker_package.json",
                }
            ),
            encoding="utf-8",
        )

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        validation = cursor_runner.validate_package_or_worker_reference(input_package_path)

        self.assertEqual(validation["validation_result"], "PASS")
        self.assertEqual(validation["contract_status"], "TASK_PACKAGE_VALID_VIA_WORKER_REFERENCE")

    def test_assist_only_lane_uses_no_force_flags(self) -> None:
        package_path = self.write_valid_package()
        args = self.parse(
            "--lane",
            "debug_hypothesis_review",
            "--workflow-id",
            "WF-CURSOR-ASSIST-001",
            "--input-package-json",
            str(package_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["selected_model"], "auto")
        self.assertEqual(result["cursor_pool"], "auto_composer")
        self.assertEqual(result["planned_command"][0], "C:\\fake\\agent.exe")
        self.assertNotIn("--force", result["planned_command"])
        self.assertNotIn("--approve-mcps", result["planned_command"])

    def test_proposal_first_lane_uses_write_shell_flags(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-PROPOSAL-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["selected_model"], "composer-2.5")
        self.assertEqual(result["cursor_pool"], "auto_composer")
        self.assertEqual(result["planned_command"][0], "C:\\fake\\agent.exe")
        self.assertIn("--force", result["planned_command"])
        self.assertIn("--approve-mcps", result["planned_command"])

    def test_api_pool_dry_run_passes_model_and_pool_to_planned_command(self) -> None:
        package_path = self.write_valid_package()
        args = self.parse(
            "--lane",
            "documentation_draft_review",
            "--workflow-id",
            "WF-CURSOR-API-DRY-001",
            "--input-package-json",
            str(package_path),
            "--cursor-pool",
            "api",
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["selected_model"], "gpt-5.4-mini-medium")
        self.assertEqual(result["cursor_pool"], "api")
        self.assertIn("--model", result["planned_command"])
        self.assertIn("gpt-5.4-mini-medium", result["planned_command"])

    def test_allowlist_violation_detection_fails_mocked_live_run(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "execution_patch_candidate",
            "--workflow-id",
            "WF-CURSOR-VIOLATION-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--execute-live",
        )

        git_calls = {"count": 0}

        def fake_run(command: list[str], *, timeout_seconds=None):
            class Completed:
                returncode = 0
                stdout = json.dumps({"session_id": "sess-001", "status": "success"})
                stderr = ""

            if command[:3] == ["git", "diff", "--name-only"]:
                git_calls["count"] += 1
                Completed.stdout = "" if git_calls["count"] == 1 else "tests/fixtures/example.py\nsrc/outside.py\n"
            return Completed()

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                with patch.object(cursor_runner, "run_command", side_effect=fake_run):
                    with patch.object(
                        cursor_runner,
                        "invoke_agent_command",
                        return_value=type(
                            "Completed",
                            (),
                            {"returncode": 0, "stdout": json.dumps({"session_id": "sess-001", "status": "success"}), "stderr": ""},
                        )(),
                    ):
                        result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["final_outcome"], "CURSOR_ALLOWLIST_VIOLATION")
        self.assertIn("src/outside.py", result["changed_outside_allowlist"])

    def test_session_id_persisted_and_resume_used_in_mocked_live_run(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-SESSION-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--resume-session-id",
            "resume-123",
            "--execute-live",
        )

        git_calls = {"count": 0}

        def fake_run(command: list[str], *, timeout_seconds=None):
            class Completed:
                returncode = 0
                stdout = json.dumps({"session_id": "sess-abc", "status": "success"})
                stderr = ""

            if command[:3] == ["git", "diff", "--name-only"]:
                git_calls["count"] += 1
                Completed.stdout = "" if git_calls["count"] == 1 else "tests/fixtures/example.py\n"
            return Completed()

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                with patch.object(cursor_runner, "run_command", side_effect=fake_run):
                    snapshot_calls = {"count": 0}

                    def fake_snapshot(paths: list[str]) -> dict[str, str | None]:
                        label = "before" if snapshot_calls["count"] == 0 else "after"
                        snapshot_calls["count"] += 1
                        return {path: label for path in paths}

                    with patch.object(cursor_runner, "snapshot_file_hashes", side_effect=fake_snapshot):
                        with patch.object(
                            cursor_runner,
                            "invoke_agent_command",
                            return_value=type(
                                "Completed",
                                (),
                                {
                                    "returncode": 0,
                                    "stdout": json.dumps({"session_id": "sess-abc", "status": "success"}),
                                    "stderr": "",
                                },
                            )(),
                        ):
                            result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["session_id"], "sess-abc")
        self.assertIn("--resume", result["planned_command"])
        session_file = self.temp_path / "runs" / "WF-CURSOR-SESSION-001" / "session_id.txt"
        self.assertTrue(session_file.exists())
        self.assertEqual(session_file.read_text(encoding="utf-8").strip(), "sess-abc")
        log_lines = cursor_runner.CURSOR_DELEGATION_LOG_PATH.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(log_lines), 1)
        log_row = json.loads(log_lines[0])
        self.assertTrue(log_row["resume_used"])

    def test_prompt_uses_worker_package_and_contract_when_input_package_lacks_task_prompt(self) -> None:
        worker_package_path = self.write_valid_package()
        input_package_path = self.temp_path / "input_package.json"
        input_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Bounded fixture edit",
                    "worker_package_json": str(worker_package_path.relative_to(cursor_runner.REPO_ROOT)).replace("\\", "/")
                    if worker_package_path.is_relative_to(cursor_runner.REPO_ROOT)
                    else None,
                    "cursor_prompt_contract": "Edit only allowlisted files. Return concise summary.",
                    "acceptance_criteria": ["Only fixture files may change."],
                }
            ),
            encoding="utf-8",
        )
        allowlist = ["tests/fixtures/example.py"]

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        rewritten_input = self.temp_path / "input_package_repo_relative.json"
        rewritten_input.write_text(
            json.dumps(
                {
                    "task_label": "Bounded fixture edit",
                    "worker_package_json": "worker_package.json",
                    "cursor_prompt_contract": "Edit only allowlisted files. Return concise summary.",
                    "acceptance_criteria": ["Only fixture files may change."],
                }
            ),
            encoding="utf-8",
        )

        prompt = cursor_runner.task_prompt_from_package(rewritten_input, "test_fixture_worker", allowlist)

        self.assertIn("Write one bounded fixture.", prompt)
        self.assertIn("Edit only allowlisted files. Return concise summary.", prompt)
        self.assertIn("Allowed edit paths:", prompt)
        self.assertIn("tests/fixtures/example.py", prompt)

    def test_prompt_uses_worker_task_prompt_path_when_present(self) -> None:
        prompt_path = self.temp_path / "worker_prompt.md"
        prompt_path.write_text("Use prompt path text.\n", encoding="utf-8")
        worker_package_path = self.temp_path / "worker_package.json"
        worker_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Fixture helper",
                    "worker_profile": "cursor-agent",
                    "allowed_edit_paths": ["tests/fixtures/example.py"],
                    "acceptance_criteria": ["writes one bounded fixture"],
                    "checks": [{"label": "unit", "command": ["python", "-m", "pytest", "tests/fixtures"]}],
                    "forbidden_actions": [
                        "commit",
                        "push",
                        "tag",
                        "merge",
                        "release",
                        "publish",
                        "dependency",
                        "secret",
                        "auth",
                        "security",
                        "privacy",
                        "migration",
                        "architecture",
                    ],
                    "requested_actions": ["edit"],
                    "task_prompt_path": "worker_prompt.md",
                }
            ),
            encoding="utf-8",
        )
        input_package_path = self.temp_path / "input_package.json"
        input_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Bounded fixture edit",
                    "worker_package_json": "worker_package.json",
                }
            ),
            encoding="utf-8",
        )

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        prompt = cursor_runner.task_prompt_from_package(input_package_path, "test_fixture_worker", ["tests/fixtures/example.py"])

        self.assertIn("Use prompt path text.", prompt)

    def test_dry_run_blocks_when_worker_package_and_allowlist_disagree(self) -> None:
        worker_package_path = self.write_valid_package()
        input_package_path = self.temp_path / "input_package.json"
        input_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Bounded fixture edit",
                    "worker_package_json": "worker_package.json",
                    "allowlist_file": "allowlist.txt",
                }
            ),
            encoding="utf-8",
        )
        allowlist_path = self.write_allowlist("tests/fixtures/other.py")

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-ALLOWLIST-MISMATCH-001",
            "--input-package-json",
            str(input_package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "BLOCKED")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_INPUT_BLOCKED")
        self.assertEqual(result["allowlist_consistency_validation"]["validation_result"], "FAIL")
        self.assertTrue(
            any("allowed_edit_paths" in issue for issue in result["allowlist_consistency_validation"]["issues"])
        )

    def test_execution_write_apply_candidate_blocks_without_accepted_source(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "execution_write_apply_candidate",
            "--workflow-id",
            "WF-CURSOR-WRITE-BLOCK-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "BLOCKED")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_INPUT_BLOCKED")
        self.assertEqual(result["accepted_source_validation"]["validation_result"], "FAIL")
        self.assertIn("accepted_source_run_dir is required", result["accepted_source_validation"]["issues"])

    def test_execution_write_apply_candidate_dry_run_includes_accepted_source_context(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        accepted_source_run_dir = self.write_accepted_source_run_dir()
        args = self.parse(
            "--lane",
            "execution_write_apply_candidate",
            "--workflow-id",
            "WF-CURSOR-WRITE-DRY-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--accepted-source-run-dir",
            str(accepted_source_run_dir),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "CURSOR_WORKER_DRY_RUN_READY")
        self.assertEqual(result["accepted_source_validation"]["validation_result"], "PASS")
        prompt = result["planned_command"][-1]
        self.assertIn("Accepted source package context:", prompt)
        self.assertIn("EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW", prompt)
        self.assertIn("Apply the accepted prompt delta exactly once.", prompt)

    def test_dry_run_uses_common_allowlist_workspace_root(self) -> None:
        sandbox_dir = self.temp_path / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        helper_path = sandbox_dir / "helper.py"
        test_path = sandbox_dir / "test_helper.py"
        helper_path.write_text("print('ok')\n", encoding="utf-8")
        test_path.write_text("print('ok')\n", encoding="utf-8")

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("sandbox/helper.py", "sandbox/test_helper.py")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-WORKSPACE-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["workspace_root"], str(sandbox_dir))
        self.assertEqual(result["planned_command"][3], str(sandbox_dir))
        prompt = result["planned_command"][-1]
        self.assertIn("Workspace root:", prompt)
        self.assertIn("Workspace-relative edit paths:\n- helper.py\n- test_helper.py", prompt)

    def test_dry_run_uses_parent_workspace_root_for_nonexistent_allowlist_targets(self) -> None:
        sandbox_dir = self.temp_path / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("sandbox/future.md", "sandbox/future.json")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-WORKSPACE-NEWFILES-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["workspace_root"], str(sandbox_dir))

    def test_minimal_write_apply_prompt_uses_compact_shape(self) -> None:
        allowlist_path = self.write_allowlist("sandbox/helper.py", "sandbox/test_helper.py")
        accepted_source_run_dir = self.write_accepted_source_run_dir()
        input_package_path = self.temp_path / "input_package.json"
        input_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Compact accepted-source write apply",
                    "worker_package_json": "worker_package.json",
                    "local_validation_command": "python -m pytest sandbox/test_helper.py -q",
                    "cursor_prompt_mode": "minimal_write_apply",
                }
            ),
            encoding="utf-8",
        )

        sandbox_dir = self.temp_path / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        (sandbox_dir / "helper.py").write_text("print('ok')\n", encoding="utf-8")
        (sandbox_dir / "test_helper.py").write_text("print('ok')\n", encoding="utf-8")

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))
        self.write_valid_package()

        args = self.parse(
            "--lane",
            "execution_write_apply_candidate",
            "--workflow-id",
            "WF-CURSOR-MINIMAL-WRITE-001",
            "--input-package-json",
            str(input_package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--accepted-source-run-dir",
            str(accepted_source_run_dir),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        prompt = result["planned_command"][-1]
        self.assertIn("Task: Compact accepted-source write apply", prompt)
        self.assertIn("Files:\n- helper.py\n- test_helper.py", prompt)
        self.assertIn("Run only this validation command: python -m pytest sandbox/test_helper.py -q", prompt)
        self.assertIn("Accepted source summary: Apply the accepted prompt delta exactly once.", prompt)
        self.assertNotIn("Accepted source package context:", prompt)

    def test_minimal_worker_prompt_uses_compact_shape(self) -> None:
        sandbox_dir = self.temp_path / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)

        original_repo_root = cursor_runner.REPO_ROOT
        cursor_runner.REPO_ROOT = self.temp_path
        self.addCleanup(lambda: setattr(cursor_runner, "REPO_ROOT", original_repo_root))

        package_path = self.write_valid_package()
        input_package_path = self.temp_path / "input_package.json"
        input_package_path.write_text(
            json.dumps(
                {
                    "task_label": "Compact worker",
                    "worker_package_json": "worker_package.json",
                    "cursor_prompt_mode": "minimal_worker",
                    "cursor_prompt_contract": "Write exactly two evidence files or a BLOCKED note.",
                    "local_validation_command": "python -c pass",
                    "acceptance_criteria": ["Only allowlisted files may change."],
                }
            ),
            encoding="utf-8",
        )
        allowlist_path = self.write_allowlist("sandbox/result.md", "sandbox/result.json")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-MINIMAL-WORKER-001",
            "--input-package-json",
            str(input_package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--dry-run",
        )

        with patch.dict(os.environ, {"CURSOR_API_KEY": "test-key"}, clear=False):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "PASS")
        prompt = result["planned_command"][-1]
        self.assertIn("Task: Compact worker", prompt)
        self.assertIn("Write exactly two evidence files or a BLOCKED note.", prompt)
        self.assertIn("Files:\n- result.md\n- result.json", prompt)
        self.assertIn("Check: python -c pass", prompt)
        self.assertNotIn("Variable suffix:\nCollect bounded live evidence", prompt)

    def test_live_timeout_writes_partial_artifacts_and_blocks(self) -> None:
        package_path = self.write_valid_package()
        allowlist_path = self.write_allowlist("tests/fixtures/example.py")
        args = self.parse(
            "--lane",
            "test_fixture_worker",
            "--workflow-id",
            "WF-CURSOR-TIMEOUT-001",
            "--input-package-json",
            str(package_path),
            "--allowlist-file",
            str(allowlist_path),
            "--execute-live",
        )

        def fake_run(command: list[str], *, timeout_seconds=None):
            if command[:3] == ["git", "diff", "--name-only"]:
                class GitCompleted:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return GitCompleted()
            raise subprocess.TimeoutExpired(
                cmd=command,
                timeout=timeout_seconds or 180,
                output='{"partial":"stdout"}',
                stderr="partial stderr",
            )

        with patch.dict(
            os.environ,
            {"CURSOR_API_KEY": "test-key", "JANUS_CURSOR_LIVE_TIMEOUT_SECONDS": "7"},
            clear=False,
        ):
            with patch.object(cursor_runner, "resolve_agent_binary", return_value="C:\\fake\\agent.exe"):
                with patch.object(cursor_runner, "run_command", side_effect=fake_run):
                    with patch.object(
                        cursor_runner,
                        "invoke_agent_command",
                        side_effect=subprocess.TimeoutExpired(
                            cmd=["C:\\fake\\agent.exe"],
                            timeout=7,
                            output='{"partial":"stdout"}',
                            stderr="partial stderr",
                        ),
                    ):
                        result = cursor_runner.summarize(args)

        self.assertEqual(result["validation_result"], "BLOCKED")
        self.assertEqual(result["final_outcome"], "CURSOR_AGENT_TIMEOUT")
        self.assertEqual(result["timeout_seconds"], 7)
        run_dir = self.temp_path / "runs" / "WF-CURSOR-TIMEOUT-001"
        self.assertTrue((run_dir / "dispatcher_result.json").exists())
        self.assertEqual((run_dir / "stdout.log").read_text(encoding="utf-8"), '{"partial":"stdout"}')
        self.assertEqual((run_dir / "stderr.log").read_text(encoding="utf-8"), "partial stderr")
        cursor_response = json.loads((run_dir / "cursor_response.json").read_text(encoding="utf-8"))
        self.assertTrue(cursor_response["timeout"])
        self.assertEqual(result["transport_result"], "TRANSPORT_FAIL")
        self.assertEqual(result["semantic_result"], "SEMANTIC_FAIL")

    def test_resolve_live_timeout_seconds_uses_lane_tiers(self) -> None:
        assist_config = {"mode": "assist_only", "allow_write": False}
        tool_config = {"mode": "proposal_first", "allow_write": True}
        self.assertEqual(
            cursor_runner.resolve_live_timeout_seconds(cursor_config=assist_config, allowlist=["a.py"]),
            (180, "assist_or_review_default"),
        )
        self.assertEqual(
            cursor_runner.resolve_live_timeout_seconds(cursor_config=tool_config, allowlist=["a.py"]),
            (240, "single_file_tool_lane"),
        )
        self.assertEqual(
            cursor_runner.resolve_live_timeout_seconds(cursor_config=tool_config, allowlist=["a.py", "b.py"]),
            (300, "multi_file_tool_lane"),
        )

    def test_classify_live_run_outcome_marks_zero_file_write_lane_as_semantic_fail(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")
        outcome = cursor_runner.classify_live_run_outcome(
            completed=completed,
            changed_files=[],
            changed_outside_allowlist=[],
            cursor_config={"mode": "proposal_first", "allow_write": True},
            package_payload={},
        )
        self.assertEqual(outcome["transport_result"], "TRANSPORT_PASS")
        self.assertEqual(outcome["semantic_result"], "SEMANTIC_FAIL")
        self.assertEqual(outcome["validation_result"], "FAIL")
        self.assertEqual(outcome["final_outcome"], "CURSOR_SEMANTIC_FAIL_NO_CHANGES")

    def test_classify_live_run_outcome_allows_explicit_no_op_package(self) -> None:
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")
        outcome = cursor_runner.classify_live_run_outcome(
            completed=completed,
            changed_files=[],
            changed_outside_allowlist=[],
            cursor_config={"mode": "proposal_first", "allow_write": True},
            package_payload={"explicit_no_op_ok": True},
        )
        self.assertEqual(outcome["semantic_result"], "SEMANTIC_PASS")
        self.assertEqual(outcome["validation_result"], "PASS")


if __name__ == "__main__":
    unittest.main()
