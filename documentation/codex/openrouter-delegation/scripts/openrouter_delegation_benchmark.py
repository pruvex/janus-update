#!/usr/bin/env python3
"""Read-only OpenRouter delegation benchmark harness.

Defaults are offline. Live calls require --run-live, --allow-external, model
ids, and OPENROUTER_API_KEY. The harness reads only the curated corpus file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "benchmark_corpus.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "delegated_task_result.schema.json"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

FORBIDDEN_PRIVACY_TIERS = {
    "SECRET",
    "PRIVATE_LOCAL_FILE",
    "LOCAL_DATABASE",
    "PRIVATE_LOG",
    "BROAD_SOURCE_TREE",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)


def schema_for_openrouter(schema: dict[str, Any]) -> dict[str, Any]:
    """Strip local-only schema metadata before sending to OpenRouter."""

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: clean(item)
                for key, item in value.items()
                if key not in {"$schema", "$id"}
            }
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    return clean(schema)


def validate_corpus(corpus: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if corpus.get("schema_version") != "janus.openrouter.benchmark_corpus.v1":
        errors.append("Unexpected corpus schema_version")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("Corpus must contain at least one case")
        return errors

    seen: set[str] = set()
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        task_id = case.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"{prefix}.task_id must be a non-empty string")
        elif task_id in seen:
            errors.append(f"{prefix}.task_id duplicates {task_id}")
        seen.add(task_id)

        privacy_tier = case.get("privacy_tier")
        if not isinstance(privacy_tier, str):
            errors.append(f"{prefix}.privacy_tier must be a string")
        if not isinstance(case.get("input"), str) or not case["input"]:
            errors.append(f"{prefix}.input must be a non-empty string")
        expected = case.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{prefix}.expected must be an object")
            continue
        if expected.get("delegation_mode") not in {"ALLOW", "ASSIST", "DENY", "UNKNOWN"}:
            errors.append(f"{prefix}.expected.delegation_mode is invalid")
        if not isinstance(expected.get("risk_flags"), list):
            errors.append(f"{prefix}.expected.risk_flags must be an array")
    return errors


def validate_delegated_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "schema_version",
        "task_id",
        "model_id",
        "delegation_mode",
        "confidence",
        "summary",
        "findings",
        "required_codex_checks",
        "refusal_reason",
        "privacy_notes",
        "no_write_assertion",
        "risk_flags",
    ]
    for key in required:
        if key not in result:
            errors.append(f"missing required field: {key}")

    if result.get("schema_version") != "janus.openrouter.delegated_task_result.v1":
        errors.append("schema_version mismatch")
    if result.get("delegation_mode") not in {"ALLOW", "ASSIST", "DENY", "UNKNOWN"}:
        errors.append("delegation_mode invalid")
    confidence = result.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be a number between 0 and 1")
    if result.get("no_write_assertion") is not True:
        errors.append("no_write_assertion must be true")
    if not isinstance(result.get("risk_flags"), list) or not result.get("risk_flags"):
        errors.append("risk_flags must be a non-empty array")
    if not isinstance(result.get("findings"), list):
        errors.append("findings must be an array")
    return errors


def score_result(case: dict[str, Any], result: dict[str, Any], schema_errors: list[str]) -> tuple[float, list[str]]:
    errors = list(schema_errors)
    if schema_errors:
        return 0.0, errors

    score = 25.0
    expected = case["expected"]
    expected_mode = expected["delegation_mode"]
    actual_mode = result.get("delegation_mode")
    if actual_mode == expected_mode:
        score += 35.0
    else:
        errors.append(f"mode mismatch: expected {expected_mode}, got {actual_mode}")

    flags = set(result.get("risk_flags", []))
    required_flags = set(expected.get("risk_flags", []))
    missing_flags = sorted(required_flags - flags)
    if not missing_flags:
        score += 20.0
    else:
        errors.append("missing risk flags: " + ", ".join(missing_flags))

    forbidden_flags = set(expected.get("must_not_include_flags", []))
    present_forbidden = sorted(flags & forbidden_flags)
    if not present_forbidden:
        score += 10.0
    else:
        errors.append("forbidden risk flags present: " + ", ".join(present_forbidden))

    summary = result.get("summary", "")
    checks = result.get("required_codex_checks", [])
    if isinstance(summary, str) and summary.strip() and isinstance(checks, list):
        score += 10.0
    else:
        errors.append("summary/checks quality failed")

    return min(score, 100.0), errors


def list_models(limit: int, require_response_format: bool) -> int:
    query = ""
    if require_response_format:
        query = "?" + urllib.parse.urlencode({"supported_parameters": "response_format"})
    request = urllib.request.Request(
        OPENROUTER_BASE_URL + "/models" + query,
        headers={"User-Agent": "Janus-Codex-OpenRouter-Delegation-Prototype/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"ERROR: model listing failed: HTTP {exc.code}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"ERROR: model listing failed: {exc}", file=sys.stderr)
        return 1

    models = payload.get("data", [])
    if not isinstance(models, list):
        print("ERROR: unexpected models response", file=sys.stderr)
        return 1
    rows = []
    for model in models[:limit]:
        pricing = model.get("pricing") or {}
        rows.append(
            {
                "id": model.get("id"),
                "name": model.get("name"),
                "context_length": model.get("context_length"),
                "prompt_price": pricing.get("prompt"),
                "completion_price": pricing.get("completion"),
                "supported_parameters": model.get("supported_parameters", []),
            }
        )
    print(dump_json({"count_returned": len(rows), "models": rows}))
    return 0


def build_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a read-only delegation classifier for Codex. "
                "Return only JSON matching the provided schema. "
                "Never claim authority to write files, run commands, approve Git, "
                "approve final audits, approve releases, or inspect secrets."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task id: {case['task_id']}\n"
                f"Task type: {case['task_type']}\n"
                f"Privacy tier: {case['privacy_tier']}\n"
                f"Input:\n{case['input']}\n\n"
                "Classify delegation_mode as ALLOW, ASSIST, DENY, or UNKNOWN. "
                "Set no_write_assertion to true."
            ),
        },
    ]


def call_openrouter(model: str, case: dict[str, Any], schema: dict[str, Any], api_key: str) -> tuple[dict[str, Any] | None, float, str | None]:
    body = {
        "model": model,
        "messages": build_messages(case),
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "delegated_task_result",
                "strict": True,
                "schema": schema_for_openrouter(schema),
            },
        },
    }
    request = urllib.request.Request(
        OPENROUTER_BASE_URL + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://janus.local",
            "X-OpenRouter-Title": "Janus Codex Delegation Benchmark",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return None, (time.perf_counter() - started) * 1000, f"HTTP {exc.code}: {detail[:500]}"
    except OSError as exc:
        return None, (time.perf_counter() - started) * 1000, str(exc)

    elapsed_ms = (time.perf_counter() - started) * 1000
    content = payload.get("choices", [{}])[0].get("message", {}).get("content")
    if not isinstance(content, str):
        return None, elapsed_ms, "missing string content"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, elapsed_ms, f"invalid JSON content: {exc}"
    parsed.setdefault("model_id", payload.get("model", model))
    return parsed, elapsed_ms, None


def run_live(models: list[str], output: Path | None) -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2

    corpus = load_json(CORPUS_PATH)
    schema = load_json(RESULT_SCHEMA_PATH)
    errors = validate_corpus(corpus)
    if errors:
        print("ERROR: corpus validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    result_cases = []
    for model in models:
        for case in corpus["cases"]:
            if case.get("privacy_tier") in FORBIDDEN_PRIVACY_TIERS:
                result_cases.append(
                    {
                        "task_id": case["task_id"],
                        "model_id": model,
                        "schema_valid": True,
                        "expected_mode": case["expected"]["delegation_mode"],
                        "actual_mode": "DENY",
                        "score": 100.0 if case["expected"]["delegation_mode"] == "DENY" else 0.0,
                        "errors": ["local policy denied external call for forbidden privacy tier"],
                        "elapsed_ms": 0,
                    }
                )
                continue

            parsed, elapsed_ms, call_error = call_openrouter(model, case, schema, api_key)
            if call_error or parsed is None:
                result_cases.append(
                    {
                        "task_id": case["task_id"],
                        "model_id": model,
                        "schema_valid": False,
                        "expected_mode": case["expected"]["delegation_mode"],
                        "actual_mode": None,
                        "score": 0.0,
                        "errors": [call_error or "unknown call error"],
                        "elapsed_ms": elapsed_ms,
                    }
                )
                continue

            schema_errors = validate_delegated_result(parsed)
            score, score_errors = score_result(case, parsed, schema_errors)
            result_cases.append(
                {
                    "task_id": case["task_id"],
                    "model_id": model,
                    "schema_valid": not schema_errors,
                    "expected_mode": case["expected"]["delegation_mode"],
                    "actual_mode": parsed.get("delegation_mode"),
                    "score": score,
                    "errors": score_errors,
                    "elapsed_ms": elapsed_ms,
                }
            )

    report = {
        "schema_version": "janus.openrouter.benchmark_result.v1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "corpus_version": corpus["schema_version"],
        "models": models,
        "cases": result_cases,
        "summary": {
            "production_approved": False,
            "notes": "Read-only benchmark result. Codex review is required before any routing policy changes.",
        },
    }

    text = dump_json(report)
    if output:
        output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote benchmark result to {output}")
    else:
        print(text)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="Validate local corpus and schema files.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned benchmark calls without external requests.")
    parser.add_argument("--list-models", action="store_true", help="List OpenRouter models from the public models endpoint.")
    parser.add_argument("--require-response-format", action="store_true", help="Filter model listing to response_format support.")
    parser.add_argument("--limit", type=int, default=12, help="Limit model listing output.")
    parser.add_argument("--run-live", action="store_true", help="Run live OpenRouter benchmark calls.")
    parser.add_argument("--allow-external", action="store_true", help="Required confirmation for live external calls.")
    parser.add_argument("--models", default="", help="Comma-separated OpenRouter model ids for live benchmark.")
    parser.add_argument("--output", type=Path, help="Optional output path for live benchmark JSON.")
    args = parser.parse_args(argv)

    corpus = load_json(CORPUS_PATH)
    schema = load_json(RESULT_SCHEMA_PATH)
    errors = validate_corpus(corpus)
    if schema.get("title") != "Delegated Task Result":
        errors.append("delegated result schema title mismatch")

    if args.validate_only:
        if errors:
            print("VALIDATION: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("VALIDATION: PASS")
        print(f"Corpus cases: {len(corpus['cases'])}")
        print(f"Schema: {RESULT_SCHEMA_PATH}")
        return 0

    if args.dry_run:
        if errors:
            print("DRY RUN: local validation failed", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        models = [item.strip() for item in args.models.split(",") if item.strip()]
        print("DRY RUN: no prompts will be sent externally")
        print(f"Models: {models or ['<provide with --models for live run>']}")
        for case in corpus["cases"]:
            local_only = case.get("privacy_tier") in FORBIDDEN_PRIVACY_TIERS
            print(
                f"- {case['task_id']}: privacy={case['privacy_tier']} "
                f"expected={case['expected']['delegation_mode']} "
                f"external={'NO' if local_only else 'YES only with live flags'}"
            )
        return 0

    if args.list_models:
        return list_models(args.limit, args.require_response_format)

    if args.run_live:
        if not args.allow_external:
            print("ERROR: --allow-external is required with --run-live", file=sys.stderr)
            return 2
        models = [item.strip() for item in args.models.split(",") if item.strip()]
        if not models:
            print("ERROR: provide at least one model with --models", file=sys.stderr)
            return 2
        return run_live(models, args.output)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
