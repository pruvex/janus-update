#!/usr/bin/env python3
"""Post-check saved GPT-5.4 documentation-skill OR artifacts.

This helper combines wrapper capture metadata with the hardened local response
evaluation logic. It is intended for future bounded batch follow-ups and does
not perform any model calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gpt54_doc_skill_response_evaluator import (
    evaluate_doc_skill_002,
    evaluate_doc_skill_006,
    evaluate_doc_skill_008,
    extract_content,
    load_json,
)


def build_common_checks(response_summary: dict[str, Any]) -> dict[str, bool]:
    usage = response_summary.get("usage")
    return {
        "generation_id_present": bool(response_summary.get("generation_id")),
        "usage_present": bool(usage),
        "actual_cost_present": response_summary.get("actual_or_cost") is not None,
        "finish_reason_not_length": str(response_summary.get("finish_reason", "")).lower() != "length",
    }


def evaluate_saved_artifacts(skill_id: str, response_body: dict[str, Any], response_summary: dict[str, Any]) -> dict[str, Any]:
    content = extract_content(response_body)
    if skill_id == "DOC-SKILL-002":
        content_eval = evaluate_doc_skill_002(content)
    elif skill_id == "DOC-SKILL-006":
        content_eval = evaluate_doc_skill_006(content)
    elif skill_id == "DOC-SKILL-008":
        content_eval = evaluate_doc_skill_008(content)
    else:
        raise ValueError(f"Unsupported skill_id for postcheck helper: {skill_id}")

    common_checks = build_common_checks(response_summary)
    accepted = content_eval["validation_result"] == "PASS" and all(common_checks.values())

    return {
        "skill_id": skill_id,
        "generation_id": response_summary.get("generation_id"),
        "model": response_body.get("model") or response_summary.get("model"),
        "finish_reason": response_summary.get("finish_reason"),
        "actual_or_cost": response_summary.get("actual_or_cost"),
        "common_checks": common_checks,
        "content_evaluation": content_eval,
        "postcheck_validation_result": "PASS" if accepted else "FAIL",
        "accepted_for_local_batch_use": accepted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-check saved GPT-5.4 documentation-skill OR artifacts.")
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--response-body", type=Path, required=True)
    parser.add_argument("--response-summary", type=Path, required=True)
    parser.add_argument("--write-json", type=Path, default=None)
    args = parser.parse_args()

    response_body = load_json(args.response_body)
    response_summary = load_json(args.response_summary)
    result = evaluate_saved_artifacts(args.skill_id, response_body, response_summary)

    if args.write_json is not None:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
