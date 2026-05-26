from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.tests.websearch_v3.live_phase1_smoke import _resolve_api_key  # noqa: E402
from backend.tests.websearch_v3.golden_prompts import prompts_for_set  # noqa: E402
from backend.services.websearch_v3 import execute_single_verified_news  # noqa: E402


DEFAULT_PROMPTS = (
    *prompts_for_set("smoke"),
)

DEFAULT_MODELS = {
    "openai": "gpt-5.4-nano",
    "gemini": "gemini-3-flash-preview",
}

BAD_URL_MARKERS = (
    "google.com/search",
    "bing.com/search",
    "duckduckgo.com",
    "vertexaisearch.cloud.google.com",
    "reddit.com",
    "youtube.com",
    "youtu.be",
    "/filme-vorschau",
    "/filme/jahre/",
    "/film/filmstarts.html",
    "/filme/aktuell/",
    "/filme-imkino/vorpremiere",
    "/filme-imkino/kinos",
    "/filmstarts/all/",
    "/filmstarts/",
    "/aktuell/festivalberichte",
    "/news/cinema/month/",
    "/kinofilme/kinofilme-",
    "/filme/kinofilme-",
    "/de-de/recent-news",
    "/recent-news",
    "/news/latest",
    "/alle-anzeigen",
    "/whats-new",
    "/category/press-releases",
    "/filmstarts/aktuell-im-kino",
    "/community/",
    "/forum/",
    "/thread/",
)

NAVIGATION_MARKERS = (
    "zum inhalt springen",
    "navigation",
    "newsletter",
    "registriere dich",
    "jetzt kostenlos registrieren",
    "alle anzeigen",
    "shop menu",
    "toplisten",
    "alle filme",
    "kinoprogramm",
    "kleiner-kalender",
    "plus shop",
    "login | registrieren",
)

GENERIC_SUMMARY_MARKERS = (
    "details stehen in der verifizierten quelle",
    "die quelle meldet:",
)

DOMAIN_FALSE_POSITIVES = {
    "gaming": ("badminton", "keto", "ticket", "tickets", "sport"),
    "film": ("aktie", "boerse", "börse"),
}

LOW_VALUE_HOSTS = (
    "deraktionaer.de",
    "finanztreff.de",
    "infinigate.com",
    "phemex.com",
)

GENERIC_HOST_PATH_MARKERS = (
    "computerbase.de/news/openai",
    "pcwelt.de/article/1154148/grafikkartentreiber-nvidia-geforce-treiber",
)


def _domain_for_prompt(prompt: str) -> str:
    lowered = prompt.casefold()
    if any(marker in lowered for marker in ("gaming", "games", "spiele")):
        return "gaming"
    if any(marker in lowered for marker in ("kino", "film")):
        return "film"
    return "company"


def _host(url: str) -> str:
    match = re.match(r"https?://([^/]+)", str(url or "").casefold())
    return match.group(1).removeprefix("www.") if match else ""


