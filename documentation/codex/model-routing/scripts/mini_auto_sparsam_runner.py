#!/usr/bin/env python3
"""Operator-invoked mini Auto-sparsam runner skeleton.

Bounded to the seven live-evidenced documentation skills only.
This helper is local-workflow tooling and is not production routing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
SCRIPTS_DIR = MODEL_ROUTING_DIR / "scripts"
WRAPPER_PATH = SCRIPTS_DIR / "or_file_first_capture_wrapper.ps1"
HEALTH_SNAPSHOT_PATH = (
    REPO_ROOT / "documentation" / "codex" / "skills" / "janus-health-check" / "scripts" / "health_snapshot.py"
)
SESSION_RUNS_DIR = MODEL_ROUTING_DIR / "auto-sparsam-runs"
ALLOWED_SKILLS: dict[str, str] = {
    "DOC-SKILL-001": "openai/gpt-oss-20b",
    "DOC-SKILL-002": "openai/gpt-oss-20b",
    "DOC-SKILL-003": "openai/gpt-oss-20b",
    "DOC-SKILL-006": "openai/gpt-oss-120b",
    "DOC-SKILL-008": "qwen/qwen3.5-flash-02-23",
    "DOC-SKILL-009": "qwen/qwen3.5-flash-02-23",
    "DOC-SKILL-010": "qwen/qwen3.5-flash-02-23",
}
MAX_CALL_COST = 0.0020
MAX_SESSION_COST = 0.0060
MAX_SESSION_CALLS = 3


@dataclass
class RunResult:
    exit_code: int
    summary: dict[str, Any]


def iso_now() -> str:
    return datetime.now().astimezone().isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def build_session_paths(workflow_id: str) -> tuple[Path, Path]:
    session_dir = SESSION_RUNS_DIR / workflow_id
    session_jsonl = MODEL_ROUTING_DIR / f"or_healthcheck_telemetry_auto_sparsam_session_{datetime.now().strftime('%Y-%m-%d')}_{workflow_id}.jsonl"
    return session_dir, session_jsonl


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def skill_in_scope(skill_id: str) -> bool:
    return skill_id in ALLOWED_SKILLS


def base_summary(args: argparse.Namespace, workflow_id: str) -> dict[str, Any]:
    return {
        "workflow_id": workflow_id,
        "skill_id": args.skill_id,
        "routing_mode": "Auto-sparsam",
        "selected_path": "N_A",
        "codex_default_model": args.codex_default_model,
        "or_model": ALLOWED_SKILLS.get(args.skill_id, "N_A"),
        "estimated_or_cost": args.estimated_or_cost,
        "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
        "validation_result": "N_A",
        "fallback_used": "NO",
        "rework_required": "NO",
        "final_outcome": "N_A",
        "operator_message": "",
    }


def fail_before_wrapper(
    args: argparse.Namespace,
    workflow_id: str,
    final_outcome: str,
    operator_message: str,
    selected_path: str,
    validation_result: str,
    fallback_used: str = "NO",
    rework_required: str = "NO",
    exit_code: int = 1,
) -> RunResult:
    summary = base_summary(args, workflow_id)
    summary.update(
        {
            "selected_path": selected_path,
            "validation_result": validation_result,
            "fallback_used": fallback_used,
            "rework_required": rework_required,
            "final_outcome": final_outcome,
            "operator_message": operator_message,
        }
    )
    return RunResult(exit_code=exit_code, summary=summary)


def require_estimate_confidence(args: argparse.Namespace) -> tuple[bool, str]:
    required_values = {
        "estimated_prompt_tokens": args.estimated_prompt_tokens,
        "estimated_completion_tokens": args.estimated_completion_tokens,
        "estimated_or_cost": args.estimated_or_cost,
        "price_snapshot_source": args.price_snapshot_source,
        "price_snapshot_timestamp": args.price_snapshot_timestamp,
        "cost_estimate_confidence_percent": args.cost_estimate_confidence_percent,
        "cost_estimate_sample_count": args.cost_estimate_sample_count,
        "cost_estimate_mean_abs_error_percent": args.cost_estimate_mean_abs_error_percent,
        "cost_estimate_p50_error_percent": args.cost_estimate_p50_error_percent,
        "cost_estimate_p90_error_percent": args.cost_estimate_p90_error_percent,
        "cost_estimate_basis": args.cost_estimate_basis,
        "prompt_template_hash": args.prompt_template_hash,
        "task_variant": args.task_variant,
    }
    missing = [name for name, value in required_values.items() if value is None or value == ""]
    if missing:
        return False, f"Missing estimate/confidence fields: {', '.join(missing)}"
    return True, ""


def operator_display(args: argparse.Namespace, workflow_id: str) -> dict[str, str]:
    return {
        "workflow_id": workflow_id,
        "estimate_line": (
            f"Estimated OR cost: {args.estimated_or_cost:.8f} | Prompt tokens: {args.estimated_prompt_tokens} | "
            f"Completion tokens: {args.estimated_completion_tokens} | Price source: {args.price_snapshot_source} @ {args.price_snapshot_timestamp}"
        ),
        "confidence_line": (
            f"Cost confidence: {args.cost_estimate_confidence_percent:.2f}% | Samples: {args.cost_estimate_sample_count} | "
            f"Avg error: {args.cost_estimate_mean_abs_error_percent:.2f}% | "
            f"P50: {args.cost_estimate_p50_error_percent:.2f}% | P90: {args.cost_estimate_p90_error_percent:.2f}%"
        ),
    }


def invoke_wrapper(args: argparse.Namespace, run_dir: Path) -> subprocess.CompletedProcess[str]:
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(WRAPPER_PATH),
        "-RunDirectory",
        str(run_dir),
        "-RequestBodyPath",
        str(args.request_body_path.resolve()),
    ]
    if args.use_local_fixture:
        command.extend(
            [
                "-UseLocalFixture",
                "-LocalFixtureResponsePath",
                str(args.local_fixture_response_path.resolve()),
            ]
        )
    return run_command(command, REPO_ROOT)


def parse_wrapper_summary(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "response_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Wrapper summary missing: {summary_path}")
    return load_json(summary_path)


def actual_cost_from_usage(usage: dict[str, Any]) -> float | None:
    cost = usage.get("cost")
    if isinstance(cost, (int, float)):
        return float(cost)
    return None


def generate_telemetry_row(args: argparse.Namespace, workflow_id: str, wrapper_summary: dict[str, Any], latency_ms: int) -> dict[str, Any]:
    usage = wrapper_summary.get("usage") or {}
    actual_cost = actual_cost_from_usage(usage)
    if actual_cost is None:
        raise ValueError("Usage cost missing from wrapper summary")
    estimated_cost = float(args.estimated_or_cost)
    error_percent = ((actual_cost - estimated_cost) / estimated_cost * 100.0) if estimated_cost else 0.0
    return {
        "workflow_id": workflow_id,
        "skill_id": args.skill_id,
        "routing_mode": "Auto-sparsam",
        "selected_path": "or_first_then_codex_validate",
        "codex_default_model": args.codex_default_model,
        "or_model": ALLOWED_SKILLS[args.skill_id],
        "estimated_prompt_tokens": args.estimated_prompt_tokens,
        "estimated_completion_tokens": args.estimated_completion_tokens,
        "estimated_or_cost": estimated_cost,
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
        "actual_reasoning_tokens": int(usage.get("reasoning_tokens", 0)),
        "actual_cached_tokens": int(usage.get("cached_tokens", 0)),
        "actual_or_cost": actual_cost,
        "generation_id": wrapper_summary.get("generation_id", ""),
        "usage_source": "response_usage",
        "estimated_codex_effort": args.estimated_codex_effort,
        "estimation_error_percent": round(error_percent, 2),
        "cost_delta_vs_codex_estimate": round(actual_cost - estimated_cost, 8),
        "latency_ms": latency_ms,
        "validation_result": "PASS",
        "fallback_used": "NO",
        "rework_required": "NO",
        "final_outcome": "OR_PASSED_LOCAL_VALIDATION",
        "reason_for_escalation": "",
        "quality_notes": args.quality_notes,
        "recommendation_signal": args.recommendation_signal,
    }


def run_healthcheck(session_jsonl_path: Path, run_dir: Path) -> tuple[dict[str, Any], subprocess.CompletedProcess[str]]:
    command = [
        sys.executable,
        str(HEALTH_SNAPSHOT_PATH),
        "--repo",
        str(REPO_ROOT),
        "--or-telemetry-jsonl",
        str(session_jsonl_path),
    ]
    result = run_command(command, REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "health_snapshot.py failed")
    parsed = json.loads(result.stdout)
    write_json(run_dir / "healthcheck_summary.json", parsed)
    write_text(run_dir / "healthcheck_command.txt", " ".join(command) + "\n")
    return parsed, result


def operator_summary(row: dict[str, Any], session_jsonl_path: Path, healthcheck_summary_path: Path) -> dict[str, Any]:
    return {
        "summary_header": "AUTO-SPARSAM SUMMARY",
        "workflow_id": row["workflow_id"],
        "skill_id": row["skill_id"],
        "or_model": row["or_model"],
        "selected_path": row["selected_path"],
        "estimated_or_cost": row["estimated_or_cost"],
        "actual_or_cost": row["actual_or_cost"],
        "cost_estimate_confidence_percent": row["cost_estimate_confidence_percent"],
        "latency_ms": row["latency_ms"],
        "validation_result": row["validation_result"],
        "fallback_used": row["fallback_used"],
        "rework_required": row["rework_required"],
        "final_outcome": row["final_outcome"],
        "session_jsonl_path": str(session_jsonl_path),
        "healthcheck_summary_path": str(healthcheck_summary_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded operator-invoked mini Auto-sparsam runner skeleton.")
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--request-body-path", type=Path, required=True)
    parser.add_argument("--codex-default-model", default="5.4 mini low")
    parser.add_argument("--estimated-prompt-tokens", type=int, default=None)
    parser.add_argument("--estimated-completion-tokens", type=int, default=None)
    parser.add_argument("--estimated-or-cost", type=float, default=None)
    parser.add_argument("--price-snapshot-source", default=None)
    parser.add_argument("--price-snapshot-timestamp", default=None)
    parser.add_argument("--cost-estimate-confidence-percent", type=float, default=None)
    parser.add_argument("--cost-estimate-sample-count", type=int, default=None)
    parser.add_argument("--cost-estimate-mean-abs-error-percent", type=float, default=None)
    parser.add_argument("--cost-estimate-p50-error-percent", type=float, default=None)
    parser.add_argument("--cost-estimate-p90-error-percent", type=float, default=None)
    parser.add_argument("--cost-estimate-basis", default=None)
    parser.add_argument("--prompt-template-hash", default=None)
    parser.add_argument("--task-variant", default=None)
    parser.add_argument("--estimated-codex-effort", default="low")
    parser.add_argument("--quality-notes", default="Fixture/local validation only. This runner skeleton does not activate production routing.")
    parser.add_argument("--recommendation-signal", default="OR_PREFERRED")
    parser.add_argument("--manual-review-threshold", type=float, default=50.0)
    parser.add_argument("--session-call-count", type=int, default=1)
    parser.add_argument("--session-cost-so-far", type=float, default=0.0)
    parser.add_argument("--use-local-fixture", action="store_true")
    parser.add_argument("--local-fixture-response-path", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workflow_id = args.workflow_id or f"AUTO-SPARSAM-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{args.skill_id}"
    session_dir, session_jsonl_path = build_session_paths(workflow_id)
    run_dir = session_dir / args.skill_id.lower()
    session_dir.mkdir(parents=True, exist_ok=True)

    if not skill_in_scope(args.skill_id):
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="CODEX_ONLY_OUT_OF_SCOPE",
            operator_message="Skill is outside the bounded seven-skill Auto-sparsam scope.",
            selected_path="codex_only_pre_wrapper",
            validation_result="NEEDS_REVIEW",
            fallback_used="YES",
            rework_required="NO",
            exit_code=2,
        )
        print_json(result.summary)
        return result.exit_code

    ok, message = require_estimate_confidence(args)
    if not ok:
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="ABORTED_PRECALL_METADATA_MISSING",
            operator_message=message,
            selected_path="abort_pre_wrapper",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            exit_code=3,
        )
        print_json(result.summary)
        return result.exit_code

    if args.estimated_or_cost > MAX_CALL_COST or (args.session_cost_so_far + args.estimated_or_cost) > MAX_SESSION_COST:
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="ABORTED_COST_CAP",
            operator_message="Estimated cost breaches bounded Auto-sparsam cap.",
            selected_path="abort_pre_wrapper",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            exit_code=4,
        )
        print_json(result.summary)
        return result.exit_code

    if args.session_call_count > MAX_SESSION_CALLS:
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="ABORTED_SESSION_CALL_LIMIT",
            operator_message="Requested session call count exceeds bounded Auto-sparsam maximum.",
            selected_path="abort_pre_wrapper",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            exit_code=5,
        )
        print_json(result.summary)
        return result.exit_code

    if args.cost_estimate_confidence_percent < args.manual_review_threshold:
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="MANUAL_REVIEW_CONFIDENCE_GATE",
            operator_message="Confidence is below the manual-review threshold.",
            selected_path="manual_review_pre_wrapper",
            validation_result="NEEDS_REVIEW",
            fallback_used="NO",
            rework_required="NO",
            exit_code=6,
        )
        print_json(result.summary)
        return result.exit_code

    if args.use_local_fixture and args.local_fixture_response_path is None:
        raise SystemExit("--use-local-fixture requires --local-fixture-response-path")

    display = operator_display(args, workflow_id)
    write_json(run_dir / "pre_call_display.json", display)

    wrapper_result = invoke_wrapper(args, run_dir)
    write_text(run_dir / "wrapper_command_stdout.txt", wrapper_result.stdout)
    write_text(run_dir / "wrapper_command_stderr.txt", wrapper_result.stderr)
    if wrapper_result.returncode != 0:
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="CODEX_ONLY_WRAPPER_FAILURE",
            operator_message="Wrapper invocation failed; route back to Codex-only handling.",
            selected_path="codex_only_wrapper_failure",
            validation_result="FAIL",
            fallback_used="YES",
            rework_required="YES",
            exit_code=wrapper_result.returncode,
        )
        print_json(result.summary)
        return result.exit_code

    wrapper_summary = parse_wrapper_summary(run_dir)
    if not wrapper_summary.get("generation_id") or not wrapper_summary.get("usage"):
        result = fail_before_wrapper(
            args,
            workflow_id,
            final_outcome="CODEX_ONLY_CAPTURE_INCOMPLETE",
            operator_message="Wrapper summary is missing generation_id or usage.",
            selected_path="codex_only_post_wrapper",
            validation_result="FAIL",
            fallback_used="YES",
            rework_required="YES",
            exit_code=7,
        )
        print_json(result.summary)
        return result.exit_code

    telemetry_row = generate_telemetry_row(args, workflow_id, wrapper_summary, latency_ms=0)
    append_jsonl(session_jsonl_path, telemetry_row)
    healthcheck_summary, _ = run_healthcheck(session_jsonl_path, run_dir)
    summary = operator_summary(telemetry_row, session_jsonl_path, run_dir / "healthcheck_summary.json")
    write_json(run_dir / "operator_summary.json", summary)
    write_json(run_dir / "healthcheck_summary_excerpt.json", healthcheck_summary.get("or_telemetry", {}))
    print_json(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
