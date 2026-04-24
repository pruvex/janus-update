"""Model Catalog Service - Lädt und filtert Modelle aus model_catalog.json."""

import json
from pathlib import Path
from typing import List, Dict, Any
from backend.utils.paths import get_app_data_dir

CONFIG_FILE = Path(get_app_data_dir()) / "config"
MODEL_CATALOG_FILE = CONFIG_FILE / "model_catalog.json"


def _load_model_catalog() -> List[Dict[str, Any]]:
    """Lädt das Model-Katalog-JSON."""
    # Fallback: Prüfe sowohl App-Data als auch Projekt-Root
    possible_paths = [
        MODEL_CATALOG_FILE,
        Path(__file__).parent.parent.parent / "config" / "model_catalog.json",
        Path(__file__).parent.parent.parent.parent / "backend" / "config" / "model_catalog.json",
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    
    # Fallback zur lokalen Projektstruktur
    local_fallback = Path(__file__).parent.parent.parent / "config" / "model_catalog.json"
    if local_fallback.exists():
        with open(local_fallback, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return []


def get_models_by_provider(provider: str) -> List[Dict[str, Any]]:
    """Gibt alle Modelle für einen bestimmten Provider zurück.
    
    Args:
        provider: Der Provider-Name (z.B. 'openai', 'gemini', 'ollama')
    
    Returns:
        Liste der Modelle für diesen Provider
    """
    catalog = _load_model_catalog()
    return [model for model in catalog if model.get("provider") == provider]
