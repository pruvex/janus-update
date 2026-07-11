from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = TESTS_DIR.parent.parent / "skills" / "janus-spec-normalizer" / "scripts" / "validate_feature_spec.py"
REPO_ROOT = TESTS_DIR.parent.parent.parent.parent


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


validator = load_module("janus_spec_normalizer_validator_contracts", VALIDATOR_PATH)


class ValidateFeatureSpecContractsTests(unittest.TestCase):
    def test_current_contract_spec_passes(self) -> None:
        spec_path = REPO_ROOT / "documentation" / "SPEC" / "26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md"
        errors = validator.validate(spec_path.read_text(encoding="utf-8"))
        self.assertEqual([], errors)

    def test_legacy_contract_spec_passes(self) -> None:
        spec_path = REPO_ROOT / "documentation" / "SPEC" / "Spec Done" / "14_gemini_cost_attribution_and_deepdive_forensics.md"
        errors = validator.validate(spec_path.read_text(encoding="utf-8"))
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
