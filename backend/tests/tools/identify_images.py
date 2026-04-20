#!/usr/bin/env python3
"""Temporary mapping helper for Supercluster images 41-60.

Runs cloud-object pass only (no orchestrator, no DB writes) and prints detected tags.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.vision_helper import analyze_image_with_cloud  # noqa: E402


def _to_base64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("ascii")


async def main() -> int:
    matrix_dir = PROJECT_ROOT / "backend" / "tests" / "vision_matrix" / "Supercluster"
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    provider = "openai" if openai_key else "gemini"
    api_key = openai_key if openai_key else gemini_key

    if not api_key:
        print("ERROR: Kein OPENAI_API_KEY oder GEMINI_API_KEY in .env gefunden.")
        return 1

    print(f"Cloud mapping provider: {provider}")
    print("=" * 120)

    for idx in range(41, 61):
        image_path = matrix_dir / f"Supercluster-{idx}.jpg"
        if not image_path.exists():
            print(f"{idx:02d} | MISSING FILE | {image_path.name}")
            continue

        image_b64 = _to_base64(image_path)
        cloud_result = await analyze_image_with_cloud(image_b64, provider, api_key)
        objects = cloud_result.get("objects", []) if isinstance(cloud_result, dict) else []

        tags = []
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            name = str(obj.get("name", "")).strip()
            color = str(obj.get("color", "")).strip()
            material = str(obj.get("material", "")).strip()
            details = str(obj.get("details", "")).strip()

            parts = [p for p in [name, color, material, details] if p]
            if parts:
                tags.append(" | ".join(parts))

        print(f"{idx:02d} | {image_path.name}")
        if tags:
            for tag in tags:
                print(f"    - {tag}")
        else:
            print("    - <no objects>")

    print("=" * 120)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
