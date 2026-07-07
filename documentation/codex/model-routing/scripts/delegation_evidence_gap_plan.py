#!/usr/bin/env python3
"""Build a local next-evidence plan from delegation calibration output.

This helper is intentionally review-only. It consumes the already-rendered
local calibration report plus routing metadata, then ranks the remaining
evidence gaps. It never calls Cursor, OpenRouter, or any live runner.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from delegation_routing import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_TASK_LIST_PATH,
    NEVER_DELEGATE_LANES,
    NEVER_DELEGATE_PIPELINE_MODES,
    find_task,
    load_manifest,
    load_task_list,
)


DEFAULT_CALIBRATION_REPORT_PATH = (
    Path(__file__).resolve().parents[4]
    / "development"
    / "openrouter-skill-tests"
    / "delegation_routing_calibration_report_2026-07-06.json"
)

DEFAULT_OUTPUT_JSON_PATH = (
    Path(__file__).resolve().parents[4]
    / "development"
    / "openrouter-skill-tests"
    / "delegation_evidence_gap_plan_2026-07-06.json"
)

DEFAULT_OUTPUT_MD_PATH = (
    Path(__file__).resolve().parents[4]
    / "development"
    / "openrouter-skill-tests"
    / "delegation_evidence_gap_plan_2026-07-06.md"
)


ACTION_BY_STATUS = {
    "NO_EVIDENCE": "create_shadow_fixture_then_request_one_live_run",
    "HIGH_VARIANCE_REVIEW_SCOPE": "split_or_deprioritize_no_default_tuning",
    "NEW_ESTIMATE_NEEDED": "review_before_manifest_tuning",
    "UNDER_ESTIMATED": "tune_only_with_bounded_evidence",
    "OVER_ESTIMATED": "review_only_no_urgent_tuning",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_never_delegate(lane_id: str, task: dict[str, Any] | None) -> bool:
    if lane_id in NEVER_DELEGATE_LANES:
        return True
    pipeline_mode = task.get("pipeline_mode") if isinstance(task, dict) else None
    return str(pipeline_mode or "") in NEVER_DELEGATE_PIPELINE_MODES


def _priority(
    *,
    lane_id: str,
    task: dict[str, Any] | None,
    status: str,
    sample_count: int,
) -> int:
    if _is_never_delegate(lane_id, task):
        return 0
    recommended_backend = task.get("recommended_backend") if isinstance(task, dict) else None
    saved = _as_int(task.get("estimated_codex_saved_tokens")) if isinstance(task, dict) else None
    overhead = _as_int(task.get("estimated_delegation_overhead_tokens")) if isinstance(task, dict) else None
    net_saved = (saved - overhead) if saved is not None and overhead is not None else 0

    if status == "HIGH_VARIANCE_REVIEW_SCOPE":
        return 65
    if status == "NO_EVIDENCE":
        if recommended_backend == "deterministic_apply":
            return 20
        if recommended_backend == "cursor":
            return 100 if net_saved >= 15000 else 90
        if recommended_backend == "openrouter":
            return 80 if net_saved >= 7000 else 70
        return 30
    if status in {"UNDER_ESTIMATED", "NEW_ESTIMATE_NEEDED"}:
        return 55 + min(sample_count, 5)
    if status == "OVER_ESTIMATED":
        return 25
    return 10


def _next_action(lane_id: str, task: dict[str, Any] | None, status: str) -> str:
    if _is_never_delegate(lane_id, task):
        return "keep_codex_owned_never_delegate"
    recommended_backend = task.get("recommended_backend") if isinstance(task, dict) else None
    if status == "NO_EVIDENCE" and recommended_backend == "deterministic_apply":
        return "keep_deterministic_apply_contract_and_avoid_live_agent_planning"
    if status == "NO_EVIDENCE" and recommended_backend == "cursor":
        return "build_or_reuse_cursor_shadow_fixture_then_request_explicit_live_cursor_smoke"
    if status == "NO_EVIDENCE" and recommended_backend == "openrouter":
        return "build_bounded_input_package_then_request_explicit_live_openrouter_smoke"
    return ACTION_BY_STATUS.get(status, "no_action_required")


def _rationale(lane_id: str, task: dict[str, Any] | None, status: str) -> str:
    if _is_never_delegate(lane_id, task):
        return "Lane is Codex-owned by policy and should not become delegated evidence work."
    recommended_backend = task.get("recommended_backend") if isinstance(task, dict) else "unknown"
    if status == "NO_EVIDENCE":
        if recommended_backend == "deterministic_apply":
            return "This lane is already intentionally sealed to a deterministic local worker, so missing agent evidence is not a reason to reopen Cursor or OpenRouter planning."
        return f"{recommended_backend} is configured as the preferred backend, but no bounded local evidence was found."
    if status == "HIGH_VARIANCE_REVIEW_SCOPE":
        return "Existing evidence is too mixed to tune automatically; separate transport/runtime evidence before changing defaults."
    if status in {"UNDER_ESTIMATED", "NEW_ESTIMATE_NEEDED", "OVER_ESTIMATED"}:
        return "The calibration report indicates a default mismatch that needs a human bounded-evidence review."
    return "The current calibration status does not require immediate evidence work."


def build_plan(
    *,
    calibration_report: dict[str, Any],
    manifest: dict[str, Any],
    task_list: dict[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    lanes = manifest.get("lanes")
    if not isinstance(lanes, dict):
        raise ValueError("manifest.lanes must be an object")

    entries: list[dict[str, Any]] = []
    for summary in calibration_report.get("lane_summaries", []):
        if not isinstance(summary, dict):
            continue
        lane_id = str(summary.get("lane_id") or "")
        if not lane_id:
            continue
        status = str(summary.get("status") or "UNKNOWN")
        if status == "ALIGNED":
            continue
        task = find_task(task_list, task_id=summary.get("task_id"), lane_id=lane_id)
        sample_count = _as_int(summary.get("sample_count")) or 0
        priority = _priority(lane_id=lane_id, task=task, status=status, sample_count=sample_count)
        entries.append(
            {
                "lane_id": lane_id,
                "task_id": summary.get("task_id") or (task.get("task_id") if isinstance(task, dict) else None),
                "skill": summary.get("skill") or (lanes.get(lane_id, {}).get("skill") if isinstance(lanes.get(lane_id), dict) else None),
                "status": status,
                "sample_count": sample_count,
                "recommended_backend": task.get("recommended_backend") if isinstance(task, dict) else summary.get("recommended_backend"),
                "pipeline_mode": task.get("pipeline_mode") if isinstance(task, dict) else None,
                "priority": priority,
                "next_action": _next_action(lane_id, task, status),
                "live_requires_explicit_approval": priority > 0,
                "do_not_tune_manifest_yet": status in {"NO_EVIDENCE", "HIGH_VARIANCE_REVIEW_SCOPE"},
                "rationale": _rationale(lane_id, task, status),
            }
        )

    entries.sort(key=lambda item: (-int(item["priority"]), str(item["lane_id"])))
    return {
        "generated_at": generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "report_type": "delegation_evidence_gap_plan",
        "source_calibration_report_type": calibration_report.get("report_type"),
        "manifest_path": str(DEFAULT_MANIFEST_PATH),
        "task_list_path": str(DEFAULT_TASK_LIST_PATH),
        "entry_count": len(entries),
        "live_call_policy": "No Cursor or OpenRouter live calls are authorized by this plan. Live runs require explicit operator approval.",
        "manifest_write_policy": "This plan is review-only and must not auto-change routing defaults.",
        "entries": entries,
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Delegation Evidence Gap Plan",
        "",
        f"- Generated at: `{plan['generated_at']}`",
        f"- Entry count: `{plan['entry_count']}`",
        f"- Live call policy: {plan['live_call_policy']}",
        f"- Manifest write policy: {plan['manifest_write_policy']}",
        "",
        "| Priority | Lane | Task | Backend | Status | Action |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for entry in plan.get("entries", []):
        lines.append(
            "| {priority} | {lane} | {task} | {backend} | {status} | {action} |".format(
                priority=entry["priority"],
                lane=entry["lane_id"],
                task=entry.get("task_id") or "-",
                backend=entry.get("recommended_backend") or "-",
                status=entry["status"],
                action=entry["next_action"],
            )
        )

    for entry in plan.get("entries", []):
        lines.extend(
            [
                "",
                f"## {entry['lane_id']}",
                "",
                f"- Task: `{entry.get('task_id') or '-'}`",
                f"- Skill: `{entry.get('skill') or '-'}`",
                f"- Pipeline mode: `{entry.get('pipeline_mode') or '-'}`",
                f"- Recommended backend: `{entry.get('recommended_backend') or '-'}`",
                f"- Calibration status: `{entry['status']}`",
                f"- Sample count: `{entry['sample_count']}`",
                f"- Priority: `{entry['priority']}`",
                f"- Next action: `{entry['next_action']}`",
                f"- Live requires explicit approval: `{entry['live_requires_explicit_approval']}`",
                f"- Do not tune manifest yet: `{entry['do_not_tune_manifest_yet']}`",
                f"- Rationale: {entry['rationale']}",
            ]
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-report", type=Path, default=DEFAULT_CALIBRATION_REPORT_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASK_LIST_PATH)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan(
        calibration_report=_load_json(args.calibration_report),
        manifest=load_manifest(args.manifest),
        task_list=load_task_list(args.tasks),
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(plan), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
