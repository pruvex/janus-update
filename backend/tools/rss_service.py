import asyncio
import logging
import ssl
from typing import Optional

import feedparser
from pydantic import BaseModel, Field

# Lokaler Import für Websuche, um Zirkelbezüge zu vermeiden
# from backend.tool_registry import perform_websearch (Achtung: Zirkelbezug Gefahr!)
# Besser: Wir importieren den Service direkt
from backend.services.websearch.websearch import perform_websearch_service

logger = logging.getLogger("janus_backend")


class CleanGetLatestNewsRssToolArgs(BaseModel):
    source: str = Field(
        ...,
        description="Die Quelle: 'spiegel', 'gamestar', 'tagesschau', 'zeit', 'heise', 'reuters', 'bbc'.",
    )
    query: Optional[str] = Field(
        None,
        description="Optional. Nutze dies NUR, wenn der Benutzer explizit nach einem bestimmten Thema fragt (z.B. 'News zu Nintendo'). Bei allgemeinen Anfragen ('Was gibt es Neues?') lasse dieses Feld LEER.",
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


# WICHTIG: api_key und provider als Argumente hinzufügen!
async def get_latest_news_rss(
    source: str,
    query: Optional[str] = None,
    api_key: str = None,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    **kwargs,
) -> dict:
    """
    Ruft RSS-Feeds ab. Bei Fehler Fallback auf Websuche mit dem korrekten Provider.
    """
    # ssl hack
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context

    feed_url = RSS_FEEDS.get(source.lower())
    if not feed_url:
        return {
            "status": "error",
            "output": f"Unbekannte Quelle: {source}. Verfügbar: {', '.join(RSS_FEEDS.keys())}",
        }

    try:
        # Timeout-Handling für den Feed-Download
        feed = await asyncio.to_thread(feedparser.parse, feed_url)

        if feed.bozo:
            logger.warning(f"RSS Feed Fehler bei {source}: {feed.bozo_exception}")
            # Fallback auslösen
            raise Exception("Feed parsing error")

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
                # WICHTIG: Hier nutzen wir den Service direkt mit den injizierten Credentials
                web_result = await perform_websearch_service(
                    query=search_q, api_key=api_key, provider=provider, model=model
                )
                return {
                    "status": "success",
                    "output": f"Keine direkten RSS-Treffer, aber hier sind Suchergebnisse:\n{web_result.get('text', 'Nichts gefunden.')}",
                }
            else:
                return {"status": "success", "output": "Keine Nachrichten gefunden."}

        # Formatierung der RSS-Einträge
        news_list = []
        for entry in entries:
            news_list.append(f"- {entry.title}")

        return {
            "status": "success",
            "output": f"Top-Schlagzeilen von '{source.capitalize()}':\n" + "\n".join(news_list),
        }

    except Exception as e:
        logger.error(f"RSS Download Fehler: {e}")
        # Fallback Websuche bei generellem Fehler (z.B. Timeout)
        try:
            logger.info(
                f"RSS-Feed von {source} nicht erreichbar. Starte Fallback-Websuche mit Provider {provider}..."
            )
            fallback_query = f"{source} aktuelle schlagzeilen {query if query else ''}"

            # WICHTIG: Provider und Key weiterreichen!
            web_result = await perform_websearch_service(
                query=fallback_query,
                api_key=api_key,
                provider=provider,  # <--- DAS IST DER FIX
                model=model,
            )
            return {
                "status": "success",
                "output": f"Feed nicht erreichbar, hier sind Suchergebnisse:\n{web_result.get('text', 'Keine Ergebnisse.')}",
            }
        except Exception as web_e:
            return {
                "status": "error",
                "output": f"Fehler beim Abrufen der News (RSS & Web): {str(e)} | {str(web_e)}",
            }