def _source_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = result.get("sources") if isinstance(result.get("sources"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _quality_debug(result: dict[str, Any]) -> dict[str, Any]:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    value = metadata.get("quality_debug")
    return value if isinstance(value, dict) else {}


def _metadata(result: dict[str, Any]) -> dict[str, Any]:
    value = result.get("metadata")
    return value if isinstance(value, dict) else {}


def _status_reason(result: dict[str, Any]) -> tuple[str, str]:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    return str(metadata.get("status") or ""), str(metadata.get("reason") or "")


def evaluate_result(prompt: str, provider: str, result: dict[str, Any], elapsed_ms: int) -> dict[str, Any]:
    status, reason = _status_reason(result)
    text = str(result.get("text") or "")
    sources = _source_rows(result)
    domain = _domain_for_prompt(prompt)
    warnings: list[str] = []
    score = 100

    if status != "ok":
        score -= 55
        warnings.append(f"status_not_ok:{status or 'missing'}:{reason or '-'}")

    if not sources:
        score -= 30
        warnings.append("no_sources")
    elif len(sources) == 1 and domain in {"gaming", "film"}:
        score -= 8
        warnings.append("broad_query_only_one_source")

    seen_hosts: set[str] = set()
    for source in sources:
        url = str(source.get("url") or "")
        title = str(source.get("title") or "")
        label = str(source.get("source_label") or _host(url))
        lowered_url = url.casefold()
        lowered_title = title.casefold()
        lowered_label = label.casefold()
        if any(marker in lowered_url for marker in BAD_URL_MARKERS):
            score -= 20
            warnings.append(f"bad_url:{url}")
        if any(marker in lowered_url for marker in GENERIC_HOST_PATH_MARKERS):
            score -= 18
            warnings.append(f"generic_topic_or_driver_page:{label or url}")
        if any(marker in lowered_label for marker in LOW_VALUE_HOSTS):
            score -= 18
            warnings.append(f"low_value_host:{label}")
        if "region/" in lowered_url and "microsoft" in lowered_label:
            score -= 18
            warnings.append(f"official_listing:{label}")
        if lowered_label in seen_hosts:
            score -= 8
            warnings.append(f"duplicate_host:{label}")
        seen_hosts.add(lowered_label)
        if domain in DOMAIN_FALSE_POSITIVES and any(
            marker in f"{lowered_url} {lowered_title} {lowered_label}" for marker in DOMAIN_FALSE_POSITIVES[domain]
        ):
            score -= 18
            warnings.append(f"domain_false_positive:{label or url}")
        quality = source.get("source_quality_score")
        topic = source.get("topic_match_score")
        if isinstance(quality, (int, float)) and quality < 0.8:
            score -= 8
            warnings.append(f"low_quality_score:{label}:{quality}")
        if isinstance(topic, (int, float)) and topic < 0.7:
            score -= 8
            warnings.append(f"low_topic_score:{label}:{topic}")

    lowered_text = text.casefold()
    if any(marker in lowered_text for marker in NAVIGATION_MARKERS):
        score -= 14
        warnings.append("navigation_noise_in_text")
    if any(marker in lowered_text for marker in GENERIC_SUMMARY_MARKERS):
        score -= 6
        warnings.append("generic_summary_fallback")
    if "[link](" not in lowered_text and sources:
        score -= 20
        warnings.append("missing_markdown_link")
    if elapsed_ms > 25000:
        score -= 10
        warnings.append(f"slow:{elapsed_ms}ms")
    elif elapsed_ms > 15000:
        score -= 5
        warnings.append(f"borderline_latency:{elapsed_ms}ms")

    rejected = _quality_debug(result).get("rejected_sources")
    rejected_count = len(rejected) if isinstance(rejected, list) else 0
    reject_reasons: dict[str, int] = {}
    if isinstance(rejected, list):
        for item in rejected:
            if not isinstance(item, dict):
                continue
            for reason in item.get("reasons") or []:
                reason_key = str(reason or "").strip()
                if reason_key:
                    reject_reasons[reason_key] = reject_reasons.get(reason_key, 0) + 1
    source_types: dict[str, int] = {}
    for source in sources:
        source_type = str(source.get("source_type") or "unknown")
        source_types[source_type] = source_types.get(source_type, 0) + 1
    metadata = _metadata(result)
    score = max(0, min(100, score))
    return {
        "provider": provider,
        "prompt": prompt,
        "score": score,
        "grade": "green" if score >= 85 else "yellow" if score >= 70 else "red",
        "status": status,
        "reason": reason,
        "elapsed_ms": elapsed_ms,
        "source_count": len(sources),
        "rejected_count": rejected_count,
        "reject_reasons": reject_reasons,
        "source_types": source_types,
        "mode": metadata.get("verified_source_mode") or "",
        "search_budget": metadata.get("search_budget"),
        "warnings": warnings,
        "sources": [
            {
                "label": source.get("source_label") or _host(str(source.get("url") or "")),
                "title": source.get("title") or "",
                "url": source.get("url") or "",
                "quality": source.get("source_quality_score"),
                "topic": source.get("topic_match_score"),
                "source_type": source.get("source_type") or "",
                "evidence": source.get("evidence_score"),
                "topic_label": source.get("topic_label") or "",
            }
            for source in sources
        ],
        "text_preview": " ".join(text.split())[:420],
    }


async def _run_case(prompt: str, provider: str, model: str, api_key: str, timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            execute_single_verified_news(query=prompt, api_key=api_key, provider=provider, model=model),
            timeout=max(5, timeout),
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return evaluate_result(prompt, provider, result, elapsed_ms)
    except TimeoutError:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "provider": provider,
            "prompt": prompt,
            "score": 0,
            "grade": "red",
            "status": "error",
            "reason": f"Timeout after {timeout}s",
            "elapsed_ms": elapsed_ms,
            "source_count": 0,
            "rejected_count": 0,
            "warnings": ["timeout"],
            "sources": [],
            "text_preview": "",
        }
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "provider": provider,
            "prompt": prompt,
            "score": 0,
            "grade": "red",
            "status": "error",
            "reason": f"{type(exc).__name__}: {exc}",
            "elapsed_ms": elapsed_ms,
            "source_count": 0,
            "rejected_count": 0,
            "warnings": ["exception"],
            "sources": [],
            "text_preview": "",
        }


def _print_report(rows: list[dict[str, Any]]) -> None:
    print("websearch_v3 live quality evaluation")
    print("=" * 96)
    if rows:
        avg = sum(row["score"] for row in rows) / len(rows)
        print(f"overall_score: {avg:.1f}/100")
    for row in rows:
        print(
            f"\n[{row['grade'].upper()} {row['score']:>3}/100] "
            f"{row['provider']} | {row['prompt']} | {row['elapsed_ms']}ms | "
            f"sources={row['source_count']} rejected={row['rejected_count']} "
            f"mode={row.get('mode') or '-'} budget={row.get('search_budget') or '-'}"
        )
        if row["warnings"]:
            print("warnings: " + ", ".join(row["warnings"]))
        if row.get("reject_reasons"):
            top_reasons = sorted(row["reject_reasons"].items(), key=lambda item: (-item[1], item[0]))[:6]
            print("rejects: " + ", ".join(f"{reason}={count}" for reason, count in top_reasons))
        for idx, source in enumerate(row["sources"], start=1):
            print(
                f"  {idx}. {source['label']} | q={source['quality']} t={source['topic']} "
                f"type={source.get('source_type') or '-'} ev={source.get('evidence')} | {source['title']}"
            )
            print(f"     {source['url']}")
        if row["text_preview"]:
            print(f"text: {row['text_preview']}")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run live websearch_v3 prompts and score result quality.")
    parser.add_argument("--providers", default="openai,gemini", help="Comma-separated providers: openai,gemini")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print planned runs without calling providers.")
    parser.add_argument("--prompt-set", default="smoke", help="Golden set: smoke, company, entertainment, sport, finance_explicit, all")
    parser.add_argument("--max-cases", type=int, default=0, help="Limit total provider/prompt calls; 0 means no limit.")
    parser.add_argument("--prompt", action="append", default=[], help="Prompt to run. Can be repeated.")
    parser.add_argument("--openai-model", default=DEFAULT_MODELS["openai"])
    parser.add_argument("--gemini-model", default=DEFAULT_MODELS["gemini"])
    args = parser.parse_args()

    prompts = tuple(args.prompt) if args.prompt else prompts_for_set(args.prompt_set)
    providers = tuple(provider.strip().lower() for provider in args.providers.split(",") if provider.strip())
    planned = [(provider, prompt) for provider in providers for prompt in prompts]
    if args.max_cases > 0:
        planned = planned[: args.max_cases]
    if args.dry_run:
        print("websearch_v3 live quality evaluation dry-run")
        print(f"providers: {', '.join(providers)}")
        print(f"prompt_set: {args.prompt_set}")
        print(f"planned_calls: {len(planned)}")
        for provider, prompt in planned:
            print(f"- {provider}: {prompt}")
        return 0
    keys: dict[str, str] = {}
    models = {"openai": args.openai_model, "gemini": args.gemini_model}
    for provider in providers:
        api_key, source = _resolve_api_key(provider, None)
        if not api_key:
            raise RuntimeError(f"No API key found for provider={provider}")
        keys[provider] = api_key
        if not args.json:
            print(f"provider={provider} model={models[provider]} key_source={source}")

    rows: list[dict[str, Any]] = []
    for provider, prompt in planned:
        if not args.json:
            print(f"running {provider}: {prompt}", flush=True)
        rows.append(await _run_case(prompt, provider, models[provider], keys[provider], args.timeout))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        _print_report(rows)
    return 0 if all(row["score"] >= 70 for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
