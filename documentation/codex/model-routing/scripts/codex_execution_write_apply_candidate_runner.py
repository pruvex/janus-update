#!/usr/bin/env python3
"""Bounded helper for validated execution write-apply candidate flows."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "execution-write-apply-runs"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def normalize_touched_files(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return []


def _resolve_working_tree_path(working_directory: Path, rel_path: str) -> Path:
    return (working_directory / rel_path.replace("/", working_directory.anchor and "/" or "\\")).resolve()


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_choice(choice: str) -> str:
    value = choice.strip().lower()
    if value == "prompt":
        return "prompt"
    if value in {"local", "codex", "1"}:
        return "local"
    if value in {"delegated", "sidecar", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, delegated/2/sidecar")


def build_run_dir(workflow_id: str) -> Path:
    return RUN_ROOT / workflow_id


def prompt_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE GATE",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "choice_1": "Codex",
        "choice_2": "Delegated",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded workspace-write execution candidate backed by an accepted proposal-first execution package and Codex-owned acceptance",
        "operator_prompt_lines": [
            "Willst du 1 Codex das machen lassen?",
            "Oder 2 den bounded execution_write_apply_candidate Delegation-Pfad nutzen?",
        ],
        "boundaries": [
            "No delegated broad repo write authority",
            "No delegated test execution",
            "No delegated task completion claim",
            "Codex remains validation and acceptance owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex execution path. No delegated execution write-apply candidate path was used.",
    }


def validate_accepted_source(
    run_dir: Path,
    *,
    working_directory: Path | None = None,
    require_source_snapshots: bool = False,
) -> dict[str, Any]:
    input_path = run_dir / "input_package.json"
    validation_path = run_dir / "validation_summary.json"
    operator_path = run_dir / "operator_summary.json"
    delegated_result_path = run_dir / "delegated_result.md"
    summary_path = run_dir / "summary.json"
    diff_path = run_dir / "git_diff.patch"
    changed_files_path = run_dir / "changed_files.txt"
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    exit_code_path = run_dir / "exit_code.txt"

    issues: list[str] = []
    if not input_path.exists():
        issues.append("missing input_package.json")
    if not validation_path.exists():
        issues.append("missing validation_summary.json")
    if not operator_path.exists():
        issues.append("missing operator_summary.json")
    if not delegated_result_path.exists():
        issues.append("missing delegated_result.md")
    if not summary_path.exists():
        issues.append("missing summary.json")
    if not diff_path.exists():
        issues.append("missing git_diff.patch")
    if not changed_files_path.exists():
        issues.append("missing changed_files.txt")
    if not stdout_path.exists():
        issues.append("missing stdout.log")
    if not stderr_path.exists():
        issues.append("missing stderr.log")
    if not exit_code_path.exists():
        issues.append("missing exit_code.txt")

    input_payload: dict[str, Any] = load_json(input_path) if input_path.exists() else {}
    validation_payload: dict[str, Any] = load_json(validation_path) if validation_path.exists() else {}
    operator_payload: dict[str, Any] = load_json(operator_path) if operator_path.exists() else {}
    summary_payload: dict[str, Any] = load_json(summary_path) if summary_path.exists() else {}
    changed_files = []
    if changed_files_path.exists():
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    diff_text = diff_path.read_text(encoding="utf-8-sig") if diff_path.exists() else ""

    if input_payload.get("precheck_status") != "PRE-CHECK PASSED":
        issues.append("source precheck_status is not PRE-CHECK PASSED")
    allowed_files = input_payload.get("allowed_files")
    if not isinstance(allowed_files, list) or not allowed_files:
        issues.append("source allowed_files is empty")
    max_touched_files = input_payload.get("max_touched_files")
    if not isinstance(max_touched_files, int) or max_touched_files < 1:
        issues.append("source max_touched_files is invalid")
    if validation_payload.get("accepted_for_codex_patch_review") is not True:
        issues.append("accepted_for_codex_patch_review is not true")
    validation_status = validation_payload.get("status")
    if validation_status not in {None, "PASS"}:
        issues.append("validation_summary status is not PASS")
    validation_changed_files = validation_payload.get("changed_files")
    if summary_payload.get("status") != "PASS":
        issues.append("source summary status is not PASS")
    if not changed_files:
        issues.append("changed_files.txt is empty")
    if not diff_text.strip():
        issues.append("git_diff.patch is empty")
    if not isinstance(validation_changed_files, list) or not validation_changed_files:
        issues.append("source validation_summary changed_files is empty")
    else:
        if isinstance(allowed_files, list):
            for item in validation_changed_files:
                if item not in allowed_files:
                    issues.append(f"source changed file escapes allowlist: {item}")
        if isinstance(max_touched_files, int) and len(validation_changed_files) > max_touched_files:
            issues.append("source changed_files exceeds max_touched_files")
    if changed_files and isinstance(validation_changed_files, list) and changed_files != validation_changed_files:
        issues.append("changed_files.txt does not match validation_summary changed_files")
    if summary_payload.get("git_diff") and Path(str(summary_payload["git_diff"])).name != "git_diff.patch":
        issues.append("summary git_diff does not point to git_diff.patch")
    if summary_payload.get("changed_files") and Path(str(summary_payload["changed_files"])).name != "changed_files.txt":
        issues.append("summary changed_files does not point to changed_files.txt")
    if operator_payload.get("final_outcome") != "EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW":
        issues.append("source final_outcome is not EXECUTION_PATCH_CANDIDATE_READY_FOR_CODEX_REVIEW")
    if operator_payload.get("validation_result") != "PASS":
        issues.append("source operator validation_result is not PASS")

    source_file_snapshots = validation_payload.get("source_file_snapshots")
    if require_source_snapshots:
        if not isinstance(source_file_snapshots, dict) or not source_file_snapshots:
            issues.append("source_file_snapshots are required for live write validation")
        elif working_directory is None:
            issues.append("working_directory is required for live write snapshot validation")
        else:
            for rel_path, snapshot in source_file_snapshots.items():
                if not isinstance(snapshot, dict):
                    issues.append(f"source snapshot is malformed for {rel_path}")
                    continue
                expected_hash = str(snapshot.get("sha256") or "").strip().lower()
                if not expected_hash:
                    issues.append(f"source snapshot hash is missing for {rel_path}")
                    continue
                target_path = working_directory / rel_path
                if not target_path.exists() or not target_path.is_file():
                    issues.append(f"working tree file missing for source snapshot: {rel_path}")
                    continue
                observed_hash = _hash_file(target_path).lower()
                if observed_hash != expected_hash:
                    issues.append(f"working tree drift detected for source snapshot: {rel_path}")

    return {
        "input_path": str(input_path),
        "validation_path": str(validation_path),
        "operator_path": str(operator_path),
        "delegated_result_path": str(delegated_result_path),
        "summary_path": str(summary_path),
        "diff_path": str(diff_path),
        "changed_files_path": str(changed_files_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "exit_code_path": str(exit_code_path),
        "allowed_files": allowed_files,
        "max_touched_files": max_touched_files,
        "changed_files": changed_files,
        "issues": issues,
        "input_payload": input_payload,
        "validation_payload": validation_payload,
        "operator_payload": operator_payload,
        "summary_payload": summary_payload,
        "source_file_snapshots": source_file_snapshots,
    }


def build_sidecar_apply_prompt(validation: dict[str, Any]) -> str:
    input_payload = validation["input_payload"]
    changed_files = validation["changed_files"]
    source_run_dir = Path(validation["summary_path"]).parent
    delegated_result_path = source_run_dir / "delegated_result.md"
    diff_path = source_run_dir / "git_diff.patch"

    lines = [
        "You are executing a bounded workspace-write apply task inside the Janus repository.",
        "Apply the exact accepted patch from the provided artifact package to the repository working tree.",
        "Do not redesign the change. Do not add extra edits. Do not touch files outside the exact allowlist.",
        "Do not run git commands. Do not run tests. Do not claim task completion beyond the bounded write.",
        "",
        f"Accepted source package: {source_run_dir}",
        f"Patch artifact: {diff_path}",
        f"Review artifact: {delegated_result_path}",
        "",
        "Exact allowlisted files:",
        *[f"- {item}" for item in changed_files],
        "",
        f"Max touched files: {input_payload['max_touched_files']}",
        "",
        "Required behavior:",
        "1. Read the accepted patch artifact and apply that patch locally.",
        "2. If the patch cannot be applied cleanly, stop and explain why in the final message.",
        "3. Do not create new files, delete files, rename files, or move files.",
        "4. Keep the final message compact: changed files, whether apply succeeded, and any blocker.",
    ]
    return "\n".join(lines) + "\n"


def _capture_git_status(working_directory: Path, paths: list[str]) -> str:
    command = ["git", "status", "--short"]
    if paths:
        command.extend(["--", *paths])
    completed = run_command(command, working_directory)
    if completed.returncode == 0:
        return completed.stdout.strip()
    return f"GIT_STATUS_UNAVAILABLE (exit {completed.returncode})"


def _capture_hashes(working_directory: Path, paths: list[str]) -> dict[str, str | None]:
    hashes: dict[str, str | None] = {}
    for rel_path in paths:
        target_path = working_directory / rel_path
        hashes[rel_path] = _hash_file(target_path) if target_path.exists() and target_path.is_file() else None
    return hashes


def _extract_patch_files(diff_text: str) -> tuple[list[str], list[str]]:
    seen: list[str] = []
    issues: list[str] = []
    old_path: str | None = None
    new_path: str | None = None

    for raw_line in diff_text.splitlines():
        line = raw_line.strip()
        if line.startswith("rename from ") or line.startswith("rename to "):
            issues.append("patch contains rename metadata")
        if line.startswith("new file mode "):
            issues.append("patch contains new file metadata")
        if line.startswith("deleted file mode "):
            issues.append("patch contains deleted file metadata")
        if line.startswith("--- "):
            old_path = line[4:].strip()
            continue
        if line.startswith("+++ "):
            new_path = line[4:].strip()
            if old_path is None:
                issues.append("patch hunk is missing old path header")
                continue
            if old_path == "/dev/null" or new_path == "/dev/null":
                issues.append("patch contains file create/delete path")
                old_path = None
                new_path = None
                continue
            normalized_old = old_path[2:] if old_path.startswith("a/") else old_path
            normalized_new = new_path[2:] if new_path.startswith("b/") else new_path
            if normalized_old != normalized_new:
                issues.append("patch contains path move or rename")
            elif normalized_new not in seen:
                seen.append(normalized_new)
            old_path = None
            new_path = None

    if not seen:
        issues.append("patch does not declare any target files")
    return seen, issues


def invoke_local_apply_run(
    *,
    run_directory: Path,
    working_directory: Path,
    source_diff_path: Path,
    editable_paths: list[str],
    max_touched_files: int,
) -> subprocess.CompletedProcess[str]:
    run_directory.mkdir(parents=True, exist_ok=True)
    diff_text = read_text(source_diff_path)
    write_text(run_directory / "source_git_diff.patch", diff_text)

    patch_files, patch_issues = _extract_patch_files(diff_text)
    allowlist_ok = set(patch_files) == set(editable_paths)
    delete_rename_move_ok = not patch_issues
    pre_run_status = _capture_git_status(working_directory, editable_paths)
    pre_hashes = _capture_hashes(working_directory, editable_paths)

    check_completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
    apply_completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
    apply_attempted = False
    local_issues = list(patch_issues)

    if not allowlist_ok:
        local_issues.append("patch target files do not match expected changed_files allowlist")

    if delete_rename_move_ok and allowlist_ok:
        apply_attempted = True
        check_completed = run_command(
            ["git", "apply", "--check", "--verbose", "--whitespace=nowarn", str(source_diff_path)],
            working_directory,
        )
        if check_completed.returncode == 0:
            apply_completed = run_command(
                ["git", "apply", "--verbose", "--whitespace=nowarn", str(source_diff_path)],
                working_directory,
            )
        else:
            local_issues.append(f"git apply --check failed with exit code {check_completed.returncode}")

    post_run_status = _capture_git_status(working_directory, editable_paths)
    post_hashes = _capture_hashes(working_directory, editable_paths)
    touched_files = [item for item in editable_paths if pre_hashes.get(item) != post_hashes.get(item)]
    touched_file_cap_ok = len(touched_files) <= max_touched_files
    if not touched_file_cap_ok:
        local_issues.append("touched files exceed max_touched_files")

    diff_completed = run_command(["git", "diff", "--", *editable_paths], working_directory)
    diff_output = diff_completed.stdout if diff_completed.returncode == 0 else ""
    if not diff_output.strip():
        diff_output = diff_text
    write_text(run_directory / "git_diff.patch", diff_output)
    write_text(run_directory / "changed_files.txt", "\n".join(touched_files) + ("\n" if touched_files else ""))
    write_text(run_directory / "pre_run_status.txt", pre_run_status + ("\n" if pre_run_status else ""))
    write_text(run_directory / "post_run_status.txt", post_run_status + ("\n" if post_run_status else ""))
    write_text(run_directory / "stdout.log", check_completed.stdout + apply_completed.stdout)
    write_text(run_directory / "stderr.log", check_completed.stderr + apply_completed.stderr)
    write_text(run_directory / "exit_code.txt", f"{apply_completed.returncode if apply_attempted else check_completed.returncode}\n")

    artifact_success = (
        apply_attempted
        and check_completed.returncode == 0
        and apply_completed.returncode == 0
        and allowlist_ok
        and delete_rename_move_ok
        and touched_file_cap_ok
    )
    last_message = (
        f"Apply succeeded: {'yes' if artifact_success else 'no'}.\n"
        f"Touched files: {', '.join(touched_files) if touched_files else '(none)'}\n"
    )
    if local_issues:
        last_message += "Issues:\n" + "\n".join(f"- {issue}" for issue in local_issues) + "\n"
    write_text(run_directory / "last_message.md", last_message)

    write_json(
        run_directory / "summary.json",
        {
            "status": "PASS" if artifact_success else "FAIL",
            "artifact_success": artifact_success,
            "mode": "deterministic_local_patch_apply",
            "patch_target_files": patch_files,
            "expected_files": editable_paths,
        },
    )
    write_json(
        run_directory / "validation_summary.json",
        {
            "allowlist_ok": allowlist_ok,
            "touched_file_cap_ok": touched_file_cap_ok,
            "delete_rename_move_ok": delete_rename_move_ok,
            "touched_files": touched_files,
            "patch_issues": patch_issues,
        },
    )

    return subprocess.CompletedProcess(
        args=["git", "apply", str(source_diff_path)],
        returncode=0 if artifact_success else 1,
        stdout=check_completed.stdout + apply_completed.stdout,
        stderr=check_completed.stderr + apply_completed.stderr,
    )


def delegated_live_from_accepted_source(
    *,
    run_dir: Path,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    working_directory: Path,
    source_run_dir: Path,
) -> tuple[int, dict[str, Any]]:
    validation = validate_accepted_source(
        source_run_dir,
        working_directory=working_directory,
        require_source_snapshots=True,
    )
    write_json(run_dir / "source_validation.json", validation)
    if validation["issues"]:
        result = {
            "summary_header": "EXECUTION WRITE APPLY CANDIDATE RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-executioner",
            "task_label": task_label,
            "selected_path": "delegated_execution_write_apply_candidate_local_apply_live",
            "normal_target_model": normal_target_model,
            "delegated_model_label": "Accepted OR patch package / deterministic local apply",
            "validation_result": "FAIL",
            "final_outcome": "INVALID_ACCEPTED_SOURCE_PACKAGE",
            "accepted_source_run_dir": str(source_run_dir),
            "source_validation_path": str(run_dir / "source_validation.json"),
            "operator_message": "Accepted source package failed bounded validation before live write execution.",
        }
        return 1, result

    instructions_path = run_dir / "apply_instructions.md"
    write_text(instructions_path, build_sidecar_apply_prompt(validation))

    apply_run_dir = run_dir / "local_apply_run"
    completed = invoke_local_apply_run(
        run_directory=apply_run_dir,
        source_diff_path=source_run_dir / "git_diff.patch",
        editable_paths=validation["changed_files"],
        max_touched_files=int(validation["max_touched_files"]),
        working_directory=working_directory,
    )
    write_text(run_dir / "runner_stdout.txt", completed.stdout)
    write_text(run_dir / "runner_stderr.txt", completed.stderr)

    summary_path = apply_run_dir / "summary.json"
    validation_path = apply_run_dir / "validation_summary.json"
    pre_run_status_path = apply_run_dir / "pre_run_status.txt"
    post_run_status_path = apply_run_dir / "post_run_status.txt"
    last_message_path = apply_run_dir / "last_message.md"
    summary_payload = load_json(summary_path) if summary_path.exists() else {}
    apply_validation_payload = load_json(validation_path) if validation_path.exists() else {}
    touched_files = normalize_touched_files(apply_validation_payload.get("touched_files"))
    expected_files = validation["changed_files"]
    pre_run_status = read_text(pre_run_status_path).strip()
    post_run_status = read_text(post_run_status_path).strip()
    last_message = read_text(last_message_path).strip()
    apply_succeeded = "apply succeeded" in last_message.casefold() and "apply succeeded: no" not in last_message.casefold()
    git_diff_text = read_text(apply_run_dir / "git_diff.patch").strip()

    issues: list[str] = []
    if completed.returncode != 0:
        issues.append(f"local apply runner exit code was {completed.returncode}")
    if summary_payload.get("status") != "PASS":
        issues.append("local apply summary status is not PASS")
    if summary_payload.get("artifact_success") is not True and not (
        apply_succeeded
        and apply_validation_payload.get("allowlist_ok") is True
        and apply_validation_payload.get("touched_file_cap_ok") is True
        and apply_validation_payload.get("delete_rename_move_ok") is True
        and bool(git_diff_text)
    ):
        issues.append("local apply artifact_success is not true")
    if apply_validation_payload.get("allowlist_ok") is not True:
        issues.append("local apply allowlist_ok is not true")
    if apply_validation_payload.get("touched_file_cap_ok") is not True:
        issues.append("local apply touched_file_cap_ok is not true")
    if apply_validation_payload.get("delete_rename_move_ok") is not True:
        issues.append("local apply delete_rename_move_ok is not true")
    if touched_files != expected_files:
        issues.append("local apply touched_files do not match expected changed_files")
    if pre_run_status == post_run_status and not (
        apply_succeeded and touched_files == expected_files and bool(git_diff_text)
    ):
        issues.append("local apply pre_run_status and post_run_status are identical")
    if "apply succeeded: no" in last_message.casefold():
        issues.append("local apply last_message reports apply failed")
    if not (apply_run_dir / "git_diff.patch").exists():
        issues.append("local apply git_diff.patch is missing")
    elif not git_diff_text:
        issues.append("local apply git_diff.patch is empty")

    live_validation = {
        "workflow_id": workflow_id,
        "mode": "execution_write_apply_candidate_local_apply_live",
        "accepted_source_run_dir": str(source_run_dir),
        "source_validation_path": str(run_dir / "source_validation.json"),
        "local_apply_run_dir": str(apply_run_dir),
        "expected_changed_files": expected_files,
        "touched_files": touched_files,
        "pre_run_status": pre_run_status,
        "post_run_status": post_run_status,
        "apply_succeeded": apply_succeeded,
        "last_message_excerpt": last_message[:500],
        "issues": issues,
        "local_apply_summary_path": str(summary_path),
        "local_apply_validation_path": str(validation_path),
    }
    write_json(run_dir / "live_validation_summary.json", live_validation)

    validation_pass = not issues
    result = {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": task_label,
        "selected_path": "delegated_execution_write_apply_candidate_local_apply_live",
        "normal_target_model": normal_target_model,
        "delegated_model_label": "Accepted OR patch package / deterministic local apply",
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": (
            "EXECUTION_WRITE_APPLY_LIVE_WRITE_READY_FOR_CODEX_ACCEPT_REJECT"
            if validation_pass
            else "EXECUTION_WRITE_APPLY_LIVE_WRITE_REJECT_AND_FALLBACK"
        ),
        "accepted_source_run_dir": str(source_run_dir),
        "source_validation_path": str(run_dir / "source_validation.json"),
        "live_validation_summary_path": str(run_dir / "live_validation_summary.json"),
        "apply_instructions_path": str(instructions_path),
        "local_apply_run_dir": str(apply_run_dir),
        "runner_summary_path": str(summary_path),
        "operator_message": (
            "Delegated bounded live write completed via deterministic local patch apply inside the exact accepted-source allowlist. Codex still owns diff review, acceptance, and final task completion."
            if validation_pass
            else "Delegated bounded live write failed bounded local-apply validation. Fallback to Codex-only execution is required."
        ),
    }
    return (0 if validation_pass else 1), result


def main_with_args(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded execution write apply candidate helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default="bounded workspace-write execution candidate / accepted proposal-first evidence path")
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    parser.add_argument("--sidecar-model", default="gpt-5.4")
    parser.add_argument("--sidecar-timeout-seconds", type=int, default=180)
    parser.add_argument("--working-directory", type=Path, default=REPO_ROOT)
    parser.add_argument("--execute-live-sidecar", action="store_true")
    args = parser.parse_args(argv)

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"EXECUTION-WRITE-APPLY-CANDIDATE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
        )
        write_json(run_dir / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = local_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
        )
        write_json(run_dir / "operator_choice_local.json", result)
        output(result)
        return 0

    if args.accepted_source_run_dir is None:
        raise SystemExit("--accepted-source-run-dir is required for operator-choice delegated in local validation mode")

    source_run_dir = args.accepted_source_run_dir.resolve()
    if args.execute_live_sidecar:
        exit_code, result = delegated_live_from_accepted_source(
            run_dir=run_dir,
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            working_directory=args.working_directory.resolve(),
            source_run_dir=source_run_dir,
        )
        write_json(run_dir / "operator_summary.json", result)
        output(result)
        return exit_code

    validation = validate_accepted_source(source_run_dir)
    write_json(run_dir / "source_validation.json", validation)

    validation_pass = not validation["issues"]
    operator_summary = {
        "summary_header": "EXECUTION WRITE APPLY CANDIDATE RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-executioner",
        "task_label": args.task_label,
        "selected_path": "delegated_execution_write_apply_candidate",
        "normal_target_model": args.normal_target_model,
        "delegated_model_label": args.delegated_model_label,
        "validation_result": "PASS" if validation_pass else "FAIL",
        "final_outcome": (
            "EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_CODEX_ACCEPT_REJECT"
            if validation_pass
            else "EXECUTION_WRITE_APPLY_CANDIDATE_REJECT_AND_FALLBACK"
        ),
        "accepted_source_run_dir": str(source_run_dir),
        "source_validation_path": str(run_dir / "source_validation.json"),
        "operator_message": (
            "Delegated execution write-apply candidate is backed by an accepted proposal-first execution package with required validation artifacts present. Codex still owns the explicit accept-or-reject decision, any future live write approval, and final task acceptance."
            if validation_pass
            else "Accepted-source validation failed. Fallback to Codex-only execution is required."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_pass else 1


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
