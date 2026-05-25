from __future__ import annotations

import asyncio
import re

import requests
from bs4 import BeautifulSoup

from .models import PageFetchResult, SearchCandidate
from .url_normalizer import host_for_url


DEFAULT_HEADERS = {
    "User-Agent": "Janus-WebSearchV3/1.0 (+https://local.janus)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _resolve_vertex_redirect(url: str, timeout: int) -> str:
    if host_for_url(url) != "vertexaisearch.cloud.google.com":
        return url
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=False)
    location = response.headers.get("Location") or response.headers.get("location") or ""
    return str(location or url)


def _first_meta_content(soup: BeautifulSoup, keys: tuple[str, ...]) -> str | None:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag:
            value = str(tag.get("content") or "").strip()
            if value:
                return value
    for tag in soup.find_all("time"):
        value = str(tag.get("datetime") or "").strip()
        if value:
            return value
    return None


def _extract_text(html: str) -> tuple[str, str, str, str | None]:
    soup = BeautifulSoup(str(html or ""), "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = ""
    if soup.title:
        title = " ".join(soup.title.get_text(" ", strip=True).split())
    language = str((soup.html or {}).get("lang") or "").strip() if soup.html else ""
    published_at = _first_meta_content(
        soup,
        (
            "article:published_time",
            "og:published_time",
            "datePublished",
            "datepublished",
            "publishdate",
            "pubdate",
            "dc.date",
            "date",
        ),
    )
    text = " ".join(soup.get_text(" ", strip=True).split())
    text = re.sub(r"\s+", " ", text).strip()
    return _repair_mojibake(title), _repair_mojibake(text), language, published_at


def _response_html(response: requests.Response) -> str:
    apparent = str(response.apparent_encoding or "").lower().replace("_", "-")
    declared = str(response.encoding or "").lower().replace("_", "-")
    if apparent in {"utf-8", "utf-8-sig"} and declared not in {"utf-8", "utf-8-sig"}:
        return response.content.decode(response.apparent_encoding or "utf-8", errors="replace")
    return response.text


def _repair_mojibake(value: str) -> str:
    text = str(value or "")
    if not any(marker in text for marker in ("Ã", "Â")):
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if repaired.count("�") <= text.count("�") else text


async def fetch_candidate_page(candidate: SearchCandidate, timeout: int = 10) -> PageFetchResult:
    def _request() -> PageFetchResult:
        request_url = candidate.url
        try:
            request_url = _resolve_vertex_redirect(candidate.url, timeout)
            response = requests.get(request_url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return PageFetchResult(
                    url=candidate.url,
                    final_url=str(response.url or request_url or candidate.url),
                    status_code=response.status_code,
                    title=candidate.title,
                    text="",
                    error=f"non_html:{content_type}",
                )
            title, text, language, published_at = _extract_text(_response_html(response))
            return PageFetchResult(
                url=candidate.url,
                final_url=str(response.url or candidate.url),
                status_code=response.status_code,
                title=title or candidate.title,
                text=text[:12000],
                language_hint=language,
                published_at=published_at,
            )
        except Exception as exc:
            return PageFetchResult(
                url=candidate.url,
                final_url=request_url or candidate.url,
                status_code=None,
                title=candidate.title,
                text="",
                error=str(exc),
            )

    return await asyncio.to_thread(_request)
