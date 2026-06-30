#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-backlog-prioritization."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-backlog-prioritization" / "backlog_prioritization_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-backlog-prioritization" / "runs"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "qwen/qwen3.5-flash-02-23",
    "deepseek/deepseek-v4-flash",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus backlog-prioritization assistant. "
    "Use only the redacted input package. "
    "Return exactly one JSON object and no prose. "
    "Do not claim implementation, handoff, Git authority, release authority, or final routing authority."
)

USER_TEMPLATE = (
    "Return a JSON object with these exact top-level fields: "
    "status, review_mode, recommended_item_id, recommended_title, recommended_why, "
    "full_review_recommended, deep_reviewed_items, compact_reviewed_items, candidate_assessments, cache_update_suggestions, notes.\n\n"
    "Rules:\n"
    "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
    "- review_mode must be DELTA or FULL\n"
    "- full_review_recommended must be YES or NO\n"
    "- deep_reviewed_items must be 1 to 5 short backlog ids\n"
    "- compact_reviewed_items must be 0 to 10 short backlog ids\n"
    "- candidate_assessments must contain 1 to 3 objects with fields backlog_id, wichtigkeit, umsetzungsrisiko, aufwand, umsetzungsreife, empfehlung, rationale\n"
    "- cache_update_suggestions must contain 0 to 3 objects with fields backlog_id, wichtigkeit, umsetzungsrisiko, aufwand, umsetzungsreife, empfehlung\n"
    "- recommended_item_id must match one provided candidate item\n"
    "- do not claim implementation handoff or final execution authority\n\n"
    "Redacted input package JSON:\n{payload}"
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


def validate(parsed: dict) -> list[str]:
    issues: list[str] = []
    required = [
        "status",
        "review_mode",
        "recommended_item_id",
        "recommended_title",
        "recommended_why",
        "full_review_recommended",
        "deep_reviewed_items",
        "compact_reviewed_items",
        "candidate_assessments",
        "cache_update_suggestions",
        "notes",
    ]
    for field in required:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if parsed.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status invalid")
    if parsed.get("review_mode") not in {"DELTA", "FULL"}:
        issues.append("review_mode invalid")
    if parsed.get("full_review_recommended") not in {"YES", "NO"}:
        issues.append("full_review_recommended invalid")
    deep = parsed.get("deep_reviewed_items")
    if not isinstance(deep, list) or not (1 <= len(deep) <= 5):
        issues.append("deep_reviewed_items invalid")
    compact = parsed.get("compact_reviewed_items")
    if not isinstance(compact, list) or len(compact) > 10:
        issues.append("compact_reviewed_items invalid")
    assessments = parsed.get("candidate_assessments")
    if not isinstance(assessments, list) or not (1 <= len(assessments) <= 3):
        issues.append("candidate_assessments invalid")
    else:
        for idx, item in enumerate(assessments, start=1):
            if not isinstance(item, dict):
                issues.append(f"candidate_assessment {idx} not object")
                continue
            for key in ["backlog_id", "wichtigkeit", "umsetzungsrisiko", "aufwand", "umsetzungsreife", "empfehlung", "rationale"]:
                if key not in item:
                    issues.append(f"candidate_assessment {idx} missing {key}")
        candidate_ids = {
            str(item.get("backlog_id"))
            for item in assessments
            if isinstance(item, dict) and item.get("backlog_id")
        }
        if parsed.get("recommended_item_id") not in candidate_ids:
            issues.append("recommended_item_id invalid")
    suggestions = parsed.get("cache_update_suggestions")
    if not isinstance(suggestions, list) or len(suggestions) > 3:
        issues.append("cache_update_suggestions invalid")
    return issues


def main() -> int:
    payload = load_json(INPUT_PACKAGE)
    for model in MODELS:
        model_slug = model.replace("/", "-")
        run_dir = RUN_ROOT / model_slug
        request = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_TEMPLATE.format(payload=json.dumps(payload, ensure_ascii=False, indent=2))},
            ],
            "temperature": 0,
            "max_tokens": 1200,
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
            f"Bearer {__import__('os').environ['OPENROUTER_API_KEY']}",
            "-HttpReferer",
            "https://github.com/pruvex/Janus-Projekt",
            "-XTitle",
            "Janus Backlog Prioritization Lean Eval",
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
            issues = validate(parsed)
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
