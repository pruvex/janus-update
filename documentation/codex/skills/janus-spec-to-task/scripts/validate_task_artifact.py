#!/usr/bin/env python3
"""Validate a Janus generated task artifact."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    args = parser.parse_args()

    try:
        text = args.task.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"TASK ARTIFACT VALIDATION FAILED\nERROR: missing file: {args.task}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    if not re.search(r"\bTASK-[A-Z0-9-]+(?:\.\d+)?\b", text):
        errors.append("No TASK id found")
    for marker in ("Files", "Acceptance Criteria", "Tests", "Model"):
        if marker not in text:
            errors.append(f"Missing marker: {marker}")
    if "Source Spec" not in text:
        warnings.append("Missing Source Spec marker; tolerated for legacy task artifacts")

    verify_only = re.findall(r"(?im)^#+\s*TASK-[^\n]*(review|verify|analyse|analysis|design|non-regression)", text)
    if verify_only:
        errors.append("Potential verify/review/design-only task title found")

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        print("TASK ARTIFACT VALIDATION FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if warnings:
        print("TASK ARTIFACT VALIDATION PASS WITH WARNINGS")
    else:
        print("TASK ARTIFACT VALIDATION PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
