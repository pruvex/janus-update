import openai
from typing import Any

async def perform_websearch(query: str, openai_client: openai.OpenAI) -> str:
    """
    Führt eine Websuche mit GPTs eingebautem web.search Tool aus
    und gibt die Ergebnisse zurück.
    """
    response = await openai_client.chat.completions.create(
        model="gpt-4.1", # Assuming gpt-4.1 supports web_search tool
        messages=[
            {"role": "system", "content": "Du bist ein Websuche-Assistent."},
            {"role": "user", "content": query} # Pass query directly
        ],
        tools=[{"type": "web_search"}],  # GPT internes Tool
    )
    # Das ist der wichtige Teil:
    if response.output_text is not None:
        return response.output_text
    return ""
