#!/usr/bin/env python3
"""Real-image evaluation harness (cost-aware).

Runs the existing E2E evaluator image-by-image on a sampled subset and provides
an explicit cost estimate before execution.
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATOR_PATH = PROJECT_ROOT / "backend" / "tests" / "tools" / "vision_evaluator.py"


@dataclass
class RunSummary:
    total_images: int = 0
    strict_green_images: int = 0
    failed_images: int = 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cost-aware real image evaluator harness")
    parser.add_argument("--matrix-dir", type=str, required=True, help="Folder with images + GT JSON")
    parser.add_argument("--sample-size", type=int, default=0, help="0 = all images, otherwise random sample size")
    parser.add_argument("--seed", type=int, default=42, help="Sampling seed")
    parser.add_argument("--providers", type=str, default="gemini", help="Comma-separated providers: gemini, openai, or both")
    parser.add_argument("--estimate-only", action="store_true", help="Only print cost estimate and selected images")
    parser.add_argument("--cost-gemini-per-run-eur", type=float, default=0.0026)
    parser.add_argument("--cost-openai-per-run-eur", type=float, default=0.0045)
    parser.add_argument("--kpi-gate", action="store_true")
    parser.add_argument("--max-contradiction-rate", type=float, default=0.0)
    parser.add_argument("--min-source-map-coverage", type=float, default=0.95)
    parser.add_argument("--min-slot-source-coverage", type=float, default=0.80)
    return parser.parse_args()


def _collect_images(matrix_dir: Path) -> List[Path]:
    images = sorted(list(matrix_dir.glob("*.jpg")) + list(matrix_dir.glob("*.jpeg")))
    return [img for img in images if (img.with_suffix(f"{img.suffix}.json").exists() or img.with_suffix(".jpg.json").exists())]


def _select_sample(images: List[Path], sample_size: int, seed: int) -> List[Path]:
    if sample_size <= 0 or sample_size >= len(images):
        return images
    rng = random.Random(seed)
    return sorted(rng.sample(images, sample_size), key=lambda p: p.name.lower())


def _estimate_cost(images_count: int, providers: List[str], gemini_cost: float, openai_cost: float) -> float:
    total = 0.0
    for provider in providers:
        if provider == "gemini":
            total += images_count * gemini_cost
        elif provider == "openai":
            total += images_count * openai_cost
    return total


def _run_single_image(args: argparse.Namespace, image_name: str, providers_csv: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(EVALUATOR_PATH),
        "--e2e",
        "--matrix-dir",
        str(Path(args.matrix_dir).resolve()),
        "--image",
        image_name,
        "--providers",
        providers_csv,
    ]
    if args.kpi_gate:
        cmd.extend(
            [
                "--kpi-gate",
                "--max-contradiction-rate",
                str(args.max_contradiction_rate),
                "--min-source-map-coverage",
                str(args.min_source_map_coverage),
                "--min-slot-source-coverage",
                str(args.min_slot_source_coverage),
            ]
        )

    return subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)


def main() -> int:
    args = _parse_args()
    matrix_dir = Path(args.matrix_dir).resolve()
    if not matrix_dir.exists():
        print(f"ERROR: matrix dir not found: {matrix_dir}")
        return 2

    providers = [p.strip().lower() for p in str(args.providers or "").split(",") if p.strip()]
    providers = [p for p in providers if p in {"gemini", "openai"}]
    if not providers:
        print("ERROR: no valid providers selected. Use --providers gemini or --providers openai,gemini")
        return 2

    images = _collect_images(matrix_dir)
    if not images:
        print(f"ERROR: no evaluable images found in {matrix_dir}")
        return 2

    selected = _select_sample(images, args.sample_size, args.seed)
    est = _estimate_cost(
        images_count=len(selected),
        providers=providers,
        gemini_cost=float(args.cost_gemini_per_run_eur),
        openai_cost=float(args.cost_openai_per_run_eur),
    )

    print("=== REAL IMAGE EVAL PLAN ===")
    print(f"matrix_dir: {matrix_dir}")
    print(f"providers: {','.join(providers)}")
    print(f"images_total: {len(images)}")
    print(f"images_selected: {len(selected)}")
    print(f"estimated_cost_eur: {est:.2f}")

    if args.estimate_only:
        print("estimate_only=true -> no evaluator runs executed")
        return 0

    summary = RunSummary(total_images=len(selected))
    providers_csv = ",".join(providers)

    for image in selected:
        result = _run_single_image(args, image.name, providers_csv)
        out = result.stdout or ""
        strict_ok = "STRICT-V3 SUMMARY: 2/2" in out or "STRICT-V3 SUMMARY: 1/1" in out
        status = "PASS" if result.returncode == 0 and strict_ok else "FAIL"

        if status == "PASS":
            summary.strict_green_images += 1
        else:
            summary.failed_images += 1

        print(f"[{status}] {image.name} (exit={result.returncode})")

    print("=== REAL IMAGE EVAL SUMMARY ===")
    print(f"images_selected: {summary.total_images}")
    print(f"strict_green_images: {summary.strict_green_images}")
    print(f"failed_images: {summary.failed_images}")
    if summary.total_images:
        print(f"strict_green_rate: {summary.strict_green_images / summary.total_images:.3f}")

    return 0 if summary.failed_images == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
