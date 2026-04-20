"""Legacy import path for OllamaServiceProvider; implementation lives in ``ollama.service``."""

from backend.llm_providers.ollama.service import OllamaServiceProvider

__all__ = ["OllamaServiceProvider"]
