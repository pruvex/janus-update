#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-spec-review."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-review" / "spec_review_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-review" / "runs"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "qwen/qwen3.5-flash-02-23",
    "deepseek/deepseek-v4-flash",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus spec-review assistant. "
    "Use only the provided spec review package. "
    "Return exactly one JSON object and no prose outside that JSON. "
    "Do not create tasks, do not claim authoritative spec writes, and do not invent product decisions."
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


def normalize_payload(parsed: dict) -> dict:
    normalized = dict(parsed)

    model_recommendation = normalized.get("model_recommendation")
    if isinstance(model_recommendation, (int, float)):
        normalized["model_recommendation"] = str(model_recommendation)

    notes = normalized.get("notes")
    if isinstance(notes, str):
        normalized["notes"] = [notes]

    readiness_checklist = normalized.get("readiness_checklist")
    if isinstance(readiness_checklist, dict):
        normalized["readiness_checklist"] = [
            key for key, value in readiness_checklist.items() if value is True
        ]

    return normalized


def validate(parsed: dict, input_payload: dict) -> list[str]:
    issues: list[str] = []
    required = [
        "decision",
        "spec_path",
        "mode",
        "complexity_score",
        "risk",
        "model_recommendation",
        "readiness_checklist",
        "key_issues",
        "required_refinements",
        "split_recommendation",
        "metadata_written",
        "next_skill",
        "metadata_suggestion",
        "notes",
    ]
    for field in required:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if parsed.get("decision") not in {"APPROVED", "NEEDS_REVISION", "BLOCKED"}:
        issues.append("decision invalid")
    if parsed.get("spec_path") != input_payload["spec_path"]:
        issues.append("spec_path invalid")
    if parsed.get("mode") != "REVIEW_ONLY":
        issues.append("mode invalid")
    if not isinstance(parsed.get("complexity_score"), int):
        issues.append("complexity_score invalid")
    if parsed.get("risk") not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        issues.append("risk invalid")
    if parsed.get("model_recommendation") not in {"5.4", "5.5"}:
        issues.append("model_recommendation invalid")
    if parsed.get("next_skill") not in {"janus-spec-to-task", "janus-spec-generator", "janus-feature-design"}:
        issues.append("next_skill invalid")
    if parsed.get("metadata_written") not in {"YES", "NO"}:
        issues.append("metadata_written invalid")
    split = parsed.get("split_recommendation")
    if split not in {"YES", "NO"}:
        issues.append("split_recommendation invalid")
    for list_field in ["readiness_checklist", "key_issues", "required_refinements", "notes"]:
        value = parsed.get(list_field)
        if not isinstance(value, list):
            issues.append(f"{list_field} invalid")
    metadata = parsed.get("metadata_suggestion")
    if not isinstance(metadata, dict):
        issues.append("metadata_suggestion invalid")
    else:
        for field in [
            "review_status",
            "complexity_score",
            "risk",
            "recommended_review_model",
            "skill_1_ready",
            "split_required",
            "review_confidence",
            "review_source",
        ]:
            if field not in metadata:
                issues.append(f"metadata_suggestion missing {field}")
    return issues


def main() -> int:
    input_payload = load_json(INPUT_PACKAGE)
    user_prompt = (
        "Return a JSON object with these exact top-level fields: "
        "decision, spec_path, mode, complexity_score, risk, model_recommendation, readiness_checklist, "
        "key_issues, required_refinements, split_recommendation, metadata_written, next_skill, metadata_suggestion, notes.\n\n"
        "Rules:\n"
        "- decision must be APPROVED, NEEDS_REVISION, or BLOCKED\n"
        "- spec_path must match the input package exactly\n"
        "- mode must be REVIEW_ONLY\n"
        "- complexity_score must be an integer from 0 to 100\n"
        "- risk must be LOW, MEDIUM, HIGH, or CRITICAL\n"
        "- model_recommendation must be 5.4 or 5.5\n"
        "- split_recommendation and metadata_written must be YES or NO\n"
        "- next_skill must be janus-spec-to-task, janus-spec-generator, or janus-feature-design\n"
        "- metadata_suggestion must be an object with review_status, complexity_score, risk, recommended_review_model, skill_1_ready, split_required, review_confidence, review_source\n"
        "- do not create tasks and do not claim authoritative spec writes\n\n"
        f"Bounded review package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
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
            "Janus Spec Review Lean Eval",
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
            parsed = normalize_payload(parse_payload(content))
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
