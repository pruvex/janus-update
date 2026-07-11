#!/usr/bin/env python3
"""Operator-invoked fixed OR choice runner for the seven mini documentation skills.

This helper is bounded local workflow tooling only.
It does not enable production routing and does not use Auto Router.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DEFAULT_CONFIG_PATH = (
    MODEL_ROUTING_DIR / "config" / "doc_skill_mini_fixed_or_live_enabled_2026-06-13.json"
)
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

from bounded_or_worker_eligibility import evaluate_doc_skill_fixed_or
from bounded_or_worker_gate_prompt import build_operator_prompt_lines
from bounded_or_worker_outcome import normalize_codex_owned_outcome

OPERATOR_RECOMMENDATION_MAP: dict[str, dict[str, str]] = {
    "DOC-SKILL-001": {
        "operator_recommendation": "PREFER_OR",
        "operator_recommendation_reason": "sehr guenstige, deterministische Summary-Spur mit sauberer Live-Evidenz",
    },
    "DOC-SKILL-002": {
        "operator_recommendation": "PREFER_OR",
        "operator_recommendation_reason": "guenstige Report-/Summary-Spur mit sauberer Live-Evidenz",
    },
    "DOC-SKILL-003": {
        "operator_recommendation": "PREFER_OR",
        "operator_recommendation_reason": "guenstigste akzeptierte Handoff-Spur mit sauberer Live-Evidenz",
    },
    "DOC-SKILL-006": {
        "operator_recommendation": "PREFER_OR",
        "operator_recommendation_reason": "mechanische Formatierung blieb im Live-Betrieb extrem guenstig",
    },
    "DOC-SKILL-008": {
        "operator_recommendation": "OR_OPTIONAL",
        "operator_recommendation_reason": "valide und bounded, aber nicht unter den staerksten Sparspuren",
    },
    "DOC-SKILL-009": {
        "operator_recommendation": "OR_OPTIONAL",
        "operator_recommendation_reason": "valide und bounded, aber nicht unter den staerksten Sparspuren",
    },
    "DOC-SKILL-010": {
        "operator_recommendation": "OR_OPTIONAL",
        "operator_recommendation_reason": "valide und bounded, aber nicht unter den staerksten Sparspuren",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def iso_now() -> str:
    return datetime.now().astimezone().isoformat()


def norm(text: str) -> str:
    return text.strip().lower()


def model_matches(normal_target_model: str, config: dict[str, Any]) -> bool:
    check = norm(normal_target_model)
    return any(token in check for token in config["normal_target_model_match"])


def load_baseline_row(config: dict[str, Any], skill_id: str) -> dict[str, Any]:
    for rel_path in config["baseline_telemetry_sources"]:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("skill_id") == skill_id:
                return row
    raise KeyError(f"Baseline telemetry not found for {skill_id}")


def healthcheck_command(config: dict[str, Any], session_jsonl_path: Path) -> list[str]:
    return [
        sys.executable,
        str(HEALTH_SNAPSHOT_PATH),
        "--repo",
        str(REPO_ROOT),
        "--or-telemetry-jsonl",
        str(session_jsonl_path),
    ]


def build_paths(config: dict[str, Any], workflow_id: str, skill_id: str) -> tuple[Path, Path, Path]:
    runs_dir = REPO_ROOT / config["fixed_or_runs_dir"]
    session_dir = runs_dir / workflow_id / skill_id.lower()
    date_part = datetime.now().strftime("%Y-%m-%d")
    session_jsonl_name = f"or_healthcheck_telemetry_fixed_or_session_{date_part}_{workflow_id}.jsonl"
    session_jsonl_path = MODEL_ROUTING_DIR / session_jsonl_name
    request_body_source_path = session_dir / "request_body_source.json"
    return session_dir, session_jsonl_path, request_body_source_path


def get_operator_recommendation(skill_id: str) -> dict[str, str]:
    return OPERATOR_RECOMMENDATION_MAP.get(
        skill_id,
        {
            "operator_recommendation": "OR_OPTIONAL",
            "operator_recommendation_reason": "bounded OR live evidence exists, but no stronger operator guidance is mapped",
        },
    )


def make_operator_prompt(
    args: argparse.Namespace,
    config: dict[str, Any],
    baseline_row: dict[str, Any],
    skill_config: dict[str, Any],
    workflow_id: str,
) -> dict[str, Any]:
    recommendation = get_operator_recommendation(args.skill_id)
    return {
        "workflow_id": workflow_id,
        "skill_id": args.skill_id,
        "local_codex_option": "handle locally with Codex and spend Codex quota",
        "or_option": f"handle with OR using fixed model {skill_config['selected_or_model']} and preserve Codex quota",
        "estimated_or_cost": baseline_row["estimated_or_cost"],
        "operator_recommendation": recommendation["operator_recommendation"],
        "operator_recommendation_reason": recommendation["operator_recommendation_reason"],
        "confidence_status": {
            "cost_estimate_confidence_percent": baseline_row.get("cost_estimate_confidence_percent"),
            "cost_estimate_sample_count": baseline_row.get("cost_estimate_sample_count"),
            "cost_estimate_mean_abs_error_percent": baseline_row.get("cost_estimate_mean_abs_error_percent"),
            "cost_estimate_p50_error_percent": baseline_row.get("cost_estimate_p50_error_percent"),
            "cost_estimate_p90_error_percent": baseline_row.get("cost_estimate_p90_error_percent"),
            "cost_estimate_basis": baseline_row.get("cost_estimate_basis"),
            "prompt_template_hash": baseline_row.get("prompt_template_hash"),
            "task_variant": skill_config["task_variant"],
            "price_snapshot_source": baseline_row.get("price_snapshot_source"),
            "price_snapshot_timestamp": baseline_row.get("price_snapshot_timestamp")
        },
        "per_call_cap_usd": config["per_call_cap_usd"],
        "session_cap_usd": config["session_cap_usd"],
        "note": "Operator-invoked fixed OR use only. No Auto Router. Not production routing."
    }


def build_request_body(skill_id: str, skill_config: dict[str, Any]) -> dict[str, Any]:
    fixture_dir = REPO_ROOT / skill_config["fixture_dir"]
    prompt = (fixture_dir / "prompt.md").read_text(encoding="utf-8-sig").strip()
    sanitized = load_json(fixture_dir / "input.sanitized.json")
    user_content = (
        prompt
        + "\n\nSanitized input JSON:\n"
        + json.dumps(sanitized, ensure_ascii=False, indent=2)
    )
    return {
        "model": skill_config["selected_or_model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are assisting with {skill_id}."
                    " Use only the sanitized input. Return concise Markdown only."
                    " Do not imply release readiness or any production, routing, Git, repo-write, or release authority."
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        "temperature": 0,
        "max_tokens": 1200,
    }


def output_summary(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def with_codex_owned_outcome(data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_codex_owned_outcome(
        selected_path=str(data.get("selected_path", "")),
        validation_result=str(data.get("validation_result", "")),
        final_outcome=str(data.get("final_outcome", "")),
        fallback_used=data.get("fallback_used"),
        rework_required=data.get("rework_required"),
    )
    merged = dict(data)
    merged.update(normalized)
    return merged


def choice_aliases(choice: str) -> set[str]:
    mapping = {
        "prompt": {"prompt"},
        "local": {"local", "1", "codex"},
        "or": {"or", "2", "opr", "openrouter"},
    }
    return mapping[choice]


def fail_pre_wrapper(
    *,
    workflow_id: str,
    skill_id: str,
    final_outcome: str,
    selected_path: str,
    operator_message: str,
    validation_result: str,
    fallback_used: str = "YES",
    rework_required: str = "NO",
    or_model: str = "N_A",
) -> int:
    summary = with_codex_owned_outcome(
        {
            "workflow_id": workflow_id,
            "skill_id": skill_id,
            "selected_path": selected_path,
            "or_model": or_model,
            "validation_result": validation_result,
            "fallback_used": fallback_used,
            "rework_required": rework_required,
            "final_outcome": final_outcome,
            "operator_result_lines": [
                f"Ergebnis: {final_outcome}",
                "Tatsaechliche Kosten: nicht verfuegbar",
            ],
            "operator_message": operator_message,
        }
    )
    summary["operator_result_lines"].append(
        f"Codex-Status: {summary['codex_owned_outcome_status']}"
    )
    output_summary(summary)
    return 0


def eligibility_summary(
    *,
    workflow_id: str,
    skill_id: str,
    eligibility: dict[str, Any],
    final_outcome: str,
    selected_path: str = "codex_only_pre_wrapper",
    validation_result: str = "PASS",
) -> int:
    summary = with_codex_owned_outcome(
        {
            "workflow_id": workflow_id,
            "skill_id": skill_id,
            "selected_path": selected_path,
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "eligibility_message": eligibility["message"],
            "evidence_status": eligibility["evidence_status"],
            "or_model": eligibility["selected_or_model"],
            "validation_result": validation_result,
            "fallback_used": "YES",
            "rework_required": "NO" if validation_result == "PASS" else "YES",
            "final_outcome": final_outcome,
            "operator_result_lines": [
                f"Ergebnis: {eligibility['eligibility_result']}",
                "Tatsaechliche Kosten: nicht verfuegbar",
            ],
            "operator_message": eligibility["message"],
        }
    )
    summary["operator_result_lines"].append(
        f"Codex-Status: {summary['codex_owned_outcome_status']}"
    )
    output_summary(summary)
    return 0


def invoke_wrapper(
    config: dict[str, Any],
    session_dir: Path,
    request_body_source_path: Path,
    use_local_fixture: bool,
    local_fixture_response_path: Path | None,
) -> subprocess.CompletedProcess[str]:
    wrapper_path = REPO_ROOT / config["file_first_wrapper_path"]
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(wrapper_path),
        "-RunDirectory",
        str(session_dir),
        "-RequestBodyPath",
        str(request_body_source_path),
    ]
    if use_local_fixture:
        command.extend(
            [
                "-UseLocalFixture",
                "-LocalFixtureResponsePath",
                str(local_fixture_response_path),
            ]
        )
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY missing for live fixed OR invocation")
        command.extend(
            [
                "-AuthorizationBearer",
                f"Bearer {api_key}",
                "-HttpReferer",
                "https://github.com/pruvex/Janus-Projekt",
                "-XTitle",
                "Janus Codex Fixed OR Mini Skills",
            ]
        )
    return run_command(command, REPO_ROOT)


def parse_wrapper_outputs(session_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    response_body_path = session_dir / "response_body.json"
    response_summary_path = session_dir / "response_summary.json"
    if not response_body_path.exists():
        raise FileNotFoundError("response_body.json missing")
    if not response_summary_path.exists():
        raise FileNotFoundError("response_summary.json missing")
    return load_json(response_body_path), load_json(response_summary_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Operator-invoked fixed OR choice runner for mini documentation skills.")
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--normal-target-model", required=True)
    parser.add_argument("--task-intent", default="documentation_skill")
    parser.add_argument("--operator-choice", required=True)
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--session-call-count", type=int, default=1)
    parser.add_argument("--session-cost-so-far", type=float, default=0.0)
    parser.add_argument("--use-local-fixture", action="store_true")
    parser.add_argument("--local-fixture-response-path", type=Path, default=None)
    parser.add_argument("--governance-flag", action="store_true")
    args = parser.parse_args()

    config = load_json(args.config_path)
    normalized_choice = norm(args.operator_choice)
    if normalized_choice in choice_aliases("prompt"):
        args.operator_choice = "prompt"
    elif normalized_choice in choice_aliases("local"):
        args.operator_choice = "local"
    elif normalized_choice in choice_aliases("or"):
        args.operator_choice = "or"
    else:
        raise SystemExit("operator-choice must be one of: prompt, local/1/codex, or or/2/opr/openrouter")
    workflow_id = args.workflow_id or f"FIXED-OR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{args.skill_id}"

    eligibility = evaluate_doc_skill_fixed_or(
        skill_id=args.skill_id,
        normal_target_model=args.normal_target_model,
        task_intent=args.task_intent,
        governance_flag=args.governance_flag,
    )
    enabled_skills = config["enabled_skills"]
    if eligibility["eligibility_result"] == "OR_NOT_ELIGIBLE":
        return eligibility_summary(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            eligibility=eligibility,
            final_outcome="CODEX_ONLY_OR_NOT_ELIGIBLE",
        )
    if eligibility["eligibility_result"] == "OR_EVIDENCE_MISSING":
        return eligibility_summary(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            eligibility=eligibility,
            final_outcome="CODEX_ONLY_OR_EVIDENCE_MISSING",
        )

    skill_config = enabled_skills[args.skill_id]
    try:
        baseline_row = load_baseline_row(config, args.skill_id)
    except Exception as exc:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_BASELINE_METADATA_MISSING",
            selected_path="abort_pre_wrapper",
            operator_message=f"Baseline metadata missing before wrapper invocation: {exc}",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    operator_prompt = make_operator_prompt(args, config, baseline_row, skill_config, workflow_id)
    session_dir, session_jsonl_path, request_body_source_path = build_paths(config, workflow_id, args.skill_id)
    operator_prompt["eligibility_result"] = eligibility["eligibility_result"]
    operator_prompt["eligibility_reason_code"] = eligibility["reason_code"]
    operator_prompt["evidence_status"] = eligibility["evidence_status"]
    write_json(session_dir / "operator_choice_prompt.json", operator_prompt)

    estimated_or_cost_raw = baseline_row.get("estimated_or_cost")
    confidence_percent = baseline_row.get("cost_estimate_confidence_percent")
    if estimated_or_cost_raw is None:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_MISSING_ESTIMATE",
            selected_path="abort_pre_wrapper",
            operator_message="Estimated OR cost missing before wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    estimated_or_cost = float(estimated_or_cost_raw)
    if estimated_or_cost is None:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_MISSING_ESTIMATE",
            selected_path="abort_pre_wrapper",
            operator_message="Estimated OR cost missing before wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    if confidence_percent is None:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_MISSING_CONFIDENCE",
            selected_path="abort_pre_wrapper",
            operator_message="Confidence display missing before wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    if estimated_or_cost > float(config["per_call_cap_usd"]):
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_ESTIMATE_OVER_CAP",
            selected_path="abort_pre_wrapper",
            operator_message="Estimated cost exceeds per-call cap before wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    if args.session_cost_so_far + estimated_or_cost > float(config["session_cap_usd"]):
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_SESSION_CAP",
            selected_path="abort_pre_wrapper",
            operator_message="Estimated session cost would exceed bounded session cap.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    if args.session_call_count > int(config["max_or_calls_per_session"]):
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_SESSION_CALL_LIMIT",
            selected_path="abort_pre_wrapper",
            operator_message="Session call count exceeds bounded maximum before wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    if args.operator_choice == "prompt":
        summary = with_codex_owned_outcome(
            {
                "summary_header": "FIXED OR OPERATOR CHOICE",
                "workflow_id": workflow_id,
                "skill_id": args.skill_id,
                "selected_path": "operator_choice_pending",
                "eligibility_result": eligibility["eligibility_result"],
                "eligibility_reason_code": eligibility["reason_code"],
                "evidence_status": eligibility["evidence_status"],
                "choice_1": "Codex",
                "choice_2": "OR",
                "or_model": skill_config["selected_or_model"],
                "estimated_or_cost": estimated_or_cost,
                "operator_recommendation": operator_prompt["operator_recommendation"],
                "operator_recommendation_reason": operator_prompt["operator_recommendation_reason"],
                "cost_estimate_confidence_percent": baseline_row["cost_estimate_confidence_percent"],
                "cost_estimate_sample_count": baseline_row["cost_estimate_sample_count"],
                "cost_estimate_mean_abs_error_percent": baseline_row["cost_estimate_mean_abs_error_percent"],
                "cost_estimate_p50_error_percent": baseline_row["cost_estimate_p50_error_percent"],
                "cost_estimate_p90_error_percent": baseline_row["cost_estimate_p90_error_percent"],
                "per_call_cap_usd": config["per_call_cap_usd"],
                "session_cap_usd": config["session_cap_usd"],
                "validation_result": "PASS",
                "fallback_used": "NO",
                "rework_required": "NO",
                "final_outcome": "AWAITING_OPERATOR_CHOICE",
                "operator_prompt_lines": build_operator_prompt_lines(
                    selected_or_model=skill_config["selected_or_model"],
                    estimated_or_cost=estimated_or_cost,
                    cost_estimate_confidence_percent=float(baseline_row["cost_estimate_confidence_percent"]),
                    operator_recommendation=operator_prompt["operator_recommendation"],
                    operator_recommendation_reason=operator_prompt["operator_recommendation_reason"],
                ),
                "operator_message": (
                    "Eligible bounded mini documentation task detected. "
                    "Reply with 1 or 2 to continue. "
                    "No OR call has been made."
                ),
            }
        )
        output_summary(summary)
        return 0

    if args.operator_choice == "local":
        summary = with_codex_owned_outcome({
            "workflow_id": workflow_id,
            "skill_id": args.skill_id,
            "selected_path": "codex_only_operator_choice",
            "eligibility_result": eligibility["eligibility_result"],
            "eligibility_reason_code": eligibility["reason_code"],
            "evidence_status": eligibility["evidence_status"],
            "local_codex_option": "enabled",
            "or_option": "enabled_but_not_used",
            "or_model": skill_config["selected_or_model"],
            "validation_result": "PASS",
            "fallback_used": "YES",
            "rework_required": "NO",
            "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
            "operator_result_lines": [
                "Ergebnis: Codex lokal ausgewaehlt",
                "Tatsaechliche Kosten: 0.000000000",
            ],
            "operator_message": "Operator chose local Codex path. No OR call was made.",
        })
        summary["operator_result_lines"].append(
            f"Codex-Status: {summary['codex_owned_outcome_status']}"
        )
        write_json(session_dir / "operator_decision.json", summary)
        output_summary(summary)
        return 0

    request_body = build_request_body(args.skill_id, skill_config)
    write_json(request_body_source_path, request_body)
    start = time.time()
    wrapper_result = invoke_wrapper(
        config=config,
        session_dir=session_dir,
        request_body_source_path=request_body_source_path,
        use_local_fixture=args.use_local_fixture,
        local_fixture_response_path=args.local_fixture_response_path,
    )
    latency_ms = int(round((time.time() - start) * 1000))
    write_text(session_dir / "wrapper_command_stdout.txt", wrapper_result.stdout)
    write_text(session_dir / "wrapper_command_stderr.txt", wrapper_result.stderr)
    if wrapper_result.returncode != 0:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="CODEX_ONLY_WRAPPER_FAILURE",
            selected_path="codex_only_post_wrapper",
            operator_message="Wrapper invocation failed; returning to Codex-only path.",
            validation_result="FAIL",
            fallback_used="YES",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    try:
        response_body, response_summary = parse_wrapper_outputs(session_dir)
    except Exception as exc:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_RESPONSE_BODY_OR_SUMMARY_MISSING",
            selected_path="abort_post_wrapper",
            operator_message=str(exc),
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    generation_id = response_summary.get("generation_id")
    usage = response_summary.get("usage")
    finish_reason = response_summary.get("finish_reason")
    actual_or_cost = response_summary.get("actual_or_cost")
    if not generation_id:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_GENERATION_ID_MISSING",
            selected_path="abort_post_wrapper",
            operator_message="generation_id missing after wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    if not usage:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_USAGE_MISSING",
            selected_path="abort_post_wrapper",
            operator_message="usage missing and unrecoverable after wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    if actual_or_cost is None:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_ACTUAL_COST_MISSING",
            selected_path="abort_post_wrapper",
            operator_message="actual cost missing after wrapper invocation.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    if float(actual_or_cost) > float(config["per_call_cap_usd"]):
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_ACTUAL_COST_OVER_CAP",
            selected_path="abort_post_wrapper",
            operator_message="Actual cost exceeded per-call cap.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    if finish_reason == "length":
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_FINISH_REASON_LENGTH",
            selected_path="abort_post_wrapper",
            operator_message="finish_reason=length triggered OR path abort.",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )

    estimated_cost = float(baseline_row["estimated_or_cost"])
    estimation_error_percent = (
        ((float(actual_or_cost) - estimated_cost) / estimated_cost) * 100.0 if estimated_cost else 0.0
    )
    telemetry_row = {
        "workflow_id": workflow_id,
        "skill_id": args.skill_id,
        "routing_mode": "operator_invoked_fixed_or",
        "selected_path": "fixed_or_then_codex_validate",
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility["evidence_status"],
        "codex_default_model": args.normal_target_model,
        "or_model": skill_config["selected_or_model"],
        "estimated_prompt_tokens": baseline_row["estimated_prompt_tokens"],
        "estimated_completion_tokens": baseline_row["estimated_completion_tokens"],
        "estimated_or_cost": estimated_cost,
        "cost_estimate_confidence_percent": baseline_row["cost_estimate_confidence_percent"],
        "cost_estimate_sample_count": baseline_row["cost_estimate_sample_count"],
        "cost_estimate_mean_abs_error_percent": baseline_row["cost_estimate_mean_abs_error_percent"],
        "cost_estimate_p50_error_percent": baseline_row["cost_estimate_p50_error_percent"],
        "cost_estimate_p90_error_percent": baseline_row["cost_estimate_p90_error_percent"],
        "cost_estimate_basis": baseline_row["cost_estimate_basis"],
        "prompt_template_hash": baseline_row["prompt_template_hash"],
        "task_variant": skill_config["task_variant"],
        "price_snapshot_source": baseline_row["price_snapshot_source"],
        "price_snapshot_timestamp": baseline_row["price_snapshot_timestamp"],
        "actual_prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "actual_completion_tokens": int(usage.get("completion_tokens", 0)),
        "actual_reasoning_tokens": int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)),
        "actual_cached_tokens": int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)),
        "actual_or_cost": float(actual_or_cost),
        "generation_id": generation_id,
        "usage_source": "response_usage",
        "estimated_codex_effort": "low",
        "estimation_error_percent": round(estimation_error_percent, 2),
        "cost_delta_vs_codex_estimate": round(float(actual_or_cost) - estimated_cost, 8),
        "latency_ms": latency_ms,
        "validation_result": "PASS",
        "fallback_used": "NO",
        "rework_required": "NO",
        "final_outcome": "FIXED_OR_PASSED_LOCAL_VALIDATION",
        "reason_for_escalation": "",
        "quality_notes": (
            "Operator-invoked fixed OR path only. No Auto Router. "
            "Bounded local workflow evidence only; not production routing."
        ),
        "recommendation_signal": "OR_PREFERRED",
    }
    append_jsonl(session_jsonl_path, telemetry_row)
    hc_command = healthcheck_command(config, session_jsonl_path)
    hc_result = run_command(hc_command, REPO_ROOT)
    if hc_result.returncode != 0:
        return fail_pre_wrapper(
            workflow_id=workflow_id,
            skill_id=args.skill_id,
            final_outcome="ABORTED_HEALTHCHECK_INGESTION",
            selected_path="abort_post_wrapper",
            operator_message=hc_result.stderr.strip() or hc_result.stdout.strip() or "healthcheck ingestion failed",
            validation_result="FAIL",
            fallback_used="NO",
            rework_required="YES",
            or_model=skill_config["selected_or_model"],
        )
    hc_summary = json.loads(hc_result.stdout)
    write_json(session_dir / "healthcheck_summary.json", hc_summary)

    operator_summary = with_codex_owned_outcome({
        "summary_header": "FIXED OR MINI DOC SKILL SUMMARY",
        "workflow_id": workflow_id,
        "skill_id": args.skill_id,
        "selected_path": "fixed_or_then_codex_validate",
        "eligibility_result": eligibility["eligibility_result"],
        "eligibility_reason_code": eligibility["reason_code"],
        "evidence_status": eligibility["evidence_status"],
        "local_codex_option": "enabled",
        "or_option": "enabled",
        "or_model": skill_config["selected_or_model"],
        "estimated_or_cost": estimated_cost,
        "cost_estimate_confidence_percent": baseline_row["cost_estimate_confidence_percent"],
        "actual_or_cost": float(actual_or_cost),
        "finish_reason": finish_reason,
        "validation_result": "PASS",
        "fallback_used": "NO",
        "rework_required": "NO",
        "operator_result_lines": [
            f"Ergebnis: OR erfolgreich ({finish_reason})",
            f"Tatsaechliche Kosten: {float(actual_or_cost):.9f}",
        ],
        "session_jsonl_path": str(session_jsonl_path),
        "healthcheck_summary_path": str(session_dir / "healthcheck_summary.json"),
        "operator_message": "Accepted fixed-model OR row captured and ingested locally. No Auto Router used.",
    })
    operator_summary["operator_result_lines"].append(
        f"Codex-Status: {operator_summary['codex_owned_outcome_status']}"
    )
    write_json(session_dir / "operator_summary.json", operator_summary)
    output_summary(operator_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
