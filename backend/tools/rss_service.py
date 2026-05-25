import asyncio
from email.utils import parsedate_to_datetime
import html
import logging
import re
import ssl
import time
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import requests
from pydantic import BaseModel, Field

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.services.websearch.websearch import execute_websearch_service

logger = logging.getLogger("janus_backend")


class CleanGetLatestNewsRssToolArgs(BaseModel):
    source: str = Field(
        "auto",
        description=(
            "Feed-Schluessel. 'auto' nutzt kuratierte deutschsprachige News-Feeds. "
            "Einzelquellen: 'spiegel', 'gamestar', 'tagesschau', 'zeit', 'heise', "
            "'golem', 'dlf', 'sz', 'handelsblatt', 'ntv', 'reuters', 'bbc'."
        ),
    )
    query: Optional[str] = Field(
        None,
        description=(
            "Optional: Stichwort zum Filtern der Schlagzeilen, z.B. 'OpenAI', "
            "'Ukraine' oder 'Nintendo'. Bei allgemeinen News leer lassen."
        ),
    )


RSS_FEEDS = {
    "spiegel": "https://www.spiegel.de/schlagzeilen/index.rss",
    "gamestar": "https://www.gamestar.de/news/rss/news.rss",
    "tagesschau": "https://www.tagesschau.de/xml/rss2",
    "zeit": "https://newsfeed.zeit.de/news/index",
    "heise": "https://www.heise.de/rss/heise-atom.xml",
    "golem": "https://rss.golem.de/rss.php?feed=RSS2.0",
    "dlf": "https://www.deutschlandfunk.de/nachrichten-100.rss",
    "sz": "https://rss.sueddeutsche.de/rss/Topthemen",
    "handelsblatt": "https://feeds.cms.handelsblatt.com/schlagzeilen",
    "ntv": "https://www.n-tv.de/rss",
    "reuters": "https://feeds.reuters.com/reuters/topNews",
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
}

AUTO_RSS_SOURCES = (
    "tagesschau",
    "dlf",
    "spiegel",
    "zeit",
    "sz",
    "heise",
    "golem",
    "handelsblatt",
    "ntv",
)

SOURCE_LABELS = {
    "spiegel": "SPIEGEL",
    "gamestar": "GameStar",
    "tagesschau": "Tagesschau",
    "zeit": "ZEIT",
    "heise": "Heise",
    "golem": "Golem",
    "dlf": "Deutschlandfunk",
    "sz": "Sueddeutsche Zeitung",
    "handelsblatt": "Handelsblatt",
    "ntv": "n-tv",
    "reuters": "Reuters",
    "bbc": "BBC",
}

_RSS_HEADERS = {
    "User-Agent": "JanusAI/1.0 RSS (compatible; +https://example.com)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

_QUERY_STOPWORDS = {
    "aktuell",
    "aktuelle",
    "aktuellen",
    "news",
    "nachrichten",
    "neuigkeiten",
    "schlagzeilen",
    "was",
    "gibt",
    "gibt's",
    "gibts",
    "neues",
    "heute",
    "jetzt",
    "zu",
    "zur",
    "zum",
    "über",
    "ueber",
    "uber",
    "der",
    "die",
    "das",
    "den",
    "dem",
    "und",
    "oder",
    "von",
    "in",
}


def _fetch_rss_content(url: str) -> bytes:
    """Synchroner HTTP-Download mit festem Timeout (Diamond Async-Safety)."""
    resp = requests.get(url, timeout=10, headers=_RSS_HEADERS)
    resp.raise_for_status()
    return resp.content


def _clean_rss_text(value: Any, max_chars: int = 260) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(str(value or "")))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip(" ,.;:") + "."


def _entry_value(entry: Any, key: str, default: Any = None) -> Any:
    if isinstance(entry, dict):
        return entry.get(key, default)
    if hasattr(entry, "get"):
        try:
            return entry.get(key, default)
        except TypeError:
            pass
    return getattr(entry, key, default)


