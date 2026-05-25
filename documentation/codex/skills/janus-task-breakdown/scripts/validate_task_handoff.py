#!/usr/bin/env python3
"""Validate that a Janus task artifact contains the selected target task."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    try:
        text = args.task.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"TASK HANDOFF VALIDATION FAILED\nERROR: missing file: {args.task}")
        return 1

    errors: list[str] = []
    if args.target not in text:
        errors.append(f"Target task not found: {args.target}")
    for marker in ("Acceptance Criteria", "Tests", "Files"):
        if marker not in text:
            errors.append(f"Missing marker: {marker}")
    if re.search(r"documentation/test-runs/.*_plan\.json", text) and "documentation/TEST_SPEC/" not in text:
        errors.append("Potential TestPlan-only oracle task without source TestSpec")

    if errors:
        print("TASK HANDOFF VALIDATION FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("TASK HANDOFF VALIDATION PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
