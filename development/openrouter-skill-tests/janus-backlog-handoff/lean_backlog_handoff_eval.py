#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-backlog-handoff."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-backlog-handoff" / "backlog_handoff_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-backlog-handoff" / "runs"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "qwen/qwen3.5-flash-02-23",
    "deepseek/deepseek-v4-flash",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus backlog-handoff assistant. "
    "Use only the redacted input package. "
    "Return exactly one JSON object and no prose. "
    "Do not claim authoritative backlog edits, status moves, handoff creation, Git authority, release authority, or final routing authority."
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def validate(parsed: dict, expected_artifact_path: str) -> list[str]:
    issues: list[str] = []
    required = [
        "status",
        "selected_backlog_id",
        "mode",
        "recommended_entry_point",
        "routing_reason",
        "routing_confidence",
        "required_artifact_path",
        "artifact_action",
        "recommended_next_skill",
        "next_skill_copy_prompt",
        "handoff_scope",
        "manual_review_needed",
        "notes",
    ]
    for field in required:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if parsed.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status invalid")
    if parsed.get("selected_backlog_id") != "BACKLOG-109":
        issues.append("selected_backlog_id invalid")
    if parsed.get("mode") != "SELECTED_HANDOFF":
        issues.append("mode invalid")
    if parsed.get("recommended_entry_point") not in {"PRE_IMPLEMENTATION_VERIFICATION", "SPEC_PIPELINE_START", "ROUTING_BLOCKED"}:
        issues.append("recommended_entry_point invalid")
    routing_confidence = parsed.get("routing_confidence")
    if isinstance(routing_confidence, str):
        if routing_confidence not in {"HIGH", "MEDIUM", "LOW"}:
            issues.append("routing_confidence invalid")
    elif isinstance(routing_confidence, (int, float)):
        if not (0.0 <= float(routing_confidence) <= 1.0):
            issues.append("routing_confidence invalid")
    else:
        issues.append("routing_confidence invalid")
    if parsed.get("artifact_action") not in {"CREATE_NEW", "REUSE_EXISTING", "NONE"}:
        issues.append("artifact_action invalid")
    if parsed.get("recommended_next_skill") not in {"janus-preimplementation-check", "janus-feature-design", "none"}:
        issues.append("recommended_next_skill invalid")
    if parsed.get("required_artifact_path") != expected_artifact_path:
        issues.append("required_artifact_path invalid")
    if parsed.get("manual_review_needed") not in {"YES", "NO"}:
        issues.append("manual_review_needed invalid")
    scope = parsed.get("handoff_scope")
    if not isinstance(scope, dict):
        issues.append("handoff_scope invalid")
    else:
        for field in [
            "backlog_item",
            "entry_point",
            "required_artifact",
            "required_next_skill",
            "evidence_paths",
            "dropped_context",
        ]:
            if field not in scope:
                issues.append(f"handoff_scope missing {field}")
    notes = parsed.get("notes")
    if not isinstance(notes, list) or not (1 <= len(notes) <= 4):
        issues.append("notes invalid")
    prompt = str(parsed.get("next_skill_copy_prompt") or "")
    if not prompt.strip():
        issues.append("next_skill_copy_prompt invalid")
    else:
        prompt_lower = prompt.lower()
        if "preimplementation" not in prompt_lower and "pre-implementation" not in prompt_lower and "backlog-109" not in prompt_lower:
            issues.append("next_skill_copy_prompt invalid")
    return issues


def main() -> int:
    input_payload = load_json(INPUT_PACKAGE)
    expected_artifact_path = str(input_payload["expected_artifact_path"])
    user_prompt = (
        "Return a JSON object with these exact top-level fields: "
        "status, selected_backlog_id, mode, recommended_entry_point, routing_reason, routing_confidence, "
        "required_artifact_path, artifact_action, recommended_next_skill, next_skill_copy_prompt, handoff_scope, "
        "manual_review_needed, notes.\n\n"
        "Rules:\n"
        "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
        "- selected_backlog_id must be BACKLOG-109\n"
        "- mode must be SELECTED_HANDOFF\n"
        "- recommended_entry_point must be PRE_IMPLEMENTATION_VERIFICATION, SPEC_PIPELINE_START, or ROUTING_BLOCKED\n"
        "- required_artifact_path must match the expected artifact path from the input package exactly\n"
        "- artifact_action must be CREATE_NEW, REUSE_EXISTING, or NONE\n"
        "- recommended_next_skill must be janus-preimplementation-check, janus-feature-design, or none\n"
        "- manual_review_needed must be YES or NO\n"
        "- handoff_scope must be an object with fields backlog_item, entry_point, required_artifact, required_next_skill, evidence_paths, dropped_context\n"
        "- notes must contain 1 to 4 short strings\n"
        "- do not claim authoritative backlog edits, status moves, or final handoff creation\n\n"
        f"Redacted input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
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
            "max_tokens": 1400,
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
            "Janus Backlog Handoff Lean Eval",
        ]
        completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        (run_dir / "wrapper_stdout.log").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "wrapper_stderr.log").write_text(completed.stderr, encoding="utf-8")
        result = {"model": model, "returncode": completed.returncode}
        if completed.returncode != 0:
            result["status"] = "WRAPPER_FAILED"
            write_json(run_dir / "lean_eval_result.json", result)
            continue
        response_body = load_json(run_dir / "response_body.json")
        response_summary = load_json(run_dir / "response_summary.json")
        content = extract_content(response_body)
        try:
            parsed = parse_payload(content)
            issues = validate(parsed, expected_artifact_path)
        except Exception as exc:
            parsed = {}
            issues = [f"parse_failed: {exc}"]
        write_json(run_dir / "parsed_response.json", parsed if parsed else {"raw_content": content})
        result.update(
            {
                "finish_reason": response_summary.get("finish_reason"),
                "actual_or_cost": response_summary.get("actual_or_cost"),
                "validation_issues": issues,
                "status": "PASS" if not issues and response_summary.get("finish_reason") != "length" else "FAIL",
                "response_path": str(run_dir / "response_body.json"),
            }
        )
        write_json(run_dir / "lean_eval_result.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
