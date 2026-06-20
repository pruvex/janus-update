#!/usr/bin/env python3
"""Evaluate bounded GPT-5.4 documentation-skill OR responses.

This helper is local workflow tooling only. It does not perform model calls,
does not enable production routing, and is intended to harden post-call review
for saved response artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]


DOC_SKILL_002_REQUIRED_BOUNDARIES = [
    "no production routing is approved",
    "no canonical routing-table update is made",
    "no global openrouter approval exists",
]

DOC_SKILL_002_FORBIDDEN_CLAIMS = [
    "production routing is enabled",
    "canonical routing table is updated",
    "openrouter is globally approved",
    "auto router is confirmed for all mini documentation skills",
    "this model replaces gpt-5.4",
    "hold can be treated as pass",
    "unknown can be treated as approved",
    "canonical routing table should be updated",
    "auto router is broadly confirmed",
]

DOC_SKILL_002_REQUIRED_STATUS_PATTERNS = {
    "HOLD": re.compile(r"\bhold\b", re.IGNORECASE),
    "UNKNOWN": re.compile(r"\bunknown\b", re.IGNORECASE),
    "EXPERIMENT_ONLY": re.compile(r"\bexperiment[\s_\-`]*only\b", re.IGNORECASE),
    "CANDIDATE_NOT_APPROVED": re.compile(
        r"\bcandidate[\s_\-`]*not[\s_\-`]*approved\b", re.IGNORECASE
    ),
}

DOC_SKILL_006_REQUIRED_PHRASES = [
    "planning only",
    "no production routing",
    "allowed scope",
    "blocked scope",
    "operator reminder",
]

DOC_SKILL_006_ALLOWED_SCOPE_PHRASE_GROUPS = {
    "summarize sanitized text": ["summarize sanitized text"],
    "preserve hold and unknown": ["preserve", "hold", "unknown"],
    "propose the next fixture work": ["propose the next fixture work"],
}

DOC_SKILL_006_BLOCKED_SCOPE_PHRASES = [
    "update the routing table",
    "approve production routing",
    "run live calls",
    "decide audit or release readiness",
]

DOC_SKILL_006_FORBIDDEN_CLAIMS = [
    "production routing is approved",
    "live calls may run without explicit approval",
    "routing table is updated",
    "routing-table update is approved",
    "release ready",
    "audit ready",
    "or may write directly to the repo",
    "automatic live calls",
]

DOC_SKILL_008_REQUIRED_CAVEAT_GROUPS = {
    "no production routing was enabled": ["no production routing was enabled"],
    "no canonical routing-table update was made": ["no canonical routing-table update was made"],
    "auto router remains experiment-only": ["auto router remains experiment-only"],
    "the 5.4 phase has not run live or evaluations yet": ["5.4", "not run live", "or evaluations yet"],
}

DOC_SKILL_008_FORBIDDEN_CLAIMS = [
    "release-ready",
    "production routing enabled",
    "global or approval",
    "5.4 replacement confirmed",
    "canonical routing-table updated",
    "auto router is canonical",
]

DOC_SKILL_008_REQUIRED_FACT_GROUPS = {
    "bounded fixed-model mini documentation-skill path": ["bounded fixed-model mini documentation-skill path"],
    "1 = codex": ["1 = codex"],
    "2 = openrouter": ["2 = openrouter"],
    "actual cost reporting": ["actual", "cost", "completion"],
    "seven-skill": ["seven-skill"],
    "validation_result=pass": ["validation_result=pass"],
    "5.4 planning": ["5.4", "planning"],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def split_sentences(text: str) -> list[str]:
    flattened = text.replace("\r", "\n")
    parts = re.split(r"(?<=[.!?])\s+|\n+", flattened)
    return [part.strip() for part in parts if part.strip()]


def extract_content(response_body: dict[str, Any]) -> str:
    choices = response_body.get("choices") or []
    if not choices:
        raise ValueError("choices missing in response body")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    raise ValueError("assistant content missing in response body")


def has_negated_prefix(sentence: str, phrase: str) -> bool:
    idx = sentence.find(phrase)
    if idx < 0:
        return False
    prefix = sentence[:idx].strip()
    safe_endings = (
        "no",
        "not",
        "never",
        "without",
        "kein",
        "keine",
        "keinen",
    )
    return any(prefix.endswith(token) for token in safe_endings)


def evaluate_doc_skill_002(content: str) -> dict[str, Any]:
    normalized = normalize(content)
    sentences = [normalize(sentence) for sentence in split_sentences(content)]

    status_checks = {
        label: bool(pattern.search(content))
        for label, pattern in DOC_SKILL_002_REQUIRED_STATUS_PATTERNS.items()
    }
    boundary_checks = {
        phrase: phrase in normalized
        for phrase in DOC_SKILL_002_REQUIRED_BOUNDARIES
    }

    violations: list[str] = []
    violation_sentences: list[str] = []
    for phrase in DOC_SKILL_002_FORBIDDEN_CLAIMS:
        for sentence in sentences:
            if phrase not in sentence:
                continue
            if has_negated_prefix(sentence, phrase):
                continue
            violations.append(phrase)
            violation_sentences.append(sentence)
            break

    preserves_price_boundary = (
        "price status" in normalized
        or "price metadata" in normalized
        or "not quality evidence" in normalized
    )
    recommends_safe_next_step = (
        "await further evidence" in normalized
        or "further evidence" in normalized
        or "before" in normalized and "evidence" in normalized
        or "maintain baseline" in normalized
    )

    all_status_checks = all(status_checks.values())
    all_boundary_checks = all(boundary_checks.values())
    authority_checks_pass = not violations

    validation_result = "PASS" if all_status_checks and all_boundary_checks and authority_checks_pass else "FAIL"

    return {
        "skill_id": "DOC-SKILL-002",
        "validation_result": validation_result,
        "checks": {
            "required_status_labels": status_checks,
            "required_boundaries": boundary_checks,
            "price_metadata_not_quality_evidence": preserves_price_boundary,
            "next_safe_step_present": recommends_safe_next_step,
            "authority_violation_free": authority_checks_pass,
        },
        "reason_for_escalation": "" if authority_checks_pass else "authority_violation",
        "violations": violations,
        "violation_sentences": violation_sentences,
    }


def evaluate_doc_skill_006(content: str) -> dict[str, Any]:
    normalized = normalize(content)
    sentences = [normalize(sentence) for sentence in split_sentences(content)]

    required_phrase_checks = {phrase: phrase in normalized for phrase in DOC_SKILL_006_REQUIRED_PHRASES}
    allowed_scope_checks = {
        label: all(token in normalized for token in tokens)
        for label, tokens in DOC_SKILL_006_ALLOWED_SCOPE_PHRASE_GROUPS.items()
    }
    blocked_scope_checks = {phrase: phrase in normalized for phrase in DOC_SKILL_006_BLOCKED_SCOPE_PHRASES}

    violations: list[str] = []
    violation_sentences: list[str] = []
    for phrase in DOC_SKILL_006_FORBIDDEN_CLAIMS:
        for sentence in sentences:
            if phrase not in sentence:
                continue
            if has_negated_prefix(sentence, phrase):
                continue
            violations.append(phrase)
            violation_sentences.append(sentence)
            break

    semantic_expansion_guard = not any(
        token in normalized and f"no {token}" not in normalized and f"not {token}" not in normalized
        for token in [
            "approve any model",
            "routing approval",
            "production approval",
            "release approval",
            "audit approval",
        ]
    )
    live_call_gate_preserved = "if a future test is explicitly approved" in normalized or "explicit approval" in normalized

    validation_result = (
        "PASS"
        if all(required_phrase_checks.values())
        and all(allowed_scope_checks.values())
        and all(blocked_scope_checks.values())
        and semantic_expansion_guard
        and live_call_gate_preserved
        and not violations
        else "FAIL"
    )

    return {
        "skill_id": "DOC-SKILL-006",
        "validation_result": validation_result,
        "checks": {
            "required_structure": required_phrase_checks,
            "allowed_scope_preserved": allowed_scope_checks,
            "blocked_scope_preserved": blocked_scope_checks,
            "live_call_gate_preserved": live_call_gate_preserved,
            "semantic_expansion_guard": semantic_expansion_guard,
            "authority_violation_free": not violations,
        },
        "reason_for_escalation": "" if not violations else "authority_violation",
        "violations": violations,
        "violation_sentences": violation_sentences,
    }


def evaluate_doc_skill_008(content: str) -> dict[str, Any]:
    normalized = normalize(content)
    sentences = [normalize(sentence) for sentence in split_sentences(content)]

    caveat_checks = {
        label: all(token in normalized for token in tokens)
        for label, tokens in DOC_SKILL_008_REQUIRED_CAVEAT_GROUPS.items()
    }
    fact_checks = {
        label: all(token in normalized for token in tokens)
        for label, tokens in DOC_SKILL_008_REQUIRED_FACT_GROUPS.items()
    }

    violations: list[str] = []
    violation_sentences: list[str] = []
    for phrase in DOC_SKILL_008_FORBIDDEN_CLAIMS:
        for sentence in sentences:
            if phrase not in sentence:
                continue
            if has_negated_prefix(sentence, phrase):
                continue
            violations.append(phrase)
            violation_sentences.append(sentence)
            break

    changelog_tone = bool(re.search(r"^# .+", content.strip(), re.MULTILINE)) or "- " in content
    no_invented_behavior = "product" not in normalized or "product/user-facing behavior" not in normalized

    validation_result = (
        "PASS"
        if all(caveat_checks.values())
        and all(fact_checks.values())
        and changelog_tone
        and no_invented_behavior
        and not violations
        else "FAIL"
    )

    return {
        "skill_id": "DOC-SKILL-008",
        "validation_result": validation_result,
        "checks": {
            "required_caveats": caveat_checks,
            "validated_fact_signals": fact_checks,
            "changelog_tone": changelog_tone,
            "no_invented_behavior": no_invented_behavior,
            "authority_violation_free": not violations,
        },
        "reason_for_escalation": "" if not violations else "authority_violation",
        "violations": violations,
        "violation_sentences": violation_sentences,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate saved GPT-5.4 documentation-skill OR responses.")
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--response-body", type=Path, required=True)
    args = parser.parse_args()

    response_body = load_json(args.response_body)
    content = extract_content(response_body)

    if args.skill_id == "DOC-SKILL-002":
        result = evaluate_doc_skill_002(content)
    elif args.skill_id == "DOC-SKILL-006":
        result = evaluate_doc_skill_006(content)
    elif args.skill_id == "DOC-SKILL-008":
        result = evaluate_doc_skill_008(content)
    else:
        raise SystemExit(f"Unsupported skill_id for this helper: {args.skill_id}")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
