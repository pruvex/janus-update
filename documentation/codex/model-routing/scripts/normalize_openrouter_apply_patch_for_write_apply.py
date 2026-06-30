#!/usr/bin/env python3
"""Normalize accepted OpenRouter apply_patch calls into write-apply source format."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DEFAULT_OUTPUT_ROOT = MODEL_ROUTING_DIR / "execution-write-apply-source-bridges"

ACCEPTED_OUTCOMES = {
    "QWEN_RESPONSES_APPLY_PATCH_READY_FOR_CODEX_REVIEW",
    "QWEN_RESPONSES_EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW",
}


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


def normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def strip_diff_fence(diff_text: str) -> str:
    stripped = diff_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def sequence_index(lines: list[str], needle: list[str], start_index: int) -> int | None:
    if not needle:
        return None
    max_index = len(lines) - len(needle)
    for index in range(start_index, max_index + 1):
        if lines[index : index + len(needle)] == needle:
            return index
    return None


def parse_unified_hunks(diff_text: str) -> tuple[list[list[str]], list[str]]:
    lines = strip_diff_fence(diff_text).splitlines()
    issues: list[str] = []
    hunks: list[list[str]] = []
    current_hunk: list[str] | None = None

    for line in lines:
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = []
            continue
        if current_hunk is None:
            if line.strip():
                issues.append("diff content before hunk marker")
            continue
        current_hunk.append(line)

    if current_hunk:
        hunks.append(current_hunk)
    if not hunks:
        issues.append("diff has no hunks")
    return hunks, issues


def extract_patch_sections(patch_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    lines = patch_text.splitlines()
    issues: list[str] = []
    if not lines or lines[0].strip() != "*** Begin Patch":
        return [], ["patch must start with *** Begin Patch"]
    if lines[-1].strip() != "*** End Patch":
        return [], ["patch must end with *** End Patch"]

    sections: list[dict[str, Any]] = []
    index = 1
    while index < len(lines) - 1:
        line = lines[index]
        if not line:
            index += 1
            continue
        if line.startswith(("*** Add File:", "*** Delete File:", "*** Move to:")):
            issues.append("patch contains add/delete/move operation")
            index += 1
            continue
        if not line.startswith("*** Update File: "):
            issues.append(f"unsupported patch line: {line}")
            index += 1
            continue

        path = normalize_repo_path(line[len("*** Update File: ") :].strip())
        index += 1
        hunks: list[list[str]] = []
        current_hunk: list[str] | None = None
        while index < len(lines) - 1:
            current_line = lines[index]
            if current_line.startswith("*** Update File: "):
                break
            if current_line == "@@":
                if current_hunk:
                    hunks.append(current_hunk)
                current_hunk = []
            else:
                if current_hunk is None:
                    issues.append(f"patch content before hunk marker in {path}")
                    current_hunk = []
                current_hunk.append(current_line)
            index += 1
        if current_hunk:
            hunks.append(current_hunk)
        sections.append({"path": path, "hunks": hunks})
    return sections, issues


def hunk_old_sequence(hunk: list[str]) -> tuple[list[str], list[str]]:
    exact = [line[1:] if line.startswith("-") else line for line in hunk if not line.startswith("+")]
    stripped = [line[1:] if line.startswith((" ", "-")) else line for line in hunk if not line.startswith("+")]
    return exact, stripped


def hunk_new_sequence(hunk: list[str]) -> list[str]:
    result: list[str] = []
    for line in hunk:
        if line.startswith("+"):
            result.append(line[1:])
        elif line.startswith(" "):
            result.append(line[1:])
        elif not line.startswith("-"):
            result.append(line)
    return result


def apply_hunks(lines: list[str], hunks: list[list[str]], repo_path: str) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    working = list(lines)
    search_from = 0
    for hunk in hunks:
        old_exact, old_stripped = hunk_old_sequence(hunk)
        if not old_exact:
            issues.append(f"hunk has no removable/context lines: {repo_path}")
            continue
        index = sequence_index(working, old_exact, search_from)
        old_sequence = old_exact
        if index is None and old_stripped != old_exact:
            index = sequence_index(working, old_stripped, search_from)
            old_sequence = old_stripped
        if index is None:
            issues.append(f"hunk context not found in current file: {repo_path}")
            continue
        replacement = hunk_new_sequence(hunk)
        working[index : index + len(old_sequence)] = replacement
        search_from = index + len(replacement)
    return working, issues


def build_unified_diff(path: str, before: list[str], after: list[str]) -> str:
    diff_lines = difflib.unified_diff(
        before,
        after,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
    )
    return "\n".join(diff_lines).rstrip() + "\n"


def _read_changed_files(validation_summary: dict[str, Any]) -> list[str]:
    raw = validation_summary.get("touched_files")
    if not isinstance(raw, list) or not raw:
        raw = validation_summary.get("changed_files")
    if not isinstance(raw, list) or not raw:
        raise SystemExit("validation_summary.json does not contain non-empty touched_files or changed_files.")
    return [normalize_repo_path(str(item)) for item in raw if str(item).strip()]


def _build_source_file_snapshots(working_directory: Path, changed_files: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    snapshots: dict[str, dict[str, Any]] = {}
    missing_files: list[str] = []
    for rel_path in changed_files:
        file_path = working_directory / rel_path
        if not file_path.exists() or not file_path.is_file():
            missing_files.append(rel_path)
            continue
        raw = file_path.read_bytes()
        snapshots[rel_path] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    return snapshots, missing_files


def _copy_or_synthesize_run_log(source_run_dir: Path, output_dir: Path, name: str, fallback: str) -> None:
    source = source_run_dir / name
    if source.exists():
        shutil.copy2(source, output_dir / name)
        return
    write_text(output_dir / name, fallback)


def _copy_input_package(source_run_dir: Path, output_dir: Path) -> dict[str, Any]:
    source = source_run_dir / "input_package.json"
    if not source.exists():
        raise SystemExit("source input_package.json is required for execution_write_apply_candidate normalization.")
    shutil.copy2(source, output_dir / "input_package.json")
    return load_json(source)


def _build_diff_from_calls(
    *,
    working_directory: Path,
    calls: list[dict[str, Any]],
    allowed_files: list[str],
) -> tuple[str, list[str], list[str]]:
    issues: list[str] = []
    allowed = set(allowed_files)
    original_by_path: dict[str, list[str]] = {}
    working_by_path: dict[str, list[str]] = {}
    touched_order: list[str] = []

    def ensure_file(repo_path: str) -> list[str]:
        normalized = normalize_repo_path(repo_path)
        if normalized not in allowed:
            issues.append(f"patch touches files outside allowlist: {normalized}")
        if normalized not in working_by_path:
            file_path = working_directory / normalized
            if not file_path.exists() or not file_path.is_file():
                issues.append(f"working tree file missing: {normalized}")
                original_by_path[normalized] = []
                working_by_path[normalized] = []
            else:
                lines = file_path.read_text(encoding="utf-8-sig").splitlines()
                original_by_path[normalized] = list(lines)
                working_by_path[normalized] = list(lines)
            touched_order.append(normalized)
        return working_by_path[normalized]

    for call in calls:
        call_type = str(call.get("type") or "")
        if call_type == "openrouter:apply_patch":
            operation_type = str(call.get("operation_type") or "")
            repo_path = normalize_repo_path(str(call.get("path") or ""))
            if operation_type != "update_file":
                issues.append(f"unsupported apply_patch operation type: {operation_type or 'missing'}")
                continue
            hunks, hunk_issues = parse_unified_hunks(str(call.get("diff") or ""))
            issues.extend(hunk_issues)
            if hunk_issues:
                continue
            file_lines = ensure_file(repo_path)
            updated, apply_issues = apply_hunks(file_lines, hunks, repo_path)
            issues.extend(apply_issues)
            working_by_path[repo_path] = updated
            continue

        patch_text = str(call.get("patch") or "")
        sections, section_issues = extract_patch_sections(patch_text)
        issues.extend(section_issues)
        if section_issues:
            continue
        for section in sections:
            repo_path = normalize_repo_path(str(section["path"]))
            file_lines = ensure_file(repo_path)
            updated, apply_issues = apply_hunks(file_lines, list(section.get("hunks") or []), repo_path)
            issues.extend(apply_issues)
            working_by_path[repo_path] = updated

    diff_parts: list[str] = []
    changed_files: list[str] = []
    for repo_path in touched_order:
        before = original_by_path.get(repo_path, [])
        after = working_by_path.get(repo_path, [])
        if before == after:
            continue
        diff_parts.append(build_unified_diff(repo_path, before, after))
        changed_files.append(repo_path)
    if not changed_files and not issues:
        issues.append("normalized patch produced no file changes")
    return "\n".join(part.rstrip() for part in diff_parts if part.strip()).rstrip() + "\n", changed_files, issues


def build_normalized_package(
    source_run_dir: Path,
    output_dir: Path,
    *,
    working_directory: Path = REPO_ROOT,
) -> dict[str, Any]:
    operator_summary = load_json(source_run_dir / "operator_summary.json")
    validation_summary = load_json(source_run_dir / "validation_summary.json")
    calls_payload = load_json(source_run_dir / "apply_patch_calls.json")
    calls = calls_payload.get("calls")
    if not isinstance(calls, list) or not calls:
        raise SystemExit("apply_patch_calls.json does not contain non-empty calls.")
    if operator_summary.get("validation_result") != "PASS":
        raise SystemExit("source operator_summary validation_result must be PASS")
    if operator_summary.get("final_outcome") not in ACCEPTED_OUTCOMES:
        raise SystemExit("source operator_summary final_outcome is not an accepted apply_patch proposal outcome")
    if validation_summary.get("validation_result") != "PASS":
        raise SystemExit("source validation_summary validation_result must be PASS")

    output_dir.mkdir(parents=True, exist_ok=True)
    input_package = _copy_input_package(source_run_dir, output_dir)
    allowed_files = [normalize_repo_path(str(item)) for item in input_package.get("allowed_files", [])]
    if not allowed_files:
        raise SystemExit("input_package.json does not contain non-empty allowed_files.")
    max_touched_files = int(input_package.get("max_touched_files", 0) or 0)
    if max_touched_files < 1:
        raise SystemExit("input_package.json max_touched_files must be >= 1.")

    source_touched_files = _read_changed_files(validation_summary)
    diff_text, changed_files, diff_issues = _build_diff_from_calls(
        working_directory=working_directory,
        calls=calls,
        allowed_files=allowed_files,
    )
    if diff_issues:
        raise SystemExit("; ".join(diff_issues))
    if set(changed_files) != set(source_touched_files):
        raise SystemExit("normalized changed files do not match source validation touched_files.")
    if len(changed_files) > max_touched_files:
        raise SystemExit("normalized changed files exceed max_touched_files.")

    source_file_snapshots, snapshot_missing_files = _build_source_file_snapshots(working_directory, changed_files)
    if snapshot_missing_files:
        raise SystemExit("source snapshot files missing: " + ", ".join(snapshot_missing_files))

    git_diff_path = output_dir / "git_diff.patch"
    changed_files_path = output_dir / "changed_files.txt"
    delegated_result_path = output_dir / "delegated_result.md"

    write_text(git_diff_path, diff_text)
    write_text(changed_files_path, "\n".join(changed_files) + "\n")
    write_text(
        delegated_result_path,
        "# Delegated Result\n\nAccepted OpenRouter apply_patch tool calls normalized for write-apply validation.\n\n```diff\n"
        + diff_text.rstrip()
        + "\n```\n",
    )

    normalized_validation = dict(validation_summary)
    normalized_validation["status"] = "PASS"
    normalized_validation["accepted_for_codex_patch_review"] = True
    normalized_validation["changed_files"] = changed_files
    normalized_validation["source_file_snapshots"] = source_file_snapshots
    write_json(output_dir / "validation_summary.json", normalized_validation)

    normalized_operator = dict(operator_summary)
    normalized_operator["validation_result"] = "PASS"
    normalized_operator["final_outcome"] = "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW"
    normalized_operator["operator_message"] = (
        "Normalized accepted OpenRouter apply_patch package for execution_write_apply_candidate validation. "
        "Codex still owns accept-or-reject, validation, and final task completion."
    )
    write_json(output_dir / "operator_summary.json", normalized_operator)

    write_json(
        output_dir / "summary.json",
        {
            "status": "PASS",
            "artifact_success": True,
            "git_diff": str(git_diff_path.resolve()),
            "changed_files": str(changed_files_path.resolve()),
            "normalized_from": str(source_run_dir.resolve()),
            "normalizer": "normalize_openrouter_apply_patch_for_write_apply",
        },
    )
    _copy_or_synthesize_run_log(source_run_dir, output_dir, "stdout.log", "normalized OpenRouter apply_patch source\n")
    _copy_or_synthesize_run_log(source_run_dir, output_dir, "stderr.log", "")
    _copy_or_synthesize_run_log(source_run_dir, output_dir, "exit_code.txt", "0\n")

    bridge_summary = {
        "status": "PASS",
        "source_run_dir": repo_rel(source_run_dir),
        "output_dir": repo_rel(output_dir),
        "changed_files": changed_files,
        "source_snapshot_count": len(source_file_snapshots),
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
    parser = argparse.ArgumentParser(description="Normalize accepted OpenRouter apply_patch output for write-apply validation.")
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--working-directory", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    source_run_dir = args.source_run_dir.resolve()
    if not source_run_dir.exists():
        raise SystemExit(f"source run dir does not exist: {source_run_dir}")

    output_dir = args.output_dir.resolve() if args.output_dir else (DEFAULT_OUTPUT_ROOT / args.workflow_id).resolve()
    summary = build_normalized_package(
        source_run_dir,
        output_dir,
        working_directory=args.working_directory.resolve(),
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
