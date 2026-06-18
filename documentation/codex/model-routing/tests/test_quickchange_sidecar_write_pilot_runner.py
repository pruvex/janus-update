from __future__ import annotations

import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()
