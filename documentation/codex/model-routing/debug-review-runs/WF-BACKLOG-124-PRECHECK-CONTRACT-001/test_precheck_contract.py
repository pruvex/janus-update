from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
RUN_DIR = Path(__file__).resolve().parent
VALIDATOR = REPO_ROOT / "documentation/codex/skills/janus-preimplementation-check/scripts/validate_precheck.py"
PRECHECK_SKILL = REPO_ROOT / "documentation/codex/skills/janus-preimplementation-check/SKILL.md"
EXECUTIONER_SKILL = REPO_ROOT / "documentation/codex/skills/janus-executioner/SKILL.md"

CODEX_NATIVE_FIELDS = (
    "NEXT STEP",
    "Recommended Skill: janus-executioner",
    "Recommended Model:",
    "Recommended Intelligence:",
    "User Action:",
)
LEGACY_COPYBLOCK_MARKERS = (
    "BEGIN COPY FOR SKILL 4",
    "END COPY FOR SKILL 4",
)


def run_validator(fixture: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(RUN_DIR / fixture)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_codex_native_precheck_contract_is_shared() -> None:
    valid = run_validator("valid_precheck.md")
    invalid = run_validator("invalid_precheck.md")

    assert valid.returncode == 0, valid.stdout + valid.stderr
    assert invalid.returncode != 0, "invalid legacy-style result unexpectedly passed"

    for path in (PRECHECK_SKILL, EXECUTIONER_SKILL):
        text = path.read_text(encoding="utf-8")
        for marker in LEGACY_COPYBLOCK_MARKERS:
            assert marker not in text, f"{marker} remains active in {path}"
        for field in CODEX_NATIVE_FIELDS:
            assert field in text, f"{field} missing from {path}"
