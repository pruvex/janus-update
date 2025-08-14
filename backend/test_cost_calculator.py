import unittest
import os
import json
from unittest.mock import patch, mock_open
from cost_calculator import calculate_cost, MODEL_CATALOG_FILE

class TestCostCalculator(unittest.TestCase):

    def setUp(self):
        # Create a dummy model_catalog.json for testing
        self.test_catalog_content = [
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
        # Ensure the directory exists for the mock file
        os.makedirs(os.path.dirname(MODEL_CATALOG_FILE), exist_ok=True)
        with open(MODEL_CATALOG_FILE, "w") as f:
            json.dump(self.test_catalog_content, f)

    def tearDown(self):
        # Clean up the dummy model_catalog.json
        if os.path.exists(MODEL_CATALOG_FILE):
            os.remove(MODEL_CATALOG_FILE)
        # No need to remove the directory, as it's the 'backend' directory


    def test_calculate_cost_text_model(self):
        # Test case for a text model
        usage = {"input_tokens": 1000, "output_tokens": 500}
        cost = calculate_cost("gpt-4o-mini", usage)
        expected_cost = (1000 * 0.00000015) + (500 * 0.0000006)
        self.assertAlmostEqual(cost, expected_cost)

    def test_calculate_cost_image_model_from_usage(self):
        # Test case for an image model with cost in usage
        usage = {"image_cost": 0.08, "image_quality": "hd"}
        cost = calculate_cost("dall-e-3-hd", usage)
        self.assertAlmostEqual(cost, 0.08)

    def test_calculate_cost_image_model_from_catalog(self):
        # Test case for an image model without cost in usage, falls back to catalog
        usage = {"image_quality": "standard"} # No image_cost in usage
        cost = calculate_cost("dall-e-3-standard", usage)
        self.assertAlmostEqual(cost, 0.04)

    def test_calculate_cost_unknown_model(self):
        # Test case for an unknown model
        usage = {"input_tokens": 100, "output_tokens": 100}
        cost = calculate_cost("unknown-model", usage)
        self.assertEqual(cost, 0.0)

    def test_calculate_cost_zero_tokens(self):
        # Test case for text model with zero tokens
        usage = {"input_tokens": 0, "output_tokens": 0}
        cost = calculate_cost("gpt-4o-mini", usage)
        self.assertEqual(cost, 0.0)

    def test_calculate_cost_missing_usage_keys(self):
        # Test case for text model with missing usage keys
        usage = {}
        cost = calculate_cost("gpt-4o-mini", usage)
        self.assertEqual(cost, 0.0)

if __name__ == '__main__':
    unittest.main()