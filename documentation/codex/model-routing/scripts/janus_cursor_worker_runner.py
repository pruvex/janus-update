#!/usr/bin/env python3
"""Bounded Cursor worker wrapper for tri-modal delegation.

This runner is intentionally conservative: it validates the bounded Cursor
contract, writes deterministic artifacts, and blocks live execution unless the
caller explicitly opts in. Unit tests mock subprocess execution; production
calls remain approval-gated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
CURSOR_RUNS_DIR = MODEL_ROUTING_DIR / "cursor-worker-runs"
CURSOR_DELEGATION_LOG_PATH = MODEL_ROUTING_DIR / "cursor_delegation_log.jsonl"
SCRIPTS_DIR = MODEL_ROUTING_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from delegation_routing import DEFAULT_MANIFEST_PATH, estimate_run_cost_usd, find_lane, lane_cursor_model, load_manifest  # noqa: E402
from janus_worker_contract import validate_worker_task_package_file  # noqa: E402


FORBIDDEN_ALLOWLIST_MARKERS = (".git", "node_modules", "dist", "build", ".env")
DEFAULT_AGENT_PATHS = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "cursor-agent" / "agent.cmd",
    Path(os.environ.get("LOCALAPPDATA", "")) / "cursor-agent" / "agent.ps1",
    Path(os.environ.get("LOCALAPPDATA", "")) / "cursor-agent" / "agent.exe",
    Path.home() / ".local" / "bin" / "agent.exe",
    Path.home() / ".local" / "bin" / "agent",
)
ACCEPTED_SOURCE_REQUIRED_LANES = {"execution_write_apply_candidate"}
ACCEPTED_SOURCE_REQUIRED_ARTIFACTS = (
    "dispatcher_result.json",
    "validation_summary.json",
    "operator_summary.json",
    "summary.json",
    "cursor_response.json",
    "git_diff.patch",
    "changed_files.txt",
)
DEFAULT_LIVE_TIMEOUT_SECONDS = 180
ASSIST_OR_REVIEW_TIMEOUT_SECONDS = 180
SINGLE_FILE_TOOL_TIMEOUT_SECONDS = 240
MULTI_FILE_TOOL_TIMEOUT_SECONDS = 300
EXPLICIT_NO_OP_PACKAGE_KEYS = (
    "explicit_no_op_ok",
    "allow_zero_file_pass",
    "cursor_explicit_no_op",
)


def resolve_live_timeout_seconds(
    *,
    cursor_config: dict[str, Any],
    allowlist: list[str],
) -> tuple[int, str]:
    env_override = os.environ.get("JANUS_CURSOR_LIVE_TIMEOUT_SECONDS")
    if env_override is not None and str(env_override).strip():
        return int(str(env_override).strip()), "env_override"
    mode = str(cursor_config.get("mode") or "")
    allow_write = bool(cursor_config.get("allow_write"))
    if mode in {"assist_only", "review_only"} or not allow_write:
        return ASSIST_OR_REVIEW_TIMEOUT_SECONDS, "assist_or_review_default"
    if len(allowlist) <= 1:
        return SINGLE_FILE_TOOL_TIMEOUT_SECONDS, "single_file_tool_lane"
    return MULTI_FILE_TOOL_TIMEOUT_SECONDS, "multi_file_tool_lane"


def package_allows_explicit_no_op(package_payload: dict[str, Any] | None) -> bool:
    if not isinstance(package_payload, dict):
        return False
    return any(package_payload.get(key) is True for key in EXPLICIT_NO_OP_PACKAGE_KEYS)


def write_capable_lane_requires_file_changes(
    *,
    cursor_config: dict[str, Any],
    package_payload: dict[str, Any] | None,
) -> bool:
    if bool(cursor_config.get("allow_write")) is not True:
        return False
    mode = str(cursor_config.get("mode") or "")
    if mode not in {"proposal_first"}:
        return False
    return not package_allows_explicit_no_op(package_payload)


def classify_live_run_outcome(
    *,
    completed: subprocess.CompletedProcess[str],
    changed_files: list[str],
    changed_outside_allowlist: list[str],
    cursor_config: dict[str, Any],
    package_payload: dict[str, Any] | None,
) -> dict[str, str]:
    if completed.returncode != 0:
        return {
            "transport_result": "TRANSPORT_FAIL",
            "semantic_result": "SEMANTIC_FAIL",
            "validation_result": "FAIL",
            "final_outcome": "CURSOR_AGENT_EXIT_NONZERO",
            "operator_message": "Cursor agent returned a non-zero exit code.",
        }
    if changed_outside_allowlist:
        return {
            "transport_result": "TRANSPORT_FAIL",
            "semantic_result": "SEMANTIC_FAIL",
            "validation_result": "FAIL",
            "final_outcome": "CURSOR_ALLOWLIST_VIOLATION",
            "operator_message": "Cursor changed files outside the bounded allowlist.",
        }
    if write_capable_lane_requires_file_changes(
        cursor_config=cursor_config,
        package_payload=package_payload,
    ) and not changed_files:
        return {
            "transport_result": "TRANSPORT_PASS",
            "semantic_result": "SEMANTIC_FAIL",
            "validation_result": "FAIL",
            "final_outcome": "CURSOR_SEMANTIC_FAIL_NO_CHANGES",
            "operator_message": (
                "Cursor agent finished without allowlisted file changes on a write-capable lane. "
                "Treat as semantic failure; do not accept the result."
            ),
        }
    return {
        "transport_result": "TRANSPORT_PASS",
        "semantic_result": "SEMANTIC_PASS",
        "validation_result": "PASS",
        "final_outcome": "CURSOR_WORKER_READY_FOR_CODEX_REVIEW",
        "operator_message": "Cursor worker finished the bounded slice and returned artifacts for Codex review.",
    }


def resolve_agent_binary() -> str | None:
    from shutil import which

    for candidate in ("agent", "agent.cmd", "agent.exe"):
        found = which(candidate)
        if found:
            return found
    for path in DEFAULT_AGENT_PATHS:
        if path.exists():
            return str(path)
    return None


def agent_cli_missing_result() -> dict[str, Any]:
    return {
        "validation_result": "BLOCKED",
        "final_outcome": "CURSOR_AGENT_CLI_MISSING",
        "operator_message": (
            "Cursor Agent CLI is not installed. Run: "
            "irm 'https://cursor.com/install?win32=true' | iex "
            "Then open a fresh terminal and verify with: agent --version"
        ),
    }


def validate_package_or_worker_reference(package_path: Path | None) -> dict[str, Any]:
    if package_path is None:
        return {
            "validation_result": "PASS",
            "contract_status": "TASK_PACKAGE_NOT_BOUND",
            "issues": [],
            "task_label": "N_A",
        }

    direct_validation = validate_worker_task_package_file(package_path)
    if direct_validation["validation_result"] == "PASS":
        return direct_validation

    try:
        package = json.loads(package_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return direct_validation

    worker_package_json = package.get("worker_package_json")
    if not isinstance(worker_package_json, str) or not worker_package_json.strip():
        return direct_validation

    worker_package_path = REPO_ROOT / worker_package_json.replace("\\", "/")
    worker_validation = validate_worker_task_package_file(worker_package_path)
    if worker_validation["validation_result"] != "PASS":
        return direct_validation

    worker_validation = dict(worker_validation)
    worker_validation["contract_status"] = "TASK_PACKAGE_VALID_VIA_WORKER_REFERENCE"
    worker_validation["source_package_path"] = str(package_path)
    worker_validation["worker_package_path"] = str(worker_package_path)
    return worker_validation


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_optional_package(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError):
        return {}


def load_prompt_text_from_package(package: dict[str, Any], *, base_path: Path | None = None) -> str:
    prompt = package.get("task_prompt")
    if isinstance(prompt, str) and prompt.strip():
        return prompt.strip()

    prompt_path_value = package.get("task_prompt_path")
    if not isinstance(prompt_path_value, str) or not prompt_path_value.strip():
        return ""

    resolved_base = base_path.parent if base_path is not None else REPO_ROOT
    prompt_path = (resolved_base / prompt_path_value.replace("\\", "/")).resolve()
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8-sig")
    except OSError:
        return ""
    return prompt_text.strip()


def load_allowlist(path: Path | None) -> list[str]:
    if path is None:
        return []
    if not path.exists():
        raise SystemExit(f"Allowlist file does not exist: {path}")
    return [line.strip().replace("\\", "/") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_allowlist(paths: list[str]) -> dict[str, Any]:
    issues: list[str] = []
    if not paths:
        issues.append("allowlist must contain at least one path")
    for item in paths:
        lowered = item.lower()
        if item.startswith("/") or ":" in item:
            issues.append(f"allowlist path must be repository-relative: {item}")
        if ".." in Path(item).parts:
            issues.append(f"allowlist path must not contain parent traversal: {item}")
        if any(marker in lowered for marker in FORBIDDEN_ALLOWLIST_MARKERS):
            issues.append(f"allowlist path contains forbidden marker: {item}")
    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "allowlist": paths,
    }


def validate_allowlist_consistency(
    *,
    declared_allowlist_file: Path | None,
    package_allowed_edit_paths: list[str],
    allowlist: list[str],
) -> dict[str, Any]:
    normalized_package = [item.replace("\\", "/") for item in package_allowed_edit_paths]
    normalized_allowlist = [item.replace("\\", "/") for item in allowlist]
    issues: list[str] = []
    if declared_allowlist_file is not None and normalized_package and set(normalized_package) != set(normalized_allowlist):
        issues.append("allowed_edit_paths must exactly match the provided allowlist entries")
    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "package_allowed_edit_paths": normalized_package,
        "allowlist": normalized_allowlist,
        "declared_allowlist_file": str(declared_allowlist_file) if declared_allowlist_file is not None else None,
    }


def path_is_allowlisted(path: str, allowlist: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    for allowed in allowlist:
        prefix = allowed.rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def derive_workspace_root(allowlist: list[str]) -> Path:
    resolved_files: list[Path] = []
    for item in allowlist:
        absolute = (REPO_ROOT / item).resolve()
        if absolute.exists():
            resolved_files.append(absolute if absolute.is_dir() else absolute.parent)
            continue
        resolved_files.append(absolute.parent)
    if not resolved_files:
        return REPO_ROOT
    common_root = Path(os.path.commonpath([str(path) for path in resolved_files]))
    try:
        common_root.relative_to(REPO_ROOT)
    except ValueError:
        return REPO_ROOT
    return common_root


def workspace_relative_allowlist(allowlist: list[str], workspace_root: Path) -> list[str]:
    relative_items: list[str] = []
    for item in allowlist:
        absolute = (REPO_ROOT / item).resolve()
        try:
            relative_items.append(str(absolute.relative_to(workspace_root)).replace("\\", "/"))
        except ValueError:
            return []
    return relative_items


def build_cursor_agent_command(
    *,
    agent_binary: str,
    model: str,
    task_prompt: str,
    workspace: Path,
    mode: str,
    resume_session_id: str | None,
) -> list[str]:
    command = [
        agent_binary,
        "-p",
        "--workspace",
        str(workspace),
        "--model",
        model,
        "--output-format",
        "json",
    ]
    if mode != "assist_only":
        command.extend(["--force", "--trust", "--approve-mcps"])
    if resume_session_id:
        command.extend(["--resume", resume_session_id])
    command.append(task_prompt)
    return command


def infer_cursor_pool(model: str, explicit_pool: str | None) -> str:
    if explicit_pool in {"auto_composer", "api"}:
        return explicit_pool
    return "auto_composer" if model in {"auto", "composer-2.5"} else "api"


def run_command(
    command: list[str],
    *,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


def coerce_timeout_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def invoke_agent_command(
    command: list[str],
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=timeout_seconds,
            output=stdout,
            stderr=stderr,
        )
    return subprocess.CompletedProcess(
        args=command,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def parse_json_response(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Cursor response must be a JSON object")
    return parsed


def changed_files_from_git(paths: list[str] | None = None) -> list[str]:
    command = ["git", "diff", "--name-only"]
    if paths:
        command.append("--")
        command.extend(paths)
    completed = run_command(command)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def snapshot_file_hashes(paths: list[str]) -> dict[str, str | None]:
    snapshot: dict[str, str | None] = {}
    for relative_path in paths:
        absolute_path = REPO_ROOT / relative_path
        if not absolute_path.exists() or not absolute_path.is_file():
            snapshot[relative_path] = None
            continue
        digest = hashlib.sha256(absolute_path.read_bytes()).hexdigest()
        snapshot[relative_path] = digest
    return snapshot


def lane_cursor_config(manifest: dict[str, Any], lane_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    lane = find_lane(manifest, lane_id)
    if lane is None:
        raise SystemExit(f"Unknown lane: {lane_id}")
    cursor = lane.get("cursor")
    if not isinstance(cursor, dict):
        raise SystemExit(f"Lane {lane_id} has no cursor configuration")
    return lane, cursor


def accepted_source_requirement(*, lane_id: str, lane: dict[str, Any], package_path: Path | None) -> bool:
    if lane_id in ACCEPTED_SOURCE_REQUIRED_LANES:
        return True
    cursor = lane.get("cursor")
    if isinstance(cursor, dict) and cursor.get("requires_accepted_source") is True:
        return True
    if package_path is None:
        return False
    try:
        package = load_json(package_path)
    except (OSError, json.JSONDecodeError):
        return False
    return package.get("requires_accepted_source") is True


def resolve_accepted_source_run_dir(explicit_path: Path | None, package_path: Path | None) -> Path | None:
    if explicit_path is not None:
        return explicit_path
    if package_path is None:
        return None
    try:
        package = load_json(package_path)
    except (OSError, json.JSONDecodeError):
        return None
    candidate = package.get("accepted_source_run_dir")
    if not isinstance(candidate, str) or not candidate.strip():
        return None
    return REPO_ROOT / candidate.replace("\\", "/")


def validate_accepted_source_run_dir(path: Path | None, *, required: bool) -> dict[str, Any]:
    if path is None:
        return {
            "validation_result": "FAIL" if required else "PASS",
            "issues": ["accepted_source_run_dir is required"] if required else [],
            "accepted_source_run_dir": None,
            "recognized_artifacts": [],
        }
    resolved = path.resolve()
    issues: list[str] = []
    if not resolved.exists():
        issues.append("accepted_source_run_dir does not exist")
    elif not resolved.is_dir():
        issues.append("accepted_source_run_dir is not a directory")
    recognized = [name for name in ACCEPTED_SOURCE_REQUIRED_ARTIFACTS if (resolved / name).exists()] if not issues else []
    if resolved.exists() and resolved.is_dir() and not recognized:
        issues.append("accepted_source_run_dir does not contain recognized accepted-source artifacts")
    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "accepted_source_run_dir": str(resolved),
        "recognized_artifacts": recognized,
    }


def accepted_source_prompt_context(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_dir():
        return ""

    lines = [f"Accepted source run dir: {resolved}"]
    dispatcher_path = resolved / "dispatcher_result.json"
    if dispatcher_path.exists():
        try:
            dispatcher = load_json(dispatcher_path)
        except (OSError, json.JSONDecodeError):
            dispatcher = {}
        final_outcome = dispatcher.get("final_outcome")
        if isinstance(final_outcome, str) and final_outcome.strip():
            lines.append(f"Accepted source final outcome: {final_outcome.strip()}")
        changed_files = dispatcher.get("changed_files")
        if isinstance(changed_files, list):
            normalized = [str(item).strip() for item in changed_files if str(item).strip()]
            if normalized:
                lines.append("Accepted source changed files:\n- " + "\n- ".join(normalized))

    changed_files_path = resolved / "changed_files.txt"
    if changed_files_path.exists() and not any(line.startswith("Accepted source changed files:") for line in lines):
        changed_files = [line.strip() for line in changed_files_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if changed_files:
            lines.append("Accepted source changed files:\n- " + "\n- ".join(changed_files))

    response_path = resolved / "cursor_response.json"
    if response_path.exists():
        try:
            response = load_json(response_path)
        except (OSError, json.JSONDecodeError):
            response = {}
        summary = response.get("result") or response.get("summary")
        if isinstance(summary, str) and summary.strip():
            lines.append(f"Accepted source summary: {summary.strip()}")

    return "\n".join(lines)


def accepted_source_summary_line(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_dir():
        return ""
    response_path = resolved / "cursor_response.json"
    if not response_path.exists():
        return ""
    try:
        response = load_json(response_path)
    except (OSError, json.JSONDecodeError):
        return ""
    summary = response.get("result") or response.get("summary")
    return summary.strip() if isinstance(summary, str) and summary.strip() else ""


def task_prompt_from_package(package_path: Path | None, lane_id: str, allowlist: list[str]) -> str:
    if package_path is None:
        return (
            "Execute this bounded Janus delegated worker task now. Treat the full prompt below as instructions, not as text to analyze. Do not ask clarifying questions unless the task is impossible with the provided files and rules.\n\n"
            "Stable prefix:\n"
            f"- lane: {lane_id}\n"
            "- worker_contract: janus-delegated-worker\n"
            "- output_schema: status, changed_files, command_results, summary, blockers\n"
            "- hard_rules: stay bounded, do not commit, do not leave the allowlist\n\n"
            "Variable suffix:\n"
            "Run the bounded Cursor delegated worker for this lane. Keep changes inside the allowlist, run only bounded checks, and return a concise JSON summary."
        )
    try:
        package = json.loads(package_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return (
            "Execute this bounded Janus delegated worker task now. Treat the full prompt below as instructions, not as text to analyze. Do not ask clarifying questions unless the task is impossible with the provided files and rules.\n\n"
            "Stable prefix:\n"
            f"- lane: {lane_id}\n"
            "- worker_contract: janus-delegated-worker\n"
            "- output_schema: status, changed_files, command_results, summary, blockers\n"
            "- hard_rules: stay bounded, do not commit, do not leave the allowlist\n\n"
            "Variable suffix:\n"
            "The package could not be parsed inline; rely on the provided file path and return bounded JSON output."
        )
    prompt_parts: list[str] = [
        "Execute this bounded Janus delegated worker task now. Treat the full prompt below as instructions, not as text to analyze. Do not ask clarifying questions unless the task is impossible with the provided files and rules.",
        "",
        "Stable prefix:",
        f"- lane: {lane_id}",
        "- worker_contract: janus-delegated-worker",
        "- output_schema: status, changed_files, command_results, summary, blockers",
        "- hard_rules: stay bounded, do not commit, do not leave the allowlist",
        "",
        "Variable suffix:",
    ]
    suffix_parts: list[str] = []

    prompt_text = load_prompt_text_from_package(package, base_path=package_path)
    if prompt_text:
        suffix_parts.append(prompt_text)

    worker_package_json = package.get("worker_package_json")
    if not suffix_parts and isinstance(worker_package_json, str) and worker_package_json.strip():
        worker_package_path = REPO_ROOT / worker_package_json.replace("\\", "/")
        try:
            worker_package = json.loads(worker_package_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            worker_package = {}
        worker_prompt_text = load_prompt_text_from_package(worker_package, base_path=worker_package_path)
        if worker_prompt_text:
            suffix_parts.append(worker_prompt_text)

    task_label = package.get("task_label")
    if isinstance(task_label, str) and task_label.strip():
        suffix_parts.append(f"Task label: {task_label.strip()}")

    prompt_contract = package.get("cursor_prompt_contract")
    if isinstance(prompt_contract, str) and prompt_contract.strip():
        suffix_parts.append(prompt_contract.strip())

    acceptance = package.get("acceptance_criteria")
    if isinstance(acceptance, list) and acceptance:
        criteria = [item.strip() for item in acceptance if isinstance(item, str) and item.strip()]
        if criteria:
            suffix_parts.append("Acceptance criteria:\n- " + "\n- ".join(criteria))

    if allowlist:
        suffix_parts.append("Allowed edit paths:\n- " + "\n- ".join(allowlist))

    suffix_parts.append("Return status, changed_files, command_results, summary, and blockers as concise JSON-compatible output.")

    if suffix_parts:
        return "\n".join(prompt_parts + suffix_parts)

    return (
        "Execute this bounded Janus delegated worker task now. Treat the full prompt below as instructions, not as text to analyze. Do not ask clarifying questions unless the task is impossible with the provided files and rules.\n\n"
        "Stable prefix:\n"
        f"- lane: {lane_id}\n"
        "- worker_contract: janus-delegated-worker\n"
        "- output_schema: status, changed_files, command_results, summary, blockers\n"
        "- hard_rules: stay bounded, do not commit, do not leave the allowlist\n\n"
        "Variable suffix:\n"
        "Return status, changed_files, command_results, summary, and blockers."
    )


def minimal_write_apply_prompt(
    *,
    task_label: str,
    workspace_allowlist: list[str],
    validation_command: str,
    accepted_source_summary: str,
) -> str:
    lines = [
        "Execute this bounded Janus delegated worker task now. Treat the full prompt below as instructions, not as text to analyze. Do not ask clarifying questions unless the task is impossible with the provided files and rules.",
        "",
        "Stable prefix:",
        "- worker_contract: janus-delegated-worker",
        "- mode: minimal_write_apply",
        "- output_schema: status, changed_files, command_results, summary, blockers",
        "- hard_rules: stay bounded, do not commit, do not leave the allowlist",
        "",
        "Variable suffix:",
        f"Task: {task_label}",
        "Edit only the listed workspace files.",
        "Make exactly one bounded change that matches the accepted source summary.",
    ]
    if workspace_allowlist:
        lines.append("Files:\n- " + "\n- ".join(workspace_allowlist))
    if accepted_source_summary:
        lines.append(f"Accepted source summary: {accepted_source_summary}")
    if validation_command:
        lines.append(f"Run only this validation command: {validation_command}")
    lines.append("Do not commit. Return concise JSON with status, changed_files, command_results, summary, blockers.")
    return "\n\n".join(lines)


def minimal_worker_prompt(
    *,
    task_label: str,
    task_summary: str,
    workspace_allowlist: list[str],
    validation_command: str,
    acceptance_criteria: list[str],
) -> str:
    lines = [
        "Execute this bounded Janus delegated worker task now.",
        "",
        "Stable prefix:",
        "- worker_contract: janus-delegated-worker",
        "- mode: minimal_worker",
        "- output_schema: status, changed_files, command_results, summary, blockers",
        "- hard_rules: stay bounded, do not commit, do not leave the allowlist",
        "",
        "Variable suffix:",
        f"Task: {task_label}",
    ]
    if task_summary:
        lines.append(task_summary)
    if workspace_allowlist:
        lines.append("Files:\n- " + "\n- ".join(workspace_allowlist))
    if acceptance_criteria:
        lines.append("Acceptance:\n- " + "\n- ".join(acceptance_criteria))
    if validation_command:
        lines.append(f"Check: {validation_command}")
    lines.append("Return concise JSON with status, changed_files, command_results, summary, blockers.")
    return "\n\n".join(lines)


def run_dir_for(workflow_id: str) -> Path:
    return CURSOR_RUNS_DIR / workflow_id


def blocked_result(
    *,
    args: argparse.Namespace,
    lane_id: str,
    selected_model: str,
    validation_result: str,
    final_outcome: str,
    operator_message: str,
    package_validation: dict[str, Any],
    allowlist_validation: dict[str, Any],
    allowlist_consistency_validation: dict[str, Any],
    accepted_source_validation: dict[str, Any] | None = None,
    accepted_source_run_dir: str | None = None,
    session_id: str | None = None,
    cursor_pool: str | None = None,
    estimated_cost_usd_static: float | None = None,
) -> dict[str, Any]:
    result = {
        "backend": "cursor",
        "lane_id": lane_id,
        "workflow_id": args.workflow_id,
        "selected_model": selected_model,
        "cursor_pool": cursor_pool,
        "estimated_cost_usd_static": estimated_cost_usd_static,
        "session_id": session_id,
        "validation_result": validation_result,
        "selected_path": "cursor_worker_blocked",
        "final_outcome": final_outcome,
        "package_validation": package_validation,
        "allowlist_validation": allowlist_validation,
        "allowlist_consistency_validation": allowlist_consistency_validation,
        "codex_review_required": True,
        "operator_message": operator_message,
    }
    if accepted_source_validation is not None:
        result["accepted_source_validation"] = accepted_source_validation
    if accepted_source_run_dir is not None:
        result["accepted_source_run_dir"] = accepted_source_run_dir
    return result


def log_delegation_result(
    *,
    workflow_id: str,
    lane_id: str,
    model: str,
    cursor_pool: str,
    session_id: str | None,
    validation_result: str,
    changed_files_count: int,
    resume_used: bool,
    estimated_cost_usd_static: float | None,
    duration_ms: int | None = None,
    transport_result: str | None = None,
    semantic_result: str | None = None,
) -> None:
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workflow_id": workflow_id,
        "lane_id": lane_id,
        "model": model,
        "cursor_pool": cursor_pool,
        "session_id": session_id or "",
        "validation_result": validation_result,
        "changed_files_count": changed_files_count,
        "resume_used": resume_used,
        "estimated_cost_usd_static": estimated_cost_usd_static,
        "duration_ms": duration_ms,
    }
    if transport_result is not None:
        entry["transport_result"] = transport_result
    if semantic_result is not None:
        entry["semantic_result"] = semantic_result
    append_jsonl(
        CURSOR_DELEGATION_LOG_PATH,
        entry,
    )


def summarize(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_manifest(args.manifest)
    lane, cursor_config = lane_cursor_config(manifest, args.lane)
    assist_like_mode = str(cursor_config.get("mode") or "") in {"assist_only", "review_only"}
    default_lane_model = lane_cursor_model(lane, manifest, "auto_composer")
    if args.model is None and assist_like_mode:
        default_lane_model = "auto"
    preselected_model = args.model or default_lane_model or "auto"
    cursor_pool = infer_cursor_pool(preselected_model, args.cursor_pool)
    selected_model = args.model or (
        lane_cursor_model(lane, manifest, cursor_pool) if args.cursor_pool is not None else (preselected_model if assist_like_mode else lane_cursor_model(lane, manifest, cursor_pool))
    ) or preselected_model
    estimated_cost_usd_static = estimate_run_cost_usd(selected_model, manifest)
    mode = str(cursor_config.get("mode") or "assist_only")
    require_allowlist = bool(cursor_config.get("require_allowlist") is True or args.require_allowlist)
    allow_shell = bool(cursor_config.get("allow_shell") is True)
    allow_write = bool(cursor_config.get("allow_write") is True)

    package_validation = validate_package_or_worker_reference(args.input_package_json)
    allowlist = load_allowlist(args.allowlist_file)
    accepted_source_required = accepted_source_requirement(
        lane_id=args.lane,
        lane=lane,
        package_path=args.input_package_json,
    )
    accepted_source_run_dir = resolve_accepted_source_run_dir(args.accepted_source_run_dir, args.input_package_json)
    accepted_source_validation = validate_accepted_source_run_dir(
        accepted_source_run_dir,
        required=accepted_source_required,
    )
    allowlist_validation = (
        validate_allowlist(allowlist)
        if args.allowlist_file is not None
        else {
            "validation_result": "PASS" if not require_allowlist else "FAIL",
            "issues": [] if not require_allowlist else ["allowlist is required for this lane"],
            "allowlist": [],
        }
    )
    declared_allowlist_file = None
    if isinstance(package_payload := load_optional_package(args.input_package_json), dict):
        declared_allowlist_value = package_payload.get("allowlist_file")
        if isinstance(declared_allowlist_value, str) and declared_allowlist_value.strip():
            declared_allowlist_file = REPO_ROOT / declared_allowlist_value.replace("\\", "/")
    allowlist_consistency_validation = validate_allowlist_consistency(
        declared_allowlist_file=declared_allowlist_file,
        package_allowed_edit_paths=package_validation.get("allowed_edit_paths", []),
        allowlist=allowlist,
    )

    run_dir = run_dir_for(args.workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    task_prompt = task_prompt_from_package(args.input_package_json, args.lane, allowlist)
    workspace_root = derive_workspace_root(allowlist)
    workspace_allowlist = workspace_relative_allowlist(allowlist, workspace_root)
    prompt_mode = package_payload.get("cursor_prompt_mode") if isinstance(package_payload, dict) else None
    accepted_source_summary = accepted_source_summary_line(accepted_source_run_dir)
    if prompt_mode == "minimal_write_apply":
        task_prompt = minimal_write_apply_prompt(
            task_label=str(package_payload.get("task_label") or args.lane),
            workspace_allowlist=workspace_allowlist or allowlist,
            validation_command=str(package_payload.get("local_validation_command") or "").strip(),
            accepted_source_summary=accepted_source_summary,
        )
    elif prompt_mode == "minimal_worker":
        acceptance = package_payload.get("acceptance_criteria") if isinstance(package_payload, dict) else []
        criteria = [item.strip() for item in acceptance if isinstance(item, str) and item.strip()] if isinstance(acceptance, list) else []
        task_summary = str(package_payload.get("cursor_prompt_contract") or "").strip()
        if not task_summary:
            task_summary = load_prompt_text_from_package(package_payload, base_path=args.input_package_json).splitlines()[0].strip() if isinstance(package_payload, dict) else ""
        task_prompt = minimal_worker_prompt(
            task_label=str(package_payload.get("task_label") or args.lane),
            task_summary=task_summary,
            workspace_allowlist=workspace_allowlist or allowlist,
            validation_command=str(package_payload.get("local_validation_command") or "").strip(),
            acceptance_criteria=criteria,
        )
    elif workspace_root != REPO_ROOT and workspace_allowlist:
        task_prompt = (
            f"{task_prompt}\n\nWorkspace root: {workspace_root}\n"
            "Workspace-relative edit paths:\n- " + "\n- ".join(workspace_allowlist)
        )
    accepted_source_context = accepted_source_prompt_context(accepted_source_run_dir)
    if accepted_source_context and prompt_mode != "minimal_write_apply":
        task_prompt = f"{task_prompt}\n\nAccepted source package context:\n{accepted_source_context}"
    agent_binary = resolve_agent_binary()
    if agent_binary is None:
        missing = agent_cli_missing_result()
        result = blocked_result(
            args=args,
            lane_id=args.lane,
            selected_model=selected_model,
            validation_result=missing["validation_result"],
            final_outcome=missing["final_outcome"],
            operator_message=missing["operator_message"],
            package_validation=package_validation,
            allowlist_validation=allowlist_validation,
            allowlist_consistency_validation=allowlist_consistency_validation,
            accepted_source_validation=accepted_source_validation,
            accepted_source_run_dir=str(accepted_source_run_dir.resolve()) if accepted_source_run_dir is not None else None,
            session_id=args.resume_session_id,
            cursor_pool=cursor_pool,
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        write_json(run_dir / "dispatcher_result.json", result)
        write_text(run_dir / "stdout.log", "")
        write_text(run_dir / "stderr.log", "")
        write_json(run_dir / "cursor_response.json", {})
        write_text(run_dir / "changed_files.txt", "")
        log_delegation_result(
            workflow_id=args.workflow_id,
            lane_id=args.lane,
            model=selected_model,
            cursor_pool=cursor_pool,
            session_id=args.resume_session_id,
            validation_result="BLOCKED",
            changed_files_count=0,
            resume_used=bool(args.resume_session_id),
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        return result

    planned_command = build_cursor_agent_command(
        agent_binary=agent_binary,
        model=selected_model,
        task_prompt=task_prompt,
        workspace=workspace_root,
        mode=mode,
        resume_session_id=args.resume_session_id,
    )

    if (
        package_validation["validation_result"] != "PASS"
        or allowlist_validation["validation_result"] != "PASS"
        or allowlist_consistency_validation["validation_result"] != "PASS"
        or accepted_source_validation["validation_result"] != "PASS"
    ):
        result = blocked_result(
            args=args,
            lane_id=args.lane,
            selected_model=selected_model,
            validation_result="BLOCKED",
            final_outcome="CURSOR_WORKER_INPUT_BLOCKED",
            operator_message="Cursor worker input was blocked before invocation.",
            package_validation=package_validation,
            allowlist_validation=allowlist_validation,
            allowlist_consistency_validation=allowlist_consistency_validation,
            accepted_source_validation=accepted_source_validation,
            accepted_source_run_dir=str(accepted_source_run_dir.resolve()) if accepted_source_run_dir is not None else None,
            session_id=args.resume_session_id,
            cursor_pool=cursor_pool,
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        result["planned_command"] = planned_command
        write_json(run_dir / "dispatcher_result.json", result)
        write_text(run_dir / "stdout.log", "")
        write_text(run_dir / "stderr.log", "")
        write_json(run_dir / "cursor_response.json", {})
        write_text(run_dir / "changed_files.txt", "")
        log_delegation_result(
            workflow_id=args.workflow_id,
            lane_id=args.lane,
            model=selected_model,
            cursor_pool=cursor_pool,
            session_id=args.resume_session_id,
            validation_result="BLOCKED",
            changed_files_count=0,
            resume_used=bool(args.resume_session_id),
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        return result

    if not os.getenv("CURSOR_API_KEY"):
        result = blocked_result(
            args=args,
            lane_id=args.lane,
            selected_model=selected_model,
            validation_result="BLOCKED",
            final_outcome="CURSOR_API_KEY_MISSING",
            operator_message="CURSOR_API_KEY is required before a bounded Cursor worker may run.",
            package_validation=package_validation,
            allowlist_validation=allowlist_validation,
            allowlist_consistency_validation=allowlist_consistency_validation,
            accepted_source_validation=accepted_source_validation,
            accepted_source_run_dir=str(accepted_source_run_dir.resolve()) if accepted_source_run_dir is not None else None,
            session_id=args.resume_session_id,
            cursor_pool=cursor_pool,
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        result["planned_command"] = planned_command
        write_json(run_dir / "dispatcher_result.json", result)
        write_text(run_dir / "stdout.log", "")
        write_text(run_dir / "stderr.log", "")
        write_json(run_dir / "cursor_response.json", {})
        write_text(run_dir / "changed_files.txt", "")
        log_delegation_result(
            workflow_id=args.workflow_id,
            lane_id=args.lane,
            model=selected_model,
            cursor_pool=cursor_pool,
            session_id=args.resume_session_id,
            validation_result="BLOCKED",
            changed_files_count=0,
            resume_used=bool(args.resume_session_id),
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        return result

    if args.dry_run and not args.execute_live:
        result = {
            "backend": "cursor",
            "lane_id": args.lane,
            "workflow_id": args.workflow_id,
            "selected_model": selected_model,
            "cursor_pool": cursor_pool,
            "estimated_cost_usd_static": estimated_cost_usd_static,
            "session_id": args.resume_session_id,
            "validation_result": "PASS",
            "selected_path": "cursor_worker_dry_run",
            "final_outcome": "CURSOR_WORKER_DRY_RUN_READY",
            "package_validation": package_validation,
            "allowlist_validation": allowlist_validation,
            "allowlist_consistency_validation": allowlist_consistency_validation,
            "accepted_source_validation": accepted_source_validation,
            "accepted_source_run_dir": str(accepted_source_run_dir.resolve()) if accepted_source_run_dir is not None else None,
            "planned_command": planned_command,
            "mode": mode,
            "workspace_root": str(workspace_root),
            "live_execution_allowed": False,
            "codex_review_required": True,
            "operator_message": "No live Cursor call executed. Codex remains final reviewer and acceptance owner.",
        }
        write_json(run_dir / "dispatcher_result.json", result)
        write_text(run_dir / "stdout.log", "")
        write_text(run_dir / "stderr.log", "")
        write_json(run_dir / "cursor_response.json", {})
        write_text(run_dir / "changed_files.txt", "")
        log_delegation_result(
            workflow_id=args.workflow_id,
            lane_id=args.lane,
            model=selected_model,
            cursor_pool=cursor_pool,
            session_id=args.resume_session_id,
            validation_result="PASS",
            changed_files_count=0,
            resume_used=bool(args.resume_session_id),
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        return result

    baseline_changed_files = changed_files_from_git()
    baseline_allowlist_hashes = snapshot_file_hashes(allowlist)
    live_timeout_seconds, timeout_tier = resolve_live_timeout_seconds(
        cursor_config=cursor_config,
        allowlist=allowlist,
    )
    try:
        completed = invoke_agent_command(planned_command, timeout_seconds=live_timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        timeout_stdout = coerce_timeout_output(exc.stdout)
        timeout_stderr = coerce_timeout_output(exc.stderr)
        result = blocked_result(
            args=args,
            lane_id=args.lane,
            selected_model=selected_model,
            validation_result="BLOCKED",
            final_outcome="CURSOR_AGENT_TIMEOUT",
            operator_message=(
                f"Cursor agent exceeded the bounded live timeout ({live_timeout_seconds}s, tier={timeout_tier}) "
                "before producing a final result."
            ),
            package_validation=package_validation,
            allowlist_validation=allowlist_validation,
            allowlist_consistency_validation=allowlist_consistency_validation,
            accepted_source_validation=accepted_source_validation,
            accepted_source_run_dir=str(accepted_source_run_dir.resolve()) if accepted_source_run_dir is not None else None,
            session_id=args.resume_session_id,
            cursor_pool=cursor_pool,
            estimated_cost_usd_static=estimated_cost_usd_static,
        )
        result["transport_result"] = "TRANSPORT_FAIL"
        result["semantic_result"] = "SEMANTIC_FAIL"
        result["planned_command"] = planned_command
        result["live_execution_allowed"] = True
        result["mode"] = mode
        result["workspace_root"] = str(workspace_root)
        result["timeout_seconds"] = live_timeout_seconds
        result["timeout_tier"] = timeout_tier
        result["changed_files"] = []
        result["changed_outside_allowlist"] = []
        write_json(run_dir / "dispatcher_result.json", result)
        write_text(run_dir / "stdout.log", timeout_stdout)
        write_text(run_dir / "stderr.log", timeout_stderr)
        write_json(run_dir / "cursor_response.json", {"timeout": True, "timeout_seconds": live_timeout_seconds})
        write_text(run_dir / "changed_files.txt", "")
        log_delegation_result(
            workflow_id=args.workflow_id,
            lane_id=args.lane,
            model=selected_model,
            cursor_pool=cursor_pool,
            session_id=args.resume_session_id,
            validation_result="BLOCKED",
            changed_files_count=0,
            resume_used=bool(args.resume_session_id),
            estimated_cost_usd_static=estimated_cost_usd_static,
            transport_result="TRANSPORT_FAIL",
            semantic_result="SEMANTIC_FAIL",
        )
        return result
    response_json: dict[str, Any]
    try:
        response_json = parse_json_response(completed.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        response_json = {"parse_error": str(exc)}
    session_id = str(response_json.get("session_id") or response_json.get("id") or args.resume_session_id or "").strip()
    duration_ms_raw = response_json.get("duration_ms")
    duration_ms = int(duration_ms_raw) if isinstance(duration_ms_raw, int) else None
    post_changed_files = changed_files_from_git()
    post_allowlist_hashes = snapshot_file_hashes(allowlist)
    changed_files = [path for path in allowlist if baseline_allowlist_hashes.get(path) != post_allowlist_hashes.get(path)]
    changed_outside_allowlist = [
        path
        for path in post_changed_files
        if path not in baseline_changed_files and not path_is_allowlisted(path, allowlist)
    ]

    outcome = classify_live_run_outcome(
        completed=completed,
        changed_files=changed_files,
        changed_outside_allowlist=changed_outside_allowlist,
        cursor_config=cursor_config,
        package_payload=package_payload if isinstance(package_payload, dict) else None,
    )
    validation_result = outcome["validation_result"]
    final_outcome = outcome["final_outcome"]
    operator_message = outcome["operator_message"]

    result = {
        "backend": "cursor",
        "lane_id": args.lane,
        "workflow_id": args.workflow_id,
        "selected_model": selected_model,
        "cursor_pool": cursor_pool,
        "estimated_cost_usd_static": estimated_cost_usd_static,
        "session_id": session_id or None,
        "validation_result": validation_result,
        "transport_result": outcome["transport_result"],
        "semantic_result": outcome["semantic_result"],
        "selected_path": "cursor_worker_live_mockable",
        "final_outcome": final_outcome,
        "package_validation": package_validation,
        "allowlist_validation": allowlist_validation,
        "allowlist_consistency_validation": allowlist_consistency_validation,
        "accepted_source_validation": accepted_source_validation,
        "accepted_source_run_dir": str(accepted_source_run_dir.resolve()) if accepted_source_run_dir is not None else None,
        "planned_command": planned_command,
        "mode": mode,
        "workspace_root": str(workspace_root),
        "live_execution_allowed": False,
        "codex_review_required": True,
        "timeout_seconds": live_timeout_seconds,
        "timeout_tier": timeout_tier,
        "changed_files": changed_files,
        "changed_outside_allowlist": changed_outside_allowlist,
        "operator_message": operator_message,
    }

    write_json(run_dir / "dispatcher_result.json", result)
    write_text(run_dir / "stdout.log", completed.stdout)
    write_text(run_dir / "stderr.log", completed.stderr)
    write_json(run_dir / "cursor_response.json", response_json)
    write_text(run_dir / "changed_files.txt", "\n".join(changed_files) + ("\n" if changed_files else ""))
    write_text(run_dir / "session_id.txt", session_id + ("\n" if session_id else ""))
    log_delegation_result(
        workflow_id=args.workflow_id,
        lane_id=args.lane,
        model=selected_model,
        cursor_pool=cursor_pool,
        session_id=session_id,
        validation_result=validation_result,
        changed_files_count=len(changed_files),
        resume_used=bool(args.resume_session_id),
        estimated_cost_usd_static=estimated_cost_usd_static,
        duration_ms=duration_ms,
        transport_result=outcome["transport_result"],
        semantic_result=outcome["semantic_result"],
    )
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded Cursor worker runner.")
    parser.add_argument("--lane", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--allowlist-file", type=Path, default=None)
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--cursor-pool", choices=("auto_composer", "api"), default=None)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--resume-session-id", default=None)
    parser.add_argument("--require-allowlist", action="store_true")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = summarize(args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["validation_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
