#!/usr/bin/env python3
"""Normalize one accepted execution_patch_candidate run into write-apply source format."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DEFAULT_OUTPUT_ROOT = MODEL_ROUTING_DIR / "execution-write-apply-source-bridges"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def _read_patch_text(source_run_dir: Path) -> str:
    patch_candidate = load_json(source_run_dir / "patch_candidate_result.json")
    patch_text = str(patch_candidate.get("patch_text") or "").strip()
    if not patch_text:
        raise SystemExit("patch_candidate_result.json does not contain patch_text.")
    return patch_text


def _read_changed_files(source_run_dir: Path) -> list[str]:
    validation_summary = load_json(source_run_dir / "validation_summary.json")
    changed_files = validation_summary.get("changed_files")
    if not isinstance(changed_files, list) or not changed_files:
        raise SystemExit("validation_summary.json does not contain non-empty changed_files.")
    return [str(item).strip().replace("\\", "/") for item in changed_files if str(item).strip()]


def _copy_required_logs(source_run_dir: Path, output_dir: Path) -> None:
    for name in ("input_package.json", "stdout.log", "stderr.log", "exit_code.txt"):
        source = source_run_dir / name
        if not source.exists():
            raise SystemExit(f"required source artifact missing: {source}")
        shutil.copy2(source, output_dir / name)


def _build_source_file_snapshots(changed_files: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    snapshots: dict[str, dict[str, Any]] = {}
    missing_files: list[str] = []
    for rel_path in changed_files:
        repo_path = REPO_ROOT / rel_path
        if not repo_path.exists() or not repo_path.is_file():
            missing_files.append(rel_path)
            continue
        raw = repo_path.read_bytes()
        snapshots[rel_path] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    return snapshots, missing_files


def build_normalized_package(source_run_dir: Path, output_dir: Path) -> dict[str, Any]:
    operator_summary = load_json(source_run_dir / "operator_summary.json")
    validation_summary = load_json(source_run_dir / "validation_summary.json")

    if operator_summary.get("validation_result") != "PASS":
        raise SystemExit("source operator_summary validation_result must be PASS")
    if validation_summary.get("validation_result") != "PASS":
        raise SystemExit("source validation_summary validation_result must be PASS")

    patch_text = _read_patch_text(source_run_dir)
    changed_files = _read_changed_files(source_run_dir)
    source_file_snapshots, snapshot_missing_files = _build_source_file_snapshots(changed_files)

    output_dir.mkdir(parents=True, exist_ok=True)
    _copy_required_logs(source_run_dir, output_dir)

    git_diff_path = output_dir / "git_diff.patch"
    changed_files_path = output_dir / "changed_files.txt"
    delegated_result_path = output_dir / "delegated_result.md"

    write_text(git_diff_path, patch_text.rstrip() + "\n")
    write_text(changed_files_path, "\n".join(changed_files) + "\n")
    write_text(
        delegated_result_path,
        "# Delegated Result\n\nAccepted proposal-first execution patch candidate normalized for write-apply validation.\n\n```diff\n"
        + patch_text.rstrip()
        + "\n```\n",
    )

    normalized_validation = dict(validation_summary)
    normalized_validation["status"] = "PASS"
    normalized_validation["accepted_for_codex_patch_review"] = True
    normalized_validation["changed_files"] = changed_files
    if source_file_snapshots:
        normalized_validation["source_file_snapshots"] = source_file_snapshots
    if snapshot_missing_files:
        normalized_validation["source_snapshot_missing_files"] = snapshot_missing_files
    write_json(output_dir / "validation_summary.json", normalized_validation)

    normalized_operator = dict(operator_summary)
    normalized_operator["validation_result"] = "PASS"
    normalized_operator["final_outcome"] = "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW"
    normalized_operator["operator_message"] = (
        "Normalized accepted proposal-first execution package for execution_write_apply_candidate validation. "
        "Codex still owns accept-or-reject and any future live write approval."
    )
    write_json(output_dir / "operator_summary.json", normalized_operator)

    summary_payload = {
        "status": "PASS",
        "artifact_success": True,
        "git_diff": str(git_diff_path.resolve()),
        "changed_files": str(changed_files_path.resolve()),
        "normalized_from": str(source_run_dir.resolve()),
    }
    write_json(output_dir / "summary.json", summary_payload)

    bridge_summary = {
        "status": "PASS",
        "source_run_dir": repo_rel(source_run_dir),
        "output_dir": repo_rel(output_dir),
        "changed_files": changed_files,
        "source_snapshot_count": len(source_file_snapshots),
        "source_snapshot_missing_files": snapshot_missing_files,
        "artifacts": {
            "input_package": repo_rel(output_dir / "input_package.json"),
            "validation_summary": repo_rel(output_dir / "validation_summary.json"),
            "operator_summary": repo_rel(output_dir / "operator_summary.json"),
            "summary": repo_rel(output_dir / "summary.json"),
            "delegated_result": repo_rel(delegated_result_path),
            "git_diff": repo_rel(git_diff_path),
            "changed_files": repo_rel(changed_files_path),
            "stdout": repo_rel(output_dir / "stdout.log"),
            "stderr": repo_rel(output_dir / "stderr.log"),
            "exit_code": repo_rel(output_dir / "exit_code.txt"),
        },
    }
    write_json(output_dir / "bridge_summary.json", bridge_summary)
    return bridge_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize accepted execution patch candidate output for write-apply validation.")
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    source_run_dir = args.source_run_dir.resolve()
    if not source_run_dir.exists():
        raise SystemExit(f"source run dir does not exist: {source_run_dir}")

    output_dir = args.output_dir.resolve() if args.output_dir else (DEFAULT_OUTPUT_ROOT / args.workflow_id).resolve()
    summary = build_normalized_package(source_run_dir, output_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
