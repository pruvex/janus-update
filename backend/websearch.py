import openai
import os
from typing import Any

# Initialize client once at module level
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def perform_websearch(query: str) -> str:
    """
    Führt eine Websuche mit GPTs eingebautem web.search Tool aus
    und gibt die Ergebnisse zurück.
    """
    response = await openai_client.chat.completions.create(
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