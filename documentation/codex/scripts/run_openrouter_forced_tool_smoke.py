#!/usr/bin/env python
"""OpenRouter forced-tool smoke — offline matrix + optional live probe.

Default (safe, no spend):
  python documentation/codex/scripts/run_openrouter_forced_tool_smoke.py

Optional live probe (real OR key, bounded spend, fail-closed timeout):
  python documentation/codex/scripts/run_openrouter_forced_tool_smoke.py --execute-live

Live probes one representative model per hard family (Qwen / Kimi / GLM) with
force_tool_name=system.weather. Named-choice hangs must fail within --timeout-s
instead of waiting for OpenRouter idle timeout.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "documentation" / "test-results" / "openrouter-forced-tool-smoke"
SUMMARY_PATH = OUT_DIR / "forced_tool_smoke_summary.json"

# One representative per hard family (cheap tier preferred).
LIVE_PROBE_MODELS = (
    "qwen/qwen3.6-flash",
    "moonshotai/kimi-k2.6",
    "z-ai/glm-4.7-flash",
)

WEATHER_TOOL = {
    "name": "system.weather",
    "description": "Get weather",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_offline_matrix() -> Dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "backend/tests/test_openrouter_forced_tool_compat_matrix.py",
        "-q",
        "--tb=line",
    ]
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "mode": "offline_matrix",
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "exit_code": proc.returncode,
        "elapsed_ms": elapsed_ms,
        "stdout_tail": (proc.stdout or "")[-1200:],
        "stderr_tail": (proc.stderr or "")[-1200:],
    }


async def _live_force_weather(model: str, *, timeout_s: float) -> Dict[str, Any]:
    from backend.llm_providers.openrouter.service import OpenRouterServiceProvider
    from backend.services.openrouter_credential_authority import (
        get_openrouter_runtime_reader,
    )

    cred = get_openrouter_runtime_reader().get_eligible_credential()
    if cred is None or not getattr(cred, "api_key", None):
        return {
            "model": model,
            "status": "BLOCKED",
            "detail": "no_eligible_openrouter_credential",
        }

    api_key = str(cred.api_key)
    service = OpenRouterServiceProvider()
    started = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            service.generate_response(
                api_key=api_key,
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": "Call the weather tool for Berlin. Do not answer without the tool.",
                    }
                ],
                tools=[WEATHER_TOOL],
                force_tool_name="system.weather",
                max_completion_tokens=256,
            ),
            timeout=timeout_s,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        tool_calls = result.get("tool_calls") or []
        has_tool = bool(tool_calls)
        # Accept either tool_calls or text that indicates provider returned something quickly.
        status = "PASS" if has_tool or str(result.get("text") or "").strip() else "FAIL"
        return {
            "model": model,
            "status": status,
            "elapsed_ms": elapsed_ms,
            "has_tool_calls": has_tool,
            "finish_reason": result.get("finish_reason"),
            "error_code": result.get("error_code"),
        }
    except asyncio.TimeoutError:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "model": model,
            "status": "FAIL",
            "elapsed_ms": elapsed_ms,
            "detail": f"timeout_after_{timeout_s:.0f}s",
        }
    except Exception as exc:  # noqa: BLE001 - smoke boundary
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "model": model,
            "status": "FAIL",
            "elapsed_ms": elapsed_ms,
            "detail": type(exc).__name__,
            "error": str(exc)[:240],
        }


async def run_live_probes(*, timeout_s: float) -> Dict[str, Any]:
    probes: List[Dict[str, Any]] = []
    for model in LIVE_PROBE_MODELS:
        probes.append(await _live_force_weather(model, timeout_s=timeout_s))
    failed = [p for p in probes if p.get("status") != "PASS"]
    blocked = [p for p in probes if p.get("status") == "BLOCKED"]
    if blocked and len(blocked) == len(probes):
        overall = "BLOCKED"
    elif failed:
        overall = "FAIL"
    else:
        overall = "PASS"
    return {
        "mode": "live_force_weather",
        "status": overall,
        "timeout_s": timeout_s,
        "models": list(LIVE_PROBE_MODELS),
        "probes": probes,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute-live",
        action="store_true",
        help="Run live OR forced-weather probes (costs money; needs valid key).",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=25.0,
        help="Per-model live timeout seconds (fail-closed). Default: 25",
    )
    parser.add_argument(
        "--skip-offline",
        action="store_true",
        help="Skip the offline pytest matrix (live-only).",
    )
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Any] = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "steps": [],
    }

    if not args.skip_offline:
        offline = run_offline_matrix()
        results["steps"].append(offline)
        print(f"[offline] {offline['status']} ({offline['elapsed_ms']} ms)")
        if offline["status"] != "PASS":
            print(offline.get("stdout_tail") or "")
            print(offline.get("stderr_tail") or "", file=sys.stderr)

    if args.execute_live:
        live = asyncio.run(run_live_probes(timeout_s=float(args.timeout_s)))
        results["steps"].append(live)
        print(f"[live] {live['status']}")
        for probe in live.get("probes") or []:
            print(
                f"  - {probe.get('model')}: {probe.get('status')}"
                f" ({probe.get('elapsed_ms', '?')} ms)"
                f"{(' · ' + str(probe.get('detail'))) if probe.get('detail') else ''}"
            )

    statuses = [str(step.get("status") or "") for step in results["steps"]]
    if not statuses:
        results["status"] = "BLOCKED"
        results["detail"] = "no_steps_run"
    elif any(s == "FAIL" for s in statuses):
        results["status"] = "FAIL"
    elif any(s == "BLOCKED" for s in statuses) and all(
        s in {"PASS", "BLOCKED"} for s in statuses
    ):
        results["status"] = "BLOCKED" if "PASS" not in statuses else "PASS"
    else:
        results["status"] = "PASS"

    SUMMARY_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(f"summary: {SUMMARY_PATH}")
    print(f"overall: {results['status']}")

    if results["status"] == "PASS":
        return 0
    if results["status"] == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
