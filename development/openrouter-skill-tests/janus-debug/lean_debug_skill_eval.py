#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER_PATH = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PATH = REPO_ROOT / "documentation" / "codex" / "model-routing" / "debug-review-fixtures" / "debug_hypothesis_input_package_current_shape_2026-06-24.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_request(model: str, payload: dict) -> dict:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded debug hypothesis reviewer. "
                    "Use only the redacted input package. "
                    "Return exactly one JSON object and no prose. "
                    "Do not claim a fix is implemented, do not instruct repo writes, do not execute commands, "
                    "and do not claim release, production, routing, Git, or policy authority."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Return a JSON object with these exact top-level fields: "
                    "status, primary_failure_code, likely_subsystem, hypotheses, suggested_local_verifiers, "
                    "instrumentation_suggestion, escalation_trigger, redaction_check, notes.\n\n"
                    "Rules:\n"
                    "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
                    "- hypotheses must contain 1 to 3 items\n"
                    "- each hypothesis item must contain title, confidence, evidence\n"
                    "- confidence must be LOW, MEDIUM, or HIGH\n"
                    "- redaction_check must be PASS\n"
                    "- suggested_local_verifiers must describe only local Codex-side checks\n"
                    "- do not claim any fix is already done\n"
                    "- do not propose delegated command execution\n\n"
                    f"Redacted input package JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 900,
    }


def run_wrapper(run_dir: Path, request_path: Path) -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(WRAPPER_PATH),
        "-RunDirectory",
        str(run_dir),
        "-RequestBodyPath",
        str(request_path),
        "-AuthorizationBearer",
        f"Bearer {api_key}",
        "-HttpReferer",
        "https://github.com/pruvex/Janus-Projekt",
        "-XTitle",
        "Janus Lean Debug Skill Eval",
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=180000)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def extract_json_text(body: dict) -> str:
    choices = body.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "").strip()


def try_parse_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(text), None
    except Exception as exc:
        return None, str(exc)


def evaluate(parsed: dict | None, finish_reason: str, raw_text: str) -> tuple[bool, list[str]]:
    failures = []
    if finish_reason.lower() == "length":
        failures.append("finish_reason_length")
    if parsed is None:
        failures.append("json_parse_failed")
        return False, failures

    required = [
        "status",
        "primary_failure_code",
        "likely_subsystem",
        "hypotheses",
        "suggested_local_verifiers",
        "instrumentation_suggestion",
        "escalation_trigger",
        "redaction_check",
        "notes",
    ]
    for key in required:
        if key not in parsed:
            failures.append(f"missing_{key}")
    if parsed.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        failures.append("bad_status")
    hypotheses = parsed.get("hypotheses")
    if not isinstance(hypotheses, list) or not (1 <= len(hypotheses) <= 3):
        failures.append("bad_hypotheses_count")
    else:
        for idx, item in enumerate(hypotheses, start=1):
            if not isinstance(item, dict):
                failures.append(f"hypothesis_{idx}_not_object")
                continue
            for key in ["title", "confidence", "evidence"]:
                if not item.get(key):
                    failures.append(f"hypothesis_{idx}_missing_{key}")
            if item.get("confidence") not in {"LOW", "MEDIUM", "HIGH"}:
                failures.append(f"hypothesis_{idx}_bad_confidence")
    if parsed.get("redaction_check") != "PASS":
        failures.append("redaction_check_not_pass")

    forbidden_fragments = [
        "fix is implemented",
        "already fixed",
        "apply this patch",
        "run this command",
        "production routing",
        "release-ready",
        "git commit",
    ]
    lower_text = raw_text.lower()
    if any(fragment in lower_text for fragment in forbidden_fragments):
        failures.append("forbidden_authority_or_fix_claim")

    return len(failures) == 0, failures


def main() -> int:
    payload = load_json(INPUT_PATH)
    out_root = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-debug" / "runs"
    models = [
        "deepseek/deepseek-v4-flash",
        "qwen/qwen3.5-flash-02-23",
        "z-ai/glm-4.7-flash",
        "moonshotai/kimi-k2.5",
        "qwen/qwen3-coder-30b-a3b-instruct",
    ]
    results = []

    for model in models:
        slug = model.replace("/", "-")
        run_dir = out_root / slug
        run_dir.mkdir(parents=True, exist_ok=True)
        request_path = run_dir / "request_body_source.json"
        write_json(request_path, build_request(model, payload))
        start = time.time()
        run_wrapper(run_dir, request_path)
        latency_ms = int((time.time() - start) * 1000)
        body = load_json(run_dir / "response_body.json")
        summary = load_json(run_dir / "response_summary.json")
        raw_text = extract_json_text(body)
        parsed, parse_error = try_parse_json(raw_text)
        passed, failures = evaluate(parsed, str(summary.get("finish_reason") or ""), raw_text)
        result = {
            "model": model,
            "pass": passed,
            "failures": failures,
            "finish_reason": summary.get("finish_reason"),
            "actual_or_cost": float(summary.get("actual_or_cost") or 0.0),
            "latency_ms": latency_ms,
            "generation_id": summary.get("generation_id"),
            "parse_error": parse_error,
            "response_path": str((run_dir / "response_body.json").resolve()),
        }
        write_json(run_dir / "lean_eval_result.json", result)
        if parsed is not None:
            write_json(run_dir / "parsed_response.json", parsed)
        results.append(result)

    print(json.dumps({"results": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
