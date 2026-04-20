import json
import logging
import os
from backend.utils.paths import get_app_data_dir, resource_path  # Importiere get_app_data_dir

logger = logging.getLogger("janus_backend")

# ÄNDERUNG: Versuche zuerst, die Datei aus AppData zu laden (wo Updates landen)
def get_model_catalog_path():
    app_data_path = os.path.join(get_app_data_dir(), "model_catalog.json")
    if os.path.exists(app_data_path):
        return app_data_path
    # Fallback auf Installationsverzeichnis
    return resource_path("backend/config/model_catalog.json")

MODEL_CATALOG_FILE = get_model_catalog_path()

def load_model_prices():
    # Pfad dynamisch neu holen, falls Datei erst später erstellt wurde
    current_path = get_model_catalog_path() 
    try:
        with open(current_path, "r", encoding="utf-8") as f:  # Encoding utf-8 ist sicherer
            models = json.load(f)
        return {model["id"]: model for model in models}
    except Exception as e:
        logger.error(f"Error loading model catalog from {current_path}: {e}")
        return {}


USD_TO_EUR_CONVERSION_RATE = 0.9009
# Initiales Laden der Preise beim Start
MODEL_PRICES = load_model_prices()


def calculate_cost(model_id: str, usage_data: dict = None, custom_prompt: str = None) -> tuple[dict, dict]:
    """
    Berechnet die Kosten für ein gegebenes Modell basierend auf Nutzungsdaten oder Bildparametern.
    """
    # Zugriff auf das Modul-Level Dictionary
    prices = MODEL_PRICES
    
    # Fallback: Wenn das Modell nicht im Cache ist, versuche neu zu laden (ohne 'global' Keyword Hack)
    if model_id not in prices:
        prices = load_model_prices()
        
    if model_id not in prices:
        logger.warning(f"Price for model {model_id} not found.")
        return {}, {}

    model_info = prices[model_id]
    model_type = model_info.get("type")

    usage = {}
    cost_usd = 0.0

    # --- FALL A: TEXT & AUDIO (Jetzt robuster) ---
    if (model_type == "text" or model_type == "audio") and usage_data is not None:
        input_tokens = 0
        output_tokens = 0

        # Helper um Attribute oder Keys sicher zu holen
        def get_val(obj, keys, default=0):
            for k in keys:
                if isinstance(obj, dict):
                    if k in obj: return obj[k]
                else:
                    if hasattr(obj, k): return getattr(obj, k)
            return default

        # Wir suchen nach 'prompt_tokens' (LLM) ODER 'input_tokens' (TTS/Generic)
        input_tokens = get_val(usage_data, ['prompt_tokens', 'input_tokens'])
        # Wir suchen nach 'completion_tokens' (LLM) ODER 'output_tokens' (Generic)
        output_tokens = get_val(usage_data, ['completion_tokens', 'output_tokens'])

        input_cost_per_token = model_info.get("cost_per_token_input", 0)
        output_cost_per_token = model_info.get("cost_per_token_output", 0)
        
        cost_usd = (input_tokens * input_cost_per_token) + (output_tokens * output_cost_per_token)
        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}

    # --- FALL B: BILD GENERIERUNG ---
    elif model_type == "image":
        if model_info.get("provider") == "openai":
            requested_quality = usage_data.get("quality", model_info.get("default_quality", "medium"))
            requested_size = usage_data.get("size", model_info.get("default_size", "1024x1024"))

            if ("pricing" in model_info and 
                requested_quality in model_info["pricing"] and 
                requested_size in model_info["pricing"][requested_quality]):
                
                cost_usd = model_info["pricing"][requested_quality][requested_size]
            else:
                cost_usd = 0.0 
            
            usage = {"image_quality": requested_quality, "image_size": requested_size}

        elif model_info.get("provider") == "gemini":
            default_res = model_info.get("default_resolution", "1K")
            requested_res = usage_data.get("image_size") or default_res
                        
            tokens_table = model_info.get("tokens_per_resolution", {})
            output_tokens = tokens_table.get(requested_res, tokens_table.get("1K", 1290))
            
            cost_per_million_output = model_info.get("cost_per_million_tokens_output", 0.0)
            output_cost_usd = (output_tokens / 1_000_000) * cost_per_million_output
            
            input_tokens_per_image = 560
            cost_per_million_input = model_info.get("cost_per_million_tokens_input", 0.0)
            input_cost_usd = (input_tokens_per_image / 1_000_000) * cost_per_million_input
            
            cost_usd = output_cost_usd + input_cost_usd
            
            default_ratio = model_info.get("default_aspect_ratio", "1:1")
            requested_ratio = usage_data.get("aspect_ratio") or default_ratio
                        
            usage = {
                "input_tokens": input_tokens_per_image,
                "output_tokens": output_tokens,
                "image_quality": "standard",                 
                "image_size": f"{requested_ratio} ({requested_res})"
            }

        else:
            cost_usd = model_info.get("cost_per_image", 0)
            usage = {"image_quality": "standard", "image_size": "1024x1024"}

    # --- FALL C: WEBSUCHE ---
    elif model_type == "websearch":
        cost_usd = model_info.get("cost_per_query", 0)
        usage = {"query_count": 1}

    # Endberechnung
    total_cost_eur = cost_usd * USD_TO_EUR_CONVERSION_RATE
    cost = {"total_cost": total_cost_eur}

    if model_type == "image":
        cost["image_cost"] = cost_usd * USD_TO_EUR_CONVERSION_RATE
    elif model_type == "websearch":
        cost["query_cost"] = cost_usd * USD_TO_EUR_CONVERSION_RATE

    return usage, cost


def get_image_pricing_structure() -> dict:
    structured_pricing = {}
    for model_id, model_info in MODEL_PRICES.items():
        if model_info.get("type") == "image":
            provider = model_info["provider"]
            if provider not in structured_pricing:
                structured_pricing[provider] = {}
            structured_pricing[provider][model_id] = model_info
    return structured_pricing
