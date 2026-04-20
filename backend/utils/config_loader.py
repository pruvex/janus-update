import json
import logging
import os
import shutil
from typing import Any, Dict, List

from backend.utils.paths import get_app_data_dir, resource_path

logger = logging.getLogger("janus_backend")

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_NODE = {
    "id": "localhost",
    "name": "Localhost",
    "url": DEFAULT_OLLAMA_BASE_URL,
    "active": True,
}
DEFAULT_CONFIG: Dict[str, Any] = {
    "ollama_base_url": DEFAULT_OLLAMA_BASE_URL,
    "ollama_nodes": [dict(DEFAULT_OLLAMA_NODE)],
}

DATA_DIR = get_app_data_dir()
MODEL_CATALOG_FILE = os.path.join(DATA_DIR, "model_catalog.json")
TEMPLATE_MODEL_CATALOG_FILE = resource_path("backend/config/model_catalog.json")

# NEU: Pfad zur Hauptkonfigurationsdatei
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
# TEMPLATE_CONFIG_FILE = resource_path("backend/config/config.json") # <-- ENTFERNEN


def initialize_file_from_template(template_path, destination_path):
    if not os.path.exists(destination_path):
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy2(template_path, destination_path)
            logger.info(f"Initialized '{os.path.basename(destination_path)}' from template.")
        except FileNotFoundError:
            logger.error(f"Template file not found: {template_path}. Cannot initialize config.")
            with open(destination_path, "w") as f:
                json.dump({}, f)


def _model_list_to_by_id(models_list: Any) -> Dict[str, Any]:
    if not isinstance(models_list, list):
        return {}
    out: Dict[str, Any] = {}
    for model in models_list:
        if isinstance(model, dict) and model.get("id"):
            out[str(model["id"])] = dict(model)
    return out


def load_model_catalog() -> Dict[str, Any]:
    """
    Lädt den Modell-Katalog als Merge aus Vorlage + optionaler AppData-Datei.

    - **Vorlage:** ``backend/config/model_catalog.json`` (liefert u. a. neue Felder wie ``desc``).
    - **AppData:** ``%APPDATA%/Janus Projekt/model_catalog.json`` — pro Modell-ID werden
      Einträge **über** die Vorlage gelegt (gleiche Keys: Benutzer gewinnt).

    So bleiben lokale Anpassungen erhalten, fehlende neue Felder aus dem Release (z. B.
    Beschreibungstexte) werden aber ergänzt.
    """
    template_path = resource_path("backend/config/model_catalog.json")
    template_by_id: Dict[str, Any] = {}
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_by_id = _model_list_to_by_id(json.load(f))
            logger.info("Loaded template model catalog: %s", template_path)
        except Exception as e:
            logger.error("Failed to load template model catalog: %s", e)

    app_data_path = os.path.join(get_app_data_dir(), "model_catalog.json")
    user_by_id: Dict[str, Any] = {}
    if os.path.exists(app_data_path):
        try:
            with open(app_data_path, "r", encoding="utf-8") as f:
                user_by_id = _model_list_to_by_id(json.load(f))
            logger.info("Merging user model catalog from AppData: %s", app_data_path)
        except Exception as e:
            logger.error("Failed to load catalog from AppData: %s", e)

    merged: Dict[str, Any] = {}
    for mid in set(template_by_id) | set(user_by_id):
        if mid in template_by_id and mid in user_by_id:
            merged[mid] = {**template_by_id[mid], **user_by_id[mid]}
        elif mid in template_by_id:
            merged[mid] = dict(template_by_id[mid])
        else:
            merged[mid] = dict(user_by_id[mid])

    if not merged:
        logger.error("No model catalog found after template/AppData merge.")
    return merged

