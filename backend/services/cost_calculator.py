import json
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


USD_TO_EUR_CONVERSION_RATE = 0.9009
MODEL_PRICES = load_model_prices()


def calculate_cost(model_id: str, usage_data: dict = None, custom_prompt: str = None) -> tuple[dict, dict]:
    """
    Berechnet die Kosten für ein gegebenes Modell basierend auf Nutzungsdaten oder Bildparametern.
    Für Bilder werden 'quality' und 'size' aus den usage_data/kwargs erwartet.
    """
    if model_id not in MODEL_PRICES:
        logger.warning(f"Price for model {model_id} not found.")
        return {}, {}

    model_info = MODEL_PRICES[model_id]
    model_type = model_info.get("type")

    usage = {}
    cost_usd = 0.0

    if (model_type == "text" or model_type == "audio") and usage_data is not None:
        input_tokens = usage_data.get("prompt_tokens", 0)
        output_tokens = usage_data.get("completion_tokens", 0)

        input_cost_per_token = model_info.get("cost_per_token_input", 0)
        output_cost_per_token = model_info.get("cost_per_token_output", 0)
        cost_usd = (input_tokens * input_cost_per_token) + (output_tokens * output_cost_per_token)
        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}

    elif model_type == "image":
        if model_info.get("provider") == "openai":
            # Extract quality and size from usage_data (which comes from frontend parameters)
            requested_quality = usage_data.get("quality", model_info.get("default_quality", "medium"))
            requested_size = usage_data.get("size", model_info.get("default_size", "1024x1024"))

            if "pricing" in model_info and \
               requested_quality in model_info["pricing"] and \
               requested_size in model_info["pricing"][requested_quality]:
                
                cost_usd = model_info["pricing"][requested_quality][requested_size]
                usage = {
                    "image_quality": requested_quality,
                    "image_size": requested_size
                }
            else:
                logger.warning(f"Pricing for OpenAI image model {model_id} with quality {requested_quality} and size {requested_size} not found in catalog. Falling back to 0 cost.")
                cost_usd = 0.0 # Default to 0 if pricing not found
                usage = {
                    "image_quality": requested_quality,
                    "image_size": requested_size
                }
        # Prüfe, ob es sich um ein Gemini-Bildmodell mit Token-basierter Preisgestaltung handelt
        elif model_info.get("provider") == "gemini" and "output_tokens_per_image_1024x1024" in model_info:
            output_tokens = model_info.get("output_tokens_per_image_1024x1024", 0)
            cost_per_million_output_tokens = model_info.get("cost_per_million_output_tokens", 0)
            cost_usd = (output_tokens / 1_000_000) * cost_per_million_output_tokens
            usage = {"output_tokens": output_tokens, "image_quality": "standard", "image_size": "1024x1024"}
        else:
            # Fallback für andere Bildmodelle mit fixem cost_per_image, falls quality/size nicht in id
            cost_usd = model_info.get("cost_per_image", 0)
            usage = {"image_quality": "standard", "image_size": "1024x1024"}

    elif model_type == "websearch":
        cost_usd = model_info.get("cost_per_query", 0)
        usage = {"query_count": 1}

    total_cost_eur = cost_usd * USD_TO_EUR_CONVERSION_RATE
    cost = {"total_cost": total_cost_eur}

    if model_type == "image":
        cost["image_cost"] = cost_usd * USD_TO_EUR_CONVERSION_RATE
    elif model_type == "websearch":
        cost["query_cost"] = cost_usd * USD_TO_EUR_CONVERSION_RATE

    return usage, cost


def get_image_pricing_structure() -> dict:
    """
    Generiert eine Dictionary-Struktur mit den Informationen aller Bildmodelle,
    gruppiert nach Provider.
    Struktur: {provider: {model_id: model_info_object}}
    """
    structured_pricing = {}
    for model_id, model_info in MODEL_PRICES.items():
        if model_info.get("type") == "image":
            provider = model_info["provider"]
            if provider not in structured_pricing:
                structured_pricing[provider] = {}
            structured_pricing[provider][model_id] = model_info
    return structured_pricing
