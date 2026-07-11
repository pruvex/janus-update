#!/usr/bin/env python3
"""Lean OR candidate evaluator for janus-executioner execution_patch_candidate."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(r"C:\KI\Janus-Projekt")
RUNNER = REPO_ROOT / "documentation" / "codex" / "model-routing" / "scripts" / "openrouter_direct_execution_patch_candidate_runner.py"
INPUT_PACKAGE = REPO_ROOT / "documentation" / "codex" / "model-routing" / "execution-review-fixtures" / "backlog_108_execution_patch_candidate_input_package_current_shape_2026-06-24.json"
RUN_ROOT = REPO_ROOT / "development" / "openrouter-skill-tests" / "janus-executioner" / "runs"

MODELS = [
    "deepseek/deepseek-v4-flash",
    "qwen/qwen3.5-flash-02-23",
    "z-ai/glm-4.7-flash",
    "moonshotai/kimi-k2.5",
    "qwen/qwen3-coder-30b-a3b-instruct",
]


def run_one(model: str) -> dict:
    model_slug = model.replace("/", "-")
    workflow_id = f"LEAN-EXEC-{model_slug}"
    run_dir = RUN_ROOT / model_slug
    run_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "python",
        str(RUNNER),
        "--task-label",
        "Lean execution patch candidate current-shape",
        "--normal-target-model",
        "5.4 medium",
        "--model",
        model,
        "--workflow-id",
        workflow_id,
        "--input-package-json",
        str(INPUT_PACKAGE),
        "--estimated-prompt-tokens",
        "3600",
        "--estimated-completion-tokens",
        "700",
        "--estimated-or-cost",
        "0.0035",
        "--cost-estimate-confidence-percent",
        "65",
        "--cost-estimate-basis",
        f"{model}+execution_patch_candidate+lean_eval",
        "--prompt-template-hash",
        "lean_execution_patch_candidate_v1",
        "--task-variant",
        "execution_patch_candidate",
        "--price-snapshot-source",
        "lean_eval_manual_baseline",
        "--price-snapshot-timestamp",
        "2026-06-25T00:00:00+02:00",
        "--estimated-codex-effort",
        "medium",
        "--execute-live",
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    (run_dir / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (run_dir / "stderr.log").write_text(completed.stderr, encoding="utf-8")

    if completed.returncode != 0:
        summary = {
            "model": model,
            "pass": False,
            "validation_result": "FAIL",
            "final_outcome": "RUNNER_FAILED",
            "parse_error": completed.stderr.strip() or completed.stdout.strip(),
        }
        (run_dir / "lean_eval_result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return summary

    parsed = json.loads(completed.stdout)
    response_summary_path = Path(parsed["response_summary_path"]) if parsed.get("response_summary_path") else None
    response_summary = json.loads(response_summary_path.read_text(encoding="utf-8-sig")) if response_summary_path and response_summary_path.exists() else {}
    validation_summary_path = Path(parsed["validation_summary_path"]) if parsed.get("validation_summary_path") else None
    validation_summary = json.loads(validation_summary_path.read_text(encoding="utf-8-sig")) if validation_summary_path and validation_summary_path.exists() else {}
    result = {
        "model": model,
        "pass": parsed.get("validation_result") == "PASS",
        "validation_result": parsed.get("validation_result"),
        "final_outcome": parsed.get("final_outcome"),
        "actual_or_cost": parsed.get("actual_or_cost"),
        "generation_id": response_summary.get("generation_id"),
        "finish_reason": response_summary.get("finish_reason"),
        "changed_files": (json.loads(Path(parsed["patch_candidate_result_path"]).read_text(encoding="utf-8-sig")).get("changed_files") if parsed.get("patch_candidate_result_path") else []),
        "issues": validation_summary.get("issues", []),
        "response_summary_path": parsed.get("response_summary_path"),
        "operator_summary_path": str((REPO_ROOT / "documentation" / "codex" / "model-routing" / "execution-direct-or-runs" / workflow_id / "operator_summary.json")),
    }
    (run_dir / "lean_eval_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    results = [run_one(model) for model in MODELS]
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
