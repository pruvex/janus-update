#!/usr/bin/env python3
"""Bounded OR review helper for janus-backlog-intake."""

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
RUN_ROOT = MODEL_ROUTING_DIR / "backlog-intake-review-runs"
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
DEFAULT_BACKLOG_INTAKE_OR_MODEL = "qwen/qwen3-coder-30b-a3b-instruct"

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
    "raw_user_request",
    "source_type",
    "suspected_type",
    "target_area",
    "evidence_snippets",
    "expected_output",
    "redaction_ready",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "backlog_type",
    "suggested_status",
    "title",
    "kurzbeschreibung",
    "erwartetes_verhalten",
    "tatsaechliches_verhalten",
    "reproduktion_kontext",
    "betroffener_bereich",
    "nachweise",
    "akzeptanzkriterien",
    "fehlende_informationen",
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
    if payload.get("bound_skill_context") != "janus-backlog-intake":
        issues.append("bound_skill_context must be exactly janus-backlog-intake")
    snippets = payload.get("evidence_snippets")
    if not isinstance(snippets, list) or not snippets:
        issues.append("evidence_snippets must be a non-empty list")
    elif len(snippets) > 4:
        issues.append("evidence_snippets must contain at most 4 items")
    if payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")
    return issues


def validate_result_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in payload:
            issues.append(f"missing result field: {field}")
    if payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status must be PASS, WEAK_SIGNAL, or BLOCKED")
    if payload.get("backlog_type") not in {"BUG", "CHANGE", "ENHANCEMENT", "IMPROVEMENT", "TECH_DEBT", "UNCLEAR"}:
        issues.append("backlog_type must be BUG, CHANGE, ENHANCEMENT, IMPROVEMENT, TECH_DEBT, or UNCLEAR")
    if payload.get("suggested_status") not in {"READY", "NEEDS_INFO", "BLOCKED"}:
        issues.append("suggested_status must be READY, NEEDS_INFO, or BLOCKED")
    for list_field, min_items, max_items in (("nachweise", 1, 4), ("akzeptanzkriterien", 1, 4), ("fehlende_informationen", 0, 3)):
        value = payload.get(list_field)
        if not isinstance(value, list):
            issues.append(f"{list_field} must be a list")
            continue
        if len(value) < min_items or len(value) > max_items:
            issues.append(f"{list_field} must contain between {min_items} and {max_items} items")
    return issues


def render_result_markdown(result_payload: dict[str, Any]) -> str:
    lines = [
        "BACKLOG_INTAKE_REVIEW",
        f"Status: {result_payload['status']}",
        f"Backlog Type: {result_payload['backlog_type']}",
        f"Suggested Status: {result_payload['suggested_status']}",
        f"Title: {result_payload['title']}",
        f"Kurzbeschreibung: {result_payload['kurzbeschreibung']}",
        f"Erwartetes Verhalten: {result_payload['erwartetes_verhalten']}",
        f"Tatsaechliches Verhalten: {result_payload['tatsaechliches_verhalten']}",
        f"Reproduktion / Kontext: {result_payload['reproduktion_kontext']}",
        f"Betroffener Bereich: {result_payload['betroffener_bereich']}",
        f"Nachweise: {result_payload['nachweise']}",
        f"Akzeptanzkriterien: {result_payload['akzeptanzkriterien']}",
        f"Fehlende Informationen: {result_payload['fehlende_informationen']}",
        f"Notes: {result_payload['notes']}",
    ]
    return "\n".join(lines) + "\n"


def build_consumer_input_package(
    *,
    workflow_id: str,
    raw_user_request: str,
    source_type: str,
    suspected_type: str,
    target_area: str,
    evidence_snippets: list[str],
    expected_output: str,
    redaction_ready: bool = True,
) -> dict[str, Any]:
    return {
        "workflow_id": workflow_id,
        "bound_skill_context": "janus-backlog-intake",
        "raw_user_request": raw_user_request,
        "source_type": source_type,
        "suspected_type": suspected_type,
        "target_area": target_area,
        "evidence_snippets": evidence_snippets,
        "expected_output": expected_output,
        "redaction_ready": redaction_ready,
    }


