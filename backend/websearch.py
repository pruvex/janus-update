import openai
from typing import Any

async def perform_websearch(query: str, openai_client: openai.OpenAI) -> str:
    """
    Führt eine Websuche mit GPTs eingebautem web.search Tool aus
    und gibt die Ergebnisse zurück.
    """
    response = await openai_client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Du bist ein Websuche-Assistent."},
            {"role": "user", "content": f"Suche nach: {query}"}
        ],
        tools=[{"type": "web_search"}],  # GPT internes Tool
    )
    # GPT packt Suchergebnisse in die message
    return response.choices[0].message.content
