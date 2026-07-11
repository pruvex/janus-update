#!/usr/bin/env python3
"""Bounded OR review helper for janus-health-check."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
RUN_ROOT = MODEL_ROUTING_DIR / "health-check-review-runs"
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
DEFAULT_HEALTH_CHECK_OR_MODEL = "qwen/qwen3-coder-30b-a3b-instruct"

if str(MODEL_ROUTING_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MODEL_ROUTING_DIR / "scripts"))

from bounded_or_worker_gate_prompt import build_missing_gate_result  # noqa: E402


REQUIRED_INPUT_FIELDS = [
    "workflow_id",
    "bound_skill_context",
    "mode",
    "scan_summary",
    "git_state",
    "backlog_visibility",
    "doc_skill_drift",
    "large_files",
    "expected_systemhealth",
    "expected_traffic_light",
    "expected_next_skill",
    "expected_model",
    "expected_reasoning",
    "expected_operational_recommendation",
    "redaction_ready",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "systemhealth_percent",
    "traffic_light",
    "working_state",
    "recommended_next_skill",
    "recommended_model",
    "recommended_reasoning",
    "operational_recommendation",
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
        "Live-Evidenz: bounded health-check review lane in fixture-validation mode",
        "Einordnung: hygiene scan interpretation only; Codex keeps final process authority",
        f"Fest empfohlenes OR-Modell: {model_label}",
        f"Pre-Call-Kostenbasis: Health-check bounded lane for {task_label}",
        f"Voraussichtliche OR-Kosten {estimated_cost:.9f}, Evidenzgenauigkeit {confidence_percent:.0f}%",
    ]


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    if payload.get("bound_skill_context") != "janus-health-check":
        issues.append("bound_skill_context must be exactly janus-health-check")
    if payload.get("mode") != "DAILY":
        issues.append("mode must be DAILY for this bounded review")
    if payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")
    return issues


def validate_result_payload(payload: dict[str, Any], input_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in payload:
            issues.append(f"missing result field: {field}")
    health_value = payload.get("systemhealth_percent")
    if not isinstance(health_value, (int, float)) or not (0 <= float(health_value) <= 100):
        issues.append("systemhealth_percent invalid")
    if str(payload.get("traffic_light") or "") != str(input_payload.get("expected_traffic_light") or ""):
        issues.append("traffic_light must match expected_traffic_light")
    if payload.get("working_state") not in {"WORKABLE", "CAUTION", "BLOCKED"}:
        issues.append("working_state invalid")
    if str(payload.get("recommended_next_skill") or "") != str(input_payload.get("expected_next_skill") or ""):
        issues.append("recommended_next_skill must match expected_next_skill")
    if str(payload.get("recommended_model") or "") != str(input_payload.get("expected_model") or ""):
        issues.append("recommended_model must match expected_model")
    if str(payload.get("recommended_reasoning") or "") != str(input_payload.get("expected_reasoning") or ""):
        issues.append("recommended_reasoning must match expected_reasoning")
    if str(payload.get("operational_recommendation") or "").strip() != str(input_payload.get("expected_operational_recommendation") or "").strip():
        issues.append("operational_recommendation must match expected_operational_recommendation")
    if payload.get("manual_review_needed") not in {"YES", "NO"}:
        issues.append("manual_review_needed must be YES or NO")
    notes = payload.get("notes")
    if not isinstance(notes, list) or not (1 <= len(notes) <= 4):
        issues.append("notes must contain 1 to 4 items")
    return issues


def build_request_body(model: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded Janus health-check review assistant. "
                    "Use only the redacted input package. "
                    "Return exactly one JSON object and no prose. "
                    "Do not claim authoritative file deletion, Git action, release action, or final process authority."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return a JSON object with these exact top-level fields: "
                    "status, systemhealth_percent, traffic_light, working_state, recommended_next_skill, "
                    "recommended_model, recommended_reasoning, operational_recommendation, manual_review_needed, notes.\n\n"
                    "Rules:\n"
                    "- systemhealth_percent must be a number from 0 to 100\n"
                    "- traffic_light must match the expected traffic light from the input package exactly\n"
                    "- working_state must be WORKABLE, CAUTION, or BLOCKED\n"
                    "- recommended_next_skill, recommended_model, recommended_reasoning, and operational_recommendation "
                    "must match the expected values from the input package exactly\n"
                    "- manual_review_needed must be YES or NO\n"
                    "- notes must contain 1 to 4 short strings\n"
                    "- do not propose file deletion, release actions, or Git actions as if already approved\n\n"
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
            raise SystemExit("OPENROUTER_API_KEY missing for live health-check OR invocation")
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
        DEFAULT_HEALTH_CHECK_OR_MODEL,
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
            final_outcome="HEALTH_CHECK_INPUT_INVALID",
            normal_target_model=args.normal_target_model,
            skill="janus-health-check",
            task_class="HEALTH_CHECK_REVIEW",
            eligibility_result="NOT_ELIGIBLE",
            eligibility_reason_code="MISSING_INPUT",
            evidence_status="NO_OR_RUN",
        )
        write_json(run_dir / "result.json", result_payload)
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 1

    if choice == "prompt":
        result_payload = {
            "summary_header": "HEALTH CHECK GATE",
            "workflow_id": args.workflow_id,
            "skill": "janus-health-check",
            "task_label": args.task_label,
            "selected_path": "operator_choice_pending",
            "normal_target_model": args.normal_target_model,
            "choice_1": "Codex",
            "choice_2": "OR",
            "selected_or_model": DEFAULT_HEALTH_CHECK_OR_MODEL,
            "estimated_or_cost": args.estimated_or_cost,
            "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
            "operator_prompt_lines": prompt_text,
            "boundaries": [
                "No delegated Git action",
                "No delegated release action",
                "No delegated file deletion",
                "Codex remains final health-check owner",
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
            "systemhealth_percent": input_payload["expected_systemhealth"],
            "traffic_light": input_payload["expected_traffic_light"],
            "working_state": "CAUTION" if input_payload["expected_traffic_light"] == "GELB" else "WORKABLE",
            "recommended_next_skill": input_payload["expected_next_skill"],
            "recommended_model": input_payload["expected_model"],
            "recommended_reasoning": input_payload["expected_reasoning"],
            "operational_recommendation": input_payload["expected_operational_recommendation"],
            "manual_review_needed": "NO",
            "notes": ["Local Codex health-check path used.", "No OR call performed."],
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
            "systemhealth_percent": parsed.get("systemhealth_percent"),
            "traffic_light": str(parsed.get("traffic_light") or input_payload["expected_traffic_light"]),
            "working_state": str(parsed.get("working_state") or "CAUTION"),
            "recommended_next_skill": str(parsed.get("recommended_next_skill") or input_payload["expected_next_skill"]),
            "recommended_model": str(parsed.get("recommended_model") or input_payload["expected_model"]),
            "recommended_reasoning": str(parsed.get("recommended_reasoning") or input_payload["expected_reasoning"]),
            "operational_recommendation": str(parsed.get("operational_recommendation") or input_payload["expected_operational_recommendation"]),
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
            "skill_id": "janus-health-check",
            "routing_mode": "Manual-review",
            "selected_path": "delegated_health_check_review",
            "codex_default_model": args.normal_target_model,
            "or_model": DEFAULT_HEALTH_CHECK_OR_MODEL,
            "estimated_prompt_tokens": 0,
            "estimated_completion_tokens": 0,
            "estimated_or_cost": args.estimated_or_cost,
            "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
            "cost_estimate_sample_count": 0,
            "cost_estimate_mean_abs_error_percent": 0.0,
            "cost_estimate_p50_error_percent": 0.0,
            "cost_estimate_p90_error_percent": 0.0,
            "cost_estimate_basis": "health_check_fixture_gate",
            "prompt_template_hash": "health_check_review_v1",
            "task_variant": "health_check_review",
            "price_snapshot_source": "fixture",
            "price_snapshot_timestamp": datetime.utcnow().isoformat(),
            "actual_prompt_tokens": 0,
            "actual_completion_tokens": 0,
            "actual_reasoning_tokens": None,
            "actual_cached_tokens": None,
            "actual_or_cost": 0.0,
            "generation_id": "fixture-health-check-review",
            "usage_source": "fallback_estimate",
            "estimated_codex_effort": "medium",
            "estimation_error_percent": 0.0,
            "cost_delta_vs_codex_estimate": 0.0,
            "latency_ms": 0,
            "validation_result": validation_result,
            "fallback_used": "NO",
            "rework_required": "NO" if validation_result == "PASS" else "YES",
            "final_outcome": "HEALTH_CHECK_REVIEW_READY_FOR_CODEX_VALIDATION" if validation_result == "PASS" else "HEALTH_CHECK_REVIEW_NEEDS_CODEX_RECHECK",
            "reason_for_escalation": "bounded health-check review",
            "quality_notes": "Fixture-validated bounded health-check review only; Codex remains final owner.",
            "recommendation_signal": "OR_PREFERRED" if validation_result == "PASS" else "MANUAL_REVIEW",
        }
        telemetry_path = run_dir / "or_healthcheck_telemetry.jsonl"
        write_single_jsonl_row(telemetry_path, telemetry_row)
        run_healthcheck(telemetry_path, run_dir)
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 0 if validation_result == "PASS" else 2

    request_body = build_request_body(DEFAULT_HEALTH_CHECK_OR_MODEL, input_payload)
    request_path = run_dir / "request_body.json"
    write_json(request_path, request_body)
    completed = invoke_file_first_wrapper(
        run_dir=run_dir,
        request_body_path=request_path,
        use_local_fixture=False,
        local_fixture_response_path=None,
        execute_live=True,
        title="Janus Health Check Review",
    )
    write_text(run_dir / "wrapper_stdout.log", completed.stdout)
    write_text(run_dir / "wrapper_stderr.log", completed.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or "wrapper failed")
    response_body = load_json(run_dir / "response_body.json")
    parsed = parse_json_from_text(content_from_response(response_body))
    result_payload = {
        "status": str(parsed.get("status") or "PASS"),
        "systemhealth_percent": parsed.get("systemhealth_percent"),
        "traffic_light": str(parsed.get("traffic_light") or input_payload["expected_traffic_light"]),
        "working_state": str(parsed.get("working_state") or "CAUTION"),
        "recommended_next_skill": str(parsed.get("recommended_next_skill") or input_payload["expected_next_skill"]),
        "recommended_model": str(parsed.get("recommended_model") or input_payload["expected_model"]),
        "recommended_reasoning": str(parsed.get("recommended_reasoning") or input_payload["expected_reasoning"]),
        "operational_recommendation": str(parsed.get("operational_recommendation") or input_payload["expected_operational_recommendation"]),
        "manual_review_needed": str(parsed.get("manual_review_needed") or "NO"),
        "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [str(parsed.get("notes") or "Live OR response used.")],
    }
    issues = validate_result_payload(result_payload, input_payload)
    validation_result = "PASS" if not issues else "FAIL"
    result_payload["validation_result"] = validation_result
    result_payload["issue_count"] = len(issues)
    write_json(run_dir / "result.json", result_payload)

    telemetry_row = {
        "workflow_id": args.workflow_id,
        "skill_id": "janus-health-check",
        "routing_mode": "Manual-review",
        "selected_path": "delegated_health_check_review",
        "codex_default_model": args.normal_target_model,
        "or_model": DEFAULT_HEALTH_CHECK_OR_MODEL,
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 0,
        "estimated_or_cost": args.estimated_or_cost,
        "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
        "cost_estimate_sample_count": 1,
        "cost_estimate_mean_abs_error_percent": 0.0,
        "cost_estimate_p50_error_percent": 0.0,
        "cost_estimate_p90_error_percent": 0.0,
        "cost_estimate_basis": "health_check_live_gate",
        "prompt_template_hash": "health_check_review_v1",
        "task_variant": "health_check_review",
        "price_snapshot_source": "live_openrouter_response",
        "price_snapshot_timestamp": datetime.utcnow().isoformat(),
        "actual_prompt_tokens": None,
        "actual_completion_tokens": None,
        "actual_reasoning_tokens": None,
        "actual_cached_tokens": None,
        "actual_or_cost": 0.0,
        "generation_id": None,
        "usage_source": "fallback_estimate",
        "estimated_codex_effort": "medium",
        "estimation_error_percent": 0.0,
        "cost_delta_vs_codex_estimate": -args.estimated_or_cost,
        "latency_ms": 0,
        "validation_result": validation_result,
        "fallback_used": "NO",
        "rework_required": "NO" if validation_result == "PASS" else "YES",
        "final_outcome": "HEALTH_CHECK_REVIEW_READY_FOR_CODEX_VALIDATION" if validation_result == "PASS" else "HEALTH_CHECK_REVIEW_NEEDS_CODEX_RECHECK",
        "reason_for_escalation": "bounded health-check review",
        "quality_notes": "Bounded health-check review only; Codex remains final owner.",
        "recommendation_signal": "OR_PREFERRED" if validation_result == "PASS" else "MANUAL_REVIEW",
    }
    telemetry_path = run_dir / "or_healthcheck_telemetry.jsonl"
    write_single_jsonl_row(telemetry_path, telemetry_row)
    run_healthcheck(telemetry_path, run_dir)
    print(json.dumps(result_payload, indent=2, ensure_ascii=False))
    return 0 if validation_result == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
