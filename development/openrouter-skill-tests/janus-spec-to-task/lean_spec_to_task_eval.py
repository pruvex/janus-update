#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-spec-to-task."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-to-task" / "spec_to_task_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-to-task" / "runs"
VALIDATOR = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-spec-to-task" / "scripts" / "validate_task_artifact.py"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "deepseek/deepseek-v4-flash",
    "qwen/qwen3.5-flash-02-23",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus spec-to-task assistant. "
    "Use only the provided approved spec compilation package. "
    "Return exactly one JSON object and no prose outside that JSON. "
    "Do not implement code, do not invent product requirements, and do not claim authoritative repo writes."
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
    return normalized


def render_task_markdown(parsed: dict) -> str:
    lines = [
        parsed["task_root_id"],
        f"- Source Spec: {parsed['source_spec']}",
        f"- Backlog Item: {parsed['backlog_item']}",
        f"- Feature: {parsed['feature_name']}",
        f"- Generated At: {parsed['generated_at']}",
        "",
        "## Generated Tasks",
        "",
    ]
    for task in parsed["generated_tasks"]:
        lines.extend(
            [
                f"### {task['task_id']} {task['title']}",
                f"- Ziel: {task['ziel']}",
                f"- Scope: {task['scope']}",
                "- Files:",
            ]
        )
        for entry in task["files"]:
            lines.append(f"  - {entry}")
        lines.append("- Steps:")
        for entry in task["steps"]:
            lines.append(f"  - {entry}")
        lines.append("- Acceptance Criteria:")
        for entry in task["acceptance_criteria"]:
            lines.append(f"  - {entry}")
        lines.append("- Tests:")
        for entry in task["tests"]:
            lines.append(f"  - {entry}")
        lines.append(f"- Model: {task['model']}")
        lines.append(f"- Reason: {task['reason']}")
        lines.append("")
    lines.extend(
        [
            "@janus-task-breakdown",
            f"Spec: {parsed['source_spec']}",
            f"Task: {parsed['task_file_path']}",
            f"Backlog Item: {parsed['backlog_item']}",
            f"Target Task: {parsed['generated_tasks'][0]['task_id']}",
            "Mode: TASK_REFINEMENT",
            f"Execution Model: {parsed['execution_model']}",
            "Rules: USE_SPEC_AND_TASK_AS_SOURCE_OF_TRUTH_NO_IMPLEMENTATION_RELEASE_ONE_TARGET_TASK",
            "Expected Output: TASK_REFINED_PLUS_PRECHECK_HANDOFF",
            "",
        ]
    )
    return "\n".join(lines)