# NEU: Funktion zum Laden der Hauptkonfigurationsdatei
def load_config_data() -> Dict[str, Any]:
    """Lädt die Hauptkonfigurationsdaten aus der config.json."""
    # Ensure the config file exists and is initialized from template if not present
    # No, we don't want to initialize from template here. We want to load what exists.
    # The initialization happens when the backend starts through ChatOrchestrator.
    try:
        if not os.path.exists(CONFIG_FILE): # <-- NEU: Prüfe Existenz VOR dem Öffnen
            logger.warning(f"Config file does not exist at {CONFIG_FILE}. Returning empty config.")
            return _ensure_ollama_nodes(dict(DEFAULT_CONFIG))

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            if not isinstance(loaded_config, dict):
                return _ensure_ollama_nodes(dict(DEFAULT_CONFIG))
            merged_config = dict(DEFAULT_CONFIG)
            merged_config.update(loaded_config)
            return _ensure_ollama_nodes(merged_config)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding config.json at {CONFIG_FILE}: {e}")
        return _ensure_ollama_nodes(dict(DEFAULT_CONFIG))
    except Exception as e: # NEU: Allgemeine Fehler abfangen
        logger.error(f"An unexpected error occurred while loading config from {CONFIG_FILE}: {e}")
        return _ensure_ollama_nodes(dict(DEFAULT_CONFIG))

# NEU: Funktion zum Speichern der Hauptkonfigurationsdatei
def save_config_data(config_data: Dict[str, Any]):
    """Speichert die Hauptkonfigurationsdaten in die config.json."""
    normalized_config = _ensure_ollama_nodes(dict(config_data or {}))
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized_config, f, indent=2)
    logger.info(f"Config data saved to {CONFIG_FILE}.")


def _normalize_ollama_base_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = f"http://{raw}"
    return raw.rstrip("/")


def _ensure_ollama_nodes(config_data: Dict[str, Any]) -> Dict[str, Any]:
    normalized_config = dict(DEFAULT_CONFIG)
    normalized_config.update(config_data or {})

    nodes_raw = normalized_config.get("ollama_nodes")
    nodes_list: List[Dict[str, Any]] = []
    seen_ids = set()

    if isinstance(nodes_raw, list):
        for index, node in enumerate(nodes_raw):
            if not isinstance(node, dict):
                continue
            node_url = _normalize_ollama_base_url(node.get("url"))
            if not node_url:
                continue
            node_id = str(node.get("id") or "").strip() or f"node_{index + 1}"
            if node_id in seen_ids:
                continue
            seen_ids.add(node_id)
            node_name = str(node.get("name") or "").strip() or node_id
            nodes_list.append(
                {
                    "id": node_id,
                    "name": node_name,
                    "url": node_url,
                    "active": bool(node.get("active")),
                }
            )

    localhost_exists = any(
        str(node.get("id")) == "localhost"
        or _normalize_ollama_base_url(node.get("url")) == DEFAULT_OLLAMA_BASE_URL
        for node in nodes_list
    )
    if not localhost_exists:
        nodes_list.insert(
            0,
            {
                "id": "localhost",
                "name": "Localhost",
                "url": DEFAULT_OLLAMA_BASE_URL,
                "active": not nodes_list,
            },
        )

    has_active_node = any(bool(node.get("active")) for node in nodes_list)
    if not has_active_node:
        localhost_node = next(
            (
                node
                for node in nodes_list
                if str(node.get("id")) == "localhost"
                or _normalize_ollama_base_url(node.get("url")) == DEFAULT_OLLAMA_BASE_URL
            ),
            None,
        )
        if localhost_node is None:
            localhost_node = {
                "id": "localhost",
                "name": "Localhost",
                "url": DEFAULT_OLLAMA_BASE_URL,
                "active": True,
            }
            nodes_list.insert(0, localhost_node)
        localhost_node["active"] = True

    first_active_id = next((str(node.get("id")) for node in nodes_list if bool(node.get("active"))), str(nodes_list[0].get("id")))
    for node in nodes_list:
        node["active"] = str(node.get("id")) == first_active_id

    active_node = next((node for node in nodes_list if node.get("active")), nodes_list[0])

    normalized_config["ollama_nodes"] = nodes_list
    normalized_config["ollama_base_url"] = str(active_node.get("url") or DEFAULT_OLLAMA_BASE_URL)
    return normalized_config