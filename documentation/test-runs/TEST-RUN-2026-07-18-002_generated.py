"""Runner-generated OpenRouter certification entry point. Do not edit."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.conformance.openrouter_live_certification import cli_main


PLAN_PATH = Path("documentation/test-runs/TEST-RUN-2026-07-18-002_plan.json")
EXPECTED_PLAN_SHA256 = "D2D1ECAC9BE734705AC7E8D76E13A260FC71F4D034AAD313C057E85E16E531F1"


EXPECTED_EXECUTOR_SHA256 = "400CC413BAD76BC4DDAAA25242ABFADEFAB88D9D865A992E9FEC3919FE5DA3CF"


if __name__ == "__main__":
    raise SystemExit(
        cli_main(
            plan_path=PLAN_PATH,
            expected_plan_sha256=EXPECTED_PLAN_SHA256,
            expected_executor_sha256=EXPECTED_EXECUTOR_SHA256,
            runner_path=Path(__file__),
        )
    )
