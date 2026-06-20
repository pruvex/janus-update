from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "codex_bounded_delegation_dispatcher.py"
)
SPEC = importlib.util.spec_from_file_location("codex_bounded_delegation_dispatcher", SCRIPT_PATH)
dispatcher = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = dispatcher
SPEC.loader.exec_module(dispatcher)


class AssistiveOrReviewCaptureDispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.original_run_root = dispatcher.RUN_ROOT
        self.original_telemetry_dir = dispatcher.OR_TELEMETRY_DIR
        dispatcher.RUN_ROOT = self.temp_path / "runs"
        dispatcher.OR_TELEMETRY_DIR = self.temp_path / "telemetry"
        self.addCleanup(self._restore_paths)

    def _restore_paths(self) -> None:
        dispatcher.RUN_ROOT = self.original_run_root
        dispatcher.OR_TELEMETRY_DIR = self.original_telemetry_dir

    def _write_json(self, path: Path, payload: dict[str, object]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def _debug_input_payload(self) -> dict[str, object]:
        return {
            "workflow_id": "WF-DEBUG-OR-001",
            "bound_skill_context": "janus-debug",
            "expected_behavior": "One bounded assist-only review should return hypotheses only.",
            "actual_behavior": "The delegated path should stay read-only and file-first captured.",
            "evidence_snippets": [
                "bounded request package contains only redacted snippets",
                "Codex still owns local validation afterwards",
            ],
            "iteration_number": 1,
            "explicit_question": "What is the next local verifier?",
            "redaction_ready": True,
            "failure_code": "RUNNER_ARTIFACT_MISMATCH",
        }

    def _triage_input_payload(self) -> dict[str, object]:
        return {
            "workflow_id": "WF-TRIAGE-OR-001",
            "bound_skill_context": "janus-test-pipeline",
            "test_run_id": "TEST-RUN-2026-06-20-777",
            "result_outcome_summary": "Generator boundary failed before a product assertion was classified.",
            "evidence_snippets": [
                "artifact bundle is redacted and bounded",
                "no raw file paths leave the local review package",
            ],
            "classification_question": "Is this an infra blocker or test bug?",
            "redaction_ready": True,
            "candidate_blocker_category": "infra_or_harness",
        }

    def _fixture_response(
        self,
        *,
        model_result: dict[str, object],
        include_usage: bool = True,
        finish_reason: str = "stop",
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": "gen_assistive_fixture_001",
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

    def _debug_args(self, input_path: Path, fixture_path: Path) -> Namespace:
        return Namespace(
            task_label="Debug review",
            normal_target_model="5.4 medium",
            selected_or_model="qwen/qwen3.5-flash-02-23",
            estimated_or_cost=0.0004,
            cost_estimate_confidence_percent=82.0,
            use_local_or_fixture=True,
            execute_direct_or=False,
            or_local_fixture_response_path=fixture_path,
            debug_input_package=input_path,
            test_triage_input_package=None,
        )

    def _triage_args(self, input_path: Path, fixture_path: Path) -> Namespace:
        return Namespace(
            task_label="Triage review",
            normal_target_model="5.4 medium",
            selected_or_model="openai/gpt-oss-20b",
            estimated_or_cost=0.0003,
            cost_estimate_confidence_percent=79.0,
            use_local_or_fixture=True,
            execute_direct_or=False,
            or_local_fixture_response_path=fixture_path,
            debug_input_package=None,
            test_triage_input_package=input_path,
        )

    def test_debug_review_direct_or_fixture_creates_capture_and_telemetry(self) -> None:
        input_path = self._write_json(self.temp_path / "debug_input.json", self._debug_input_payload())
        fixture_path = self._write_json(
            self.temp_path / "debug_response.json",
            self._fixture_response(
                model_result=json.loads(
                    (
                        Path(__file__).resolve().parents[1]
                        / "debug-review-fixtures"
                        / "debug_hypothesis_fixture_result_2026-06-14.json"
                    ).read_text(encoding="utf-8")
                )
            ),
        )

        result = dispatcher.invoke_debug_hypothesis_review(
            self._debug_args(input_path, fixture_path),
            "WF-DEBUG-DIRECT-OR-001",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION")
        self.assertEqual(result["healthcheck_status"], "PASS")
        self.assertAlmostEqual(result["actual_or_cost"], 0.00045678)
        self.assertTrue(Path(result["response_body_path"]).exists())
        self.assertTrue(Path(result["response_summary_path"]).exists())
        self.assertTrue(Path(result["telemetry_jsonl_path"]).exists())
        healthcheck_summary = json.loads(Path(result["healthcheck_summary_path"]).read_text(encoding="utf-8"))
        self.assertEqual(healthcheck_summary["or_telemetry"]["record_count"], 1)
        telemetry_row = json.loads(Path(result["telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(telemetry_row["skill_id"], "debug_hypothesis_review")
        self.assertEqual(telemetry_row["validation_result"], "PASS")

    def test_triage_review_direct_or_missing_usage_rejects_but_still_ingests_healthcheck(self) -> None:
        input_path = self._write_json(self.temp_path / "triage_input.json", self._triage_input_payload())
        fixture_path = self._write_json(
            self.temp_path / "triage_response.json",
            self._fixture_response(
                model_result=json.loads(
                    (
                        Path(__file__).resolve().parents[1]
                        / "test-triage-fixtures"
                        / "test_result_triage_fixture_result_2026-06-14.json"
                    ).read_text(encoding="utf-8")
                ),
                include_usage=False,
            ),
        )

        result = dispatcher.invoke_test_result_triage_review(
            self._triage_args(input_path, fixture_path),
            "WF-TRIAGE-DIRECT-OR-001",
        )

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["final_outcome"], "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK")
        self.assertEqual(result["fallback_used"], "YES")
        self.assertEqual(result["healthcheck_status"], "PASS")
        validation_summary = json.loads(Path(result["validation_summary_path"]).read_text(encoding="utf-8"))
        self.assertIn("usage missing", validation_summary["telemetry_issues"])
        telemetry_row = json.loads(Path(result["telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(telemetry_row["validation_result"], "FAIL")
        self.assertEqual(telemetry_row["usage_source"], "fallback_estimate")

    def test_debug_review_wrapper_failure_still_persists_one_rejected_telemetry_row(self) -> None:
        input_path = self._write_json(self.temp_path / "debug_input_wrapper_fail.json", self._debug_input_payload())
        fixture_path = self._write_json(
            self.temp_path / "debug_response_wrapper_fail.json",
            self._fixture_response(model_result={"status": "PASS"}),
        )

        with mock.patch.object(
            dispatcher,
            "invoke_file_first_wrapper",
            return_value=subprocess.CompletedProcess(
                args=["powershell"],
                returncode=1,
                stdout="wrapper failed",
                stderr="simulated wrapper failure",
            ),
        ):
            result = dispatcher.invoke_debug_hypothesis_review(
                self._debug_args(input_path, fixture_path),
                "WF-DEBUG-WRAPPER-FAIL-001",
            )

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["healthcheck_status"], "SKIPPED")
        telemetry_row = json.loads(Path(result["telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(telemetry_row["selected_path"], "abort_post_wrapper")
        self.assertEqual(telemetry_row["validation_result"], "FAIL")
        self.assertEqual(telemetry_row["final_outcome"], "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK")

    def test_debug_review_healthcheck_failure_finalizes_persisted_row_to_fail(self) -> None:
        input_path = self._write_json(self.temp_path / "debug_input_healthcheck_fail.json", self._debug_input_payload())
        fixture_path = self._write_json(
            self.temp_path / "debug_response_healthcheck_fail.json",
            self._fixture_response(
                model_result=json.loads(
                    (
                        Path(__file__).resolve().parents[1]
                        / "debug-review-fixtures"
                        / "debug_hypothesis_fixture_result_2026-06-14.json"
                    ).read_text(encoding="utf-8")
                )
            ),
        )

        with mock.patch.object(dispatcher, "run_healthcheck", side_effect=RuntimeError("simulated healthcheck failure")):
            result = dispatcher.invoke_debug_hypothesis_review(
                self._debug_args(input_path, fixture_path),
                "WF-DEBUG-HEALTHCHECK-FAIL-001",
            )

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["healthcheck_status"], "FAIL")
        telemetry_row = json.loads(Path(result["telemetry_jsonl_path"]).read_text(encoding="utf-8").strip())
        self.assertEqual(telemetry_row["selected_path"], "abort_post_healthcheck")
        self.assertEqual(telemetry_row["validation_result"], "FAIL")
        self.assertEqual(telemetry_row["recommendation_signal"], "CODEX_PREFERRED")
        validation_summary = json.loads(Path(result["validation_summary_path"]).read_text(encoding="utf-8"))
        self.assertIn("simulated healthcheck failure", validation_summary["telemetry_issues"])


if __name__ == "__main__":
    unittest.main()
