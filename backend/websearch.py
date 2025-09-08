import openai
from typing import Any

async def perform_websearch(query: str, api_key: str) -> str:
    """
    Führt eine Websuche mit GPTs eingebautem web.search Tool aus
    und gibt die Ergebnisse zurück.
    """
    client = openai.AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4.1", # or a model with web access
        messages=[
            {"role": "user", "content": f"Suche im Web nach: {query}"}
        ],
        tools=[{"type": "web_search"}],  # GPT internes Tool
    )
    # Extract response text
    if response.output_text is not None:
        return response.output_text
    return ""
