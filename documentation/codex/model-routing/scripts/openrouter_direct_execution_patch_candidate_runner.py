#!/usr/bin/env python3
"""Direct OpenRouter runner for bounded execution_patch_candidate flows."""

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
RUN_ROOT = MODEL_ROUTING_DIR / "execution-direct-or-runs"
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

REQUIRED_INPUT_FIELDS = [
    "workflow_id",
    "bound_skill_context",
    "target_task",
    "spec_path",
    "precheck_status",
    "allowed_files",
    "max_touched_files",
    "mini_test_plan",
    "manual_validation_gate",
    "delegation_question",
]

RESULT_SCHEMA: dict[str, Any] = {
    "name": "janus_execution_patch_candidate_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "status",
            "target_task",
            "patch_text",
            "changed_files",
            "risk_list",
            "suggested_validation_steps",
            "manual_validation_note",
            "codex_acceptance_rule",
            "notes",
        ],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["PASS", "WEAK_SIGNAL", "BLOCKED"],
            },
            "target_task": {"type": "string", "maxLength": 160},
            "patch_text": {"type": "string", "maxLength": 5000},
            "changed_files": {
                "type": "array",
                "maxItems": 5,
                "items": {"type": "string"},
            },
            "risk_list": {
                "type": "array",
                "maxItems": 4,
                "items": {"type": "string", "maxLength": 220},
            },
            "suggested_validation_steps": {
                "type": "array",
                "maxItems": 4,
                "items": {"type": "string", "maxLength": 220},
            },
            "manual_validation_note": {"type": "string", "maxLength": 160},
            "codex_acceptance_rule": {"type": "string", "maxLength": 120},
            "notes": {"type": "string", "maxLength": 320},
        },
    },
}

PLACEHOLDER_PATCH_MARKERS = (
    "# existing header",
    "existing artifact-oriented summary logic",
    "existing prompt logic",
)


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


def build_compact_task_brief(spec_text: str) -> str:
    lines = [line.rstrip() for line in spec_text.splitlines()]
    collected: list[str] = []
    capture = False
    stop_prefixes = ("- Tests:", "- Model:", "- Reason:", "HANDOFF_SCOPE:")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            capture = True
        if not capture:
            continue
        if any(stripped.startswith(prefix) for prefix in stop_prefixes):
            break
        if stripped.startswith("- Evidence Paths:"):
            break
        collected.append(line)
    compact = "\n".join(collected).strip()
    if not compact:
        compact = "\n".join(lines[:40]).strip()
    return compact[:3500].rstrip()


def summarize_task_contract(spec_text: str) -> dict[str, str]:
    compact = build_compact_task_brief(spec_text)
    lines = [line.strip() for line in compact.splitlines() if line.strip()]
    goal = ""
    acceptance = ""
    risk = ""
    bullets: list[str] = []
    for line in lines:
        if line.startswith("- Ziel:") or line.startswith("### "):
            if not goal:
                goal = line
        elif line.startswith("- Acceptance Criteria:"):
            acceptance = line
        elif line.startswith("- Scope:"):
            risk = line
        elif line.startswith("- ") and len(bullets) < 3:
            bullets.append(line)
    if not goal and lines:
        goal = lines[0]
    if not acceptance and len(lines) > 1:
        acceptance = lines[min(1, len(lines) - 1)]
    if not risk:
        risk = "Keep scope bounded to the exact allowlist and avoid broader product changes."
    return {
        "goal": goal[:240].rstrip(),
        "acceptance": acceptance[:280].rstrip(),
        "risk": risk[:240].rstrip(),
        "context_bullets": " | ".join(item[:120].rstrip() for item in bullets),
    }


