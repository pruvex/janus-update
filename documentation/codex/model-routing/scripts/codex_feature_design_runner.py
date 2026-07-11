#!/usr/bin/env python3
"""Bounded OR review helper for janus-feature-design."""

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
RUN_ROOT = MODEL_ROUTING_DIR / "feature-design-runs"
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
DEFAULT_FEATURE_DESIGN_OR_MODEL = "qwen/qwen3-coder-30b-a3b-instruct"

if str(MODEL_ROUTING_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))

from bounded_or_worker_gate_prompt import (  # noqa: E402
    build_missing_gate_result,
    build_operator_prompt_lines,
    missing_gate_fields,
)


REQUIRED_INPUT_FIELDS = [
    "workflow_id",
    "bound_skill_context",
    "raw_feature_request",
    "locked_answers",
    "expected_routing_decision",
    "expected_next_skill",
    "expected_output",
    "redaction_ready",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "decision_state",
    "recommended_next_skill",
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


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


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


def actual_or_cost(response_summary: dict[str, object]) -> float | None:
    value = response_summary.get("actual_or_cost")
    if isinstance(value, (int, float)):
        return float(value)
    usage = response_summary.get("usage")
    if isinstance(usage, dict):
        cost = usage.get("cost")
        if isinstance(cost, (int, float)):
            return float(cost)
    return None


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


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    if payload.get("bound_skill_context") != "janus-feature-design":
        issues.append("bound_skill_context must be exactly janus-feature-design")
    answers = payload.get("locked_answers")
    if not isinstance(answers, list) or len(answers) < 8:
        issues.append("locked_answers must contain at least 8 lines")
    if payload.get("expected_routing_decision") not in {"FULL FEATURE PIPELINE", "BACKLOG PIPELINE"}:
        issues.append("expected_routing_decision invalid")
    if payload.get("expected_next_skill") not in {"janus-spec-generator", "janus-backlog-intake"}:
        issues.append("expected_next_skill invalid")
    if payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")
    return issues


def build_rendered_decision_summary(payload: dict[str, Any]) -> str:
    summary = payload.get("structured_decision_summary")
    if not isinstance(summary, dict):
        return str(payload.get("latest_decision_summary") or "")
    ordered_keys = [
        "Feature Name",
        "Primary Goal",
        "User Problem",
        "User Value",
        "Primary Target Surface",
        "Existing or New Surface",
        "Existence Confirmation",
        "User Trigger",
        "Success Behavior",
        "Failure Behavior",
        "User Action Surface",
        "Data / Persistence",
        "Security / Privacy",
        "Edge Cases",
        "Out of Scope",
        "Routing Decision",
        "Routing Reason",
        "Recommended Next Skill",
    ]
    lines = ["LATEST DECISION SUMMARY"]
    for key in ordered_keys:
        value = summary.get(key)
        if isinstance(value, list):
            rendered = "; ".join(str(item).strip() for item in value if str(item).strip())
        else:
            rendered = str(value).strip() if value is not None else ""
        lines.append(f"{key}: {rendered}")
    return "\n".join(lines) + "\n"


def validate_result_payload(payload: dict[str, Any], input_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in payload:
            issues.append(f"missing result field: {field}")
    if payload.get("decision_state") not in {"DECISION_SUMMARY_READY", "BLOCKING_QUESTION"}:
        issues.append("decision_state invalid")
    if payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status invalid")
    if payload.get("recommended_next_skill") not in {"janus-spec-generator", "janus-backlog-intake", "NEEDS_INFO"}:
        issues.append("recommended_next_skill invalid")
    notes = payload.get("notes")
    if not isinstance(notes, list) or not (1 <= len(notes) <= 4):
        issues.append("notes invalid")

    if payload.get("decision_state") == "DECISION_SUMMARY_READY":
        rendered = build_rendered_decision_summary(payload)
        if not rendered.strip():
            issues.append("latest decision summary missing after render")
            return issues
        for required_prefix in [
            "Feature Name:",
            "Primary Goal:",
            "User Problem:",
            "User Value:",
            "Primary Target Surface:",
            "Existing or New Surface:",
            "Existence Confirmation:",
            "User Trigger:",
            "Success Behavior:",
            "Failure Behavior:",
            "User Action Surface:",
            "Data / Persistence:",
            "Security / Privacy:",
            "Edge Cases:",
            "Out of Scope:",
            "Routing Decision:",
            "Routing Reason:",
            "Recommended Next Skill:",
        ]:
            if required_prefix not in rendered:
                issues.append(f"missing summary field: {required_prefix}")
        if f"Routing Decision: {input_payload['expected_routing_decision']}" not in rendered:
            issues.append("routing decision does not match expected_routing_decision")
        if f"Recommended Next Skill: {input_payload['expected_next_skill']}" not in rendered:
            issues.append("recommended next skill does not match expected_next_skill")
    else:
        for field in ["blocking_question", "option_a", "option_b", "recommendation"]:
            if not str(payload.get(field) or "").strip():
                issues.append(f"{field} missing for BLOCKING_QUESTION state")
    return issues


def render_result_markdown(result_payload: dict[str, Any]) -> str:
    if result_payload.get("decision_state") == "DECISION_SUMMARY_READY":
        body = build_rendered_decision_summary(result_payload).strip()
    else:
        body = "\n".join(
            [
                "BLOCKING QUESTION",
                f"Question: {result_payload.get('blocking_question', '')}",
                f"Option A: {result_payload.get('option_a', '')}",
                f"Option B: {result_payload.get('option_b', '')}",
                f"Recommendation: {result_payload.get('recommendation', '')}",
            ]
        )
    lines = [
        "FEATURE_DESIGN_REVIEW",
        f"Status: {result_payload['status']}",
        f"Decision State: {result_payload['decision_state']}",
        f"Recommended Next Skill: {result_payload['recommended_next_skill']}",
        body,
        f"Notes: {result_payload['notes']}",
    ]
    return "\n".join(lines) + "\n"


def build_request_body(model: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded Janus feature-design assistant. "
                    "Use only the redacted input package. "
                    "Return exactly one JSON object and no prose. "
                    "Do not claim implementation, task creation, Git authority, release authority, or final product decision authority. "
                    "Your job is only to consolidate already-given answers into a bounded structured decision summary draft or exactly one blocking question."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return a JSON object with these exact top-level fields: "
                    "status, decision_state, recommended_next_skill, notes, structured_decision_summary, blocking_question, option_a, option_b, recommendation.\n\n"
                    "Rules:\n"
                    "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
                    "- decision_state must be DECISION_SUMMARY_READY or BLOCKING_QUESTION\n"
                    "- recommended_next_skill must be janus-spec-generator, janus-backlog-intake, or NEEDS_INFO\n"
                    "- notes must contain 1 to 4 short strings\n"
                    "- if decision_state is DECISION_SUMMARY_READY, structured_decision_summary must be an object with exactly these keys: "
                    "Feature Name, Primary Goal, User Problem, User Value, Primary Target Surface, Existing or New Surface, Existence Confirmation, User Trigger, Success Behavior, Failure Behavior, User Action Surface, Data / Persistence, Security / Privacy, Edge Cases, Out of Scope, Routing Decision, Routing Reason, Recommended Next Skill\n"
                    "- if decision_state is BLOCKING_QUESTION, provide exactly one blocking_question plus option_a, option_b, and recommendation, and do not invent a finished decision summary\n"
                    "- Routing Decision must match the best bounded interpretation of the locked answers and should usually equal the expected routing decision when the package is sufficiently locked\n"
                    "- Do not claim final product authority; Codex remains the final decision owner\n\n"
                    f"Redacted input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 1800,
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
            raise SystemExit("OPENROUTER_API_KEY missing for live feature-design OR invocation")
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


def build_telemetry_row(
    *,
    workflow_id: str,
    normal_target_model: str,
    or_model: str,
    estimated_or_cost: float,
    cost_estimate_confidence_percent: float,
    response_summary: dict[str, object],
    validation_result: str,
    final_outcome: str,
    fallback_used: str,
    rework_required: str,
    latency_ms: int,
) -> dict[str, object]:
    actual_cost = actual_or_cost(response_summary)
    estimation_error_percent = 0.0
    if actual_cost not in {None, 0.0} and estimated_or_cost > 0:
        estimation_error_percent = abs((float(actual_cost) - estimated_or_cost) / estimated_or_cost) * 100.0
    usage = response_summary.get("usage") if isinstance(response_summary.get("usage"), dict) else {}
    usage = usage if isinstance(usage, dict) else {}
    return {
        "workflow_id": workflow_id,
        "skill_id": "janus-feature-design",
        "routing_mode": "Manual-review",
        "selected_path": "delegated_feature_design_review",
        "codex_default_model": normal_target_model,
        "or_model": or_model,
        "estimated_or_cost": estimated_or_cost,
        "cost_estimate_confidence_percent": cost_estimate_confidence_percent,
        "cost_estimate_sample_count": 1,
        "cost_estimate_mean_abs_error_percent": round(estimation_error_percent, 2),
        "cost_estimate_p50_error_percent": round(estimation_error_percent, 2),
        "cost_estimate_p90_error_percent": round(estimation_error_percent, 2),
        "cost_estimate_basis": "feature_design_initial_batch",
        "prompt_template_hash": "feature_design_review_v1",
        "task_variant": "feature_design_review",
        "price_snapshot_source": "live_openrouter_response",
        "price_snapshot_timestamp": datetime.now().isoformat(),
        "actual_prompt_tokens": usage.get("prompt_tokens"),
        "actual_completion_tokens": usage.get("completion_tokens"),
        "actual_reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") if isinstance(usage.get("completion_tokens_details"), dict) else None,
        "actual_cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens") if isinstance(usage.get("prompt_tokens_details"), dict) else None,
        "actual_or_cost": actual_cost,
        "generation_id": str(response_summary.get("generation_id") or ""),
        "usage_source": "response_usage" if usage else "fallback_estimate",
        "estimated_codex_effort": "medium",
        "estimation_error_percent": round(estimation_error_percent, 2),
        "cost_delta_vs_codex_estimate": round((actual_cost or 0.0) - estimated_or_cost, 8),
        "latency_ms": latency_ms,
        "validation_result": validation_result,
        "fallback_used": fallback_used,
        "rework_required": rework_required,
        "final_outcome": final_outcome,
        "reason_for_escalation": "",
        "quality_notes": "Bounded feature-design draft only; Codex remains final decision owner and writer.",
        "recommendation_signal": "OR_PREFERRED" if validation_result == "PASS" else "CODEX_PREFERRED",
    }


def prompt_summary(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    delegated_model_label: str,
    estimated_or_cost: float | None,
    cost_estimate_confidence_percent: float | None,
) -> dict[str, Any]:
    missing_fields = missing_gate_fields(
        selected_or_model=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
    )
    if missing_fields:
        return build_missing_gate_result(
            workflow_id=workflow_id,
            task_label=task_label,
            selected_path="codex_only_prompt_data_missing",
            missing_fields=missing_fields,
            final_outcome="LOCAL_CODEX_PATH_SELECTED",
            normal_target_model=normal_target_model,
            skill="janus-feature-design",
        )
    return {
        "summary_header": "FEATURE DESIGN GATE",
        "workflow_id": workflow_id,
        "skill": "janus-feature-design",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "selected_or_model": delegated_model_label,
        "estimated_or_cost": float(estimated_or_cost),
        "cost_estimate_confidence_percent": float(cost_estimate_confidence_percent),
        "choice_1": "Codex",
        "choice_2": "OR",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded decision-summary draft or one blocking question from already-given feature answers",
        "operator_prompt_lines": build_operator_prompt_lines(
            choice_2_label="OR",
            selected_or_model=delegated_model_label,
            estimated_or_cost=float(estimated_or_cost),
            cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
        ),
        "boundaries": [
            "No delegated final product decision authority",
            "No delegated implementation or task creation",
            "No delegated Git or release authority",
            "Codex remains final feature-design owner",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "FEATURE DESIGN RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-feature-design",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex feature-design path. No delegated OR feature-design path was used.",
    }


def run_consumer_flow(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    delegated_model_label: str,
    estimated_or_cost: float,
    cost_estimate_confidence_percent: float,
    input_package_json: Path,
    use_local_or_fixture: bool,
    or_local_fixture_response_path: Path | None,
    execute_direct_or: bool,
) -> dict[str, Any]:
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    input_payload = load_json(input_package_json.resolve())
    input_issues = validate_input_package(input_payload)
    write_json(run_dir / "consumer_input_package.json", input_payload)
    if input_issues:
        result = {
            "summary_header": "FEATURE DESIGN RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-feature-design",
            "task_label": task_label,
            "selected_path": "input_package_invalid",
            "validation_result": "FAIL",
            "final_outcome": "FEATURE_DESIGN_INPUT_INVALID",
            "result_issues": input_issues,
            "operator_message": "Input package failed bounded validation before any OR call.",
        }
        write_json(run_dir / "consumer_operator_choice_delegated.json", result)
        return result

    request_body = build_request_body(delegated_model_label, input_payload)
    request_body_path = run_dir / "request_body_source.json"
    write_json(request_body_path, request_body)

    started = time.time()
    completed = invoke_file_first_wrapper(
        run_dir=run_dir,
        request_body_path=request_body_path,
        use_local_fixture=use_local_or_fixture,
        local_fixture_response_path=or_local_fixture_response_path,
        execute_live=execute_direct_or,
        title="Janus Feature Design Review",
    )
    latency_ms = int((time.time() - started) * 1000)
    write_text(run_dir / "wrapper_stdout.log", completed.stdout)
    write_text(run_dir / "wrapper_stderr.log", completed.stderr)

    response_body_path = run_dir / "response_body.json"
    response_summary_path = run_dir / "response_summary.json"
    if completed.returncode != 0 or not response_body_path.exists() or not response_summary_path.exists():
        result = {
            "summary_header": "FEATURE DESIGN RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-feature-design",
            "task_label": task_label,
            "selected_path": "wrapper_failed",
            "validation_result": "FAIL",
            "final_outcome": "FEATURE_DESIGN_WRAPPER_FAILED",
            "result_issues": ["wrapper capture failed before delegated response validation"],
            "operator_message": "Delegated feature-design path failed before bounded capture completed. Fallback to Codex-only is required.",
        }
        write_json(run_dir / "consumer_operator_choice_delegated.json", result)
        return result

    response_body = load_json(response_body_path)
    response_summary = load_json(response_summary_path)
    delegated_text = content_from_response(response_body)
    try:
        extracted_payload = parse_json_from_text(delegated_text)
        result_issues = validate_result_payload(extracted_payload, input_payload)
    except Exception as exc:
        extracted_payload = {}
        result_issues = [f"parse_failed: {exc}"]

    write_json(run_dir / "delegated_result_payload.json", extracted_payload if extracted_payload else {"raw_content": delegated_text})
    delegated_markdown = render_result_markdown(extracted_payload) if extracted_payload and not result_issues else (delegated_text if delegated_text else "NO_DELEGATED_RESULT_CAPTURED\n")
    write_text(run_dir / "delegated_result.md", delegated_markdown)

    finish_reason = str(response_summary.get("finish_reason") or "")
    actual_cost = actual_or_cost(response_summary)
    if finish_reason == "length":
        result_issues.append("finish_reason=length")
    if not str(response_summary.get("generation_id") or "").strip():
        result_issues.append("generation_id missing")
    if actual_cost is None:
        result_issues.append("actual OR cost missing")

    validation_summary = {
        "workflow_id": workflow_id,
        "task_label": task_label,
        "validation_issues": result_issues,
        "finish_reason": finish_reason,
        "actual_or_cost": actual_cost,
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    validation_result = "PASS" if not result_issues else "FAIL"
    final_outcome = "FEATURE_DESIGN_REVIEW_READY_FOR_CODEX_VALIDATION" if validation_result == "PASS" else "FEATURE_DESIGN_REVIEW_FAILED_VALIDATION"
    telemetry_path = MODEL_ROUTING_DIR / f"or_healthcheck_telemetry_feature_design_2026-06-26_{workflow_id}.jsonl"
    telemetry_row = build_telemetry_row(
        workflow_id=workflow_id,
        normal_target_model=normal_target_model,
        or_model=delegated_model_label,
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        response_summary=response_summary,
        validation_result=validation_result,
        final_outcome=final_outcome,
        fallback_used="NO" if validation_result == "PASS" else "YES",
        rework_required="NO" if validation_result == "PASS" else "YES",
        latency_ms=latency_ms,
    )
    write_single_jsonl_row(telemetry_path, telemetry_row)

    healthcheck_status = "FAIL"
    healthcheck_summary_path = ""
    try:
        healthcheck_summary = run_healthcheck(telemetry_path, run_dir)
        healthcheck_status = "PASS"
        healthcheck_summary_path = str(run_dir / "healthcheck_summary.json")
    except Exception as exc:
        result_issues.append(f"healthcheck_failed: {exc}")
        validation_result = "FAIL"
        final_outcome = "FEATURE_DESIGN_REVIEW_FAILED_HEALTHCHECK"
        healthcheck_summary = {"error": str(exc)}

    result = {
        "summary_header": "FEATURE DESIGN RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-feature-design",
        "task_label": task_label,
        "selected_path": "delegated_feature_design_review" if healthcheck_status == "PASS" and validation_result == "PASS" else "abort_post_validation",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "input_package_path": str(run_dir / "consumer_input_package.json"),
        "request_body_path": str(request_body_path),
        "response_body_path": str(response_body_path),
        "response_summary_path": str(response_summary_path),
        "delegated_result_path": str(run_dir / "delegated_result.md"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "telemetry_jsonl_path": str(telemetry_path),
        "healthcheck_summary_path": healthcheck_summary_path,
        "validation_result": validation_result,
        "final_outcome": final_outcome,
        "operator_result_lines": [
            f"Ergebnis: {final_outcome}",
            f"OR-Modell: {delegated_model_label}",
            f"Tatsaechliche OR-Kosten: {actual_cost if actual_cost is not None else 'N/A'}",
        ],
        "result_issues": result_issues,
        "operator_message": (
            "Delegated feature-design path stayed bounded and file-first captured. Codex must still decide the final decision summary or blocking question."
            if validation_result == "PASS" and healthcheck_status == "PASS"
            else "Delegated feature-design path failed bounded capture or validation gates. Fallback to Codex-only feature-design is required."
        ),
        "healthcheck_status": healthcheck_status,
        "healthcheck_summary": healthcheck_summary,
    }
    write_json(run_dir / "consumer_operator_choice_delegated.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded OR review helper for janus-feature-design.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--delegated-model-label", default=DEFAULT_FEATURE_DESIGN_OR_MODEL)
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--use-local-or-fixture", action="store_true")
    parser.add_argument("--or-local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--execute-direct-or", action="store_true")
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=args.workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
            estimated_or_cost=args.estimated_or_cost,
            cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
        )
        write_json(build_run_dir(args.workflow_id) / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = local_summary(
            workflow_id=args.workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
        )
        write_json(build_run_dir(args.workflow_id) / "operator_choice_local.json", result)
        output(result)
        return 0

    if args.input_package_json is None:
        raise SystemExit("--input-package-json is required for delegated feature-design review")
    if args.estimated_or_cost is None or args.cost_estimate_confidence_percent is None:
        raise SystemExit("--estimated-or-cost and --cost-estimate-confidence-percent are required for delegated feature-design review")

    result = run_consumer_flow(
        workflow_id=args.workflow_id,
        task_label=args.task_label,
        normal_target_model=args.normal_target_model,
        delegated_model_label=args.delegated_model_label,
        estimated_or_cost=float(args.estimated_or_cost),
        cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
        input_package_json=args.input_package_json,
        use_local_or_fixture=args.use_local_or_fixture,
        or_local_fixture_response_path=args.or_local_fixture_response_path,
        execute_direct_or=args.execute_direct_or,
    )
    output(result)
    return 0 if result.get("validation_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
