import os
import re
from openai import AsyncOpenAI
from typing import Dict, Any
import logging
from backend.services.cost_calculator import calculate_cost # NEU: Importiere calculate_cost

logger = logging.getLogger("janus_backend")
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def perform_websearch(query: str) -> Dict[str, Any]:
    """
    Führt IMMER eine Websuche mit dem spezialisierten Web-Search-Tool von OpenAI (via gpt-4o-mini) durch,
    um die qualitativ hochwertigsten und am besten belegten Ergebnisse zu erhalten. Benutze dieses Werkzeug,
    wenn der Benutzer nach aktuellen Ereignissen, Preisen, Definitionen oder Fakten fragt, die nach 2023
    passiert sind oder sich ändern können.
    """
    try:
        response = await openai_client.responses.create(
            model="gpt-4o-mini",
            input=f"Führe eine Websuche durch und gib eine detaillierte, faktenbasierte Antwort auf die folgende Frage: {query}",
            tools=[{"type": "web_search"}],
        )
        text_output = response.output_text or "Keine Ergebnisse gefunden."
        urls = []
        if hasattr(response, "citations") and response.citations:
            for citation in response.citations:
                if hasattr(citation, "url") and citation.url:
                    urls.append(citation.url)

        # Fallback zur URL-Extraktion aus dem Text
        if not urls and text_output:
            url_pattern = r"https?://[\S]+"
            found_urls = re.findall(url_pattern, text_output)
            urls.extend(found_urls)
            if urls:
                urls = list(dict.fromkeys(urls))

        # NEU: Kosten für die Websuche berechnen
        usage, cost = calculate_cost("websearch") # model_id "websearch" verwenden

        return {"text": text_output, "urls": urls, "usage": usage, "cost": cost} # NEU: usage und cost zurückgeben
    except Exception as e:
        logger.error(f"Error during OpenAI web search: {e}", exc_info=True)
        return {
            "text": f"Bei der Websuche über die OpenAI API ist ein Fehler aufgetreten.",
            "urls": [],
            "usage": {}, # NEU: Leere usage und cost bei Fehler
            "cost": {}
        }
