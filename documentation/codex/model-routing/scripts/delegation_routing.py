#!/usr/bin/env python3
"""Cost-aware delegation manifest helpers.

This module validates the operator-facing Codex / OpenRouter / Cursor routing
artifacts and builds gate summaries. It is intentionally deterministic and does
not invoke external agents.
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
VALID_RECOMMENDED_BACKENDS = set(BACKENDS) | {"deterministic_apply"}
NEVER_DELEGATE_LANES = {"live_test_execution", "diamond_retest_audit"}
NEVER_DELEGATE_PIPELINE_MODES = {
    "LIVE_TEST_EXECUTION",
    "DIAMOND_RETEST_AUDIT",
    "TESTSPEC_TO_TEST_PLAN",
    "EXECUTION_VALIDATION",
}
DEFAULT_COMPOSER_PERCENT_HINTS = {
    "assist_only": "0.2-0.4 % Monatskontingent",
    "review_only": "0.2-0.4 % Monatskontingent",
    "proposal_first": "0.3-0.6 % Monatskontingent",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    return load_json(path)


def load_task_list(path: Path = DEFAULT_TASK_LIST_PATH) -> dict[str, Any]:
    return load_json(path)


def load_operator_choices(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    gate = manifest.get("operator_gate")
    if not isinstance(gate, dict):
        return {}
    choices = gate.get("choices")
    return choices if isinstance(choices, dict) else {}


def is_backend_enabled(lane: dict[str, Any], backend: str) -> bool:
    config = lane.get(backend)
    return isinstance(config, dict) and config.get("enabled") is True


def deterministic_apply_config(lane_id: str, lane: dict[str, Any]) -> dict[str, Any] | None:
    if lane_id != "execution_write_apply_candidate":
        return None
    config = lane.get("deterministic_apply_worker")
    return config if isinstance(config, dict) and config.get("enabled") is True else None


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


def cursor_config(lane: dict[str, Any]) -> dict[str, Any]:
    config = lane.get("cursor")
    return config if isinstance(config, dict) else {}


def lane_cursor_pool_config(lane: dict[str, Any], pool: str) -> dict[str, Any]:
    config = cursor_config(lane)
    pool_key = "composer_pool" if pool == "auto_composer" else "api_pool"
    pool_config = config.get(pool_key)
    return pool_config if isinstance(pool_config, dict) else {}


def lane_cursor_pool_enabled(lane: dict[str, Any], pool: str) -> bool:
    if not is_backend_enabled(lane, "cursor"):
        return False
    return lane_cursor_pool_config(lane, pool).get("enabled") is True


def option2_mode(lane_id: str, lane: dict[str, Any]) -> str:
    if deterministic_apply_config(lane_id, lane) is not None:
        return "deterministic_apply"
    return "openrouter"


def lane_cursor_model(lane: dict[str, Any], manifest: dict[str, Any], pool: str) -> str | None:
    policy = manifest.get("cursor_model_policy")
    if not isinstance(policy, dict):
        policy = {}
    if pool == "auto_composer":
        composer_policy = policy.get("composer_pool") if isinstance(policy.get("composer_pool"), dict) else {}
        pool_config = lane_cursor_pool_config(lane, pool)
        for key in ("model", "default_model"):
            value = pool_config.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for key in ("default_model", "alternate_model"):
            value = composer_policy.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
    api_policy = policy.get("api_pool") if isinstance(policy.get("api_pool"), dict) else {}
    api_models = api_policy.get("models") if isinstance(api_policy.get("models"), dict) else {}
    pool_config = lane_cursor_pool_config(lane, pool)
    value = pool_config.get("model")
    if isinstance(value, str) and value.strip():
        return value.strip()
    fallback_key = pool_config.get("policy_model_key")
    if isinstance(fallback_key, str):
        api_value = api_models.get(fallback_key)
        if isinstance(api_value, str) and api_value.strip():
            return api_value.strip()
    return None


def lane_model(
    lane: dict[str, Any],
    task: dict[str, Any] | None,
    backend: str,
    manifest: dict[str, Any] | None = None,
    pool: str | None = None,
) -> str | None:
    lane_id = lane.get("__lane_id")
    if backend == "cursor":
        if isinstance(lane_id, str):
            deterministic_config = deterministic_apply_config(lane_id, lane)
            if deterministic_config is not None and pool is None:
                value = deterministic_config.get("model") or deterministic_config.get("display_label")
                if isinstance(value, str) and value.strip():
                    return value.strip()
        if manifest is not None and pool is not None:
            return lane_cursor_model(lane, manifest, pool)
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

    operator_choices = load_operator_choices(manifest or {})
    if operator_choices:
        for choice_id, config in operator_choices.items():
            aliases = {
                str(choice_id).lower(),
                str(config.get("label") or "").strip().lower(),
                str(config.get("backend") or "").strip().lower(),
            }
            pool = str(config.get("pool") or "").strip().lower()
            if pool == "auto_composer":
                aliases.update({"cursor", "cursor-composer", "cursor_composer", "composer", "composer-2.5"})
            elif pool == "api":
                aliases.update({"4", "cursor-api", "cursor_api", "api"})
            elif str(config.get("backend")) == "openrouter":
                aliases.update({"2", "or", "opr", "openrouter"})
            elif str(config.get("backend")) == "codex":
                aliases.update({"1", "codex", "local"})
            if choice in aliases:
                return str(choice_id)

    if choice in {"1", "codex", "local"}:
        return "1"
    if choice in {"2", "openrouter", "or", "opr"}:
        return "2"
    if choice in {"3", "cursor", "cursor-composer", "cursor_composer", "composer", "composer-2.5"}:
        return "3"
    if choice in {"4", "cursor-api", "cursor_api", "api"}:
        return "4"
    raise ValueError(
        "operator-choice must be prompt, 1/codex/local, 2/openrouter/or/opr, 3/cursor/composer, or 4/cursor-api/api"
    )


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


def keep_external_options_visible_on_negative_roi(lane: dict[str, Any]) -> bool:
    return str(lane.get("negative_roi_visibility_mode") or "").strip().lower() == "keep_visible_non_recommended"


def visible_backends(task: dict[str, Any] | None, lane_id: str, lane: dict[str, Any], roi: dict[str, Any]) -> list[str]:
    if is_never_delegate(task, lane_id):
        return ["codex"]
    if roi.get("status") == "NEGATIVE" and not keep_external_options_visible_on_negative_roi(lane):
        return ["codex"]
    visible = ["codex"]
    if option2_mode(lane_id, lane) == "deterministic_apply" or is_backend_enabled(lane, "openrouter"):
        visible.append("openrouter" if option2_mode(lane_id, lane) == "openrouter" else "cursor")
    if lane_cursor_pool_enabled(lane, "auto_composer") or lane_cursor_pool_enabled(lane, "api"):
        if "cursor" not in visible:
            visible.append("cursor")
    if is_backend_enabled(lane, "openrouter") and "openrouter" not in visible:
        visible.append("openrouter")
    return visible


def composer_percent_hint(lane: dict[str, Any]) -> str:
    cursor = cursor_config(lane)
    value = cursor.get("composer_percent_hint")
    if isinstance(value, str) and value.strip():
        return value.strip()
    mode = str(cursor.get("mode") or "assist_only")
    return DEFAULT_COMPOSER_PERCENT_HINTS.get(mode, "0.2-0.8 % Monatskontingent")


def estimate_run_cost_usd(model: str | None, manifest: dict[str, Any]) -> float | None:
    if not model:
        return None
    policy = manifest.get("cursor_model_policy")
    if not isinstance(policy, dict):
        return None
    pricing = policy.get("pricing_per_million_tokens")
    assumptions = policy.get("default_token_assumptions")
    if not isinstance(pricing, dict) or not isinstance(assumptions, dict):
        return None
    model_pricing = pricing.get(model)
    if not isinstance(model_pricing, dict):
        return None
    input_rate = model_pricing.get("input_usd")
    output_rate = model_pricing.get("output_usd")
    input_tokens = assumptions.get("input_tokens")
    output_tokens = assumptions.get("output_tokens")
    if not all(isinstance(value, (int, float)) for value in (input_rate, output_rate, input_tokens, output_tokens)):
        return None
    return (float(input_tokens) / 1_000_000 * float(input_rate)) + (
        float(output_tokens) / 1_000_000 * float(output_rate)
    )


def format_usd_hint(value: float | None) -> str | None:
    if value is None:
        return None
    if value < 0.01:
        return f"~${value:.4f} +/-30%"
    if value < 0.1:
        return f"~${value:.3f} +/-30%"
    return f"~${value:.2f} +/-30%"


def recommended_backend(task: dict[str, Any] | None, lane_id: str, lane: dict[str, Any], roi: dict[str, Any]) -> str:
    visible = visible_backends(task, lane_id, lane, roi)
    if roi.get("status") == "NEGATIVE":
        return "codex"
    deterministic_config = deterministic_apply_config(lane_id, lane)
    if isinstance(deterministic_config, dict) and deterministic_config.get("recommended") is True and "cursor" in visible:
        return "deterministic_apply"
    for pool in ("auto_composer", "api"):
        pool_config = lane_cursor_pool_config(lane, pool)
        if pool_config.get("enabled") is True and pool_config.get("recommended") is True and "cursor" in visible:
            return "cursor"
    task_recommended = task.get("recommended_backend") if isinstance(task, dict) else None
    if isinstance(task_recommended, str) and task_recommended in visible:
        return task_recommended
    openrouter_config = lane.get("openrouter")
    if isinstance(openrouter_config, dict) and openrouter_config.get("recommended") is True and "openrouter" in visible:
        return "openrouter"
    return "codex"


def recommended_choice_id(
    manifest: dict[str, Any],
    task: dict[str, Any] | None,
    lane_id: str,
    lane: dict[str, Any],
    roi: dict[str, Any],
) -> str:
    visible_choice_ids = {"1"}
    if is_never_delegate(task, lane_id):
        return "1"
    if roi.get("status") == "NEGATIVE":
        return "1"
    if deterministic_apply_config(lane_id, lane) is not None:
        visible_choice_ids.add("2")
    else:
        if is_backend_enabled(lane, "openrouter"):
            visible_choice_ids.add("2")
        if lane_cursor_pool_enabled(lane, "auto_composer"):
            visible_choice_ids.add("3")
        if lane_cursor_pool_enabled(lane, "api"):
            visible_choice_ids.add("4")
    if deterministic_apply_config(lane_id, lane) is not None and "2" in visible_choice_ids:
        return "2"
    if lane_cursor_pool_config(lane, "auto_composer").get("recommended") is True and "3" in visible_choice_ids:
        return "3"
    if lane_cursor_pool_config(lane, "api").get("recommended") is True and "4" in visible_choice_ids:
        return "4"
    if recommended_backend(task, lane_id, lane, roi) == "openrouter" and "2" in visible_choice_ids:
        return "2"
    if recommended_backend(task, lane_id, lane, roi) == "cursor":
        if "3" in visible_choice_ids:
            return "3"
        if "4" in visible_choice_ids:
            return "4"
    return "1"


def visible_operator_choices(
    manifest: dict[str, Any],
    task: dict[str, Any] | None,
    lane_id: str,
    lane: dict[str, Any],
    roi: dict[str, Any],
) -> list[dict[str, Any]]:
    if is_never_delegate(task, lane_id) or (
        roi.get("status") == "NEGATIVE" and not keep_external_options_visible_on_negative_roi(lane)
    ):
        codex_model = lane_model(lane, task, "codex", manifest)
        return [
            {
                "choice_id": "1",
                "label": "Codex",
                "backend": "codex",
                "pool": None,
                "model": codex_model,
                "cost_hint": "Codex-Tokens",
                "cost_estimate_usd_static": None,
                "recommended": True,
                "operator_gate_line": "1 = Codex",
            }
        ]

    operator_choices = load_operator_choices(manifest)
    recommended_choice = recommended_choice_id(manifest, task, lane_id, lane, roi)
    codex_model = lane_model(lane, task, "codex", manifest)
    visible: list[dict[str, Any]] = [
        {
            "choice_id": "1",
            "label": "Codex",
            "backend": "codex",
            "pool": None,
            "model": codex_model,
            "cost_hint": "Codex-Tokens",
            "cost_estimate_usd_static": None,
            "recommended": recommended_choice == "1",
            "operator_gate_line": "1 = Codex",
        }
    ]

    if deterministic_apply_config(lane_id, lane) is not None:
        config = deterministic_apply_config(lane_id, lane) or {}
        visible.append(
            {
                "choice_id": "2",
                "label": str(config.get("display_label") or "Deterministic Apply"),
                "backend": "deterministic_apply",
                "pool": None,
                "model": str(config.get("model") or "deterministic_local_apply"),
                "cost_hint": "Lokaler Apply-Schritt",
                "cost_estimate_usd_static": None,
                "recommended": True,
                "operator_gate_line": "2 = Deterministic Apply",
            }
        )
        return visible

    if is_backend_enabled(lane, "openrouter"):
        openrouter = lane.get("openrouter") if isinstance(lane.get("openrouter"), dict) else {}
        or_model = lane_model(lane, task, "openrouter", manifest)
        or_cost = openrouter.get("prompt_estimated_or_cost")
        visible.append(
            {
                "choice_id": "2",
                "label": str((operator_choices.get("2") or {}).get("label") or "OpenRouter"),
                "backend": "openrouter",
                "pool": None,
                "model": or_model,
                "cost_hint": format_usd_hint(float(or_cost)) if isinstance(or_cost, (int, float)) else None,
                "cost_estimate_usd_static": float(or_cost) if isinstance(or_cost, (int, float)) else None,
                "recommended": recommended_choice == "2",
                "operator_gate_line": "2 = OpenRouter",
            }
        )

    if lane_cursor_pool_enabled(lane, "auto_composer"):
        model = lane_cursor_model(lane, manifest, "auto_composer")
        visible.append(
            {
                "choice_id": "3",
                "label": str((operator_choices.get("3") or {}).get("label") or "Cursor Composer"),
                "backend": "cursor",
                "pool": "auto_composer",
                "model": model,
                "cost_hint": composer_percent_hint(lane),
                "cost_estimate_usd_static": estimate_run_cost_usd(model, manifest),
                "recommended": recommended_choice == "3",
                "operator_gate_line": "3 = Cursor Composer",
            }
        )

    if lane_cursor_pool_enabled(lane, "api"):
        model = lane_cursor_model(lane, manifest, "api")
        estimate = estimate_run_cost_usd(model, manifest)
        visible.append(
            {
                "choice_id": "4",
                "label": str((operator_choices.get("4") or {}).get("label") or "Cursor API"),
                "backend": "cursor",
                "pool": "api",
                "model": model,
                "cost_hint": format_usd_hint(estimate),
                "cost_estimate_usd_static": estimate,
                "recommended": recommended_choice == "4",
                "operator_gate_line": "4 = Cursor API",
            }
        )

    return visible


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
    visible_choices = visible_operator_choices(manifest, task, lane_id, lane, roi)
    gate_lines = [choice["operator_gate_line"] for choice in visible_choices]
    recommended_choice = next((choice["choice_id"] for choice in visible_choices if choice["recommended"]), "1")
    models: dict[str, str] = {}
    for choice in visible_choices:
        model = choice.get("model")
        if not isinstance(model, str) or not model:
            continue
        backend = str(choice["backend"])
        pool = choice.get("pool")
        if backend == "cursor" and pool == "auto_composer":
            models["cursor_composer"] = model
        elif backend == "cursor" and pool == "api":
            models["cursor_api"] = model
        elif backend == "deterministic_apply":
            models["cursor"] = model
        else:
            models[backend] = model
    return {
        "manifest_version": manifest.get("manifest_version"),
        "operator_gate_version": ((manifest.get("operator_gate") or {}).get("version")),
        "status": "OPERATOR_CHOICE_READY",
        "lane_id": lane_id,
        "task_id": task.get("task_id") if isinstance(task, dict) else task_id,
        "skill": lane.get("skill"),
        "lane_class": lane.get("lane_class"),
        "operator_gate_lines": gate_lines,
        "visible_backends": visible,
        "visible_choices": visible_choices,
        "recommended_backend": recommendation,
        "recommended_choice": recommended_choice,
        "models": models,
        "roi": roi,
        "negative_roi_visibility_mode": lane.get("negative_roi_visibility_mode"),
        "negative_roi_visibility_reason": lane.get("negative_roi_visibility_reason"),
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

    operator_choices = load_operator_choices(manifest)
    if not operator_choices:
        issues.append("manifest.operator_gate.choices must be a non-empty object")
    else:
        for required in ("1", "2", "3", "4"):
            if required not in operator_choices:
                issues.append(f"operator gate missing choice {required}")

    cursor_policy = manifest.get("cursor_model_policy")
    if not isinstance(cursor_policy, dict):
        issues.append("manifest.cursor_model_policy must be an object")
    else:
        for required_key in ("composer_pool", "api_pool", "pricing_per_million_tokens", "default_token_assumptions"):
            if not isinstance(cursor_policy.get(required_key), dict):
                issues.append(f"cursor_model_policy.{required_key} must be an object")

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
            for backend in ("cursor", "openrouter"):
                if is_backend_enabled(lane, backend):
                    issues.append(f"never-delegate lane {lane_id} must disable {backend}")
        if is_backend_enabled(lane, "cursor"):
            for pool in ("auto_composer", "api"):
                config = lane_cursor_pool_config(lane, pool)
                if config and config.get("enabled") is True:
                    model = lane_cursor_model({**lane, "__lane_id": lane_id}, manifest, pool)
                    if not isinstance(model, str) or not model.strip():
                        issues.append(f"lane {lane_id} cursor {pool} must resolve to a model")

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
        if recommended not in VALID_RECOMMENDED_BACKENDS:
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
