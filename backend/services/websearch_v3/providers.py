from __future__ import annotations

from typing import Any, Iterable, Mapping

from .models import SearchCandidate
from .url_normalizer import normalize_url


def candidates_from_websearch_result(result: Mapping[str, Any], provider: str = "") -> list[SearchCandidate]:
    metadata = result.get("metadata") if isinstance(result.get("metadata"), Mapping) else {}
    provider_name = str(provider or metadata.get("provider") or "unknown")
    grounding_metadata = metadata.get("grounding_metadata") if isinstance(metadata.get("grounding_metadata"), Mapping) else {}
    if provider_name == "gemini" and grounding_metadata:
        grounded = candidates_from_gemini_grounding_metadata(grounding_metadata)
        if grounded:
            return grounded

    openai_native_sources = []
    if isinstance(metadata.get("url_citations"), list):
        openai_native_sources.extend(metadata.get("url_citations") or [])
    if isinstance(metadata.get("web_search_sources"), list):
        openai_native_sources.extend(metadata.get("web_search_sources") or [])
    if provider_name == "openai" and openai_native_sources:
        native = _candidates_from_sources(_merge_sources_by_url(openai_native_sources), provider_name)
        if native:
            return native

    raw_sources = result.get("sources") if isinstance(result.get("sources"), list) else []
    return _candidates_from_sources(raw_sources, provider_name)


def _merge_sources_by_url(raw_sources: list[Any]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for source in raw_sources:
        if not isinstance(source, Mapping):
            continue
        url = normalize_url(str(source.get("url") or source.get("uri") or source.get("source_url") or ""))
        if not url:
            continue
        if url not in merged:
            merged[url] = {"url": url}
            order.append(url)
        target = merged[url]
        for key in ("title", "name", "snippet", "text", "description"):
            value = str(source.get(key) or "").strip()
            if value and (not target.get(key) or len(value) > len(str(target.get(key) or ""))):
                target[key] = value
    return [merged[url] for url in order]


def _candidates_from_sources(raw_sources: list[Any], provider_name: str) -> list[SearchCandidate]:
    candidates: list[SearchCandidate] = []
    for rank, source in enumerate(raw_sources, start=1):
        if not isinstance(source, Mapping):
            continue
        url = normalize_url(str(source.get("url") or source.get("uri") or source.get("source_url") or ""))
        if not url:
            continue
        candidates.append(
            SearchCandidate(
                provider=provider_name,
                url=url,
                title=str(source.get("title") or source.get("name") or "").strip(),
                snippet=str(source.get("snippet") or source.get("text") or source.get("description") or "").strip(),
                rank=rank,
                metadata=dict(source),
            )
        )
    return candidates


def candidates_from_gemini_grounding_metadata(metadata: Mapping[str, Any]) -> list[SearchCandidate]:
    return _candidates_from_gemini_metadata(metadata)


def normalize_gemini_grounding_response(response: Mapping[str, Any]) -> list[SearchCandidate]:
    """Normalize Gemini google_search groundingMetadata per official API contract."""
    candidates = response.get("candidates") if isinstance(response.get("candidates"), list) else []
    if not candidates or not isinstance(candidates[0], Mapping):
        return []
    metadata = {}
    if isinstance(candidates[0].get("groundingMetadata"), Mapping):
        metadata = candidates[0].get("groundingMetadata")  # type: ignore[assignment]
    elif isinstance(candidates[0].get("grounding_metadata"), Mapping):
        metadata = candidates[0].get("grounding_metadata")  # type: ignore[assignment]
    return _candidates_from_gemini_metadata(metadata)


def _candidates_from_gemini_metadata(metadata: Mapping[str, Any]) -> list[SearchCandidate]:
    chunks = metadata.get("groundingChunks") if isinstance(metadata.get("groundingChunks"), list) else metadata.get("grounding_chunks") if isinstance(metadata.get("grounding_chunks"), list) else []
    supports = metadata.get("groundingSupports") if isinstance(metadata.get("groundingSupports"), list) else metadata.get("grounding_supports") if isinstance(metadata.get("grounding_supports"), list) else []

    snippets_by_chunk: dict[int, list[str]] = {}
    for support in supports:
        if not isinstance(support, Mapping):
            continue
        segment = support.get("segment") if isinstance(support.get("segment"), Mapping) else {}
        segment_text = str(segment.get("text") or "").strip()
        if not segment_text:
            continue
        indices = support.get("groundingChunkIndices") or support.get("grounding_chunk_indices") or []
        for index in indices:
            if isinstance(index, int):
                snippets_by_chunk.setdefault(index, []).append(segment_text)

    normalized: list[SearchCandidate] = []
    for rank, chunk in enumerate(chunks, start=1):
        if not isinstance(chunk, Mapping):
            continue
        web = chunk.get("web") if isinstance(chunk.get("web"), Mapping) else {}
        url = normalize_url(str(web.get("uri") or ""))
        if not url:
            continue
        normalized.append(
            SearchCandidate(
                provider="gemini",
                url=url,
                title=str(web.get("title") or "").strip(),
                snippet=" ".join(snippets_by_chunk.get(rank - 1, [])[:3]).strip(),
                rank=rank,
                metadata={"grounding_chunk": dict(chunk), "grounding_supports": snippets_by_chunk.get(rank - 1, [])},
            )
        )
    return normalized


def normalize_openai_response_output(output_items: Iterable[Any]) -> list[SearchCandidate]:
    """Normalize OpenAI Responses web_search citations/sources per official API contract."""
    raw_sources: list[dict[str, Any]] = []

    for item in output_items or []:
        item_type = getattr(item, "type", "") if not isinstance(item, Mapping) else item.get("type", "")
        if item_type == "web_search_call":
            action = getattr(item, "action", None) if not isinstance(item, Mapping) else item.get("action")
            sources = getattr(action, "sources", None) if action is not None and not isinstance(action, Mapping) else (action or {}).get("sources", [])
            for source in sources or []:
                if hasattr(source, "model_dump"):
                    raw_sources.append(source.model_dump())
                elif isinstance(source, Mapping):
                    raw_sources.append(dict(source))
        if item_type == "message":
            content_blocks = getattr(item, "content", None) if not isinstance(item, Mapping) else item.get("content", [])
            for block in content_blocks or []:
                annotations = getattr(block, "annotations", None) if not isinstance(block, Mapping) else block.get("annotations", [])
                text = getattr(block, "text", "") if not isinstance(block, Mapping) else block.get("text", "")
                for annotation in annotations or []:
                    ann_type = getattr(annotation, "type", "") if not isinstance(annotation, Mapping) else annotation.get("type", "")
                    if ann_type != "url_citation":
                        continue
                    raw_sources.append(
                        {
                            "url": getattr(annotation, "url", "") if not isinstance(annotation, Mapping) else annotation.get("url", ""),
                            "title": getattr(annotation, "title", "") if not isinstance(annotation, Mapping) else annotation.get("title", ""),
                            "text": text,
                        }
                    )

    return candidates_from_websearch_result({"sources": raw_sources, "metadata": {"provider": "openai"}}, provider="openai")
