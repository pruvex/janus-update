"""Runner-generated OpenRouter certification entry point. Do not edit."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.conformance.openrouter_live_certification import cli_main


PLAN_PATH = Path("documentation/test-runs/TEST-RUN-2026-07-17-006_plan.json")
EXPECTED_PLAN_SHA256 = "7C5AD398D15E7FC21A8AE70597881DC85F39764966C06DF6B753C51C544DC34F"


EXPECTED_EXECUTOR_SHA256 = "669A58209EA70F434341B9599100259D256880AEB1FD1C250CFA24756E9F82F3"


if __name__ == "__main__":
    raise SystemExit(
        cli_main(
            plan_path=PLAN_PATH,
            expected_plan_sha256=EXPECTED_PLAN_SHA256,
            expected_executor_sha256=EXPECTED_EXECUTOR_SHA256,
            runner_path=Path(__file__),
        )
    )
