import os
from openai import AsyncOpenAI
from typing import Any

# Initialisiere Client global mit ENV-Key
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def perform_websearch(query: str) -> str:
    """
    Führt eine Websuche mit GPTs eingebautem web.search Tool aus
    und gibt die Ergebnisse zurück.
    """
    response = await openai_client.responses.create(
        model="gpt-4o-mini",
        input=f"Suche im Web nach: {query}",
        tools=[{"type": "web_search"}],
    )
    return response.output_text or "Keine Ergebnisse gefunden."