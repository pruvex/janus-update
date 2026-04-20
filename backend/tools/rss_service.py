import asyncio
import logging
import ssl
import time
from typing import Optional

import feedparser
import requests
from pydantic import BaseModel, Field

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.services.websearch.websearch import execute_websearch_service

logger = logging.getLogger("janus_backend")


class CleanGetLatestNewsRssToolArgs(BaseModel):
    source: str = Field(
        ...,
        description=(
            "Fest codierter Feed-Schlüssel (kein Freitext): "
            "'spiegel', 'gamestar', 'tagesschau', 'zeit', 'heise', 'reuters', 'bbc'. "
            "Genau so schreiben wie in der Liste."
        ),
    )
    query: Optional[str] = Field(
        None,
        description=(
            "Optional: Stichwort zum Filtern der Schlagzeilen (z.B. 'Nintendo', 'Ukraine'). "
            "Nur setzen, wenn der Nutzer ein konkretes Thema will; bei allgemeinen News leer lassen."
        ),
    )


RSS_FEEDS = {
    "spiegel": "https://www.spiegel.de/schlagzeilen/index.rss",
    "gamestar": "https://www.gamestar.de/news/rss/news.rss",
    "tagesschau": "https://www.tagesschau.de/xml/rss2",
    "zeit": "https://newsfeed.zeit.de/news/index",
    "heise": "https://www.heise.de/rss/heise-atom.xml",
    "reuters": "https://feeds.reuters.com/reuters/topNews",
    "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
}

_RSS_HEADERS = {
    "User-Agent": "JanusAI/1.0 RSS (compatible; +https://example.com)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}


def _fetch_rss_content(url: str) -> bytes:
    """Synchroner HTTP-Download mit festem Timeout (Diamond Async-Safety)."""
    resp = requests.get(url, timeout=10, headers=_RSS_HEADERS)
    resp.raise_for_status()
    return resp.content


async def get_latest_news_rss(
    source: str,
    query: Optional[str] = None,
    api_key: str = None,
    provider: str = "openai",
    model: str = "gpt-5.4-nano",  # Internal alias for the default model
    **kwargs,
) -> ToolResultV1:
    """
    Ruft RSS-Feeds ab. Bei Fehler Fallback auf Websuche mit dem korrekten Provider.
    Gibt ToolResultV1 zurück.
    """
    started_at = time.perf_counter()
    skill_name = "system.rss_news"

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    try:
        # ssl hack (legacy feeds)
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context

        feed_url = RSS_FEEDS.get(source.lower())
        if not feed_url:
            logger.warning("skill=%s status=error code=INVALID_SOURCE source=%s", skill_name, source)
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="INVALID_SOURCE",
                    message=(
                        f"Unbekannte Quelle: {source}. Verfügbar: {', '.join(RSS_FEEDS.keys())}"
                    ),
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        try:
            raw = await asyncio.to_thread(_fetch_rss_content, feed_url)
            feed = await asyncio.to_thread(feedparser.parse, raw)
        except Exception as fetch_err:
            logger.warning("RSS fetch/parse error for %s: %s", source, fetch_err)
            raise

        if feed.bozo:
            logger.warning(f"RSS Feed Fehler bei {source}: {feed.bozo_exception}")
            raise RuntimeError("Feed parsing error")

        entries = feed.entries[:10]
        if query:
            query_lower = query.lower()
            # Suche in Titel UND Zusammenfassung
            entries = [
                e
                for e in entries
                if query_lower in e.title.lower() or query_lower in (e.get("summary", "")).lower()
            ]

        if not entries:
            # Wenn Filter zu strikt war -> Fallback Websuche
            if query:
                logger.info(
                    f"Keine RSS-Treffer für '{query}'. Starte Fallback-Websuche mit Provider {provider}..."
                )
                search_q = f"{source} news {query}"
                web_result = await execute_websearch_service(
                    query=search_q, api_key=api_key, provider=provider, model=model
                )
                logger.info("skill=%s status=ok source=websearch_fallback ms=%s", skill_name, _elapsed_ms())
                return ToolResultV1(
                    status="ok",
                    data={
                        "headlines": [],
                        "source": source,
                        "fallback": "websearch",
                        "websearch_text": web_result.get("text", "Nichts gefunden."),
                    },
                    metadata={"execution_time_ms": _elapsed_ms()},
                )
            logger.info("skill=%s status=ok data=[] source=%s ms=%s", skill_name, source, _elapsed_ms())
            return ToolResultV1(
                status="ok",
                data={"headlines": [], "source": source},
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        news_list = [entry.title for entry in entries]

        logger.info("skill=%s status=ok count=%s source=%s ms=%s", skill_name, len(news_list), source, _elapsed_ms())
        return ToolResultV1(
            status="ok",
            data={
                "headlines": news_list,
                "source": source,
                "count": len(news_list),
                "formatted": f"Top-Schlagzeilen von '{source.capitalize()}':\n"
                + "\n".join(f"- {h}" for h in news_list),
            },
            metadata={"execution_time_ms": _elapsed_ms()},
        )

    except Exception as e:
        logger.error("RSS error: %s", e, exc_info=True)
        try:
            logger.info(
                f"RSS-Feed von {source} nicht erreichbar. Starte Fallback-Websuche mit Provider {provider}..."
            )
            fallback_query = f"{source} aktuelle schlagzeilen {query if query else ''}"

            web_result = await execute_websearch_service(
                query=fallback_query,
                api_key=api_key,
                provider=provider,
                model=model,
            )
            logger.info("skill=%s status=ok source=websearch_fallback ms=%s", skill_name, _elapsed_ms())
            return ToolResultV1(
                status="ok",
                data={
                    "headlines": [],
                    "source": source,
                    "fallback": "websearch",
                    "websearch_text": web_result.get("text", "Keine Ergebnisse."),
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
                    message=f"Fehler beim Abrufen der News (RSS & Web): {str(e)} | {str(web_e)}",
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )
