import json
import os

MODEL_CATALOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_catalog.json")

def load_model_catalog():
    if not os.path.exists(MODEL_CATALOG_FILE):
        return []
    try:
        with open(MODEL_CATALOG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []
    except Exception:
        raise

def calculate_cost(model_id: str, usage: dict) -> float:
    catalog = load_model_catalog()
    model_info = next((m for m in catalog if m["id"] == model_id), None)

    if not model_info:
        print(f"WARNING: Model {model_id} not found in catalog. Cannot calculate cost.")
        return 0.0

    model_type = model_info.get("type")
    
    if model_type == "text":
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cost_per_token_input = model_info.get("cost_per_token_input", 0)
        cost_per_token_output = model_info.get("cost_per_token_output", 0)
        
        cost = (input_tokens * cost_per_token_input) + (output_tokens * cost_per_token_output)
        return cost
    
    elif model_type == "image":
        # For image models, usage might contain image_cost directly from API or we use cost_per_image
        image_cost_from_usage = usage.get("image_cost")
        if image_cost_from_usage is not None:
            return image_cost_from_usage
        else:
            return model_info.get("cost_per_image", 0.0)
            
    else:
        print(f"WARNING: Unknown model type {model_type} for model {model_id}. Cannot calculate cost.")
        return 0.0
