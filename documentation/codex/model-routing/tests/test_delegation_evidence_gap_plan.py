from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


delegation_routing = _load_module("delegation_routing", SCRIPTS_DIR / "delegation_routing.py")
gap_plan = _load_module("delegation_evidence_gap_plan", SCRIPTS_DIR / "delegation_evidence_gap_plan.py")


class DelegationEvidenceGapPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = {
            "lanes": {
                "test_fixture_worker": {"skill": "janus-test-pipeline"},
                "skill_router_review": {"skill": "janus-skill-router"},
                "live_test_execution": {"skill": "janus-test-pipeline"},
                "execution_patch_candidate": {"skill": "janus-executioner"},
                "spec_review": {"skill": "janus-spec-review"},
            }
        }
        self.task_list = {
            "tasks": [
                {
                    "task_id": "TASK-TP-003",
                    "lane_id": "test_fixture_worker",
                    "recommended_backend": "cursor",
                    "pipeline_mode": "TEST_RUN_PRECHECK",
                    "estimated_codex_saved_tokens": 30000,
                    "estimated_delegation_overhead_tokens": 10000,
                },
                {
                    "task_id": "TASK-SR-001",
                    "lane_id": "skill_router_review",
                    "recommended_backend": "openrouter",
                    "pipeline_mode": "SKILL_ROUTER_REVIEW",
                    "estimated_codex_saved_tokens": 12000,
                    "estimated_delegation_overhead_tokens": 4000,
                },
                {
                    "task_id": "TASK-TP-004",
                    "lane_id": "live_test_execution",
                    "recommended_backend": "codex",
                    "pipeline_mode": "LIVE_TEST_EXECUTION",
                },
                {
                    "task_id": "TASK-EX-001",
                    "lane_id": "execution_patch_candidate",
                    "recommended_backend": "cursor",
                    "pipeline_mode": "EXECUTION_PATCH",
                    "estimated_codex_saved_tokens": 35000,
                    "estimated_delegation_overhead_tokens": 10000,
                },
                {
                    "task_id": "TASK-SR-002",
                    "lane_id": "spec_review",
                    "recommended_backend": "openrouter",
                    "pipeline_mode": "SPEC_REVIEW",
                    "estimated_codex_saved_tokens": 12000,
                    "estimated_delegation_overhead_tokens": 4000,
                },
            ]
        }
        self.calibration_report = {
            "report_type": "delegation_routing_calibration",
            "lane_summaries": [
                {
                    "lane_id": "test_fixture_worker",
                    "task_id": "TASK-TP-003",
                    "skill": "janus-test-pipeline",
                    "status": "NO_EVIDENCE",
                    "sample_count": 0,
                },
                {
                    "lane_id": "skill_router_review",
                    "task_id": "TASK-SR-001",
                    "skill": "janus-skill-router",
                    "status": "NO_EVIDENCE",
                    "sample_count": 0,
                },
                {
                    "lane_id": "live_test_execution",
                    "task_id": "TASK-TP-004",
                    "skill": "janus-test-pipeline",
                    "status": "NO_EVIDENCE",
                    "sample_count": 0,
                },
                {
                    "lane_id": "execution_patch_candidate",
                    "task_id": "TASK-EX-001",
                    "skill": "janus-executioner",
                    "status": "HIGH_VARIANCE_REVIEW_SCOPE",
                    "sample_count": 60,
                },
                {
                    "lane_id": "spec_review",
                    "task_id": "TASK-SR-002",
                    "skill": "janus-spec-review",
                    "status": "ALIGNED",
                    "sample_count": 2,
                },
            ],
        }

    def test_build_plan_prioritizes_cursor_no_evidence_before_openrouter(self) -> None:
        plan = gap_plan.build_plan(
            calibration_report=self.calibration_report,
            manifest=self.manifest,
            task_list=self.task_list,
            generated_at="2026-07-06T12:00:00+00:00",
        )

        self.assertEqual(plan["entry_count"], 4)
        lane_order = [entry["lane_id"] for entry in plan["entries"]]
        self.assertEqual(lane_order[0], "test_fixture_worker")
        fixture_entry = plan["entries"][0]
        self.assertEqual(fixture_entry["recommended_backend"], "cursor")
        self.assertEqual(fixture_entry["priority"], 100)
        self.assertEqual(
            fixture_entry["next_action"],
            "build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke",
        )
        self.assertTrue(fixture_entry["live_requires_explicit_approval"])

    def test_build_plan_keeps_never_delegate_lane_codex_owned(self) -> None:
        plan = gap_plan.build_plan(
            calibration_report=self.calibration_report,
            manifest=self.manifest,
            task_list=self.task_list,
            generated_at="2026-07-06T12:00:00+00:00",
        )

        live_entry = next(entry for entry in plan["entries"] if entry["lane_id"] == "live_test_execution")
        self.assertEqual(live_entry["priority"], 0)
        self.assertEqual(live_entry["next_action"], "keep_codex_owned_never_delegate")
        self.assertFalse(live_entry["live_requires_explicit_approval"])

    def test_high_variance_lane_is_not_manifest_tuning_candidate(self) -> None:
        plan = gap_plan.build_plan(
            calibration_report=self.calibration_report,
            manifest=self.manifest,
            task_list=self.task_list,
            generated_at="2026-07-06T12:00:00+00:00",
        )

        execution_entry = next(entry for entry in plan["entries"] if entry["lane_id"] == "execution_patch_candidate")
        self.assertEqual(execution_entry["priority"], 65)
        self.assertEqual(execution_entry["next_action"], "split_or_deprioritize_no_default_tuning")
        self.assertTrue(execution_entry["do_not_tune_manifest_yet"])

    def test_render_markdown_includes_operator_boundaries(self) -> None:
        plan = gap_plan.build_plan(
            calibration_report=self.calibration_report,
            manifest=self.manifest,
            task_list=self.task_list,
            generated_at="2026-07-06T12:00:00+00:00",
        )

        rendered = gap_plan.render_markdown(plan)
        self.assertIn("No Cursor or OpenRouter live calls are authorized by this plan", rendered)
        self.assertIn("| 100 | test_fixture_worker | TASK-TP-003 | cursor | NO_EVIDENCE |", rendered)
        self.assertIn("Live requires explicit approval: `True`", rendered)
        self.assertIn("keep_codex_owned_never_delegate", rendered)

    def test_deterministic_apply_lane_is_not_treated_as_missing_cursor_evidence(self) -> None:
        manifest = {"lanes": {"execution_write_apply_candidate": {"skill": "janus-executioner"}}}
        task_list = {
            "tasks": [
                {
                    "task_id": "TASK-EX-002",
                    "lane_id": "execution_write_apply_candidate",
                    "recommended_backend": "deterministic_apply",
                    "pipeline_mode": "EXECUTION_WRITE_APPLY",
                    "estimated_codex_saved_tokens": 28000,
                    "estimated_delegation_overhead_tokens": 10000,
                }
            ]
        }
        calibration_report = {
            "report_type": "delegation_routing_calibration",
            "lane_summaries": [
                {
                    "lane_id": "execution_write_apply_candidate",
                    "task_id": "TASK-EX-002",
                    "skill": "janus-executioner",
                    "status": "NO_EVIDENCE",
                    "sample_count": 0,
                }
            ],
        }

        plan = gap_plan.build_plan(
            calibration_report=calibration_report,
            manifest=manifest,
            task_list=task_list,
            generated_at="2026-07-07T13:30:00+00:00",
        )

        self.assertEqual(plan["entry_count"], 1)
        entry = plan["entries"][0]
        self.assertEqual(entry["recommended_backend"], "deterministic_apply")
        self.assertEqual(entry["priority"], 20)
        self.assertEqual(entry["next_action"], "keep_deterministic_apply_contract_and_avoid_live_agent_planning")
        self.assertIn("deterministic local worker", entry["rationale"])


if __name__ == "__main__":
    unittest.main()
