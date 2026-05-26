from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Mapping

from backend.services.websearch.websearch import execute_websearch_service

from .fact_extractor import extract_supported_fact
from .gemini_native import search_gemini_grounded_phase1
from .models import PageFetchResult, SearchCandidate, SingleVerifiedNewsResult
from .page_fetcher import fetch_candidate_page
from .providers import candidates_from_websearch_result, normalize_gemini_grounding_response
from .query_planner import (
    build_briefing_search_queries,
    build_company_search_queries,
    build_single_news_search_query,
    is_broad_briefing_query,
    is_simple_news_query,
    query_domain,
)
from .renderer_adapter import render_single_verified_news
from .source_verifier import is_verified, sort_verified_sources, verify_source
from .topic_labeler import label_source_topic, with_topic_label
from .url_normalizer import is_blocked_url

logger = logging.getLogger("janus_backend")

SearchFn = Callable[[str], Awaitable[Mapping[str, Any]]]
FetchFn = Callable[[SearchCandidate], Awaitable[PageFetchResult]]
SUPPORTED_NATIVE_PROVIDERS = {"openai", "gemini"}


@dataclass(frozen=True)
class SourcePolicy:
    target_sources: int
    search_budget: int
    mode: str


class WebSearchV3Pipeline:
    def __init__(self, search_fn: SearchFn, fetch_fn: FetchFn = fetch_candidate_page, max_candidates: int = 6) -> None:
        self.search_fn = search_fn
        self.fetch_fn = fetch_fn
        self.max_candidates = max_candidates
        self.last_search_metadata: dict[str, Any] = {}

    async def single_verified_news(self, query: str) -> SingleVerifiedNewsResult:
        return await self.verified_news(query, max_sources=1)

    async def verified_news(self, query: str, *, max_sources: int = 1) -> SingleVerifiedNewsResult:
        policy = source_policy_for_query(query, max_sources)
        if policy.mode == "briefing":
            return await self.briefing_news(query, max_sources=policy.target_sources, search_budget=policy.search_budget)

        if not is_simple_news_query(query):
            return SingleVerifiedNewsResult(query=query, fact=None, status="skipped", reason="not_simple_news_query")

        if policy.mode == "company":
            return await self.company_news(query, max_sources=policy.target_sources, search_budget=policy.search_budget)
        return await self._verified_news_for_search_query(
            query=query,
            search_query=build_single_news_search_query(query),
            max_sources=policy.target_sources,
        )

    async def company_news(self, query: str, *, max_sources: int = 2, search_budget: int = 2) -> SingleVerifiedNewsResult:
        if not is_simple_news_query(query):
            return SingleVerifiedNewsResult(query=query, fact=None, status="skipped", reason="not_simple_news_query")

        max_sources = max(1, min(int(max_sources or 2), 2))
        primary_query = build_single_news_search_query(query)
        search_queries = _limit_search_queries(
            (primary_query, *tuple(item for item in build_company_search_queries(query) if item != primary_query)),
            budget=search_budget,
        )
        return await self._collect_from_search_queries(
            query=query,
            search_queries=search_queries,
            max_sources=max_sources,
            metadata_key="company_queries",
            primary_query=primary_query,
        )

    async def briefing_news(self, query: str, *, max_sources: int = 3, search_budget: int = 3) -> SingleVerifiedNewsResult:
        if not is_simple_news_query(query):
            return SingleVerifiedNewsResult(query=query, fact=None, status="skipped", reason="not_simple_news_query")

        max_sources = max(1, min(int(max_sources or 3), 3))
        search_queries = _limit_search_queries(build_briefing_search_queries(query), budget=search_budget)
        return await self._collect_from_search_queries(
            query=query,
            search_queries=search_queries,
            max_sources=max_sources,
            metadata_key="briefing_queries",
        )

    async def _collect_from_search_queries(
        self,
        *,
        query: str,
        search_queries: tuple[str, ...],
        max_sources: int,
        metadata_key: str,
        primary_query: str = "",
    ) -> SingleVerifiedNewsResult:
        all_facts = []
        all_rejected = []
        search_debug = []
        seen_urls: set[str] = set()
        seen_hosts: set[str] = set()
        seen_titles: set[str] = set()
        tasks = {
            asyncio.create_task(
                self._verified_news_for_search_query(
                    query=query,
                    search_query=search_query,
                    max_sources=max_sources if search_query == primary_query else 1,
                )
            ): search_query
            for search_query in search_queries
        }
        pending = set(tasks.keys())
        try:
            while pending and len(all_facts) < max_sources:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    if len(all_facts) >= max_sources:
                        break
                    search_query = tasks[task]
                    try:
                        result = task.result()
                    except Exception as exc:
                        search_debug.append({"query": search_query, "status": "error", "reason": f"{type(exc).__name__}: {exc}"})
                        continue
                    search_debug.append({"query": search_query, "status": result.status, "reason": result.reason})
                    all_rejected.extend(getattr(self, "_briefing_rejected_by_query", {}).get(search_query, []))
                    for fact in result.facts or ((result.fact,) if result.fact else tuple()):
                        if len(all_facts) >= max_sources:
                            break
                        if _append_unique_fact(
                            fact,
                            all_facts=all_facts,
                            seen_urls=seen_urls,
                            seen_hosts=seen_hosts,
                            seen_titles=seen_titles,
                        ):
                            if search_query != primary_query:
                                break
                    if len(all_facts) >= max_sources:
                        break
        finally:
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        self.last_search_metadata = {
            metadata_key: search_debug,
            "rejected_sources": all_rejected,
        }
        if not all_facts:
            return SingleVerifiedNewsResult(query=query, fact=None, status="no_source", reason="no_verified_source")
        capped_facts = tuple(all_facts[:max_sources])
        return SingleVerifiedNewsResult(query=query, fact=capped_facts[0], status="ok", facts=capped_facts)

    async def _verified_news_for_search_query(
        self,
        *,
        query: str,
        search_query: str,
        max_sources: int,
    ) -> SingleVerifiedNewsResult:
        raw = await self.search_fn(search_query)
        search_metadata = dict(raw.get("metadata") or {}) if isinstance(raw.get("metadata"), Mapping) else {}
        self.last_search_metadata = search_metadata
        candidates = [
            candidate
            for candidate in candidates_from_websearch_result(raw)
            if candidate.url and (candidate.provider == "gemini" or not is_blocked_url(candidate.url))
        ][: self.max_candidates]
        if not candidates:
            return SingleVerifiedNewsResult(query=query, fact=None, status="no_source", reason="no_candidates")

        pages = await asyncio.gather(*(self.fetch_fn(candidate) for candidate in candidates))
        verified = []
        rejected = []
        for candidate, page in zip(candidates, pages):
            source = verify_source(query, candidate, page)
            if is_verified(source):
                verified.append(source)
            else:
                rejected.append(
                    {
                        "url": source.canonical_url or candidate.url,
                        "provider": candidate.provider,
                        "rank": candidate.rank,
                        "reasons": list(source.rejection_reasons),
                        "quality": source.source_quality_score,
                        "topic": source.topic_match_score,
                        "source_type": source.source_type,
                        "evidence": source.evidence_score,
                    }
                )
                logger.debug(
                    "WEBSEARCH-V3: rejected url=%s reasons=%s score=%s topic=%s",
                    source.canonical_url,
                    ",".join(source.rejection_reasons),
                    source.source_quality_score,
                    source.topic_match_score,
                )
        self.last_search_metadata["rejected_sources"] = rejected
        rejected_by_query = getattr(self, "_briefing_rejected_by_query", None)
        if not isinstance(rejected_by_query, dict):
            rejected_by_query = {}
            setattr(self, "_briefing_rejected_by_query", rejected_by_query)
        rejected_by_query[search_query] = rejected
        if not verified:
            return SingleVerifiedNewsResult(query=query, fact=None, status="no_source", reason="no_verified_source")

        selected_sources = _select_verified_sources(sort_verified_sources(verified), max_sources, query=query)
        facts = tuple(with_topic_label(extract_supported_fact(source, query)) for source in selected_sources)
        return SingleVerifiedNewsResult(query=query, fact=facts[0] if facts else None, status="ok", facts=facts)


