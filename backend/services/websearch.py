# backend/services/websearch.py (Gateway-Implementierung)

import logging
from typing import Dict, Any, Optional

from backend.utils.config_loader import load_model_catalog
from .websearch.duckduckgo_provider import DuckDuckGoWebSearchProvider
from .websearch.openai_provider import OpenAIWebSearchProvider
from .websearch.gemini_provider import GeminiWebSearchProvider

logger = logging.getLogger("janus_backend")

OPENAI_PROVIDER = OpenAIWebSearchProvider()
GEMINI_PROVIDER = GeminiWebSearchProvider()
DUCKDUCKGO_PROVIDER = DuckDuckGoWebSearchProvider()

async def execute_websearch(
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
    if not provider:
        config = load_model_catalog()
        provider = str(config.get("last_used_provider", "") or "").strip().lower()
        if not provider:
            raise RuntimeError("WEBSEARCH_PROVIDER_MISSING: No request provider supplied and no default provider configured")
        logger.info("WEBSEARCH-GATEWAY: provider missing in request, using configured default '%s'", provider)
    else:
        provider = str(provider).strip().lower()

    logger.info("WEBSEARCH-GATEWAY: request_provider='%s' model='%s' query='%s'", provider, model or "", query)

    if provider == "gemini":
        if not api_key:
            raise RuntimeError("PROVIDER_KEY_MISSING: Gemini native web search requires an API key")
        return await GEMINI_PROVIDER.search(api_key=api_key, query=query, model=model)

    if provider == "openai":
        if not api_key:
            raise RuntimeError("PROVIDER_KEY_MISSING: OpenAI native web search requires an API key")
        return await OPENAI_PROVIDER.search(api_key=api_key, query=query, model=model)

    if provider == "ollama":
        logger.info("WEBSEARCH-GATEWAY: routing provider='ollama' to DuckDuckGo fallback")
        return await DUCKDUCKGO_PROVIDER.search(api_key="", query=query, model=model)

    raise RuntimeError(f"WEBSEARCH_PROVIDER_UNSUPPORTED: Unsupported websearch provider '{provider}'")
