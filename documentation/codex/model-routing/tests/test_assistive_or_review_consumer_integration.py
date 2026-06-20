from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
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


class AssistiveOrReviewConsumerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_debug_run_root = debug_runner.RUN_ROOT
        self.original_triage_run_root = triage_runner.RUN_ROOT
        debug_runner.RUN_ROOT = self.temp_path / "debug-runs"
        triage_runner.RUN_ROOT = self.temp_path / "triage-runs"
        self.addCleanup(self._restore_run_roots)

    def _restore_run_roots(self) -> None:
        debug_runner.RUN_ROOT = self.original_debug_run_root
        triage_runner.RUN_ROOT = self.original_triage_run_root

    def _write_json(self, path: Path, payload: dict[str, object]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

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
            prompt_summary=lambda args, workflow_id: {
                "workflow_id": workflow_id,
                "task_class": args.task_class,
                "selected_path": "operator_choice_pending",
                "final_outcome": "AWAITING_OPERATOR_CHOICE",
                "validation_result": "PASS",
            },
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
            )

        self.assertEqual(result["task_class"], "debug_hypothesis_review")
        self.assertEqual(result["codex_owned_outcome_status"], "AWAITING_OPERATOR_CHOICE")
        prompt_path = debug_runner.build_run_dir("WF-DEBUG-PROMPT-001") / "consumer_operator_choice_prompt.json"
        self.assertTrue(prompt_path.exists())

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

    def test_debug_delegated_consumer_writes_package_before_dispatcher_invocation(self) -> None:
        fixture_path = self._write_json(self.temp_path / "debug_fixture.json", {"status": "PASS"})
        captured: dict[str, object] = {}

        def fake_invoke(args, workflow_id):
            captured["workflow_id"] = workflow_id
            captured["task_class"] = args.task_class
            captured["debug_input_package"] = str(args.debug_input_package)
            captured["debug_fixture_result"] = str(args.debug_fixture_result)
            captured["use_local_or_fixture"] = args.use_local_or_fixture
            return {
                "workflow_id": workflow_id,
                "selected_path": "delegated_assist_only_hypothesis_review",
                "final_outcome": "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION",
                "validation_result": "PASS",
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
                use_local_or_fixture=True,
            )

        self.assertEqual(result["codex_owned_outcome_status"], "DELEGATED_REVIEW_PENDING_CODEX_DECISION")
        self.assertEqual(captured["task_class"], "debug_hypothesis_review")
        self.assertEqual(captured["use_local_or_fixture"], True)
        package_path = Path(str(captured["debug_input_package"]))
        self.assertTrue(package_path.exists())
        package_payload = json.loads(package_path.read_text(encoding="utf-8"))
        self.assertEqual(package_payload["workflow_id"], "WF-DEBUG-DELEGATED-001")

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


if __name__ == "__main__":
    unittest.main()