def build_request_body(model: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded Janus backlog-intake assistant. "
                    "Use only the redacted input package. "
                    "Return exactly one JSON object and no prose. "
                    "Do not claim prioritization, implementation, routing authority, Git authority, or release authority."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return a JSON object with these exact top-level fields: "
                    "status, backlog_type, suggested_status, title, kurzbeschreibung, erwartetes_verhalten, "
                    "tatsaechliches_verhalten, reproduktion_kontext, betroffener_bereich, nachweise, "
                    "akzeptanzkriterien, fehlende_informationen, notes.\n\n"
                    "Rules:\n"
                    "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
                    "- backlog_type must be BUG, CHANGE, ENHANCEMENT, IMPROVEMENT, TECH_DEBT, or UNCLEAR\n"
                    "- suggested_status must be READY, NEEDS_INFO, or BLOCKED\n"
                    "- akzeptanzkriterien must contain 1 to 4 short checklist-style strings\n"
                    "- fehlende_informationen must contain 0 to 3 short strings\n"
                    "- do not claim prioritization, implementation, or direct execution handoff\n"
                    "- keep the output bounded to one backlog candidate only\n\n"
                    f"Redacted input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 1100,
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
            raise SystemExit("OPENROUTER_API_KEY missing for live backlog-intake OR invocation")
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
        "skill_id": "janus-backlog-intake",
        "routing_mode": "Manual-review",
        "selected_path": "delegated_backlog_intake_review",
        "codex_default_model": normal_target_model,
        "or_model": or_model,
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "estimated_or_cost": estimated_or_cost,
        "cost_estimate_confidence_percent": cost_estimate_confidence_percent,
        "cost_estimate_sample_count": 1,
        "cost_estimate_mean_abs_error_percent": round(estimation_error_percent, 2),
        "cost_estimate_p50_error_percent": round(estimation_error_percent, 2),
        "cost_estimate_p90_error_percent": round(estimation_error_percent, 2),
        "cost_estimate_basis": "backlog_intake_initial_batch",
        "prompt_template_hash": "backlog_intake_review_v1",
        "task_variant": "backlog_intake_review",
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
        "quality_notes": "Bounded backlog-intake review only; Codex remains final backlog editor and owner.",
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
            skill="janus-backlog-intake",
        )
    return {
        "summary_header": "BACKLOG INTAKE REVIEW GATE",
        "workflow_id": workflow_id,
        "skill": "janus-backlog-intake",
        "task_label": task_label,
        "selected_path": "operator_choice_pending",
        "normal_target_model": normal_target_model,
        "selected_or_model": delegated_model_label,
        "estimated_or_cost": float(estimated_or_cost),
        "cost_estimate_confidence_percent": float(cost_estimate_confidence_percent),
        "choice_1": "Codex",
        "choice_2": "OR",
        "delegated_model_label": delegated_model_label,
        "expected_delegation_value": "bounded backlog candidate drafting with no prioritization or implementation authority",
        "operator_prompt_lines": build_operator_prompt_lines(
            choice_2_label="OR",
            selected_or_model=delegated_model_label,
            estimated_or_cost=float(estimated_or_cost),
            cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
        ),
        "boundaries": [
            "No delegated backlog write acceptance",
            "No delegated prioritization",
            "No delegated implementation handoff",
            "Codex remains final backlog editor",
        ],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
    }


def local_summary(*, workflow_id: str, task_label: str, normal_target_model: str, delegated_model_label: str) -> dict[str, Any]:
    return {
        "summary_header": "BACKLOG INTAKE REVIEW RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-backlog-intake",
        "task_label": task_label,
        "selected_path": "codex_only_operator_choice",
        "normal_target_model": normal_target_model,
        "delegated_model_label": delegated_model_label,
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "validation_result": "PASS",
        "operator_message": "Operator chose the local Codex backlog-intake path. No delegated backlog review was used.",
    }


