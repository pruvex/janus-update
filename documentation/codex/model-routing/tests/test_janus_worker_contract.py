from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "janus_worker_contract",
    SCRIPTS_DIR / "janus_worker_contract.py",
)
contract = importlib.util.module_from_spec(CONTRACT_SPEC)
assert CONTRACT_SPEC and CONTRACT_SPEC.loader
sys.modules[CONTRACT_SPEC.name] = contract
CONTRACT_SPEC.loader.exec_module(contract)


def valid_package() -> dict[str, object]:
    return {
        "task_label": "Docs fixture update",
        "worker_profile": "aider-openrouter-qwen",
        "allowed_edit_paths": ["docs/target.md"],
        "forbidden_actions": sorted(contract.REQUIRED_FORBIDDEN_ACTIONS),
        "acceptance_criteria": ["Update only the target doc."],
        "checks": [{"label": "markdown check", "command": ["python", "--version"]}],
        "requested_actions": ["edit"],
        "task_prompt": "Update docs/target.md only.",
    }


def write_result_dir(root: Path, *, status: str = "success", checks_status: str = "pass") -> Path:
    result_dir = root / "result"
    result_dir.mkdir()
    (result_dir / "RESULT.json").write_text(
        json.dumps({"status": status, "checks_status": checks_status}, indent=2),
        encoding="utf-8",
    )
    (result_dir / "RESULT.md").write_text("# Result\n", encoding="utf-8")
    (result_dir / "DIFF.patch").write_text("diff --git a/docs/target.md b/docs/target.md\n", encoding="utf-8")
    (result_dir / "FILES_CHANGED.txt").write_text("docs/target.md\n", encoding="utf-8")
    (result_dir / "CHECKS.log").write_text("checks passed\n", encoding="utf-8")
    (result_dir / "COST.json").write_text(
        json.dumps({"usage_available": True, "estimated_or_cost_usd": 0.001}, indent=2),
        encoding="utf-8",
    )
    return result_dir


def write_shadow_package(root: Path, class_id: str, *, allowed_edit_paths: list[str] | None = None) -> Path:
    package_dir = root / "development" / "openrouter-skill-tests" / "janus-worker-gateway-shadow-eval" / class_id
    package_dir.mkdir(parents=True, exist_ok=True)
    package_path = package_dir / "task_package.json"
    payload = valid_package()
    payload["task_label"] = f"{class_id} shadow package"
    payload["shadow_work_class"] = class_id
    payload["worker_profile"] = "shadow-eval-fixed-pair"
    payload["allowed_edit_paths"] = allowed_edit_paths or [f"{class_id}/target.md"]
    payload["task_prompt"] = f"Edit only the bounded files for {class_id}."
    package_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return package_path


