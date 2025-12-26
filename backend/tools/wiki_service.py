import logging
from typing import Dict

import wikipediaapi
from pydantic import BaseModel, Field

logger = logging.getLogger("janus_backend")


class CleanGetWikipediaSummaryArgs(BaseModel):
    query: str = Field(
        ...,
        description="Der genaue Suchbegriff für Wikipedia (z.B. 'Eiffelturm', 'Thermodynamik').",
    )
    lang: str = Field("de", description="Sprachcode, meist 'de'.")


def get_wikipedia_summary(query: str, lang: str = "de") -> Dict[str, str]:
    """
    Holt Zusammenfassungen von Wikipedia.
    """
    try:
        wiki_wiki = wikipediaapi.Wikipedia(
            "Janus AI Assistant (janus.projekt@example.com)", lang, timeout=10
        )
        page = wiki_wiki.page(query)

        if not page.exists():
            logger.warning(f"Wikipedia-Artikel für '{query}' nicht gefunden.")
            return {
                "status": "success",
                "output": f"Ich konnte leider keinen Wikipedia-Artikel zum Thema '{query}' finden.",
            }

        summary_sentences = page.summary.split(".")
        short_summary = ". ".join(summary_sentences[:3]) + "."

        logger.info(f"Wikipedia-Zusammenfassung für '{query}' erfolgreich abgerufen.")
        return {"status": "success", "output": short_summary}

    except Exception as e:
        logger.error(f"Fehler bei Wikipedia: {e}", exc_info=True)
        return {"status": "error", "message": f"Wikipedia-Fehler: {e}"}
