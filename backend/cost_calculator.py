import json
import os
# Lade den Modellkatalog einmal beim Start, um die Leistung zu verbessern
catalog_path = os.path.join(os.path.dirname(__file__), 'model_catalog.json')
with open(catalog_path, 'r') as f:
    MODEL_CATALOG = json.load(f)

def get_model_from_catalog(model_id):
    for model in MODEL_CATALOG:
        if model['id'] == model_id:
            return model
    return None

def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Berechnet die Kosten für einen bestimmten API-Aufruf basierend auf dem Modellkatalog.
    """
    model_info = get_model_from_catalog(model_id)
    if not model_info:
        print(f"Warning: Model '{model_id}' not found in catalog. Cost calculation skipped.")
        return 0.0
    cost_per_input = model_info.get('cost_per_token_input', 0)
    cost_per_output = model_info.get('cost_per_token_output', 0)
    # Kosten werden pro 1 Million Token angegeben
    total_cost = ((input_tokens / 1_000_000) * cost_per_input) + \
                 ((output_tokens / 1_000_000) * cost_per_output)
    return round(total_cost, 6)