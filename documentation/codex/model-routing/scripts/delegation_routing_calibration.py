#!/usr/bin/env python3
"""Local calibration helper for tri-modal delegation routing cost defaults.

This helper is intentionally local and deterministic. It reads the current
manifest and task list, scans bounded local evidence files from known
delegation run directories, and renders a non-binding calibration report. It
does not call external agents and never rewrites routing files automatically.
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from delegation_routing import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_TASK_LIST_PATH,
    MODEL_ROUTING_DIR,
    find_task,
    load_manifest,
    load_task_list,
)


EVIDENCE_GLOBS_BY_LANE: dict[str, list[str]] = {
    "documentation_draft_review": [
        "bounded-dispatch-runs/WF-DOC-DRAFT-GATE-CHECK-*/dispatcher_result.json",
    ],
    "quickchange_patch_review": [
        "direct-or-runs/BOUNDED-QUICKCHANGE-OR-LIVE-*/operator_summary.json",
    ],
    "backlog_handoff_review": [
        "backlog-handoff-review-runs/*/validation_summary.json",
    ],
    "backlog_prioritization_review": [
        "backlog-prioritization-review-runs/*/operator_choice_delegated.json",
    ],
    "backlog_intake_review": [
        "backlog-intake-review-runs/*/operator_choice_delegated.json",
    ],
    "debug_hypothesis_review": [
        "debug-review-runs/WF-DEBUG-EVERYDAY-*/operator_choice_delegated.json",
        "debug-review-runs/WF-DEBUG-EVERYDAY-OR-*/operator_choice_delegated.json",
    ],
    "test_result_triage_review": [
        "test-triage-runs/WF-TRIAGE-EVERYDAY-*/operator_choice_delegated.json",
    ],
    "spec_generator_review": [
        "spec-generator-review-runs/*/validation_summary.json",
    ],
    "spec_normalizer_review": [
        "spec-normalizer-runs/*/response_summary.json",
    ],
    "spec_review": [
        "spec-review-runs/*/validation_summary.json",
    ],
    "spec_to_task_review": [
        "spec-to-task-runs/*/validation_summary.json",
    ],
    "task_breakdown_review": [
        "task-breakdown-runs/*/validation_summary.json",
    ],
    "precheck_review": [
        "precheck-review-runs/*/response_summary.json",
    ],
    "execution_patch_candidate": [
        "bounded-dispatch-runs/WF-EXEC-EVERYDAY-OR-*/dispatcher_result.json",
        "execution-direct-or-runs/*/validation_summary.json",
    ],
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_evidence_record(path: Path) -> dict[str, Any] | None:
    data = _load_json(path)
    actual_cost = _float_or_none(data.get("actual_or_cost"))
    if actual_cost is None:
        usage = data.get("usage")
        if isinstance(usage, dict):
            actual_cost = _float_or_none(usage.get("cost"))
    if actual_cost is None:
        return None

    model = data.get("selected_or_model") or data.get("model")
    workflow_id = data.get("workflow_id") or path.parent.name
    confidence = _float_or_none(data.get("cost_estimate_confidence_percent"))
    return {
        "workflow_id": str(workflow_id),
        "actual_or_cost": actual_cost,
        "selected_or_model": str(model) if model else None,
        "cost_estimate_confidence_percent": confidence,
        "source_path": str(path),
    }


def collect_lane_evidence(
    lane_id: str,
    *,
    model_routing_dir: Path = MODEL_ROUTING_DIR,
    evidence_globs: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    patterns = (evidence_globs or EVIDENCE_GLOBS_BY_LANE).get(lane_id, [])
    records: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for pattern in patterns:
        for path in sorted(model_routing_dir.glob(pattern)):
            resolved = str(path.resolve())
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            record = extract_evidence_record(path)
            if record is not None:
                records.append(record)
    return records


def _round_cost(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 8)


def _suggest_confidence(
    *,
    sample_count: int,
    configured_estimate: float | None,
    observed_mean: float | None,
    observed_min: float | None,
    observed_max: float | None,
    configured_confidence: float | None,
) -> int | None:
    if sample_count <= 0:
        return int(configured_confidence) if configured_confidence is not None else None
    if sample_count == 1:
        baseline = 65
        if configured_confidence is not None:
            baseline = max(baseline, min(int(configured_confidence), 75))
        return baseline

    spread = 0.0
    if observed_max and observed_min is not None and observed_max > 0:
        spread = max(0.0, (observed_max - observed_min) / observed_max)

    confidence = 85 if spread <= 0.15 else 75 if spread <= 0.35 else 60
    if configured_estimate and observed_mean:
        estimate_error = abs(configured_estimate - observed_mean) / observed_mean if observed_mean else 0.0
        if estimate_error <= 0.15:
            confidence = min(90, confidence + 5)
        elif estimate_error >= 0.75:
            confidence = max(50, confidence - 10)
    return confidence


def summarize_lane(
    lane_id: str,
    lane: dict[str, Any],
    task: dict[str, Any] | None,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    openrouter = lane.get("openrouter") if isinstance(lane, dict) else {}
    if not isinstance(openrouter, dict):
        openrouter = {}

    configured_estimate = _float_or_none(openrouter.get("prompt_estimated_or_cost"))
    configured_confidence = _float_or_none(openrouter.get("prompt_cost_estimate_confidence_percent"))
    task_minimum = task.get("minimum_net_codex_saved_tokens") if isinstance(task, dict) else None
    lane_minimum = lane.get("minimum_net_codex_saved_tokens") if isinstance(lane, dict) else None
    overhead = task.get("estimated_delegation_overhead_tokens") if isinstance(task, dict) else None
    if overhead is None:
        overhead = lane.get("estimated_delegation_overhead_tokens")

    actuals = [record["actual_or_cost"] for record in evidence if record["actual_or_cost"] > 0]
    sample_count = len(actuals)
    observed_min = min(actuals) if actuals else None
    observed_max = max(actuals) if actuals else None
    observed_mean = statistics.mean(actuals) if actuals else None
    observed_median = statistics.median(actuals) if actuals else None

    suggested_estimate = None
    status = "NO_EVIDENCE"
    if actuals:
        high_variance = bool(
            sample_count >= 4
            and observed_median
            and observed_max
            and observed_max / observed_median >= 5
        )
        if high_variance:
            observed_anchor = max(observed_mean or 0.0, observed_median or 0.0)
            suggested_estimate = _round_cost(observed_anchor * 1.1)
            status = "HIGH_VARIANCE_REVIEW_SCOPE"
        else:
            observed_anchor = max(observed_mean or 0.0, observed_max or 0.0)
            suggested_estimate = _round_cost(observed_anchor * 1.05)
            if configured_estimate is None:
                status = "NEW_ESTIMATE_NEEDED"
            else:
                lower_bound = (observed_max or 0.0) * 0.9
                upper_bound = (observed_max or 0.0) * 1.35
                if configured_estimate < lower_bound:
                    status = "UNDER_ESTIMATED"
                elif configured_estimate > upper_bound:
                    status = "OVER_ESTIMATED"
                else:
                    status = "ALIGNED"

    suggested_confidence = _suggest_confidence(
        sample_count=sample_count,
        configured_estimate=configured_estimate,
        observed_mean=observed_mean,
        observed_min=observed_min,
        observed_max=observed_max,
        configured_confidence=configured_confidence,
    )

    return {
        "lane_id": lane_id,
        "task_id": task.get("task_id") if isinstance(task, dict) else None,
        "skill": lane.get("skill"),
        "recommended_backend": task.get("recommended_backend") if isinstance(task, dict) else None,
        "configured_prompt_estimated_or_cost": _round_cost(configured_estimate),
        "configured_confidence_percent": int(configured_confidence) if configured_confidence is not None else None,
        "minimum_net_codex_saved_tokens": task_minimum if task_minimum is not None else lane_minimum,
        "estimated_delegation_overhead_tokens": overhead,
        "sample_count": sample_count,
        "observed_actual_or_cost_min": _round_cost(observed_min),
        "observed_actual_or_cost_max": _round_cost(observed_max),
        "observed_actual_or_cost_mean": _round_cost(observed_mean),
        "observed_actual_or_cost_median": _round_cost(observed_median),
        "suggested_prompt_estimated_or_cost": suggested_estimate,
        "suggested_confidence_percent": suggested_confidence,
        "status": status,
        "evidence_records": evidence,
    }


def build_report(
    *,
    manifest: dict[str, Any],
    task_list: dict[str, Any],
    model_routing_dir: Path = MODEL_ROUTING_DIR,
    evidence_globs: dict[str, list[str]] | None = None,
    lane_filter: set[str] | None = None,
) -> dict[str, Any]:
    lanes = manifest.get("lanes")
    if not isinstance(lanes, dict):
        raise ValueError("manifest.lanes must be an object")

    summaries: list[dict[str, Any]] = []
    for lane_id, lane in sorted(lanes.items()):
        if lane_filter and lane_id not in lane_filter:
            continue
        if not isinstance(lane, dict):
            continue
        task = find_task(task_list, lane_id=lane_id)
        evidence = collect_lane_evidence(
            lane_id,
            model_routing_dir=model_routing_dir,
            evidence_globs=evidence_globs,
        )
        summaries.append(summarize_lane(lane_id, lane, task, evidence))

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "manifest_path": str(DEFAULT_MANIFEST_PATH),
        "task_list_path": str(DEFAULT_TASK_LIST_PATH),
        "lane_count": len(summaries),
        "report_type": "delegation_routing_calibration",
        "lane_summaries": summaries,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Delegation Routing Calibration Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Lane count: `{report['lane_count']}`",
        "- Purpose: compare configured OpenRouter routing defaults against bounded local evidence only",
        "",
        "| Lane | Task | Samples | Configured | Observed max | Suggested | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for summary in report.get("lane_summaries", []):
        lines.append(
            "| {lane} | {task} | {samples} | {configured} | {observed} | {suggested} | {status} |".format(
                lane=summary["lane_id"],
                task=summary.get("task_id") or "-",
                samples=summary["sample_count"],
                configured=_format_cost(summary.get("configured_prompt_estimated_or_cost")),
                observed=_format_cost(summary.get("observed_actual_or_cost_max")),
                suggested=_format_cost(summary.get("suggested_prompt_estimated_or_cost")),
                status=summary["status"],
            )
        )

    for summary in report.get("lane_summaries", []):
        lines.extend(
            [
                "",
                f"## {summary['lane_id']}",
                "",
                f"- Task: `{summary.get('task_id') or '-'}`",
                f"- Skill: `{summary.get('skill') or '-'}`",
                f"- Recommended backend: `{summary.get('recommended_backend') or '-'}`",
                f"- Configured estimate: `{_format_cost(summary.get('configured_prompt_estimated_or_cost'))}`",
                f"- Configured confidence: `{summary.get('configured_confidence_percent') if summary.get('configured_confidence_percent') is not None else '-'}`",
                f"- Sample count: `{summary['sample_count']}`",
                f"- Observed min/mean/max: `{_format_cost(summary.get('observed_actual_or_cost_min'))}` / `{_format_cost(summary.get('observed_actual_or_cost_mean'))}` / `{_format_cost(summary.get('observed_actual_or_cost_max'))}`",
                f"- Suggested estimate: `{_format_cost(summary.get('suggested_prompt_estimated_or_cost'))}`",
                f"- Suggested confidence: `{summary.get('suggested_confidence_percent') if summary.get('suggested_confidence_percent') is not None else '-'}`",
                f"- Status: `{summary['status']}`",
            ]
        )
        if summary["evidence_records"]:
            lines.append("- Evidence:")
            for record in summary["evidence_records"]:
                lines.append(
                    f"  - `{record['workflow_id']}` via `{record['source_path']}` -> `{_format_cost(record['actual_or_cost'])}`"
                )
        else:
            lines.append("- Evidence: none collected from the bounded local lane patterns")

    return "\n".join(lines) + "\n"


def _format_cost(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.8f}".rstrip("0").rstrip(".")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASK_LIST_PATH)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--lane", action="append", dest="lanes", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    task_list = load_task_list(args.tasks)
    lane_filter = set(args.lanes) if args.lanes else None
    report = build_report(
        manifest=manifest,
        task_list=task_list,
        lane_filter=lane_filter,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
