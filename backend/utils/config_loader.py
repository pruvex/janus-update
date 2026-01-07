import json
import logging
import os
import shutil
from typing import Any, Dict

from backend.utils.paths import get_app_data_dir, resource_path

logger = logging.getLogger("janus_backend")

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


def load_model_catalog() -> Dict[str, Any]:
    """
    Lädt den Modell-Katalog.
    Priorität 1: %APPDATA%/Janus Projekt/model_catalog.json (Benutzer-Config)
    Priorität 2: Install-Ordner/backend/config/model_catalog.json (Fallback/Original)
    """
    # 1. Suche im AppData Ordner
    app_data_path = os.path.join(get_app_data_dir(), "model_catalog.json")
    
    if os.path.exists(app_data_path):
        try:
            with open(app_data_path, 'r', encoding='utf-8') as f:
                logger.info(f"Loading model catalog from AppData: {app_data_path}")
                models_list = json.load(f)
                return {model["id"]: model for model in models_list}
        except Exception as e:
            logger.error(f"Failed to load catalog from AppData: {e}")

    # 2. Fallback: Installationsverzeichnis
    fallback_path = resource_path("backend/config/model_catalog.json")
    
    if os.path.exists(fallback_path):
        try:
            with open(fallback_path, 'r', encoding='utf-8') as f:
                logger.info(f"Loading model catalog from internal resources: {fallback_path}")
                models_list = json.load(f)
                return {model["id"]: model for model in models_list}
        except Exception as e:
            logger.error(f"Failed to load internal catalog: {e}")
            
    logger.error("No model catalog found in AppData or resources.")
    return {}  # Leeres Dict zurückgeben, damit der Code nicht crasht

# NEU: Funktion zum Laden der Hauptkonfigurationsdatei
def load_config_data() -> Dict[str, Any]:
    """Lädt die Hauptkonfigurationsdaten aus der config.json."""
    # Ensure the config file exists and is initialized from template if not present
    # No, we don't want to initialize from template here. We want to load what exists.
    # The initialization happens when the backend starts through ChatOrchestrator.
    try:
        if not os.path.exists(CONFIG_FILE): # <-- NEU: Prüfe Existenz VOR dem Öffnen
            logger.warning(f"Config file does not exist at {CONFIG_FILE}. Returning empty config.")
            return {}

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding config.json at {CONFIG_FILE}: {e}")
        return {}
    except Exception as e: # NEU: Allgemeine Fehler abfangen
        logger.error(f"An unexpected error occurred while loading config from {CONFIG_FILE}: {e}")
        return {}

# NEU: Funktion zum Speichern der Hauptkonfigurationsdatei
def save_config_data(config_data: Dict[str, Any]):
    """Speichert die Hauptkonfigurationsdaten in die config.json."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    logger.info(f"Config data saved to {CONFIG_FILE}.")