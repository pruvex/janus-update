import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

def get_api_key(provider: str) -> str | None:
    """Lädt den API-Key für einen gegebenen Anbieter aus der config.json."""
    if not CONFIG_PATH.exists():
        return None
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    return config.get("api_keys", {}).get(provider)
