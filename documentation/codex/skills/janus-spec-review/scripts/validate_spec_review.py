#!/usr/bin/env python3
"""Validate the Janus Spec Review metadata block."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "Review Status",
    "Complexity Score",
    "Risk",
    "Recommended Review Model",
    "Skill-1 Ready",
    "Split Required",
    "Reviewed At",
    "Review Confidence",
    "Review Source",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()

    try:
        text = args.spec.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"SPEC REVIEW VALIDATION FAILED\nERROR: missing file: {args.spec}")
        return 1

    errors: list[str] = []
    if "## SPEC REVIEW METADATA" not in text:
        errors.append("Missing ## SPEC REVIEW METADATA block")

    for field in REQUIRED_FIELDS:
        if f"**{field}:**" not in text:
            errors.append(f"Missing metadata field: {field}")

    score = re.search(r"\*\*Complexity Score:\*\*\s*(\d+)", text)
    if score and not 0 <= int(score.group(1)) <= 100:
        errors.append("Complexity Score must be 0-100")

    if errors:
        print("SPEC REVIEW VALIDATION FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("SPEC REVIEW VALIDATION PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
