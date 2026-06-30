from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


debug_runner = _load_module(
    "codex_debug_hypothesis_review_runner",
    SCRIPTS_DIR / "codex_debug_hypothesis_review_runner.py",
)
triage_runner = _load_module(
    "codex_test_result_triage_review_runner",
    SCRIPTS_DIR / "codex_test_result_triage_review_runner.py",
)
dispatcher = _load_module(
    "codex_bounded_delegation_dispatcher",
    SCRIPTS_DIR / "codex_bounded_delegation_dispatcher.py",
)


class AssistiveOrReviewConsumerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_debug_run_root = debug_runner.RUN_ROOT
        self.original_triage_run_root = triage_runner.RUN_ROOT
        self.original_dispatcher_run_root = dispatcher.RUN_ROOT
        self.original_dispatcher_telemetry_dir = dispatcher.OR_TELEMETRY_DIR
        debug_runner.RUN_ROOT = self.temp_path / "debug-runs"
        triage_runner.RUN_ROOT = self.temp_path / "triage-runs"
        dispatcher.RUN_ROOT = self.temp_path / "dispatcher-runs"
        dispatcher.OR_TELEMETRY_DIR = self.temp_path / "dispatcher-telemetry"
        self.addCleanup(self._restore_run_roots)

    def _restore_run_roots(self) -> None:
        debug_runner.RUN_ROOT = self.original_debug_run_root
        triage_runner.RUN_ROOT = self.original_triage_run_root
        dispatcher.RUN_ROOT = self.original_dispatcher_run_root
        dispatcher.OR_TELEMETRY_DIR = self.original_dispatcher_telemetry_dir

    def _write_json(self, path: Path, payload: dict[str, object]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def _debug_fixture_response(
        self,
        *,
        finish_reason: str = "stop",
        include_usage: bool = True,
    ) -> dict[str, object]:
        model_result = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "debug-review-fixtures"
                / "debug_hypothesis_fixture_result_2026-06-14.json"
            ).read_text(encoding="utf-8")
        )
        payload: dict[str, object] = {
            "id": "gen_assistive_fixture_consumer_001",
            "model": "qwen/qwen3.5-flash-02-23",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(model_result, ensure_ascii=False),
                    },
                    "finish_reason": finish_reason,
                }
            ],
        }
        if include_usage:
            payload["usage"] = {
                "prompt_tokens": 123,
                "completion_tokens": 345,
                "total_tokens": 468,
                "cost": 0.00045678,
            }
        return payload

    def test_debug_consumer_input_package_matches_allowlist_shape(self) -> None:
        payload = debug_runner.build_consumer_input_package(
            workflow_id="WF-DEBUG-CONSUMER-001",
            bound_skill_context="janus-debug",
            expected_behavior="Codex asks for one bounded review only.",
            actual_behavior="Consumer should build a redacted dispatcher package.",
            evidence_snippets=["snippet one", "snippet two"],
            iteration_number=2,
            explicit_question="Which local verifier should Codex run next?",
            failure_code="RUNNER_ARTIFACT_MISMATCH",
        )

        self.assertEqual(payload["workflow_id"], "WF-DEBUG-CONSUMER-001")
        self.assertEqual(payload["redaction_ready"], True)
        self.assertEqual(payload["failure_code"], "RUNNER_ARTIFACT_MISMATCH")
        self.assertNotIn("changed_files", payload)

    def test_triage_consumer_input_package_matches_allowlist_shape(self) -> None:
        payload = triage_runner.build_consumer_input_package(
            workflow_id="WF-TRIAGE-CONSUMER-001",
            bound_skill_context="janus-test-pipeline",
            test_run_id="TEST-RUN-001",
            result_outcome_summary="One bounded triage slice only.",
            evidence_snippets=["snippet one"],
            classification_question="Infra blocker or test bug?",
            candidate_blocker_category="infra_or_harness",
        )

        self.assertEqual(payload["test_run_id"], "TEST-RUN-001")
        self.assertEqual(payload["candidate_blocker_category"], "infra_or_harness")
        self.assertEqual(payload["redaction_ready"], True)
        self.assertNotIn("test_result_path", payload)

    def test_debug_prompt_consumer_uses_dispatcher_gate_and_persists_summary(self) -> None:
        fake_dispatcher = types.SimpleNamespace(
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "AWAITING_OPERATOR_CHOICE"},
        )

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = debug_runner.run_consumer_flow(
                workflow_id="WF-DEBUG-PROMPT-001",
                task_label="Debug prompt",
                normal_target_model="5.4 medium",
                operator_choice="prompt",
                delegated_model_label="qwen/qwen3.5-flash-02-23",
                estimated_or_cost=0.0004,
                cost_estimate_confidence_percent=81.0,
                input_payload=debug_runner.build_consumer_input_package(
                    workflow_id="WF-DEBUG-PROMPT-001",
                    bound_skill_context="janus-debug",
                    expected_behavior="Codex may offer one bounded debug review gate.",
                    actual_behavior="Consumer should expose the operator choice only for an eligible package.",
                    evidence_snippets=["snippet one"],
                    iteration_number=1,
                    explicit_question="Which local verifier should Codex run next?",
                ),
            )

        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["eligibility_result"], "OR_ALLOWED")
        self.assertEqual(result["codex_owned_outcome_status"], "AWAITING_OPERATOR_CHOICE")
        prompt_path = debug_runner.build_run_dir("WF-DEBUG-PROMPT-001") / "consumer_operator_choice_prompt.json"
        self.assertTrue(prompt_path.exists())

    def test_debug_prompt_consumer_skips_gate_when_no_bounded_package_exists(self) -> None:
        fake_dispatcher = types.SimpleNamespace(
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "CODEX_LOCAL_PATH"},
        )

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = debug_runner.run_consumer_flow(
                workflow_id="WF-DEBUG-PROMPT-002",
                task_label="Debug prompt missing package",
                normal_target_model="5.4 medium",
                operator_choice="prompt",
                delegated_model_label="qwen/qwen3.5-flash-02-23",
                estimated_or_cost=0.0004,
                cost_estimate_confidence_percent=81.0,
            )

        self.assertEqual(result["selected_path"], "codex_only_pre_gate")
        self.assertEqual(result["eligibility_reason_code"], "DEBUG_PACKAGE_REQUIRED")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["codex_owned_outcome_status"], "CODEX_LOCAL_PATH")

    def test_triage_local_consumer_uses_dispatcher_gate_and_persists_summary(self) -> None:
        fake_dispatcher = types.SimpleNamespace(
            local_summary=lambda args, workflow_id: {
                "workflow_id": workflow_id,
                "task_class": args.task_class,
                "selected_path": "codex_only_operator_choice",
                "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
                "validation_result": "PASS",
            },
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "CODEX_LOCAL_PATH"},
        )

        with mock.patch.object(triage_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = triage_runner.run_consumer_flow(
                workflow_id="WF-TRIAGE-LOCAL-001",
                task_label="Triage local",
                normal_target_model="5.4 medium",
                operator_choice="local",
                delegated_model_label="openai/gpt-oss-20b",
            )

        self.assertEqual(result["task_class"], "test_result_triage_review")
        self.assertEqual(result["codex_owned_outcome_status"], "CODEX_LOCAL_PATH")
        local_path = triage_runner.build_run_dir("WF-TRIAGE-LOCAL-001") / "consumer_operator_choice_local.json"
        self.assertTrue(local_path.exists())

    def test_triage_prompt_consumer_blocks_or_when_roi_is_negative(self) -> None:
        fake_dispatcher = types.SimpleNamespace(
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "CODEX_LOCAL_PATH"},
        )

        with mock.patch.object(triage_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = triage_runner.run_consumer_flow(
                workflow_id="WF-TRIAGE-ROI-NEG-001",
                task_label="Triage ROI negative",
                normal_target_model="5.4 medium",
                operator_choice="prompt",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.0003,
                cost_estimate_confidence_percent=80.0,
                estimated_codex_saved_tokens=800,
                estimated_codex_or_overhead_tokens=1200,
                minimum_net_codex_saved_tokens=250,
                input_payload=triage_runner.build_consumer_input_package(
                    workflow_id="WF-TRIAGE-ROI-NEG-001",
                    bound_skill_context="janus-test-pipeline",
                    test_run_id="TEST-RUN-ROI-NEG",
                    result_outcome_summary="One bounded triage slice only.",
                    evidence_snippets=["snippet one"],
                    classification_question="Infra or product bug?",
                ),
            )

        self.assertEqual(result["selected_path"], "codex_only_or_roi_gate")
        self.assertEqual(result["final_outcome"], "LOCAL_CODEX_PATH_SELECTED")
        self.assertEqual(result["or_roi"]["status"], "NEGATIVE")
        self.assertEqual(result["codex_owned_outcome_status"], "CODEX_LOCAL_PATH")

    def test_triage_prompt_consumer_shows_or_when_roi_is_positive(self) -> None:
        fake_dispatcher = types.SimpleNamespace(
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "AWAITING_OPERATOR_CHOICE"},
        )

        with mock.patch.object(triage_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = triage_runner.run_consumer_flow(
                workflow_id="WF-TRIAGE-ROI-POS-001",
                task_label="Triage ROI positive",
                normal_target_model="5.4 medium",
                operator_choice="prompt",
                delegated_model_label="qwen/qwen3-coder-30b-a3b-instruct",
                estimated_or_cost=0.0003,
                cost_estimate_confidence_percent=80.0,
                estimated_codex_saved_tokens=3000,
                estimated_codex_or_overhead_tokens=900,
                minimum_net_codex_saved_tokens=500,
                input_payload=triage_runner.build_consumer_input_package(
                    workflow_id="WF-TRIAGE-ROI-POS-001",
                    bound_skill_context="janus-test-pipeline",
                    test_run_id="TEST-RUN-ROI-POS",
                    result_outcome_summary="One bounded triage slice only.",
                    evidence_snippets=["snippet one"],
                    classification_question="Infra or product bug?",
                ),
            )

        self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
        self.assertEqual(result["choice_2"], "OR")
        self.assertEqual(result["or_roi"]["status"], "POSITIVE")
        self.assertEqual(result["codex_owned_outcome_status"], "AWAITING_OPERATOR_CHOICE")

    def test_debug_delegated_consumer_writes_package_before_dispatcher_invocation(self) -> None:
        fixture_path = self._write_json(self.temp_path / "debug_fixture.json", {"status": "PASS"})
        captured: dict[str, object] = {}

        def fake_invoke(args, workflow_id):
            captured["workflow_id"] = workflow_id
            captured["task_class"] = args.task_class
            captured["debug_input_package"] = str(args.debug_input_package)
            captured["debug_fixture_result"] = str(args.debug_fixture_result)
            return {
                "workflow_id": workflow_id,
                "selected_path": "delegated_assist_only_hypothesis_review",
                "final_outcome": "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION",
                "validation_result": "PASS",
                "fallback_used": "NO",
                "rework_required": "NO",
            }

        fake_dispatcher = types.SimpleNamespace(
            invoke_debug_hypothesis_review=fake_invoke,
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "DELEGATED_REVIEW_PENDING_CODEX_DECISION"},
        )

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = debug_runner.run_consumer_flow(
                workflow_id="WF-DEBUG-DELEGATED-001",
                task_label="Debug delegated",
                normal_target_model="5.4 medium",
                operator_choice="delegated",
                delegated_model_label="qwen/qwen3.5-flash-02-23",
                estimated_or_cost=0.0004,
                cost_estimate_confidence_percent=81.0,
                input_payload=debug_runner.build_consumer_input_package(
                    workflow_id="WF-DEBUG-DELEGATED-001",
                    bound_skill_context="janus-debug",
                    expected_behavior="One bounded hypothesis review only.",
                    actual_behavior="Consumer should write package before dispatch.",
                    evidence_snippets=["snippet one"],
                    iteration_number=1,
                    explicit_question="What verifier next?",
                ),
                fixture_result_json=fixture_path,
            )

        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REVIEW_PENDING_CODEX_DECISION")
        self.assertEqual(result["selected_path"], "delegated_assist_only_hypothesis_review")
        self.assertEqual(result["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(captured["task_class"], "debug_hypothesis_review")
        package_path = Path(str(captured["debug_input_package"]))
        self.assertTrue(package_path.exists())
        package_payload = json.loads(package_path.read_text(encoding="utf-8"))
        self.assertEqual(package_payload["workflow_id"], "WF-DEBUG-DELEGATED-001")
        self.assertEqual(captured["debug_fixture_result"], str(fixture_path))

    def test_debug_delegated_consumer_surfaces_visible_codex_fallback_on_failed_review(self) -> None:
        fixture_path = self._write_json(self.temp_path / "debug_failed_fixture.json", {"status": "WEAK_SIGNAL"})

        fake_dispatcher = types.SimpleNamespace(
            invoke_debug_hypothesis_review=lambda args, workflow_id: {
                "workflow_id": workflow_id,
                "selected_path": "abort_post_healthcheck",
                "final_outcome": "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK",
                "validation_result": "FAIL",
                "fallback_used": "YES",
                "rework_required": "YES",
                "operator_message": "Fallback to Codex-only debug is required.",
            },
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "DELEGATED_REJECT_AND_FALLBACK"},
        )

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = debug_runner.run_consumer_flow(
                workflow_id="WF-DEBUG-DELEGATED-FAIL-001",
                task_label="Debug delegated fallback",
                normal_target_model="5.4 medium",
                operator_choice="delegated",
                delegated_model_label="qwen/qwen3.5-flash-02-23",
                estimated_or_cost=0.0004,
                cost_estimate_confidence_percent=81.0,
                input_payload=debug_runner.build_consumer_input_package(
                    workflow_id="WF-DEBUG-DELEGATED-FAIL-001",
                    bound_skill_context="janus-debug",
                    expected_behavior="One bounded hypothesis review only.",
                    actual_behavior="Failed delegated review must fall back visibly to Codex.",
                    evidence_snippets=["snippet one"],
                    iteration_number=2,
                    explicit_question="What verifier next?",
                ),
                fixture_result_json=fixture_path,
            )

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK")
        self.assertEqual(result["fallback_used"], "YES")
        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REJECT_AND_FALLBACK")

    def test_debug_delegated_consumer_without_runtime_mode_falls_back_before_dispatch(self) -> None:
        fake_dispatcher = types.SimpleNamespace(
            invoke_debug_hypothesis_review=lambda args, workflow_id: self.fail("delegated dispatcher should not be invoked"),
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "DELEGATED_REJECT_AND_FALLBACK"},
        )

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = debug_runner.run_consumer_flow(
                workflow_id="WF-DEBUG-DELEGATED-NO-MODE-001",
                task_label="Debug delegated no mode",
                normal_target_model="5.4 medium",
                operator_choice="delegated",
                delegated_model_label="qwen/qwen3.5-flash-02-23",
                estimated_or_cost=0.0004,
                cost_estimate_confidence_percent=81.0,
                input_payload=debug_runner.build_consumer_input_package(
                    workflow_id="WF-DEBUG-DELEGATED-NO-MODE-001",
                    bound_skill_context="janus-debug",
                    expected_behavior="Delegated flow should require one explicit runtime mode.",
                    actual_behavior="No fixture or live mode should fall back locally before dispatch.",
                    evidence_snippets=["snippet one"],
                    iteration_number=1,
                    explicit_question="What verifier next?",
                ),
            )

        self.assertEqual(result["selected_path"], "codex_local_fallback_missing_delegated_runtime_mode")
        self.assertEqual(result["delegated_runtime_reason_code"], "DELEGATED_RUNTIME_MODE_REQUIRED")
        self.assertEqual(result["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK")
        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REJECT_AND_FALLBACK")

    def test_debug_delegated_consumer_fixture_uses_real_dispatcher_without_self_spawn(self) -> None:
        fixture_path = self._write_json(
            self.temp_path / "debug_real_dispatcher_fixture.json",
            self._debug_fixture_response(),
        )
        original_run_command = dispatcher.run_command
        commands: list[list[str]] = []

        def recording_run_command(command: list[str]):
            commands.append(command)
            if len(command) > 1 and Path(command[1]).resolve() == dispatcher.DEBUG_REVIEW_RUNNER.resolve():
                self.fail("consumer fixture path must not spawn the debug runner as a child process")
            return original_run_command(command)

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=dispatcher):
            with mock.patch.object(dispatcher, "run_command", side_effect=recording_run_command):
                result = debug_runner.run_consumer_flow(
                    workflow_id="WF-DEBUG-DELEGATED-REAL-001",
                    task_label="Debug delegated real dispatcher",
                    normal_target_model="5.4 medium",
                    operator_choice="delegated",
                    delegated_model_label="qwen/qwen3.5-flash-02-23",
                    estimated_or_cost=0.0004,
                    cost_estimate_confidence_percent=81.0,
                    input_payload=debug_runner.build_consumer_input_package(
                        workflow_id="WF-DEBUG-DELEGATED-REAL-001",
                        bound_skill_context="janus-debug",
                        expected_behavior="Exactly one bounded fixture-backed review should run through the shared dispatcher.",
                        actual_behavior="The consumer should resolve fixture mode and avoid self-recursion.",
                        evidence_snippets=["snippet one"],
                        iteration_number=1,
                        explicit_question="What verifier next?",
                    ),
                    fixture_result_json=fixture_path,
                )

        self.assertEqual(result["selected_path"], "delegated_assist_only_hypothesis_review")
        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertTrue(Path(result["response_summary_path"]).exists())
        self.assertTrue(Path(result["telemetry_jsonl_path"]).exists())
        self.assertGreaterEqual(len(commands), 2)

    def test_debug_productive_gate_rejects_other_debug_modes(self) -> None:
        result = debug_runner.evaluate_productive_gate(
            estimated_or_cost=0.0004,
            input_payload=debug_runner.build_consumer_input_package(
                workflow_id="WF-DEBUG-MODE-001",
                bound_skill_context="janus-debug",
                expected_behavior="No unrelated debug mode should gain a productive OR gate.",
                actual_behavior="Regression guard for out-of-scope task class.",
                evidence_snippets=["snippet one"],
                iteration_number=1,
                explicit_question="What verifier next?",
            ),
            task_class="debug_patch_apply",
        )

        self.assertEqual(result["eligibility_result"], "OR_NOT_ELIGIBLE")
        self.assertEqual(result["reason_code"], "DEBUG_MODE_NOT_ALLOWED")

    def test_triage_delegated_consumer_writes_package_before_dispatcher_invocation(self) -> None:
        fixture_path = self._write_json(self.temp_path / "triage_fixture.json", {"status": "PASS"})
        captured: dict[str, object] = {}

        def fake_invoke(args, workflow_id):
            captured["workflow_id"] = workflow_id
            captured["task_class"] = args.task_class
            captured["test_triage_input_package"] = str(args.test_triage_input_package)
            captured["test_triage_fixture_result"] = str(args.test_triage_fixture_result)
            return {
                "workflow_id": workflow_id,
                "selected_path": "delegated_assist_only_test_result_triage_review",
                "final_outcome": "TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION",
                "validation_result": "PASS",
            }

        fake_dispatcher = types.SimpleNamespace(
            invoke_test_result_triage_review=fake_invoke,
            with_codex_owned_outcome=lambda result: {**result, "codex_owned_outcome_status": "DELEGATED_REVIEW_PENDING_CODEX_DECISION"},
        )

        with mock.patch.object(triage_runner, "_load_dispatcher_module", return_value=fake_dispatcher):
            result = triage_runner.run_consumer_flow(
                workflow_id="WF-TRIAGE-DELEGATED-001",
                task_label="Triage delegated",
                normal_target_model="5.4 medium",
                operator_choice="2",
                delegated_model_label="openai/gpt-oss-20b",
                estimated_or_cost=0.0003,
                cost_estimate_confidence_percent=80.0,
                estimated_codex_saved_tokens=2500,
                estimated_codex_or_overhead_tokens=900,
                minimum_net_codex_saved_tokens=500,
                input_payload=triage_runner.build_consumer_input_package(
                    workflow_id="WF-TRIAGE-DELEGATED-001",
                    bound_skill_context="janus-test-pipeline",
                    test_run_id="TEST-RUN-777",
                    result_outcome_summary="One bounded triage slice only.",
                    evidence_snippets=["snippet one"],
                    classification_question="Infra or test bug?",
                ),
                fixture_result_json=fixture_path,
            )

        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REVIEW_PENDING_CODEX_DECISION")
        self.assertEqual(captured["task_class"], "test_result_triage_review")
        package_path = Path(str(captured["test_triage_input_package"]))
        self.assertTrue(package_path.exists())
        package_payload = json.loads(package_path.read_text(encoding="utf-8"))
        self.assertEqual(package_payload["test_run_id"], "TEST-RUN-777")

    def test_debug_cli_prompt_requires_productive_gate_package(self) -> None:
        stdout = io.StringIO()
        argv = [
            "codex_debug_hypothesis_review_runner.py",
            "--task-label",
            "Debug prompt CLI",
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "prompt",
            "--workflow-id",
            "WF-DEBUG-CLI-PROMPT-001",
            "--delegated-model-label",
            "qwen/qwen3.5-flash-02-23",
            "--estimated-or-cost",
            "0.0004",
            "--cost-estimate-confidence-percent",
            "81",
        ]

        with mock.patch.object(sys, "argv", argv):
            with redirect_stdout(stdout):
                exit_code = debug_runner.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["selected_path"], "codex_only_pre_gate")
        self.assertEqual(payload["eligibility_reason_code"], "DEBUG_PACKAGE_REQUIRED")

    def test_debug_cli_delegated_fixture_executes_bounded_review_path_without_self_spawn(self) -> None:
        input_path = self._write_json(
            self.temp_path / "debug_input.json",
            debug_runner.build_consumer_input_package(
                workflow_id="WF-DEBUG-CLI-DELEGATED-001",
                bound_skill_context="janus-debug",
                expected_behavior="One bounded hypothesis review only.",
                actual_behavior="CLI delegated selection should execute the bounded review path.",
                evidence_snippets=["snippet one"],
                iteration_number=1,
                explicit_question="What verifier next?",
            ),
        )
        fixture_path = self._write_json(
            self.temp_path / "debug_cli_fixture_response.json",
            self._debug_fixture_response(),
        )
        stdout = io.StringIO()
        original_run_command = dispatcher.run_command
        commands: list[list[str]] = []

        def recording_run_command(command: list[str]):
            commands.append(command)
            if len(command) > 1 and Path(command[1]).resolve() == dispatcher.DEBUG_REVIEW_RUNNER.resolve():
                self.fail("CLI delegated fixture path must not spawn the debug runner as a child process")
            return original_run_command(command)

        argv = [
            "codex_debug_hypothesis_review_runner.py",
            "--task-label",
            "Debug delegated CLI",
            "--normal-target-model",
            "5.4 medium",
            "--operator-choice",
            "delegated",
            "--workflow-id",
            "WF-DEBUG-CLI-DELEGATED-001",
            "--delegated-model-label",
            "qwen/qwen3.5-flash-02-23",
            "--estimated-or-cost",
            "0.0004",
            "--cost-estimate-confidence-percent",
            "81",
            "--input-package-json",
            str(input_path),
            "--fixture-result-json",
            str(fixture_path),
        ]

        with mock.patch.object(debug_runner, "_load_dispatcher_module", return_value=dispatcher):
            with mock.patch.object(dispatcher, "run_command", side_effect=recording_run_command):
                with mock.patch.object(sys, "argv", argv):
                    with redirect_stdout(stdout):
                        exit_code = debug_runner.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["selected_path"], "delegated_assist_only_hypothesis_review")
        self.assertEqual(payload["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(payload["codex_owned_outcome_status"], "DELEGATED_REVIEW_PENDING_CODEX_DECISION")
        self.assertTrue(Path(payload["response_summary_path"]).exists())
        self.assertGreaterEqual(len(commands), 2)


if __name__ == "__main__":
    unittest.main()
