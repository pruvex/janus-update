#!/usr/bin/env python3
"""Shared bounded OR worker eligibility helpers."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
MODEL_ROUTING_DIR = REPO_ROOT / "documentation" / "codex" / "model-routing"
DEFAULT_ELIGIBILITY_CONFIG_PATH = (
    MODEL_ROUTING_DIR / "config" / "bounded_or_worker_eligibility_2026-06-17.json"
)
DEFAULT_BUDGET_PROFILE_CONFIG_PATH = (
    MODEL_ROUTING_DIR / "config" / "or_task_budget_profiles_2026-06-19.json"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_budget_profile(profile_name: str, config_path: Path) -> dict[str, Any] | None:
    config = load_json(config_path)
    return (config.get("profiles") or {}).get(profile_name)


def norm(text: str) -> str:
    return text.strip().lower()


def _invalid_estimated_cost_result(
    *,
    subject_id: str,
    budget_profile_name: str,
    budget_profile: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    return {
        **_base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="productive_dev_workhorse_path",
            subject_id=subject_id,
            reason_code="ESTIMATED_COST_INVALID",
            message=message,
        ),
        "budget_profile": budget_profile_name,
        "per_call_cap_usd": float(budget_profile["per_call_cap_usd"]),
        "session_cap_usd": float(budget_profile["session_cap_usd"]),
    }


def _base_result(
    *,
    result: str,
    subject_type: str,
    subject_id: str,
    reason_code: str,
    message: str,
    evidence_status: str = "N_A",
    selected_or_model: str | None = None,
) -> dict[str, Any]:
    return {
        "eligibility_result": result,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "reason_code": reason_code,
        "message": message,
        "evidence_status": evidence_status,
        "selected_or_model": selected_or_model or "N_A",
    }


def model_matches(normal_target_model: str, expected_tokens: list[str]) -> bool:
    check = norm(normal_target_model)
    return any(token in check for token in expected_tokens)


def evaluate_doc_skill_fixed_or(
    *,
    skill_id: str,
    normal_target_model: str,
    task_intent: str,
    governance_flag: bool,
    config_path: Path = DEFAULT_ELIGIBILITY_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_json(config_path)["doc_skill_fixed_or"]
    skill_entry = config["skills"].get(skill_id)
    if skill_entry is None:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="doc_skill_fixed_or",
            subject_id=skill_id,
            reason_code="SKILL_NOT_ALLOWED",
            message="Skill is outside the explicitly allowed bounded OR worker set.",
        )
    if governance_flag:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="doc_skill_fixed_or",
            subject_id=skill_id,
            reason_code="GOVERNANCE_BOUNDARY",
            message="Governance boundary detected before OR eligibility gate.",
            evidence_status=skill_entry.get("evidence_status", "UNKNOWN"),
            selected_or_model=skill_entry.get("selected_or_model"),
        )
    if norm(task_intent) != norm(config["required_task_intent"]):
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="doc_skill_fixed_or",
            subject_id=skill_id,
            reason_code="TASK_INTENT_MISMATCH",
            message="Task intent drifted outside the bounded documentation-skill OR contract.",
            evidence_status=skill_entry.get("evidence_status", "UNKNOWN"),
            selected_or_model=skill_entry.get("selected_or_model"),
        )
    if not model_matches(normal_target_model, config["normal_target_model_match"]):
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="doc_skill_fixed_or",
            subject_id=skill_id,
            reason_code="NORMAL_TARGET_MODEL_MISMATCH",
            message="Normal target model does not match the bounded OR worker contract.",
            evidence_status=skill_entry.get("evidence_status", "UNKNOWN"),
            selected_or_model=skill_entry.get("selected_or_model"),
        )
    evidence_status = skill_entry.get("evidence_status", "UNKNOWN")
    if evidence_status != "LIVE_EVIDENCE_CONFIRMED":
        return _base_result(
            result="OR_EVIDENCE_MISSING",
            subject_type="doc_skill_fixed_or",
            subject_id=skill_id,
            reason_code="EVIDENCE_NOT_CONFIRMED",
            message="Skill is listed but does not yet have confirmed bounded OR evidence.",
            evidence_status=evidence_status,
            selected_or_model=skill_entry.get("selected_or_model"),
        )
    return _base_result(
        result="OR_ALLOWED",
        subject_type="doc_skill_fixed_or",
        subject_id=skill_id,
        reason_code="ELIGIBILITY_CONFIRMED",
        message="Bounded OR worker eligibility confirmed for this documentation skill.",
        evidence_status=evidence_status,
        selected_or_model=skill_entry.get("selected_or_model"),
    )


def evaluate_dispatch_task_class(
    *,
    task_class: str,
    config_path: Path = DEFAULT_ELIGIBILITY_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_json(config_path)["dispatcher_task_classes"]
    task_entry = config.get(task_class)
    if task_entry is None:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="dispatcher_task_class",
            subject_id=task_class,
            reason_code="TASK_CLASS_NOT_ALLOWED",
            message="Task class is outside the shared bounded OR worker contract.",
        )
    evidence_status = task_entry.get("evidence_status", "UNKNOWN")
    if task_entry.get("eligibility_result") == "OR_EVIDENCE_MISSING":
        return _base_result(
            result="OR_EVIDENCE_MISSING",
            subject_type="dispatcher_task_class",
            subject_id=task_class,
            reason_code=task_entry.get("reason_code", "EVIDENCE_NOT_CONFIRMED"),
            message=task_entry.get("message", "Task class is not yet evidence-backed for bounded OR use."),
            evidence_status=evidence_status,
        )
    if task_entry.get("eligibility_result") == "OR_NOT_ELIGIBLE":
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="dispatcher_task_class",
            subject_id=task_class,
            reason_code=task_entry.get("reason_code", "TASK_CLASS_NOT_ALLOWED"),
            message=task_entry.get("message", "Task class is not allowed for bounded OR use."),
            evidence_status=evidence_status,
        )
    return _base_result(
        result="OR_ALLOWED",
        subject_type="dispatcher_task_class",
        subject_id=task_class,
        reason_code=task_entry.get("reason_code", "ELIGIBILITY_CONFIRMED"),
        message=task_entry.get("message", "Task class is allowed for bounded OR worker gating."),
        evidence_status=evidence_status,
    )


def evaluate_assistive_or_workhorse_pilot(
    *,
    skill_id: str,
    task_class: str,
    request_payload: dict[str, Any] | None = None,
    config_path: Path = DEFAULT_ELIGIBILITY_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_json(config_path)["assistive_or_workhorse_pilot"]
    skill_entry = config["skills"].get(skill_id)
    if skill_entry is None:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="assistive_or_workhorse_pilot",
            subject_id=f"{skill_id}:{task_class}",
            reason_code="SKILL_NOT_ALLOWED",
            message="Skill is outside the approved assistive OR workhorse pilot scope.",
        )

    allowed_task_classes = skill_entry.get("allowed_task_classes", [])
    if task_class not in allowed_task_classes:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="assistive_or_workhorse_pilot",
            subject_id=f"{skill_id}:{task_class}",
            reason_code="TASK_CLASS_NOT_ALLOWED",
            message="Task class is outside the approved assistive OR workhorse pilot scope.",
        )

    if request_payload is None:
        return _base_result(
            result="OR_ALLOWED",
            subject_type="assistive_or_workhorse_pilot",
            subject_id=f"{skill_id}:{task_class}",
            reason_code="ELIGIBILITY_CONFIRMED",
            message="Assistive OR workhorse pilot eligibility confirmed for this skill and task class.",
            evidence_status="PILOT_SCOPE_ALLOWED",
        )

    allowlist = config["request_package_allowlists"].get(task_class)
    if allowlist is None:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="assistive_or_workhorse_pilot",
            subject_id=f"{skill_id}:{task_class}",
            reason_code="REQUEST_ALLOWLIST_MISSING",
            message="No request allowlist exists for this pilot task class.",
        )

    required_fields = set(allowlist.get("required_fields", []))
    optional_fields = set(allowlist.get("optional_fields", []))
    allowed_fields = required_fields | optional_fields

    issues: list[str] = []
    for field in required_fields:
        if field not in request_payload:
            issues.append(f"missing input field: {field}")
    for field in request_payload:
        if field not in allowed_fields:
            issues.append(f"forbidden input field: {field}")

    snippets = request_payload.get("evidence_snippets")
    max_evidence_snippets = allowlist.get("max_evidence_snippets")
    if not isinstance(snippets, list) or not snippets:
        issues.append("evidence_snippets must be a non-empty list")
    elif isinstance(max_evidence_snippets, int) and len(snippets) > max_evidence_snippets:
        issues.append(f"evidence_snippets must contain at most {max_evidence_snippets} items")

    if request_payload.get("redaction_ready") is not True:
        issues.append("redaction_ready must be true for delegated review")

    if issues:
        return {
            **_base_result(
                result="OR_CONTEXT_REDACTION_REQUIRED",
                subject_type="assistive_or_workhorse_pilot",
                subject_id=f"{skill_id}:{task_class}",
                reason_code="REQUEST_PACKAGE_NOT_ALLOWLISTED",
                message="Request package must be narrowed to the approved redacted allowlist before delegated review.",
                evidence_status="PILOT_SCOPE_ALLOWED",
            ),
            "request_validation_issues": issues,
        }

    return _base_result(
        result="OR_ALLOWED",
        subject_type="assistive_or_workhorse_pilot",
        subject_id=f"{skill_id}:{task_class}",
        reason_code="ELIGIBILITY_CONFIRMED",
        message="Assistive OR workhorse pilot eligibility and request allowlist validation passed.",
        evidence_status="PILOT_SCOPE_ALLOWED",
    )


def evaluate_productive_dev_workhorse_path(
    *,
    path_id: str,
    task_class: str,
    estimated_or_cost: float | int | None,
    config_path: Path = DEFAULT_ELIGIBILITY_CONFIG_PATH,
    budget_config_path: Path = DEFAULT_BUDGET_PROFILE_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_json(config_path)["productive_dev_workhorse_path"]
    allowed_path_id = str(config["allowed_path_id"])
    subject_id = f"{path_id}:{task_class}"

    if norm(path_id) != norm(allowed_path_id):
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="productive_dev_workhorse_path",
            subject_id=subject_id,
            reason_code="PATH_NOT_ALLOWED",
            message="Workflow is outside the first dedicated productive Dev-workhorse path.",
        )

    task_entry = (config.get("allowed_task_classes") or {}).get(task_class)
    if task_entry is None:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="productive_dev_workhorse_path",
            subject_id=subject_id,
            reason_code="TASK_CLASS_NOT_ALLOWED",
            message="Task class is outside the approved productive Dev-workhorse boundary contract.",
        )

    budget_profile_name = str(task_entry.get("budget_profile") or "").strip()
    if not budget_profile_name:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="productive_dev_workhorse_path",
            subject_id=subject_id,
            reason_code="BUDGET_PROFILE_MISSING",
            message="No budget profile is configured for this productive Dev-workhorse task class.",
        )

    budget_profile = _load_budget_profile(budget_profile_name, budget_config_path)
    if budget_profile is None:
        return _base_result(
            result="OR_NOT_ELIGIBLE",
            subject_type="productive_dev_workhorse_path",
            subject_id=subject_id,
            reason_code="BUDGET_PROFILE_MISSING",
            message="Referenced budget profile is missing for this productive Dev-workhorse task class.",
        )

    if estimated_or_cost is None:
        return {
            **_base_result(
                result="OR_NOT_ELIGIBLE",
                subject_type="productive_dev_workhorse_path",
                subject_id=subject_id,
                reason_code="ESTIMATED_COST_MISSING",
                message="Estimated OR cost is required before offering the productive Dev-workhorse gate.",
            ),
            "budget_profile": budget_profile_name,
            "per_call_cap_usd": float(budget_profile["per_call_cap_usd"]),
            "session_cap_usd": float(budget_profile["session_cap_usd"]),
        }

    try:
        estimated = float(estimated_or_cost)
    except (TypeError, ValueError):
        return _invalid_estimated_cost_result(
            subject_id=subject_id,
            budget_profile_name=budget_profile_name,
            budget_profile=budget_profile,
            message="Estimated OR cost must be numeric before offering the productive Dev-workhorse gate.",
        )

    if not math.isfinite(estimated) or estimated < 0:
        return _invalid_estimated_cost_result(
            subject_id=subject_id,
            budget_profile_name=budget_profile_name,
            budget_profile=budget_profile,
            message="Estimated OR cost must be finite and non-negative before offering the productive Dev-workhorse gate.",
        )

    per_call_cap = float(budget_profile["per_call_cap_usd"])
    session_cap = float(budget_profile["session_cap_usd"])
    if estimated > per_call_cap:
        return {
            **_base_result(
                result="OR_NOT_ELIGIBLE",
                subject_type="productive_dev_workhorse_path",
                subject_id=subject_id,
                reason_code="PER_CALL_CAP_EXCEEDED",
                message="Estimated OR cost exceeds the productive Dev-workhorse per-call cap before the gate can be offered.",
            ),
            "budget_profile": budget_profile_name,
            "per_call_cap_usd": per_call_cap,
            "session_cap_usd": session_cap,
            "estimated_or_cost": estimated,
        }

    return {
        **_base_result(
            result="OR_ALLOWED",
            subject_type="productive_dev_workhorse_path",
            subject_id=subject_id,
            reason_code="ELIGIBILITY_CONFIRMED",
            message="Productive Dev-workhorse path eligibility confirmed for this task class.",
            evidence_status="CONTRACT_ONLY_ALLOWED",
        ),
        "budget_profile": budget_profile_name,
        "per_call_cap_usd": per_call_cap,
        "session_cap_usd": session_cap,
        "estimated_or_cost": estimated,
    }
