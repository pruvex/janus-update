from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
RUNNER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "codex_spec_normalizer_runner.py"
FIXTURE_INPUT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-normalizer" / "spec_normalizer_input_package.json"
FIXTURE_RESPONSE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-normalizer" / "fixture_normalized_spec_response.json"


class SpecNormalizerRunnerTests(unittest.TestCase):
    def test_prompt_gate_passes_with_bound_input(self) -> None:
        workflow_id = "WF-SPEC-NORMALIZER-PROMPT-TEST-2026-06-27"
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--task-label",
                "Spec normalizer prompt gate",
                "--normal-target-model",
                "5.4 mini",
                "--operator-choice",
                "prompt",
                "--workflow-id",
                workflow_id,
                "--estimated-or-cost",
                "0.00022",
                "--cost-estimate-confidence-percent",
                "72",
                "--input-package-json",
                str(FIXTURE_INPUT),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + "\n" + completed.stderr)

        run_dir = REPO_ROOT / "documentation" / "codex" / "model-routing" / "spec-normalizer-runs" / workflow_id
        self.assertTrue((run_dir / "result.json").exists())
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("PASS", result["validation_result"])
        self.assertEqual("AWAITING_OPERATOR_CHOICE", result["final_outcome"])
        self.assertEqual("OR", result["choice_2"])

    def test_fixture_local_run_passes(self) -> None:
        workflow_id = "WF-SPEC-NORMALIZER-TEST-2026-06-26"
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--task-label",
                "Spec normalizer fixture smoke",
                "--normal-target-model",
                "5.4 mini",
                "--operator-choice",
                "delegated",
                "--workflow-id",
                workflow_id,
                "--estimated-or-cost",
                "0.00022",
                "--cost-estimate-confidence-percent",
                "72",
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

        run_dir = REPO_ROOT / "documentation" / "codex" / "model-routing" / "spec-normalizer-runs" / workflow_id
        self.assertTrue((run_dir / "result.json").exists())
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual("PASS", result["validation_result"])
        self.assertIn("normalized_spec_markdown", result)
        self.assertTrue((run_dir / "normalized_spec.md").exists())
        self.assertTrue((run_dir / "or_healthcheck_telemetry.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
