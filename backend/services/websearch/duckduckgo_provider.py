import asyncio
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from .base_provider import BaseWebSearchProvider, WebSearchResult, WebSearchSource

logger = logging.getLogger("janus_backend")


def _looks_like_generic_ddg_summary(text: str) -> bool:
    normalized = " ".join(str(text or "").strip().lower().split())
    if not normalized:
        return True
    markers = {
        "keine prägnanten ergebnisse.",
        "keine pragnanten ergebnisse.",
        "keine prägnanten suchergebnisse.",
        "keine pragnanten suchergebnisse.",
    }
    return normalized in markers


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    unique_values: List[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique_values.append(normalized)
    return unique_values


def _normalize_duckduckgo_result_url(url: str) -> str:
    normalized = str(url or "").strip()
    if not normalized:
        return ""
    try:
        parsed = urlparse(normalized)
        if parsed.netloc.casefold().endswith("duckduckgo.com"):
            query_params = parse_qs(parsed.query)
            candidate = query_params.get("uddg", [""])[0] or query_params.get("rut", [""])[0]
            if candidate:
                return unquote(candidate).strip()
    except Exception:
        return normalized
    return normalized


def _looks_like_internal_duckduckgo_url(url: str) -> bool:
    normalized = str(url or "").strip()
    if not normalized:
        return True
    parsed = urlparse(normalized)
    host = parsed.netloc.casefold()
    if not host:
        return True
    return host.endswith("duckduckgo.com")


class DuckDuckGoWebSearchProvider(BaseWebSearchProvider):
    """Lightweight, no-key web search using DuckDuckGo's Instant Answer API."""

    ENDPOINT = "https://api.duckduckgo.com/"
    HTML_ENDPOINT = "https://html.duckduckgo.com/html/"

    @staticmethod
    def _http_headers() -> Dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    @staticmethod
    def _empty_result() -> WebSearchResult:
        """Return empty WebSearchResult."""
        return {
            "text": "",
            "sources": [],
            "metadata": {"provider": "duckduckgo"},
        }

    @classmethod
    def _parse_html_results(cls, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(str(html or ""), "html.parser")
        urls: List[str] = []
        snippets: List[str] = []

        for result in soup.select(".result, .web-result, .result.results_links, div[data-layout='organic']"):
            link = result.select_one("a.result__a, h2 a, a[data-testid='result-title-a']")
            snippet = result.select_one(".result__snippet, .result__extras__url + a, .excerpt, [data-result='snippet']")
            title = " ".join(link.get_text(" ", strip=True).split()) if link else ""
            href = _normalize_duckduckgo_result_url(str(link.get("href") or "").strip()) if link else ""
            snippet_text = " ".join(snippet.get_text(" ", strip=True).split()) if snippet else ""
            if href:
                urls.append(href)
            line_parts = [part for part in [title, snippet_text] if part]
            if line_parts:
                snippets.append(" - ".join(line_parts))

        if not urls and not snippets:
            for link in soup.select("a[href]"):
                href = _normalize_duckduckgo_result_url(str(link.get("href") or "").strip())
                if not href or _looks_like_internal_duckduckgo_url(href):
                    continue
                title = " ".join(link.get_text(" ", strip=True).split())
                if len(title) < 3:
                    continue
                container = link.find_parent(["div", "article", "li", "tr"]) or link.parent
                context_text = ""
                if container is not None:
                    context_text = " ".join(container.get_text(" ", strip=True).split())
                snippet_text = context_text
                if snippet_text.startswith(title):
                    snippet_text = snippet_text[len(title):].strip(" -–—|:·")
                urls.append(href)
                line_parts = [part for part in [title, snippet_text[:220] if snippet_text else ""] if part]
                snippets.append(" - ".join(line_parts))

        unique_urls = _dedupe_preserve_order(urls)
        unique_snippets = _dedupe_preserve_order(snippets)
        if not unique_urls and not unique_snippets:
            title_text = " ".join((soup.title.get_text(" ", strip=True) if soup.title else "").split())
            preview_text = " ".join(soup.get_text(" ", strip=True).split())[:300]
            logger.info(
                "DDG-HTML: no structured results title=%r preview=%r",
                title_text,
                preview_text,
            )
        logger.info(
            "DDG-HTML: parsed results urls=%s snippets=%s html_chars=%s",
            len(unique_urls),
            len(unique_snippets),
            len(str(html or "")),
        )
        return {
            "text": "\n\n".join(f"- {snippet}" for snippet in unique_snippets[:5]),
            "urls": unique_urls[:10],
            "usage": {},
            "cost": {},
        }

    async def _search_html_results(self, query: str) -> Dict[str, Any]:
        try:
            response = await asyncio.to_thread(
                requests.get,
                self.HTML_ENDPOINT,
                params={"q": query},
                headers=self._http_headers(),
                timeout=15,
            )
            response.raise_for_status()
            return self._parse_html_results(response.text)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout) as exc:
            logger.warning(
                "DuckDuckGo HTML search soft-failed for query '%s': %s",
                query,
                exc,
            )
            return self._empty_result()
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "DuckDuckGo HTML search request failed for query '%s': %s",
                query,
                exc,
            )
            return self._empty_result()

    async def _search_via_library(self, query: str) -> Optional[Dict[str, Any]]:
        """Primary search via duckduckgo-search library (handles anti-bot measures)."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.debug("DDG-LIB: duckduckgo-search not installed, skipping library search")
            return None

        try:
            def _run():
                with DDGS() as ddgs:
                    return list(ddgs.text(query, region="de-de", max_results=8))

            raw_results = await asyncio.to_thread(_run)
            if not raw_results:
                return None

            urls: List[str] = []
            snippets: List[str] = []
            for item in raw_results:
                title = str(item.get("title") or "").strip()
                href = str(item.get("href") or "").strip()
                body = str(item.get("body") or "").strip()
                if href:
                    urls.append(href)
                line_parts = [part for part in [title, body] if part]
                if line_parts:
                    snippets.append(" - ".join(line_parts))

            if not urls and not snippets:
                return None

            text = "\n\n".join(f"- {s}" for s in snippets[:6])

            # 💎 DIAMOND: Sources are returned separately in WebSearchResult, never appended to text
            logger.info(
                "DDG-LIB: query='%s' results=%s urls=%s text_chars=%s",
                query, len(raw_results), len(urls), len(text),
            )
            # 💎 DIAMOND: Return WebSearchResult
            sources: list[WebSearchSource] = []
            for url in urls[:10]:
                try:
                    domain = urlparse(url).netloc.replace("www.", "")
                except Exception:
                    domain = url
                sources.append({
                    "url": url,
                    "title": domain or "Quelle",
                })
            result: WebSearchResult = {
                "text": text,
                "sources": sources,
                "metadata": {"provider": "duckduckgo"},
            }
            return result

        except Exception as exc:
            logger.warning("DDG-LIB: library search failed for query '%s': %s", query, exc)
            return None

    async def search(self, api_key: str, query: str, model: Optional[str] = None) -> WebSearchResult:
        """Execute DuckDuckGo search and return WebSearchResult."""
        # 1. Primär: duckduckgo-search Library (robuster gegen Captcha)
        lib_result = await self._search_via_library(query)
        if lib_result:
            return lib_result

        # 2. Fallback: Instant Answer API + HTML-Scraping
        logger.info("DDG: library search empty, falling back to Instant Answer + HTML scraping")
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1,
        }
        try:
            response = await asyncio.to_thread(
                requests.get,
                self.ENDPOINT,
                params=params,
                headers=self._http_headers(),
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout) as exc:
            logger.warning(
                "DuckDuckGo search soft-failed for query '%s': %s",
                query,
                exc,
            )
            return self._empty_result()
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "DuckDuckGo search request failed for query '%s': %s",
                query,
                exc,
            )
            return self._empty_result()

        summary = str(payload.get("AbstractText") or payload.get("AbstractURL") or "Keine prägnanten Ergebnisse.")
        related = payload.get("RelatedTopics") or []
        urls: List[str] = []
        snippets: List[str] = []

        def _extract_entry(entry: Dict[str, Any]) -> None:
            if not isinstance(entry, dict):
                return
            text = entry.get("Text")
            url = entry.get("FirstURL")
            if text:
                snippets.append(text)
            if url:
                urls.append(url)

        for item in related:
            if isinstance(item, dict) and item.get("Topics"):
                for sub in item.get("Topics"):
                    _extract_entry(sub)
            else:
                _extract_entry(item)

        if not snippets and payload.get("Results"):
            for item in payload.get("Results"):
                _extract_entry(item)

        unique_snippets = _dedupe_preserve_order(snippets)
        snippet_lines = [f"- {snippet}" for snippet in unique_snippets[:5]]

        summary_is_generic = _looks_like_generic_ddg_summary(summary)
        text_parts: List[str] = []
        if summary and not summary_is_generic:
            text_parts.append(summary)
        if snippet_lines:
            text_parts.extend(snippet_lines)
        if not text_parts:
            text_parts.append(summary)

        combined_text = "\n\n".join(part for part in text_parts if str(part or "").strip())

        html_results = await self._search_html_results(query)
        html_text = str(html_results.get("text") or "").strip()
        html_urls = html_results.get("urls") if isinstance(html_results.get("urls"), list) else []

        if html_text and summary_is_generic and not snippet_lines:
            combined_text = ""

        final_text_parts = [part for part in [combined_text, html_text] if str(part or "").strip()]
        # 💎 DIAMOND: Normalize to WebSearchResult
        final_urls = _dedupe_preserve_order([*_dedupe_preserve_order(urls), *[str(url).strip() for url in html_urls if str(url).strip()]])
        
        # Build sources from URLs (DDG doesn't provide titles reliably)
        sources: list[WebSearchSource] = []
        for url in final_urls[:10]:
            try:
                domain = urlparse(url).netloc.replace("www.", "")
            except Exception:
                domain = url
            sources.append({
                "url": url,
                "title": domain or "Quelle",
            })
        
        logger.info(
            "DDG: query='%s' instant_snippets=%s instant_urls=%s html_urls=%s final_sources=%s final_text_chars=%s",
            query,
            len(unique_snippets),
            len(_dedupe_preserve_order(urls)),
            len([str(url).strip() for url in html_urls if str(url).strip()]),
            len(sources),
            len("\n\n".join(final_text_parts)),
        )

        result: WebSearchResult = {
            "text": "\n\n".join(final_text_parts),
            "sources": sources,
            "metadata": {"provider": "duckduckgo"},
        }
        return result
