from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROBE = ROOT / "backend" / "tests" / "websearch_v3" / "live_gemini_sdk_grounding_probe.py"

MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
]

VARIANTS = [
    ["--dict-config"],
    [],
]


def _run_probe(model: str, variant: list[str]) -> tuple[int, str]:
    cmd = [
        sys.executable,
        str(PROBE),
        "--model",
        model,
        "--prompt",
        "was gibt es neues zu Microsoft?",
        "--max-output-tokens",
        "1024",
        "--dump-raw-keys",
        *variant,
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45,
    )
    return completed.returncode, completed.stdout


def _extract_json(output: str) -> dict:
    start = output.find("{")
    if start < 0:
        return {}
    try:
        return json.loads(output[start:])
    except json.JSONDecodeError:
        return {}


def main() -> int:
    print("Gemini-only grounding matrix. No cross-provider fallback.")
    print("=" * 72)
    any_grounded = False
    for model in MODELS:
        for variant in VARIANTS:
            label = "dict-config" if variant else "typed-config"
            print(f"\nMODEL={model} VARIANT={label}")
            try:
                code, output = _run_probe(model, variant)
            except subprocess.TimeoutExpired:
                print("STATUS=timeout")
                continue
            data = _extract_json(output)
            chunks = int(data.get("grounding_chunks_count") or 0)
            supports = int(data.get("grounding_supports_count") or 0)
            queries = data.get("web_search_queries") or []
            finish = data.get("finish_reason") or ""
            keys = data.get("metadata_keys") or []
            print(f"STATUS={'ok' if code == 0 else 'error'} finish={finish}")
            print(f"grounding_chunks={chunks} grounding_supports={supports} queries={queries}")
            print(f"metadata_keys={keys}")
            if chunks > 0:
                any_grounded = True
                print("GROUNDING=YES")
            else:
                print("GROUNDING=NO")
    print("\nRESULT:", "at least one Gemini path grounded" if any_grounded else "no Gemini grounding path found")
    return 0 if any_grounded else 2


if __name__ == "__main__":
    raise SystemExit(main())
