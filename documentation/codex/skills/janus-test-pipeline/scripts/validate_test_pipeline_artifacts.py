#!/usr/bin/env python3
"""Lightweight Janus test pipeline artifact validator."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RUN_ID_RE = re.compile(r"^TEST-RUN-\d{4}-\d{2}-\d{2}-[A-Z0-9-]+$")
RESULT_STATUSES = {"pass", "passed", "fail", "failed", "blocked", "skip", "skipped"}
RUN_STATUSES = {"PASS", "PASSED", "FAIL", "FAILED", "BLOCKED", "PARTIAL", "PASS_WITH_WARNINGS", "RUNNING"}


def load_json(path: Path) -> tuple[dict | list | None, list[str]]:
    errors: list[str] = []
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), errors
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    return None, errors


def as_dict(value: object, label: str, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def get_any(data: dict, *keys: str) -> object:
    for key in keys:
        if key in data:
            return data[key]
    return None


def normalize_status(value: object) -> str:
    return str(value or "").strip()


def validate_plan(path: Path) -> tuple[str | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    raw, load_errors = load_json(path)
    errors.extend(load_errors)
    if errors:
        return None, errors, warnings

    plan = as_dict(raw, "TestPlan", errors)
    run_id = get_any(plan, "testRunId", "test_run_id", "id")
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        errors.append("TestPlan must contain a valid testRunId/test_run_id/id")

    tests = get_any(plan, "tests", "testCases", "cases")
    if not isinstance(tests, list) or not tests:
        errors.append("TestPlan must contain a non-empty tests/testCases/cases list")
        return run_id if isinstance(run_id, str) else None, errors, warnings

    for index, item in enumerate(tests, start=1):
        case = as_dict(item, f"TestPlan test #{index}", errors)
        case_id = get_any(case, "id", "testId", "test_id", "testCaseId")
        name = get_any(case, "name", "title")
        expected = get_any(case, "expected", "expectedResult", "assertions")
        if not case_id:
            errors.append(f"TestPlan test #{index} is missing id/testId")
        if not name:
            warnings.append(f"TestPlan test #{index} is missing a human-readable name/title")
        if expected in (None, "", []):
            warnings.append(f"TestPlan test #{index} has no explicit expected/assertions field")

    return run_id if isinstance(run_id, str) else None, errors, warnings


def result_list(result: dict) -> list:
    for key in ("results", "testResults", "cases"):
        value = result.get(key)
        if isinstance(value, list):
            return value
    return []


def validate_result(path: Path) -> tuple[str | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    raw, load_errors = load_json(path)
    errors.extend(load_errors)
    if errors:
        return None, errors, warnings

    result = as_dict(raw, "TestResult", errors)
    run_id = get_any(result, "testRunId", "test_run_id", "id")
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        errors.append("TestResult must contain a valid testRunId/test_run_id/id")

    schema = result.get("schemaVersion")
    if schema and schema != "janus.test-result.v1":
        warnings.append(f"Unexpected schemaVersion: {schema}")

    status = normalize_status(get_any(result, "status", "overallStatus", "result"))
    if status and status not in RUN_STATUSES:
        warnings.append(f"Unexpected overall result status: {status}")

    cases = result_list(result)
    if not cases:
        errors.append("TestResult must contain a non-empty results/testResults/cases list")
        return run_id if isinstance(run_id, str) else None, errors, warnings

    observed_counts = {"passed": 0, "failed": 0, "blocked": 0, "skipped": 0}
    for index, item in enumerate(cases, start=1):
        case = as_dict(item, f"TestResult case #{index}", errors)
        case_id = get_any(case, "id", "testId", "test_id", "testCaseId")
        case_status = normalize_status(get_any(case, "status", "result", "outcome")).lower()
        if not case_id:
            errors.append(f"TestResult case #{index} is missing id/testId/testCaseId")
        if case_status not in RESULT_STATUSES:
            errors.append(f"TestResult case #{index} has invalid status/result/outcome: {case_status or '<missing>'}")
        elif case_status in {"pass", "passed"}:
            observed_counts["passed"] += 1
        elif case_status in {"fail", "failed"}:
            observed_counts["failed"] += 1
        elif case_status == "blocked":
            observed_counts["blocked"] += 1
        else:
            observed_counts["skipped"] += 1

    summary = result.get("summary")
    if isinstance(summary, dict):
        total = summary.get("total")
        if isinstance(total, int) and total != len(cases):
            errors.append(f"summary.total={total} does not match result count={len(cases)}")
        for key in ("passed", "failed", "blocked", "skipped"):
            value = summary.get(key)
            if isinstance(value, int) and value != observed_counts[key]:
                warnings.append(f"summary.{key}={value} differs from observed {observed_counts[key]}")
    else:
        warnings.append("TestResult has no summary object")

    return run_id if isinstance(run_id, str) else None, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Janus test pipeline artifacts.")
    parser.add_argument("--plan", type=Path, help="Path to TestPlan JSON")
    parser.add_argument("--result", type=Path, help="Path to TestResult JSON")
    args = parser.parse_args()

    if not args.plan and not args.result:
        parser.error("Provide --plan and/or --result")

    errors: list[str] = []
    warnings: list[str] = []
    plan_run_id: str | None = None
    result_run_id: str | None = None

    if args.plan:
        plan_run_id, plan_errors, plan_warnings = validate_plan(args.plan)
        errors.extend(plan_errors)
        warnings.extend(plan_warnings)

    if args.result:
        result_run_id, result_errors, result_warnings = validate_result(args.result)
        errors.extend(result_errors)
        warnings.extend(result_warnings)

    if plan_run_id and result_run_id and plan_run_id != result_run_id:
        errors.append(f"Plan/result testRunId mismatch: {plan_run_id} != {result_run_id}")

    for warning in warnings:
        print(f"WARN: {warning}")

    if errors:
        print("TEST PIPELINE ARTIFACT VALIDATION FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if warnings:
        print("TEST PIPELINE ARTIFACT VALIDATION PASS WITH WARNINGS")
    else:
        print("TEST PIPELINE ARTIFACT VALIDATION PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
