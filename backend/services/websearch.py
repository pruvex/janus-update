# backend/services/websearch.py (Gateway-Implementierung)

import logging
from typing import Dict, Any, Optional

from backend.utils.config_loader import load_model_catalog
from .websearch.openai_provider import OpenAIWebSearchProvider
from .websearch.gemini_provider import GeminiWebSearchProvider

logger = logging.getLogger("janus_backend")

# Mapping von Provider-Namen zu den Implementierungs-Klassen
PROVIDERS = {
    "openai": OpenAIWebSearchProvider(),
    "gemini": GeminiWebSearchProvider(),
}

async def perform_websearch(
    query: str,
    api_key: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gateway-Funktion: Wählt den passenden Provider und führt die Suche aus.
    
    Args:
        query: Die Suchanfrage
        api_key: Der API-Schlüssel für den Provider
        provider: Der zu verwendende Provider ('openai' oder 'gemini')
        model: Das zu verwendende Modell (optional, falls vom Provider benötigt)
        
    Returns:
        Dict mit 'text', 'urls', 'usage' und 'cost'
    """
    # Fallback, falls kein Provider explizit übergeben wird
    if not provider:
        config = load_model_catalog()
        provider = config.get("last_used_provider", "openai").lower()
        logger.info(f"Provider not explicitly set. Using default from config: {provider}")
    else:
        provider = provider.lower()

    search_provider = PROVIDERS.get(provider)
    
    if not search_provider:
        logger.error(f"Web search for provider '{provider}' is not implemented.")
        return {
            "text": f"Websuche für Provider '{provider}' nicht implementiert.",
            "urls": [], 
            "usage": {}, 
            "cost": {},
        }
    
    logger.info(f"perform_websearch called for provider: '{provider}'")
    
    # Ruft die standardisierte .search() Methode des ausgewählten Providers auf
    return await search_provider.search(api_key=api_key, query=query, model=model)
