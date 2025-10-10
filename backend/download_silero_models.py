import os
import urllib.request
import logging
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

# Model configurations
SILERO_MODELS = {
    "en": {"name": "en_v3", "url": "https://models.silero.ai/models/tts/en/v3_en.pt"},
    "de": {"name": "de_v3", "url": "https://models.silero.ai/models/tts/de/v3_de.pt"},
}

CACHE_DIR = os.path.join(get_app_data_dir(), "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def download_models():
    """Download Silero models if they don't exist."""
    for lang, info in SILERO_MODELS.items():
        local_path = os.path.join(CACHE_DIR, info["name"] + ".pt")
        if not os.path.exists(local_path):
            logger.info(f"Downloading Silero model {info['name']}...")
            try:
                urllib.request.urlretrieve(info["url"], local_path)
                logger.info(f"Silero model downloaded to {local_path}")
            except Exception as e:
                logger.error(f"Failed to download Silero model: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download_models()
