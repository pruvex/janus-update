from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"

SPEC = importlib.util.spec_from_file_location(
    "reset_execution_patch_candidate_shadow_fixture",
    SCRIPTS_DIR / "reset_execution_patch_candidate_shadow_fixture.py",
)
reset_script = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = reset_script
SPEC.loader.exec_module(reset_script)


class ResetExecutionPatchCandidateShadowFixtureTests(unittest.TestCase):
    def test_reset_fixture_restores_pre_session_budget_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            baseline_file = temp_path / "baseline.py"
            target_file = temp_path / "target.py"

            baseline_file.write_text(
                "def build_lines():\n"
                "    return ['1 = Codex', '2 = Cursor', 'Voraussichtliche Worker-Kosten 0.000000']\n",
                encoding="utf-8",
            )
            target_file.write_text(
                "def build_lines():\n"
                "    return ['1 = Codex', '2 = Cursor', 'Session-Budget: Sitzungs-Deckel 0.150000 USD']\n",
                encoding="utf-8",
            )

            result = reset_script.reset_fixture(baseline_file=baseline_file, target_file=target_file)

            self.assertEqual(result["validation_result"], "PASS")
            self.assertEqual(result["final_outcome"], "SHADOW_FIXTURE_RESET_TO_BASELINE")
            self.assertFalse(result["session_budget_present_after_reset"])
            self.assertEqual(target_file.read_text(encoding="utf-8"), baseline_file.read_text(encoding="utf-8"))

    def test_default_baseline_file_stays_pre_session_budget(self) -> None:
        baseline_text = reset_script.DEFAULT_BASELINE_FILE.read_text(encoding="utf-8")

        self.assertNotIn("Session-Budget:", baseline_text)
        self.assertIn("Voraussichtliche Worker-Kosten", baseline_text)


if __name__ == "__main__":
    unittest.main()