def summarize_validation_bundle(mini_test_plan: list[str]) -> dict[str, Any]:
    return {
        "validation_bundle_id": f"bundle-{len(mini_test_plan)}-steps",
        "validation_summary": (
            "Codex will run the known local validation bundle after review: "
            + "; ".join(step[:100].rstrip() for step in mini_test_plan[:2])
        )[:260].rstrip(),
    }


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    if payload.get("precheck_status") != "PRE-CHECK PASSED":
        issues.append("precheck_status must be exactly PRE-CHECK PASSED")
    allowed_files = payload.get("allowed_files")
    if not isinstance(allowed_files, list) or not allowed_files:
        issues.append("allowed_files must be a non-empty list")
    max_touched_files = payload.get("max_touched_files")
    if not isinstance(max_touched_files, int) or max_touched_files < 1:
        issues.append("max_touched_files must be an integer >= 1")
    mini_test_plan = payload.get("mini_test_plan")
    if not isinstance(mini_test_plan, list) or not mini_test_plan:
        issues.append("mini_test_plan must be a non-empty list")
    if not payload.get("manual_validation_gate"):
        issues.append("manual_validation_gate must be present")
    forbidden_anchors = payload.get("forbidden_anchors")
    if forbidden_anchors is not None and not isinstance(forbidden_anchors, list):
        issues.append("forbidden_anchors must be a list when present")
    required_current_anchors = payload.get("required_current_anchors")
    if required_current_anchors is not None and not isinstance(required_current_anchors, list):
        issues.append("required_current_anchors must be a list when present")
    current_seam_context = payload.get("current_seam_context")
    if current_seam_context is not None and not isinstance(current_seam_context, str):
        issues.append("current_seam_context must be a string when present")
    signature_context = payload.get("signature_context")
    if signature_context is not None and not isinstance(signature_context, str):
        issues.append("signature_context must be a string when present")
    call_shape_examples = payload.get("call_shape_examples")
    if call_shape_examples is not None and not isinstance(call_shape_examples, list):
        issues.append("call_shape_examples must be a list when present")
    exact_code_context_blocks = payload.get("exact_code_context_blocks")
    if exact_code_context_blocks is not None and not isinstance(exact_code_context_blocks, list):
        issues.append("exact_code_context_blocks must be a list when present")
    return issues


def make_request_body(args: argparse.Namespace, input_payload: dict[str, Any]) -> dict[str, Any]:
    spec_excerpt = ""
    compact_contract: dict[str, str] = {
        "goal": "",
        "acceptance": "",
        "risk": "",
        "context_bullets": "",
    }
    spec_file = resolve_repo_path(input_payload["spec_path"])
    if spec_file.exists():
        spec_excerpt = build_compact_task_brief(spec_file.read_text(encoding="utf-8-sig"))
        compact_contract = summarize_task_contract(spec_file.read_text(encoding="utf-8-sig"))
    manual_validation_phrase = "Codex must manually validate this patch locally before task completion."
    acceptance_phrase = "Codex must review and apply or reject locally."
    validation_bundle = summarize_validation_bundle(input_payload.get("mini_test_plan", []))
    request = {
        "model": args.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded OpenRouter worker for a Janus execution patch candidate. "
                    "Return only JSON matching the required schema. "
                    "This is proposal-only work. Do not claim completion, release readiness, routing authority, "
                    "git authority, or final validation authority. Codex will review and decide whether to apply or reject. "
                    "Return the smallest viable unified diff for the smallest viable subset of the allowlist. "
                    "If you cannot anchor a real unified diff against exact current file context, return BLOCKED with empty patch_text. "
                    "Preserve patch_text as newline-separated unified diff lines; never compress the diff into one line. "
                    "Do not invent simplified file structure, placeholder headers, ellipses, or fake helper skeletons. "
                    "Keep the JSON compact: short notes, short risk bullets, no repeated restatement of the task. "
                    "Do not include explanatory prose outside the JSON object. "
                    "Prefer backend-first minimal change shape over broad test or cleanup expansion."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "target_task": input_payload["target_task"],
                        "allowed_files": [normalize_repo_path(item) for item in input_payload["allowed_files"]],
                        "max_touched_files": input_payload["max_touched_files"],
                        "manual_validation_gate": input_payload["manual_validation_gate"],
                        "delegation_question": input_payload["delegation_question"],
                        "current_seam_context": str(input_payload.get("current_seam_context") or ""),
                        "signature_context": str(input_payload.get("signature_context") or ""),
                        "call_shape_examples": list(input_payload.get("call_shape_examples") or []),
                        "exact_code_context_blocks": list(input_payload.get("exact_code_context_blocks") or []),
                        "forbidden_anchors": list(input_payload.get("forbidden_anchors") or []),
                        "required_current_anchors": list(input_payload.get("required_current_anchors") or []),
                        "task_contract": compact_contract,
                        "validation_bundle": validation_bundle,
                        "return_contract": {
                            "required_fields": [
                                "status",
                                "target_task",
                                "patch_text",
                                "changed_files",
                                "risk_list",
                                "suggested_validation_steps",
                                "manual_validation_note",
                                "codex_acceptance_rule",
                                "notes",
                            ],
                            "empty_allowed_fields": ["changed_files", "risk_list", "suggested_validation_steps"],
                            "patch_rule": "patch_text must be unified diff text touching only the smallest necessary subset of the allowlist",
                            "newline_rule": "patch_text must preserve newline-separated unified diff headers and hunk lines; never collapse the diff into one line",
                            "anchor_rule": "do not target forbidden_anchors; prefer required_current_anchors when present",
                            "signature_rule": "preserve real local function signatures and call shapes when signature_context or call_shape_examples are provided",
                            "context_rule": "when exact_code_context_blocks are provided, keep imports, surrounding control flow, and local helper usage aligned to those real excerpts instead of inventing simplified file structure",
                            "blocked_rule": "if you cannot produce a real hunk anchored to current local code, return status BLOCKED with empty patch_text and explain why in notes/risk_list",
                            "placeholder_rule": "never use placeholder context like '# existing header', '...', or 'existing artifact-oriented summary logic'",
                        },
                        "full_spec_excerpt_for_reference_only": spec_excerpt[:1200].rstrip(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": RESULT_SCHEMA,
        },
    }
    return request


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
                "Janus Codex Direct OR Execution Patch Candidate",
            ]
        )
    else:
        raise SystemExit("Direct OpenRouter runner requires --use-local-fixture or --execute-live")
    return run_command(command)


