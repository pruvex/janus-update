#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-feature-design."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-feature-design" / "feature_design_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-feature-design" / "runs"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "deepseek/deepseek-v4-flash",
    "qwen/qwen3.5-flash-02-23",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus feature-design assistant. "
    "Use only the redacted input package. "
    "Return exactly one JSON object and no prose. "
    "Do not claim implementation, task creation, Git authority, release authority, or final product decision authority. "
    "Your job is only to consolidate already-given answers into a bounded structured decision summary draft or exactly one blocking question."
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


def validate(parsed: dict, input_payload: dict) -> list[str]:
    issues: list[str] = []
    for field in ["status", "decision_state", "recommended_next_skill", "notes"]:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if parsed.get("decision_state") not in {"DECISION_SUMMARY_READY", "BLOCKING_QUESTION"}:
        issues.append("decision_state invalid")
    if parsed.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status invalid")
    if parsed.get("recommended_next_skill") not in {"janus-spec-generator", "janus-backlog-intake", "NEEDS_INFO"}:
        issues.append("recommended_next_skill invalid")
    notes = parsed.get("notes")
    if not isinstance(notes, list) or not (1 <= len(notes) <= 4):
        issues.append("notes invalid")
    if parsed.get("decision_state") == "DECISION_SUMMARY_READY":
        summary = parsed.get("structured_decision_summary")
        if not isinstance(summary, dict):
            issues.append("structured_decision_summary missing")
            return issues
        for key in [
            "Feature Name",
            "Primary Goal",
            "User Problem",
            "User Value",
            "Primary Target Surface",
            "Existing or New Surface",
            "Existence Confirmation",
            "User Trigger",
            "Success Behavior",
            "Failure Behavior",
            "User Action Surface",
            "Data / Persistence",
            "Security / Privacy",
            "Edge Cases",
            "Out of Scope",
            "Routing Decision",
            "Routing Reason",
            "Recommended Next Skill",
        ]:
            if not str(summary.get(key) or "").strip():
                issues.append(f"missing summary key: {key}")
        if summary.get("Routing Decision") != input_payload["expected_routing_decision"]:
            issues.append("routing decision mismatch")
        if summary.get("Recommended Next Skill") != input_payload["expected_next_skill"]:
            issues.append("recommended next skill mismatch")
    else:
        for field in ["blocking_question", "option_a", "option_b", "recommendation"]:
            if not str(parsed.get(field) or "").strip():
                issues.append(f"{field} missing for blocking state")
    return issues


def main() -> int:
    input_payload = load_json(INPUT_PACKAGE)
    user_prompt = (
        "Return a JSON object with these exact top-level fields: "
        "status, decision_state, recommended_next_skill, notes, structured_decision_summary, blocking_question, option_a, option_b, recommendation.\n\n"
        "Rules:\n"
        "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
        "- decision_state must be DECISION_SUMMARY_READY or BLOCKING_QUESTION\n"
        "- recommended_next_skill must be janus-spec-generator, janus-backlog-intake, or NEEDS_INFO\n"
        "- notes must contain 1 to 4 short strings\n"
        "- if decision_state is DECISION_SUMMARY_READY, structured_decision_summary must be an object with exactly these keys: Feature Name, Primary Goal, User Problem, User Value, Primary Target Surface, Existing or New Surface, Existence Confirmation, User Trigger, Success Behavior, Failure Behavior, User Action Surface, Data / Persistence, Security / Privacy, Edge Cases, Out of Scope, Routing Decision, Routing Reason, Recommended Next Skill\n"
        "- if decision_state is BLOCKING_QUESTION, provide exactly one blocking_question plus option_a, option_b, and recommendation, and do not invent a finished decision summary\n"
        "- Routing Decision must match the best bounded interpretation of the locked answers and should usually equal the expected routing decision when the package is sufficiently locked\n"
        "- Do not claim final product authority; Codex remains the final decision owner\n\n"
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
            "Janus Feature Design Lean Eval",
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
            issues = validate(parsed, input_payload)
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
