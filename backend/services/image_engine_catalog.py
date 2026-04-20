import json
import os
from typing import Dict, List, Optional

CATALOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "image_models.json"))


def _load_catalog_raw() -> List[Dict]:
    with open(CATALOG_FILE, "r", encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def get_catalog_with_install_status() -> List[Dict]:
    catalog = _load_catalog_raw()
    enriched = []
    for model in catalog:
        entry = dict(model)
        entry["is_installed"] = os.path.exists(entry.get("install_dir", ""))
        enriched.append(entry)
    return enriched


def get_model_by_id(model_id: str) -> Optional[Dict]:
    for model in _load_catalog_raw():
        if model.get("id") == model_id:
            return dict(model)
    return None


def choose_model_for_engine(engine_type: str) -> Optional[Dict]:
    catalog = get_catalog_with_install_status()
    # Priorisiere GPU wenn verfügbar
    if engine_type == "gpu":
        gpu_models = [m for m in catalog if m.get("type") == "gpu" and m.get("is_installed")]
        if gpu_models:
            return gpu_models[0]
        cpu_models = [m for m in catalog if m.get("type") == "cpu" and m.get("is_installed")]
        if cpu_models:
            return cpu_models[0]
    elif engine_type == "cpu":
        cpu_models = [m for m in catalog if m.get("type") == "cpu" and m.get("is_installed")]
        if cpu_models:
            return cpu_models[0]
    installed_models = [m for m in catalog if m.get("is_installed")]
    return installed_models[0] if installed_models else None
