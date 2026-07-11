from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


runner = load_module(
    "quickchange_sidecar_write_pilot_runner_e2e",
    SCRIPTS_DIR / "quickchange_sidecar_write_pilot_runner.py",
)
dispatcher = load_module(
    "codex_bounded_delegation_dispatcher_e2e",
    SCRIPTS_DIR / "codex_bounded_delegation_dispatcher.py",
)


class QuickchangeLiveOperatorPathTests(unittest.TestCase):
    def test_dispatcher_prompt_summary_uses_openrouter_label_for_quickchange(self) -> None:
        args = Namespace(
            task_class="quickchange_patch_review",
            task_label="Tiny quickchange gate wording",
            normal_target_model="5.4",
            selected_or_model="openrouter/auto",
            estimated_or_cost=0.0012,
            cost_estimate_confidence_percent=84,
        )

        result = dispatcher.prompt_summary(args, workflow_id="TASK-SPEC19-4-PROMPT")

        self.assertEqual(result["choice_1"], "Codex")
        self.assertEqual(result["choice_2"], "OR")
        self.assertIn("OpenRouter patch proposal flow", result["delegated_meaning"])

    def test_dispatcher_prompt_summary_uses_configured_quickchange_model_when_missing(self) -> None:
        args = Namespace(
            task_class="quickchange_patch_review",
            task_label="Tiny quickchange gate wording",
            normal_target_model="5.4",
            selected_or_model=None,
            estimated_or_cost=0.0012,
            cost_estimate_confidence_percent=84,
        )

        result = dispatcher.prompt_summary(args, workflow_id="TASK-SPEC19-4-PROMPT-DEFAULT")

        self.assertEqual(result["selected_or_model"], "qwen/qwen3-coder-30b-a3b-instruct")

    def test_helper_main_live_mode_writes_live_operator_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            prompt_path = temp_path / "prompt.md"
            prompt_path.write_text("bounded quickchange live operator test\n", encoding="utf-8")
            run_dir = temp_path / "run"

            original_build_run_dir = runner.build_run_dir
            original_invoke_live_run = runner.invoke_live_run
            original_argv = sys.argv[:]
            self.addCleanup(setattr, runner, "build_run_dir", original_build_run_dir)
            self.addCleanup(setattr, runner, "invoke_live_run", original_invoke_live_run)
            self.addCleanup(setattr, sys, "argv", original_argv)

            runner.build_run_dir = lambda workflow_id: run_dir

            def fake_invoke_live_run(**kwargs):
                kwargs["run_directory"].mkdir(parents=True, exist_ok=True)
                (kwargs["run_directory"] / "summary.json").write_text(
                    json.dumps({"status": "PASS"}, indent=2) + "\n",
                    encoding="utf-8",
                )
                (kwargs["run_directory"] / "validation_summary.json").write_text(
                    json.dumps(
                        {
                            "allowlist_ok": True,
                            "touched_file_cap_ok": True,
                            "delete_rename_move_ok": True,
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                class Completed:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                return Completed()

            runner.invoke_live_run = fake_invoke_live_run
            sys.argv = [
                "quickchange_sidecar_write_pilot_runner.py",
                "--task-label",
                "BACKLOG-112 evidence delta",
                "--normal-target-model",
                "5.4",
                "--operator-choice",
                "openrouter",
                "--prompt-path",
                str(prompt_path),
                "--workflow-id",
                "BACKLOG-112-LIVE-EVIDENCE-TEST",
                "--editable-path",
                "frontend/index.html",
                "--execute-live",
            ]

            stdout_buffer = io.StringIO()
            with contextlib.redirect_stdout(stdout_buffer):
                exit_code = runner.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["selected_path"], "sidecar_workspace_write_live")
            self.assertEqual(operator_summary["validation_result"], "PASS")
            self.assertEqual(operator_summary["final_outcome"], "LIVE_WRITE_ACCEPTED")
            self.assertTrue(operator_summary["allowlist_ok"])
            self.assertTrue(operator_summary["touched_file_cap_ok"])
            self.assertTrue(operator_summary["delete_rename_move_ok"])

    def test_dispatcher_delegated_quickchange_path_forwards_execute_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt_path = Path(temp_dir) / "prompt.md"
            prompt_path.write_text("dispatcher quickchange path evidence\n", encoding="utf-8")
            captured: dict[str, object] = {}

            def fake_run_command(command: list[str]):
                captured["command"] = command

                class Completed:
                    returncode = 0
                    stdout = json.dumps(
                        {
                            "summary_header": "CODEX SIDECAR WRITE RESULT",
                            "workflow_id": "BACKLOG-112-DISPATCH-EVIDENCE",
                            "selected_path": "sidecar_workspace_write_live",
                            "validation_result": "PASS",
                            "final_outcome": "LIVE_WRITE_ACCEPTED",
                        }
                    )
                    stderr = ""

                return Completed()

            original = dispatcher.run_command
            dispatcher.run_command = fake_run_command
            self.addCleanup(setattr, dispatcher, "run_command", original)

            args = Namespace(
                task_label="BACKLOG-112 evidence delta",
                normal_target_model="5.4",
                prompt_path=prompt_path,
                editable_path=["frontend/index.html"],
                max_touched_files=1,
                structured_review_flow=False,
                structured_review_source_run_dir=None,
            )
            result = dispatcher.invoke_quickchange_patch_review(
                args,
                workflow_id="BACKLOG-112-DISPATCH-EVIDENCE",
            )

            self.assertEqual(result["validation_result"], "PASS")
            self.assertEqual(result["final_outcome"], "LIVE_WRITE_ACCEPTED")
            command = captured["command"]
            self.assertIn("--execute-live", command)
            self.assertIn("--editable-path", command)
            self.assertIn("frontend/index.html", command)


if __name__ == "__main__":
    unittest.main()
