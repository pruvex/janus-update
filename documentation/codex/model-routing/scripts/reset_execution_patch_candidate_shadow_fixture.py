#!/usr/bin/env python3
"""Restore the EX-001 shadow helper to its pre-session-budget baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_ROOT = (
    REPO_ROOT
    / "documentation"
    / "codex"
    / "model-routing"
    / "fixtures"
    / "cursor-shadow-catalog"
    / "execution_patch_candidate"
)
DEFAULT_BASELINE_FILE = FIXTURE_ROOT / "baseline" / "gate_prompt_shadow.py"
DEFAULT_TARGET_FILE = FIXTURE_ROOT / "sandbox" / "gate_prompt_shadow.py"


def reset_fixture(*, baseline_file: Path, target_file: Path) -> dict[str, object]:
    baseline_text = baseline_file.read_text(encoding="utf-8")
    target_file.write_text(baseline_text, encoding="utf-8")
    return {
        "validation_result": "PASS",
        "final_outcome": "SHADOW_FIXTURE_RESET_TO_BASELINE",
        "baseline_file": str(baseline_file),
        "target_file": str(target_file),
        "session_budget_present_after_reset": "Session-Budget:" in target_file.read_text(encoding="utf-8"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset the EX-001 shadow helper to its baseline state.")
    parser.add_argument("--baseline-file", type=Path, default=DEFAULT_BASELINE_FILE)
    parser.add_argument("--target-file", type=Path, default=DEFAULT_TARGET_FILE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = reset_fixture(baseline_file=args.baseline_file, target_file=args.target_file)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
