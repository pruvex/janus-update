import logging
from typing import Optional

from backend.utils.config_loader import load_model_catalog
from .base_provider import WebSearchResult, validate_websearch_result
from .duckduckgo_provider import DuckDuckGoWebSearchProvider
from .gemini_provider import GeminiWebSearchProvider
from .openai_provider import OpenAIWebSearchProvider

logger = logging.getLogger("janus_backend")

OPENAI_PROVIDER = OpenAIWebSearchProvider()
GEMINI_PROVIDER = GeminiWebSearchProvider()
DUCKDUCKGO_PROVIDER = DuckDuckGoWebSearchProvider()


async def execute_websearch_service(
    query: str,
    api_key: str,
    provider: str,
    model: Optional[str] = None,
) -> WebSearchResult:
    """Gateway-Funktion mit harter Provider-Weiche ohne Cloud-zu-DDG-Fallback."""
    provider_key = (provider or "").strip().lower()
    if not provider_key:
        config = load_model_catalog()
        provider_key = str(config.get("last_used_provider", "") or "").strip().lower()
        if not provider_key:
            raise RuntimeError("WEBSEARCH_PROVIDER_MISSING: No request provider supplied and no default provider configured")
        logger.info("WEBSEARCH-SERVICE: provider missing in request, using configured default '%s'", provider_key)

    logger.info("WEBSEARCH-SERVICE: request_provider='%s' model='%s' query='%s'", provider_key, model or "", query)

    if provider_key == "gemini":
        if not api_key:
            logger.error("💎 WEBSEARCH CRASH: PROVIDER_KEY_MISSING for provider=gemini")
            raise RuntimeError("PROVIDER_KEY_MISSING: Gemini native web search requires an API key")
        try:
            result = await GEMINI_PROVIDER.search(api_key=api_key, query=query, model=model)
            return validate_websearch_result(result)
        except Exception as exc:
            logger.error("💎 WEBSEARCH CRASH: %s", str(exc), exc_info=True)
            if "timeout" in str(exc).lower():
                logger.warning("WEBSEARCH-SERVICE: Gemini search timed out. Graceful fail.")
                return {
                    "text": "Die Suche dauerte zu lange (Timeout). Bitte versuche es später erneut oder präzisiere deine Anfrage.",
                    "sources": [],
                    "metadata": {"status": "timeout", "provider": "gemini"}
                }
            raise

    if provider_key == "openai":
        if not api_key:
            logger.error("💎 WEBSEARCH CRASH: PROVIDER_KEY_MISSING for provider=openai")
            raise RuntimeError("PROVIDER_KEY_MISSING: OpenAI native web search requires an API key")
        try:
            result = await OPENAI_PROVIDER.search(api_key=api_key, query=query, model=model)
            return validate_websearch_result(result)
        except Exception as exc:
            logger.error("💎 WEBSEARCH CRASH: %s", str(exc), exc_info=True)
            if "timeout" in str(exc).lower():
                logger.warning("WEBSEARCH-SERVICE: OpenAI search timed out. Graceful fail.")
                return {
                    "text": "Die Suche dauerte zu lange (Timeout). Bitte versuche es später erneut oder präzisiere deine Anfrage.",
                    "sources": [],
                    "metadata": {"status": "timeout", "provider": "openai"}
                }
            raise

    if provider_key == "ollama":
        logger.info("WEBSEARCH-SERVICE: routing provider='ollama' to DuckDuckGo fallback")
        try:
            result = await DUCKDUCKGO_PROVIDER.search(api_key="", query=query, model=model)
            return validate_websearch_result(result)
        except Exception as exc:
            logger.error("💎 WEBSEARCH CRASH: %s", str(exc), exc_info=True)
            raise

    logger.error("💎 WEBSEARCH CRASH: WEBSEARCH_PROVIDER_UNSUPPORTED provider=%s", provider_key)
    raise RuntimeError(f"WEBSEARCH_PROVIDER_UNSUPPORTED: Unsupported websearch provider '{provider_key}'")
