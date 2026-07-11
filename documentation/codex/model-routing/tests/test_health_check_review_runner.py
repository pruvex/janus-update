from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
RUNNER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "codex_health_check_review_runner.py"
FIXTURE_INPUT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-health-check" / "health_check_input_package.json"
FIXTURE_RESPONSE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-health-check" / "fixture_health_check_response.json"


class HealthCheckReviewRunnerTests(unittest.TestCase):
    def test_prompt_gate_passes(self) -> None:
        workflow_id = "WF-HEALTH-CHECK-PROMPT-TEST-2026-06-27"
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--task-label",
                "Health check prompt gate",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "prompt",
                "--workflow-id",
                workflow_id,
                "--estimated-or-cost",
                "0.00016",
                "--cost-estimate-confidence-percent",
                "69",
                "--input-package-json",
                str(FIXTURE_INPUT),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + "\n" + completed.stderr)
        run_dir = REPO_ROOT / "documentation" / "codex" / "model-routing" / "health-check-review-runs" / workflow_id
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("PASS", result["validation_result"])
        self.assertEqual("AWAITING_OPERATOR_CHOICE", result["final_outcome"])

    def test_fixture_delegated_passes(self) -> None:
        workflow_id = "WF-HEALTH-CHECK-FIXTURE-TEST-2026-06-27"
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--task-label",
                "Health check delegated fixture",
                "--normal-target-model",
                "5.4 medium",
                "--operator-choice",
                "delegated",
                "--workflow-id",
                workflow_id,
                "--estimated-or-cost",
                "0.00016",
                "--cost-estimate-confidence-percent",
                "69",
                "--input-package-json",
                str(FIXTURE_INPUT),
                "--use-local-or-fixture",
                "--or-local-fixture-response-path",
                str(FIXTURE_RESPONSE),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + "\n" + completed.stderr)
        run_dir = REPO_ROOT / "documentation" / "codex" / "model-routing" / "health-check-review-runs" / workflow_id
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("PASS", result["validation_result"])
        self.assertEqual("janus-backlog-intake", result["recommended_next_skill"])
        self.assertTrue((run_dir / "or_healthcheck_telemetry.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