def _is_german_news_query(query: str) -> bool:
    lowered = str(query or "").casefold()
    return any(
        marker in lowered
        for marker in (
            "was gibt es neues",
            "aktuelle nachricht",
            "aktuelle news",
            "aktuelle meldung",
            "nachrichten",
            "neuigkeiten",
        )
    )


def source_policy_for_query(query: str, configured_max_sources: int = 1) -> SourcePolicy:
    cap = max(1, min(int(configured_max_sources or 1), 4))
    if is_broad_briefing_query(query):
        target = min(cap, 3)
        return SourcePolicy(target_sources=target, search_budget=max(1, min(4, target + 1)), mode="briefing")
    if query_domain(query) == "generic" and not _is_narrow_news_query(query):
        target = min(cap, 2)
        return SourcePolicy(target_sources=target, search_budget=max(1, min(2, target)), mode="company")
    return SourcePolicy(target_sources=1, search_budget=1, mode="single")


def _is_narrow_news_query(query: str) -> bool:
    lowered = str(query or "").casefold()
    broad_markers = (
        "was gibt es neues",
        "aktuelle nachrichten",
        "aktuelle meldungen",
        "news zu",
        "neuigkeiten zu",
    )
    if any(marker in lowered for marker in broad_markers):
        return False
    narrow_markers = (
        "quartalszahl",
        "quartalszahlen",
        "earnings",
        "financial results",
        "release date",
        "veröffentlicht",
        "veroeffentlicht",
        "angekündigt",
        "angekuendigt",
        "gestartet",
        "wann",
        "wer",
        "hat ",
        "gibt es ",
    )
    return any(marker in lowered for marker in narrow_markers)


