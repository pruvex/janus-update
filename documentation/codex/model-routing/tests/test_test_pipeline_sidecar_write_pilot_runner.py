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

    def test_live_test_execution_prompt_summary_shows_visible_gate_for_eligible_local_retest(self) -> None:
        summary = MODULE.prompt_summary(
            workflow_id="WF-LIVE-TEST-001",
            testspec_path="documentation/TEST_SPEC/example.md",
            test_run_id="TEST-RUN-2026-07-01-201",
            normal_target_model="5.4 medium",
            sidecar_model="moonshotai/kimi-k2.5",
            editable_paths=[],
            node_executable=r"C:\nvm4w\nodejs\node.exe",
            mode="LIVE_TEST_EXECUTION",
            live_test_scope="local_bounded_retest",
        )

        self.assertEqual(summary["mode"], "LIVE_TEST_EXECUTION")
        self.assertEqual(summary["choice_1"], "Codex")
        self.assertEqual(summary["choice_2"], "OR")
        self.assertEqual(summary["eligibility"]["eligibility_result"], "OR_ALLOWED")
        self.assertIn("2 = OR", summary["operator_prompt_lines"])

    def test_live_test_execution_prompt_summary_hides_or_for_non_eligible_slice(self) -> None:
        summary = MODULE.prompt_summary(
            workflow_id="WF-LIVE-TEST-002",
            testspec_path="documentation/TEST_SPEC/example.md",
            test_run_id="TEST-RUN-2026-07-01-202",
            normal_target_model="5.4 medium",
            sidecar_model="moonshotai/kimi-k2.5",
            editable_paths=[],
            node_executable=r"C:\nvm4w\nodejs\node.exe",
            mode="LIVE_TEST_EXECUTION",
            live_test_scope="non_local_live_test",
        )

        self.assertEqual(summary["mode"], "LIVE_TEST_EXECUTION")
        self.assertEqual(summary["choice_1"], "Codex")
        self.assertNotIn("choice_2", summary)
        self.assertEqual(summary["eligibility"]["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertFalse(any(line == "2 = OR" for line in summary["operator_prompt_lines"]))

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

    def test_invoke_isolated_aider_runner_can_forward_prompt_choice(self) -> None:
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

        MODULE.invoke_isolated_aider_runner(
            workflow_id="TP-ISO-PROMPT-001",
            task_label="Strong OR test worker",
            normal_target_model="5.4 medium",
            or_model="moonshotai/kimi-k2.5",
            operator_choice="prompt",
            estimated_or_cost=0.02,
            confidence_percent=75,
            input_package_json=Path("C:/tmp/worker_package.json"),
        )

        command = captured["command"]
        self.assertEqual(command[command.index("--operator-choice") + 1], "prompt")
        self.assertIn("moonshotai/kimi-k2.5", command)

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
                "moonshotai/kimi-k2.5",
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
            self.assertEqual(operator_summary["mode"], "STRONG_OR_TEST_WORKER")
            self.assertEqual(operator_summary["testspec_path"], "documentation/TEST_SPEC/example.md")
            self.assertEqual(operator_summary["test_run_id"], "TEST-RUN-2026-06-27-123")
            self.assertIn("isolated_aider_workspace_runner.py", operator_summary["forwarded_runner"])
            self.assertIn("repeat_runs", operator_summary["strong_worker_contract"])

    def test_main_uses_isolated_aider_prompt_path_when_package_is_supplied(self) -> None:
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
                self.assertEqual(kwargs["operator_choice"], "prompt")

                class Completed:
                    returncode = 0
                    stdout = json.dumps(
                        {
                            "summary_header": "ISOLATED AIDER WORKER GATE",
                            "workflow_id": kwargs["workflow_id"],
                            "selected_path": "operator_choice_pending",
                            "validation_result": "PASS",
                            "final_outcome": "AWAITING_OPERATOR_CHOICE",
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
                "TEST-RUN-2026-06-27-124",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "prompt",
                "--workflow-id",
                "TP-ISOLATED-PROMPT-001",
                "--sidecar-model",
                "moonshotai/kimi-k2.5",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["selected_path"], "operator_choice_pending")
            self.assertEqual(operator_summary["mode"], "STRONG_OR_TEST_WORKER")

    def test_main_live_test_execution_rejects_non_eligible_or_choice_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            original_build_run_dir = MODULE.build_run_dir
            original_resolve_node_executable = MODULE.resolve_node_executable
            original_resolve_delegated_node_command = MODULE.resolve_delegated_node_command
            original_argv = sys.argv[:]
            self.addCleanup(setattr, MODULE, "build_run_dir", original_build_run_dir)
            self.addCleanup(setattr, MODULE, "resolve_node_executable", original_resolve_node_executable)
            self.addCleanup(setattr, MODULE, "resolve_delegated_node_command", original_resolve_delegated_node_command)
            self.addCleanup(setattr, sys, "argv", original_argv)

            MODULE.build_run_dir = lambda workflow_id: run_dir
            MODULE.resolve_node_executable = lambda preferred=None: r"C:\nvm4w\nodejs\node.exe"
            MODULE.resolve_delegated_node_command = lambda node_executable: "node"
            sys.argv = [
                "test_pipeline_sidecar_write_pilot_runner.py",
                "--testspec-path",
                "documentation/TEST_SPEC/example.md",
                "--test-run-id",
                "TEST-RUN-2026-07-01-203",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "2",
                "--workflow-id",
                "TP-LIVE-TEST-GATE-001",
                "--mode",
                "LIVE_TEST_EXECUTION",
                "--live-test-scope",
                "non_local_live_test",
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_choice_local.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["mode"], "LIVE_TEST_EXECUTION")
            self.assertEqual(operator_summary["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
            self.assertEqual(operator_summary["codex_owned_outcome_status"], "CODEX_LOCAL_PATH")
            self.assertEqual(operator_summary["review_bundle_validation"]["validation_result"], "NOT_REQUIRED")
            self.assertEqual(operator_summary["eligibility"]["reason_code"], "NON_LOCAL_LIVE_TEST")

    def test_main_live_test_execution_prompt_with_package_names_contract_backed_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "worker_package.json"
            package_path.write_text(
                json.dumps(
                    MODULE.build_live_retest_worker_package(
                        test_run_id="TEST-RUN-2026-07-05-405",
                        evidence_repo_path="documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md",
                    )
                ),
                encoding="utf-8",
            )
            run_dir = temp_path / "run"

            original_build_run_dir = MODULE.build_run_dir
            original_resolve_node_executable = MODULE.resolve_node_executable
            original_resolve_delegated_node_command = MODULE.resolve_delegated_node_command
            original_argv = sys.argv[:]
            self.addCleanup(setattr, MODULE, "build_run_dir", original_build_run_dir)
            self.addCleanup(setattr, MODULE, "resolve_node_executable", original_resolve_node_executable)
            self.addCleanup(setattr, MODULE, "resolve_delegated_node_command", original_resolve_delegated_node_command)
            self.addCleanup(setattr, sys, "argv", original_argv)

            MODULE.build_run_dir = lambda workflow_id: run_dir
            MODULE.resolve_node_executable = lambda preferred=None: r"C:\nvm4w\nodejs\node.exe"
            MODULE.resolve_delegated_node_command = lambda node_executable: "node"
            sys.argv = [
                "test_pipeline_sidecar_write_pilot_runner.py",
                "--testspec-path",
                "documentation/TEST_SPEC/example.md",
                "--test-run-id",
                "TEST-RUN-2026-07-05-405",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "prompt",
                "--workflow-id",
                "TP-LIVE-RETEST-PROMPT-PACKAGE-001",
                "--mode",
                "LIVE_TEST_EXECUTION",
                "--live-test-scope",
                "local_bounded_retest",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_choice_prompt.json").read_text(encoding="utf-8"))
            prompt_text = "\n".join(operator_summary["operator_prompt_lines"] + operator_summary["boundaries"])
            self.assertIn("Bounded Worker-Paket ist vorhanden", prompt_text)
            self.assertIn("Delegation requires a valid bounded worker package", prompt_text)
            self.assertNotIn("No delegated auth, worker, or evidence contract in this slice.", prompt_text)

    def test_live_retest_worker_package_contract_validates_without_secret_material(self) -> None:
        package = MODULE.build_live_retest_worker_package(
            test_run_id="TEST-RUN-2026-07-05-401",
            evidence_repo_path="documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md",
        )

        result = MODULE.validate_live_retest_worker_package_contract(package)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["contract_status"], "LIVE_RETEST_WORKER_PACKAGE_VALID")
        self.assertFalse(MODULE.contains_secret_value(package))

    def test_live_retest_worker_package_contract_rejects_secret_like_value(self) -> None:
        package = MODULE.build_live_retest_worker_package(
            test_run_id="TEST-RUN-2026-07-05-402",
            evidence_repo_path="documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md",
        )
        package["live_retest_contract"]["local_auth"]["versioned_secret_value"] = "Bearer should-not-be-versioned"

        result = MODULE.validate_live_retest_worker_package_contract(package)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertIn("package contains a forbidden secret-like value", result["issues"])

    def test_main_live_test_execution_with_valid_package_forwards_isolated_worker_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "worker_package.json"
            package_path.write_text(
                json.dumps(
                    MODULE.build_live_retest_worker_package(
                        test_run_id="TEST-RUN-2026-07-05-403",
                        evidence_repo_path="documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md",
                    )
                ),
                encoding="utf-8",
            )
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
                self.assertEqual(kwargs["operator_choice"], "delegated")
                self.assertEqual(kwargs["input_package_json"], package_path.resolve())

                class Completed:
                    returncode = 0
                    stdout = json.dumps(
                        {
                            "summary_header": "ISOLATED AIDER WORKER RESULT",
                            "workflow_id": kwargs["workflow_id"],
                            "selected_path": "isolated_aider_temp_workspace_live",
                            "validation_result": "PASS",
                            "final_outcome": "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW",
                            "report_path": "documentation/test-runs/TEST-RUN-2026-07-05-403_RESULT.md",
                            "log_path": "documentation/test-runs/TEST-RUN-2026-07-05-403_CHECKS.log",
                            "copy_back_files": [
                                "documentation/test-runs/TEST-RUN-2026-07-05-403_RESULT.md",
                                "documentation/test-runs/TEST-RUN-2026-07-05-403_RESULT.json",
                            ],
                            "scope_drift_files": [],
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
                "TEST-RUN-2026-07-05-403",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "2",
                "--workflow-id",
                "TP-LIVE-RETEST-WORKER-001",
                "--mode",
                "LIVE_TEST_EXECUTION",
                "--live-test-scope",
                "local_bounded_retest",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["mode"], "LIVE_TEST_EXECUTION")
            self.assertEqual(operator_summary["delegation_mode"], "isolated_aider_workspace")
            self.assertEqual(operator_summary["contract_validation"]["validation_result"], "PASS")
            self.assertTrue(operator_summary["codex_review_required"])
            self.assertEqual(operator_summary["final_outcome"], "LIVE_TEST_EXECUTION_READY_FOR_CODEX_VALIDATION")
            self.assertEqual(operator_summary["selected_path"], "delegated_live_retest_then_codex_review")
            self.assertEqual(operator_summary["codex_owned_outcome_status"], "DELEGATED_REVIEW_PENDING_CODEX_DECISION")
            self.assertEqual(operator_summary["fallback_used"], "NO")
            self.assertEqual(operator_summary["review_bundle_validation"]["validation_result"], "PASS")

    def test_main_live_test_execution_rejects_package_with_secret_material(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package = MODULE.build_live_retest_worker_package(
                test_run_id="TEST-RUN-2026-07-05-404",
                evidence_repo_path="documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md",
            )
            package["task_prompt"] = "Use Bearer should-not-leak"
            package_path = temp_path / "worker_package.json"
            package_path.write_text(json.dumps(package), encoding="utf-8")
            run_dir = temp_path / "run"

            original_build_run_dir = MODULE.build_run_dir
            original_resolve_node_executable = MODULE.resolve_node_executable
            original_resolve_delegated_node_command = MODULE.resolve_delegated_node_command
            original_argv = sys.argv[:]
            self.addCleanup(setattr, MODULE, "build_run_dir", original_build_run_dir)
            self.addCleanup(setattr, MODULE, "resolve_node_executable", original_resolve_node_executable)
            self.addCleanup(setattr, MODULE, "resolve_delegated_node_command", original_resolve_delegated_node_command)
            self.addCleanup(setattr, sys, "argv", original_argv)

            MODULE.build_run_dir = lambda workflow_id: run_dir
            MODULE.resolve_node_executable = lambda preferred=None: r"C:\nvm4w\nodejs\node.exe"
            MODULE.resolve_delegated_node_command = lambda node_executable: "node"
            sys.argv = [
                "test_pipeline_sidecar_write_pilot_runner.py",
                "--testspec-path",
                "documentation/TEST_SPEC/example.md",
                "--test-run-id",
                "TEST-RUN-2026-07-05-404",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "2",
                "--workflow-id",
                "TP-LIVE-RETEST-WORKER-SECRET-001",
                "--mode",
                "LIVE_TEST_EXECUTION",
                "--live-test-scope",
                "local_bounded_retest",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 1)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["final_outcome"], "LIVE_TEST_EXECUTION_REJECT_AND_FALLBACK")
            self.assertEqual(operator_summary["contract_validation"]["validation_result"], "FAIL")
            self.assertEqual(operator_summary["codex_owned_outcome_status"], "DELEGATED_REJECT_AND_FALLBACK")
            self.assertEqual(operator_summary["review_bundle_validation"]["validation_result"], "NOT_REQUIRED")

    def test_main_live_test_execution_fails_closed_when_worker_omits_review_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_path = temp_path / "worker_package.json"
            package_path.write_text(
                json.dumps(
                    MODULE.build_live_retest_worker_package(
                        test_run_id="TEST-RUN-2026-07-05-406",
                        evidence_repo_path="documentation/codex/model-routing/strong-or-fixtures/strong_live_retest_evidence_fixture_2026-07-05.md",
                    )
                ),
                encoding="utf-8",
            )
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
                "TEST-RUN-2026-07-05-406",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "2",
                "--workflow-id",
                "TP-LIVE-RETEST-WORKER-FAIL-CLOSED-001",
                "--mode",
                "LIVE_TEST_EXECUTION",
                "--live-test-scope",
                "local_bounded_retest",
                "--isolated-aider-package-json",
                str(package_path),
            ]

            exit_code = MODULE.main()

            self.assertEqual(exit_code, 1)
            operator_summary = json.loads((run_dir / "operator_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(operator_summary["validation_result"], "FAIL")
            self.assertEqual(operator_summary["final_outcome"], "LIVE_TEST_EXECUTION_REJECT_AND_FALLBACK")
            self.assertEqual(operator_summary["codex_owned_outcome_status"], "DELEGATED_REJECT_AND_FALLBACK")
            self.assertEqual(operator_summary["fallback_used"], "YES")
            self.assertEqual(operator_summary["review_bundle_validation"]["validation_result"], "FAIL")


if __name__ == "__main__":
    unittest.main()
