#!/usr/bin/env python3
"""Bounded OR normalizer helper for janus-spec-normalizer."""

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
RUN_ROOT = MODEL_ROUTING_DIR / "spec-normalizer-runs"
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
VALIDATOR_PATH = (
    REPO_ROOT
    / "documentation"
    / "codex"
    / "skills"
    / "janus-spec-normalizer"
    / "scripts"
    / "validate_feature_spec.py"
)
DEFAULT_SPEC_NORMALIZER_OR_MODEL = "qwen/qwen3-coder-30b-a3b-instruct"

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
    "spec_path",
    "source_path",
    "mode",
    "expected_output",
    "redaction_ready",
]

REQUIRED_RESULT_FIELDS = [
    "status",
    "source_path",
    "target_spec_path",
    "recommended_next_skill",
    "mechanical_cleanup_required",
    "notes",
]


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
        stripped = stripped.removeprefix("```markdown").removeprefix("```json").removeprefix("```").strip()
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


def build_request_body(model: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded Janus spec normalizer. "
                    "Return exactly one JSON object and no prose. "
                    "Normalize one draft spec into parser-safe markdown, do not change product meaning, "
                    "do not add requirements, do not generate tasks, and do not claim release or governance authority."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return a JSON object with these exact top-level fields: "
                    "status, source_path, target_spec_path, recommended_next_skill, mechanical_cleanup_required, notes, normalized_spec_markdown.\n\n"
                    "Rules:\n"
                    "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
                    "- recommended_next_skill must be janus-spec-review or NEEDS_INFO\n"
                    "- mechanical_cleanup_required must be YES or NO\n"
                    "- notes must contain 1 to 4 short strings\n"
                    "- normalized_spec_markdown must contain one full parser-safe Janus Feature Spec\n"
                    "- keep the product meaning unchanged\n"
                    "- do not add implementation details or task breakdowns\n\n"
                    f"Redacted input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 2000,
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
            raise SystemExit("OPENROUTER_API_KEY missing for live spec-normalizer OR invocation")
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
        "skill_id": "janus-spec-normalizer",
        "routing_mode": "Manual-review",
        "selected_path": "delegated_spec_normalization",
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
        "cost_estimate_basis": "spec_normalizer_initial_batch",
        "prompt_template_hash": "spec_normalizer_v1",
        "task_variant": "normalize_spec",
        "price_snapshot_source": "live_openrouter_response",
        "price_snapshot_timestamp": datetime.now().isoformat(),
        "actual_prompt_tokens": usage.get("prompt_tokens"),
        "actual_completion_tokens": usage.get("completion_tokens"),
        "actual_reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") if isinstance(usage.get("completion_tokens_details"), dict) else None,
        "actual_cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens") if isinstance(usage.get("prompt_tokens_details"), dict) else None,
        "actual_or_cost": actual_cost,
        "generation_id": str(response_summary.get("generation_id") or ""),
        "usage_source": "response_usage" if usage else "fallback_estimate",
        "estimated_codex_effort": "low",
        "estimation_error_percent": round(estimation_error_percent, 2),
        "cost_delta_vs_codex_estimate": round((actual_cost or 0.0) - estimated_or_cost, 8),
        "latency_ms": latency_ms,
        "validation_result": validation_result,
        "fallback_used": fallback_used,
        "rework_required": rework_required,
        "final_outcome": final_outcome,
        "reason_for_escalation": "bounded spec normalization" if validation_result == "PASS" else "normalization failed or fallback required",
        "quality_notes": "current contract normalized with validator compatibility",
    }


