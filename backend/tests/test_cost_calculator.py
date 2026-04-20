# backend/tests/test_cost_calculator.py
import pytest
from unittest.mock import patch

# KORREKTER IMPORT (basierend auf deinem Pfad)
from backend.services.cost_calculator import calculate_cost

# Helper Klasse für Objekt-Zugriff via getattr
class MockUsage:
    def __init__(self, prompt_tokens=0, completion_tokens=0):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

@pytest.fixture
def setup_test_catalog():
    # Wir definieren einen Dummy-Katalog, der exakt zur Logik in cost_calculator.py passt
    mock_prices = {
        "gpt-5.4-nano": {
            "id": "gpt-5.4-nano",
            "type": "text",
            "cost_per_token_input": 0.00000015,
            "cost_per_token_output": 0.00000060,
            "provider": "openai"
        },
        "dall-e-3-hd": {
            "id": "dall-e-3-hd",
            "type": "image",
            "provider": "openai",
            "pricing": {
                "standard": {
                    "1024x1024": 0.08
                }
            },
            "default_quality": "standard",
            "default_size": "1024x1024"
        },
        "unknown-model": {} 
    }

    # CRITICAL FIX: Wir patchen das Dictionary direkt im Modul backend.services.cost_calculator
    with patch.dict("backend.services.cost_calculator.MODEL_PRICES", mock_prices, clear=True):
        yield

def test_calculate_cost_text_model(setup_test_catalog):
    usage_data = MockUsage(prompt_tokens=1000, completion_tokens=500)
    usage, cost = calculate_cost("gpt-5.4-nano", usage_data=usage_data)
    assert "total_cost" in cost
    assert cost["total_cost"] > 0

def test_calculate_cost_image_model(setup_test_catalog):
    usage_params = {"quality": "standard", "size": "1024x1024"}
    usage, cost = calculate_cost("dall-e-3-hd", usage_data=usage_params)
    assert "total_cost" in cost
    assert cost["total_cost"] > 0.07

def test_calculate_cost_unknown_model(setup_test_catalog):
    usage, cost = calculate_cost("super-new-model")
    assert cost == {}

def test_calculate_cost_zero_tokens(setup_test_catalog):
    usage_data = MockUsage(prompt_tokens=0, completion_tokens=0)
    usage, cost = calculate_cost("gpt-5.4-nano", usage_data=usage_data)
    assert "total_cost" in cost
    assert cost["total_cost"] == 0

def test_calculate_cost_missing_usage_keys(setup_test_catalog):
    usage_data = MockUsage()
    usage, cost = calculate_cost("gpt-5.4-nano", usage_data=usage_data)
    assert "total_cost" in cost
    assert cost["total_cost"] == 0

def test_calculate_cost_openai_object(setup_test_catalog):
    usage_data = MockUsage(prompt_tokens=2000, completion_tokens=1000)
    usage, cost = calculate_cost("gpt-5.4-nano", usage_data=usage_data)
    assert "total_cost" in cost
    assert cost["total_cost"] > 0
