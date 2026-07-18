"""Runner-generated OpenRouter certification entry point. Do not edit."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.conformance.openrouter_live_certification import cli_main


PLAN_PATH = Path("documentation/test-runs/TEST-RUN-2026-07-17-008_plan.json")
EXPECTED_PLAN_SHA256 = "E332018422033E95C6F94BFD9CA4031822519B9079E2B34A3D633444BA650851"


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
