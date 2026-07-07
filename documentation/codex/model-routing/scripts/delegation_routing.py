#!/usr/bin/env python3
"""Tri-modal delegation manifest helpers.

This module is intentionally local and deterministic. It validates the
operator-facing Codex / Cursor / OpenRouter routing artifacts and builds gate
summaries, but it does not call external agents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DEFAULT_MANIFEST_PATH = MODEL_ROUTING_DIR / "config" / "delegation_routing_manifest.json"
DEFAULT_TASK_LIST_PATH = MODEL_ROUTING_DIR / "config" / "delegation_task_list_2026-07-05.json"

BACKENDS = ("codex", "cursor", "openrouter")
EXTERNAL_BACKENDS = ("cursor", "openrouter")
NEVER_DELEGATE_LANES = {"live_test_execution", "diamond_retest_audit"}
NEVER_DELEGATE_PIPELINE_MODES = {
    "LIVE_TEST_EXECUTION",
    "DIAMOND_RETEST_AUDIT",
    "TESTSPEC_TO_TEST_PLAN",
    "EXECUTION_VALIDATION",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    return load_json(path)


def load_task_list(path: Path = DEFAULT_TASK_LIST_PATH) -> dict[str, Any]:
    return load_json(path)


def is_backend_enabled(lane: dict[str, Any], backend: str) -> bool:
    config = lane.get(backend)
    return isinstance(config, dict) and config.get("enabled") is True


def deterministic_apply_config(lane_id: str, lane: dict[str, Any]) -> dict[str, Any] | None:
    if lane_id != "execution_write_apply_candidate":
        return None
    config = lane.get("deterministic_apply_worker")
    return config if isinstance(config, dict) and config.get("enabled") is True else None


def option2_mode(lane_id: str, lane: dict[str, Any]) -> str | None:
    if deterministic_apply_config(lane_id, lane) is not None:
        return "deterministic_apply"
    if is_backend_enabled(lane, "cursor"):
        return "cursor"
    return None


def lane_model(lane: dict[str, Any], task: dict[str, Any] | None, backend: str) -> str | None:
    lane_id = lane.get("__lane_id")
    if backend == "cursor" and isinstance(lane_id, str):
        deterministic_config = deterministic_apply_config(lane_id, lane)
        if deterministic_config is not None:
            value = deterministic_config.get("model") or deterministic_config.get("display_label")
            if isinstance(value, str) and value.strip():
                return value.strip()
    task_models = task.get("models") if isinstance(task, dict) else None
    if isinstance(task_models, dict):
        task_backend_model = task_models.get(backend)
        if isinstance(task_backend_model, dict):
            value = task_backend_model.get("model")
            if isinstance(value, str) and value.strip():
                return value.strip()
    config = lane.get(backend)
    if isinstance(config, dict):
        value = config.get("model") or config.get("default_model")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_operator_choice(value: str, manifest: dict[str, Any] | None = None) -> str:
    choice = str(value or "").strip().lower()
    if choice in {"prompt", ""}:
        return "prompt"

    backends = (manifest or {}).get("backends") if isinstance(manifest, dict) else None
    if isinstance(backends, dict):
        for backend, config in backends.items():
            aliases = config.get("operator_aliases") if isinstance(config, dict) else None
            if isinstance(aliases, list) and choice in {str(alias).lower() for alias in aliases}:
                return str(backend)

    if choice in {"1", "codex", "local"}:
        return "codex"
    if choice in {"2", "cursor"}:
        return "cursor"
    if choice in {"3", "openrouter", "or", "opr"}:
        return "openrouter"
    raise ValueError("operator-choice must be prompt, 1/codex/local, 2/cursor, or 3/openrouter/or/opr")


def tasks_by_id(task_list: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = task_list.get("tasks") if isinstance(task_list, dict) else None
    if not isinstance(tasks, list):
        return {}
    return {str(task.get("task_id")): task for task in tasks if isinstance(task, dict) and task.get("task_id")}


def find_task(task_list: dict[str, Any], *, task_id: str | None = None, lane_id: str | None = None) -> dict[str, Any] | None:
    tasks = task_list.get("tasks") if isinstance(task_list, dict) else None
    if not isinstance(tasks, list):
        return None
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task_id and task.get("task_id") == task_id:
            return task
        if lane_id and task.get("lane_id") == lane_id:
            return task
    return None


def find_lane(manifest: dict[str, Any], lane_id: str) -> dict[str, Any] | None:
    lanes = manifest.get("lanes") if isinstance(manifest, dict) else None
    if not isinstance(lanes, dict):
        return None
    lane = lanes.get(lane_id)
    return lane if isinstance(lane, dict) else None


def evaluate_roi(
    *,
    estimated_saved_tokens: int | None,
    estimated_overhead_tokens: int | None,
    minimum_net_saved_tokens: int,
) -> dict[str, Any]:
    if estimated_saved_tokens is None or estimated_overhead_tokens is None:
        return {
            "status": "UNKNOWN",
            "estimated_codex_saved_tokens": estimated_saved_tokens,
            "estimated_delegation_overhead_tokens": estimated_overhead_tokens,
            "minimum_net_codex_saved_tokens": minimum_net_saved_tokens,
            "net_codex_saved_tokens": None,
        }
    net_saved = int(estimated_saved_tokens) - int(estimated_overhead_tokens)
    return {
        "status": "POSITIVE" if net_saved >= int(minimum_net_saved_tokens) else "NEGATIVE",
        "estimated_codex_saved_tokens": int(estimated_saved_tokens),
        "estimated_delegation_overhead_tokens": int(estimated_overhead_tokens),
        "minimum_net_codex_saved_tokens": int(minimum_net_saved_tokens),
        "net_codex_saved_tokens": net_saved,
    }


def effective_roi(task: dict[str, Any] | None, lane: dict[str, Any], overrides: dict[str, int | None]) -> dict[str, Any]:
    minimum = overrides.get("minimum_net_codex_saved_tokens")
    if minimum is None:
        minimum = task.get("minimum_net_codex_saved_tokens") if isinstance(task, dict) else None
    if minimum is None:
        minimum = lane.get("minimum_net_codex_saved_tokens", 0)

    saved = overrides.get("estimated_codex_saved_tokens")
    if saved is None and isinstance(task, dict):
        saved = task.get("estimated_codex_saved_tokens")
    overhead = overrides.get("estimated_delegation_overhead_tokens")
    if overhead is None and isinstance(task, dict):
        overhead = task.get("estimated_delegation_overhead_tokens")
    if overhead is None:
        overhead = lane.get("estimated_delegation_overhead_tokens")

    return evaluate_roi(
        estimated_saved_tokens=int(saved) if saved is not None else None,
        estimated_overhead_tokens=int(overhead) if overhead is not None else None,
        minimum_net_saved_tokens=int(minimum or 0),
    )


def is_never_delegate(task: dict[str, Any] | None, lane_id: str | None) -> bool:
    if lane_id in NEVER_DELEGATE_LANES:
        return True
    pipeline_mode = task.get("pipeline_mode") if isinstance(task, dict) else None
    return str(pipeline_mode or "") in NEVER_DELEGATE_PIPELINE_MODES


def visible_backends(task: dict[str, Any] | None, lane_id: str, lane: dict[str, Any], roi: dict[str, Any]) -> list[str]:
    if is_never_delegate(task, lane_id):
        return ["codex"]
    if roi.get("status") == "NEGATIVE":
        return ["codex"]
    visible = ["codex"]
    if option2_mode(lane_id, lane) is not None:
        visible.append("cursor")
    if is_backend_enabled(lane, "openrouter"):
        visible.append("openrouter")
    return visible


def recommended_backend(task: dict[str, Any] | None, lane_id: str, lane: dict[str, Any], roi: dict[str, Any]) -> str:
    visible = visible_backends(task, lane_id, lane, roi)
    deterministic_config = deterministic_apply_config(lane_id, lane)
    if isinstance(deterministic_config, dict) and deterministic_config.get("recommended") is True and "cursor" in visible:
        return "deterministic_apply"
    task_recommended = task.get("recommended_backend") if isinstance(task, dict) else None
    if isinstance(task_recommended, str) and task_recommended in visible:
        return task_recommended
    for backend in EXTERNAL_BACKENDS:
        config = lane.get(backend)
        if isinstance(config, dict) and config.get("recommended") is True and backend in visible:
            return backend
    return "codex"


def build_gate(
    *,
    manifest: dict[str, Any],
    task_list: dict[str, Any],
    lane_id: str,
    task_id: str | None = None,
    estimated_codex_saved_tokens: int | None = None,
    estimated_delegation_overhead_tokens: int | None = None,
    minimum_net_codex_saved_tokens: int | None = None,
) -> dict[str, Any]:
    lane = find_lane(manifest, lane_id)
    if lane is None:
        raise ValueError(f"Unknown lane_id: {lane_id}")
    lane = dict(lane)
    lane["__lane_id"] = lane_id
    task = find_task(task_list, task_id=task_id, lane_id=lane_id)
    roi = effective_roi(
        task,
        lane,
        {
            "estimated_codex_saved_tokens": estimated_codex_saved_tokens,
            "estimated_delegation_overhead_tokens": estimated_delegation_overhead_tokens,
            "minimum_net_codex_saved_tokens": minimum_net_codex_saved_tokens,
        },
    )
    visible = visible_backends(task, lane_id, lane, roi)
    recommendation = recommended_backend(task, lane_id, lane, roi)
    gate_lines = ["1 = Codex"]
    if "cursor" in visible:
        gate_lines.append(
            "2 = Deterministic Apply"
            if option2_mode(lane_id, lane) == "deterministic_apply"
            else "2 = Cursor"
        )
    if "openrouter" in visible:
        gate_lines.append("3 = OpenRouter")
    return {
        "manifest_version": manifest.get("manifest_version"),
        "status": "OPERATOR_CHOICE_READY",
        "lane_id": lane_id,
        "task_id": task.get("task_id") if isinstance(task, dict) else task_id,
        "skill": lane.get("skill"),
        "lane_class": lane.get("lane_class"),
        "operator_gate_lines": gate_lines,
        "visible_backends": visible,
        "recommended_backend": recommendation,
        "models": {backend: lane_model(lane, task, backend) for backend in visible},
        "roi": roi,
        "codex_final_owner": True,
        "no_production_routing": manifest.get("status") == "OPERATOR_ROUTING_NOT_PRODUCTION_ROUTING",
    }


def validate_manifest_and_task_list(manifest: dict[str, Any], task_list: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if manifest.get("status") != "OPERATOR_ROUTING_NOT_PRODUCTION_ROUTING":
        issues.append("manifest.status must be OPERATOR_ROUTING_NOT_PRODUCTION_ROUTING")
    backends = manifest.get("backends")
    if not isinstance(backends, dict):
        issues.append("manifest.backends must be an object")
        backends = {}
    for backend in BACKENDS:
        config = backends.get(backend)
        if not isinstance(config, dict):
            issues.append(f"missing backend config: {backend}")
        elif not isinstance(config.get("operator_aliases"), list) or not config.get("operator_aliases"):
            issues.append(f"backend {backend} must declare operator_aliases")

    lanes = manifest.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        issues.append("manifest.lanes must be a non-empty object")
        lanes = {}
    for lane_id, lane in lanes.items():
        if not isinstance(lane, dict):
            issues.append(f"lane {lane_id} must be an object")
            continue
        if lane.get("skill") is None:
            issues.append(f"lane {lane_id} missing skill")
        if lane.get("lane_class") is None:
            issues.append(f"lane {lane_id} missing lane_class")
        if not is_backend_enabled(lane, "codex"):
            issues.append(f"lane {lane_id} must keep codex enabled")
        if lane_id in NEVER_DELEGATE_LANES:
            for backend in EXTERNAL_BACKENDS:
                if is_backend_enabled(lane, backend):
                    issues.append(f"never-delegate lane {lane_id} must disable {backend}")

    tasks = task_list.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        issues.append("task_list.tasks must be a non-empty list")
        tasks = []
    seen_task_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            issues.append("task entry must be an object")
            continue
        task_id = str(task.get("task_id") or "")
        if not task_id:
            issues.append("task missing task_id")
        elif task_id in seen_task_ids:
            issues.append(f"duplicate task_id: {task_id}")
        seen_task_ids.add(task_id)
        lane_id = task.get("lane_id")
        if lane_id is not None and lane_id not in lanes:
            issues.append(f"task {task_id} references unknown lane_id: {lane_id}")
        recommended = task.get("recommended_backend")
        if recommended not in BACKENDS and recommended != "deterministic_apply":
            issues.append(f"task {task_id} has invalid recommended_backend: {recommended}")
        if is_never_delegate(task, str(lane_id) if lane_id else None):
            if recommended != "codex":
                issues.append(f"never-delegate task {task_id} must recommend codex")
            if task.get("operator_override_allowed") is not False:
                issues.append(f"never-delegate task {task_id} must disallow operator override")

    return {
        "validation_result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "lane_count": len(lanes),
        "task_count": len(tasks),
    }
