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


def write_shadow_package(root: Path, class_id: str) -> Path:
    package_dir = root / "development" / "openrouter-skill-tests" / "janus-worker-gateway-shadow-eval" / class_id
    package_dir.mkdir(parents=True)
    package_path = package_dir / "task_package.json"
    package_path.write_text(
        json.dumps(
            {
                "task_label": f"{class_id} shadow package",
                "shadow_work_class": class_id,
                "worker_profile": "shadow-eval-fixed-pair",
                "allowed_edit_paths": [f"{class_id}/target.md"],
                "forbidden_actions": sorted(contract.REQUIRED_FORBIDDEN_ACTIONS),
                "acceptance_criteria": ["Stay inside the bounded shadow path."],
                "checks": [{"label": "python", "command": ["python", "--version"], "expected_exit_codes": [0]}],
                "requested_actions": ["edit"],
                "task_prompt": f"Edit only the bounded files for {class_id}.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return package_path


def write_shadow_manifest(root: Path, *, include_third_class: bool = False) -> Path:
    sandbox_root = root / "development" / "openrouter-skill-tests" / "janus-worker-gateway-shadow-eval"
    sandbox_root.mkdir(parents=True, exist_ok=True)
    class_ids = ["docs_fleissarbeit", "test_fixture_arbeit"]
    if include_third_class:
        class_ids.append("unexpected_class")
    shadow_classes: list[dict[str, object]] = []
    for class_id in class_ids:
        package_path = write_shadow_package(root, class_id)
        shadow_classes.append(
            {
                "class_id": class_id,
                "task_package_path": package_path.relative_to(root).as_posix(),
                "comparison_models": [
                    "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
                    "openrouter/moonshotai/kimi-k2.5",
                ],
            }
        )
    manifest_path = sandbox_root / "shadow_evaluation_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "evaluation_id": "SPEC30-SHADOW-EVAL-001",
                "sandbox_root": "development/openrouter-skill-tests/janus-worker-gateway-shadow-eval",
                "real_repo_writeback_allowed": False,
                "global_worker_release_allowed": False,
                "real_consumer_activation_allowed": False,
                "shadow_work_classes": shadow_classes,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def write_shadow_comparison_summary(
    root: Path,
    class_id: str,
    *,
    blocked_second_model: bool = False,
) -> Path:
    manifest_path = write_shadow_manifest(root)
    task_package_path = (
        root
        / "development"
        / "openrouter-skill-tests"
        / "janus-worker-gateway-shadow-eval"
        / class_id
        / "task_package.json"
    )
    task_payload = json.loads(task_package_path.read_text(encoding="utf-8"))
    task_payload["allowed_edit_paths"] = (
        ["docs/target_doc.md"]
        if class_id == "docs_fleissarbeit"
        else ["fixtures/contact_memory_fixture.json", "tests/test_contact_memory_fixture.py"]
    )
    task_package_path.write_text(json.dumps(task_payload, indent=2), encoding="utf-8")
    class_dir = root / "evaluation-runs" / class_id
    class_dir.mkdir(parents=True, exist_ok=True)

    model_ids = [
        "openrouter/qwen/qwen3-coder-30b-a3b-instruct",
        "openrouter/moonshotai/kimi-k2.5",
    ]
    model_runs: list[dict[str, object]] = []
    for index, model_id in enumerate(model_ids):
        run_dir = class_dir / f"run-{index + 1}"
        run_dir.mkdir()
        status = "blocked" if blocked_second_model and index == 1 else "success"
        changed = "" if status == "blocked" else ("docs/target_doc.md\n" if class_id == "docs_fleissarbeit" else "fixtures/contact_memory_fixture.json\n")
        result_dir = write_result(run_dir, status=status, changed_files=changed)
        if status == "blocked":
            (result_dir / "DIFF.patch").write_text("", encoding="utf-8")
        (result_dir / "COST.json").write_text(
            json.dumps({"usage_available": False, "estimated_or_cost_usd": 0.0012}, indent=2),
            encoding="utf-8",
        )
        model_runs.append(
            {
                "model_id": model_id,
                "run_directory": result_dir.relative_to(root).as_posix(),
                "final_outcome": "ISOLATED_AIDER_READY_FOR_CODEX_REVIEW" if status == "success" else "ISOLATED_AIDER_BLOCKED_AND_FALLBACK",
                "gateway_status": "WORKER_SUCCESS_REVIEWABLE" if status == "success" else "WORKER_NON_SUCCESS_REVIEWABLE",
                "validation_result": "PASS",
                "result_status": status,
                "changed_files": [line for line in changed.splitlines() if line],
                "cost_hint_available": True,
            }
        )

    summary_path = class_dir / "comparison_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "class_id": class_id,
                "task_package_path": task_package_path.relative_to(root).as_posix(),
                "expected_models": model_ids,
                "model_runs": model_runs,
                "comparison_status": "SHADOW_CLASS_COMPARISON_BLOCKED_REVIEWABLE" if blocked_second_model else "SHADOW_CLASS_COMPARISON_READY",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


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

    def test_validate_shadow_evaluation_bundle_marks_exact_two_class_bundle_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_manifest(root)

            result = gateway.validate_shadow_evaluation_bundle(manifest_path, repo_root=root)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["gateway_status"], "SHADOW_EVALUATION_READY")
        self.assertEqual(
            result["shadow_evaluation_manifest"]["contract_status"],
            "SHADOW_EVALUATION_READY",
        )

    def test_validate_shadow_evaluation_bundle_rejects_third_class_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_manifest(root, include_third_class=True)

            result = gateway.validate_shadow_evaluation_bundle(manifest_path, repo_root=root)

        self.assertEqual(result["validation_result"], "FAIL")
        self.assertEqual(result["gateway_status"], "SHADOW_EVALUATION_REJECTED")
        self.assertTrue(
            any(
                "exactly two class definitions" in issue
                for issue in result["shadow_evaluation_manifest"]["issues"]
            )
        )

    def test_validate_shadow_class_comparison_marks_ready_when_both_runs_are_reviewable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_shadow_comparison_summary(root, "docs_fleissarbeit")
            summary_path = root / "evaluation-runs" / "docs_fleissarbeit" / "comparison_summary.json"

            result = gateway.validate_shadow_class_comparison(summary_path, repo_root=root)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["comparison_status"], "SHADOW_CLASS_COMPARISON_READY")

    def test_validate_shadow_class_comparison_accepts_blocked_run_as_reviewable_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_shadow_comparison_summary(root, "docs_fleissarbeit", blocked_second_model=True)
            summary_path = root / "evaluation-runs" / "docs_fleissarbeit" / "comparison_summary.json"

            result = gateway.validate_shadow_class_comparison(summary_path, repo_root=root)

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["comparison_status"], "SHADOW_CLASS_COMPARISON_BLOCKED_REVIEWABLE")

    def test_validate_shadow_evaluation_run_bundle_marks_blocked_reviewable_when_one_class_blocks_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = write_shadow_comparison_summary(root, "docs_fleissarbeit")
            write_shadow_comparison_summary(root, "test_fixture_arbeit", blocked_second_model=True)
            evaluation_run_dir = root / "evaluation-runs"

            result = gateway.validate_shadow_evaluation_run_bundle(
                manifest_path,
                evaluation_run_dir,
                repo_root=root,
            )

        self.assertEqual(result["validation_result"], "PASS")
        self.assertEqual(result["gateway_status"], "SHADOW_EVALUATION_RUNS_BLOCKED_REVIEWABLE")


if __name__ == "__main__":
    unittest.main()
