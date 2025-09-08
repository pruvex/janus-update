import openai
from typing import Any

async def perform_websearch(query: str, api_key: str) -> str:
    """
    Führt eine Websuche mit GPTs eingebautem web.search Tool aus
    und gibt die Ergebnisse zurück.
    """
    client = openai.AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini", # Use gpt-4o-mini as specified
        messages=[
            {"role": "system", "content": "Du bist ein Websuche-Assistent."},
            {"role": "user", "content": f"Suche nach: {query}"}
        ],
        tools=[{"type": "web_search"}],  # GPT internes Tool
    )
    # GPT packt Suchergebnisse in die message
    return response.choices[0].message.content