def run_consumer_flow(
    *,
    workflow_id: str,
    task_label: str,
    normal_target_model: str,
    operator_choice: str,
    delegated_model_label: str,
    estimated_or_cost: float | None = None,
    cost_estimate_confidence_percent: float | None = None,
    input_payload: dict[str, Any] | None = None,
    input_package_path: Path | None = None,
    use_local_or_fixture: bool = False,
    execute_direct_or: bool = False,
    or_local_fixture_response_path: Path | None = None,
) -> dict[str, Any]:
    choice = normalize_choice(operator_choice)
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if input_payload is not None:
        package_path = run_dir / "consumer_input_package.json"
        write_json(package_path, input_payload)
        input_package_path = package_path

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=task_label,
            normal_target_model=normal_target_model,
            delegated_model_label=delegated_model_label,
            estimated_or_cost=estimated_or_cost,
            cost_estimate_confidence_percent=cost_estimate_confidence_percent,
        )
        write_json(run_dir / "consumer_operator_choice_prompt.json", result)
        return result
    if choice == "local":
        result = local_summary(
            workflow_id=workflow_id,
            task_label=task_label,
            normal_target_model=normal_target_model,
            delegated_model_label=delegated_model_label,
        )
        write_json(run_dir / "consumer_operator_choice_local.json", result)
        return result

    if input_package_path is None:
        raise SystemExit("delegated backlog-intake review requires an input package")
    if estimated_or_cost is None or cost_estimate_confidence_percent is None:
        raise SystemExit("delegated backlog-intake review requires estimated cost and confidence")

    input_payload = load_json(input_package_path.resolve())
    input_issues = validate_input_package(input_payload)
    write_json(run_dir / "input_package.json", input_payload)
    if input_issues:
        result = {
            "summary_header": "BACKLOG INTAKE REVIEW RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-backlog-intake",
            "task_label": task_label,
            "selected_path": "codex_local_fallback_invalid_input_package",
            "normal_target_model": normal_target_model,
            "delegated_model_label": delegated_model_label,
            "validation_result": "FAIL",
            "final_outcome": "BACKLOG_INTAKE_REVIEW_REJECT_AND_FALLBACK",
            "fallback_used": "YES",
            "rework_required": "YES",
            "input_issues": input_issues,
            "operator_message": "Delegated backlog-intake input package failed bounded validation. Codex keeps the slice local.",
        }
        write_json(run_dir / "consumer_operator_choice_delegated.json", result)
        return result

    request_body = build_request_body(delegated_model_label, input_payload)
    request_path = run_dir / "request_body_source.json"
    write_json(request_path, request_body)

    start = time.time()
    wrapper_result = invoke_file_first_wrapper(
        run_dir=run_dir,
        request_body_path=request_path,
        use_local_fixture=use_local_or_fixture,
        local_fixture_response_path=or_local_fixture_response_path,
        execute_live=execute_direct_or,
        title="Janus Backlog Intake Review",
    )
    latency_ms = int(round((time.time() - start) * 1000))
    write_text(run_dir / "wrapper_stdout.log", wrapper_result.stdout)
    write_text(run_dir / "wrapper_stderr.log", wrapper_result.stderr)
    if wrapper_result.returncode != 0:
        result = {
            "summary_header": "BACKLOG INTAKE REVIEW RESULT",
            "workflow_id": workflow_id,
            "skill": "janus-backlog-intake",
            "task_label": task_label,
            "selected_path": "abort_post_wrapper",
            "normal_target_model": normal_target_model,
            "delegated_model_label": delegated_model_label,
            "validation_result": "FAIL",
            "final_outcome": "BACKLOG_INTAKE_REVIEW_REJECT_AND_FALLBACK",
            "fallback_used": "YES",
            "rework_required": "YES",
            "operator_message": "File-first capture failed before delegated backlog-intake review could be validated.",
        }
        write_json(run_dir / "consumer_operator_choice_delegated.json", result)
        return result

    response_body = load_json(run_dir / "response_body.json")
    response_summary = load_json(run_dir / "response_summary.json")
    delegated_text = content_from_response(response_body)
    parse_issues: list[str] = []
    try:
        extracted_payload = parse_json_from_text(delegated_text)
    except Exception as exc:
        extracted_payload = {}
        parse_issues.append(f"response content parse failed: {exc}")
    write_json(run_dir / "delegated_result_payload.json", extracted_payload if extracted_payload else {"raw_content": delegated_text})

    result_issues = validate_result_payload(extracted_payload) if extracted_payload else []
    delegated_markdown = render_result_markdown(extracted_payload) if extracted_payload and not result_issues else (delegated_text or "NO_DELEGATED_RESULT_CAPTURED\n")
    write_text(run_dir / "delegated_result.md", delegated_markdown)

    telemetry_issues: list[str] = []
    if not response_summary.get("generation_id"):
        telemetry_issues.append("generation_id missing")
    usage = response_summary.get("usage")
    if not isinstance(usage, dict):
        telemetry_issues.append("usage missing")
    if actual_or_cost(response_summary) is None:
        telemetry_issues.append("actual OR cost missing")
    if response_summary.get("finish_reason") == "length":
        telemetry_issues.append("finish_reason=length")

    validation_pass = not parse_issues and not result_issues and not telemetry_issues
    validation_summary = {
        "workflow_id": workflow_id,
        "task_label": task_label,
        "input_validation_pass": not input_issues,
        "result_validation_pass": not result_issues and not parse_issues,
        "telemetry_validation_pass": not telemetry_issues,
        "input_issues": input_issues,
        "result_issues": parse_issues + result_issues,
        "telemetry_issues": telemetry_issues,
        "redaction_ready": input_payload.get("redaction_ready"),
        "accepted_for_local_codex_validation": validation_pass,
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    final_outcome = "BACKLOG_INTAKE_REVIEW_READY_FOR_CODEX_VALIDATION" if validation_pass else "BACKLOG_INTAKE_REVIEW_REJECT_AND_FALLBACK"
    validation_result = "PASS" if validation_pass else "FAIL"
    fallback_used = "NO" if validation_pass else "YES"
    rework_required = "NO" if validation_pass else "YES"

    telemetry_path = MODEL_ROUTING_DIR / (
        f"or_healthcheck_telemetry_backlog_intake_review_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
    )
    telemetry_row = build_telemetry_row(
        workflow_id=workflow_id,
        normal_target_model=normal_target_model,
        or_model=delegated_model_label,
        estimated_or_cost=float(estimated_or_cost),
        cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
        response_summary=response_summary,
        validation_result=validation_result,
        final_outcome=final_outcome,
        fallback_used=fallback_used,
        rework_required=rework_required,
        latency_ms=latency_ms,
    )
    write_single_jsonl_row(telemetry_path, telemetry_row)

    healthcheck_status = "SKIPPED"
    healthcheck_summary_path = ""
    try:
        run_healthcheck(telemetry_path, run_dir)
        healthcheck_status = "PASS"
        healthcheck_summary_path = str(run_dir / "healthcheck_summary.json")
    except Exception as exc:
        validation_result = "FAIL"
        fallback_used = "YES"
        rework_required = "YES"
        final_outcome = "BACKLOG_INTAKE_REVIEW_REJECT_AND_FALLBACK"
        validation_summary["telemetry_issues"].append(str(exc))
        validation_summary["telemetry_validation_pass"] = False
        validation_summary["accepted_for_local_codex_validation"] = False
        write_json(run_dir / "validation_summary.json", validation_summary)
        telemetry_row = build_telemetry_row(
            workflow_id=workflow_id,
            normal_target_model=normal_target_model,
            or_model=delegated_model_label,
            estimated_or_cost=float(estimated_or_cost),
            cost_estimate_confidence_percent=float(cost_estimate_confidence_percent),
            response_summary=response_summary,
            validation_result=validation_result,
            final_outcome=final_outcome,
            fallback_used=fallback_used,
            rework_required=rework_required,
            latency_ms=latency_ms,
        )
        write_single_jsonl_row(telemetry_path, telemetry_row)
        healthcheck_status = "FAIL"

    result = {
        "summary_header": "BACKLOG INTAKE REVIEW RESULT",
        "workflow_id": workflow_id,
        "skill": "janus-backlog-intake",
        "task_label": task_label,
        "selected_path": "delegated_backlog_intake_review" if healthcheck_status == "PASS" else "abort_post_healthcheck",
        "normal_target_model": normal_target_model,
        "selected_or_model": delegated_model_label,
        "estimated_or_cost": float(estimated_or_cost),
        "actual_or_cost": actual_or_cost(response_summary),
        "cost_estimate_confidence_percent": float(cost_estimate_confidence_percent),
        "generation_id": str(response_summary.get("generation_id") or ""),
        "finish_reason": response_summary.get("finish_reason"),
        "latency_ms": latency_ms,
        "validation_result": validation_result,
        "final_outcome": final_outcome,
        "fallback_used": fallback_used,
        "rework_required": rework_required,
        "input_package_path": str(run_dir / "input_package.json"),
        "request_body_path": str(run_dir / "request_body.json"),
        "response_body_path": str(run_dir / "response_body.json"),
        "response_summary_path": str(run_dir / "response_summary.json"),
        "delegated_result_path": str(run_dir / "delegated_result.md"),
        "validation_summary_path": str(run_dir / "validation_summary.json"),
        "telemetry_jsonl_path": str(telemetry_path),
        "healthcheck_status": healthcheck_status,
        "healthcheck_summary_path": healthcheck_summary_path,
        "operator_result_lines": [
            f"Ergebnis: {final_outcome}",
            f"Tatsaechliche Kosten: {(actual_or_cost(response_summary) or 0.0):.9f}",
        ],
        "operator_message": (
            "Delegated backlog-intake review stayed bounded and file-first captured. Codex must still decide the final backlog edit locally."
            if validation_result == "PASS"
            else "Delegated backlog-intake review failed bounded capture or validation gates. Fallback to Codex-only intake is required."
        ),
    }
    write_json(run_dir / "consumer_operator_choice_delegated.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded backlog intake review helper.")
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--delegated-model-label", default=DEFAULT_BACKLOG_INTAKE_OR_MODEL)
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--input-package-json", type=Path, default=None)
    parser.add_argument("--use-local-or-fixture", action="store_true")
    parser.add_argument("--execute-direct-or", action="store_true")
    parser.add_argument("--or-local-fixture-response-path", type=Path, default=None)
    args = parser.parse_args()

    choice = normalize_choice(args.operator_choice)
    workflow_id = args.workflow_id or f"BACKLOG-INTAKE-REVIEW-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_dir = build_run_dir(workflow_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    input_payload = None
    if args.input_package_json is not None:
        input_payload = load_json(args.input_package_json.resolve())
        write_json(run_dir / "input_package.json", input_payload)

    if choice == "prompt":
        result = prompt_summary(
            workflow_id=workflow_id,
            task_label=args.task_label,
            normal_target_model=args.normal_target_model,
            delegated_model_label=args.delegated_model_label,
            estimated_or_cost=args.estimated_or_cost,
            cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
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

    if args.input_package_json is None:
        raise SystemExit("--input-package-json is required for operator-choice delegated")
    result = run_consumer_flow(
        workflow_id=workflow_id,
        task_label=args.task_label,
        normal_target_model=args.normal_target_model,
        operator_choice="delegated",
        delegated_model_label=args.delegated_model_label,
        estimated_or_cost=args.estimated_or_cost,
        cost_estimate_confidence_percent=args.cost_estimate_confidence_percent,
        input_payload=input_payload,
        input_package_path=run_dir / "input_package.json",
        use_local_or_fixture=args.use_local_or_fixture,
        execute_direct_or=args.execute_direct_or,
        or_local_fixture_response_path=args.or_local_fixture_response_path,
    )
    write_json(run_dir / "operator_choice_delegated.json", result)
    output(result)
    return 0 if result.get("validation_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
