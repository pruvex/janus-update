import json
import os
import logging
from backend.utils.paths import resource_path

logger = logging.getLogger("janus_backend")

MODEL_CATALOG_FILE = resource_path("backend/config/model_catalog.json")


def load_model_prices():
    try:
        with open(MODEL_CATALOG_FILE, "r") as f:
            models = json.load(f)
        return {model["id"]: model for model in models}
    except Exception as e:
        logger.error(f"Error loading model catalog: {e}")
        return {}

# KORREKTUR: Die Variable wird jetzt konsistent verwendet.
USD_TO_EUR_CONVERSION_RATE = 0.9009 # 1 Euro = 1.11 Dollar, also 1 Dollar = 1/1.11 Euro

MODEL_PRICES = load_model_prices()


def calculate_cost(model_id, usage_data=None, custom_prompt=None):
    if model_id not in MODEL_PRICES:
        logger.warning(f"Price for model {model_id} not found.")
        return {}, {}

    model_info = MODEL_PRICES[model_id]
    model_type = model_info.get("type")

    usage = {}
    cost_usd = 0.0

    if model_type == "text" and usage_data is not None:
        if isinstance(usage_data, dict):
            input_tokens = usage_data.get("prompt_tokens", 0)
            output_tokens = usage_data.get("completion_tokens", 0)
        else:
            input_tokens = usage_data.prompt_tokens
            output_tokens = usage_data.completion_tokens

        input_cost_per_token = model_info.get("cost_per_token_input", 0)
        output_cost_per_token = model_info.get("cost_per_token_output", 0)

        input_cost_usd = input_tokens * input_cost_per_token
        output_cost_usd = output_tokens * output_cost_per_token
        
        cost_usd = input_cost_usd + output_cost_usd

        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}

    elif model_type == "image":
        image_cost_usd = model_info.get("cost_per_image", 0)
        cost_usd = image_cost_usd

        usage = {"image_quality": "standard", "image_size": "1024x1024"}

    elif model_type == "websearch": # NEU: Websuchkosten
        cost_usd = model_info.get("cost_per_query", 0)
        usage = {"query_count": 1} # Eine Websuche

    # Umrechnung von USD in EUR am Ende der Berechnung
    if USD_TO_EUR_CONVERSION_RATE > 0:
        total_cost_eur = cost_usd * USD_TO_EUR_CONVERSION_RATE
    else:
        total_cost_eur = cost_usd
        
    cost = {"total_cost": total_cost_eur}

    # KORREKTUR: Bei Bildern muss auch der `image_cost` umgerechnet werden.
    if model_type == "image":
        cost["image_cost"] = cost_usd * USD_TO_EUR_CONVERSION_RATE
    elif model_type == "websearch": # NEU: Websuchkosten
        cost["query_cost"] = cost_usd * USD_TO_EUR_CONVERSION_RATE

    return usage, cost