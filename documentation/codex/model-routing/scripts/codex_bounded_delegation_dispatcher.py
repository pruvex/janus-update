#!/usr/bin/env python3
"""Dispatcher for bounded Codex/Sidecar/structured delegation flows."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DOC_RUNNER = MODEL_ROUTING_DIR / "scripts" / "doc_skill_sidecar_draft_runner.py"
PATCH_RUNNER = MODEL_ROUTING_DIR / "scripts" / "quickchange_sidecar_write_pilot_runner.py"
DIRECT_OR_QUICKCHANGE_RUNNER = MODEL_ROUTING_DIR / "scripts" / "openrouter_direct_quickchange_patch_runner.py"
QUICKCHANGE_APPLY_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_quickchange_write_apply_runner.py"
GENERATOR_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_generator_review_runner.py"
DEBUG_REVIEW_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_debug_hypothesis_review_runner.py"
TEST_TRIAGE_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_test_result_triage_review_runner.py"
EXECUTION_PATCH_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_execution_patch_candidate_runner.py"
DIRECT_OR_EXECUTION_PATCH_RUNNER = MODEL_ROUTING_DIR / "scripts" / "openrouter_direct_execution_patch_candidate_runner.py"
QWEN_OR_EXECUTION_PATCH_RUNNER = MODEL_ROUTING_DIR / "scripts" / "openrouter_qwen_execution_patch_candidate_runner.py"
EXECUTION_WRITE_APPLY_RUNNER = MODEL_ROUTING_DIR / "scripts" / "codex_execution_write_apply_candidate_runner.py"
RUN_ROOT = MODEL_ROUTING_DIR / "bounded-dispatch-runs"
OR_TELEMETRY_DIR = MODEL_ROUTING_DIR
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
if str(MODEL_ROUTING_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))

import codex_debug_hypothesis_review_runner as debug_review_runner
import codex_test_result_triage_review_runner as triage_review_runner
from bounded_or_worker_eligibility import (
    evaluate_dispatch_task_class,
    evaluate_assistive_or_workhorse_pilot,
    evaluate_existing_skill_operator_gate_visibility,
)
from bounded_or_worker_gate_prompt import (
    build_missing_gate_result,
    build_operator_prompt_lines,
    build_or_roi,
    build_or_roi_gate_result,
    build_visibility_suppressed_result,
    missing_gate_fields,
    should_enforce_or_roi,
)
from bounded_or_worker_outcome import normalize_codex_owned_outcome
from codex_structured_action_request_builder import validate_bounded_review_payload


def normalize_choice(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "prompt":
        return "prompt"
    if normalized in {"local", "codex", "1"}:
        return "local"
    if normalized in {"sidecar", "delegated", "2"}:
        return "delegated"
    raise SystemExit("operator-choice must be one of: prompt, local/1/codex, delegated/2/sidecar")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_single_jsonl_row(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def output(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def with_codex_owned_outcome(payload: dict) -> dict:
    normalized = normalize_codex_owned_outcome(
        selected_path=str(payload.get("selected_path", "")),
        validation_result=str(payload.get("validation_result", "")),
        final_outcome=str(payload.get("final_outcome", "")),
        fallback_used=payload.get("fallback_used"),
        rework_required=payload.get("rework_required"),
    )
    merged = dict(payload)
    merged.update(normalized)
    return merged


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def parse_json_output(text: str, label: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} did not return valid JSON.\n{text}") from exc


def summarize_failure_text(text: str, limit: int = 600) -> str:
    collapsed = " ".join(part.strip() for part in text.splitlines() if part.strip())
    return collapsed[:limit] if collapsed else "No failure details captured."


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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
        message = {}
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


def resolve_selected_or_model(args: argparse.Namespace, eligibility: dict[str, object] | None = None) -> str:
    selected = str(getattr(args, "selected_or_model", "") or "").strip()
    if selected:
        return selected
    if str(getattr(args, "task_class", "") or "").strip() == "documentation_draft":
        return "codex-cli/gpt-5.4-read-only-sidecar"
    if eligibility is not None:
        selected = str(eligibility.get("selected_or_model") or "").strip()
        if selected:
            return selected
    return ""


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
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise SystemExit("OPENROUTER_API_KEY missing for bounded assistive OR live invocation")
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
        raise SystemExit("choose --use-local-or-fixture or --execute-direct-or for bounded assistive OR review")
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
    write_text(run_dir / "healthcheck_command.txt", " ".join(command) + "\n")
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "health_snapshot.py failed")
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise RuntimeError("health_snapshot.py did not return a JSON object")
    write_json(run_dir / "healthcheck_summary.json", parsed)
    return parsed


PILOT_TASK_CLASS_SKILL_MAP = {
    "debug_hypothesis_review": "janus-debug",
    "test_result_triage_review": "janus-test-pipeline",
}

PILOT_VISIBLE_GATE_LABELS = {
    "debug_hypothesis_review": "OR",
    "test_result_triage_review": "OR",
}

PILOT_REQUEST_ALLOWLISTS = {
    "debug_hypothesis_review": {
        "required_fields": [
            "workflow_id",
            "bound_skill_context",
            "expected_behavior",
            "actual_behavior",
            "evidence_snippets",
            "iteration_number",
            "explicit_question",
            "redaction_ready",
        ],
        "optional_fields": ["failure_code"],
        "max_evidence_snippets": 3,
    },
    "test_result_triage_review": {
        "required_fields": [
            "workflow_id",
            "bound_skill_context",
            "test_run_id",
            "result_outcome_summary",
            "evidence_snippets",
            "classification_question",
            "redaction_ready",
        ],
        "optional_fields": ["candidate_blocker_category"],
        "max_evidence_snippets": 3,
    },
}

DEBUG_REVIEW_RESULT_SCHEMA = {
    "name": "janus_debug_hypothesis_review_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": debug_review_runner.REQUIRED_RESULT_FIELDS,
        "properties": {
            "status": {"type": "string", "enum": ["PASS", "WEAK_SIGNAL", "BLOCKED"]},
            "primary_failure_code": {"type": "string"},
            "likely_subsystem": {"type": "string"},
            "hypotheses": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "confidence", "evidence"],
                    "properties": {
                        "title": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                        "evidence": {"type": "string"},
                    },
                },
            },
            "suggested_local_verifiers": {"type": "string"},
            "instrumentation_suggestion": {"type": "string"},
            "escalation_trigger": {"type": "string"},
            "redaction_check": {"type": "string", "enum": ["PASS"]},
            "notes": {"type": "string"},
        },
    },
}

TRIAGE_REVIEW_RESULT_SCHEMA = {
    "name": "janus_test_result_triage_review_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": triage_review_runner.REQUIRED_RESULT_FIELDS,
        "properties": {
            "status": {"type": "string", "enum": ["PASS", "WEAK_SIGNAL", "BLOCKED"]},
            "test_run_id": {"type": "string"},
            "primary_outcome": {"type": "string"},
            "likely_classification": {"type": "string", "enum": sorted(triage_review_runner.SUPPORTED_CLASSIFICATIONS)},
            "likely_subsystem": {"type": "string"},
            "finding_clusters": {
                "type": "array",
                "minItems": 1,
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "confidence", "evidence"],
                    "properties": {
                        "title": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                        "evidence": {"type": "string"},
                    },
                },
            },
            "suggested_next_local_verifiers": {"type": "string"},
            "suggested_routing": {"type": "string"},
            "escalation_trigger": {"type": "string"},
            "redaction_check": {"type": "string", "enum": ["PASS"]},
            "notes": {"type": "string"},
        },
    },
}


def evaluate_assistive_or_workhorse_dispatcher_eligibility(*, task_class: str) -> dict:
    if task_class in PILOT_TASK_CLASS_SKILL_MAP:
        skill_id = PILOT_TASK_CLASS_SKILL_MAP[task_class]
        return evaluate_assistive_or_workhorse_pilot(
            skill_id=skill_id,
            task_class=task_class,
        )
    return evaluate_dispatch_task_class(task_class=task_class)


def validate_assistive_or_workhorse_request(
    *,
    task_class: str,
    input_package_path: Path,
) -> tuple[dict, dict]:
    payload = load_json(input_package_path.resolve())
    allowlist = PILOT_REQUEST_ALLOWLISTS[task_class]
    issues = validate_bounded_review_payload(
        payload,
        required_fields=allowlist["required_fields"],
        optional_fields=allowlist["optional_fields"],
        max_evidence_snippets=allowlist["max_evidence_snippets"],
    )
    eligibility = evaluate_assistive_or_workhorse_pilot(
        skill_id=PILOT_TASK_CLASS_SKILL_MAP[task_class],
        task_class=task_class,
        request_payload=payload,
    )
    if issues and "request_validation_issues" not in eligibility:
        eligibility = dict(eligibility)
        eligibility["request_validation_issues"] = issues
    return payload, eligibility


def build_assistive_or_pilot_reject_result(
    *,
    workflow_id: str,
    task_class: str,
    task_label: str,
    input_payload: dict,
    eligibility: dict,
) -> dict:
    run_dir = RUN_ROOT / workflow_id
    copied_input = run_dir / f"{task_class}_input_package_rejected.json"
    write_json(copied_input, input_payload)
    issues = eligibility.get("request_validation_issues", [])
    result = {
        "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
        "workflow_id": workflow_id,
        "task_class": task_class,
        "task_label": task_label,
        "selected_path": "codex_only_pre_dispatch",
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility.get("evidence_status", "N_A"),
        "validation_result": "PASS",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "input_package_path": str(copied_input),
        "operator_result_lines": [
            f"Ergebnis: {eligibility['eligibility_result']}",
            "Route: Codex-only bis das Request-Paket auf die Pilot-Allowlist reduziert ist",
        ],
        "operator_message": eligibility["message"],
        "request_validation_issues": issues,
    }
    return result


def build_assistive_review_request_body(*, task_class: str, model: str, input_payload: dict[str, object]) -> dict[str, object]:
    if task_class == "debug_hypothesis_review":
        schema = DEBUG_REVIEW_RESULT_SCHEMA
        system = (
            "You are a bounded OpenRouter worker for a Janus debug hypothesis review. "
            "Return only JSON matching the schema. Do not claim a fix, do not run commands, and do not claim validation authority. "
            "Codex remains local validation and acceptance owner."
        )
        user_payload = {
            "task_class": task_class,
            "workflow_id": input_payload.get("workflow_id"),
            "bound_skill_context": input_payload.get("bound_skill_context"),
            "expected_behavior": input_payload.get("expected_behavior"),
            "actual_behavior": input_payload.get("actual_behavior"),
            "evidence_snippets": input_payload.get("evidence_snippets"),
            "iteration_number": input_payload.get("iteration_number"),
            "explicit_question": input_payload.get("explicit_question"),
            "constraints": [
                "At most 3 hypotheses",
                "No command execution",
                "No final fix claim",
                "redaction_check must be PASS",
            ],
        }
    else:
        schema = TRIAGE_REVIEW_RESULT_SCHEMA
        system = (
            "You are a bounded OpenRouter worker for a Janus test-result triage review. "
            "Return only JSON matching the schema. Do not run tests, do not claim release readiness, and do not claim final PASS authority. "
            "Codex remains local validation and routing owner."
        )
        user_payload = {
            "task_class": task_class,
            "workflow_id": input_payload.get("workflow_id"),
            "bound_skill_context": input_payload.get("bound_skill_context"),
            "test_run_id": input_payload.get("test_run_id"),
            "result_outcome_summary": input_payload.get("result_outcome_summary"),
            "evidence_snippets": input_payload.get("evidence_snippets"),
            "classification_question": input_payload.get("classification_question"),
            "constraints": [
                "At most 2 finding clusters",
                "No live test execution",
                "No final PASS decision",
                "redaction_check must be PASS",
            ],
        }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
        ],
        "temperature": 0.0,
        "max_tokens": 1600,
        "response_format": {
            "type": "json_schema",
            "json_schema": schema,
        },
    }


def build_assistive_review_telemetry_row(
    *,
    task_class: str,
    workflow_id: str,
    selected_path: str,
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
    usage = response_summary.get("usage")
    usage_dict = usage if isinstance(usage, dict) else {}
    actual_cost = actual_or_cost(response_summary)
    estimated = float(estimated_or_cost)
    error_percent = ((actual_cost - estimated) / estimated * 100.0) if actual_cost is not None and estimated else 0.0
    return {
        "workflow_id": workflow_id,
        "skill_id": task_class,
        "routing_mode": "assistive_or_workhorse_bounded_review",
        "selected_path": selected_path,
        "codex_default_model": normal_target_model,
        "or_model": or_model,
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "estimated_or_cost": estimated,
        "cost_estimate_confidence_percent": float(cost_estimate_confidence_percent),
        "cost_estimate_sample_count": 0,
        "cost_estimate_mean_abs_error_percent": 0.0,
        "cost_estimate_p50_error_percent": 0.0,
        "cost_estimate_p90_error_percent": 0.0,
        "cost_estimate_basis": "bounded_assistive_review_dispatcher",
        "prompt_template_hash": f"{task_class}_direct_or_v1",
        "task_variant": task_class,
        "price_snapshot_source": "dispatcher_runtime",
        "price_snapshot_timestamp": datetime.now().isoformat(timespec="seconds"),
        "actual_prompt_tokens": int(usage_dict.get("prompt_tokens", 0)),
        "actual_completion_tokens": int(usage_dict.get("completion_tokens", 0)),
        "actual_reasoning_tokens": int((usage_dict.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))
        if isinstance(usage_dict.get("completion_tokens_details"), dict)
        else 0,
        "actual_cached_tokens": int((usage_dict.get("prompt_tokens_details") or {}).get("cached_tokens", 0))
        if isinstance(usage_dict.get("prompt_tokens_details"), dict)
        else 0,
        "actual_or_cost": actual_cost if actual_cost is not None else 0.0,
        "generation_id": str(response_summary.get("generation_id") or ""),
        "usage_source": "response_usage" if usage_dict else "fallback_estimate",
        "estimated_codex_effort": "medium",
        "estimation_error_percent": round(error_percent, 2),
        "cost_delta_vs_codex_estimate": round((actual_cost or 0.0) - estimated, 8),
        "latency_ms": latency_ms,
        "validation_result": validation_result,
        "fallback_used": fallback_used,
        "rework_required": rework_required,
        "final_outcome": final_outcome,
        "reason_for_escalation": "",
        "quality_notes": "Bounded assist-only OR review; Codex remains local validation and acceptance owner.",
        "recommendation_signal": "OR_PREFERRED" if validation_result == "PASS" else "CODEX_PREFERRED",
    }


def invoke_assistive_or_review_via_wrapper(args: argparse.Namespace, workflow_id: str, task_class: str) -> dict:
    input_arg = args.debug_input_package if task_class == "debug_hypothesis_review" else args.test_triage_input_package
    if input_arg is None:
        raise SystemExit(f"{task_class} delegated flow requires an input package")
    if not args.selected_or_model:
        raise SystemExit(f"{task_class} direct OR flow requires --selected-or-model")
    if args.estimated_or_cost is None or args.cost_estimate_confidence_percent is None:
        raise SystemExit(f"{task_class} direct OR flow requires estimated cost and confidence")

    input_payload, pilot_eligibility = validate_assistive_or_workhorse_request(
        task_class=task_class,
        input_package_path=input_arg,
    )
    if pilot_eligibility["eligibility_result"] != "OR_ALLOWED":
        return build_assistive_or_pilot_reject_result(
            workflow_id=workflow_id,
            task_class=task_class,
            task_label=args.task_label,
            input_payload=input_payload,
            eligibility=pilot_eligibility,
        )

    run_dir = RUN_ROOT / workflow_id
    telemetry_path = OR_TELEMETRY_DIR / (
        f"or_healthcheck_telemetry_assistive_or_review_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
    )
    delegated_selected_path = (
        "delegated_assist_only_hypothesis_review"
        if task_class == "debug_hypothesis_review"
        else "delegated_assist_only_test_result_triage_review"
    )
    request_body = build_assistive_review_request_body(
        task_class=task_class,
        model=args.selected_or_model,
        input_payload=input_payload,
    )
    request_path = run_dir / "request_body_source.json"
    write_json(request_path, request_body)
    write_json(run_dir / "input_package.json", input_payload)

    start = time.time()
    wrapper_result = invoke_file_first_wrapper(
        run_dir=run_dir,
        request_body_path=request_path,
        use_local_fixture=args.use_local_or_fixture,
        local_fixture_response_path=args.or_local_fixture_response_path,
        execute_live=args.execute_direct_or,
        title=f"Janus Bounded Assistive OR Review ({task_class})",
    )
    latency_ms = int(round((time.time() - start) * 1000))
    write_text(run_dir / "wrapper_command_stdout.log", wrapper_result.stdout)
    write_text(run_dir / "wrapper_command_stderr.log", wrapper_result.stderr)
    if wrapper_result.returncode != 0:
        validation_summary = {
            "workflow_id": workflow_id,
            "task_class": task_class,
            "input_validation_pass": True,
            "result_validation_pass": False,
            "telemetry_validation_pass": False,
            "input_issues": [],
            "result_issues": ["wrapper capture failed before delegated response validation"],
            "telemetry_issues": ["wrapper invocation failed"],
            "redaction_ready": input_payload.get("redaction_ready"),
            "redaction_check": None,
            "accepted_for_local_codex_validation": False,
        }
        write_json(run_dir / "validation_summary.json", validation_summary)
        write_single_jsonl_row(
            telemetry_path,
            build_assistive_review_telemetry_row(
                task_class=task_class,
                workflow_id=workflow_id,
                selected_path="abort_post_wrapper",
                normal_target_model=args.normal_target_model,
                or_model=args.selected_or_model,
                estimated_or_cost=float(args.estimated_or_cost),
                cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
                response_summary={},
                validation_result="FAIL",
                final_outcome=(
                    "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK"
                    if task_class == "debug_hypothesis_review"
                    else "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK"
                ),
                fallback_used="YES",
                rework_required="YES",
                latency_ms=latency_ms,
            ),
        )
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": task_class,
            "task_label": args.task_label,
            "selected_path": "abort_post_wrapper",
            "normal_target_model": args.normal_target_model,
            "selected_or_model": args.selected_or_model,
            "estimated_or_cost": float(args.estimated_or_cost),
            "cost_estimate_confidence_percent": float(args.cost_estimate_confidence_percent),
            "validation_result": "FAIL",
            "final_outcome": (
                "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK"
                if task_class == "debug_hypothesis_review"
                else "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK"
            ),
            "fallback_used": "YES",
            "rework_required": "YES",
            "validation_summary_path": str(run_dir / "validation_summary.json"),
            "telemetry_jsonl_path": str(telemetry_path),
            "healthcheck_status": "SKIPPED",
            "operator_message": "File-first capture failed before a bounded review result could be validated. Fallback to Codex-only is required.",
        }

    response_body = load_json(run_dir / "response_body.json")
    response_summary = load_json(run_dir / "response_summary.json")
    delegated_text = content_from_response(response_body)
    parse_issues: list[str] = []
    try:
        extracted_payload = parse_json_from_text(delegated_text)
    except Exception as exc:
        extracted_payload = {}
        parse_issues.append(f"response content parse failed: {exc}")
    extracted_payload_path = run_dir / "delegated_result_payload.json"
    write_json(extracted_payload_path, extracted_payload if extracted_payload else {"raw_content": delegated_text})

    validator_module = debug_review_runner if task_class == "debug_hypothesis_review" else triage_review_runner
    result_issues = validator_module.validate_result_payload(extracted_payload) if extracted_payload else []
    delegated_markdown = validator_module.render_result_markdown(extracted_payload) if extracted_payload and not result_issues else (
        delegated_text if delegated_text else "NO_DELEGATED_RESULT_CAPTURED\n"
    )
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
        "task_class": task_class,
        "input_validation_pass": True,
        "result_validation_pass": not result_issues and not parse_issues,
        "telemetry_validation_pass": not telemetry_issues,
        "input_issues": [],
        "result_issues": parse_issues + result_issues,
        "telemetry_issues": telemetry_issues,
        "redaction_ready": input_payload.get("redaction_ready"),
        "redaction_check": extracted_payload.get("redaction_check") if isinstance(extracted_payload, dict) else None,
        "accepted_for_local_codex_validation": validation_pass and extracted_payload.get("status") == "PASS",
    }
    write_json(run_dir / "validation_summary.json", validation_summary)

    final_outcome = (
        "DEBUG_HYPOTHESIS_REVIEW_READY_FOR_CODEX_VALIDATION"
        if task_class == "debug_hypothesis_review"
        else "TEST_RESULT_TRIAGE_REVIEW_READY_FOR_CODEX_VALIDATION"
    )
    if not validation_pass:
        final_outcome = (
            "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK"
            if task_class == "debug_hypothesis_review"
            else "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK"
        )
    validation_result = "PASS" if validation_pass else "FAIL"
    fallback_used = "NO" if validation_pass else "YES"
    rework_required = "NO" if validation_pass else "YES"

    telemetry_row = build_assistive_review_telemetry_row(
        task_class=task_class,
        workflow_id=workflow_id,
        selected_path=delegated_selected_path,
        normal_target_model=args.normal_target_model,
        or_model=args.selected_or_model,
        estimated_or_cost=float(args.estimated_or_cost),
        cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
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
        final_outcome = (
            "DEBUG_HYPOTHESIS_REVIEW_REJECT_AND_FALLBACK"
            if task_class == "debug_hypothesis_review"
            else "TEST_RESULT_TRIAGE_REVIEW_REJECT_AND_FALLBACK"
        )
        validation_summary["telemetry_issues"].append(str(exc))
        validation_summary["telemetry_validation_pass"] = False
        validation_summary["accepted_for_local_codex_validation"] = False
        write_json(run_dir / "validation_summary.json", validation_summary)
        healthcheck_status = "FAIL"
    finalized_telemetry_row = build_assistive_review_telemetry_row(
        task_class=task_class,
        workflow_id=workflow_id,
        selected_path=delegated_selected_path if healthcheck_status == "PASS" else "abort_post_healthcheck",
        normal_target_model=args.normal_target_model,
        or_model=args.selected_or_model,
        estimated_or_cost=float(args.estimated_or_cost),
        cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
        response_summary=response_summary,
        validation_result=validation_result,
        final_outcome=final_outcome,
        fallback_used=fallback_used,
        rework_required=rework_required,
        latency_ms=latency_ms,
    )
    write_single_jsonl_row(telemetry_path, finalized_telemetry_row)

    operator_message = (
        "Delegated debug hypothesis review stayed bounded and file-first captured. Codex must still validate the hypotheses locally."
        if task_class == "debug_hypothesis_review" and validation_result == "PASS"
        else "Delegated debug hypothesis review failed bounded capture or validation gates. Fallback to Codex-only debug is required."
        if task_class == "debug_hypothesis_review"
        else "Delegated test-result triage review stayed bounded and file-first captured. Codex must still validate the classification locally."
        if validation_result == "PASS"
        else "Delegated test-result triage review failed bounded capture or validation gates. Fallback to Codex-only triage is required."
    )
    operator_result_lines = [
        f"Ergebnis: {final_outcome}",
        f"Tatsaechliche Kosten: {(actual_or_cost(response_summary) or 0.0):.9f}",
    ]
    return {
        "summary_header": (
            "DEBUG HYPOTHESIS REVIEW RESULT"
            if task_class == "debug_hypothesis_review"
            else "TEST RESULT TRIAGE REVIEW RESULT"
        ),
        "workflow_id": workflow_id,
        "skill": "janus-debug" if task_class == "debug_hypothesis_review" else "janus-test-pipeline",
        "task_label": args.task_label,
        "selected_path": (
            delegated_selected_path if healthcheck_status == "PASS" else "abort_post_healthcheck"
        ),
        "normal_target_model": args.normal_target_model,
        "selected_or_model": args.selected_or_model,
        "estimated_or_cost": float(args.estimated_or_cost),
        "actual_or_cost": actual_or_cost(response_summary),
        "cost_estimate_confidence_percent": float(args.cost_estimate_confidence_percent),
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
        "operator_result_lines": operator_result_lines,
        "operator_message": operator_message,
    }


def validate_write_candidate_entry(payload: dict, expected_target_task: str) -> list[str]:
    required_fields = [
        "workflow_id",
        "bound_skill_context",
        "target_task",
        "spec_path",
        "precheck_status",
        "allowed_files",
        "max_touched_files",
        "manual_validation_gate",
        "delegation_question",
    ]
    issues: list[str] = []
    for field in required_fields:
        if field not in payload:
            issues.append(f"missing input field: {field}")

    target_task = payload.get("target_task")
    if not isinstance(target_task, str) or not target_task.strip():
        issues.append("target_task must be a non-empty string")
    elif target_task != expected_target_task:
        issues.append(f"target_task must exactly match expected target task: {expected_target_task}")

    if payload.get("precheck_status") != "PRE-CHECK PASSED":
        issues.append("precheck_status must be exactly PRE-CHECK PASSED")

    allowed_files = payload.get("allowed_files")
    if not isinstance(allowed_files, list) or not allowed_files:
        issues.append("allowed_files must be a non-empty list")
    elif any(not isinstance(item, str) or not item.strip() for item in allowed_files):
        issues.append("allowed_files entries must be non-empty strings")

    max_touched_files = payload.get("max_touched_files")
    if not isinstance(max_touched_files, int) or max_touched_files < 1:
        issues.append("max_touched_files must be an integer >= 1")

    if not str(payload.get("manual_validation_gate", "")).strip():
        issues.append("manual_validation_gate must be present")
    if not str(payload.get("delegation_question", "")).strip():
        issues.append("delegation_question must be present")

    for flag in ("delete_intent", "rename_intent", "move_intent"):
        if payload.get(flag) is True:
            issues.append(f"{flag} is not allowed in write-candidate entry")
    for field in ("deleted_files", "renamed_files", "moved_files"):
        value = payload.get(field)
        if isinstance(value, list) and value:
            issues.append(f"{field} must be empty for write-candidate entry")

    requested_operations = payload.get("requested_operations")
    if isinstance(requested_operations, list):
        forbidden = [item for item in requested_operations if str(item).strip().lower() in {"delete", "rename", "move"}]
        if forbidden:
            issues.append(f"requested_operations contains forbidden entries: {', '.join(forbidden)}")

    return issues


def build_write_candidate_validator_manifest(payload: dict) -> dict:
    return {
        "validator_id": "validate_write_candidate_entry_v1",
        "inputs": {
            "target_task": payload["target_task"],
            "precheck_status": payload["precheck_status"],
            "allowed_files": [str(item).replace("\\", "/") for item in payload["allowed_files"]],
            "max_touched_files": payload["max_touched_files"],
            "forbid_delete_rename_move": True,
            "manual_validation_gate": payload["manual_validation_gate"],
            "delegation_question": payload["delegation_question"],
        },
    }


def invoke_write_candidate_entry_gate(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.execution_input_package is None:
        raise SystemExit("execution_write_apply_candidate entry gate requires --execution-input-package")

    input_payload = load_json(args.execution_input_package.resolve())
    expected_target_task = args.execution_expected_target_task or args.task_label
    run_dir = RUN_ROOT / workflow_id
    input_copy_path = run_dir / "write_candidate_entry_input.json"
    validation_path = run_dir / "write_candidate_entry_validation.json"
    manifest_path = run_dir / "write_candidate_entry_validator_manifest.json"
    request_path = run_dir / "write_candidate_entry_request.json"

    write_json(input_copy_path, input_payload)
    issues = validate_write_candidate_entry(input_payload, expected_target_task)
    validation_payload = {
        "workflow_id": workflow_id,
        "mode": "execution_write_apply_candidate_entry_gate",
        "expected_target_task": expected_target_task,
        "validation_pass": not issues,
        "issues": issues,
        "delete_rename_move_tripwire": "PASS" if not any("forbidden" in issue or "must be empty" in issue or "_intent" in issue for issue in issues) else "FAIL",
    }
    write_json(validation_path, validation_payload)

    if issues:
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": args.task_class,
            "task_label": args.task_label,
            "selected_path": "delegated_execution_write_apply_candidate_entry_gate",
            "validation_result": "FAIL",
            "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
            "input_package_path": str(input_copy_path),
            "validation_summary_path": str(validation_path),
            "reject_reasons": issues,
            "operator_result_lines": [
                "Ergebnis: Delegated write-candidate Entry abgelehnt",
                "Route: Fallback auf Codex-only vor spaeteren Write-Phasen",
            ],
            "operator_message": (
                "The delegated write-candidate entry failed bounded contract validation. "
                "Codex must keep execution local until a corrected prechecked entry package exists."
            ),
        }

    manifest_payload = build_write_candidate_validator_manifest(input_payload)
    write_json(manifest_path, manifest_payload)
    builder_command = [
        "python",
        str(MODEL_ROUTING_DIR / "scripts" / "codex_structured_action_request_builder.py"),
        "--workflow-id",
        f"{workflow_id}-ENTRY",
        "--skill-id",
        "janus-executioner",
        "--action-type",
        "run_validator",
        "--summary",
        "Capture the bounded execution write-candidate entry contract for later Codex-owned review.",
        "--source-path",
        str(manifest_path),
        "--output-request-json",
        str(request_path),
        "--non-goal",
        "No delegated write apply",
        "--non-goal",
        "No diff capture in entry gate slice",
        "--non-goal",
        "No task completion claim",
    ]
    builder_result = run_command(builder_command)
    write_text(run_dir / "write_candidate_entry_builder_stdout.txt", builder_result.stdout)
    write_text(run_dir / "write_candidate_entry_builder_stderr.txt", builder_result.stderr)
    if builder_result.returncode != 0:
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": args.task_class,
            "task_label": args.task_label,
            "selected_path": "delegated_execution_write_apply_candidate_entry_gate",
            "validation_result": "FAIL",
            "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_REJECT_AND_FALLBACK",
            "input_package_path": str(input_copy_path),
            "validation_summary_path": str(validation_path),
            "validator_manifest_path": str(manifest_path),
            "builder_stdout_path": str(run_dir / "write_candidate_entry_builder_stdout.txt"),
            "builder_stderr_path": str(run_dir / "write_candidate_entry_builder_stderr.txt"),
            "operator_result_lines": [
                "Ergebnis: Review-Artefakt fuer Entry-Gate konnte nicht gebaut werden",
                "Route: Fallback auf Codex-only",
            ],
            "operator_message": "Entry contract validation passed, but the reviewable request artifact could not be built.",
        }

    return {
        "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
        "workflow_id": workflow_id,
        "task_class": args.task_class,
        "task_label": args.task_label,
        "selected_path": "delegated_execution_write_apply_candidate_entry_gate",
        "validation_result": "PASS",
        "final_outcome": "EXECUTION_WRITE_APPLY_CANDIDATE_ENTRY_ACCEPTED_FOR_LATER_PHASES",
        "input_package_path": str(input_copy_path),
        "validation_summary_path": str(validation_path),
        "validator_manifest_path": str(manifest_path),
        "structured_request_path": str(request_path),
        "operator_result_lines": [
            "Ergebnis: Delegated write-candidate Entry zugelassen",
            "Route: Nur Entry-Gate bestanden, spaetere Write-Phasen bleiben separat",
        ],
        "operator_message": (
            "The delegated write-candidate entry contract passed bounded validation and was captured as a reviewable artifact. "
            "Later diff, validation-summary, and Codex-owned acceptance phases remain separate."
        ),
    }


def prompt_summary(args: argparse.Namespace, workflow_id: str) -> dict:
    eligibility = evaluate_assistive_or_workhorse_dispatcher_eligibility(task_class=args.task_class)
    resolved_selected_or_model = resolve_selected_or_model(args, eligibility)
    if eligibility["eligibility_result"] != "OR_ALLOWED":
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": args.task_class,
            "task_label": args.task_label,
            "selected_path": "codex_only_pre_dispatch",
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility["evidence_status"],
            "validation_result": "PASS",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_result_lines": [
                f"Ergebnis: {eligibility['eligibility_result']}",
                f"Route: {args.task_class} bleibt lokal",
            ],
            "operator_message": eligibility["message"],
        }
    visibility = evaluate_existing_skill_operator_gate_visibility(
        subject_type="dispatcher_task_class",
        subject_id=args.task_class,
    )
    if visibility["operator_gate_visibility"] != "VISIBLE":
        return {
            **build_visibility_suppressed_result(
                workflow_id=workflow_id,
                task_label=args.task_label,
                selected_path="codex_only_visibility_hidden",
                final_outcome="LOCAL_CODEX_PATH_SELECTED",
                normal_target_model=args.normal_target_model,
                visibility_status=visibility["visibility_status"],
                suppression_reason=visibility["reason_code"],
                selected_or_model=resolved_selected_or_model or None,
                task_class=args.task_class,
                evidence_status=eligibility["evidence_status"],
            ),
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility["evidence_status"],
        }
    missing_fields = missing_gate_fields(
        selected_or_model=resolved_selected_or_model or None,
        estimated_or_cost=getattr(args, "estimated_or_cost", None),
        cost_estimate_confidence_percent=getattr(args, "cost_estimate_confidence_percent", None),
    )
    if missing_fields:
        return build_missing_gate_result(
            workflow_id=workflow_id,
            task_label=args.task_label,
            selected_path="codex_only_prompt_data_missing",
            missing_fields=missing_fields,
            final_outcome="LOCAL_CODEX_PATH_SELECTED",
            normal_target_model=args.normal_target_model,
            task_class=args.task_class,
            eligibility_result=eligibility["eligibility_result"],
            eligibility_reason_code=eligibility["reason_code"],
            evidence_status=eligibility["evidence_status"],
        )
    roi = build_or_roi(
        estimated_codex_saved_tokens=getattr(args, "estimated_codex_saved_tokens", None),
        estimated_codex_or_overhead_tokens=getattr(args, "estimated_codex_or_overhead_tokens", None),
        minimum_net_codex_saved_tokens=getattr(args, "minimum_net_codex_saved_tokens", 0),
    )
    if should_enforce_or_roi(
        estimated_codex_saved_tokens=getattr(args, "estimated_codex_saved_tokens", None),
        estimated_codex_or_overhead_tokens=getattr(args, "estimated_codex_or_overhead_tokens", None),
        require_positive_or_roi=bool(getattr(args, "require_positive_or_roi", False)),
    ) and roi["status"] != "POSITIVE":
        return build_or_roi_gate_result(
            workflow_id=workflow_id,
            task_label=args.task_label,
            selected_path="codex_only_or_roi_gate",
            normal_target_model=args.normal_target_model,
            task_class=args.task_class,
            eligibility_result=eligibility["eligibility_result"],
            eligibility_reason_code=eligibility["reason_code"],
            evidence_status=eligibility["evidence_status"],
            roi=roi,
        )
    route_notes = {
        "documentation_draft": "Uses the bounded external read-only documentation draft helper.",
        "quickchange_patch_review": "Uses the bounded quickchange patch-review helper and optional structured patch capture.",
        "quickchange_write_apply": "Uses the bounded quickchange write-apply helper backed by accepted workspace-write evidence.",
        "generator_review": "Uses the local structured generator-review helper with deterministic executor validation.",
        "debug_hypothesis_review": "Uses the bounded assist-only debug hypothesis review helper with redaction and Codex-owned validation.",
        "test_result_triage_review": "Uses the bounded assist-only test-result triage review helper with redaction and Codex-owned validation.",
        "execution_patch_candidate": "Uses the bounded execution patch-candidate helper with precheck binding, file-cluster allowlist, and Codex-owned apply/reject authority.",
        "execution_write_apply_candidate": "Uses the bounded execution write-apply candidate helper backed by an accepted proposal-first execution package and Codex-owned future live-write approval.",
    }
    delegated_meaning = {
        "documentation_draft": "External read-only draft helper, then Codex review and binding local writes.",
        "quickchange_patch_review": "OpenRouter patch proposal flow, still bounded and review-first.",
        "quickchange_write_apply": "OpenRouter bounded workspace-write quickchange, but Codex still owns diff validation and final acceptance.",
        "generator_review": "Delegated intent, but local deterministic builder/executor path instead of sidecar write execution.",
        "debug_hypothesis_review": "Delegated assist-only hypothesis review, but Codex still owns reproduction, validation, and next debug action.",
        "test_result_triage_review": "Delegated assist-only triage review, but Codex still owns final classification, rerun, and routing decisions.",
        "execution_patch_candidate": "Delegated proposal-only execution patch candidate, but Codex still owns patch review, apply/reject, and final task completion.",
        "execution_write_apply_candidate": "Delegated bounded execution write candidate, but Codex still owns future live-write approval, diff review, validation review, and final task completion.",
    }
    choice_2_label = PILOT_VISIBLE_GATE_LABELS.get(args.task_class, "OR")
    operator_prompt_lines = build_operator_prompt_lines(
        choice_2_label=choice_2_label,
        selected_or_model=resolved_selected_or_model,
        estimated_or_cost=float(args.estimated_or_cost),
        cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
    )
    if roi["status"] in {"POSITIVE", "NEGATIVE"}:
        operator_prompt_lines.append(
            "OR ROI Gate: "
            f"{roi['status']} (geschaetzte Codex-Ersparnis {roi['estimated_codex_saved_tokens']} Tokens, "
            f"OR-Overhead {roi['estimated_codex_or_overhead_tokens']} Tokens, "
            f"netto {roi['net_codex_saved_tokens']} Tokens)"
        )

    return {
        "summary_header": "BOUNDED DELEGATION DISPATCH GATE",
        "workflow_id": workflow_id,
        "task_class": args.task_class,
        "task_label": args.task_label,
        "operator_gate_visibility": visibility["operator_gate_visibility"],
        "visibility_status": visibility["visibility_status"],
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility["evidence_status"],
        "normal_target_model": args.normal_target_model,
        "selected_or_model": resolved_selected_or_model,
        "estimated_or_cost": float(args.estimated_or_cost),
        "cost_estimate_confidence_percent": float(args.cost_estimate_confidence_percent),
        "or_roi": roi,
        "choice_1": "Codex",
        "choice_2": choice_2_label,
        "delegated_meaning": delegated_meaning[args.task_class],
        "route_note": route_notes[args.task_class],
        "final_outcome": "AWAITING_OPERATOR_CHOICE",
        "validation_result": "PASS",
        "operator_prompt_lines": operator_prompt_lines,
        "boundaries": [
            "No production routing",
            "No canonical routing-table update",
            "No Git/release authority by delegated path",
            "Codex App remains final reviewer",
        ],
    }


def local_summary(args: argparse.Namespace, workflow_id: str) -> dict:
    eligibility = evaluate_assistive_or_workhorse_dispatcher_eligibility(task_class=args.task_class)
    return {
        "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
        "workflow_id": workflow_id,
        "task_class": args.task_class,
        "task_label": args.task_label,
        "selected_path": "codex_only_operator_choice",
        "selected_or_model": resolve_selected_or_model(args, eligibility),
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility["evidence_status"],
        "validation_result": "PASS",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "operator_result_lines": [
            "Ergebnis: Codex lokal ausgewaehlt",
            f"Route: {args.task_class} bleibt lokal",
        ],
        "operator_message": "Operator chose the normal Codex-only path. No delegated helper was invoked.",
    }


def invoke_documentation_draft(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.prompt_path is None:
        raise SystemExit("documentation_draft delegated flow requires --prompt-path")
    command = [
        "python",
        str(DOC_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "sidecar",
        "--prompt-path",
        str(args.prompt_path.resolve()),
        "--workflow-id",
        workflow_id,
    ]
    if args.structured_review_flow:
        command.append("--structured-review-flow")
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"documentation_draft flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "documentation_draft flow")


def invoke_quickchange_patch_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.prompt_path is None:
        raise SystemExit("quickchange_patch_review delegated flow requires --prompt-path")
    if not args.editable_path:
        raise SystemExit("quickchange_patch_review delegated flow requires at least one --editable-path")
    selected_model = str(getattr(args, "selected_or_model", "") or "").strip() or "gpt-5.4"
    if "/" in selected_model:
        command = [
            "python",
            str(DIRECT_OR_QUICKCHANGE_RUNNER),
            "--task-label",
            args.task_label,
            "--normal-target-model",
            args.normal_target_model,
            "--model",
            selected_model,
            "--task-class",
            args.task_class,
            "--prompt-path",
            str(args.prompt_path.resolve()),
            "--workflow-id",
            workflow_id,
            "--max-touched-files",
            str(args.max_touched_files),
            "--estimated-or-cost",
            str(args.estimated_or_cost),
            "--cost-estimate-confidence-percent",
            str(args.cost_estimate_confidence_percent),
            "--estimated-prompt-tokens",
            str(args.estimated_prompt_tokens),
            "--estimated-completion-tokens",
            str(args.estimated_completion_tokens),
            "--cost-estimate-sample-count",
            str(args.cost_estimate_sample_count),
            "--cost-estimate-mean-abs-error-percent",
            str(args.cost_estimate_mean_abs_error_percent),
            "--cost-estimate-p50-error-percent",
            str(args.cost_estimate_p50_error_percent),
            "--cost-estimate-p90-error-percent",
            str(args.cost_estimate_p90_error_percent),
            "--cost-estimate-basis",
            args.cost_estimate_basis,
            "--prompt-template-hash",
            args.prompt_template_hash,
            "--task-variant",
            args.task_variant,
            "--price-snapshot-source",
            args.price_snapshot_source,
            "--price-snapshot-timestamp",
            args.price_snapshot_timestamp,
        ]
        for item in args.editable_path:
            command.extend(["--editable-path", item])
        if args.use_local_or_fixture:
            command.append("--use-local-fixture")
            if args.or_local_fixture_response_path:
                command.extend(["--local-fixture-response-path", str(args.or_local_fixture_response_path.resolve())])
        if args.execute_direct_or:
            command.append("--execute-live")
        completed = run_command(command)
        if completed.returncode != 0:
            raise SystemExit(f"quickchange_patch_review direct OR flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
        return parse_json_output(completed.stdout, "quickchange_patch_review direct OR flow")
    command = [
        "python",
        str(PATCH_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "sidecar",
        "--prompt-path",
        str(args.prompt_path.resolve()),
        "--workflow-id",
        workflow_id,
        "--max-touched-files",
        str(args.max_touched_files),
        "--sidecar-model",
        selected_model,
        "--execute-live",
    ]
    for item in args.editable_path:
        command.extend(["--editable-path", item])
    if args.structured_review_flow:
        command.append("--structured-review-flow")
    if args.structured_review_source_run_dir:
        command.extend(["--structured-review-source-run-dir", str(args.structured_review_source_run_dir.resolve())])
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"quickchange_patch_review flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "quickchange_patch_review flow")


def invoke_quickchange_write_apply(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.accepted_source_run_dir is None:
        raise SystemExit("quickchange_write_apply delegated flow requires --accepted-source-run-dir")
    command = [
        "python",
        str(QUICKCHANGE_APPLY_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--accepted-source-run-dir",
        str(args.accepted_source_run_dir.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"quickchange_write_apply flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "quickchange_write_apply flow")


def invoke_generator_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.generator_manifest is None:
        raise SystemExit("generator_review delegated flow requires --generator-manifest")
    command = [
        "python",
        str(GENERATOR_RUNNER),
        "--workflow-id",
        workflow_id,
        "--skill-id",
        args.generator_skill_id,
        "--generator-manifest",
        str(args.generator_manifest.resolve()),
        "--summary",
        args.generator_summary or f"Run bounded generator-backed structured action review flow for {args.task_label}.",
        "--non-goal",
        "No prompt-level shell delegation",
        "--non-goal",
        "No production routing activation",
        "--validate-generated-output",
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        return {
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": "generator_review",
            "task_label": args.task_label,
            "selected_path": "codex_local_fallback_after_structured_executor_failure",
            "validation_result": "FAIL",
            "final_outcome": "CODEX_LOCAL_FALLBACK_REQUIRED",
            "operator_result_lines": [
                "Ergebnis: Lokaler Fallback aktiviert",
                "Route: Delegated intent -> structured executor failed -> Codex local",
            ],
            "fallback_reason": "Structured generator or validator execution did not complete successfully.",
            "generator_runner_stdout_excerpt": summarize_failure_text(completed.stdout),
            "generator_runner_stderr_excerpt": summarize_failure_text(completed.stderr),
            "operator_message": (
                "Delegated generator intent stayed bounded, but the structured local path failed. "
                "Codex must take over locally instead of attempting any free delegated shell execution."
            ),
        }
    result = parse_json_output(completed.stdout, "generator_review flow")
    result["selected_path"] = "delegated_intent_local_structured_executor"
    result["task_class"] = "generator_review"
    result["task_label"] = args.task_label
    result["operator_message"] = (
        "Generator review stayed bounded: delegated intent was converted into local builder/executor/validator steps."
    )
    return result


def invoke_debug_hypothesis_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.use_local_or_fixture or args.execute_direct_or:
        return invoke_assistive_or_review_via_wrapper(args, workflow_id, "debug_hypothesis_review")
    if args.debug_input_package is None:
        raise SystemExit("debug_hypothesis_review delegated flow requires --debug-input-package")
    if args.debug_fixture_result is None:
        raise SystemExit("debug_hypothesis_review delegated flow requires --debug-fixture-result in local validation mode")
    input_payload, pilot_eligibility = validate_assistive_or_workhorse_request(
        task_class="debug_hypothesis_review",
        input_package_path=args.debug_input_package,
    )
    if pilot_eligibility["eligibility_result"] != "OR_ALLOWED":
        return build_assistive_or_pilot_reject_result(
            workflow_id=workflow_id,
            task_class="debug_hypothesis_review",
            task_label=args.task_label,
            input_payload=input_payload,
            eligibility=pilot_eligibility,
        )
    command = [
        "python",
        str(DEBUG_REVIEW_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(args.debug_input_package.resolve()),
        "--fixture-result-json",
        str(args.debug_fixture_result.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"debug_hypothesis_review flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "debug_hypothesis_review flow")


def invoke_test_result_triage_review(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.use_local_or_fixture or args.execute_direct_or:
        return invoke_assistive_or_review_via_wrapper(args, workflow_id, "test_result_triage_review")
    if args.test_triage_input_package is None:
        raise SystemExit("test_result_triage_review delegated flow requires --test-triage-input-package")
    if args.test_triage_fixture_result is None:
        raise SystemExit("test_result_triage_review delegated flow requires --test-triage-fixture-result in local validation mode")
    input_payload, pilot_eligibility = validate_assistive_or_workhorse_request(
        task_class="test_result_triage_review",
        input_package_path=args.test_triage_input_package,
    )
    if pilot_eligibility["eligibility_result"] != "OR_ALLOWED":
        return build_assistive_or_pilot_reject_result(
            workflow_id=workflow_id,
            task_class="test_result_triage_review",
            task_label=args.task_label,
            input_payload=input_payload,
            eligibility=pilot_eligibility,
        )
    command = [
        "python",
        str(TEST_TRIAGE_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(args.test_triage_input_package.resolve()),
        "--fixture-result-json",
        str(args.test_triage_fixture_result.resolve()),
    ]
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"test_result_triage_review flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "test_result_triage_review flow")


def invoke_execution_patch_candidate(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.execution_input_package is None:
        raise SystemExit("execution_patch_candidate delegated flow requires --execution-input-package")
    if (args.selected_or_model and "/" in args.selected_or_model) or args.execute_direct_or or args.use_local_or_fixture:
        selected_model = args.selected_or_model or "openai/gpt-oss-20b"
        direct_runner = (
            QWEN_OR_EXECUTION_PATCH_RUNNER
            if str(selected_model).strip().lower().startswith("qwen/")
            else DIRECT_OR_EXECUTION_PATCH_RUNNER
        )
        command = [
            "python",
            str(direct_runner),
            "--task-label",
            args.task_label,
            "--normal-target-model",
            args.normal_target_model,
            "--model",
            selected_model,
            "--task-class",
            args.task_class,
            "--workflow-id",
            workflow_id,
            "--input-package-json",
            str(args.execution_input_package.resolve()),
            "--estimated-or-cost",
            str(args.estimated_or_cost),
            "--cost-estimate-confidence-percent",
            str(args.cost_estimate_confidence_percent),
            "--estimated-prompt-tokens",
            str(args.estimated_prompt_tokens),
            "--estimated-completion-tokens",
            str(args.estimated_completion_tokens),
            "--cost-estimate-sample-count",
            str(args.cost_estimate_sample_count),
            "--cost-estimate-mean-abs-error-percent",
            str(args.cost_estimate_mean_abs_error_percent),
            "--cost-estimate-p50-error-percent",
            str(args.cost_estimate_p50_error_percent),
            "--cost-estimate-p90-error-percent",
            str(args.cost_estimate_p90_error_percent),
            "--cost-estimate-basis",
            args.cost_estimate_basis,
            "--prompt-template-hash",
            args.prompt_template_hash,
            "--task-variant",
            "execution_patch_candidate",
            "--price-snapshot-source",
            args.price_snapshot_source,
            "--price-snapshot-timestamp",
            args.price_snapshot_timestamp,
        ]
        if args.use_local_or_fixture:
            command.append("--use-local-fixture")
            if args.or_local_fixture_response_path:
                command.extend(["--local-fixture-response-path", str(args.or_local_fixture_response_path.resolve())])
        if args.execute_direct_or:
            command.append("--execute-live")
        completed = run_command(command)
        if completed.returncode != 0:
            raise SystemExit(f"execution_patch_candidate direct OR flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
        return parse_json_output(completed.stdout, "execution_patch_candidate direct OR flow")
    command = [
        "python",
        str(EXECUTION_PATCH_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(args.execution_input_package.resolve()),
        "--sidecar-model",
        args.execution_sidecar_model,
        "--sidecar-timeout-seconds",
        str(args.execution_sidecar_timeout_seconds),
    ]
    if args.execution_fixture_result is not None:
        command.extend(["--fixture-result-json", str(args.execution_fixture_result.resolve())])
    if args.execution_live_sidecar:
        command.append("--execute-live-sidecar")
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"execution_patch_candidate flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "execution_patch_candidate flow")


def invoke_execution_write_apply_candidate(args: argparse.Namespace, workflow_id: str) -> dict:
    if args.execution_input_package is not None:
        return invoke_write_candidate_entry_gate(args, workflow_id)
    if args.accepted_source_run_dir is None:
        raise SystemExit(
            "execution_write_apply_candidate delegated flow requires either --execution-input-package or --accepted-source-run-dir"
        )
    command = [
        "python",
        str(EXECUTION_WRITE_APPLY_RUNNER),
        "--task-label",
        args.task_label,
        "--normal-target-model",
        args.normal_target_model,
        "--operator-choice",
        "delegated",
        "--workflow-id",
        workflow_id,
        "--accepted-source-run-dir",
        str(args.accepted_source_run_dir.resolve()),
    ]
    if getattr(args, "execution_live_sidecar", False):
        command.extend(
            [
                "--sidecar-model",
                args.execution_sidecar_model,
                "--sidecar-timeout-seconds",
                str(args.execution_sidecar_timeout_seconds),
                "--working-directory",
                str(REPO_ROOT),
                "--execute-live-sidecar",
            ]
        )
    completed = run_command(command)
    if completed.returncode != 0:
        raise SystemExit(f"execution_write_apply_candidate flow failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return parse_json_output(completed.stdout, "execution_write_apply_candidate flow")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch one bounded delegation task to the matching helper.")
    parser.add_argument("--task-class", required=True, choices=["documentation_draft", "quickchange_patch_review", "quickchange_write_apply", "generator_review", "debug_hypothesis_review", "test_result_triage_review", "execution_patch_candidate", "execution_write_apply_candidate"])
    parser.add_argument("--task-label", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--selected-or-model", default=None)
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--estimated-prompt-tokens", type=int, default=0)
    parser.add_argument("--estimated-completion-tokens", type=int, default=0)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--cost-estimate-sample-count", type=int, default=0)
    parser.add_argument("--cost-estimate-mean-abs-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-p50-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-p90-error-percent", type=float, default=0.0)
    parser.add_argument("--cost-estimate-basis", default="dispatcher_direct_or_initial")
    parser.add_argument("--prompt-template-hash", default="dispatcher_direct_or_quickchange_v1")
    parser.add_argument("--task-variant", default="quickchange_patch_review")
    parser.add_argument("--price-snapshot-source", default="manual_current_openrouter_model_page")
    parser.add_argument("--price-snapshot-timestamp", default="")
    parser.add_argument("--prompt-path", type=Path, default=None)
    parser.add_argument("--structured-review-flow", action="store_true")
    parser.add_argument("--structured-review-source-run-dir", type=Path, default=None)
    parser.add_argument("--editable-path", action="append", default=[])
    parser.add_argument("--max-touched-files", type=int, default=1)
    parser.add_argument("--execute-direct-or", action="store_true")
    parser.add_argument("--use-local-or-fixture", action="store_true")
    parser.add_argument("--or-local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--generator-manifest", type=Path, default=None)
    parser.add_argument("--generator-skill-id", default="janus-test-pipeline")
    parser.add_argument("--generator-summary", default=None)
    parser.add_argument("--debug-input-package", type=Path, default=None)
    parser.add_argument("--debug-fixture-result", type=Path, default=None)
    parser.add_argument("--test-triage-input-package", type=Path, default=None)
    parser.add_argument("--test-triage-fixture-result", type=Path, default=None)
    parser.add_argument("--execution-input-package", type=Path, default=None)
    parser.add_argument("--execution-expected-target-task", default=None)
    parser.add_argument("--execution-fixture-result", type=Path, default=None)
    parser.add_argument("--execution-sidecar-model", default="gpt-5.4")
    parser.add_argument("--execution-sidecar-timeout-seconds", type=int, default=180)
    parser.add_argument("--execution-live-sidecar", action="store_true")
    parser.add_argument("--accepted-source-run-dir", type=Path, default=None)
    parser.add_argument("--estimated-codex-saved-tokens", type=int, default=None)
    parser.add_argument("--estimated-codex-or-overhead-tokens", type=int, default=None)
    parser.add_argument("--minimum-net-codex-saved-tokens", type=int, default=0)
    parser.add_argument("--require-positive-or-roi", action="store_true")
    args = parser.parse_args()

    workflow_id = args.workflow_id
    run_dir = RUN_ROOT / workflow_id
    run_dir.mkdir(parents=True, exist_ok=True)
    choice = normalize_choice(args.operator_choice)
    eligibility = evaluate_assistive_or_workhorse_dispatcher_eligibility(task_class=args.task_class)
    if not args.selected_or_model:
        resolved_selected_or_model = resolve_selected_or_model(args, eligibility)
        if resolved_selected_or_model:
            args.selected_or_model = resolved_selected_or_model

    if choice == "prompt":
        result = with_codex_owned_outcome(prompt_summary(args, workflow_id))
        write_json(run_dir / "operator_choice_prompt.json", result)
        output(result)
        return 0

    if choice == "local":
        result = with_codex_owned_outcome(local_summary(args, workflow_id))
        write_json(run_dir / "operator_choice_local.json", result)
        output(result)
        return 0

    if eligibility["eligibility_result"] != "OR_ALLOWED":
        result = with_codex_owned_outcome({
            "summary_header": "BOUNDED DELEGATION DISPATCH RESULT",
            "workflow_id": workflow_id,
            "task_class": args.task_class,
            "task_label": args.task_label,
            "selected_path": "codex_only_pre_dispatch",
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility["evidence_status"],
            "validation_result": "PASS",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_result_lines": [
                f"Ergebnis: {eligibility['eligibility_result']}",
                f"Route: {args.task_class} bleibt lokal",
            ],
            "operator_message": eligibility["message"],
        })
        write_json(run_dir / "operator_choice_blocked_by_eligibility.json", result)
        output(result)
        return 0

    if args.task_class == "documentation_draft":
        result = invoke_documentation_draft(args, workflow_id)
    elif args.task_class == "quickchange_patch_review":
        result = invoke_quickchange_patch_review(args, workflow_id)
    elif args.task_class == "quickchange_write_apply":
        result = invoke_quickchange_write_apply(args, workflow_id)
    elif args.task_class == "debug_hypothesis_review":
        result = invoke_debug_hypothesis_review(args, workflow_id)
    elif args.task_class == "test_result_triage_review":
        result = invoke_test_result_triage_review(args, workflow_id)
    elif args.task_class == "execution_patch_candidate":
        result = invoke_execution_patch_candidate(args, workflow_id)
    elif args.task_class == "execution_write_apply_candidate":
        result = invoke_execution_write_apply_candidate(args, workflow_id)
    else:
        result = invoke_generator_review(args, workflow_id)

    result = with_codex_owned_outcome(result)
    write_json(run_dir / "dispatcher_result.json", result)
    output(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
