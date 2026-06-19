#!/usr/bin/env python3
"""Direct OpenRouter quickchange patch proposal runner.

This runner is bounded Janus workflow tooling. It calls OpenRouter directly via
the file-first capture wrapper and asks for a structured patch proposal. Codex
still owns local apply, validation, and final acceptance.
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


PATCH_SCHEMA: dict[str, Any] = {
    "name": "janus_quickchange_patch_proposal",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "status",
            "summary",
            "changed_files",
            "unified_diff",
            "validation_notes",
            "risk_notes",
        ],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["PATCH_PROPOSAL", "NO_CHANGE", "BLOCKED"],
            },
            "summary": {"type": "string"},
            "changed_files": {
                "type": "array",
                "items": {"type": "string"},
            },
            "unified_diff": {"type": "string"},
            "validation_notes": {
                "type": "array",
                "items": {"type": "string"},
            },
            "risk_notes": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}


def is_qwen_model(model: str) -> bool:
    return model.strip().lower().startswith("qwen/")


def should_harden_structured_output(response_format: str) -> bool:
    return response_format in {"json_schema", "json_object"}


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
    return path.strip().replace("\\", "/").lstrip("./")


def build_run_dir(workflow_id: str) -> Path:
    return RUN_ROOT / workflow_id


def resolve_prompt_path(prompt_path: Path) -> Path:
    resolved = prompt_path.resolve()
    if not resolved.exists():
        raise SystemExit(f"Prompt path does not exist: {resolved}")
    return resolved


def load_budget_profile(profile_name: str | None, task_class: str) -> tuple[str, dict[str, Any]]:
    budget_config = load_json(BUDGET_PROFILE_PATH)
    profiles = budget_config.get("profiles", {})
    selected_name = profile_name or task_class or budget_config.get("default_profile")
    if selected_name not in profiles:
        available = ", ".join(sorted(profiles))
        raise SystemExit(f"Unknown OR budget profile '{selected_name}'. Available: {available}")
    return selected_name, profiles[selected_name]


def make_request_body(args: argparse.Namespace, prompt_text: str) -> dict[str, Any]:
    allowed_files = [normalize_repo_path(item) for item in args.editable_path]
    system = (
        "You are a bounded OpenRouter worker for a Janus quickchange patch review. "
        "Return only JSON matching the requested schema. Do not edit files. "
        "Do not claim Git, release, routing, production, backlog, registry, or CURRENT_STATE authority. "
        "Codex will review the patch before any local apply."
    )
    if is_qwen_model(args.model):
        system += " Use non-thinking mode for this turn. /no_think"
    user = {
        "task_label": args.task_label,
        "allowed_files": allowed_files,
        "max_touched_files": args.max_touched_files,
        "diff_policy": "Return one unified diff proposal only for the allowed file set.",
        "prompt": prompt_text,
    }
    request: dict[str, Any] = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False, indent=2)},
        ],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if should_harden_structured_output(args.response_format):
        request["provider"] = {
            "require_parameters": True,
        }
        request["plugins"] = [
            {
                "id": "response-healing",
            }
        ]
    if args.response_format == "json_schema":
        request["response_format"] = {
            "type": "json_schema",
            "json_schema": PATCH_SCHEMA,
        }
    elif args.response_format == "json_object":
        request["response_format"] = {"type": "json_object"}
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
                "Janus Codex Direct OR Quickchange",
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


def coerce_quickchange_proposal_shape(proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        return proposal
    required_keys = {"status", "summary", "changed_files", "unified_diff", "validation_notes", "risk_notes"}
    if required_keys.issubset(proposal.keys()):
        return proposal

    file_value = proposal.get("file")
    diff_value = proposal.get("diff")
    summary_value = proposal.get("summary")
    if not isinstance(file_value, str) or not isinstance(diff_value, str):
        return proposal

    normalized_file = normalize_repo_path(file_value)
    summary_text = ""
    validation_notes: list[str] = []
    risk_notes: list[str] = []

    if isinstance(summary_value, dict):
        file_changed = summary_value.get("file_changed")
        text_changed = summary_value.get("text_changed")
        confirmation = summary_value.get("confirmation")
        summary_parts = [part for part in [text_changed, confirmation] if isinstance(part, str) and part.strip()]
        summary_text = " ".join(summary_parts).strip()
        if isinstance(file_changed, str) and file_changed.strip():
            validation_notes.append(f"model reported changed file: {normalize_repo_path(file_changed)}")
        if isinstance(confirmation, str) and confirmation.strip():
            validation_notes.append(confirmation.strip())
    elif isinstance(summary_value, str):
        summary_text = summary_value.strip()

    if not summary_text:
        summary_text = f"Bounded quickchange patch proposal for {normalized_file}."

    return {
        "status": "PATCH_PROPOSAL",
        "summary": summary_text,
        "changed_files": [normalized_file],
        "unified_diff": diff_value,
        "validation_notes": validation_notes,
        "risk_notes": risk_notes,
    }


def contains_forbidden_diff_operation(diff_text: str) -> bool:
    forbidden_patterns = [
        r"^deleted file mode ",
        r"^rename from ",
        r"^rename to ",
        r"^similarity index ",
        r"^--- /dev/null",
        r"^\+\+\+ /dev/null",
    ]
    return any(re.search(pattern, diff_text, flags=re.MULTILINE) for pattern in forbidden_patterns)


def validate_patch_proposal(
    *,
    proposal: dict[str, Any],
    editable_paths: list[str],
    max_touched_files: int,
) -> tuple[str, list[str]]:
    issues: list[str] = []
    status = proposal.get("status")
    if status not in {"PATCH_PROPOSAL", "NO_CHANGE", "BLOCKED"}:
        issues.append("status must be PATCH_PROPOSAL, NO_CHANGE, or BLOCKED")
    changed_files_raw = proposal.get("changed_files")
    if not isinstance(changed_files_raw, list):
        issues.append("changed_files must be a list")
        changed_files: list[str] = []
    else:
        changed_files = [normalize_repo_path(str(item)) for item in changed_files_raw]
    allowed = {normalize_repo_path(item) for item in editable_paths}
    outside = [item for item in changed_files if item not in allowed]
    if outside:
        issues.append(f"changed files outside allowlist: {', '.join(outside)}")
    if len(set(changed_files)) > max_touched_files:
        issues.append("changed file count exceeds max_touched_files")
    diff_text = proposal.get("unified_diff")
    if not isinstance(diff_text, str):
        issues.append("unified_diff must be a string")
        diff_text = ""
    if status == "PATCH_PROPOSAL" and not diff_text.strip():
        issues.append("PATCH_PROPOSAL requires non-empty unified_diff")
    if contains_forbidden_diff_operation(diff_text):
        issues.append("diff contains delete, rename, move, or /dev/null operation")
    if status == "PATCH_PROPOSAL" and not changed_files:
        issues.append("PATCH_PROPOSAL requires at least one changed file")
    if status in {"NO_CHANGE", "BLOCKED"} and changed_files:
        issues.append("NO_CHANGE or BLOCKED must not list changed files")
    return ("PASS" if not issues else "FAIL"), issues


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
        "skill_id": "janus-quickchange",
        "routing_mode": "Direct-OR",
        "selected_path": "direct_or_patch_proposal_then_codex_review",
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
        "quality_notes": "Direct OpenRouter patch proposal only; Codex remains local apply and validation owner.",
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
    parser = argparse.ArgumentParser(description="Direct OpenRouter quickchange patch proposal runner.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--model", required=True)
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
    parser.add_argument("--cost-estimate-basis", default="direct_or_quickchange_initial")
    parser.add_argument("--prompt-template-hash", default="direct_or_quickchange_v1")
    parser.add_argument("--task-variant", default="quickchange_patch_review")
    parser.add_argument("--price-snapshot-source", default="manual_current_openrouter_model_page")
    parser.add_argument("--price-snapshot-timestamp", default="")
    parser.add_argument("--estimated-codex-effort", default="low")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--response-format", choices=["json_schema", "json_object", "none"], default="json_schema")
    parser.add_argument("--use-local-fixture", action="store_true")
    parser.add_argument("--local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    resolved_budget_profile, budget_profile = load_budget_profile(args.budget_profile, args.task_class)
    args.budget_profile = resolved_budget_profile
    if args.cost_cap is None:
        args.cost_cap = float(budget_profile["per_call_cap_usd"])

    workflow_id = args.workflow_id or f"DIRECT-OR-QUICKCHANGE-{now_id()}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    pre_call_issues = validate_pre_call(args)
    if pre_call_issues:
        summary = {
            "summary_header": "DIRECT OR QUICKCHANGE RESULT",
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

    prompt_path = resolve_prompt_path(args.prompt_path)
    prompt_text = prompt_path.read_text(encoding="utf-8-sig")
    request_body = make_request_body(args, prompt_text)
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
            "summary_header": "DIRECT OR QUICKCHANGE RESULT",
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
        proposal = parse_json_from_text(content)
    except Exception as exc:
        proposal = {"status": "BLOCKED", "summary": f"Could not parse model content as JSON: {exc}", "changed_files": [], "unified_diff": "", "validation_notes": [], "risk_notes": []}
    proposal = coerce_quickchange_proposal_shape(proposal)
    write_json(run_dir / "patch_proposal.json", proposal)

    validation_result, issues = validate_patch_proposal(
        proposal=proposal,
        editable_paths=args.editable_path,
        max_touched_files=args.max_touched_files,
    )
    if cost_issue:
        issues.append("actual OR cost missing or above cap")
    if not response_summary.get("generation_id"):
        issues.append("generation_id missing")
    if not response_summary.get("usage"):
        issues.append("usage missing")
    if finish_reason == "length":
        issues.append("finish_reason=length")
    validation_result = "PASS" if not issues else "FAIL"
    final_outcome = "DIRECT_OR_PATCH_PROPOSAL_READY_FOR_CODEX_REVIEW" if validation_result == "PASS" else "DIRECT_OR_REJECT_AND_FALLBACK"
    recommendation = "OR_PREFERRED" if validation_result == "PASS" else "CODEX_PREFERRED"
    validation_summary = {
        "workflow_id": workflow_id,
        "validation_result": validation_result,
        "budget_profile": args.budget_profile,
        "issues": issues,
        "changed_files": proposal.get("changed_files", []),
        "editable_paths": [normalize_repo_path(item) for item in args.editable_path],
        "max_touched_files": args.max_touched_files,
        "finish_reason": finish_reason,
        "actual_or_cost": cost,
        "cost_cap": args.cost_cap,
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    telemetry_path = MODEL_ROUTING_DIR / f"or_healthcheck_telemetry_direct_or_quickchange_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
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
        "summary_header": "DIRECT OR QUICKCHANGE RESULT",
        "workflow_id": workflow_id,
        "task_label": args.task_label,
        "selected_path": "direct_or_patch_proposal_then_codex_review",
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
        "patch_proposal_path": str(run_dir / "patch_proposal.json"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "telemetry_jsonl_path": str(telemetry_path),
        "healthcheck_status": healthcheck_status,
        "healthcheck_summary_path": healthcheck_summary_path,
        "operator_result_lines": [
            f"Ergebnis: {final_outcome}",
            f"Tatsaechliche Kosten: {(cost or 0.0):.9f}",
        ],
        "operator_message": "Direct OR produced a bounded patch proposal. Codex must review and apply locally." if validation_result == "PASS" else "Direct OR result failed bounded gates. Fallback to Codex-only.",
    }
    write_json(run_dir / "operator_summary.json", operator_summary)
    output(operator_summary)
    return 0 if validation_result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