def _select_verified_sources(sources: list[Any], max_sources: int, *, query: str = "") -> list[Any]:
    if _is_german_news_query(query):
        german_sources = [source for source in sources if str(getattr(source, "language", "") or "") == "de"]
        if german_sources:
            sources = german_sources
        else:
            max_sources = 1
    selected: list[Any] = []
    seen_urls: set[str] = set()
    seen_hosts: set[str] = set()
    seen_topics: set[str] = set()
    deferred_same_topic: list[Any] = []
    for source in sources:
        url = str(source.canonical_url or source.url or "").strip()
        if not url or url in seen_urls:
            continue
        host = str(source.source_label or "").strip().casefold()
        if host in seen_hosts and len(sources) > max_sources:
            continue
        topic = label_source_topic(source)
        if selected and topic in seen_topics and _has_unseen_topic_candidate(sources, seen_urls, seen_hosts, seen_topics):
            deferred_same_topic.append(source)
            continue
        selected.append(source)
        seen_urls.add(url)
        if host:
            seen_hosts.add(host)
        if topic:
            seen_topics.add(topic)
        if len(selected) >= max_sources:
            break
    if len(selected) < max_sources:
        for source in deferred_same_topic:
            url = str(source.canonical_url or source.url or "").strip()
            if not url or url in seen_urls:
                continue
            selected.append(source)
            seen_urls.add(url)
            if len(selected) >= max_sources:
                break
    if len(selected) < max_sources:
        for source in sources:
            url = str(source.canonical_url or source.url or "").strip()
            if not url or url in seen_urls:
                continue
            selected.append(source)
            seen_urls.add(url)
            if len(selected) >= max_sources:
                break
    return selected


def _has_unseen_topic_candidate(
    sources: list[Any],
    seen_urls: set[str],
    seen_hosts: set[str],
    seen_topics: set[str],
) -> bool:
    for candidate in sources:
        url = str(candidate.canonical_url or candidate.url or "").strip()
        if not url or url in seen_urls:
            continue
        host = str(candidate.source_label or "").strip().casefold()
        if host and host in seen_hosts:
            continue
        topic = label_source_topic(candidate)
        if topic and topic not in seen_topics:
            return True
    return False


def _append_unique_fact(
    fact: Any,
    *,
    all_facts: list[Any],
    seen_urls: set[str],
    seen_hosts: set[str],
    seen_titles: set[str],
) -> bool:
    source = fact.source
    url = str(source.canonical_url or source.url or "").strip()
    host = str(source.source_label or "").strip().casefold()
    title_key = _title_similarity_key(fact.title)
    if not url or url in seen_urls:
        return False
    if host and host in seen_hosts and len(all_facts) >= 1:
        return False
    if title_key and title_key in seen_titles:
        return False
    all_facts.append(fact)
    seen_urls.add(url)
    if host:
        seen_hosts.add(host)
    if title_key:
        seen_titles.add(title_key)
    return True


def _limit_search_queries(search_queries: tuple[str, ...], *, budget: int) -> tuple[str, ...]:
    selected: list[str] = []
    seen: set[str] = set()
    for query in search_queries:
        value = str(query or "").strip()
        if not value or value in seen:
            continue
        selected.append(value)
        seen.add(value)
        if len(selected) >= max(1, budget):
            break
    return tuple(selected)


def _title_similarity_key(title: str) -> str:
    words = [
        word
        for word in str(title or "").casefold().replace(":", " ").replace("-", " ").split()
        if len(word) >= 4 and word not in {"aktuelle", "news", "neues", "deutschland", "ueberblick", "überblick"}
    ]
    return " ".join(words[:5])


