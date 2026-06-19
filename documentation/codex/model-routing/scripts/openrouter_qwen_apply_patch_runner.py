#!/usr/bin/env python3
"""Fixture-first OpenRouter Responses API runner for Qwen apply_patch proposals.

This runner is intentionally bounded. It prepares a Responses API request with
allowlisted file content, captures file-first artifacts through the shared
wrapper, validates the returned apply_patch proposal locally, and records the
same OR telemetry/healthcheck evidence used by the existing bounded lanes.

No local file changes are applied by this script.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "direct-or-runs"
WRAPPER_PATH = MODEL_ROUTING_DIR / "scripts" / "or_file_first_capture_wrapper.ps1"
BUDGET_PROFILE_PATH = MODEL_ROUTING_DIR / "config" / "or_task_budget_profiles_2026-06-19.json"
HEALTH_SNAPSHOT_PATH = (
    REPO_ROOT
    / "documentation"
    / "codex"
    / "skills"
    / "janus-health-check"
    / "scripts"
    / "health_snapshot.py"
)
RESPONSES_URI = "https://openrouter.ai/api/v1/responses"
DEFAULT_EXCERPT_CONTEXT_LINES = 3
FULL_CONTENT_FALLBACK_MAX_BYTES = 12000


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


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def resolve_repo_path(path: str) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def build_run_dir(workflow_id: str) -> Path:
    return RUN_ROOT / workflow_id


def load_budget_profile(profile_name: str | None, task_class: str) -> tuple[str, dict[str, Any]]:
    budget_config = load_json(BUDGET_PROFILE_PATH)
    profiles = budget_config.get("profiles", {})
    selected_name = profile_name or task_class or budget_config.get("default_profile")
    if selected_name not in profiles:
        available = ", ".join(sorted(profiles))
        raise SystemExit(f"Unknown OR budget profile '{selected_name}'. Available: {available}")
    return selected_name, profiles[selected_name]


def extract_prompt_targets(prompt_text: str) -> list[str]:
    candidates: list[str] = []
    for match in re.findall(r"`([^`]+)`", prompt_text):
        value = match.strip()
        if len(value) >= 8:
            candidates.append(value)
    for match in re.findall(r'"([^"\n]+)"', prompt_text):
        value = match.strip()
        if len(value) >= 8:
            candidates.append(value)

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate not in seen:
            unique.append(candidate)
            seen.add(candidate)
    return unique


def merge_line_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def build_excerpt_ranges(lines: list[str], prompt_targets: list[str], context_lines: int) -> list[tuple[int, int]]:
    raw_ranges: list[tuple[int, int]] = []
    lowered_targets = [target.lower() for target in prompt_targets]
    for index, line in enumerate(lines):
        lowered_line = line.lower()
        if any(target in lowered_line for target in lowered_targets):
            start = max(0, index - context_lines)
            end = min(len(lines) - 1, index + context_lines)
            raw_ranges.append((start, end))
    return merge_line_ranges(raw_ranges)


def build_excerpt_content(lines: list[str], ranges: list[tuple[int, int]]) -> str:
    blocks: list[str] = []
    for start, end in ranges:
        header = f"# excerpt lines {start + 1}-{end + 1}"
        body = "\n".join(lines[start : end + 1])
        blocks.append(header + "\n" + body)
    return "\n\n".join(blocks)


def load_allowed_file_inputs(editable_paths: list[str], prompt_text: str, context_lines: int) -> list[dict[str, Any]]:
    prompt_targets = extract_prompt_targets(prompt_text)
    file_inputs: list[dict[str, str]] = []
    for raw_path in editable_paths:
        normalized = normalize_repo_path(raw_path)
        resolved = resolve_repo_path(raw_path)
        if not resolved.exists() or not resolved.is_file():
            raise SystemExit(f"Editable path does not exist as a file: {raw_path}")
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError as exc:
            raise SystemExit(f"Editable path escapes repo root: {raw_path}") from exc
        full_content = resolved.read_text(encoding="utf-8-sig")
        lines = full_content.splitlines()
        excerpt_ranges = build_excerpt_ranges(lines, prompt_targets, context_lines)
        if excerpt_ranges:
            content = build_excerpt_content(lines, excerpt_ranges)
            content_mode = "excerpt"
            excerpts = [
                {
                    "start_line": start + 1,
                    "end_line": end + 1,
                }
                for start, end in excerpt_ranges
            ]
        elif len(full_content.encode("utf-8")) <= FULL_CONTENT_FALLBACK_MAX_BYTES:
            content = full_content
            content_mode = "full_file"
            excerpts = []
        else:
            raise SystemExit(
                f"Could not derive bounded excerpts from prompt for large file: {raw_path}. "
                "Add stronger anchor text to the prompt or reduce file scope."
            )
        file_inputs.append(
            {
                "path": normalized,
                "content": content,
                "content_mode": content_mode,
                "excerpt_line_ranges": excerpts,
                "full_line_count": len(lines),
            }
        )
    return file_inputs


def make_request_body(args: argparse.Namespace, prompt_text: str, file_inputs: list[dict[str, str]]) -> dict[str, Any]:
    system_text = (
        "You are a bounded OpenRouter worker for a Janus patch-proposal task. "
        "You must not claim git, release, routing, production, registry, or "
        "CURRENT_STATE authority. Use the apply_patch tool to propose a patch "
        "only inside the allowlisted files. Do not add, delete, rename, or move files. "
        "Codex will validate and decide whether to apply or reject the proposal locally. "
        "Use non-thinking mode for this turn. /no_think "
        "Produce exactly one final completed tool proposal. "
        "Do not emit excerpt snapshots or rewritten content blocks as the diff payload. "
        "The tool payload must contain unified diff hunks only."
    )
    user_payload = {
        "task_label": args.task_label,
        "allowed_files": [item["path"] for item in file_inputs],
        "max_touched_files": args.max_touched_files,
        "prompt": prompt_text,
        "file_inputs": file_inputs,
        "file_input_mode": "excerpt_preferred",
        "required_output_behavior": [
            "Use the apply_patch tool for the proposal.",
            "Touch only allowlisted files.",
            "Do not emit prose-only answers instead of a patch.",
            "Assume omitted file regions are unchanged.",
            "Return one final tool call only.",
            "Inside the tool payload, return unified diff hunks rather than excerpt snapshots.",
        ],
    }
    return {
        "model": args.model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_text}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps(user_payload, ensure_ascii=False, indent=2)}],
            },
        ],
        "tools": [
            {
                "type": "openrouter:apply_patch",
                "parameters": {
                    "engine": "openrouter",
                },
            }
        ],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "max_tool_calls": 1,
        "temperature": args.temperature,
        "max_output_tokens": args.max_output_tokens,
    }


def invoke_wrapper(
    *,
    run_dir: Path,
    request_body_path: Path,
    use_local_fixture: bool,
    local_fixture_response_path: Path | None,
    execute_live: bool,
) -> subprocess.CompletedProcess[str]:
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(WRAPPER_PATH),
        "-RunDirectory",
        str(run_dir),
        "-RequestBodyPath",
        str(request_body_path),
        "-Uri",
        RESPONSES_URI,
    ]
    if use_local_fixture:
        if local_fixture_response_path is None:
            raise SystemExit("--use-local-fixture requires --local-fixture-response-path")
        command.extend(["-UseLocalFixture", "-LocalFixtureResponsePath", str(local_fixture_response_path.resolve())])
    elif execute_live:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise SystemExit("OPENROUTER_API_KEY missing for live direct OpenRouter invocation")
        command.extend(
            [
                "-AuthorizationBearer",
                f"Bearer {api_key}",
                "-HttpReferer",
                "https://github.com/pruvex/Janus-Projekt",
                "-XTitle",
                "Janus Codex Qwen Responses Apply Patch",
            ]
        )
    else:
        raise SystemExit("Runner requires --use-local-fixture or --execute-live")
    return run_command(command)


def extract_apply_patch_calls(response_body: dict[str, Any]) -> list[dict[str, Any]]:
    output_items = response_body.get("output")
    if not isinstance(output_items, list):
        return []

    calls: list[dict[str, Any]] = []
    for item in output_items:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", "")).strip()
        item_status = str(item.get("status") or "")

        if item_type == "apply_patch_call":
            if item_status and item_status not in {"completed", "success", "succeeded"}:
                continue
            patch_text = item.get("patch")
            arguments = item.get("arguments")
            if not isinstance(patch_text, str) and isinstance(arguments, dict):
                patch_text = arguments.get("patch")
            if not isinstance(patch_text, str) and isinstance(arguments, str):
                try:
                    parsed_arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    parsed_arguments = None
                if isinstance(parsed_arguments, dict):
                    patch_text = parsed_arguments.get("patch")

            calls.append(
                {
                    "id": str(item.get("id") or ""),
                    "type": item_type,
                    "status": item_status,
                    "name": str(item.get("name") or ""),
                    "patch": patch_text if isinstance(patch_text, str) else "",
                }
            )
            continue

        if item_type == "openrouter:apply_patch":
            if item_status and item_status not in {"completed", "success", "succeeded", "in_progress"}:
                continue
            operation = item.get("operation") if isinstance(item.get("operation"), dict) else {}
            calls.append(
                {
                    "id": str(item.get("id") or ""),
                    "type": item_type,
                    "status": item_status,
                    "name": item_type,
                    "operation_type": str(operation.get("type") or ""),
                    "path": str(operation.get("path") or ""),
                    "diff": str(operation.get("diff") or ""),
                }
            )
    return calls


def contains_forbidden_patch_operation(patch_text: str) -> bool:
    forbidden_prefixes = ("*** Add File:", "*** Delete File:", "*** Move to:")
    return any(line.startswith(prefix) for prefix in forbidden_prefixes for line in patch_text.splitlines())


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


def extract_patch_sections(patch_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    lines = patch_text.splitlines()
    issues: list[str] = []
    if not lines or lines[0].strip() != "*** Begin Patch":
        issues.append("patch must start with *** Begin Patch")
        return [], issues
    if lines[-1].strip() != "*** End Patch":
        issues.append("patch must end with *** End Patch")
        return [], issues

    sections: list[dict[str, Any]] = []
    i = 1
    while i < len(lines) - 1:
        line = lines[i]
        if not line:
            i += 1
            continue
        if not line.startswith("*** Update File: "):
            issues.append(f"unsupported patch line: {line}")
            i += 1
            continue

        path = normalize_repo_path(line[len("*** Update File: ") :].strip())
        i += 1
        hunks: list[list[str]] = []
        current_hunk: list[str] | None = None
        while i < len(lines) - 1:
            current_line = lines[i]
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
            i += 1
        if current_hunk:
            hunks.append(current_hunk)
        sections.append({"path": path, "hunks": hunks})
    return sections, issues


def sequence_exists(lines: list[str], needle: list[str], start_index: int) -> tuple[bool, int]:
    if not needle:
        return False, start_index
    max_index = len(lines) - len(needle)
    for index in range(start_index, max_index + 1):
        if lines[index : index + len(needle)] == needle:
            return True, index + len(needle)
    return False, start_index


def patch_applicability_issues(patch_text: str, editable_paths: list[str]) -> list[str]:
    sections, issues = extract_patch_sections(patch_text)
    if issues:
        return issues

    editable_map = {
        normalize_repo_path(path): resolve_repo_path(path).read_text(encoding="utf-8-sig").splitlines()
        for path in editable_paths
    }
    for section in sections:
        section_path = str(section["path"])
        if section_path not in editable_map:
            issues.append(f"patch section path not found in editable files: {section_path}")
            continue
        file_lines = editable_map[section_path]
        search_from = 0
        hunks = section.get("hunks") or []
        if not hunks:
            issues.append(f"patch section has no hunks: {section_path}")
            continue
        for hunk in hunks:
            if not isinstance(hunk, list):
                issues.append(f"invalid hunk in patch section: {section_path}")
                continue
            old_sequence = [line[1:] for line in hunk if line.startswith(" ") or line.startswith("-")]
            if not old_sequence:
                issues.append(f"hunk has no removable/context lines for applicability check: {section_path}")
                continue
            found, search_from = sequence_exists(file_lines, old_sequence, search_from)
            if not found:
                issues.append(f"hunk context not found in current file: {section_path}")
    return issues


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


def unified_diff_applicability_issues(diff_text: str, repo_path: str, editable_paths: list[str]) -> list[str]:
    issues: list[str] = []
    normalized_path = normalize_repo_path(repo_path)
    editable_map = {
        normalize_repo_path(path): resolve_repo_path(path).read_text(encoding="utf-8-sig").splitlines()
        for path in editable_paths
    }
    if normalized_path not in editable_map:
        return [f"diff path not found in editable files: {normalized_path}"]

    hunks, hunk_issues = parse_unified_hunks(diff_text)
    if hunk_issues:
        return hunk_issues

    file_lines = editable_map[normalized_path]
    search_from = 0
    for hunk in hunks:
        old_sequence_exact = [line[1:] if line.startswith("-") else line for line in hunk if not line.startswith("+")]
        old_sequence_stripped = [
            line[1:] if line.startswith((" ", "-")) else line
            for line in hunk
            if not line.startswith("+")
        ]
        if not old_sequence_exact:
            issues.append(f"hunk has no removable/context lines for applicability check: {normalized_path}")
            continue
        found, next_search_from = sequence_exists(file_lines, old_sequence_exact, search_from)
        if not found and old_sequence_stripped != old_sequence_exact:
            found, next_search_from = sequence_exists(file_lines, old_sequence_stripped, search_from)
        if not found:
            issues.append(f"hunk context not found in current file: {normalized_path}")
            continue
        search_from = next_search_from
    return issues


def validate_apply_patch_calls(
    *,
    calls: list[dict[str, Any]],
    editable_paths: list[str],
    max_touched_files: int,
) -> tuple[str, list[str], list[str]]:
    issues: list[str] = []
    touched_files: list[str] = []

    if not calls:
        issues.append("no apply_patch_call items found")
        return "FAIL", issues, touched_files

    for call in calls:
        if str(call.get("type")) == "openrouter:apply_patch":
            operation_type = str(call.get("operation_type") or "")
            repo_path = normalize_repo_path(str(call.get("path") or ""))
            diff_text = str(call.get("diff") or "")
            if operation_type != "update_file":
                issues.append(f"unsupported apply_patch operation type: {operation_type or 'missing'}")
                continue
            if not repo_path:
                issues.append("apply_patch operation missing path")
                continue
            if not diff_text.strip():
                issues.append("apply_patch operation missing diff")
                continue
            touched_files.append(repo_path)
            issues.extend(unified_diff_applicability_issues(diff_text, repo_path, editable_paths))
            continue

        patch_text = str(call.get("patch") or "")
        if not patch_text:
            issues.append("apply_patch_call missing patch text")
            continue
        if contains_forbidden_patch_operation(patch_text):
            issues.append("patch contains add/delete/move operation")
            continue
        sections, section_issues = extract_patch_sections(patch_text)
        issues.extend(section_issues)
        touched_files.extend(str(section["path"]) for section in sections)
        issues.extend(patch_applicability_issues(patch_text, editable_paths))

    normalized_allowed = {normalize_repo_path(path) for path in editable_paths}
    unique_touched = sorted(set(touched_files))
    outside = [path for path in unique_touched if path not in normalized_allowed]
    if outside:
        issues.append(f"patch touches files outside allowlist: {', '.join(outside)}")
    if len(unique_touched) > max_touched_files:
        issues.append("touched file count exceeds max_touched_files")
    return ("PASS" if not issues else "FAIL"), issues, unique_touched


def actual_cost(response_summary: dict[str, Any]) -> float | None:
    value = response_summary.get("actual_or_cost")
    if isinstance(value, (int, float)):
        return float(value)
    usage = response_summary.get("usage") or {}
    cost = usage.get("cost")
    if isinstance(cost, (int, float)):
        return float(cost)
    return None


def usage_int(usage: dict[str, Any], *names: str) -> int:
    for name in names:
        value = usage.get(name)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def build_telemetry_row(
    *,
    args: argparse.Namespace,
    workflow_id: str,
    response_summary: dict[str, Any],
    latency_ms: int,
    validation_result: str,
    final_outcome: str,
    recommendation_signal: str,
) -> dict[str, Any]:
    usage = response_summary.get("usage") or {}
    cost = actual_cost(response_summary)
    estimated = float(args.estimated_or_cost)
    error_percent = ((cost - estimated) / estimated * 100.0) if cost is not None and estimated else 0.0
    return {
        "workflow_id": workflow_id,
        "skill_id": "janus-quickchange",
        "routing_mode": "Direct-OR",
        "selected_path": "qwen_responses_apply_patch_then_codex_review",
        "budget_profile": args.budget_profile,
        "budget_per_call_cap_usd": args.cost_cap,
        "codex_default_model": args.normal_target_model,
        "or_model": args.model,
        "estimated_prompt_tokens": args.estimated_prompt_tokens,
        "estimated_completion_tokens": args.estimated_completion_tokens,
        "estimated_or_cost": estimated,
        "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
        "cost_estimate_sample_count": args.cost_estimate_sample_count,
        "cost_estimate_mean_abs_error_percent": args.cost_estimate_mean_abs_error_percent,
        "cost_estimate_p50_error_percent": args.cost_estimate_p50_error_percent,
        "cost_estimate_p90_error_percent": args.cost_estimate_p90_error_percent,
        "cost_estimate_basis": args.cost_estimate_basis,
        "prompt_template_hash": args.prompt_template_hash,
        "task_variant": args.task_variant,
        "price_snapshot_source": args.price_snapshot_source,
        "price_snapshot_timestamp": args.price_snapshot_timestamp,
        "actual_prompt_tokens": usage_int(usage, "prompt_tokens", "input_tokens"),
        "actual_completion_tokens": usage_int(usage, "completion_tokens", "output_tokens"),
        "actual_reasoning_tokens": int((usage.get("completion_tokens_details") or usage.get("output_tokens_details") or {}).get("reasoning_tokens", 0)),
        "actual_cached_tokens": int((usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}).get("cached_tokens", 0)),
        "actual_or_cost": cost if cost is not None else 0.0,
        "generation_id": str(response_summary.get("generation_id") or ""),
        "usage_source": "response_usage" if usage else "fallback_estimate",
        "estimated_codex_effort": args.estimated_codex_effort,
        "estimation_error_percent": round(error_percent, 2),
        "cost_delta_vs_codex_estimate": round((cost or 0.0) - estimated, 8),
        "latency_ms": latency_ms,
        "validation_result": validation_result,
        "fallback_used": "NO" if validation_result == "PASS" else "YES",
        "rework_required": "NO" if validation_result == "PASS" else "YES",
        "final_outcome": final_outcome,
        "reason_for_escalation": "",
        "quality_notes": "Responses API apply_patch proposal only; Codex remains local validation and apply owner.",
        "recommendation_signal": recommendation_signal,
    }


def run_healthcheck(telemetry_path: Path, run_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(HEALTH_SNAPSHOT_PATH),
        "--repo",
        str(REPO_ROOT),
        "--or-telemetry-jsonl",
        str(telemetry_path),
    ]
    result = run_command(command)
    write_text(run_dir / "healthcheck_stdout.log", result.stdout)
    write_text(run_dir / "healthcheck_stderr.log", result.stderr)
    write_text(run_dir / "healthcheck_command.txt", " ".join(command) + "\n")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "health_snapshot.py failed")
    parsed = json.loads(result.stdout)
    write_json(run_dir / "healthcheck_summary.json", parsed)
    return parsed


def validate_pre_call(args: argparse.Namespace) -> list[str]:
    issues: list[str] = []
    if not args.editable_path:
        issues.append("at least one --editable-path is required")
    if args.max_touched_files < 1:
        issues.append("--max-touched-files must be >= 1")
    if args.estimated_or_cost is None:
        issues.append("--estimated-or-cost is required")
    elif args.estimated_or_cost > args.cost_cap:
        issues.append(f"estimated OR cost exceeds budget profile cap ({args.budget_profile}: {args.cost_cap:.6f})")
    if args.cost_estimate_confidence_percent is None:
        issues.append("--cost-estimate-confidence-percent is required")
    if args.execute_live and args.use_local_fixture:
        issues.append("--execute-live and --use-local-fixture are mutually exclusive")
    if not args.execute_live and not args.use_local_fixture:
        issues.append("choose --execute-live or --use-local-fixture")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture-first Qwen Responses apply_patch runner.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--model", default="qwen/qwen3-coder-flash")
    parser.add_argument("--prompt-path", type=Path, required=True)
    parser.add_argument("--editable-path", action="append", default=[])
    parser.add_argument("--max-touched-files", type=int, default=1)
    parser.add_argument("--task-class", default="quickchange_patch_review")
    parser.add_argument("--budget-profile", default=None)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--estimated-prompt-tokens", type=int, default=0)
    parser.add_argument("--estimated-completion-tokens", type=int, default=0)
    parser.add_argument("--estimated-or-cost", type=float, required=True)
    parser.add_argument("--cost-cap", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, required=True)
    parser.add_argument("--cost-estimate-sample-count", type=int, default=0)
    parser.add_argument("--cost-estimate-mean-abs-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-p50-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-p90-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-basis", default="qwen_responses_apply_patch_fixture_initial")
    parser.add_argument("--prompt-template-hash", default="qwen_responses_apply_patch_v1")
    parser.add_argument("--task-variant", default="quickchange_patch_review")
    parser.add_argument("--price-snapshot-source", default="manual_current_openrouter_model_page")
    parser.add_argument("--price-snapshot-timestamp", default="")
    parser.add_argument("--estimated-codex-effort", default="low")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-output-tokens", type=int, default=1800)
    parser.add_argument("--excerpt-context-lines", type=int, default=DEFAULT_EXCERPT_CONTEXT_LINES)
    parser.add_argument("--use-local-fixture", action="store_true")
    parser.add_argument("--local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()

    resolved_budget_profile, budget_profile = load_budget_profile(args.budget_profile, args.task_class)
    args.budget_profile = resolved_budget_profile
    if args.cost_cap is None:
        args.cost_cap = float(budget_profile["per_call_cap_usd"])

    workflow_id = args.workflow_id or f"DIRECT-OR-QWEN-RESPONSES-{now_id()}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    pre_call_issues = validate_pre_call(args)
    if pre_call_issues:
        summary = {
            "summary_header": "QWEN RESPONSES APPLY PATCH RESULT",
            "workflow_id": workflow_id,
            "selected_path": "codex_only_pre_call_guard",
            "validation_result": "FAIL",
            "final_outcome": "DIRECT_OR_PRE_CALL_ABORT",
            "budget_profile": args.budget_profile,
            "cost_cap": args.cost_cap,
            "issues": pre_call_issues,
        }
        write_json(run_dir / "operator_summary.json", summary)
        output(summary)
        return 1

    prompt_path = args.prompt_path.resolve()
    if not prompt_path.exists():
        raise SystemExit(f"Prompt path does not exist: {prompt_path}")
    prompt_text = prompt_path.read_text(encoding="utf-8-sig")
    file_inputs = load_allowed_file_inputs(args.editable_path, prompt_text, args.excerpt_context_lines)
    request_body = make_request_body(args, prompt_text, file_inputs)
    request_source = run_dir / "request_body_source.json"
    write_json(request_source, request_body)
    request_bytes = len(request_source.read_bytes())
    write_json(
        run_dir / "request_input_summary.json",
        {
            "workflow_id": workflow_id,
            "request_body_bytes": request_bytes,
            "file_inputs": [
                {
                    "path": item["path"],
                    "content_mode": item["content_mode"],
                    "full_line_count": item["full_line_count"],
                    "excerpt_line_ranges": item["excerpt_line_ranges"],
                    "content_chars": len(str(item["content"])),
                }
                for item in file_inputs
            ],
        },
    )

    start = time.time()
    wrapper_result = invoke_wrapper(
        run_dir=run_dir,
        request_body_path=request_source,
        use_local_fixture=args.use_local_fixture,
        local_fixture_response_path=args.local_fixture_response_path,
        execute_live=args.execute_live,
    )
    latency_ms = int(round((time.time() - start) * 1000))
    write_text(run_dir / "wrapper_command_stdout.log", wrapper_result.stdout)
    write_text(run_dir / "wrapper_command_stderr.log", wrapper_result.stderr)
    if wrapper_result.returncode != 0:
        summary = {
            "summary_header": "QWEN RESPONSES APPLY PATCH RESULT",
            "workflow_id": workflow_id,
            "selected_path": "codex_only_wrapper_failure",
            "validation_result": "FAIL",
            "final_outcome": "DIRECT_OR_WRAPPER_FAILURE",
            "budget_profile": args.budget_profile,
            "cost_cap": args.cost_cap,
            "wrapper_stderr": wrapper_result.stderr.strip(),
        }
        write_json(run_dir / "operator_summary.json", summary)
        output(summary)
        return 1

    response_body = load_json(run_dir / "response_body.json")
    response_summary = load_json(run_dir / "response_summary.json")
    calls = extract_apply_patch_calls(response_body)
    write_json(run_dir / "apply_patch_calls.json", {"calls": calls})
    cost = actual_cost(response_summary)
    finish_reason = response_summary.get("finish_reason")
    validation_result, issues, touched_files = validate_apply_patch_calls(
        calls=calls,
        editable_paths=args.editable_path,
        max_touched_files=args.max_touched_files,
    )
    if cost is None or cost > args.cost_cap:
        issues.append("actual OR cost missing or above cap")
    if not response_summary.get("generation_id"):
        issues.append("generation_id missing")
    if not response_summary.get("usage"):
        issues.append("usage missing")
    if finish_reason == "length":
        issues.append("finish_reason=length")
    validation_result = "PASS" if not issues else "FAIL"
    final_outcome = (
        "QWEN_RESPONSES_APPLY_PATCH_READY_FOR_CODEX_REVIEW"
        if validation_result == "PASS"
        else "QWEN_RESPONSES_APPLY_PATCH_REJECT_AND_FALLBACK"
    )
    recommendation = "OR_PREFERRED" if validation_result == "PASS" else "CODEX_PREFERRED"
    validation_summary = {
        "workflow_id": workflow_id,
        "validation_result": validation_result,
        "budget_profile": args.budget_profile,
        "issues": issues,
        "touched_files": touched_files,
        "editable_paths": [normalize_repo_path(item) for item in args.editable_path],
        "max_touched_files": args.max_touched_files,
        "finish_reason": finish_reason,
        "actual_or_cost": cost,
        "cost_cap": args.cost_cap,
        "response_api_shape": response_summary.get("api_shape"),
        "response_output_item_types": response_summary.get("output_item_types"),
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    telemetry_path = MODEL_ROUTING_DIR / (
        f"or_healthcheck_telemetry_qwen_responses_apply_patch_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
    )
    telemetry_row = build_telemetry_row(
        args=args,
        workflow_id=workflow_id,
        response_summary=response_summary,
        latency_ms=latency_ms,
        validation_result=validation_result,
        final_outcome=final_outcome,
        recommendation_signal=recommendation,
    )
    append_jsonl(telemetry_path, telemetry_row)
    healthcheck_status = "SKIPPED"
    healthcheck_summary_path = ""
    try:
        run_healthcheck(telemetry_path, run_dir)
        healthcheck_status = "PASS"
        healthcheck_summary_path = str(run_dir / "healthcheck_summary.json")
    except Exception as exc:
        validation_result = "FAIL"
        final_outcome = "DIRECT_OR_HEALTHCHECK_FAILURE"
        issues.append(str(exc))
        healthcheck_status = "FAIL"

    operator_summary = {
        "summary_header": "QWEN RESPONSES APPLY PATCH RESULT",
        "workflow_id": workflow_id,
        "task_label": args.task_label,
        "selected_path": "qwen_responses_apply_patch_then_codex_review",
        "budget_profile": args.budget_profile,
        "normal_target_model": args.normal_target_model,
        "or_model": args.model,
        "estimated_or_cost": args.estimated_or_cost,
        "actual_or_cost": cost,
        "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
        "finish_reason": finish_reason,
        "validation_result": validation_result,
        "final_outcome": final_outcome,
        "fallback_used": "NO" if validation_result == "PASS" else "YES",
        "rework_required": "NO" if validation_result == "PASS" else "YES",
        "response_summary_path": str(run_dir / "response_summary.json"),
        "apply_patch_calls_path": str(run_dir / "apply_patch_calls.json"),
        "request_input_summary_path": str(run_dir / "request_input_summary.json"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "telemetry_jsonl_path": str(telemetry_path),
        "healthcheck_status": healthcheck_status,
        "healthcheck_summary_path": healthcheck_summary_path,
        "operator_result_lines": [
            f"Ergebnis: {final_outcome}",
            f"Tatsaechliche Kosten: {(cost or 0.0):.9f}",
            f"Apply-patch-Aufrufe: {len(calls)}",
        ],
        "operator_message": (
            "Responses/apply_patch produced a bounded patch proposal. Codex must review and decide whether to apply locally."
            if validation_result == "PASS"
            else "Responses/apply_patch result failed bounded gates. Fallback to Codex-only."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
