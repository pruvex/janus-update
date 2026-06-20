#!/usr/bin/env python3
"""Build executor-ready delegated action requests from bounded local artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def rel_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one structured action request JSON from a bounded local artifact.")
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--action-type", required=True, choices=["draft_markdown", "propose_patch", "run_generator", "run_validator"])
    parser.add_argument("--summary", required=True)
    parser.add_argument("--source-path", required=True, help="Path to markdown, diff, or payload-manifest source artifact.")
    parser.add_argument("--output-request-json", required=True)
    parser.add_argument("--non-goal", action="append", dest="non_goals", required=True)
    parser.add_argument("--allowed-file", action="append", dest="allowed_files")
    return parser.parse_args()


def build_request(args: argparse.Namespace) -> dict:
    source_path = resolve_path(args.source_path)
    if not source_path.exists():
        raise SystemExit(f"Source path does not exist: {source_path}")
    source_text = load_text(source_path)
    if not source_text.strip():
        raise SystemExit(f"Source path is empty: {source_path}")

    request = {
        "schema_version": "codex_delegated_action_request.v1",
        "workflow_id": args.workflow_id,
        "skill_id": args.skill_id,
        "action_type": args.action_type,
        "summary": args.summary,
        "requires_codex_review": True,
        "non_goals": args.non_goals,
    }

    if args.action_type == "draft_markdown":
        request["action_payload"] = {
            "format": "markdown",
            "content": source_text,
        }
    elif args.action_type == "propose_patch":
        allowed_files = args.allowed_files or []
        if not allowed_files:
            raise SystemExit("propose_patch requires at least one --allowed-file entry.")
        request["action_payload"] = {
            "patch_format": "unified_diff",
            "allowed_files": [item.replace("\\", "/") for item in allowed_files],
            "patch_text": source_text,
        }
    elif args.action_type == "run_generator":
        payload = json.loads(source_text)
        if not isinstance(payload, dict):
            raise SystemExit("run_generator source manifest must be a JSON object.")
        if not payload.get("generator_id"):
            raise SystemExit("run_generator source manifest requires generator_id.")
        if not isinstance(payload.get("inputs"), dict):
            raise SystemExit("run_generator source manifest requires object inputs.")
        if not isinstance(payload.get("declared_output_artifacts"), list) or not payload["declared_output_artifacts"]:
            raise SystemExit("run_generator source manifest requires declared_output_artifacts.")
        request["action_payload"] = payload
    elif args.action_type == "run_validator":
        payload = json.loads(source_text)
        if not isinstance(payload, dict):
            raise SystemExit("run_validator source manifest must be a JSON object.")
        if not payload.get("validator_id"):
            raise SystemExit("run_validator source manifest requires validator_id.")
        if not isinstance(payload.get("inputs"), dict):
            raise SystemExit("run_validator source manifest requires object inputs.")
        if payload.get("validator_id") == "validate_write_candidate_entry_v1":
            inputs = payload["inputs"]
            required_fields = [
                "target_task",
                "precheck_status",
                "allowed_files",
                "max_touched_files",
                "forbid_delete_rename_move",
                "manual_validation_gate",
                "delegation_question",
            ]
            for field in required_fields:
                if field not in inputs:
                    raise SystemExit(
                        f"validate_write_candidate_entry_v1 requires input field: {field}."
                    )
            if not isinstance(inputs["target_task"], str) or not inputs["target_task"].strip():
                raise SystemExit("validate_write_candidate_entry_v1 requires non-empty target_task.")
            if inputs["precheck_status"] != "PRE-CHECK PASSED":
                raise SystemExit("validate_write_candidate_entry_v1 requires precheck_status=PRE-CHECK PASSED.")
            if not isinstance(inputs["allowed_files"], list) or not inputs["allowed_files"]:
                raise SystemExit("validate_write_candidate_entry_v1 requires non-empty allowed_files.")
            if not isinstance(inputs["max_touched_files"], int) or inputs["max_touched_files"] < 1:
                raise SystemExit("validate_write_candidate_entry_v1 requires max_touched_files >= 1.")
            if inputs["forbid_delete_rename_move"] is not True:
                raise SystemExit("validate_write_candidate_entry_v1 requires forbid_delete_rename_move=true.")
            if not str(inputs["manual_validation_gate"]).strip():
                raise SystemExit("validate_write_candidate_entry_v1 requires manual_validation_gate.")
            if not str(inputs["delegation_question"]).strip():
                raise SystemExit("validate_write_candidate_entry_v1 requires delegation_question.")
        request["action_payload"] = payload
    else:
        raise SystemExit(f"Unsupported action_type: {args.action_type}")

    return request


def main() -> int:
    args = parse_args()
    output_path = resolve_path(args.output_request_json)
    request = build_request(args)
    write_json(output_path, request)
    print(
        json.dumps(
            {
                "status": "PASS",
                "action_type": args.action_type,
                "output_request_json": rel_repo(output_path),
                "source_path": rel_repo(resolve_path(args.source_path)),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