def validate_input_package(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_INPUT_FIELDS:
        if field not in payload:
            issues.append(f"missing input field: {field}")
    if payload.get("bound_skill_context") != "janus-spec-normalizer":
        issues.append("bound_skill_context must be exactly janus-spec-normalizer")
    if payload.get("mode") != "NORMALIZE_SPEC":
        issues.append("mode must be NORMALIZE_SPEC")
    if payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")
    return issues


def validator_issues_for_markdown(spec_markdown: str) -> list[str]:
    if not VALIDATOR_PATH.exists():
        return ["missing validator script"]
    temp_path = RUN_ROOT / "_tmp_normalized_spec.md"
    write_text(temp_path, spec_markdown)
    completed = run_command(["python", str(VALIDATOR_PATH), str(temp_path)])
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        pass
    if completed.returncode == 0:
        return []
    issues = [line[2:] if line.startswith("- ") else line for line in completed.stdout.splitlines() if line.startswith("- ")]
    if not issues:
        issues = [completed.stdout.strip() or "validator failed"]
    return issues


def validate_result_payload(payload: dict[str, Any], input_payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in REQUIRED_RESULT_FIELDS:
        if field not in payload:
            issues.append(f"missing result field: {field}")
    if payload.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status invalid")
    if payload.get("source_path") != input_payload.get("source_path"):
        issues.append("source_path invalid")
    if payload.get("target_spec_path") != input_payload.get("spec_path"):
        issues.append("target_spec_path invalid")
    if payload.get("recommended_next_skill") not in {"janus-spec-review", "NEEDS_INFO"}:
        issues.append("recommended_next_skill invalid")
    if payload.get("mechanical_cleanup_required") not in {"YES", "NO"}:
        issues.append("mechanical_cleanup_required invalid")
    if not isinstance(payload.get("notes"), list) or not payload.get("notes"):
        issues.append("notes invalid")

    spec_markdown = payload.get("normalized_spec_markdown")
    if not isinstance(spec_markdown, str) or not spec_markdown.strip():
        issues.append("normalized_spec_markdown invalid")
        return issues
    issues.extend(validator_issues_for_markdown(spec_markdown))
    return issues


def render_result_markdown(result_payload: dict[str, Any]) -> str:
    lines = [
        "SPEC_NORMALIZER_RESULT",
        f"Status: {result_payload['status']}",
        f"Source Path: {result_payload['source_path']}",
        f"Target Spec Path: {result_payload['target_spec_path']}",
        f"Recommended Next Skill: {result_payload['recommended_next_skill']}",
        f"Mechanical Cleanup Required: {result_payload['mechanical_cleanup_required']}",
        "Normalized Spec Markdown:",
        result_payload["normalized_spec_markdown"],
        f"Notes: {result_payload['notes']}",
    ]
    return "\n".join(lines) + "\n"


def prompt_lines(task_label: str, selected_or_model: str, estimated_or_cost: float, confidence: float) -> list[str]:
    return build_operator_prompt_lines(
        choice_2_label="OR",
        selected_or_model=selected_or_model,
        pre_call_cost_basis=f"Spec normalizer bounded lane for {task_label}",
        estimated_or_cost=estimated_or_cost,
        cost_estimate_confidence_percent=confidence,
        operator_recommendation="bounded OR lane ready",
        operator_recommendation_reason="structured normalization only; Codex keeps final review ownership",
    )


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
    prompt_lines_text = prompt_lines(
        args.task_label,
        DEFAULT_SPEC_NORMALIZER_OR_MODEL,
        args.estimated_or_cost,
        args.cost_estimate_confidence_percent,
    )

    write_text(run_dir / "operator_prompt.txt", "\n".join(prompt_lines_text) + "\n")

    if args.input_package_json:
        input_path = Path(args.input_package_json)
        input_payload = load_json(input_path)
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
            final_outcome="SPEC_NORMALIZER_INPUT_INVALID",
            normal_target_model=args.normal_target_model,
            skill="janus-spec-normalizer",
            task_class="SPEC_NORMALIZER",
            eligibility_result="NOT_ELIGIBLE",
            eligibility_reason_code="MISSING_INPUT",
            evidence_status="NO_OR_RUN",
        )
        write_json(run_dir / "result.json", result_payload)
        write_single_jsonl_row(
            run_dir / "or_healthcheck_telemetry.jsonl",
            {
                "workflow_id": args.workflow_id,
                "skill": "janus-spec-normalizer",
                "selected_path": "Codex-only",
                "operator_choice": choice,
                "final_outcome": result_payload["final_outcome"],
                "validation_result": "PASS",
            },
        )
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 1

    if choice == "prompt":
        result_payload = {
            "summary_header": "SPEC NORMALIZER GATE",
            "workflow_id": args.workflow_id,
            "skill": "janus-spec-normalizer",
            "task_label": args.task_label,
            "selected_path": "operator_choice_pending",
            "normal_target_model": args.normal_target_model,
            "choice_1": "Codex",
            "choice_2": "OR",
            "selected_or_model": DEFAULT_SPEC_NORMALIZER_OR_MODEL,
            "estimated_or_cost": args.estimated_or_cost,
            "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
            "operator_prompt_lines": prompt_lines_text,
            "boundaries": [
                "No delegated product-decision changes",
                "No delegated task generation",
                "No delegated authoritative Spec acceptance",
                "Codex remains final reviewer and local writer",
            ],
            "final_outcome": "AWAITING_OPERATOR_CHOICE",
            "validation_result": "PASS",
        }
        write_json(run_dir / "result.json", result_payload)
        write_single_jsonl_row(
            run_dir / "or_healthcheck_telemetry.jsonl",
            {
                "workflow_id": args.workflow_id,
                "skill": "janus-spec-normalizer",
                "selected_path": "operator_choice_pending",
                "operator_choice": choice,
                "or_model": DEFAULT_SPEC_NORMALIZER_OR_MODEL,
                "estimated_or_cost": args.estimated_or_cost,
                "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
                "final_outcome": "AWAITING_OPERATOR_CHOICE",
                "validation_result": "PASS",
            },
        )
        print(json.dumps(result_payload, indent=2, ensure_ascii=False))
        return 0

    if choice == "local":
        spec_markdown = input_payload.get("normalized_spec_markdown")
        if not isinstance(spec_markdown, str) or not spec_markdown.strip():
            spec_markdown = input_payload.get("spec_snapshot", "")
        if not isinstance(spec_markdown, str) or not spec_markdown.strip():
            raise SystemExit("local mode needs normalized_spec_markdown or spec_snapshot")
        result_payload = {
            "status": "PASS",
            "source_path": input_payload["source_path"],
            "target_spec_path": input_payload["spec_path"],
            "recommended_next_skill": "janus-spec-review",
            "mechanical_cleanup_required": "NO",
            "notes": ["Local normalization path used.", "No OR call performed."],
            "normalized_spec_markdown": spec_markdown,
        }
        issues = validate_result_payload(result_payload, input_payload)
        result_payload["validation_result"] = "PASS" if not issues else "FAIL"
        write_json(run_dir / "result.json", result_payload)
        write_text(run_dir / "normalized_spec.md", spec_markdown)
        write_single_jsonl_row(
            run_dir / "or_healthcheck_telemetry.jsonl",
            {
                "workflow_id": args.workflow_id,
                "skill": "janus-spec-normalizer",
                "selected_path": "Codex-only",
                "operator_choice": choice,
                "final_outcome": "LOCAL_NORMALIZATION",
                "validation_result": result_payload["validation_result"],
                "issue_count": len(issues),
            },
        )
        print(render_result_markdown(result_payload))
        return 0 if not issues else 2

    if not args.use_local_or_fixture and not args.execute_direct_or:
        raise SystemExit("delegated mode currently requires --use-local-or-fixture or --execute-direct-or")
    if args.use_local_or_fixture:
        if not args.or_local_fixture_response_path:
            raise SystemExit("--or-local-fixture-response-path is required in delegated fixture mode")
        fixture_path = Path(args.or_local_fixture_response_path)
        fixture_payload = load_json(fixture_path)
        write_json(run_dir / "fixture_response_snapshot.json", fixture_payload)

        content = content_from_response(fixture_payload)
        if content:
            parsed = parse_json_from_text(content)
        else:
            parsed = dict(fixture_payload)
        spec_markdown = str(parsed.get("normalized_spec_markdown") or parsed.get("spec_markdown") or "").strip()
        if not spec_markdown:
            raise SystemExit("fixture response missing normalized_spec_markdown or spec_markdown")

        result_payload = {
            "status": str(parsed.get("status") or "PASS"),
            "source_path": str(parsed.get("source_path") or input_payload["source_path"]),
            "target_spec_path": str(parsed.get("target_spec_path") or input_payload["spec_path"]),
            "recommended_next_skill": str(parsed.get("recommended_next_skill") or "janus-spec-review"),
            "mechanical_cleanup_required": str(parsed.get("mechanical_cleanup_required") or "NO"),
            "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [str(parsed.get("notes") or "Fixture response used.")],
            "normalized_spec_markdown": spec_markdown,
        }
        result_issues = validate_result_payload(result_payload, input_payload)
        validation_result = "PASS" if not result_issues else "FAIL"
        result_payload["validation_result"] = validation_result

        write_json(run_dir / "result.json", result_payload)
        write_text(run_dir / "normalized_spec.md", spec_markdown)
        write_single_jsonl_row(
            run_dir / "or_healthcheck_telemetry.jsonl",
            {
                "workflow_id": args.workflow_id,
                "skill": "janus-spec-normalizer",
                "selected_path": "OR" if choice == "delegated" else "Codex-only",
                "operator_choice": choice,
                "final_outcome": "OR_NORMALIZATION" if validation_result == "PASS" else "OR_NORMALIZATION_FAILED",
                "validation_result": validation_result,
                "model": args.normal_target_model,
                "issue_count": len(result_issues),
            },
        )
        print(render_result_markdown(result_payload))
        return 0 if validation_result == "PASS" else 3

    request_body = build_request_body(DEFAULT_SPEC_NORMALIZER_OR_MODEL, input_payload)
    request_body_path = run_dir / "request_body_source.json"
    write_json(request_body_path, request_body)
    start = time.time()
    completed = invoke_file_first_wrapper(
        run_dir=run_dir,
        request_body_path=request_body_path,
        use_local_fixture=False,
        local_fixture_response_path=None,
        execute_live=True,
        title="Janus Spec Normalizer",
    )
    latency_ms = int(round((time.time() - start) * 1000))
    write_text(run_dir / "wrapper_stdout.log", completed.stdout)
    write_text(run_dir / "wrapper_stderr.log", completed.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or "file-first wrapper failed")

    response_body = load_json(run_dir / "response_body.json")
    response_summary = load_json(run_dir / "response_summary.json")
    content = content_from_response(response_body)
    parsed = parse_json_from_text(content)
    spec_markdown = str(parsed.get("normalized_spec_markdown") or parsed.get("spec_markdown") or "").strip()
    if not spec_markdown:
        raise SystemExit("live response missing normalized_spec_markdown or spec_markdown")

    result_payload = {
        "status": str(parsed.get("status") or "PASS"),
        "source_path": str(parsed.get("source_path") or input_payload["source_path"]),
        "target_spec_path": str(parsed.get("target_spec_path") or input_payload["spec_path"]),
        "recommended_next_skill": str(parsed.get("recommended_next_skill") or "janus-spec-review"),
        "mechanical_cleanup_required": str(parsed.get("mechanical_cleanup_required") or "NO"),
        "notes": parsed.get("notes") if isinstance(parsed.get("notes"), list) else [str(parsed.get("notes") or "Live response used.")],
        "normalized_spec_markdown": spec_markdown,
    }
    result_issues = validate_result_payload(result_payload, input_payload)
    telemetry_issues: list[str] = []
    if not str(response_summary.get("generation_id") or "").strip():
        telemetry_issues.append("generation_id missing")
    if not isinstance(response_summary.get("usage"), dict):
        telemetry_issues.append("usage missing")
    if actual_or_cost(response_summary) is None:
        telemetry_issues.append("actual OR cost missing")
    if response_summary.get("finish_reason") == "length":
        telemetry_issues.append("finish_reason=length")
    validation_result = "PASS" if not result_issues and not telemetry_issues else "FAIL"
    result_payload["validation_result"] = validation_result
    write_json(run_dir / "result.json", result_payload)
    write_text(run_dir / "normalized_spec.md", spec_markdown)
    telemetry_path = MODEL_ROUTING_DIR / f"or_healthcheck_telemetry_spec_normalizer_{datetime.now().strftime('%Y-%m-%d')}_{args.workflow_id}.jsonl"
    telemetry_row = build_telemetry_row(
        workflow_id=args.workflow_id,
        normal_target_model=args.normal_target_model,
        or_model=DEFAULT_SPEC_NORMALIZER_OR_MODEL,
        estimated_or_cost=float(args.estimated_or_cost),
        cost_estimate_confidence_percent=float(args.cost_estimate_confidence_percent),
        response_summary=response_summary,
        validation_result=validation_result,
        final_outcome="OR_NORMALIZATION_READY_FOR_CODEX_VALIDATION" if validation_result == "PASS" else "OR_NORMALIZATION_REJECT_AND_FALLBACK",
        fallback_used="NO" if validation_result == "PASS" else "YES",
        rework_required="NO" if validation_result == "PASS" else "YES",
        latency_ms=latency_ms,
    )
    write_single_jsonl_row(telemetry_path, telemetry_row)
    try:
        healthcheck_summary = run_healthcheck(telemetry_path, run_dir)
        write_json(run_dir / "healthcheck_summary.json", healthcheck_summary)
        healthcheck_status = "PASS"
    except Exception as exc:
        healthcheck_summary = {"error": str(exc)}
        healthcheck_status = "FAIL"
        validation_result = "FAIL"
        result_payload["validation_result"] = validation_result
        write_json(run_dir / "result.json", result_payload)

    result_payload["telemetry_jsonl_path"] = str(telemetry_path)
    result_payload["healthcheck_status"] = healthcheck_status
    result_payload["latency_ms"] = latency_ms
    result_payload["actual_or_cost"] = actual_or_cost(response_summary)
    write_json(run_dir / "result.json", result_payload)
    print(render_result_markdown(result_payload))
    return 0 if validation_result == "PASS" and healthcheck_status == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