def _entry_timestamp(entry: Any) -> float:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = _entry_value(entry, attr)
        if parsed:
            return time.mktime(parsed)
    for attr in ("published", "updated", "created"):
        raw = _entry_value(entry, attr)
        if raw:
            try:
                return parsedate_to_datetime(str(raw)).timestamp()
            except (TypeError, ValueError, OverflowError):
                continue
    return 0.0


def _entry_date(entry: Any) -> str:
    timestamp = _entry_timestamp(entry)
    if not timestamp:
        return ""
    return time.strftime("%d.%m.%Y", time.localtime(timestamp))


def _query_tokens(query: Optional[str]) -> List[str]:
    tokens = [
        token
        for token in re.findall(r"[\wÄÖÜäöüß-]{3,}", str(query or "").casefold())
        if token not in _QUERY_STOPWORDS
    ]
    return list(dict.fromkeys(tokens))


def _entry_matches_query(item: Dict[str, Any], tokens: List[str]) -> bool:
    if not tokens:
        return True
    haystack = f"{item.get('title', '')} {item.get('summary', '')}".casefold()
    return any(token in haystack for token in tokens)


def _websearch_fallback_has_evidence(web_result: dict) -> bool:
    if not isinstance(web_result, dict):
        return False
    metadata = web_result.get("metadata") if isinstance(web_result.get("metadata"), dict) else {}
    status = str(metadata.get("status") or "").strip().lower()
    if status in {"timeout", "error", "unavailable"}:
        return False
    text = str(web_result.get("text") or "").strip()
    sources = web_result.get("sources") if isinstance(web_result.get("sources"), list) else []
    return bool(text or sources)


def _source_label_from_url(url: str) -> str:
    host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", str(url or "").strip(), flags=re.I)).split("/")[0]
    if not host:
        return "Web"
    parts = host.split(".")
    label = parts[-2] if len(parts) >= 2 else parts[0]
    known = {
        "tagesschau": "Tagesschau",
        "spiegel": "SPIEGEL",
        "zeit": "ZEIT",
        "sueddeutsche": "Sueddeutsche Zeitung",
        "heise": "Heise",
        "golem": "Golem",
        "handelsblatt": "Handelsblatt",
        "n-tv": "n-tv",
        "ntv": "n-tv",
        "deutschlandfunk": "Deutschlandfunk",
    }
    return known.get(label.lower(), label[:1].upper() + label[1:])


def _websearch_sources_to_news_items(web_result: dict, max_items: int = 5) -> List[Dict[str, Any]]:
    sources = web_result.get("sources") if isinstance(web_result, dict) else []
    if not isinstance(sources, list):
        return []
    items: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or source.get("source_url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        title = _clean_rss_text(
            source.get("title") or source.get("name") or source.get("source") or url,
            max_chars=180,
        )
        summary = _clean_rss_text(
            source.get("snippet") or source.get("description") or source.get("text"),
            max_chars=280,
        )
        items.append(
            {
                "title": title or "Meldung",
                "summary": summary or "Kurzmeldung aus der Websuche; Details stehen in der verlinkten Quelle.",
                "url": url,
                "source": "websearch",
                "source_label": str(source.get("source") or source.get("domain") or "").strip()
                or _source_label_from_url(url),
                "date": str(source.get("date") or "").strip(),
                "timestamp": 0,
            }
        )
        if len(items) >= max_items:
            break
    return items


async def _fetch_feed_entries(source_key: str, feed_url: str, limit: int = 10) -> List[Dict[str, Any]]:
    raw = await asyncio.to_thread(_fetch_rss_content, feed_url)
    feed = await asyncio.to_thread(feedparser.parse, raw)
    if getattr(feed, "bozo", False):
        raise RuntimeError(f"Feed parsing error: {getattr(feed, 'bozo_exception', '')}")

    items: List[Dict[str, Any]] = []
    for entry in list(getattr(feed, "entries", []) or [])[:limit]:
        title = _clean_rss_text(_entry_value(entry, "title"), max_chars=180)
        if not title:
            continue
        summary = _clean_rss_text(
            _entry_value(entry, "summary")
            or _entry_value(entry, "description"),
            max_chars=280,
        )
        url = str(_entry_value(entry, "link") or "").strip()
        timestamp = _entry_timestamp(entry)
        items.append(
            {
                "title": title,
                "summary": summary,
                "url": url,
                "source": source_key,
                "source_label": SOURCE_LABELS.get(source_key, source_key),
                "date": _entry_date(entry),
                "timestamp": timestamp,
            }
        )
    return items


