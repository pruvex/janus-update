from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "quickchange_sidecar_write_pilot_runner.py"
)
SPEC = importlib.util.spec_from_file_location("quickchange_sidecar_write_pilot_runner", SCRIPT_PATH)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class QuickchangeSidecarWritePilotRunnerTests(unittest.TestCase):
    def test_prompt_summary_uses_openrouter_choice_label(self) -> None:
        result = runner.prompt_summary(
            workflow_id="TASK-SPEC19-4-PROMPT",
            task_label="Tiny quickchange gate wording",
            normal_target_model="5.4",
            sidecar_model="gpt-5.4",
            editable_paths=["frontend/index.html"],
            max_touched_files=2,
            diff_size_cap="small",
        )

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OpenRouter")
        self.assertEqual(result["sidecar_model_provider"], "OpenRouter sidecar / gpt-5.4")

    def test_invoke_live_run_includes_execute_flag_and_allowlist_controls(self) -> None:
        captured: dict[str, object] = {}

        def fake_run_command(command: list[str], cwd: Path):
            captured["command"] = command
            captured["cwd"] = cwd

            class Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return Completed()

        original = runner.run_command
        runner.run_command = fake_run_command
        self.addCleanup(setattr, runner, "run_command", original)

        result = runner.invoke_live_run(
            run_directory=Path("C:/tmp/run"),
            prompt_path=Path("C:/tmp/prompt.md"),
            sidecar_model="gpt-5.4",
            editable_paths=["frontend/index.html"],
            max_touched_files=2,
        )

        self.assertEqual(result.returncode, 0)
        command = captured["command"]
        self.assertIn("-Execute", command)
        self.assertIn("-CaptureGitDiff", command)
        self.assertIn("-FailOnDeleteRenameMove", command)
        self.assertIn("-EditablePath", command)
        self.assertIn("frontend/index.html", command)
        self.assertIn("-MaxTouchedFiles", command)
        self.assertIn("2", command)

    def test_invoke_isolated_aider_runner_forwards_package_and_cost_fields(self) -> None:
        captured: dict[str, object] = {}

        def fake_run_command(command: list[str], cwd: Path):
            captured["command"] = command
            captured["cwd"] = cwd

            class Completed:
                returncode = 0
                stdout = "{}"
                stderr = ""

            return Completed()

        original = runner.run_command
        runner.run_command = fake_run_command
        self.addCleanup(setattr, runner, "run_command", original)

        result = runner.invoke_isolated_aider_runner(
            workflow_id="QC-ISO-001",
            task_label="Quickchange isolated route",
            normal_target_model="5.4 medium",
            or_model="openrouter/qwen/qwen3-coder-30b-a3b-instruct",
            estimated_or_cost=0.0008,
            confidence_percent=70,
            input_package_json=Path("C:/tmp/worker_package.json"),
        )

        self.assertEqual(result.returncode, 0)
        command = captured["command"]
        self.assertEqual(command[0], "python")
        self.assertIn("isolated_aider_workspace_runner.py", command[1])
        self.assertIn("--operator-choice", command)
        self.assertIn("delegated", command)
        self.assertIn("--input-package-json", command)
        self.assertTrue(any(Path(item).name == "worker_package.json" for item in command))
        self.assertIn("--estimated-or-cost", command)
        self.assertIn("0.0008", command)
        self.assertIn("--cost-estimate-confidence-percent", command)
        self.assertIn("70", command)

    def test_main_uses_isolated_aider_path_when_package_is_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "worker_package.json"
            package_path.write_text("{}\n", encoding="utf-8")
            run_dir = temp_path / "run"

            original_build_run_dir = runner.build_run_dir
            original_invoke_isolated = runner.invoke_isolated_aider_runner
            original_argv = sys.argv[:]
            self.addCleanup(setattr, runner, "build_run_dir", original_build_run_dir)
            self.addCleanup(setattr, runner, "invoke_isolated_aider_runner", original_invoke_isolated)
            self.addCleanup(setattr, sys, "argv", original_argv)

            runner.build_run_dir = lambda workflow_id: run_dir

            def fake_invoke_isolated_aider_runner(**kwargs):
                class Completed:
                    returncode = 0
                    stdout = json.dumps(
                        {
                            "summary_header": "ISOLATED AIDER WORKER RESULT",
                            "workflow_id": kwargs["workflow_id"],
                            "selected_path": "isolated_aider_temp_workspace_live",
                            "validation_result": "PASS",
                            "final_outcome": "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW",
                        }
                    )
                    stderr = ""

                return Completed()

            runner.invoke_isolated_aider_runner = fake_invoke_isolated_aider_runner
            sys.argv = [
                "quickchange_sidecar_write_pilot_runner.py",
                "--task-label",
                "Quickchange isolated OR smoke",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "2",
                "--workflow-id",
                "QC-ISOLATED-TEST-001",
                "--sidecar-model",
                "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            stdout_buffer = io.StringIO()
            with contextlib.redirect_stdout(stdout_buffer):
                exit_code = runner.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["selected_path"], "isolated_aider_temp_workspace_live")
            self.assertEqual(operator_summary["validation_result"], "PASS")
            self.assertEqual(operator_summary["final_outcome"], "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW")
            self.assertEqual(operator_summary["delegation_mode"], "isolated_aider_workspace")
            self.assertIn("isolated_aider_workspace_runner.py", operator_summary["forwarded_runner"])


if __name__ == "__main__":
    unittest.main()
