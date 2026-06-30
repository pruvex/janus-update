import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "test_pipeline_sidecar_write_pilot_runner.py"
)
SPEC = importlib.util.spec_from_file_location(
    "test_pipeline_sidecar_write_pilot_runner",
    SCRIPT_PATH,
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TestTestPipelineSidecarWritePilotRunner(unittest.TestCase):
    def test_prompt_summary_uses_visible_codex_or_gate_language(self) -> None:
        summary = MODULE.prompt_summary(
            workflow_id="WF-TEST-PIPELINE-001",
            testspec_path="documentation/TEST_SPEC/example.md",
            test_run_id="TEST-RUN-2026-06-27-123",
            normal_target_model="5.4 medium",
            sidecar_model="gpt-5.4",
            editable_paths=[
                "documentation/test-runs/TEST-RUN-2026-06-27-123_plan.json",
                "documentation/test-runs/TEST-RUN-2026-06-27-123_generated.spec.js",
                "documentation/test-runs/TEST-RUN-2026-06-27-123_skill2_handover.txt",
            ],
            node_executable=r"C:\nvm4w\nodejs\node.exe",
        )

        self.assertEqual(summary["choice_1"], "Codex")
        self.assertEqual(summary["choice_2"], "OR")
        self.assertIn("1 = Codex", summary["operator_prompt_lines"])
        self.assertIn("2 = OR", summary["operator_prompt_lines"])
        self.assertTrue(
            any("structured local executor" in line for line in summary["operator_prompt_lines"])
        )

    def test_build_structured_generator_request_includes_handover_artifact(self) -> None:
        request = MODULE.build_structured_generator_request(
            workflow_id="WF-TEST-PIPELINE-001",
            testspec_path="documentation/TEST_SPEC/example.md",
            test_run_id="TEST-RUN-2026-06-27-123",
            editable_paths=[
                "documentation/test-runs/TEST-RUN-2026-06-27-123_plan.json",
                "documentation/test-runs/TEST-RUN-2026-06-27-123_generated.spec.js",
                "documentation/test-runs/TEST-RUN-2026-06-27-123_skill2_handover.txt",
            ],
        )

        self.assertEqual(request["action_type"], "run_generator")
        self.assertEqual(request["action_payload"]["generator_id"], "compile_testspec_to_testplan_v1")
        self.assertEqual(len(request["action_payload"]["declared_output_artifacts"]), 3)
        self.assertTrue(
            request["action_payload"]["declared_output_artifacts"][2].endswith("_skill2_handover.txt")
        )

    def test_build_live_prompt_includes_explicit_test_run_id(self) -> None:
        prompt = MODULE.build_live_prompt(
            testspec_path="documentation/TEST_SPEC/example.md",
            test_run_id="TEST-RUN-2026-06-27-123",
            node_executable=r"C:\nvm4w\nodejs\node.exe",
            delegated_node_command="node",
            editable_paths=[
                "documentation/test-runs/TEST-RUN-2026-06-27-123_plan.json",
                "documentation/test-runs/TEST-RUN-2026-06-27-123_generated.spec.js",
            ],
        )
        self.assertIn('--test-run-id "TEST-RUN-2026-06-27-123"', prompt)
        self.assertIn('& "node"', prompt)
        self.assertNotIn('C:\\\\nvm4w\\\\nodejs\\\\node.exe', prompt)

    def test_build_live_prompt_avoids_skill_trigger_language(self) -> None:
        prompt = MODULE.build_live_prompt(
            testspec_path="documentation/TEST_SPEC/example.md",
            test_run_id="TEST-RUN-2026-06-27-123",
            node_executable=r"C:\nvm4w\nodejs\node.exe",
            delegated_node_command="node",
            editable_paths=[
                "documentation/test-runs/TEST-RUN-2026-06-27-123_plan.json",
            ],
        )
        self.assertNotIn("janus-test-pipeline", prompt)
        self.assertNotIn("codex-start-of-work-check", prompt)
        self.assertNotIn("MODEL SWITCH GATE", prompt)
        self.assertIn("Do not perform additional workflow routing", prompt)

    def test_resolve_node_executable_prefers_existing_path(self) -> None:
        node_path = MODULE.resolve_node_executable(r"C:\nvm4w\nodejs\node.exe")
        self.assertTrue(node_path.lower().endswith("node.exe"))

    def test_resolve_delegated_node_command_prefers_runtime_name(self) -> None:
        delegated = MODULE.resolve_delegated_node_command(r"C:\nvm4w\nodejs\node.exe")
        self.assertEqual(delegated, "node")

    def test_parse_touched_files_keeps_renamed_target_path(self) -> None:
        touched = MODULE.parse_touched_files(
            [
                " M documentation/test-runs/TEST-RUN-2026-06-27-123_plan.json",
                "R  old/path.txt -> documentation/test-runs/TEST-RUN-2026-06-27-123_skill2_handover.txt",
            ]
        )
        self.assertEqual(
            touched,
            [
                "documentation/test-runs/TEST-RUN-2026-06-27-123_plan.json",
                "documentation/test-runs/TEST-RUN-2026-06-27-123_skill2_handover.txt",
            ],
        )

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

        original = MODULE.run_command
        MODULE.run_command = fake_run_command
        self.addCleanup(setattr, MODULE, "run_command", original)

        result = MODULE.invoke_isolated_aider_runner(
            workflow_id="TP-ISO-001",
            task_label="Bounded test-artifact worker",
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

            original_build_run_dir = MODULE.build_run_dir
            original_resolve_node_executable = MODULE.resolve_node_executable
            original_resolve_delegated_node_command = MODULE.resolve_delegated_node_command
            original_invoke_isolated = MODULE.invoke_isolated_aider_runner
            original_argv = sys.argv[:]
            self.addCleanup(setattr, MODULE, "build_run_dir", original_build_run_dir)
            self.addCleanup(setattr, MODULE, "resolve_node_executable", original_resolve_node_executable)
            self.addCleanup(setattr, MODULE, "resolve_delegated_node_command", original_resolve_delegated_node_command)
            self.addCleanup(setattr, MODULE, "invoke_isolated_aider_runner", original_invoke_isolated)
            self.addCleanup(setattr, sys, "argv", original_argv)

            MODULE.build_run_dir = lambda workflow_id: run_dir
            MODULE.resolve_node_executable = lambda preferred=None: r"C:\nvm4w\nodejs\node.exe"
            MODULE.resolve_delegated_node_command = lambda node_executable: "node"

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

            MODULE.invoke_isolated_aider_runner = fake_invoke_isolated_aider_runner
            sys.argv = [
                "test_pipeline_sidecar_write_pilot_runner.py",
                "--testspec-path",
                "documentation/TEST_SPEC/example.md",
                "--test-run-id",
                "TEST-RUN-2026-06-27-123",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "2",
                "--workflow-id",
                "TP-ISOLATED-TEST-001",
                "--sidecar-model",
                "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["selected_path"], "isolated_aider_temp_workspace_live")
            self.assertEqual(operator_summary["validation_result"], "PASS")
            self.assertEqual(operator_summary["final_outcome"], "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW")
            self.assertEqual(operator_summary["delegation_mode"], "isolated_aider_workspace")
            self.assertEqual(operator_summary["testspec_path"], "documentation/TEST_SPEC/example.md")
            self.assertEqual(operator_summary["test_run_id"], "TEST-RUN-2026-06-27-123")
            self.assertIn("isolated_aider_workspace_runner.py", operator_summary["forwarded_runner"])


if __name__ == "__main__":
    unittest.main()
