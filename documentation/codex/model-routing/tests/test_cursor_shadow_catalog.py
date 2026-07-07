from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


MODEL_ROUTING_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = MODEL_ROUTING_DIR / "scripts"
CATALOG_ROOT = MODEL_ROUTING_DIR / "fixtures" / "cursor-shadow-catalog"
WRITE_APPLY_ROOT = CATALOG_ROOT / "execution_write_apply_candidate"
TEST_FIXTURE_GOLDEN_PATH_DOC = MODEL_ROUTING_DIR / "TEST_FIXTURE_WORKER_GOLDEN_PATH_2026-07-06.md"
DEBUG_REPRO_GOLDEN_PATH_DOC = MODEL_ROUTING_DIR / "DEBUG_REPRO_INVESTIGATION_GOLDEN_PATH_2026-07-07.md"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


janus_delegate = _load_module("janus_delegate_cursor_shadow_catalog", SCRIPTS_DIR / "janus_delegate.py")
cursor_runner = _load_module("janus_cursor_worker_runner_cursor_shadow_catalog", SCRIPTS_DIR / "janus_cursor_worker_runner.py")
worker_contract = _load_module("janus_worker_contract_cursor_shadow_catalog", SCRIPTS_DIR / "janus_worker_contract.py")


class CursorShadowCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((CATALOG_ROOT / "manifest.json").read_text(encoding="utf-8-sig"))
        task_list_path = MODEL_ROUTING_DIR / "config" / "delegation_task_list_2026-07-05.json"
        self.task_list = json.loads(task_list_path.read_text(encoding="utf-8-sig"))
        self.task_by_id = {
            task["task_id"]: task
            for task in self.task_list["tasks"]
            if isinstance(task, dict) and task.get("task_id")
        }

    def _catalog_task(self, task_id: str) -> dict[str, object]:
        for task in self.manifest["tasks"]:
            if task["task_id"] == task_id:
                return task
        raise KeyError(task_id)

    def _allowlist_lines(self, relative_path: str) -> list[str]:
        path = Path(relative_path)
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _route(self, *args: str) -> dict[str, object]:
        parsed = janus_delegate.parse_args([
            "--workflow-id",
            "WF-CURSOR-SHADOW-TEST-000",
            *args,
        ])
        return janus_delegate.route(parsed)

    def _normalized_command(self, command: list[object]) -> list[str]:
        return [str(item).replace("\\", "/") for item in command]

    def test_manifest_lists_three_cursor_shadow_tasks(self) -> None:
        self.assertEqual(self.manifest["catalog_id"], "cursor-shadow-catalog-v1")
        self.assertEqual(self.manifest["status"], "NO_LIVE_READY")
        self.assertEqual(len(self.manifest["tasks"]), 3)

    def test_test_fixture_worker_golden_path_doc_exists_and_references_live_proofs(self) -> None:
        content = TEST_FIXTURE_GOLDEN_PATH_DOC.read_text(encoding="utf-8")

        self.assertIn("TASK-TP-003", content)
        self.assertIn("test_fixture_worker", content)
        self.assertIn("WF-CURSOR-LIVE-SMOKE-003", content)
        self.assertIn("WF-CURSOR-SHADOW-TEST-LIVE-001", content)
        self.assertIn("WF-CURSOR-SHADOW-TEST-LIVE-002", content)

    def test_debug_repro_golden_path_doc_exists_and_references_live_proofs(self) -> None:
        content = DEBUG_REPRO_GOLDEN_PATH_DOC.read_text(encoding="utf-8")

        self.assertIn("TASK-DBG-002", content)
        self.assertIn("debug_repro_investigation", content)
        self.assertIn("WF-CURSOR-SHADOW-DEBUG-LIVE-001", content)
        self.assertIn("WF-CURSOR-SHADOW-DEBUG-LIVE-002", content)

    def test_worker_packages_and_input_packages_validate(self) -> None:
        for catalog_task in self.manifest["tasks"]:
            with self.subTest(task_id=catalog_task["task_id"]):
                worker_package_path = Path(catalog_task["worker_package_json"])
                input_package_path = Path(catalog_task["input_package_json"])
                allowlist_file_path = Path(catalog_task["allowlist_file"])

                self.assertTrue(worker_package_path.exists())
                self.assertTrue(input_package_path.exists())
                self.assertTrue(allowlist_file_path.exists())

                worker_validation = worker_contract.validate_worker_task_package_file(worker_package_path)
                self.assertEqual(worker_validation["validation_result"], "PASS")

                input_validation = cursor_runner.validate_package_or_worker_reference(input_package_path)
                self.assertEqual(input_validation["validation_result"], "PASS")

                allowlist_lines = self._allowlist_lines(catalog_task["allowlist_file"])
                allowlist_validation = cursor_runner.validate_allowlist(allowlist_lines)
                self.assertEqual(allowlist_validation["validation_result"], "PASS")

                worker_package = json.loads(worker_package_path.read_text(encoding="utf-8-sig"))
                self.assertEqual(allowlist_lines, worker_package["allowed_edit_paths"])

    def test_manifest_tasks_match_delegation_task_list(self) -> None:
        for catalog_task in self.manifest["tasks"]:
            with self.subTest(task_id=catalog_task["task_id"]):
                task_id = catalog_task["task_id"]
                delegate_task = self.task_by_id[task_id]
                self.assertEqual(catalog_task["lane_id"], delegate_task["lane_id"])
                expected_backend = "deterministic_apply" if task_id == "TASK-EX-002" else "cursor"
                self.assertEqual(delegate_task["recommended_backend"], expected_backend)

    def test_prompt_gate_passes_for_all_shadow_tasks(self) -> None:
        for catalog_task in self.manifest["tasks"]:
            with self.subTest(task_id=catalog_task["task_id"]):
                result = self._route(
                    "--lane",
                    str(catalog_task["lane_id"]),
                    "--task-id",
                    str(catalog_task["task_id"]),
                    "--operator-choice",
                    "prompt",
                    "--input-package-json",
                    str(catalog_task["input_package_json"]),
                    "--allowlist-file",
                    str(catalog_task["allowlist_file"]),
                    "--dry-run",
                )

                self.assertEqual(result["validation_result"], "PASS")
                self.assertEqual(result["final_outcome"], "AWAITING_OPERATOR_CHOICE")
                expected_backend = "deterministic_apply" if catalog_task["task_id"] == "TASK-EX-002" else "cursor"
                expected_option_two = "2 = Deterministic Apply" if catalog_task["task_id"] == "TASK-EX-002" else "2 = Cursor"
                self.assertEqual(result["recommended_backend"], expected_backend)
                self.assertEqual(result["operator_gate_lines"][:2], ["1 = Codex", expected_option_two])

    def test_cursor_dry_run_passes_for_all_shadow_tasks(self) -> None:
        for catalog_task in self.manifest["tasks"]:
            with self.subTest(task_id=catalog_task["task_id"]):
                result = self._route(
                    "--lane",
                    str(catalog_task["lane_id"]),
                    "--task-id",
                    str(catalog_task["task_id"]),
                    "--operator-choice",
                    "2",
                    "--input-package-json",
                    str(catalog_task["input_package_json"]),
                    "--allowlist-file",
                    str(catalog_task["allowlist_file"]),
                    "--dry-run",
                )

                self.assertEqual(result["validation_result"], "PASS")
                self.assertEqual(result["final_outcome"], "CURSOR_WORKER_DRY_RUN_READY")
                self.assertEqual(result["backend"], "cursor")
                self.assertFalse(result["live_execution_allowed"])
                normalized_command = self._normalized_command(result["planned_command"])
                self.assertIn("janus_cursor_worker_runner.py", " ".join(normalized_command))
                self.assertIn(str(catalog_task["input_package_json"]), normalized_command)
                self.assertIn(str(catalog_task["allowlist_file"]), normalized_command)
                self.assertIn("--dry-run", normalized_command)

    def test_execution_write_apply_shadow_fixture_validates_and_dry_runs(self) -> None:
        input_package_path = WRITE_APPLY_ROOT / "input_package.json"
        worker_package_path = WRITE_APPLY_ROOT / "worker_package.json"
        allowlist_file_path = WRITE_APPLY_ROOT / "allowlist.txt"
        accepted_source_run_dir = (
            WRITE_APPLY_ROOT / "accepted_source" / "WF-CURSOR-SHADOW-EXEC-ACCEPTED-001"
        )

        worker_validation = worker_contract.validate_worker_task_package_file(worker_package_path)
        self.assertEqual(worker_validation["validation_result"], "PASS")

        input_validation = cursor_runner.validate_package_or_worker_reference(input_package_path)
        self.assertEqual(input_validation["validation_result"], "PASS")

        allowlist_lines = self._allowlist_lines(str(allowlist_file_path))
        allowlist_validation = cursor_runner.validate_allowlist(allowlist_lines)
        self.assertEqual(allowlist_validation["validation_result"], "PASS")

        accepted_source_validation = cursor_runner.validate_accepted_source_run_dir(
            accepted_source_run_dir,
            required=True,
        )
        self.assertEqual(accepted_source_validation["validation_result"], "PASS")

        result = self._route(
            "--lane",
            "execution_write_apply_candidate",
            "--task-id",
            "TASK-EX-002",
            "--operator-choice",
            "2",
            "--input-package-json",
            str(input_package_path),
            "--allowlist-file",
            str(allowlist_file_path),
            "--accepted-source-run-dir",
            str(accepted_source_run_dir),
            "--estimated-codex-saved-tokens",
            "28000",
            "--estimated-delegation-overhead-tokens",
            "10000",
            "--minimum-net-codex-saved-tokens",
            "12000",
            "--dry-run",
        )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["backend"], "deterministic_apply")
        self.assertEqual(result["final_outcome"], "DETERMINISTIC_APPLY_DRY_RUN_READY")
        self.assertEqual(result["operator_gate_lines"], ["1 = Codex", "2 = Deterministic Apply"])
        normalized_command = self._normalized_command(result["planned_command"])
        self.assertIn("--accepted-source-run-dir", normalized_command)
        self.assertIn(str(accepted_source_run_dir).replace("\\", "/"), normalized_command)
        self.assertIn("codex_execution_write_apply_candidate_runner.py", " ".join(normalized_command))


if __name__ == "__main__":
    unittest.main()
