from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


delegation_routing = _load_module("delegation_routing", SCRIPTS_DIR / "delegation_routing.py")
calibration = _load_module("delegation_routing_calibration", SCRIPTS_DIR / "delegation_routing_calibration.py")


class DelegationRoutingCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = {
            "lanes": {
                "spec_review": {
                    "skill": "janus-spec-review",
                    "openrouter": {
                        "prompt_estimated_or_cost": 0.00015,
                        "prompt_cost_estimate_confidence_percent": 55,
                    },
                    "minimum_net_codex_saved_tokens": 8000,
                    "estimated_delegation_overhead_tokens": 4000,
                },
                "precheck_review": {
                    "skill": "janus-preimplementation-check",
                    "openrouter": {
                        "prompt_estimated_or_cost": 0.00012,
                        "prompt_cost_estimate_confidence_percent": 82,
                    },
                    "minimum_net_codex_saved_tokens": 5000,
                    "estimated_delegation_overhead_tokens": 4000,
                },
            }
        }
        self.task_list = {
            "tasks": [
                {
                    "task_id": "TASK-SR-002",
                    "lane_id": "spec_review",
                    "recommended_backend": "openrouter",
                    "minimum_net_codex_saved_tokens": 8000,
                    "estimated_delegation_overhead_tokens": 4000,
                },
                {
                    "task_id": "TASK-PC-001",
                    "lane_id": "precheck_review",
                    "recommended_backend": "openrouter",
                    "minimum_net_codex_saved_tokens": 5000,
                    "estimated_delegation_overhead_tokens": 4000,
                },
            ]
        }

    def test_build_report_flags_under_estimated_lane(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            one = root / "spec-review-runs" / "WF-001" / "validation_summary.json"
            two = root / "spec-review-runs" / "WF-002" / "validation_summary.json"
            one.parent.mkdir(parents=True, exist_ok=True)
            two.parent.mkdir(parents=True, exist_ok=True)
            one.write_text(json.dumps({"workflow_id": "WF-001", "actual_or_cost": 0.00071}), encoding="utf-8")
            two.write_text(json.dumps({"workflow_id": "WF-002", "actual_or_cost": 0.00069}), encoding="utf-8")

            report = calibration.build_report(
                manifest=self.manifest,
                task_list=self.task_list,
                model_routing_dir=root,
                evidence_globs={"spec_review": ["spec-review-runs/*/validation_summary.json"]},
            )

            summary = next(item for item in report["lane_summaries"] if item["lane_id"] == "spec_review")
            self.assertEqual(summary["task_id"], "TASK-SR-002")
            self.assertEqual(summary["sample_count"], 2)
            self.assertEqual(summary["status"], "UNDER_ESTIMATED")
            self.assertAlmostEqual(summary["observed_actual_or_cost_max"], 0.00071, places=8)
            self.assertGreater(summary["suggested_prompt_estimated_or_cost"], 0.00071)
            self.assertEqual(summary["suggested_confidence_percent"], 75)

    def test_build_report_keeps_explicit_no_evidence_rows(self) -> None:
        report = calibration.build_report(
            manifest=self.manifest,
            task_list=self.task_list,
            model_routing_dir=Path.cwd(),
            evidence_globs={},
        )

        summary = next(item for item in report["lane_summaries"] if item["lane_id"] == "precheck_review")
        self.assertEqual(summary["sample_count"], 0)
        self.assertEqual(summary["status"], "NO_EVIDENCE")
        self.assertIsNone(summary["suggested_prompt_estimated_or_cost"])
        self.assertEqual(summary["suggested_confidence_percent"], 82)

    def test_render_markdown_includes_lane_summary_and_evidence(self) -> None:
        report = {
            "generated_at": "2026-07-06T12:00:00+00:00",
            "lane_count": 1,
            "lane_summaries": [
                {
                    "lane_id": "spec_review",
                    "task_id": "TASK-SR-002",
                    "skill": "janus-spec-review",
                    "recommended_backend": "openrouter",
                    "configured_prompt_estimated_or_cost": 0.00015,
                    "configured_confidence_percent": 55,
                    "sample_count": 2,
                    "observed_actual_or_cost_min": 0.00069,
                    "observed_actual_or_cost_mean": 0.0007,
                    "observed_actual_or_cost_max": 0.00071,
                    "suggested_prompt_estimated_or_cost": 0.0007455,
                    "suggested_confidence_percent": 75,
                    "status": "UNDER_ESTIMATED",
                    "evidence_records": [
                        {
                            "workflow_id": "WF-001",
                            "actual_or_cost": 0.00071,
                            "source_path": "spec-review-runs/WF-001/validation_summary.json",
                        }
                    ],
                }
            ],
        }

        rendered = calibration.render_markdown(report)
        self.assertIn("| spec_review | TASK-SR-002 | 2 | 0.00015 | 0.00071 | 0.0007455 | UNDER_ESTIMATED |", rendered)
        self.assertIn("WF-001", rendered)
        self.assertIn("Suggested confidence: `75`", rendered)


if __name__ == "__main__":
    unittest.main()
