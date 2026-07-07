from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load(name: str) -> dict[str, str]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_shadow_runner_paths_match_after_fix() -> None:
    plan = _load("runner_plan_shadow.json")
    executed = _load("executed_runner_shadow.json")

    assert plan["runner_path"] == executed["runner_path"]
