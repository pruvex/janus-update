import pytest
import os
import json
from unittest.mock import patch
from backend.cost_calculator import calculate_cost, load_model_prices

@pytest.fixture(scope="module")
def setup_test_catalog():
    test_catalog_content = [
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "provider": "openai",
            "type": "text",
            "cost_per_token_input": 0.00000015,
            "cost_per_token_output": 0.0000006
        },
        {
            "id": "dall-e-3-standard",
            "name": "DALL·E 3 (SD)",
            "provider": "openai",
            "type": "image",
            "cost_per_image": 0.04
        },
        {
            "id": "dall-e-3-hd",
            "name": "DALL·E 3 (HD)",
            "provider": "openai",
            "type": "image",
            "cost_per_image": 0.08
        }
    ]
    
    original_path = "backend.cost_calculator.MODEL_CATALOG_FILE"
    temp_dir = os.path.join("C:", "KI", "Janus-Projekt", "backend")
    temp_file_path = os.path.join(temp_dir, "temp_model_catalog_for_test.json")

    os.makedirs(temp_dir, exist_ok=True)

    with open(temp_file_path, "w") as f:
        json.dump(test_catalog_content, f)

    with patch(original_path, temp_file_path):
        load_model_prices()
        yield
    
    os.remove(temp_file_path)
    load_model_prices()

def test_calculate_cost_text_model(setup_test_catalog):
    usage_data = {"prompt_tokens": 1000, "completion_tokens": 500}
    usage, cost = calculate_cost("gpt-4o-mini", usage_data=usage_data)
    
    expected_cost = (1000 * 0.00000015) + (500 * 0.0000006)
    assert "total_cost" in cost
    assert cost["total_cost"] == pytest.approx(expected_cost)
    assert usage["input_tokens"] == 1000
    assert usage["output_tokens"] == 500

def test_calculate_cost_image_model(setup_test_catalog):
    usage, cost = calculate_cost("dall-e-3-hd")
    
    assert "total_cost" in cost
    assert cost["total_cost"] == 0.08
    assert "image_cost" in cost
    assert cost["image_cost"] == 0.08
    assert usage["image_quality"] == "standard"

def test_calculate_cost_unknown_model(setup_test_catalog):
    usage, cost = calculate_cost("unknown-model")
    assert cost == {}
    assert usage == {}

def test_calculate_cost_zero_tokens(setup_test_catalog):
    usage_data = {"prompt_tokens": 0, "completion_tokens": 0}
    usage, cost = calculate_cost("gpt-4o-mini", usage_data=usage_data)
    
    assert "total_cost" in cost
    assert cost["total_cost"] == 0.0
    assert usage["input_tokens"] == 0
    assert usage["output_tokens"] == 0

def test_calculate_cost_missing_usage_keys(setup_test_catalog):
    usage_data = {}
    usage, cost = calculate_cost("gpt-4o-mini", usage_data=usage_data)
    print(f"Usage: {usage}, Cost: {cost}")
    assert "total_cost" in cost
    assert cost["total_cost"] == 0.0
    assert usage["input_tokens"] == 0
    assert usage["output_tokens"] == 0

def test_calculate_cost_openai_object(setup_test_catalog):
    class MockUsage:
        prompt_tokens = 2000
        completion_tokens = 1000

    usage_data = MockUsage()
    usage, cost = calculate_cost("gpt-4o-mini", usage_data=usage_data)
    
    expected_cost = (2000 * 0.00000015) + (1000 * 0.0000006)
    assert "total_cost" in cost
    assert cost["total_cost"] == pytest.approx(expected_cost)
    assert usage["input_tokens"] == 2000
    assert usage["output_tokens"] == 1000
