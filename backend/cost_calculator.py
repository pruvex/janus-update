import json
import os
import logging

logger = logging.getLogger('janus_backend')

MODEL_CATALOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_catalog.json")

def load_model_prices():
    try:
        with open(MODEL_CATALOG_FILE, "r") as f:
            models = json.load(f)
        return {model["id"]: model for model in models}
    except Exception as e:
        logger.error(f"Error loading model catalog: {e}")
        return {}

MODEL_PRICES = load_model_prices()

def calculate_cost(model_id, usage_data=None, custom_prompt=None):
    if model_id not in MODEL_PRICES:
        logger.warning(f"Price for model {model_id} not found.")
        return {}, {}

    model_info = MODEL_PRICES[model_id]
    model_type = model_info.get("type")

    usage = {}
    cost = {}

    if model_type == "text" and usage_data is not None:
        if isinstance(usage_data, dict):
            input_tokens = usage_data.get("prompt_tokens", 0)
            output_tokens = usage_data.get("completion_tokens", 0)
        else: # Assume it's an object like OpenAI's usage object
            input_tokens = usage_data.prompt_tokens
            output_tokens = usage_data.completion_tokens
        
        input_cost_per_token = model_info.get("cost_per_token_input", 0)
        output_cost_per_token = model_info.get("cost_per_token_output", 0)
        
        input_cost = input_tokens * input_cost_per_token
        output_cost = output_tokens * output_cost_per_token
        
        total_cost = input_cost + output_cost
        
        usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}
        cost = {"total_cost": total_cost}

    elif model_type == "image":
        image_cost = model_info.get("cost_per_image", 0)
        total_cost = image_cost

        usage = {"image_quality": "standard", "image_size": "1024x1024"}
        cost = {"image_cost": image_cost, "total_cost": total_cost}
    
    return usage, cost