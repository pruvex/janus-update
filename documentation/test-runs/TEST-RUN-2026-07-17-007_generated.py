"""Runner-generated OpenRouter certification entry point. Do not edit."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.conformance.openrouter_live_certification import cli_main


PLAN_PATH = Path("documentation/test-runs/TEST-RUN-2026-07-17-007_plan.json")
EXPECTED_PLAN_SHA256 = "2E5B18BA328CF9F6E77C276438B14A3D4D944610DBCCBAFDC7362FFA8F8CC42E"


EXPECTED_EXECUTOR_SHA256 = "16DAC926F03647C8FEACDEC40D94ACFEE5845C5B3520C83F2886035593CF4721"


if __name__ == "__main__":
    raise SystemExit(
        cli_main(
            plan_path=PLAN_PATH,
            expected_plan_sha256=EXPECTED_PLAN_SHA256,
            expected_executor_sha256=EXPECTED_EXECUTOR_SHA256,
            runner_path=Path(__file__),
        )
    )
