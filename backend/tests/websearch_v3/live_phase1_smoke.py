from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import socket
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.websearch_v3 import execute_single_verified_news  # noqa: E402


PROMPTS = [
    "was gibt es neues zu Microsoft?",
    "was gibt es neues zu OpenAI?",
    "was gibt es neues zu Apple?",
    "aktuelle Nachrichten zu Nvidia?",
]


def _load_dotenv_value(name: str) -> tuple[str | None, str]:
    for env_path in (ROOT / ".env", ROOT / ".env.local", ROOT / "backend" / ".env", ROOT / "backend" / ".env.local"):
        if not env_path.exists():
            continue
        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = env_path.read_text(encoding="utf-8-sig").splitlines()
        for line in lines:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            if key.strip() != name:
                continue
            return value.strip().strip('"').strip("'") or None, str(env_path)
    return None, ""


def _load_keyring_value(provider: str) -> tuple[str | None, str]:
    try:
        import keyring
    except Exception:
        return None, ""
    try:
        return keyring.get_password("Janus-Projekt", provider) or None, "Windows keyring: Janus-Projekt/" + provider
    except Exception:
        return None, ""


def _root_cause(exc: BaseException) -> str:
    current: BaseException = exc
    seen: set[int] = set()
    while True:
        next_exc = current.__cause__ or current.__context__
        if not next_exc or id(next_exc) in seen:
            break
        seen.add(id(current))
        current = next_exc
    return f"{type(current).__name__}: {current}"


def _resolve_api_key(provider: str, explicit: str | None) -> tuple[str | None, str]:
    if explicit:
        return explicit, "--api-key"
    keyring_key, keyring_source = _load_keyring_value(provider)
    if keyring_key:
        return keyring_key, keyring_source
    if provider == "openai":
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            return env_key, "process env: OPENAI_API_KEY"
        dotenv_key, dotenv_source = _load_dotenv_value("OPENAI_API_KEY")
        if dotenv_key:
            return dotenv_key, dotenv_source + ":OPENAI_API_KEY"
    if provider == "gemini":
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            env_key = os.getenv(name)
            if env_key:
                return env_key, "process env: " + name
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            dotenv_key, dotenv_source = _load_dotenv_value(name)
            if dotenv_key:
                return dotenv_key, dotenv_source + ":" + name
    return None, ""


def _dns_preflight(provider: str) -> tuple[bool, str]:
    host = "api.openai.com" if provider == "openai" else "generativelanguage.googleapis.com"
    try:
        infos = socket.getaddrinfo(host, 443)
    except Exception as exc:
        return False, f"{host}: {type(exc).__name__}: {exc}"
    address = infos[0][4][0] if infos else "resolved"
    return True, f"{host}: {address}"


def _source_summary(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "url": source.get("url", ""),
        "title": source.get("title", ""),
        "source_label": source.get("source_label", ""),
        "verified": source.get("verified", False),
        "topic_match_score": source.get("topic_match_score", None),
        "source_quality_score": source.get("source_quality_score", None),
        "topic_label": source.get("topic_label", ""),
    }


