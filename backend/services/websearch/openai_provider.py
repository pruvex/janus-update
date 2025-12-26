# backend/services/websearch/openai_provider.py
import logging
import re  # --- NEU ---
from openai import AsyncOpenAI
from .base_provider import BaseWebSearchProvider
from backend.services.cost_calculator import calculate_cost

logger = logging.getLogger("janus_backend")

class OpenAIWebSearchProvider(BaseWebSearchProvider):
    async def search(self, api_key: str, query: str, model: str) -> dict:
        logger.info(f"Using OpenAI's native web search capability for query: {query}")
        try:
            openai_client = AsyncOpenAI(api_key=api_key)
            logger.info(f"ATTEMPTING RESPONSES API CALL for web search with model: {model}")

            response = await openai_client.responses.create(
                model=model,
                tools=[{"type": "web_search"}],
                input=query
            )

            text_output = ""
            urls = set()

            if response.output_text:
                text_output = response.output_text or "Keine Ergebnisse gefunden."
                
                # Extract all Markdown links directly from the response text
                markdown_links = re.findall(r'\[.*?\]\((https?://[^\s)]+)\)', text_output)
                for url in markdown_links:
                    urls.add(url)

            usage, cost = calculate_cost("websearch", usage_data={"query_count": 1})
            
            # Return the text output and the list of found URLs
            return {"text": text_output, "urls": list(urls), "usage": usage, "cost": cost}

        except Exception as e:
            logger.error(f"Error during OpenAI web search: {e}", exc_info=True)
            return {"text": f"Fehler bei OpenAI Websuche: {e}", "urls": [], "usage": {}, "cost": {}}
