#!/usr/bin/env python3
"""Lean OR candidate evaluator for janus-preimplementation-check."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(r"C:\KI\Janus-Projekt")
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-preimplementation-check" / "precheck_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-preimplementation-check" / "runs"

MODELS = [
    "deepseek/deepseek-v4-flash",
    "qwen/qwen3.5-flash-02-23",
    "z-ai/glm-4.7-flash",
    "moonshotai/kimi-k2.5",
    "qwen/qwen3-coder-30b-a3b-instruct",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus preimplementation-check reviewer. "
    "Use only the redacted input package. Return exactly one JSON object and no prose. "
    "Do not claim implementation is already complete, do not instruct repo writes, do not execute commands, "
    "and do not claim release, production, routing, Git, or policy authority."
)

FORBIDDEN_FRAGMENTS = [
    "already implemented",
    "apply this patch",
    "run this command",
    "git commit",
    "production routing",
    "release-ready",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_prompt(input_payload: dict) -> str:
    return (
        "Return a JSON object with these exact top-level fields: "
        "status, target_task, precheck_decision, artifact_identity, scope_status, risk_level, "
        "blocking_issues, required_evidence, execution_handoff_ready, notes.\n\n"
        "Rules:\n"
        "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
        "- precheck_decision must be PRECHECK_PASS_CANDIDATE, PRECHECK_BLOCK_CANDIDATE, or NEEDS_CODEX_REVIEW\n"
        "- artifact_identity must be PASS or FAIL\n"
        "- scope_status must be ATOMIC, DRIFT_RISK, or OUT_OF_SCOPE\n"
        "- risk_level must be LOW, MEDIUM, or HIGH\n"
        "- blocking_issues must contain 0 to 3 short strings\n"
        "- required_evidence must contain 1 to 4 short strings\n"
        "- execution_handoff_ready must be YES or NO\n"
        "- do not claim final release or final governance authority\n"
        "- do not propose delegated live execution\n\n"
        f"Redacted input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
    )


def build_request_body(model: str, prompt: str) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 1000,
    }


def extract_text(response_body: dict) -> str:
    choices = response_body.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first, dict) else {}
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    return ""


def parse_json_from_text(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return json.loads(stripped)


def evaluate_payload(response_body: dict) -> tuple[bool, list[str], dict | None, str | None]:
    failures: list[str] = []
    parse_error = None
    parsed = None

    choices = response_body.get("choices")
    finish_reason = None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        finish_reason = choices[0].get("finish_reason")
    if finish_reason == "length":
        failures.append("finish_reason_length")

    text = extract_text(response_body)
    lowered = text.lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in lowered:
            failures.append(f"forbidden_fragment:{fragment}")

    try:
        parsed = parse_json_from_text(text)
    except Exception as exc:
        parse_error = str(exc)
        failures.append("json_parse_failed")
        return False, failures, parsed, parse_error

    required = [
        "status",
        "target_task",
        "precheck_decision",
        "artifact_identity",
        "scope_status",
        "risk_level",
        "blocking_issues",
        "required_evidence",
        "execution_handoff_ready",
        "notes",
    ]
    for key in required:
        if key not in parsed:
            failures.append(f"missing:{key}")

    if parsed.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        failures.append("bad_status")
    if parsed.get("precheck_decision") not in {
        "PRECHECK_PASS_CANDIDATE",
        "PRECHECK_BLOCK_CANDIDATE",
        "NEEDS_CODEX_REVIEW",
    }:
        failures.append("bad_precheck_decision")
    if parsed.get("artifact_identity") not in {"PASS", "FAIL"}:
        failures.append("bad_artifact_identity")
    if parsed.get("scope_status") not in {"ATOMIC", "DRIFT_RISK", "OUT_OF_SCOPE"}:
        failures.append("bad_scope_status")
    if parsed.get("risk_level") not in {"LOW", "MEDIUM", "HIGH"}:
        failures.append("bad_risk_level")
    if parsed.get("execution_handoff_ready") not in {"YES", "NO"}:
        failures.append("bad_execution_handoff_ready")
    blocking_issues = parsed.get("blocking_issues")
    if not isinstance(blocking_issues, list) or len(blocking_issues) > 3:
        failures.append("bad_blocking_issues")
    required_evidence = parsed.get("required_evidence")
    if not isinstance(required_evidence, list) or not (1 <= len(required_evidence) <= 4):
        failures.append("bad_required_evidence")

    return len(failures) == 0, failures, parsed, parse_error


def run_one(model: str, prompt: str) -> dict:
    model_slug = model.replace("/", "-")
    run_dir = RUN_ROOT / model_slug
    run_dir.mkdir(parents=True, exist_ok=True)

    request_body = build_request_body(model, prompt)
    request_body_path = run_dir / "request_body_source.json"
    request_body_path.write_text(json.dumps(request_body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
        str(request_body_path),
        "-AuthorizationBearer",
        f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "-HttpReferer",
        "https://github.com/pruvex/Janus-Projekt",
        "-XTitle",
        "Lean janus-preimplementation-check OR candidate eval",
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"{model} wrapper call failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")

    response_body = load_json(run_dir / "response_body.json")
    response_summary = load_json(run_dir / "response_summary.json")
    ok, failures, parsed, parse_error = evaluate_payload(response_body)

    result = {
        "model": model,
        "pass": ok,
        "failures": failures,
        "finish_reason": (((response_body.get("choices") or [{}])[0]) if isinstance(response_body.get("choices"), list) else {}).get("finish_reason"),
        "actual_or_cost": response_summary.get("actual_or_cost"),
        "latency_ms": response_summary.get("latency_ms"),
        "generation_id": response_summary.get("generation_id"),
        "parse_error": parse_error,
        "response_path": str(run_dir / "response_body.json"),
    }
    if parsed is not None:
        (run_dir / "parsed_response.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "lean_eval_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    input_payload = load_json(INPUT_PACKAGE)
    prompt = build_prompt(input_payload)
    results = [run_one(model, prompt) for model in MODELS]
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
