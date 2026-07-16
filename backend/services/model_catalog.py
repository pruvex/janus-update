"""Model Catalog Service - lädt den kanonisch gefilterten Modellkatalog."""

from typing import Any, Dict, List

from backend.utils.config_loader import load_model_catalog


def _load_model_catalog() -> List[Dict[str, Any]]:
    """Lädt dieselbe gefilterte Katalogwahrheit wie die System-API."""
    return list(load_model_catalog().values())


def get_models_by_provider(provider: str) -> List[Dict[str, Any]]:
    """Gibt alle Modelle für einen bestimmten Provider zurück.
    
    Args:
        provider: Der Provider-Name (z.B. 'openai', 'gemini', 'ollama')
    
    Returns:
        Liste der Modelle für diesen Provider
    """
    catalog = _load_model_catalog()
    return [model for model in catalog if model.get("provider") == provider]