def write_shadow_manifest(root: Path, *, class_ids: list[str] | None = None, duplicate_models: bool = False) -> Path:
    class_ids = class_ids or ["docs_fleissarbeit", "test_fixture_arbeit"]
    manifest_path = root / "development" / "openrouter-skill-tests" / "janus-worker-gateway-shadow-eval" / "shadow_evaluation_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    shadow_classes: list[dict[str, object]] = []
    for class_id in class_ids:
        package_path = write_shadow_package(root, class_id)
        shadow_classes.append(
            {
                "class_id": class_id,
                "task_package_path": package_path.relative_to(root).as_posix(),
                "comparison_models": (
                    [
                        "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                        "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                    ]
                    if duplicate_models
                    else [
                        "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                        "openrouter/moonshotai/kimi-k2.5",
                    ]
                ),
            }
        )
    manifest = {
        "evaluation_id": "SPEC30-SHADOW-EVAL-001",
        "sandbox_root": "development/openrouter-skill-tests/janus-worker-gateway-shadow-eval",
        "real_repo_writeback_allowed": False,
        "global_worker_release_allowed": False,
        "real_consumer_activation_allowed": False,
        "shadow_work_classes": shadow_classes,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


class JanusWorkerContractTests(unittest.TestCase):
    def test_valid_task_package_passes_contract(self) -> None:
        result = contract.validate_worker_task_package(valid_package())

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["contract_status"], "TASK_PACKAGE_VALID")
        self.assertEqual(result["allowed_edit_paths"], ["docs/target.md"])

    def test_task_package_rejects_empty_allowlist(self) -> None:
        payload = valid_package()
        payload["allowed_edit_paths"] = []

        result = contract.validate_worker_task_package(payload)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertIn("allowed_edit_paths must contain at least one path", result["issues"])

    def test_task_package_rejects_missing_forbidden_boundary(self) -> None:
        payload = valid_package()
        payload["forbidden_actions"] = ["commit", "push"]

        result = contract.validate_worker_task_package(payload)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertTrue(any("forbidden_actions missing required boundaries" in issue for issue in result["issues"]))

    def test_task_package_rejects_requested_forbidden_action(self) -> None:
        payload = valid_package()
        payload["requested_actions"] = ["edit", "push"]

        result = contract.validate_worker_task_package(payload)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertIn("requested_actions contains forbidden actions: push", result["issues"])

    def test_task_package_allows_no_checks_only_with_reason(self) -> None:
        payload = valid_package()
        payload["checks"] = []
        payload["checks_not_required_reason"] = "docs-only fixture contract check"

        result = contract.validate_worker_task_package(payload)

        self.assertEqual(result["validation_result"], "PASS")

    def test_success_result_package_passes_when_scope_and_artifacts_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = write_result_dir(Path(temp_dir))

            result = contract.validate_worker_result_dir(result_dir, allowed_edit_paths=["docs/target.md"])

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["contract_status"], "WORKER_SUCCESS_REVIEWABLE")

    def test_success_result_rejects_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = write_result_dir(Path(temp_dir))
            (result_dir / "DIFF.patch").unlink()

            result = contract.validate_worker_result_dir(result_dir, allowed_edit_paths=["docs/target.md"])

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["contract_status"], "WORKER_SUCCESS_REJECTED")
        self.assertIn("DIFF.patch", result["issues"][0])

    def test_success_result_rejects_scope_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = write_result_dir(Path(temp_dir))
            (result_dir / "FILES_CHANGED.txt").write_text("docs/target.md\nsecrets.env\n", encoding="utf-8")

            result = contract.validate_worker_result_dir(result_dir, allowed_edit_paths=["docs/target.md"])

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertIn("changed files outside allowed_edit_paths: secrets.env", result["issues"])

    def test_success_result_rejects_red_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = write_result_dir(Path(temp_dir), checks_status="fail")

            result = contract.validate_worker_result_dir(result_dir, allowed_edit_paths=["docs/target.md"])

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertIn("success result requires RESULT.json checks_status=pass", result["issues"])

    def test_blocked_result_is_reviewable_when_artifacts_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = write_result_dir(Path(temp_dir), status="blocked", checks_status="not_run")
            (result_dir / "DIFF.patch").write_text("", encoding="utf-8")
            (result_dir / "FILES_CHANGED.txt").write_text("", encoding="utf-8")

            result = contract.validate_worker_result_dir(result_dir, allowed_edit_paths=["docs/target.md"])

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["contract_status"], "WORKER_NON_SUCCESS_REVIEWABLE")

    def test_success_result_rejects_empty_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_dir = write_result_dir(Path(temp_dir))
            (result_dir / "FILES_CHANGED.txt").write_text("", encoding="utf-8")

            result = contract.validate_worker_result_dir(result_dir, allowed_edit_paths=["docs/target.md"])

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertIn("success result must list at least one changed file", result["issues"])

    def test_shadow_evaluation_manifest_passes_with_exact_two_classes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_manifest(root)

            result = contract.validate_shadow_evaluation_manifest_file(manifest_path, repo_root=root)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["contract_status"], "SHADOW_EVALUATION_READY")
        self.assertEqual(
            sorted(result["package_validations"].keys()),
            ["docs_fleissarbeit", "test_fixture_arbeit"],
        )

    def test_shadow_evaluation_manifest_rejects_missing_required_class(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_manifest(root, class_ids=["docs_fleissarbeit", "docs_fleissarbeit"])

            result = contract.validate_shadow_evaluation_manifest_file(manifest_path, repo_root=root)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertTrue(any("missing required shadow work classes" in issue for issue in result["issues"]))

    def test_shadow_evaluation_manifest_rejects_duplicate_model_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_manifest(root, duplicate_models=True)

            result = contract.validate_shadow_evaluation_manifest_file(manifest_path, repo_root=root)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertTrue(any("comparison_models must not contain duplicates" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
