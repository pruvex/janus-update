#!/usr/bin/env python3
"""Validation-only entry point for the Janus worker gateway contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from janus_worker_contract import validate_worker_result_dir, validate_worker_task_package_file


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def validate_gateway_contract(task_package_json: Path, result_dir: Path | None = None) -> dict[str, Any]:
    task_result = validate_worker_task_package_file(task_package_json)
    result_payload: dict[str, Any] | None = None

    if result_dir is not None:
        result_payload = validate_worker_result_dir(
            result_dir,
            allowed_edit_paths=task_result.get("allowed_edit_paths", []),
        )

    validation_result = task_result["validation_result"]
    if result_payload is not None and result_payload["validation_result"] == "FAIL":
        validation_result = "FAIL"

    if validation_result == "PASS" and result_payload is None:
        gateway_status = "TASK_PACKAGE_READY"
    elif validation_result == "PASS" and result_payload is not None:
        gateway_status = result_payload["contract_status"]
    else:
        gateway_status = "GATEWAY_CONTRACT_REJECTED"

    return {
        "summary_header": "JANUS WORKER GATEWAY CONTRACT",
        "gateway_status": gateway_status,
        "validation_result": validation_result,
        "task_package": task_result,
        "result_package": result_payload,
        "operator_message": _operator_message(gateway_status),
    }


def _operator_message(gateway_status: str) -> str:
    if gateway_status == "TASK_PACKAGE_READY":
        return "Task package is contract-valid. No worker has been executed by this validation-only gateway slice."
    if gateway_status == "WORKER_SUCCESS_REVIEWABLE":
        return "Worker result is structurally reviewable by Codex. Codex must still review diff and evidence."
    if gateway_status == "WORKER_NON_SUCCESS_REVIEWABLE":
        return "Worker did not claim success, but the result package is structurally reviewable for retry or fallback."
    return "Gateway contract rejected the package fail-closed."


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Janus worker task and result contracts.")
    parser.add_argument("--task-package-json", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, default=None)
    args = parser.parse_args()

    result = validate_gateway_contract(args.task_package_json.resolve(), args.result_dir.resolve() if args.result_dir else None)
    output(result)
    return 0 if result["validation_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
