import json
import logging
import re
import time
import urllib.parse
import urllib.request

import wikipediaapi
from pydantic import BaseModel, Field

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1

logger = logging.getLogger("janus_backend")

WIKIPEDIA_SUMMARY_MAX_SENTENCES = 4
WIKIPEDIA_SUMMARY_MAX_CHARS = 900
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")


def _condense_wikipedia_summary(
    text: str,
    *,
    max_sentences: int = WIKIPEDIA_SUMMARY_MAX_SENTENCES,
    max_chars: int = WIKIPEDIA_SUMMARY_MAX_CHARS,
) -> str:
    """Keep the Wikipedia lead's opening sentences instead of dumping a long excerpt."""
    value = " ".join(str(text or "").split())
    if not value:
        return ""

    sentences = [part.strip() for part in _SENTENCE_SPLIT_RE.split(value) if part.strip()]
    if not sentences:
        return value[:max_chars].rstrip()

    selected: list[str] = []
    total_len = 0
    for sentence in sentences[:max_sentences]:
        next_len = len(sentence) if not selected else total_len + 1 + len(sentence)
        if selected and next_len > max_chars:
            break
        selected.append(sentence)
        total_len = next_len

    if selected:
        return " ".join(selected)

    return value[:max_chars].rstrip()


class CleanGetWikipediaSummaryArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Exakter Wikipedia-Artikelname oder präziser Suchbegriff "
            "(z.B. 'Eiffelturm', 'Thermodynamik', 'Bundeskanzler'). Keine ganzen Nutzerfragen — nur das Lemma/Thema."
        ),
    )
    lang: str = Field(
        "de",
        description="ISO-Sprachcode der Wikipedia-Edition (typisch 'de' oder 'en').",
    )


def _search_wikipedia_titles(query: str, lang: str = "de", limit: int = 3) -> list[str]:
    params = urllib.parse.urlencode(
        {
            "action": "opensearch",
            "search": query,
            "limit": str(limit),
            "namespace": "0",
            "format": "json",
        }
    )
    url = f"https://{lang}.wikipedia.org/w/api.php?{params}"
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
        return [str(title).strip() for title in data[1] if str(title).strip()]
    return []


async def get_wikipedia_summary(query: str, lang: str = "de", **kwargs) -> ToolResultV1:
    """Sucht auf Wikipedia. Mit eingebauter Ähnlichkeitssuche. Gibt ToolResultV1 zurück."""
    import asyncio

    started_at = time.perf_counter()
    skill_name = "system.wikipedia_summary"

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    try:
        wiki_wiki = wikipediaapi.Wikipedia(
            user_agent='Janus AI Assistant (janus.projekt@example.com)',
            language=lang,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
        )

        page = wiki_wiki.page(query)

        if not page.exists():
            logger.warning(f"Wikipedia-Artikel '{query}' nicht exakt gefunden. Starte Suche...")
            search_results = await asyncio.to_thread(_search_wikipedia_titles, query, lang, 3)

            if search_results:
                best_match = search_results[0]
                logger.info(f"Nutze besten Treffer: '{best_match}' statt '{query}'")
                page = wiki_wiki.page(best_match)
            else:
                logger.warning("skill=%s status=error code=NOT_FOUND query=%s ms=%s", skill_name, query, _elapsed_ms())
                return ToolResultV1(
                    status="error",
                    data={},
                    error=ToolErrorDetails(
                        code="NOT_FOUND",
                        message=f"Weder Artikel noch ähnliche Ergebnisse für '{query}' gefunden.",
                    ),
                    metadata={"execution_time_ms": _elapsed_ms()},
                )

        if not page.exists():
            logger.warning("skill=%s status=error code=NOT_FOUND query=%s ms=%s", skill_name, query, _elapsed_ms())
            return ToolResultV1(
                status="error",
                data={},
                error=ToolErrorDetails(
                    code="NOT_FOUND",
                    message=f"Artikel '{query}' existiert nicht.",
                ),
                metadata={"execution_time_ms": _elapsed_ms()},
            )

        summary = page.summary or ""
        logger.info(f"Wikipedia-Zusammenfassung für '{page.title}' erfolgreich abgerufen.")
        condensed = _condense_wikipedia_summary(summary)

        logger.info("skill=%s status=ok title=%s ms=%s", skill_name, page.title, _elapsed_ms())
        return ToolResultV1(
            status="ok",
            data={
                "title": page.title,
                "summary": condensed,
                "url": page.fullurl,
            },
            metadata={
                "execution_time_ms": _elapsed_ms(),
                "summary_mode": "wikipedia_lead_sentences",
                "source_chars": len(summary),
                "summary_chars": len(condensed),
            },
        )
    except Exception as e:
        logger.error("skill=%s status=error code=API_ERROR error=%s ms=%s", skill_name, e, _elapsed_ms(), exc_info=True)
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="API_ERROR",
                message=(
                    f"Wikipedia konnte fuer '{query}' nicht verlaesslich abgerufen werden. "
                    "Ohne erreichbare Wikipedia-Quelle gebe ich keine belegte Zusammenfassung aus."
                ),
                details={"exception": str(e), "source": f"wikipedia:{lang}"},
            ),
            metadata={"execution_time_ms": _elapsed_ms()},
        )
