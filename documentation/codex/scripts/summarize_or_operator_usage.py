#!/usr/bin/env python3
"""Summarize central OR operator usage logs for healthcheck-style review."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_PATH = REPO_ROOT / "documentation" / "codex" / "model-routing" / "or_operator_usage_log.jsonl"


def load_entries(path: Path) -> list[dict]:
    entries: list[dict] = []
    if not path.exists():
        return entries
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def counter_to_sorted_dict(counter: Counter) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def summarize(entries: list[dict]) -> dict:
    operator_choice = Counter()
    final_outcome = Counter()
    codex_followup_state = Counter()
    or_model_provider = Counter()
    task_label = Counter()

    repo_side_effect_runs = 0
    codex_fallback_required = 0
    ready_for_review = 0
    local_choice_count = 0
    delegated_choice_count = 0
    prompt_count = 0

    for entry in entries:
        choice = str(entry.get("operator_choice") or "")
        outcome = str(entry.get("final_outcome") or "")
        followup = str(entry.get("codex_followup_state") or "")
        model = str(entry.get("or_model_provider") or "")
        label = str(entry.get("task_label") or "")

        operator_choice[choice] += 1
        final_outcome[outcome] += 1
        codex_followup_state[followup] += 1
        if model:
            or_model_provider[model] += 1
        if label:
            task_label[label] += 1

        if entry.get("repo_side_effects"):
            repo_side_effect_runs += 1
        if followup == "CODEX_FALLBACK_REQUIRED":
            codex_fallback_required += 1
        if followup == "READY_FOR_CODEX_REVIEW":
            ready_for_review += 1
        if choice == "1":
            local_choice_count += 1
        elif choice == "2":
            delegated_choice_count += 1
        elif choice == "prompt":
            prompt_count += 1

    return {
        "log_path": str(DEFAULT_LOG_PATH),
        "entry_count": len(entries),
        "operator_choice_counts": counter_to_sorted_dict(operator_choice),
        "final_outcome_counts": counter_to_sorted_dict(final_outcome),
        "codex_followup_state_counts": counter_to_sorted_dict(codex_followup_state),
        "top_or_models": counter_to_sorted_dict(or_model_provider),
        "top_task_labels": counter_to_sorted_dict(task_label),
        "repo_side_effect_runs": repo_side_effect_runs,
        "local_choice_count": local_choice_count,
        "delegated_choice_count": delegated_choice_count,
        "prompt_count": prompt_count,
        "ready_for_codex_review_count": ready_for_review,
        "codex_fallback_required_count": codex_fallback_required,
    }


def main() -> int:
    entries = load_entries(DEFAULT_LOG_PATH)
    print(json.dumps(summarize(entries), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
