#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-task-breakdown."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-task-breakdown" / "task_breakdown_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-task-breakdown" / "runs"
VALIDATOR = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-task-breakdown" / "scripts" / "validate_task_handoff.py"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "deepseek/deepseek-v4-flash",
    "qwen/qwen3.5-flash-02-23",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus task-breakdown assistant. "
    "Use only the provided task refinement package. "
    "Return exactly one JSON object and no prose outside that JSON. "
    "Do not implement code, do not run precheck, and do not invent product requirements."
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def extract_content(response_body: dict) -> str:
    choices = response_body.get("choices") or []
    if not choices:
        return ""
    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
    return ""


def parse_payload(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(stripped[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("response content is not a JSON object")


def normalize_payload(parsed: dict) -> dict:
    normalized = dict(parsed)
    notes = normalized.get("notes")
    if isinstance(notes, str):
        normalized["notes"] = [notes]
    tests = normalized.get("tests")
    if isinstance(tests, list):
        normalized["tests"] = "; ".join(str(item) for item in tests if str(item).strip())
    acceptance = normalized.get("acceptance_criteria")
    if isinstance(acceptance, list):
        normalized["acceptance_criteria"] = "; ".join(str(item) for item in acceptance if str(item).strip())
    return normalized


def render_breakdown_markdown(parsed: dict) -> str:
    return "\n".join(
        [
            "TASK BREAKDOWN RESULT",
            f"- Spec: {parsed['spec_path']}",
            f"- Task File: {parsed['task_file_path']}",
            f"- Target Task: {parsed['target_task']}",
            f"- Decision: {parsed['decision']}",
            f"- Source Of Truth: {parsed['source_of_truth']}",
            f"- Files: {', '.join(parsed['files'])}",
            f"- Acceptance Criteria: {parsed['acceptance_criteria']}",
            f"- Tests: {parsed['tests']}",
            f"- Execution Model: {parsed['execution_model']}",
            f"- Readiness: {parsed['readiness']}",
            f"- Next Skill: {parsed['next_skill']}",
            f"- Model Recommendation: {parsed['model_recommendation']}",
            "",
            "@janus-preimplementation-check",
            f"Spec: {parsed['spec_path']}",
            f"Task: {parsed['task_file_path']}",
            f"Backlog Item: {parsed['backlog_item']}",
            f"Target Task: {parsed['target_task']}",
            f"Target Subtask: {parsed['target_subtask']}",
            "Mode: SINGLE_TASK_PRECHECK",
            f"Execution Model: {parsed['execution_model']}",
            "Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR",
            "Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED",
            "",
        ]
    )


def validate(parsed: dict, input_payload: dict) -> list[str]:
    issues: list[str] = []
    required = [
        "spec_path",
        "task_file_path",
        "backlog_item",
        "target_task",
        "target_subtask",
        "decision",
        "source_of_truth",
        "files",
        "acceptance_criteria",
        "tests",
        "execution_model",
        "readiness",
        "next_skill",
        "model_recommendation",
        "notes",
    ]
    for field in required:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if parsed.get("spec_path") != input_payload["spec_path"]:
        issues.append("spec_path invalid")
    if parsed.get("task_file_path") != input_payload["task_file_path"]:
        issues.append("task_file_path invalid")
    if parsed.get("backlog_item") != input_payload["backlog_item"]:
        issues.append("backlog_item invalid")
    if parsed.get("target_task") != input_payload["expected_target_task"]:
        issues.append("target_task invalid")
    if parsed.get("target_subtask") != input_payload["expected_target_subtask"]:
        issues.append("target_subtask invalid")
    if parsed.get("decision") != input_payload["expected_decision"]:
        issues.append("decision invalid")
    if parsed.get("next_skill") != input_payload["expected_next_skill"]:
        issues.append("next_skill invalid")
    if parsed.get("execution_model") != input_payload["expected_execution_model"]:
        issues.append("execution_model invalid")
    if parsed.get("model_recommendation") != input_payload["expected_execution_model"]:
        issues.append("model_recommendation invalid")
    files = parsed.get("files")
    if not isinstance(files, list) or not files:
        issues.append("files invalid")
    else:
        if sorted(files) != sorted(input_payload["required_files"]):
            issues.append("files mismatch")
    tests = str(parsed.get("tests", ""))
    for fragment in input_payload["required_test_focus"]:
        if fragment not in tests:
            issues.append("tests missing required focus")
            break
    acceptance = str(parsed.get("acceptance_criteria", ""))
    for fragment in input_payload["required_acceptance_focus"]:
        if fragment not in acceptance:
            issues.append("acceptance_criteria missing required focus")
            break
    readiness = str(parsed.get("readiness", "")).strip()
    if not readiness:
        issues.append("readiness invalid")
    source_of_truth = str(parsed.get("source_of_truth", ""))
    if not (
        input_payload["spec_path"] in source_of_truth
        or "Spec 21" in source_of_truth
        or "TASK-SPEC21 artifact" in source_of_truth
    ):
        issues.append("source_of_truth invalid")
    notes = parsed.get("notes")
    if not isinstance(notes, list):
        issues.append("notes invalid")
    return issues


def run_validator(task_path: Path, target_task: str) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["python", str(VALIDATOR), "--task", str(task_path), "--target", target_task],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def main() -> int:
    input_payload = load_json(INPUT_PACKAGE)
    user_prompt = (
        "Return a JSON object with these exact top-level fields: "
        "spec_path, task_file_path, backlog_item, target_task, target_subtask, decision, source_of_truth, files, acceptance_criteria, tests, execution_model, readiness, next_skill, model_recommendation, notes.\n\n"
        "Rules:\n"
        "- spec_path must match the input package exactly\n"
        "- task_file_path must match the input package exactly\n"
        "- backlog_item must match the input package exactly\n"
        "- target_task must be the single next atomic precheck-ready task from the input package\n"
        "- target_subtask must be N/A\n"
        "- decision must be TASK DESIGN COMPLETE\n"
        "- files must be exactly the required file list from the input package\n"
        "- acceptance_criteria must preserve the required acceptance focus\n"
        "- tests must preserve the required test focus\n"
        "- execution_model and model_recommendation must both be 5.4\n"
        "- next_skill must be janus-preimplementation-check\n"
        "- do not select multiple tasks and do not widen to TASK-SPEC21.4\n"
        "- do not implement code and do not run precheck\n\n"
        f"Bounded task-breakdown package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
    )

    for model in MODELS:
        model_slug = model.replace("/", "-")
        run_dir = RUN_ROOT / model_slug
        request = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_tokens": 1800,
        }
        request_path = run_dir / "request_body_source.json"
        write_json(request_path, request)
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(WRAPPER),
            "-RunDirectory",
            str(run_dir),
            "-RequestBodyPath",
            str(request_path),
            "-AuthorizationBearer",
            f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "-HttpReferer",
            "https://github.com/pruvex/Janus-Projekt",
            "-XTitle",
            "Janus Task Breakdown Lean Eval",
        ]
        completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        write_text(run_dir / "wrapper_stdout.log", completed.stdout)
        write_text(run_dir / "wrapper_stderr.log", completed.stderr)
        result = {"model": model, "returncode": completed.returncode}
        if completed.returncode != 0:
            result["status"] = "WRAPPER_FAILED"
            write_json(run_dir / "lean_eval_result.json", result)
            continue
        response_body = load_json(run_dir / "response_body.json")
        response_summary = load_json(run_dir / "response_summary.json")
        content = extract_content(response_body)
        try:
            parsed = normalize_payload(parse_payload(content))
            issues = validate(parsed, input_payload)
            rendered = render_breakdown_markdown(parsed) if not issues else ""
        except Exception as exc:
            parsed = {}
            issues = [f"parse_failed: {exc}"]
            rendered = ""
        write_json(run_dir / "parsed_response.json", parsed if parsed else {"raw_content": content})
        validator_stdout = ""
        validator_stderr = ""
        validator_rc = None
        if rendered:
            breakdown_path = run_dir / "rendered_task_breakdown.md"
            write_text(breakdown_path, rendered)
            validator_rc, validator_stdout, validator_stderr = run_validator(breakdown_path, input_payload["expected_target_task"])
            write_text(run_dir / "task_validator_stdout.log", validator_stdout)
            write_text(run_dir / "task_validator_stderr.log", validator_stderr)
            if validator_rc != 0:
                issues.append("task_handoff_validator_failed")
        result.update(
            {
                "finish_reason": response_summary.get("finish_reason"),
                "actual_or_cost": response_summary.get("actual_or_cost"),
                "validation_issues": issues,
                "status": "PASS" if not issues and response_summary.get("finish_reason") != "length" else "FAIL",
                "validator_returncode": validator_rc,
                "response_path": str(run_dir / "response_body.json"),
            }
        )
        write_json(run_dir / "lean_eval_result.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
