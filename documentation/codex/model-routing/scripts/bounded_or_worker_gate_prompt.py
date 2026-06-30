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
    choice_2_label: str = "OR",
    selected_or_model: str = "",
    pre_call_cost_basis: str = "",
    estimated_or_cost: float,
    cost_estimate_confidence_percent: float,
    operator_recommendation: str = "",
    operator_recommendation_reason: str = "",
) -> list[str]:
    lines = [
        "1 = Codex",
        f"2 = {choice_2_label}",
        "OR ist hier die externe Option, um Codex-Guthaben zu sparen.",
    ]
    if str(operator_recommendation).strip():
        lines.append(f"Live-Evidenz: {operator_recommendation}")
    if str(operator_recommendation_reason).strip():
        lines.append(f"Einordnung: {operator_recommendation_reason}")
    if str(selected_or_model).strip():
        lines.append(f"Fest empfohlenes OR-Modell: {selected_or_model}")
    if str(pre_call_cost_basis).strip():
        lines.append(f"Pre-Call-Kostenbasis: {pre_call_cost_basis}")
    lines.append(
        (
            f"Voraussichtliche OR-Kosten {estimated_or_cost:.9f}, "
            f"Evidenzgenauigkeit {cost_estimate_confidence_percent:.0f}%"
        )
    )
    return lines


def _roi_number(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_or_roi(
    *,
    estimated_codex_saved_tokens: Any = None,
    estimated_codex_or_overhead_tokens: Any = None,
    minimum_net_codex_saved_tokens: Any = 0,
) -> dict[str, Any]:
    saved_tokens = _roi_number(estimated_codex_saved_tokens)
    overhead_tokens = _roi_number(estimated_codex_or_overhead_tokens)
    minimum_net_saved = _roi_number(minimum_net_codex_saved_tokens)
    if minimum_net_saved is None:
        minimum_net_saved = 0

    missing: list[str] = []
    if saved_tokens is None:
        missing.append("estimated_codex_saved_tokens")
    if overhead_tokens is None:
        missing.append("estimated_codex_or_overhead_tokens")

    if missing:
        return {
            "status": "UNKNOWN",
            "missing_fields": missing,
            "estimated_codex_saved_tokens": saved_tokens,
            "estimated_codex_or_overhead_tokens": overhead_tokens,
            "minimum_net_codex_saved_tokens": minimum_net_saved,
            "net_codex_saved_tokens": None,
            "message": "OR ROI cannot be evaluated because Codex token estimates are missing.",
        }

    net_saved = int(saved_tokens) - int(overhead_tokens)
    status = "POSITIVE" if net_saved >= int(minimum_net_saved) else "NEGATIVE"
    return {
        "status": status,
        "missing_fields": [],
        "estimated_codex_saved_tokens": int(saved_tokens),
        "estimated_codex_or_overhead_tokens": int(overhead_tokens),
        "minimum_net_codex_saved_tokens": int(minimum_net_saved),
        "net_codex_saved_tokens": net_saved,
        "message": (
            f"OR ROI {status}: estimated saved Codex tokens {saved_tokens}, "
            f"OR orchestration/review overhead {overhead_tokens}, net {net_saved}, "
            f"minimum required {minimum_net_saved}."
        ),
    }


def should_enforce_or_roi(
    *,
    estimated_codex_saved_tokens: Any = None,
    estimated_codex_or_overhead_tokens: Any = None,
    require_positive_or_roi: bool = False,
) -> bool:
    return (
        bool(require_positive_or_roi)
        or estimated_codex_saved_tokens is not None
        or estimated_codex_or_overhead_tokens is not None
    )


def build_or_roi_gate_result(
    *,
    workflow_id: str,
    task_label: str,
    selected_path: str,
    normal_target_model: str,
    skill: str | None = None,
    task_class: str | None = None,
    eligibility_result: str | None = None,
    eligibility_reason_code: str | None = None,
    evidence_status: str | None = None,
    roi: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "summary_header": "BOUNDED OR ROI GATE RESULT",
        "workflow_id": workflow_id,
        "task_label": task_label,
        "selected_path": selected_path,
        "normal_target_model": normal_target_model,
        "operator_gate_visibility": "HIDDEN_ROI_GATE",
        "validation_result": "PASS",
        "final_outcome": "LOCAL_CODEX_PATH_SELECTED",
        "or_roi": roi,
        "choice_1": "Codex",
        "operator_result_lines": [
            "Ergebnis: OR ROI Gate negativ oder unvollstaendig",
            "Route: Codex direkt, weil OR voraussichtlich keine Netto-Codex-Ersparnis bringt",
            str(roi.get("message") or ""),
        ],
        "operator_message": (
            "The task stays on Codex because the estimated Codex savings do not clearly exceed "
            "the Codex overhead for OR briefing, orchestration, and review."
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
        "operator_gate_visibility": "HIDDEN_FAIL_CLOSED",
        "validation_result": "PASS",
        "final_outcome": final_outcome,
        "missing_gate_fields": missing_fields,
        "choice_1": "Codex",
        "operator_result_lines": [
            "Ergebnis: OR-Gate unterdrueckt",
            "Route: Codex-only wegen fehlender Pflichtdaten",
        ],
        "operator_message": (
            "The OR gate was suppressed because required prompt fields are missing: "
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


def build_visibility_suppressed_result(
    *,
    workflow_id: str,
    task_label: str,
    selected_path: str,
    final_outcome: str,
    normal_target_model: str,
    visibility_status: str,
    suppression_reason: str,
    selected_or_model: str | None = None,
    skill: str | None = None,
    task_class: str | None = None,
    evidence_status: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "summary_header": "BOUNDED OR WORKER GATE RESULT",
        "workflow_id": workflow_id,
        "task_label": task_label,
        "selected_path": selected_path,
        "normal_target_model": normal_target_model,
        "operator_gate_visibility": "HIDDEN",
        "visibility_status": visibility_status,
        "validation_result": "PASS",
        "final_outcome": final_outcome,
        "choice_1": "Codex",
        "operator_result_lines": [
            "Ergebnis: OR-Gate verborgen",
            f"Route: Codex-only wegen {suppression_reason}",
        ],
        "operator_message": (
            "The OR gate remains hidden because this lane is not approved for the normal everyday "
            f"operator choice: {suppression_reason}."
        ),
    }
    if str(selected_or_model or "").strip():
        payload["selected_or_model"] = str(selected_or_model)
    if skill is not None:
        payload["skill"] = skill
    if task_class is not None:
        payload["task_class"] = task_class
    if evidence_status is not None:
        payload["evidence_status"] = evidence_status
    return payload
