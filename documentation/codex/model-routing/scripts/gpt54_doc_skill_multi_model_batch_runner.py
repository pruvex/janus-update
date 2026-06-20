#!/usr/bin/env python3
"""Run a bounded multi-skill multi-model GPT-5.4 documentation batch.

This helper is for non-production OpenRouter evidence only. It uses the
file-first wrapper, then evaluates saved artifacts locally via the hardened
postcheck helper.
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
WRAPPER_PATH = MODEL_ROUTING_DIR / "scripts" / "or_file_first_capture_wrapper.ps1"
POSTCHECK_PATH = MODEL_ROUTING_DIR / "scripts" / "gpt54_doc_skill_batch_postcheck.py"
HEALTHCHECK_PATH = (
    REPO_ROOT / "documentation" / "codex" / "skills" / "janus-health-check" / "scripts" / "health_snapshot.py"
)
PRICE_INVENTORY_PATH = REPO_ROOT / "documentation" / "codex" / "openrouter-delegation" / "model_price_inventory_2026-06-12.json"

SKILL_CONFIG = {
    "DOC-SKILL-002": {
        "fixture_dir": REPO_ROOT / "documentation" / "codex" / "model-routing" / "live-eval" / "DOC-SKILL-002-GPT54-LIVE-EVAL-001",
        "task_variant": "scoring_report_summary_batch",
    },
    "DOC-SKILL-006": {
        "fixture_dir": REPO_ROOT / "documentation" / "codex" / "model-routing" / "live-eval" / "DOC-SKILL-006-GPT54-LIVE-EVAL-001",
        "task_variant": "markdown_formatting_batch",
    },
    "DOC-SKILL-008": {
        "fixture_dir": REPO_ROOT / "documentation" / "codex" / "model-routing" / "live-eval" / "DOC-SKILL-008-GPT54-LIVE-EVAL-001",
        "task_variant": "changelog_summary_batch",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def run(command: list[str], cwd: Path, timeout: int = 120000) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False, timeout=timeout)


def safe_slug(text: str) -> str:
    return text.replace("/", "-").replace(":", "-")


def get_inventory_model(model_id: str) -> dict[str, Any]:
    models = load_json(PRICE_INVENTORY_PATH)["models"]
    for row in models:
        if row.get("id") == model_id:
            return row
    raise KeyError(f"Model not found in inventory: {model_id}")


def estimate_cost(model_id: str) -> float:
    row = get_inventory_model(model_id)
    value = (((row.get("profile_costs") or {}).get("docs_summary") or {}).get("openrouter_estimated_cost_usd"))
    if value is None:
        raise ValueError(f"docs_summary estimate missing for {model_id}")
    return float(value)


def build_request_body(skill_id: str, model_id: str, skill_override: dict[str, Any] | None = None) -> dict[str, Any]:
    skill_override = skill_override or {}
    fixture_dir = SKILL_CONFIG[skill_id]["fixture_dir"]
    prompt_name = str(skill_override.get("prompt_file") or "prompt.md")
    prompt = (fixture_dir / prompt_name).read_text(encoding="utf-8-sig").strip()
    acceptance = (fixture_dir / "acceptance_criteria.md").read_text(encoding="utf-8-sig").strip()
    blocked = (fixture_dir / "blocked_authority_checks.md").read_text(encoding="utf-8-sig").strip()
    sanitized = load_json(fixture_dir / "input.sanitized.json")
    max_tokens = int(skill_override.get("max_tokens") or 1200)
    user_content = (
        prompt
        + "\n\nAcceptance criteria:\n"
        + acceptance
        + "\n\nBlocked authority checks:\n"
        + blocked
        + "\n\nSanitized input JSON:\n"
        + json.dumps(sanitized, ensure_ascii=False, indent=2)
    )
    return {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are assisting with {skill_id}. "
                    "Use only the sanitized input. Return concise Markdown only. "
                    "Do not imply release readiness or any production, routing, Git, repo-write, release, or policy authority."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }


def invoke_wrapper(run_dir: Path, request_body_source_path: Path) -> subprocess.CompletedProcess[str]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(WRAPPER_PATH),
        "-RunDirectory",
        str(run_dir),
        "-RequestBodyPath",
        str(request_body_source_path),
        "-AuthorizationBearer",
        f"Bearer {api_key}",
        "-HttpReferer",
        "https://github.com/pruvex/Janus-Projekt",
        "-XTitle",
        "Janus Codex GPT54 Doc Skill Batch",
    ]
    return run(command, REPO_ROOT, timeout=180000)


def postcheck(skill_id: str, response_body: Path, response_summary: Path, write_json_path: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(POSTCHECK_PATH),
        "--skill-id",
        skill_id,
        "--response-body",
        str(response_body),
        "--response-summary",
        str(response_summary),
        "--write-json",
        str(write_json_path),
    ]
    result = run(command, REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def build_telemetry_row(
    *,
    workflow_id: str,
    skill_id: str,
    model_id: str,
    est: float,
    latency_ms: int,
    response_summary: dict[str, Any],
    postcheck_result: dict[str, Any],
) -> dict[str, Any]:
    usage = response_summary.get("usage")
    actual_or_cost = float(response_summary.get("actual_or_cost") or 0.0)
    accepted = bool(postcheck_result["accepted_for_local_batch_use"])
    return {
        "workflow_id": workflow_id,
        "skill_id": skill_id,
        "routing_mode": "fixed_model_5skill_batch",
        "selected_path": "fixed_or_then_local_postcheck",
        "codex_default_model": "5.4 medium",
        "or_model": model_id,
        "estimated_prompt_tokens": 0,
        "estimated_completion_tokens": 1200,
        "estimated_or_cost": est,
        "cost_estimate_confidence_percent": 35,
        "cost_estimate_sample_count": 0,
        "cost_estimate_mean_abs_error_percent": 0.0,
        "cost_estimate_p50_error_percent": 0.0,
        "cost_estimate_p90_error_percent": 0.0,
        "cost_estimate_basis": f"{model_id}+{skill_id}+docs_summary_inventory_estimate",
        "prompt_template_hash": f"sha256:{skill_id.lower()}-gpt54-batch-v3",
        "task_variant": SKILL_CONFIG[skill_id]["task_variant"],
        "price_snapshot_source": "documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json",
        "price_snapshot_timestamp": datetime.now().astimezone().isoformat(),
        "actual_prompt_tokens": int((usage or {}).get("prompt_tokens", 0)),
        "actual_completion_tokens": int((usage or {}).get("completion_tokens", 0)),
        "actual_reasoning_tokens": int((((usage or {}).get("completion_tokens_details") or {}).get("reasoning_tokens", 0))),
        "actual_cached_tokens": int((((usage or {}).get("prompt_tokens_details") or {}).get("cached_tokens", 0))),
        "actual_or_cost": actual_or_cost,
        "generation_id": response_summary.get("generation_id"),
        "usage_source": "response_usage" if usage else "fallback_estimate",
        "estimated_codex_effort": "medium",
        "estimation_error_percent": round(((actual_or_cost - est) / est) * 100.0, 2) if est else 0.0,
        "cost_delta_vs_codex_estimate": round(actual_or_cost - est, 8),
        "latency_ms": latency_ms,
        "validation_result": postcheck_result["postcheck_validation_result"],
        "fallback_used": "NO",
        "rework_required": "NO" if accepted else "YES",
        "final_outcome": (
            "FIXED_OR_POSTCHECK_ACCEPTED"
            if accepted
            else "FIXED_OR_CAPTURED_BUT_POSTCHECK_FAILED"
        ),
        "reason_for_escalation": postcheck_result["content_evaluation"].get("reason_for_escalation", ""),
        "quality_notes": json.dumps(postcheck_result["content_evaluation"]["checks"], ensure_ascii=False, sort_keys=True),
        "recommendation_signal": "OR_PREFERRED" if accepted else "MANUAL_REVIEW",
    }


def build_postcheck_failure_result(
    *,
    skill_id: str,
    response_summary: dict[str, Any],
    error_text: str,
) -> dict[str, Any]:
    return {
        "skill_id": skill_id,
        "generation_id": response_summary.get("generation_id"),
        "model": response_summary.get("model"),
        "finish_reason": response_summary.get("finish_reason"),
        "actual_or_cost": response_summary.get("actual_or_cost"),
        "common_checks": {
            "generation_id_present": bool(response_summary.get("generation_id")),
            "usage_present": bool(response_summary.get("usage")),
            "actual_cost_present": response_summary.get("actual_or_cost") is not None,
            "finish_reason_not_length": str(response_summary.get("finish_reason", "")).lower() != "length",
        },
        "content_evaluation": {
            "validation_result": "FAIL",
            "reason_for_escalation": "postcheck_error",
            "checks": {
                "postcheck_exception": error_text,
            },
        },
        "postcheck_validation_result": "FAIL",
        "accepted_for_local_batch_use": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bounded GPT-5.4 documentation skill multi-model batch.")
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--telemetry-jsonl", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--skills", nargs="+", required=True)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--skill-overrides-json", type=Path, default=None)
    parser.add_argument("--per-call-cap", type=float, default=0.10)
    parser.add_argument("--total-cap", type=float, default=2.0)
    args = parser.parse_args()

    skill_overrides = load_json(args.skill_overrides_json) if args.skill_overrides_json else {}
    existing_rows = load_jsonl(args.telemetry_jsonl)
    existing_pairs = {
        (str(row.get("skill_id")), str(row.get("or_model")))
        for row in existing_rows
    }
    total_estimated = 0.0
    total_actual = sum(float(row.get("actual_or_cost") or 0.0) for row in existing_rows)
    summary_rows: list[dict[str, Any]] = [
        {
            "skill_id": str(row.get("skill_id")),
            "or_model": str(row.get("or_model")),
            "actual_or_cost": float(row.get("actual_or_cost") or 0.0),
            "finish_reason": row.get("finish_reason"),
            "validation_result": row.get("validation_result"),
            "accepted_for_local_batch_use": row.get("final_outcome") == "FIXED_OR_POSTCHECK_ACCEPTED",
        }
        for row in existing_rows
    ]

    for skill_id in args.skills:
        if skill_id not in SKILL_CONFIG:
            raise SystemExit(f"Unsupported skill_id: {skill_id}")

    for model_id in args.models:
        est = estimate_cost(model_id)
        if est > args.per_call_cap:
            raise SystemExit(f"Estimated cost over per-call cap for {model_id}: {est}")
        total_estimated += est * len(args.skills)

    if total_estimated > args.total_cap:
        raise SystemExit(f"Estimated total cost over batch cap: {total_estimated}")

    for skill_id in args.skills:
        for model_id in args.models:
            if (skill_id, model_id) in existing_pairs:
                continue
            est = estimate_cost(model_id)
            skill_slug = safe_slug(skill_id.lower())
            model_slug = safe_slug(model_id)
            run_dir = args.run_root / skill_slug / model_slug
            run_dir.mkdir(parents=True, exist_ok=True)
            request_body_source_path = run_dir / "request_body_source.json"
            write_json(request_body_source_path, build_request_body(skill_id, model_id, skill_overrides.get(skill_id)))

            response_summary_path = run_dir / "response_summary.json"
            response_body_path = run_dir / "response_body.json"
            latency_ms = 0

            if not response_summary_path.exists():
                start = time.time()
                wrapper_result = invoke_wrapper(run_dir, request_body_source_path)
                latency_ms = int(round((time.time() - start) * 1000))

                if wrapper_result.returncode != 0:
                    raise SystemExit(f"Wrapper failed for {skill_id} {model_id}: {wrapper_result.stderr or wrapper_result.stdout}")

            response_summary = load_json(response_summary_path)
            actual_or_cost = float(response_summary.get("actual_or_cost") or 0.0)
            total_actual += actual_or_cost
            if total_actual > args.total_cap:
                raise SystemExit(f"Actual total cost over batch cap after {skill_id} {model_id}: {total_actual}")

            local_postcheck_path = run_dir / "local_postcheck.json"
            try:
                if not response_body_path.exists():
                    raise FileNotFoundError(f"response body missing: {response_body_path}")
                postcheck_result = postcheck(skill_id, response_body_path, response_summary_path, local_postcheck_path)
            except Exception as exc:
                postcheck_result = build_postcheck_failure_result(
                    skill_id=skill_id,
                    response_summary=response_summary,
                    error_text=str(exc),
                )
                write_json(local_postcheck_path, postcheck_result)

            row = build_telemetry_row(
                workflow_id=args.workflow_id,
                skill_id=skill_id,
                model_id=model_id,
                est=est,
                latency_ms=latency_ms,
                response_summary=response_summary,
                postcheck_result=postcheck_result,
            )
            append_jsonl(args.telemetry_jsonl, row)
            existing_pairs.add((skill_id, model_id))
            summary_rows.append(
                {
                    "skill_id": skill_id,
                    "or_model": model_id,
                    "actual_or_cost": actual_or_cost,
                    "finish_reason": response_summary.get("finish_reason"),
                    "validation_result": row["validation_result"],
                    "accepted_for_local_batch_use": postcheck_result["accepted_for_local_batch_use"],
                }
            )

    healthcheck = run(
        [
            sys.executable,
            str(HEALTHCHECK_PATH),
            "--repo",
            str(REPO_ROOT),
            "--or-telemetry-jsonl",
            str(args.telemetry_jsonl),
        ],
        REPO_ROOT,
    )
    if healthcheck.returncode != 0:
        raise SystemExit(healthcheck.stderr or healthcheck.stdout)

    result = {
        "workflow_id": args.workflow_id,
        "skills": args.skills,
        "models": args.models,
        "record_count": len(summary_rows),
        "estimated_total_cost": round(total_estimated, 8),
        "actual_total_cost": round(total_actual, 8),
        "rows": summary_rows,
        "healthcheck_summary": json.loads(healthcheck.stdout),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
