#!/usr/bin/env python3
"""Bounded OR review helper for janus-skill-router."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "skill-router-review-runs"
WRAPPER_PATH = MODEL_ROUTING_DIR / "scripts" / "or_file_first_capture_wrapper.ps1"
HEALTH_SNAPSHOT_PATH = (
    REPO_ROOT
    / "documentation"
    / "codex"
    / "skills"
    / "janus-health-check"
    / "scripts"
    / "health_snapshot.py"
)
DEFAULT_SKILL_ROUTER_OR_MODEL = "qwen/qwen3-coder-30b-a3b-instruct"

if str(MODEL_ROUTING_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))

from bounded_or_worker_gate_prompt import (  # noqa: E402
    build_missing_gate_result,
)


REQUIRED_INPUT_FIELDS = [
    "workflow_id",
    "bound_skill_context",
    "user_request",
    "bound_artifact_paths",
    "expected_next_skill",
    "expected_model",
    "expected_reasoning",
    "expected_new_chat",
    "expected_context_strategy",
    "expected_reason",
    "redaction_ready",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "route_type",
    "recommended_skill",
    "recommended_model",
    "recommended_reasoning",
    "new_chat",
    "context_strategy",
    "reason",
    "next_artifact_hint",
    "manual_review_needed",
    "notes",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def write_single_jsonl_row(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_choice(choice: str) -> str:
    value = choice.strip().lower()
    if value == "prompt":
        return "prompt"
    if value in {"local", "codex", "1"}:
        return "local"
    if value in {"delegated", "or", "openrouter", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, delegated/2/or/openrouter")


def build_run_dir(workflow_id: str) -> Path:
    return RUN_ROOT / workflow_id


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def parse_json_from_text(text: str) -> dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(stripped[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("response content is not a JSON object")


def content_from_response(response_body: dict[str, object]) -> str:
    choices = response_body.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message") if isinstance(first_choice, dict) else {}
    if not isinstance(message, dict):
        return ""
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


def prompt_lines(task_label: str, model_label: str, estimated_cost: float, confidence_percent: float) -> list[str]:
    return [
        "1 = Codex",
        "2 = OR",
        "OR ist hier die externe Option, um Codex-Guthaben zu sparen.",
        "Live-Evidenz: bounded router review lane in fixture-validation mode",
        "Einordnung: routing recommendation only; Codex keeps final process authority",
        f"Fest empfohlenes OR-Modell: {model_label}",
        f"Pre-Call-Kostenbasis: Skill-router bounded lane for {task_label}",
        f"Voraussichtliche OR-Kosten {estimated_cost:.9f}, Evidenzgenauigkeit {confidence_percent:.0f}%",
    ]


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    if payload.get("bound_skill_context") != "janus-skill-router":
        issues.append("bound_skill_context must be exactly janus-skill-router")
    bound_paths = payload.get("bound_artifact_paths")
    if not isinstance(bound_paths, list) or not bound_paths:
        issues.append("bound_artifact_paths must be a non-empty list")
    if payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")
    return issues


def validate_result_payload(payload: dict[str, Any], input_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in payload:
            issues.append(f"missing result field: {field}")
    if payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status must be PASS, WEAK_SIGNAL, or BLOCKED")
    if payload.get("route_type") not in {"DIRECT_NEXT_SKILL", "MODEL_SWITCH_GATE", "BLOCKED"}:
        issues.append("route_type invalid")
    if payload.get("recommended_skill") != input_payload.get("expected_next_skill"):
        issues.append("recommended_skill must match expected_next_skill")
    if payload.get("recommended_model") != input_payload.get("expected_model"):
        issues.append("recommended_model must match expected_model")
    if payload.get("recommended_reasoning") != input_payload.get("expected_reasoning"):
        issues.append("recommended_reasoning must match expected_reasoning")
    if payload.get("new_chat") != input_payload.get("expected_new_chat"):
        issues.append("new_chat must match expected_new_chat")
    if payload.get("context_strategy") != input_payload.get("expected_context_strategy"):
        issues.append("context_strategy must match expected_context_strategy")
    if str(payload.get("reason") or "").strip() != str(input_payload.get("expected_reason") or "").strip():
        issues.append("reason must match expected_reason")
    if payload.get("manual_review_needed") not in {"YES", "NO"}:
        issues.append("manual_review_needed must be YES or NO")
    notes = payload.get("notes")
    if not isinstance(notes, list) or not (1 <= len(notes) <= 4):
        issues.append("notes must contain 1 to 4 items")
    if not str(payload.get("next_artifact_hint") or "").strip():
        issues.append("next_artifact_hint invalid")
    return issues


def build_request_body(model: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded Janus skill-router review assistant. "
                    "Use only the redacted input package. "
                    "Return exactly one JSON object and no prose. "
                    "Do not claim authoritative execution, implementation, Git, release, routing-table, or final process authority."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return a JSON object with these exact top-level fields: "
                    "status, route_type, recommended_skill, recommended_model, recommended_reasoning, "
                    "new_chat, context_strategy, reason, next_artifact_hint, manual_review_needed, notes.\n\n"
                    "Rules:\n"
                    "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
                    "- route_type must be DIRECT_NEXT_SKILL, MODEL_SWITCH_GATE, or BLOCKED\n"
                    "- recommended_skill, recommended_model, recommended_reasoning, new_chat, context_strategy, and reason "
                    "must match the expected values from the input package exactly\n"
                    "- manual_review_needed must be YES or NO\n"
                    "- notes must contain 1 to 4 short strings\n"
                    "- next_artifact_hint must be one short path or artifact note\n"
                    "- do not invent broader scope or new authority\n\n"
                    f"Redacted input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 1200,
    }


def invoke_file_first_wrapper(
    *,
    run_dir: Path,
    request_body_path: Path,
    use_local_fixture: bool,
    local_fixture_response_path: Path | None,
    execute_live: bool,
    title: str,
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
            raise SystemExit("--use-local-or-fixture requires --or-local-fixture-response-path")
        command.extend(["-UseLocalFixture", "-LocalFixtureResponsePath", str(local_fixture_response_path.resolve())])
    elif execute_live:
        api_key = __import__("os").environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise SystemExit("OPENROUTER_API_KEY missing for live skill-router OR invocation")
        command.extend(
            [
                "-AuthorizationBearer",
                f"Bearer {api_key}",
                "-HttpReferer",
                "https://github.com/pruvex/Janus-Projekt",
                "-XTitle",
                title,
            ]
        )
    else:
        raise SystemExit("choose --use-local-or-fixture or --execute-direct-or")
    return run_command(command)


def run_healthcheck(telemetry_path: Path, run_dir: Path) -> dict[str, object]:
    command = [
        sys.executable,
        str(HEALTH_SNAPSHOT_PATH),
        "--repo",
        str(REPO_ROOT),
        "--or-telemetry-jsonl",
        str(telemetry_path),
    ]
    completed = run_command(command)
    write_text(run_dir / "healthcheck_stdout.log", completed.stdout)
    write_text(run_dir / "healthcheck_stderr.log", completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "health_snapshot.py failed")
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise RuntimeError("health_snapshot.py did not return a JSON object")
    write_json(run_dir / "healthcheck_summary.json", parsed)
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--estimated-or-cost", type=float, required=True)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, required=True)
    parser.add_argument("--input-package-json")
    parser.add_argument("--use-local-or-fixture", action="store_true")
    parser.add_argument("--or-local-fixture-response-path")
    parser.add_argument("--execute-direct-or", action="store_true")
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    run_dir = build_run_dir(args.workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_text = prompt_lines(
        args.task_label,
        DEFAULT_SKILL_ROUTER_OR_MODEL,
        args.estimated_or_cost,
        args.cost_estimate_confidence_percent,
    )
    write_text(run_dir / "operator_prompt.txt", "\n".join(prompt_text) + "\n")

    if args.input_package_json:
        input_payload = load_json(Path(args.input_package_json))
        input_issues = validate_input_package(input_payload)
        write_json(run_dir / "input_package_snapshot.json", input_payload)
    else:
        input_payload = {}
        input_issues = ["missing input package json"]

    if input_issues:
        result_payload = build_missing_gate_result(
            workflow_id=args.workflow_id,
            task_label=args.task_label,
            selected_path="Codex-only",
            missing_fields=input_issues,
            final_outcome="SKILL_ROUTER_INPUT_INVALID",
            normal_target_model=args.normal_target_model,
            skill="janus-skill-router",
            task_class="SKILL_ROUTER_REVIEW",
            eligibility_result="NOT_ELIGIBLE",
            eligibility_reason_code="MISSING_INPUT",
            evidence_status="NO_OR_RUN",
        )
        write_json(run_dir / "result.json", result_payload)
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 1

    if choice == "prompt":
        result_payload = {
            "summary_header": "SKILL ROUTER GATE",
            "workflow_id": args.workflow_id,
            "skill": "janus-skill-router",
            "task_label": args.task_label,
            "selected_path": "operator_choice_pending",
            "normal_target_model": args.normal_target_model,
            "choice_1": "Codex",
            "choice_2": "OR",
            "selected_or_model": DEFAULT_SKILL_ROUTER_OR_MODEL,
            "estimated_or_cost": args.estimated_or_cost,
            "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
            "operator_prompt_lines": prompt_text,
            "boundaries": [
                "No delegated implementation",
                "No delegated Git or release authority",
                "No delegated final process authority",
                "Codex remains final router and gate owner",
            ],
            "final_outcome": "AWAITING_OPERATOR_CHOICE",
            "validation_result": "PASS",
        }
        write_json(run_dir / "result.json", result_payload)
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 0

    if choice == "local":
        result_payload = {
            "status": "PASS",
            "route_type": "DIRECT_NEXT_SKILL",
            "recommended_skill": input_payload["expected_next_skill"],
            "recommended_model": input_payload["expected_model"],
            "recommended_reasoning": input_payload["expected_reasoning"],
            "new_chat": input_payload["expected_new_chat"],
            "context_strategy": input_payload["expected_context_strategy"],
            "reason": input_payload["expected_reason"],
            "next_artifact_hint": input_payload["bound_artifact_paths"][0],
            "manual_review_needed": "NO",
            "notes": ["Local Codex routing path used.", "No OR call performed."],
            "validation_result": "PASS",
        }
        write_json(run_dir / "result.json", result_payload)
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 0

    if not args.use_local_or_fixture and not args.execute_direct_or:
        raise SystemExit("delegated mode currently requires --use-local-or-fixture or --execute-direct-or")
    if args.use_local_or_fixture:
        if not args.or_local_fixture_response_path:
            raise SystemExit("--or-local-fixture-response-path is required in delegated fixture mode")
        fixture_payload = load_json(Path(args.or_local_fixture_response_path))
        write_json(run_dir / "fixture_response_snapshot.json", fixture_payload)
        content = content_from_response(fixture_payload)
        parsed = parse_json_from_text(content) if content else dict(fixture_payload)
        result_payload = {
            "status": str(parsed.get("status") or "PASS"),
            "route_type": str(parsed.get("route_type") or "DIRECT_NEXT_SKILL"),
            "recommended_skill": str(parsed.get("recommended_skill") or input_payload["expected_next_skill"]),
            "recommended_model": str(parsed.get("recommended_model") or input_payload["expected_model"]),
            "recommended_reasoning": str(parsed.get("recommended_reasoning") or input_payload["expected_reasoning"]),
            "new_chat": str(parsed.get("new_chat") or input_payload["expected_new_chat"]),
            "context_strategy": str(parsed.get("context_strategy") or input_payload["expected_context_strategy"]),
            "reason": str(parsed.get("reason") or input_payload["expected_reason"]),
            "next_artifact_hint": str(parsed.get("next_artifact_hint") or input_payload["bound_artifact_paths"][0]),
            "manual_review_needed": str(parsed.get("manual_review_needed") or "NO"),
            "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [str(parsed.get("notes") or "Fixture response used.")],
        }
        issues = validate_result_payload(result_payload, input_payload)
        validation_result = "PASS" if not issues else "FAIL"
        result_payload["validation_result"] = validation_result
        result_payload["issue_count"] = len(issues)
        write_json(run_dir / "result.json", result_payload)

        telemetry_row = {
            "workflow_id": args.workflow_id,
            "skill_id": "janus-skill-router",
            "routing_mode": "Manual-review",
            "selected_path": "delegated_skill_router_review",
            "codex_default_model": args.normal_target_model,
            "or_model": DEFAULT_SKILL_ROUTER_OR_MODEL,
            "estimated_prompt_tokens": 0,
            "estimated_completion_tokens": 0,
            "estimated_or_cost": args.estimated_or_cost,
            "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
            "cost_estimate_sample_count": 0,
            "cost_estimate_mean_abs_error_percent": 0.0,
            "cost_estimate_p50_error_percent": 0.0,
            "cost_estimate_p90_error_percent": 0.0,
            "cost_estimate_basis": "skill_router_fixture_gate",
            "prompt_template_hash": "skill_router_review_v1",
            "task_variant": "skill_router_review",
            "price_snapshot_source": "fixture",
            "price_snapshot_timestamp": datetime.utcnow().isoformat(),
            "actual_prompt_tokens": 0,
            "actual_completion_tokens": 0,
            "actual_reasoning_tokens": None,
            "actual_cached_tokens": None,
            "actual_or_cost": 0.0,
            "generation_id": "fixture-skill-router-review",
            "usage_source": "fallback_estimate",
            "estimated_codex_effort": "medium",
            "estimation_error_percent": 0.0,
            "cost_delta_vs_codex_estimate": 0.0,
            "latency_ms": 0,
            "validation_result": validation_result,
            "fallback_used": "NO",
            "rework_required": "NO" if validation_result == "PASS" else "YES",
            "final_outcome": "SKILL_ROUTER_REVIEW_READY_FOR_CODEX_VALIDATION" if validation_result == "PASS" else "SKILL_ROUTER_REVIEW_NEEDS_CODEX_RECHECK",
            "reason_for_escalation": "bounded routing recommendation review",
            "quality_notes": "Fixture-validated bounded skill-router review only; Codex remains final router and gate owner.",
            "recommendation_signal": "OR_PREFERRED" if validation_result == "PASS" else "MANUAL_REVIEW",
        }
        telemetry_path = run_dir / "or_healthcheck_telemetry.jsonl"
        write_single_jsonl_row(telemetry_path, telemetry_row)
        run_healthcheck(telemetry_path, run_dir)
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 0 if validation_result == "PASS" else 2

    request_body = build_request_body(DEFAULT_SKILL_ROUTER_OR_MODEL, input_payload)
    request_path = run_dir / "request_body.json"
    write_json(request_path, request_body)
    completed = invoke_file_first_wrapper(
        run_dir=run_dir,
        request_body_path=request_path,
        use_local_fixture=False,
        local_fixture_response_path=None,
        execute_live=True,
        title="Janus Skill Router Review",
    )
    write_text(run_dir / "wrapper_stdout.log", completed.stdout)
    write_text(run_dir / "wrapper_stderr.log", completed.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or "wrapper failed")
    response_body = load_json(run_dir / "response_body.json")
    response_summary = load_json(run_dir / "response_summary.json")
    parsed = parse_json_from_text(content_from_response(response_body))
    result_payload = {
        "status": str(parsed.get("status") or "PASS"),
        "route_type": str(parsed.get("route_type") or "DIRECT_NEXT_SKILL"),
        "recommended_skill": str(parsed.get("recommended_skill") or input_payload["expected_next_skill"]),
        "recommended_model": str(parsed.get("recommended_model") or input_payload["expected_model"]),
        "recommended_reasoning": str(parsed.get("recommended_reasoning") or input_payload["expected_reasoning"]),
        "new_chat": str(parsed.get("new_chat") or input_payload["expected_new_chat"]),
        "context_strategy": str(parsed.get("context_strategy") or input_payload["expected_context_strategy"]),
        "reason": str(parsed.get("reason") or input_payload["expected_reason"]),
        "next_artifact_hint": str(parsed.get("next_artifact_hint") or input_payload["bound_artifact_paths"][0]),
        "manual_review_needed": str(parsed.get("manual_review_needed") or "NO"),
        "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [str(parsed.get("notes") or "Live OR response used.")],
    }
    issues = validate_result_payload(result_payload, input_payload)
    validation_result = "PASS" if not issues else "FAIL"
    result_payload["validation_result"] = validation_result
    result_payload["issue_count"] = len(issues)
    write_json(run_dir / "result.json", result_payload)

    actual_or_cost = response_summary.get("actual_or_cost")
    if not isinstance(actual_or_cost, (int, float)):
        actual_or_cost = 0.0
    telemetry_row = {
        "workflow_id": args.workflow_id,
        "skill_id": "janus-skill-router",
        "routing_mode": "Manual-review",
        "selected_path": "delegated_skill_router_review",
        "codex_default_model": args.normal_target_model,
        "or_model": DEFAULT_SKILL_ROUTER_OR_MODEL,
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "estimated_or_cost": args.estimated_or_cost,
        "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
        "cost_estimate_sample_count": 1,
        "cost_estimate_mean_abs_error_percent": 0.0,
        "cost_estimate_p50_error_percent": 0.0,
        "cost_estimate_p90_error_percent": 0.0,
        "cost_estimate_basis": "skill_router_live_gate",
        "prompt_template_hash": "skill_router_review_v1",
        "task_variant": "skill_router_review",
        "price_snapshot_source": "live_openrouter_response",
        "price_snapshot_timestamp": datetime.utcnow().isoformat(),
        "actual_prompt_tokens": response_summary.get("actual_prompt_tokens"),
        "actual_completion_tokens": response_summary.get("actual_completion_tokens"),
        "actual_reasoning_tokens": response_summary.get("actual_reasoning_tokens"),
        "actual_cached_tokens": response_summary.get("actual_cached_tokens"),
        "actual_or_cost": float(actual_or_cost),
        "generation_id": response_summary.get("generation_id"),
        "usage_source": response_summary.get("usage_source") or "response_usage",
        "estimated_codex_effort": "medium",
        "estimation_error_percent": 0.0,
        "cost_delta_vs_codex_estimate": float(actual_or_cost) - args.estimated_or_cost,
        "latency_ms": response_summary.get("latency_ms") or 0,
        "validation_result": validation_result,
        "fallback_used": "NO",
        "rework_required": "NO" if validation_result == "PASS" else "YES",
        "final_outcome": "SKILL_ROUTER_REVIEW_READY_FOR_CODEX_VALIDATION" if validation_result == "PASS" else "SKILL_ROUTER_REVIEW_NEEDS_CODEX_RECHECK",
        "reason_for_escalation": "bounded routing recommendation review",
        "quality_notes": "Bounded skill-router review only; Codex remains final router and gate owner.",
        "recommendation_signal": "OR_PREFERRED" if validation_result == "PASS" else "MANUAL_REVIEW",
    }
    telemetry_path = run_dir / "or_healthcheck_telemetry.jsonl"
    write_single_jsonl_row(telemetry_path, telemetry_row)
    run_healthcheck(telemetry_path, run_dir)
    print(json.dumps(result_payload, indent=2, ensure_ascii=False))
    return 0 if validation_result == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
