from __future__ import annotations

from typing import Any


def missing_gate_fields(
    *,
    selected_or_model: str | None,
    estimated_or_cost: float | int | None,
    cost_estimate_confidence_percent: float | int | None,
) -> list[str]:
    missing: list[str] = []
    if not str(selected_or_model or "").strip():
        missing.append("selected_or_model")
    if estimated_or_cost is None:
        missing.append("estimated_or_cost")
    if cost_estimate_confidence_percent is None:
        missing.append("cost_estimate_confidence_percent")
    return missing


def build_operator_prompt_lines(
    *,
    estimated_or_cost: float,
    cost_estimate_confidence_percent: float,
) -> list[str]:
    return [
        "Willst du 1 Codex das machen lassen?",
        (
            "Oder 2 das mit OPR machen lassen "
            f"(voraussichtliche Kosten {estimated_or_cost:.9f}, "
            f"Genauigkeit {cost_estimate_confidence_percent:.0f}%)?"
        ),
    ]


def build_missing_gate_result(
    *,
    workflow_id: str,
    task_label: str,
    selected_path: str,
    missing_fields: list[str],
    final_outcome: str,
    normal_target_model: str,
    skill: str | None = None,
    task_class: str | None = None,
    eligibility_result: str | None = None,
    eligibility_reason_code: str | None = None,
    evidence_status: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "summary_header": "BOUNDED OR WORKER GATE RESULT",
        "workflow_id": workflow_id,
        "task_label": task_label,
        "selected_path": selected_path,
        "normal_target_model": normal_target_model,
        "validation_result": "PASS",
        "final_outcome": final_outcome,
        "missing_gate_fields": missing_fields,
        "choice_1": "Codex",
        "operator_result_lines": [
            "Ergebnis: OR-Gate unterdrueckt",
            "Route: Codex-only wegen fehlender Pflichtdaten",
        ],
        "operator_message": (
            "The OpenRouter gate was suppressed because required prompt fields are missing: "
            + ", ".join(missing_fields)
            + ". Codex-only remains the safe path."
        ),
    }
    if skill is not None:
        payload["skill"] = skill
    if task_class is not None:
        payload["task_class"] = task_class
    if eligibility_result is not None:
        payload["eligibility_result"] = eligibility_result
    if eligibility_reason_code is not None:
        payload["eligibility_reason_code"] = eligibility_reason_code
    if evidence_status is not None:
        payload["evidence_status"] = evidence_status
    return payload