def content_from_response(response_body: dict[str, Any]) -> str:
    choices = response_body.get("choices") or []
    if not choices:
        return ""
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return ""


def parse_json_from_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


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


def sequence_exists(lines: list[str], needle: list[str], start_index: int) -> tuple[bool, int]:
    if not needle:
        return False, start_index
    max_index = len(lines) - len(needle)
    for index in range(start_index, max_index + 1):
        if lines[index : index + len(needle)] == needle:
            return True, index + len(needle)
    return False, start_index


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
            if line.startswith(("diff --git ", "--- a/", "+++ b/")) or not line.strip():
                continue
            issues.append("diff content before hunk marker")
            continue
        current_hunk.append(line)

    if current_hunk:
        hunks.append(current_hunk)
    if not hunks:
        issues.append("diff has no hunks")
    return hunks, issues


def unified_diff_applicability_issues(diff_text: str, repo_path: str) -> list[str]:
    issues: list[str] = []
    normalized_path = normalize_repo_path(repo_path)
    resolved_path = resolve_repo_path(normalized_path)
    if not resolved_path.exists():
        return [f"diff path not found in repo: {normalized_path}"]

    hunks, hunk_issues = parse_unified_hunks(diff_text)
    if hunk_issues:
        return hunk_issues

    file_lines = resolved_path.read_text(encoding="utf-8-sig").splitlines()
    search_from = 0
    for hunk in hunks:
        old_sequence_exact = [line[1:] if line.startswith("-") else line for line in hunk if not line.startswith("+")]
        old_sequence_stripped = [line[1:] if line.startswith((" ", "-")) else line for line in hunk if not line.startswith("+")]
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


def placeholder_patch_issues(patch_text: str) -> list[str]:
    issues: list[str] = []
    lowered = patch_text.lower()
    for marker in PLACEHOLDER_PATCH_MARKERS:
        if marker in lowered:
            issues.append(f"placeholder patch marker detected: {marker}")
    for line in strip_diff_fence(patch_text).splitlines():
        if line.startswith(("+", "-", " ")) and line[1:].strip() == "...":
            issues.append("placeholder patch marker detected: line-level ellipsis")
            break
    return issues


def extract_patch_files(patch_text: str) -> list[str]:
    files: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(normalize_repo_path(line[len("+++ b/") :].strip()))
    return files


def postprocess_result_payload(result_payload: dict[str, Any], input_payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result_payload)
    patch_text = normalized.get("patch_text")
    patch_files = extract_patch_files(patch_text if isinstance(patch_text, str) else "")
    if normalized.get("status") == "BLOCKED" and patch_files and isinstance(patch_text, str) and "@@" in patch_text:
        normalized["status"] = "WEAK_SIGNAL"
    if not isinstance(normalized.get("changed_files"), list) or not normalized.get("changed_files"):
        normalized["changed_files"] = patch_files
    else:
        normalized["changed_files"] = [normalize_repo_path(str(item)) for item in normalized["changed_files"]]
    if not isinstance(normalized.get("risk_list"), list) or not normalized.get("risk_list"):
        normalized["risk_list"] = [
            "Proposal only; Codex must still review scope, correctness, and bounded local validation before any apply step."
        ]
    if not isinstance(normalized.get("suggested_validation_steps"), list) or not normalized.get("suggested_validation_steps"):
        normalized["suggested_validation_steps"] = list(input_payload.get("mini_test_plan", []))
    normalized["manual_validation_note"] = "Codex must manually validate this patch locally before task completion."
    normalized["codex_acceptance_rule"] = "Codex must review and apply or reject locally."
    return normalized