async def _collect_auto_news(query: Optional[str], max_items: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
    tokens = _query_tokens(query)
    tasks = [
        _fetch_feed_entries(source_key, RSS_FEEDS[source_key], limit=12)
        for source_key in AUTO_RSS_SOURCES
        if source_key in RSS_FEEDS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    items: List[Dict[str, Any]] = []
    failed_sources: List[str] = []
    for source_key, result in zip(AUTO_RSS_SOURCES, results):
        if isinstance(result, Exception):
            failed_sources.append(source_key)
            logger.warning("RSS auto source failed source=%s error=%s", source_key, result)
            continue
        items.extend(item for item in result if _entry_matches_query(item, tokens))

    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for item in sorted(items, key=lambda row: float(row.get("timestamp") or 0), reverse=True):
        key = str(item.get("url") or item.get("title") or "").casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:max_items], failed_sources


async def get_latest_news_rss(
    source: str = "auto",
    query: Optional[str] = None,
    api_key: str = None,
    provider: str = "openai",
    model: str = "gpt-5.4-nano",
    **kwargs,
) -> ToolResultV1:
    """
    Ruft RSS-Feeds ab. Im auto-Modus nutzt Janus zuerst kuratierte deutsche Feeds
    und erst danach eine Provider-Websuche als Fallback.
    """
    started_at = time.perf_counter()
    skill_name = "system.rss_news"
    source_key = str(source or "auto").strip().lower()

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    try:
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context

        if source_key == "auto":
            items, failed_sources = await _collect_auto_news(query, max_items=5)
            if items:
                logger.info(
                    "skill=%s status=ok mode=auto count=%s sources=%s ms=%s",
                    skill_name,
                    len(items),
                    ",".join(sorted({str(item.get("source")) for item in items})),
                    _elapsed_ms(),
                )
                return ToolResultV1(
                    status="ok",
                    data={
                        "mode": "rss_hybrid",
                        "items": items,
                        "headlines": [str(item.get("title") or "") for item in items],
                        "source": "auto",
                        "sources_used": sorted({str(item.get("source")) for item in items}),
                        "failed_sources": failed_sources,
                        "count": len(items),
                        "query": query,
                    },
                    metadata={"execution_time_ms": _elapsed_ms()},
                )

            if query:
                logger.info(
                    "skill=%s status=error code=RSS_NO_MATCH query=%s ms=%s",
                    skill_name,
                    query,
                    _elapsed_ms(),
                )
                return ToolResultV1(
                    status="error",
                    data={},
                    error=ToolErrorDetails(
                        code="RSS_NO_MATCH",
                        message=(
                            f"RSS lieferte keine passenden Treffer fuer '{query}'. "
                            "Nutze system.websearch als belegten Fallback."
                        ),
                    ),
                    metadata={"execution_time_ms": _elapsed_ms()},
                )

            return ToolResultV1(
                status="ok",
                data={
                    "mode": "rss_hybrid",
                    "headlines": [],
                    "items": [],
                    "source": "auto",
                    "failed_sources": failed_sources,
                    "query": query,
                },
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        feed_url = RSS_FEEDS.get(source_key)
        if not feed_url:
            logger.warning("skill=%s status=error code=INVALID_SOURCE source=%s", skill_name, source)
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="INVALID_SOURCE",
                    message=(
                        f"Unbekannte Quelle: {source}. Verfuegbar: {', '.join(RSS_FEEDS.keys())}"
                    ),
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        try:
            entries = await _fetch_feed_entries(source_key, feed_url, limit=10)
        except Exception as fetch_err:
            logger.warning("RSS fetch/parse error for %s: %s", source_key, fetch_err)
            raise

        tokens = _query_tokens(query)
        if tokens:
            entries = [entry for entry in entries if _entry_matches_query(entry, tokens)]

        if not entries:
            if query:
                logger.info(
                    "Keine RSS-Treffer fuer '%s'. Starte Fallback-Websuche mit Provider %s...",
                    query,
                    provider,
                )
                search_q = f"{SOURCE_LABELS.get(source_key, source_key)} News {query}"
                web_result = await execute_websearch_service(
                    query=search_q,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                )
                if not _websearch_fallback_has_evidence(web_result):
                    raise RuntimeError("Websearch fallback returned no reliable evidence")
                fallback_items = _websearch_sources_to_news_items(web_result)
                logger.info("skill=%s status=ok source=websearch_fallback ms=%s", skill_name, _elapsed_ms())
                return ToolResultV1(
                    status="ok",
                    data={
                        "headlines": [],
                        "items": fallback_items,
                        "source": source_key,
                        "fallback": "websearch",
                        "websearch_text": web_result.get("text", "Nichts gefunden."),
                        "websearch_sources": web_result.get("sources", []),
                    },
                    metadata={"execution_time_ms": _elapsed_ms()},
                )
            logger.info("skill=%s status=ok data=[] source=%s ms=%s", skill_name, source_key, _elapsed_ms())
            return ToolResultV1(
                status="ok",
                data={"headlines": [], "items": [], "source": source_key},
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        news_list = [entry["title"] for entry in entries]
        logger.info(
            "skill=%s status=ok count=%s source=%s ms=%s",
            skill_name,
            len(news_list),
            source_key,
            _elapsed_ms(),
        )
        return ToolResultV1(
            status="ok",
            data={
                "headlines": news_list,
                "items": entries,
                "source": source_key,
                "count": len(news_list),
                "formatted": f"Top-Schlagzeilen von '{SOURCE_LABELS.get(source_key, source_key)}':\n"
                + "\n".join(f"- {h}" for h in news_list),
            },
            metadata={"execution_time_ms": _elapsed_ms()},
        )

    except Exception as e:
        logger.error("RSS error: %s", e, exc_info=True)
        try:
            logger.info(
                "RSS-Feed von %s nicht erreichbar. Starte Fallback-Websuche mit Provider %s...",
                source_key,
                provider,
            )
            fallback_query = f"{SOURCE_LABELS.get(source_key, source_key)} aktuelle Schlagzeilen {query or ''}".strip()
            web_result = await execute_websearch_service(
                query=fallback_query,
                api_key=api_key,
                provider=provider,
                model=model,
            )
            if not _websearch_fallback_has_evidence(web_result):
                raise RuntimeError("Websearch fallback returned no reliable evidence")
            fallback_items = _websearch_sources_to_news_items(web_result)
            logger.info("skill=%s status=ok source=websearch_fallback ms=%s", skill_name, _elapsed_ms())
            return ToolResultV1(
                status="ok",
                data={
                    "headlines": [],
                    "items": fallback_items,
                    "source": source_key,
                    "fallback": "websearch",
                    "websearch_text": web_result.get("text", "Keine Ergebnisse."),
                    "websearch_sources": web_result.get("sources", []),
                },
                metadata={"execution_time_ms": _elapsed_ms()},
            )
        except Exception as web_e:
            logger.error("skill=%s status=error code=RSS_AND_WEB_FAILED ms=%s", skill_name, _elapsed_ms())
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="RSS_AND_WEB_FAILED",
                    message=(
                        f"RSS-Quelle '{source_key}' und Websuche konnten keine verlaesslichen News-Belege liefern. "
                        f"Ich erfinde deshalb keine Schlagzeilen. Details: {str(e)} | {str(web_e)}"
                    ),
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )
