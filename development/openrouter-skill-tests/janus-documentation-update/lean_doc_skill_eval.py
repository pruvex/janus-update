#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER_PATH = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"

SKILLS = {
    "DOC-SKILL-002": REPO_ROOT / "documentation" / "codex" / "model-routing" / "live-eval" / "DOC-SKILL-002-GPT54-LIVE-EVAL-001" / "input.sanitized.json",
    "DOC-SKILL-006": REPO_ROOT / "documentation" / "codex" / "model-routing" / "live-eval" / "DOC-SKILL-006-GPT54-LIVE-EVAL-001" / "input.sanitized.json",
    "DOC-SKILL-008": REPO_ROOT / "documentation" / "codex" / "model-routing" / "live-eval" / "DOC-SKILL-008-GPT54-LIVE-EVAL-001" / "input.sanitized.json",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def contains_all(text: str, needles: list[str]) -> bool:
    normalized = normalize(text)
    return all(needle.lower() in normalized for needle in needles)


def contains_any(text: str, needles: list[str]) -> bool:
    normalized = normalize(text)
    return any(needle.lower() in normalized for needle in needles)


def build_request(skill_id: str, payload: dict, model: str) -> dict:
    if skill_id == "DOC-SKILL-002":
        user = (
            "Return concise Markdown only.\n\n"
            "Write a neutral summary with these exact required lines somewhere in the output:\n"
            "- No production routing is approved.\n"
            "- No canonical routing-table update is made.\n"
            "- No global OpenRouter approval exists.\n"
            "- Price metadata is not quality evidence.\n\n"
            "You must preserve these labels exactly when relevant:\n"
            "- HOLD\n- UNKNOWN\n- EXPERIMENT_ONLY\n- CANDIDATE_NOT_APPROVED\n\n"
            "End with one next-step line that recommends fixture or baseline work before any live comparison.\n\n"
            f"Sanitized input JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
    elif skill_id == "DOC-SKILL-006":
        user = (
            "Return concise Markdown only.\n\n"
            "Reformat the note into clean Markdown and preserve authority boundaries.\n"
            "You must include these exact phrases:\n"
            "- planning only\n"
            "- no production routing\n"
            "- allowed scope\n"
            "- blocked scope\n"
            "- operator reminder\n"
            "- If a future test is explicitly approved\n\n"
            "You must keep these blocked items visible:\n"
            "- update routing table\n"
            "- approve production routing\n"
            "- run live calls\n"
            "- decide audit or release readiness\n\n"
            f"Sanitized input JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
    elif skill_id == "DOC-SKILL-008":
        user = (
            "Return concise Markdown only.\n\n"
            "Write a neutral changelog-style summary under a heading. Use '- ' bullet markers, not '*'.\n"
            "You must include these exact caveat lines:\n"
            "- No production routing was enabled.\n"
            "- No canonical routing-table update was made.\n"
            "- Auto Router remains experiment-only.\n"
            "- The 5.4 phase has not run live OR evaluations yet.\n\n"
            "You must also include these exact fact fragments somewhere:\n"
            "- 1 = Codex\n"
            "- 2 = OpenRouter\n"
            "- validation_result=PASS\n"
            "- seven approved mini skills\n\n"
            f"Sanitized input JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
    else:
        raise ValueError(skill_id)
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict documentation-eval assistant. "
                    "Use only the sanitized input. "
                    "Do not claim production authority, routing authority, release readiness, repo write authority, or global approval."
                ),
            },
            {"role": "user", "content": user},
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
        "Janus Lean Doc Skill Eval",
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=180000)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def extract_text(response_body: dict) -> str:
    choices = response_body.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def evaluate(skill_id: str, text: str, finish_reason: str) -> tuple[bool, list[str]]:
    failures: list[str] = []
    forbidden = [
        "production routing enabled",
        "canonical routing table updated",
        "release-ready",
        "global or approval",
        "globally approved",
        "replaces 5.4",
    ]
    if contains_any(text, forbidden):
        failures.append("forbidden_claim")
    if finish_reason.lower() == "length":
        failures.append("finish_reason_length")

    if skill_id == "DOC-SKILL-002":
        req = [
            "No production routing is approved.",
            "No canonical routing-table update is made.",
            "No global OpenRouter approval exists.",
            "Price metadata is not quality evidence.",
            "HOLD",
            "UNKNOWN",
            "EXPERIMENT_ONLY",
            "CANDIDATE_NOT_APPROVED",
        ]
        if not contains_all(text, req):
            failures.append("missing_required_doc_skill_002_markers")
    elif skill_id == "DOC-SKILL-006":
        req = [
            "planning only",
            "no production routing",
            "allowed scope",
            "blocked scope",
            "operator reminder",
            "If a future test is explicitly approved",
            "update routing table",
            "approve production routing",
            "run live calls",
            "decide audit or release readiness",
        ]
        if not contains_all(text, req):
            failures.append("missing_required_doc_skill_006_markers")
    elif skill_id == "DOC-SKILL-008":
        req = [
            "No production routing was enabled.",
            "No canonical routing-table update was made.",
            "Auto Router remains experiment-only.",
            "The 5.4 phase has not run live OR evaluations yet.",
            "1 = Codex",
            "2 = OpenRouter",
            "validation_result=PASS",
            "seven approved mini skills",
        ]
        if not contains_all(text, req):
            failures.append("missing_required_doc_skill_008_markers")
        if not re.search(r"^#+\s", text, re.MULTILINE):
            failures.append("missing_heading")
        if "- " not in text:
            failures.append("missing_dash_bullets")

    return (len(failures) == 0, failures)


def main() -> int:
    out_root = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-documentation-update" / "strict-runs"
    models = [
        "deepseek/deepseek-v4-flash",
        "qwen/qwen3.5-flash-02-23",
        "z-ai/glm-4.7-flash",
        "moonshotai/kimi-k2.5",
        "qwen/qwen3-coder-30b-a3b-instruct",
    ]
    results = []

    for skill_id, input_path in SKILLS.items():
        payload = load_json(input_path)
        for model in models:
            slug = model.replace("/", "-")
            run_dir = out_root / skill_id.lower() / slug
            run_dir.mkdir(parents=True, exist_ok=True)
            request_path = run_dir / "request_body_source.json"
            write_json(request_path, build_request(skill_id, payload, model))
            if not (run_dir / "response_body.json").exists():
                start = time.time()
                run_wrapper(run_dir, request_path)
                latency_ms = int((time.time() - start) * 1000)
            else:
                latency_ms = 0

            summary = load_json(run_dir / "response_summary.json")
            body = load_json(run_dir / "response_body.json")
            text = extract_text(body)
            passed, failures = evaluate(skill_id, text, str(summary.get("finish_reason") or ""))
            result = {
                "skill_id": skill_id,
                "model": model,
                "pass": passed,
                "failures": failures,
                "finish_reason": summary.get("finish_reason"),
                "actual_or_cost": float(summary.get("actual_or_cost") or 0.0),
                "latency_ms": latency_ms,
                "generation_id": summary.get("generation_id"),
                "response_path": str((run_dir / "response_body.json").resolve()),
            }
            write_json(run_dir / "lean_eval_result.json", result)
            results.append(result)

    print(json.dumps({"results": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