async def _run_one(prompt: str, *, provider: str, model: str | None, api_key: str) -> dict[str, Any]:
    result = await execute_single_verified_news(
        query=prompt,
        api_key=api_key,
        provider=provider,
        model=model,
    )
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    sources = result.get("sources") if isinstance(result.get("sources"), list) else []
    return {
        "prompt": prompt,
        "status": metadata.get("status", ""),
        "reason": metadata.get("reason", ""),
        "provider": metadata.get("provider", provider),
        "search_debug": metadata.get("search_debug", {}),
        "quality_debug": metadata.get("quality_debug", {}),
        "text": result.get("text", ""),
        "sources": [_source_summary(source) for source in sources if isinstance(source, dict)],
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description="Live smoke test for websearch_v3 Phase 1 single verified news.")
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini"],
        default=os.getenv("JANUS_WEBSEARCH_V3_PROVIDER"),
        required=not bool(os.getenv("JANUS_WEBSEARCH_V3_PROVIDER")),
        help="Native provider to test. Only openai and gemini are supported for v3 Phase 1.",
    )
    parser.add_argument("--model", default=os.getenv("JANUS_WEBSEARCH_V3_MODEL") or None)
    parser.add_argument(
        "--api-key",
        default=os.getenv("JANUS_WEBSEARCH_V3_API_KEY") or None,
        help="Optional. Falls leer, nutzt das Harness OPENAI_API_KEY oder GEMINI_API_KEY passend zum Provider.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--verbose", action="store_true", help="Show provider tracebacks/logs.")
    parser.add_argument("--timeout", type=int, default=35, help="Timeout per prompt in seconds.")
    parser.add_argument(
        "--prompt",
        default="",
        help="Optional single prompt to run instead of the default four-prompt smoke set.",
    )
    args = parser.parse_args()

    provider_key = str(args.provider or "").strip().lower()
    if provider_key == "gemini" and not args.model:
        args.model = "gemini-3-flash-preview"
    if not args.verbose:
        logging.getLogger("janus_backend").setLevel(logging.CRITICAL)
    api_key, key_source = _resolve_api_key(provider_key, args.api_key)
    if not api_key:
        env_name = "OPENAI_API_KEY" if provider_key == "openai" else "GEMINI_API_KEY"
        parser.error(
            f"Kein API-Key gefunden. Setze ${env_name} oder uebergib --api-key sk-... "
            f"(Provider: {provider_key})."
        )
    dns_ok, dns_status = _dns_preflight(provider_key)
    if not dns_ok:
        parser.error(f"DNS/Netzwerk-Preflight fehlgeschlagen: {dns_status}")
    if not args.json:
        print(f"websearch_v3 Phase 1 live smoke | provider={args.provider} model={args.model or '-'}", flush=True)
        print(f"key source: {key_source}", flush=True)
        print(f"dns: {dns_status}", flush=True)
        print("=" * 88, flush=True)

    prompts = [args.prompt] if str(args.prompt or "").strip() else PROMPTS

    rows = []
    for prompt in prompts:
        if not args.json:
            print(f"Running: {prompt}", flush=True)
        try:
            rows.append(
                await asyncio.wait_for(
                    _run_one(prompt, provider=provider_key, model=args.model, api_key=api_key),
                    timeout=max(5, args.timeout),
                )
            )
        except TimeoutError:
            rows.append(
                {
                    "prompt": prompt,
                    "status": "error",
                    "reason": f"Timeout after {max(5, args.timeout)}s",
                    "provider": provider_key,
                    "search_debug": {},
                    "quality_debug": {},
                    "text": "",
                    "sources": [],
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "prompt": prompt,
                    "status": "error",
                    "reason": _root_cause(exc),
                    "provider": provider_key,
                    "search_debug": {},
                    "quality_debug": {},
                    "text": "",
                    "sources": [],
                }
            )

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"\nPROMPT: {row['prompt']}")
            print(f"STATUS: {row['status'] or '-'} | REASON: {row['reason'] or '-'}")
            if row.get("search_debug"):
                print(f"DEBUG: {json.dumps(row['search_debug'], ensure_ascii=False)}")
            if row.get("quality_debug"):
                print(f"QUALITY: {json.dumps(row['quality_debug'], ensure_ascii=False)}")
            if row["sources"]:
                for source in row["sources"]:
                    print(
                        "SOURCE: "
                        f"{source['source_label'] or '-'} | "
                        f"label={source.get('topic_label') or '-'} | "
                        f"quality={source['source_quality_score']} | "
                        f"topic={source['topic_match_score']} | "
                        f"{source['url']}"
                    )
            else:
                print("SOURCE: none")
            print("TEXT:")
            print(str(row["text"] or "").strip())
        print("\nDone.")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
