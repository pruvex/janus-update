#!/usr/bin/env python3
"""Lean OpenRouter eval for janus-spec-generator."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "or_file_first_capture_wrapper.ps1"
INPUT_PACKAGE = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-generator" / "spec_generator_input_package.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-spec-generator" / "runs"

MODELS = [
    "qwen/qwen3-coder-30b-a3b-instruct",
    "qwen/qwen3.5-flash-02-23",
    "deepseek/deepseek-v4-flash",
    "moonshotai/kimi-k2.5",
    "z-ai/glm-4.7-flash",
]

SYSTEM_PROMPT = (
    "You are a bounded Janus spec-generator assistant. "
    "Use only the locked decision summary package. "
    "Return exactly one JSON object and no prose outside that JSON. "
    "Do not claim authoritative repo writes, task creation, implementation, Git authority, release authority, or final review authority. "
    "Return structured_spec as bounded JSON so Codex can render the final spec contract locally."
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
    required = [
        "status",
        "source_type",
        "source_path",
        "target_spec_path",
        "recommended_next_skill",
        "mechanical_cleanup_required",
        "notes",
    ]
    for field in required:
        if field not in parsed:
            issues.append(f"missing field: {field}")
    if "structured_spec" not in parsed and "spec_markdown" not in parsed:
        issues.append("missing field: structured_spec or spec_markdown")
    if parsed.get("status") not in {"PASS", "WEAK_SIGNAL", "BLOCKED"}:
        issues.append("status invalid")
    if parsed.get("source_type") != "LATEST_DECISION_SUMMARY":
        issues.append("source_type invalid")
    if parsed.get("source_path") != input_payload["source_path"]:
        issues.append("source_path invalid")
    if parsed.get("target_spec_path") != input_payload["target_spec_path"]:
        issues.append("target_spec_path invalid")
    if parsed.get("recommended_next_skill") not in {"janus-spec-review", "janus-spec-normalizer", "NEEDS_INFO"}:
        issues.append("recommended_next_skill invalid")
    if parsed.get("mechanical_cleanup_required") not in {"YES", "NO"}:
        issues.append("mechanical_cleanup_required invalid")
    notes = parsed.get("notes")
    if not isinstance(notes, list) or not (1 <= len(notes) <= 4):
        issues.append("notes invalid")
    spec_markdown = ""
    if isinstance(parsed.get("structured_spec"), dict):
        structured = parsed["structured_spec"]
        routing = structured.get("routing") if isinstance(structured.get("routing"), dict) else {}
        blocks = [
            "# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3",
            "",
            "## SPEC REVIEW EXECUTION ROUTING",
        ]
        for key in [
            "target_skill",
            "recommended_model",
            "recommended_reasoning",
            "new_chat",
            "complexity_score",
            "confidence",
            "dashboard_hint",
            "reason",
        ]:
            if key in routing:
                blocks.append(f"{key}: {routing[key]}")
        blocks.extend(
            [
                "",
                "## FEATURE IDENTITY",
                "- Name: placeholder",
                "",
                "## USER VALUE",
                "placeholder",
                "",
                "## TARGET SURFACE",
                "- Surface: placeholder",
                "",
                "## USER ACTION SURFACE",
                "- Action: placeholder",
                "",
                "## SYSTEM BEHAVIOR",
                "placeholder",
                "",
                "## DATA / PERSISTENCE",
                "- Persistence Required: NO",
                "",
                "## CONSTRAINTS",
                "placeholder",
                "",
                "## SECURITY / PRIVACY",
                "- Security: placeholder",
                "",
                "## EDGE CASES",
                "placeholder",
                "",
                "## DEFINITION OF DONE",
                "- [ ] placeholder",
                "",
                "## TEST STRATEGY",
                "- Test: placeholder",
                "",
                "## OUT OF SCOPE",
                "placeholder",
                "",
                "## INTERNAL COMPLEXITY BREAKDOWN",
            ]
        )
        internal = structured.get("internal_complexity_breakdown")
        if isinstance(internal, dict):
            for key in [
                "Scope Size",
                "Architectural Risk",
                "State / Persistence Complexity",
                "Cross-System Dependencies",
                "Ambiguity Level",
                "Total Complexity Score",
                "Routing Decision",
                "Routing Reasoning",
                "Routing Confidence",
                "Dashboard Hint",
            ]:
                if key in internal:
                    blocks.append(f"{key}: {internal[key]}")
        spec_markdown = "\n".join(blocks)
    else:
        spec_markdown = str(parsed.get("spec_markdown") or "")
    if not spec_markdown.strip():
        issues.append("spec_markdown missing")
        return issues
    for heading in input_payload["required_headings"]:
        if heading not in spec_markdown:
            issues.append(f"missing heading: {heading}")
    if "target_skill: janus-spec-review" not in spec_markdown:
        issues.append("routing block missing target_skill")
    if "recommended_model: 5.4" not in spec_markdown and "recommended_model: 5.5" not in spec_markdown:
        issues.append("routing block recommended_model invalid")
    if not any(token in spec_markdown for token in ["recommended_reasoning: low", "recommended_reasoning: medium", "recommended_reasoning: high"]):
        issues.append("routing block recommended_reasoning invalid")
    if not any(token in spec_markdown for token in ["new_chat: yes", "new_chat: no"]):
        issues.append("routing block new_chat invalid")
    if not any(token in spec_markdown for token in ["confidence: LOW", "confidence: MEDIUM", "confidence: HIGH"]):
        issues.append("routing block confidence invalid")
    if not any(token in spec_markdown for token in ["dashboard_hint: SAFE", "dashboard_hint: CAUTION", "dashboard_hint: CRITICAL"]):
        issues.append("routing block dashboard_hint invalid")
    if "- [ ]" not in spec_markdown:
        issues.append("definition of done checkboxes missing")
    forbidden_markers = ["TBD", "maybe", "Maybe", "optional nice-to-have"]
    for marker in forbidden_markers:
        if marker in spec_markdown:
            issues.append(f"forbidden marker present: {marker}")
    return issues


def main() -> int:
    input_payload = load_json(INPUT_PACKAGE)
    user_prompt = (
        "Return a JSON object with these exact top-level fields: "
        "status, source_type, source_path, target_spec_path, recommended_next_skill, "
        "mechanical_cleanup_required, structured_spec, notes.\n\n"
        "Rules:\n"
        "- status must be PASS, WEAK_SIGNAL, or BLOCKED\n"
        "- source_type must be LATEST_DECISION_SUMMARY\n"
        "- source_path must match the input package exactly\n"
        "- target_spec_path must match the input package exactly\n"
        "- recommended_next_skill must be janus-spec-review, janus-spec-normalizer, or NEEDS_INFO\n"
        "- mechanical_cleanup_required must be YES or NO\n"
        "- notes must be a JSON array with 1 to 4 short strings\n"
        "- structured_spec must be a JSON object, not markdown\n"
        "- structured_spec must contain these keys exactly: routing, feature_identity, user_value, target_surface, user_action_surface, system_behavior, data_persistence, constraints, security_privacy, edge_cases, definition_of_done, test_strategy, out_of_scope, internal_complexity_breakdown\n"
        "- routing must contain exactly: target_skill, recommended_model, recommended_reasoning, new_chat, complexity_score, confidence, dashboard_hint, reason\n"
        "- use exactly these routing value domains: target_skill=janus-spec-review; recommended_model=5.4 or 5.5; recommended_reasoning=low or medium or high; new_chat=yes or no; confidence=LOW or MEDIUM or HIGH; dashboard_hint=SAFE or CAUTION or CRITICAL\n"
        "- definition_of_done must be a JSON array of observable checklist lines without the '- [ ] ' prefix\n"
        "- do not claim authoritative repo writes or final review authority\n\n"
        f"Locked input package JSON:\n{json.dumps(input_payload, ensure_ascii=False, indent=2)}"
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
            "max_tokens": 2600,
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
            "Janus Spec Generator Lean Eval",
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