def validate_result_payload(result_payload: dict[str, Any], input_payload: dict[str, Any]) -> list[str]:
    required_fields = RESULT_SCHEMA["schema"]["required"]
    issues: list[str] = []
    for field in required_fields:
        if field not in result_payload:
            issues.append(f"missing result field: {field}")
    status = result_payload.get("status")
    if status not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status must be PASS, WEAK_SIGNAL, or BLOCKED")
    patch_text = result_payload.get("patch_text")
    if status == "BLOCKED":
        if not isinstance(patch_text, str):
            issues.append("patch_text must be a string")
    elif not isinstance(patch_text, str) or ("--- a/" not in patch_text or "+++ b/" not in patch_text):
        issues.append("patch_text must be unified diff text")
    elif "\n" not in patch_text:
        issues.append("patch_text must preserve newline-separated diff lines")
    changed_files = result_payload.get("changed_files")
    if not isinstance(changed_files, list):
        issues.append("changed_files must be a list")
        changed_files = []
    changed_files = [normalize_repo_path(str(item)) for item in changed_files]
    allowed_files = {normalize_repo_path(item) for item in input_payload.get("allowed_files", [])}
    patch_files = extract_patch_files(patch_text or "")
    if status == "BLOCKED":
        if patch_text.strip():
            issues.append("BLOCKED result must not include patch_text content")
        if changed_files:
            issues.append("BLOCKED result must not declare changed_files")
    elif patch_files and changed_files != patch_files:
        issues.append("changed_files must match the files declared in patch_text")
    elif status != "BLOCKED":
        issues.extend(placeholder_patch_issues(patch_text or ""))
        for patch_file in patch_files:
            issues.extend(unified_diff_applicability_issues(patch_text or "", patch_file))
    if len(changed_files) > int(input_payload.get("max_touched_files", 0)):
        issues.append("changed_files exceeds max_touched_files")
    for item in changed_files:
        if item not in allowed_files:
            issues.append(f"changed file escapes allowlist: {item}")
    if not isinstance(result_payload.get("risk_list"), list) or not result_payload.get("risk_list"):
        issues.append("risk_list must be a non-empty list")
    if not isinstance(result_payload.get("suggested_validation_steps"), list) or not result_payload.get("suggested_validation_steps"):
        issues.append("suggested_validation_steps must be a non-empty list")
    manual_validation_note = str(result_payload.get("manual_validation_note", ""))
    if manual_validation_note != "Codex must manually validate this patch locally before task completion.":
        issues.append("manual_validation_note must preserve Codex-owned manual validation")
    codex_acceptance_rule = str(result_payload.get("codex_acceptance_rule", ""))
    if codex_acceptance_rule != "Codex must review and apply or reject locally.":
        issues.append("codex_acceptance_rule must preserve Codex apply/reject ownership")
    return issues


def actual_cost(response_summary: dict[str, Any]) -> float | None:
    value = response_summary.get("actual_or_cost")
    if isinstance(value, (int, float)):
        return float(value)
    usage = response_summary.get("usage") or {}
    cost = usage.get("cost")
    if isinstance(cost, (int, float)):
        return float(cost)
    return None


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
        "skill_id": "janus-executioner",
        "routing_mode": "Direct-OR",
        "selected_path": "direct_or_execution_patch_candidate_then_codex_review",
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
        "actual_prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "actual_completion_tokens": int(usage.get("completion_tokens", 0)),
        "actual_reasoning_tokens": int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)),
        "actual_cached_tokens": int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)),
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
        "quality_notes": "Direct OpenRouter execution patch candidate only; Codex remains apply/reject and validation owner.",
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


