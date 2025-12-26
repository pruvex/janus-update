# backend/llm_providers/__init__.py

from .base_provider import BaseLLMProvider
from .openai_service import OpenAIServiceProvider
# Fügen Sie hier Imports für Ihre anderen Provider hinzu, falls vorhanden
from .gemini_service import GeminiServiceProvider 

# Eine Registry, die die Provider-Namen auf die Service-Klassen abbildet
PROVIDERS = {
    "openai": OpenAIServiceProvider(),
    "gemini": GeminiServiceProvider(),
    # Fügen Sie hier weitere Provider hinzu
}

def get_provider(provider_name: str) -> BaseLLMProvider:
    """
    Diese Funktion ist unser "Gateway". Sie wählt den richtigen Provider-Service
    anhand des Namens aus.
    """
    provider = PROVIDERS.get(provider_name.lower())
    if provider is None:
        raise ValueError(f"Provider '{provider_name}' is not supported or not configured.")
    return provider