from __future__ import annotations

from typing import Any


def normalize_codex_owned_outcome(
    *,
    selected_path: str,
    validation_result: str,
    final_outcome: str,
    fallback_used: str | None = None,
    rework_required: str | None = None,
) -> dict[str, Any]:
    if final_outcome == "AWAITING_OPERATOR_CHOICE":
        status = "AWAITING_OPERATOR_CHOICE"
    elif selected_path.startswith("codex_only"):
        status = "CODEX_LOCAL_PATH"
    elif selected_path == "operator_choice_pending":
        status = "AWAITING_OPERATOR_CHOICE"
    elif selected_path == "fixed_or_then_codex_validate":
        if validation_result == "PASS" and fallback_used == "NO" and rework_required == "NO":
            status = "OR_ACCEPTED_BY_CODEX"
        elif fallback_used == "YES":
            status = "OR_FALLBACK_TO_CODEX"
        else:
            status = "OR_REJECTED_BY_CODEX"
    elif selected_path == "abort_post_wrapper":
        status = "OR_REJECTED_BY_CODEX"
    elif "delegated_assist_only" in selected_path or selected_path in {
        "delegated_intent_local_structured_executor",
        "delegated_execution_write_apply_candidate_entry_gate",
    }:
        if validation_result == "PASS":
            status = "DELEGATED_REVIEW_PENDING_CODEX_DECISION"
        else:
            status = "DELEGATED_REJECT_AND_FALLBACK"
    elif "fallback" in selected_path or fallback_used == "YES":
        status = "DELEGATED_REJECT_AND_FALLBACK"
    else:
        status = "CODEX_REVIEW_REQUIRED"

    return {
        "codex_owned_outcome_status": status,
        "codex_owned_outcome_final": status in {"OR_ACCEPTED_BY_CODEX", "OR_REJECTED_BY_CODEX", "OR_FALLBACK_TO_CODEX"},
    }