def validate(parsed: dict, input_payload: dict) -> list[str]:
    issues: list[str] = []
    required = [
        "task_root_id",
        "source_spec",
        "task_file_path",
        "backlog_item",
        "feature_name",
        "generated_at",
        "generated_tasks",
        "execution_model",
        "next_skill",
        "notes",
    ]
    for field in required:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if parsed.get("task_root_id") != input_payload["task_root_id"]:
        issues.append("task_root_id invalid")
    if parsed.get("source_spec") != input_payload["spec_path"]:
        issues.append("source_spec invalid")
    if parsed.get("task_file_path") != input_payload["task_file_path"]:
        issues.append("task_file_path invalid")
    if parsed.get("backlog_item") != input_payload["backlog_item"]:
        issues.append("backlog_item invalid")
    if parsed.get("feature_name") != input_payload["feature_name"]:
        issues.append("feature_name invalid")
    if parsed.get("execution_model") != input_payload["expected_execution_model"]:
        issues.append("execution_model invalid")
    if parsed.get("next_skill") != input_payload["expected_next_skill"]:
        issues.append("next_skill invalid")
    if not isinstance(parsed.get("generated_tasks"), list):
        issues.append("generated_tasks invalid")
        return issues
    tasks = parsed["generated_tasks"]
    if not input_payload["task_contract"]["minimum_task_count"] <= len(tasks) <= input_payload["task_contract"]["maximum_task_count"]:
        issues.append("generated task count invalid")
    expected_themes = list(input_payload["expected_slice_themes"])
    theme_anchors = input_payload["slice_theme_file_anchors"]
    seen_themes: list[str] = []
    banned_title_terms = ("review", "verify", "analyse", "analysis", "design", "non-regression")
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            issues.append(f"task {index} invalid")
            continue
        for field in input_payload["task_contract"]["required_task_fields"]:
            if field not in task:
                issues.append(f"task {index} missing {field}")
        if task.get("task_id") != f"{input_payload['task_root_id']}.{index}":
            issues.append(f"task {index} id invalid")
        if task.get("model") not in input_payload["task_contract"]["allowed_model_values"]:
            issues.append(f"task {index} model invalid")
        title = str(task.get("title", "")).lower()
        if any(term in title for term in banned_title_terms):
            issues.append(f"task {index} title review-only")
        for list_field in ["files", "steps", "acceptance_criteria", "tests"]:
            if not isinstance(task.get(list_field), list) or not task.get(list_field):
                issues.append(f"task {index} {list_field} invalid")
        theme = task.get("slice_theme")
        if theme not in expected_themes:
            issues.append(f"task {index} slice_theme invalid")
        else:
            seen_themes.append(theme)
            file_values = [str(value) for value in task.get("files", [])]
            anchors = theme_anchors.get(theme, [])
            if anchors and not any(anchor in file_value for anchor in anchors for file_value in file_values):
                issues.append(f"task {index} file anchors invalid")
    if sorted(seen_themes) != sorted(expected_themes):
        issues.append("slice theme coverage invalid")
    if not isinstance(parsed.get("notes"), list):
        issues.append("notes invalid")
    return issues


def run_validator(task_path: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["python", str(VALIDATOR), "--task", str(task_path)],
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
        "task_root_id, source_spec, task_file_path, backlog_item, feature_name, generated_at, generated_tasks, execution_model, next_skill, notes.\n\n"
        "Rules:\n"
        "- task_root_id must match the input package exactly\n"
        "- source_spec must match the input package exactly\n"
        "- task_file_path must match the input package exactly\n"
        "- backlog_item must match the input package exactly\n"
        "- feature_name must match the input package exactly\n"
        "- execution_model must be 5.4\n"
        "- next_skill must be janus-task-breakdown\n"
        "- generated_tasks must contain exactly 4 tasks\n"
        "- task ids must be TASK-SPEC21.1, TASK-SPEC21.2, TASK-SPEC21.3, TASK-SPEC21.4 in order\n"
        "- each task must contain task_id, title, ziel, scope, files, steps, acceptance_criteria, tests, model, reason, slice_theme\n"
        "- each files/steps/acceptance_criteria/tests field must be a non-empty array\n"
        "- slice_theme must cover each expected slice theme exactly once\n"
        "- each task files array must use only real repository-facing paths and must include at least one file anchor matching its slice theme\n"
        "- no task may be review-only, analysis-only, verification-only, or design-only\n"
        "- do not implement code and do not invent scope outside the approved spec package\n\n"
        f"Bounded task-compilation package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
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
            "max_tokens": 2400,
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
            "Janus Spec To Task Lean Eval",
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
            rendered_task = render_task_markdown(parsed) if not issues else ""
        except Exception as exc:
            parsed = {}
            issues = [f"parse_failed: {exc}"]
            rendered_task = ""
        write_json(run_dir / "parsed_response.json", parsed if parsed else {"raw_content": content})
        validator_stdout = ""
        validator_stderr = ""
        validator_rc = None
        if rendered_task:
            task_path = run_dir / "rendered_task_artifact.md"
            write_text(task_path, rendered_task)
            validator_rc, validator_stdout, validator_stderr = run_validator(task_path)
            write_text(run_dir / "task_validator_stdout.log", validator_stdout)
            write_text(run_dir / "task_validator_stderr.log", validator_stderr)
            if validator_rc != 0:
                issues.append("task_artifact_validator_failed")
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
