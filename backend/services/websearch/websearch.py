# backend/services/websearch/websearch.py (Der Gateway)
import logging
from typing import Dict, Any

from backend.utils.config_loader import load_model_catalog
from .openai_provider import OpenAIWebSearchProvider
from .gemini_provider import GeminiWebSearchProvider

logger = logging.getLogger("janus_backend")

# Mapping von Provider-Namen zu den Implementierungs-Klassen
PROVIDERS = {
    "openai": OpenAIWebSearchProvider(),
    "gemini": GeminiWebSearchProvider(),
}

async def perform_websearch_service(
    query: str,
    api_key: str,
    provider: str = None,
    model: str = None,
) -> Dict[str, Any]:
    """
    Gateway-Funktion: Wählt den passenden Provider und führt die Suche aus.
    """
    if not provider:
        config = load_model_catalog()
        provider = config.get("last_used_provider", "openai").lower()
        logger.info(f"Provider not explicitly set. Using default from config: {provider}")

    search_provider = PROVIDERS.get(provider.lower())
    
    if not search_provider:
        logger.error(f"Web search for provider '{provider}' is not implemented.")
        return {
            "text": f"Websuche für Provider '{provider}' nicht implementiert.",
            "urls": [], "usage": {}, "cost": {},
        }
    
    logger.info(f"perform_websearch called for provider: '{provider}'")
    
    return await search_provider.search(api_key=api_key, query=query, model=model)
