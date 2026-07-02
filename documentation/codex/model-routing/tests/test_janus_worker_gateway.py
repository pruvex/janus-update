from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

GATEWAY_SPEC = importlib.util.spec_from_file_location(
    "janus_worker_gateway",
    SCRIPTS_DIR / "janus_worker_gateway.py",
)
gateway = importlib.util.module_from_spec(GATEWAY_SPEC)
assert GATEWAY_SPEC and GATEWAY_SPEC.loader
sys.modules[GATEWAY_SPEC.name] = gateway
GATEWAY_SPEC.loader.exec_module(gateway)

CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "janus_worker_contract",
    SCRIPTS_DIR / "janus_worker_contract.py",
)
contract = importlib.util.module_from_spec(CONTRACT_SPEC)
assert CONTRACT_SPEC and CONTRACT_SPEC.loader
sys.modules[CONTRACT_SPEC.name] = contract
CONTRACT_SPEC.loader.exec_module(contract)


def package_payload() -> dict[str, object]:
    return {
        "task_label": "Gateway validation fixture",
        "worker_profile": "aider-openrouter-qwen",
        "allowed_edit_paths": ["docs/target.md"],
        "forbidden_actions": sorted(contract.REQUIRED_FORBIDDEN_ACTIONS),
        "acceptance_criteria": ["Only docs/target.md changes."],
        "checks": [{"label": "compile", "command": ["python", "--version"]}],
        "requested_actions": ["edit"],
        "task_prompt": "Update docs/target.md only.",
    }


def write_package(root: Path, payload: dict[str, object] | None = None) -> Path:
    path = root / "task.json"
    path.write_text(json.dumps(payload or package_payload(), indent=2), encoding="utf-8")
    return path


def write_result(root: Path, *, status: str = "success", changed_files: str = "docs/target.md\n") -> Path:
    result_dir = root / "result"
    result_dir.mkdir()
    (result_dir / "RESULT.json").write_text(
        json.dumps({"status": status, "checks_status": "pass"}, indent=2),
        encoding="utf-8",
    )
    (result_dir / "RESULT.md").write_text("# Result\n", encoding="utf-8")
    (result_dir / "DIFF.patch").write_text("diff --git a/docs/target.md b/docs/target.md\n", encoding="utf-8")
    (result_dir / "FILES_CHANGED.txt").write_text(changed_files, encoding="utf-8")
    (result_dir / "CHECKS.log").write_text("checks passed\n", encoding="utf-8")
    (result_dir / "COST.json").write_text(json.dumps({"usage_available": False}, indent=2), encoding="utf-8")
    return result_dir


class JanusWorkerGatewayTests(unittest.TestCase):
    def test_validate_gateway_contract_marks_task_package_ready_without_result_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = write_package(Path(temp_dir))

            result = gateway.validate_gateway_contract(package_path)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["gateway_status"], "TASK_PACKAGE_READY")
        self.assertIsNone(result["result_package"])

    def test_validate_gateway_contract_marks_success_result_reviewable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_path = write_package(root)
            result_dir = write_result(root)

            result = gateway.validate_gateway_contract(package_path, result_dir)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["gateway_status"], "WORKER_SUCCESS_REVIEWABLE")
        self.assertEqual(result["result_package"]["changed_files"], ["docs/target.md"])

    def test_validate_gateway_contract_rejects_invalid_task_package_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = package_payload()
            payload["allowed_edit_paths"] = []
            package_path = write_package(Path(temp_dir), payload)

            result = gateway.validate_gateway_contract(package_path)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["gateway_status"], "GATEWAY_CONTRACT_REJECTED")

    def test_validate_gateway_contract_rejects_scope_drift_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_path = write_package(root)
            result_dir = write_result(root, changed_files="docs/target.md\noutside.txt\n")

            result = gateway.validate_gateway_contract(package_path, result_dir)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["gateway_status"], "GATEWAY_CONTRACT_REJECTED")
        self.assertIn("outside.txt", result["result_package"]["issues"][0])

    def test_validate_gateway_contract_accepts_blocked_result_as_reviewable_non_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_path = write_package(root)
            result_dir = write_result(root, status="blocked", changed_files="")
            (result_dir / "DIFF.patch").write_text("", encoding="utf-8")

            result = gateway.validate_gateway_contract(package_path, result_dir)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["gateway_status"], "WORKER_NON_SUCCESS_REVIEWABLE")

    def test_validate_gateway_contract_rejects_success_without_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_path = write_package(root)
            result_dir = write_result(root, changed_files="")

            result = gateway.validate_gateway_contract(package_path, result_dir)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["gateway_status"], "GATEWAY_CONTRACT_REJECTED")
        self.assertIn("success result must list at least one changed file", result["result_package"]["issues"])


if __name__ == "__main__":
    unittest.main()