def validate_pre_call(args: argparse.Namespace, input_payload: dict[str, Any]) -> list[str]:
    issues = validate_input_package(input_payload)
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
    parser = argparse.ArgumentParser(description="Direct OpenRouter execution patch candidate runner.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--task-class", default="execution_patch_candidate")
    parser.add_argument("--budget-profile", default=None)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--input-package-json", type=Path, required=True)
    parser.add_argument("--estimated-prompt-tokens", type=int, default=0)
    parser.add_argument("--estimated-completion-tokens", type=int, default=0)
    parser.add_argument("--estimated-or-cost", type=float, required=True)
    parser.add_argument("--cost-cap", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, required=True)
    parser.add_argument("--cost-estimate-sample-count", type=int, default=0)
    parser.add_argument("--cost-estimate-mean-abs-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-p50-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-p90-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-basis", default="direct_or_execution_patch_candidate_initial")
    parser.add_argument("--prompt-template-hash", default="direct_or_execution_patch_candidate_v1")
    parser.add_argument("--task-variant", default="execution_patch_candidate")
    parser.add_argument("--price-snapshot-source", default="manual_current_openrouter_model_page")
    parser.add_argument("--price-snapshot-timestamp", default="")
    parser.add_argument("--estimated-codex-effort", default="medium")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=3200)
    parser.add_argument("--use-local-fixture", action="store_true")
    parser.add_argument("--local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()

    resolved_budget_profile, budget_profile = load_budget_profile(args.budget_profile, args.task_class)
    args.budget_profile = resolved_budget_profile
    if args.cost_cap is None:
        args.cost_cap = float(budget_profile["per_call_cap_usd"])

    input_payload = load_json(args.input_package_json.resolve())
    workflow_id = args.workflow_id or f"DIRECT-OR-EXECUTION-PATCH-{now_id()}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "input_package.json", input_payload)

    pre_call_issues = validate_pre_call(args, input_payload)
    if pre_call_issues:
        summary = {
            "summary_header": "DIRECT OR EXECUTION PATCH RESULT",
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

    request_body = make_request_body(args, input_payload)
    request_source = run_dir / "request_body_source.json"
    write_json(request_source, request_body)

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
            "summary_header": "DIRECT OR EXECUTION PATCH RESULT",
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
    cost = actual_cost(response_summary)
    cost_issue = cost is None or cost > args.cost_cap
    finish_reason = response_summary.get("finish_reason")
    content = content_from_response(response_body)
    try:
        result_payload = parse_json_from_text(content)
    except Exception as exc:
        result_payload = {
            "status": "BLOCKED",
            "target_task": input_payload.get("target_task", ""),
            "patch_text": "",
            "changed_files": [],
            "risk_list": [f"Could not parse model content as JSON: {exc}"],
            "suggested_validation_steps": [],
            "manual_validation_note": "Codex must keep manual validation ownership because the model response could not be parsed.",
            "codex_acceptance_rule": "Codex must review and apply or reject locally.",
            "notes": "Parser fallback result",
        }
    result_payload = postprocess_result_payload(result_payload, input_payload)
    write_json(run_dir / "patch_candidate_result.json", result_payload)

    issues = validate_result_payload(result_payload, input_payload)
    if cost_issue:
        issues.append("actual OR cost missing or above cap")
    if not response_summary.get("generation_id"):
        issues.append("generation_id missing")
    if not response_summary.get("usage"):
        issues.append("usage missing")
    if finish_reason == "length":
        issues.append("finish_reason=length")
    validation_result = "PASS" if not issues else "FAIL"
    if validation_result == "PASS" and result_payload.get("status") == "BLOCKED":
        final_outcome = "DIRECT_OR_BOUNDED_BLOCKED_NO_PATCH"
        recommendation = "CODEX_PREFERRED"
    elif validation_result == "PASS":
        final_outcome = "DIRECT_OR_EXECUTION_PATCH_READY_FOR_CODEX_REVIEW"
        recommendation = "OR_PREFERRED"
    else:
        final_outcome = "DIRECT_OR_REJECT_AND_FALLBACK"
        recommendation = "CODEX_PREFERRED"
    validation_summary = {
        "workflow_id": workflow_id,
        "validation_result": validation_result,
        "budget_profile": args.budget_profile,
        "issues": issues,
        "allowed_files": [normalize_repo_path(item) for item in input_payload.get("allowed_files", [])],
        "changed_files": result_payload.get("changed_files", []),
        "max_touched_files": input_payload.get("max_touched_files"),
        "finish_reason": finish_reason,
        "actual_or_cost": cost,
        "cost_cap": args.cost_cap,
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    telemetry_path = MODEL_ROUTING_DIR / f"or_healthcheck_telemetry_direct_or_execution_patch_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
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
        "summary_header": "DIRECT OR EXECUTION PATCH RESULT",
        "workflow_id": workflow_id,
        "task_label": args.task_label,
        "selected_path": "direct_or_execution_patch_candidate_then_codex_review",
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
        "patch_candidate_result_path": str(run_dir / "patch_candidate_result.json"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "telemetry_jsonl_path": str(telemetry_path),
        "healthcheck_status": healthcheck_status,
        "healthcheck_summary_path": healthcheck_summary_path,
        "operator_message": (
            "Direct OR produced a bounded execution patch candidate. Codex must review and decide whether to apply or reject locally."
            if validation_result == "PASS" and result_payload.get("status") != "BLOCKED"
            else "Direct OR returned a bounded no-patch BLOCKED assessment. Codex must continue locally."
            if validation_result == "PASS"
            else "Direct OR execution patch candidate failed bounded gates. Fallback to Codex-only."
        ),
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
