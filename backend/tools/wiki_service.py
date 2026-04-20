import logging
import time

import wikipediaapi
from pydantic import BaseModel, Field

from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1

logger = logging.getLogger("janus_backend")


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


async def get_wikipedia_summary(query: str, lang: str = "de", **kwargs) -> ToolResultV1:
    """Sucht auf Wikipedia. Mit eingebauter Ähnlichkeitssuche. Gibt ToolResultV1 zurück."""
    import wikipedia
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
            wikipedia.set_lang(lang)
            search_results = wikipedia.search(query, results=3)

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
        if len(summary) > 2000:
            truncated = summary[:2000].rstrip()
            truncated += "... [Text für lokales LLM gekürzt.]"
        else:
            truncated = summary

        logger.info("skill=%s status=ok title=%s ms=%s", skill_name, page.title, _elapsed_ms())
        return ToolResultV1(
            status="ok",
            data={
                "title": page.title,
                "summary": truncated,
                "url": page.fullurl,
            },
            metadata={"execution_time_ms": _elapsed_ms()},
        )
    except Exception as e:
        logger.error("skill=%s status=error code=API_ERROR error=%s ms=%s", skill_name, e, _elapsed_ms(), exc_info=True)
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="API_ERROR",
                message=str(e),
            ),
            metadata={"execution_time_ms": _elapsed_ms()},
        )
