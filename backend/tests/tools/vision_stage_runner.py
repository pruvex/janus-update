import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class StageResult:
    name: str
    command: List[str]
    returncode: int
    stdout_tail: str


def run_stage(name: str, command: List[str], cwd: Path) -> StageResult:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    tail = "\n".join(output.strip().splitlines()[-40:])
    return StageResult(name=name, command=command, returncode=proc.returncode, stdout_tail=tail)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cost-controlled staged runner for vision hardening.")
    parser.add_argument(
        "--matrix-dir",
        default="backend/tests/vision_matrix/Echte menschen",
        help="Matrix directory for evaluator runs.",
    )
    parser.add_argument(
        "--smoke-range",
        default="1-5",
        help="Small smoke range for stage 2 (e.g. 1-5, 1-10).",
    )
    parser.add_argument(
        "--full-range",
        default="1-20",
        help="Full range for stage 3 (e.g. 1-20).",
    )
    parser.add_argument(
        "--providers",
        default="gemini",
        help="Provider list passed to evaluator (default: gemini for token/cost efficiency).",
    )
    parser.add_argument(
        "--skip-full",
        action="store_true",
        help="Skip stage 3 full run even if stage 1/2 pass.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]

    stages = [
        (
            "stage1_py_compile",
            [sys.executable, "-m", "py_compile", "backend/services/vision/utils.py"],
        ),
        (
            "stage2_matrix_smoke",
            [
                sys.executable,
                "backend/tests/tools/vision_evaluator.py",
                "--matrix-dir",
                args.matrix_dir,
                "--range",
                args.smoke_range,
                "--e2e",
                "--providers",
                args.providers,
            ],
        ),
    ]

    if not args.skip_full:
        stages.append(
            (
                "stage3_matrix_full",
                [
                    sys.executable,
                    "backend/tests/tools/vision_evaluator.py",
                    "--matrix-dir",
                    args.matrix_dir,
                    "--range",
                    args.full_range,
                    "--e2e",
                    "--providers",
                    args.providers,
                ],
            )
        )

    results: List[StageResult] = []
    for stage_name, command in stages:
        result = run_stage(stage_name, command, cwd=repo_root)
        results.append(result)
        if result.returncode != 0:
            print(f"[FAIL] {stage_name}")
            print(result.stdout_tail)
            summary = {
                "success": False,
                "failed_stage": stage_name,
                "results": [
                    {
                        "name": r.name,
                        "returncode": r.returncode,
                        "command": r.command,
                    }
                    for r in results
                ],
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 1
        print(f"[OK] {stage_name}")

    summary = {
        "success": True,
        "results": [
            {
                "name": r.name,
                "returncode": r.returncode,
                "command": r.command,
            }
            for r in results
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
