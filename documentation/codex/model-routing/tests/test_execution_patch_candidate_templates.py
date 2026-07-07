from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SCRIPTS_DIR = MODEL_ROUTING_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "janus_worker_contract",
    SCRIPTS_DIR / "janus_worker_contract.py",
)
contract = importlib.util.module_from_spec(CONTRACT_SPEC)
assert CONTRACT_SPEC and CONTRACT_SPEC.loader
sys.modules[CONTRACT_SPEC.name] = contract
CONTRACT_SPEC.loader.exec_module(contract)


class ExecutionPatchCandidateTemplateTests(unittest.TestCase):
    def _load_json(self, relative_path: str) -> dict[str, object]:
        return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8-sig"))

    def _allowlist_lines(self, relative_path: str) -> list[str]:
        return [
            line.strip().replace("\\", "/")
            for line in (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_worker_package_template_is_contract_valid(self) -> None:
        payload = self._load_json(
            "documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_cursor_worker_package_template_2026-07-07.json"
        )

        result = contract.validate_worker_task_package(payload)

        self.assertEqual(result["validation_result"], "PASS")

    def test_real_harness_packages_match_allowlists(self) -> None:
        cases = [
            (
                "documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_live_harness_cursor_input_package_2026-07-07.json",
                "documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_live_harness_cursor_worker_package_2026-07-07.json",
                "documentation/codex/model-routing/execution-review-fixtures/allowlists/execution_patch_candidate_live_harness_allowlist_2026-07-07.txt",
            ),
            (
                "documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_text_utils_cursor_input_package_2026-07-07.json",
                "documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_text_utils_cursor_worker_package_2026-07-07.json",
                "documentation/codex/model-routing/execution-review-fixtures/allowlists/execution_patch_candidate_text_utils_allowlist_2026-07-07.txt",
            ),
        ]

        for input_path, worker_path, allowlist_path in cases:
            with self.subTest(input_path=input_path):
                input_payload = self._load_json(input_path)
                worker_payload = self._load_json(worker_path)
                allowlist_lines = self._allowlist_lines(allowlist_path)

                validation = contract.validate_worker_task_package(worker_payload)

                self.assertEqual(validation["validation_result"], "PASS")
                self.assertEqual(input_payload["worker_package_json"], worker_path)
                self.assertEqual(input_payload["allowlist_file"], allowlist_path)
                self.assertEqual(worker_payload["allowed_edit_paths"], allowlist_lines)


if __name__ == "__main__":
    unittest.main()