async def execute_single_verified_news(
    *,
    query: str,
    api_key: str = "",
    provider: str,
    model: str | None = None,
) -> dict[str, Any]:
    provider_key = str(provider or "").strip().lower()
    if provider_key not in SUPPORTED_NATIVE_PROVIDERS:
        return {
            "text": "Ich habe aktuell keine ausreichend belastbare Quelle gefunden.",
            "sources": [],
            "metadata": {
                "provider": provider_key or "unknown",
                "pipeline": "websearch_v3",
                "verified_source_mode": "single",
                "status": "skipped",
                "reason": "unsupported_provider",
            },
        }

    async def _search(search_query: str) -> Mapping[str, Any]:
        if provider_key == "gemini":
            gemini_response = await search_gemini_grounded_phase1(
                api_key=api_key,
                query=search_query,
                model=model,
            )
            candidates = normalize_gemini_grounding_response(gemini_response)
            candidate_rows = [
                {
                    "rank": candidate.rank,
                    "url": candidate.url,
                    "title": candidate.title,
                    "snippet_preview": candidate.snippet[:180],
                    "snippet_len": len(candidate.snippet),
                }
                for candidate in candidates
            ]
            return {
                "text": "",
                "sources": [
                    {
                        "url": candidate.url,
                        "title": candidate.title,
                        "snippet": candidate.snippet,
                    }
                    for candidate in candidates
                ],
                "metadata": {
                    "provider": "gemini",
                    "grounding_response": gemini_response,
                    "gemini_debug": {
                        **_gemini_response_debug(gemini_response),
                        "normalized_candidates": candidate_rows,
                    },
                },
            }
        return await execute_websearch_service(
            query=search_query,
            api_key=api_key,
            provider=provider_key,
            model=model,
            log_exceptions=False,
        )

    configured_max_sources = _configured_max_sources()
    policy = source_policy_for_query(query, configured_max_sources)
    pipeline = WebSearchV3Pipeline(_search)
    result = await pipeline.verified_news(query, max_sources=configured_max_sources)
    text = render_single_verified_news(result)
    sources = []
    for fact in result.facts or ((result.fact,) if result.fact else tuple()):
        source = fact.source
        sources.append(
            {
                "url": source.canonical_url,
                "title": source.title,
                "snippet": source.snippet,
                "source_label": source.source_label,
                "provider": source.provider,
                "verified": True,
                "topic_match_score": source.topic_match_score,
                "source_quality_score": source.source_quality_score,
                "source_type": source.source_type,
                "evidence_score": source.evidence_score,
                "topic_label": fact.topic_label,
            }
        )
        if len(sources) >= policy.target_sources:
            break
    return {
        "text": text,
        "sources": sources,
        "metadata": {
                "provider": provider_key,
                "pipeline": "websearch_v3",
                "verified_source_mode": policy.mode,
                "max_sources": policy.target_sources,
                "configured_max_sources": configured_max_sources,
                "search_budget": policy.search_budget,
                "status": result.status,
            "reason": result.reason,
            "search_debug": pipeline.last_search_metadata.get("gemini_debug", {}),
            "quality_debug": {
                "rejected_sources": pipeline.last_search_metadata.get("rejected_sources", []),
            },
        },
    }


def _verified_source_mode(query: str, max_sources: int) -> str:
    if is_broad_briefing_query(query) and max_sources > 2:
        return "briefing"
    return "single" if max_sources == 1 else "multi"


def _configured_max_sources() -> int:
    raw = os.getenv("JANUS_WEBSEARCH_V3_MAX_SOURCES", "1")
    try:
        return max(1, min(int(raw), 4))
    except (TypeError, ValueError):
        return 1


def _gemini_response_debug(response: Mapping[str, Any]) -> dict[str, Any]:
    candidates = response.get("candidates") if isinstance(response.get("candidates"), list) else []
    first = candidates[0] if candidates and isinstance(candidates[0], Mapping) else {}
    if isinstance(first.get("groundingMetadata"), Mapping):
        metadata = first.get("groundingMetadata")  # type: ignore[assignment]
    elif isinstance(first.get("grounding_metadata"), Mapping):
        metadata = first.get("grounding_metadata")  # type: ignore[assignment]
    else:
        metadata = {}
    content = first.get("content") if isinstance(first.get("content"), Mapping) else {}
    parts = content.get("parts") if isinstance(content.get("parts"), list) else []
    chunks = metadata.get("groundingChunks") or metadata.get("grounding_chunks") or []
    supports = metadata.get("groundingSupports") or metadata.get("grounding_supports") or []
    chunk_rows = []
    if isinstance(chunks, list):
        for index, chunk in enumerate(chunks[:8]):
            if not isinstance(chunk, Mapping):
                continue
            web = chunk.get("web") if isinstance(chunk.get("web"), Mapping) else {}
            chunk_rows.append(
                {
                    "index": index,
                    "title": str(web.get("title") or "")[:140],
                    "uri": str(web.get("uri") or "")[:260],
                }
            )
    return {
        "candidate_count": len(candidates),
        "finish_reason": str(first.get("finishReason") or first.get("finish_reason") or ""),
        "grounding_keys": sorted(str(key) for key in metadata.keys()),
        "grounding_chunks": len(chunks) if isinstance(chunks, list) else 0,
        "grounding_supports": len(supports) if isinstance(supports, list) else 0,
        "web_search_queries": metadata.get("webSearchQueries") or metadata.get("web_search_queries") or [],
        "chunk_preview": chunk_rows,
        "part_count": len(parts),
    }
